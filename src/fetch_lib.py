import salabim as sim
import rv64uih_lib as dec
import instr_lib as ins
# from watchpoints import watch


class FetchUnit(sim.Component):
    """docstring for InstrCache"""
    def setup(self, instr_cache, params, resources, thread_id, konata_signature, performance_counters, data_cache):
        self.instr_cache = instr_cache
        self.params = params
        self.offset = 0
        self.bb_name = 'main'
        self.branch_taken = False
        self.resources = resources
        self.thread_id = thread_id
        self.konata_signature = konata_signature
        self.performance_counters = performance_counters
        self.data_cache = data_cache
        self.instr_id = 0
        self.bp_take_branch = False, None
        self.flushed = False
        # watch(self.fetch_resource.claimed_quantity.value)

    def create_instr(self):
        self.instr_id += 1
        instr = self.instr_cache.get_instr(self.bb_name, self.offset)
        if self.params.bp_enable:
            bp_tag_index = self.bp_tag_index(instr[1], self.params.bp_entries)
            self.bp_take_branch = self.resources.branch_predictor.read_entry(bp_tag_index[0], bp_tag_index[1])
        else:
            bp_tag_index = 0, 0
            self.bp_take_branch = False, None
        instr_inst = ins.Instr(
            decoded_fields=dec.DecodedFields(instruction=instr[0], line_number=instr[1]),
            params=self.params, resources=self.resources,  thread_id=self.thread_id, instr_id=self.instr_id,
            konata_signature=self.konata_signature, performance_counters=self.performance_counters, fetch_unit=self,
            data_cache=self.data_cache, bb_name=self.bb_name, offset=self.offset, bp_take_branch=self.bp_take_branch,
            bp_tag_index=bp_tag_index, priority=0
        )
        self.resources.RobInst.add_instr(instr_inst)
        self.konata_signature.new_instr(self.thread_id, self.instr_id, instr[1], instr[0])

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
        while self.bb_name != 'END' or self.resources.RobInst.count_inst != 0:
            # Request fetch width port
            yield self.request(self.resources.fetch_resource)
            if len(self.resources.miss_branch) != 0:
                self.flushed = False
                if self.resources.miss_branch.pop(0):
                    branch_target = self.resources.branch_target.pop(0)
                    self.bb_name = branch_target[0]
                    self.offset = branch_target[1]
                else:
                    self.resources.branch_target.pop(0)
            # If fetch process reach end of file passivate it
            if self.bb_name == 'END':
                self.resources.finished = True
                yield self.passivate()
            else:
                # Create new instruction
                if self.flushed:
                    self.flushed = False
                    self.release_fetch()
                else:
                    self.create_instr()
            # Condition to advance to next basic block
            if self.bp_take_branch[0]:
                self.bb_name = self.bp_take_branch[1]
                self.offset = 0
            else:
                if self.offset == self.instr_cache.get_block_len(self.bb_name) - 1:
                    self.bb_name = self.instr_cache.get_next_block(self.bb_name)
                    self.offset = 0
                    # Check if the basic block is empty
                    while self.instr_cache.get_block_len(self.bb_name) == 0:
                        # If fetch process reach end of file passivate it
                        if self.bb_name == 'END':
                            self.resources.finished = True
                            yield self.passivate()
                        self.bb_name = self.instr_cache.get_next_block(self.bb_name)
                else:
                    self.offset = self.offset + 1
            # yield self.hold(1)
