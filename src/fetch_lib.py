import salabim as sim
import rv64uih_lib as dec
import instr_lib as ins

# from watchpoints import watch


class FetchUnit(sim.Component):
    def setup(
        self,
        pe,
    ):
        self.pe = pe
        self.offset = 0
        self.bb_name = "main"
        self.branch_taken = False
        self.instr_id = 0
        self.bp_take_branch = False, None
        self.flushed = False
        # watch(self.fetch_resource.claimed_quantity.value)

    def create_instr(self):
        self.instr_id += 1
        instr = self.pe.InstrCacheInst.get_instr(self.bb_name, self.offset)
        if self.pe.params.bp_enable:
            bp_tag_index = self.bp_tag_index(instr[1], self.pe.params.bp_entries)
            self.bp_take_branch = self.pe.BPInst.read_entry(
                bp_tag_index[0], bp_tag_index[1]
            )
        else:
            bp_tag_index = 0, 0
            self.bp_take_branch = False, None
        instr_inst = ins.Instr(
            decoded_fields=dec.DecodedFields(
                instruction=instr[0], line_number=instr[1]
            ),
            instr_id=self.instr_id,
            bp_take_branch=self.bp_take_branch,
            bp_tag_index=bp_tag_index,
            bb_name=self.bb_name,
            offset=self.offset,
            fetch_unit=self,
            priority=0,
        )
        self.pe.RoBInst.add_instr(instr_inst)
        self.pe.konata_signature.new_instr(
            self.pe.thread_id, self.instr_id, instr[1], instr[0]
        )

    @staticmethod
    def bp_tag_index(line_number, bp_entries):
        index_bits = bp_entries.bit_length() - 1
        tag = line_number >> index_bits
        index = line_number % bp_entries
        return tag, index

    def release_fetch(self):
        for resource in self.claimed_resources():
            self.release((resource, 1))

    def process(self):
        # Condition to end fetch process, if the bb_name pointer reach END and the ROB is empty the fetch process
        # is terminated
        while (
            self.bb_name != "END"
            or self.pe.RoBInst.rob_list
            or bool(self.pe.ResInst.miss_branch)
        ):
            # Request fetch width port
            yield self.request(self.pe.ResInst.fetch_resource)
            if self.pe.ResInst.miss_branch:
                if self.pe.performance_counters.CountCtrl.is_enable():
                    self.pe.performance_counters.ECInst.increase_counter(
                        "mispredictions"
                    )
                self.flushed = False
                if self.pe.ResInst.miss_branch.pop(0):
                    branch_target = self.pe.ResInst.branch_target.pop(0)
                    if branch_target[1] == self.pe.InstrCacheInst.get_block_len(
                        branch_target[0]
                    ):
                        self.bb_name = self.pe.InstrCacheInst.get_next_block(
                            branch_target[0]
                        )
                        self.offset = 0
                    else:
                        self.bb_name = branch_target[0]
                        self.offset = branch_target[1]
                else:
                    self.pe.ResInst.branch_target.pop(0)
                yield self.hold(self.pe.params.recovery_latency)
            # If fetch process reach end of file passivate it
            if self.bb_name == "END" and not self.pe.ResInst.miss_branch:
                self.pe.ResInst.finished = True
                yield self.passivate()
            else:
                # Create new instruction
                if self.flushed:
                    self.flushed = False
                    self.release_fetch()
                elif not self.bb_name == "END":
                    self.create_instr()
            # Condition to advance to next basic block
            if self.bp_take_branch[0]:
                if self.pe.performance_counters.CountCtrl.is_enable():
                    self.pe.performance_counters.ECInst.increase_counter(
                        "taken_branches"
                    )
                yield self.hold(1)
                self.bb_name = self.bp_take_branch[1]
                self.offset = 0
            else:
                if (
                    self.offset
                    == self.pe.InstrCacheInst.get_block_len(self.bb_name) - 1
                ):
                    self.bb_name = self.pe.InstrCacheInst.get_next_block(self.bb_name)
                    self.offset = 0
                    # Check if the basic block is empty
                    while self.pe.InstrCacheInst.get_block_len(self.bb_name) == 0:
                        # If fetch process reach end of file passivate it
                        if self.bb_name == "END":
                            self.pe.ResInst.finished = True
                            yield self.passivate()
                        self.bb_name = self.pe.InstrCacheInst.get_next_block(
                            self.bb_name
                        )
                else:
                    self.offset = self.offset + 1
            # yield self.hold(1)
