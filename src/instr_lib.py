import salabim as sim
import rv64uih_lib as dec
from reg_file_lib import PhysicalRegister


class Instr(sim.Component):
    def setup(
        self,
        decoded_fields,
        instr_id,
        fetch_unit,
        bb_name,
        offset,
        bp_take_branch,
        bp_tag_index,
    ):
        self.decoded_fields = decoded_fields
        self.fetch_unit = fetch_unit
        self.pe = self.fetch_unit.pe
        # Registers
        self.p_sources = []
        self.p_dest = None
        # Branch Control
        self.bb_name = bb_name
        self.offset = offset
        self.bp_take_branch = bp_take_branch
        self.bp_tag_index = bp_tag_index
        self.flushed = False
        self.branch_result = False
        self.bp_hit = None
        # L/S
        self.address = None
        self.address_align = None
        self.data = None
        self.older_store = None
        self.ls_collisions = {}
        self.ls_ready = sim.State("ls_ready", value=False)
        self.cache_port = False
        self.promoted = False
        # self.store_buff = False
        self.store_fwd = None
        # Speculative Issue
        self.store_lock = sim.State("store_lock", value=False)
        self.psrcs_hit = False
        self.cache_hit = True
        self.mshr_owner = False
        # Commit head ready
        self.commit_head = sim.State("commit_head", value=False)
        # Event Trace
        self.instr_id = instr_id

    def process(self):
        yield from self.front_end()
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.ARITH:
            yield from self.arith_queue()
        elif self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.LS:
            if self.pe.params.OoO_lsu:
                yield from self.ooo_lsu()
            else:
                yield from self.ls_buffer()
        else:
            yield from self.dispatch_alloc()
            self.release((self.pe.ResInst.alloc_ports, 1))
            yield from self.read_registers()
        if (
            not self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            is dec.InstrLabel.STORE
        ):
            yield from self.wait_commit()
        self.finish()

    def front_end(self):
        yield self.hold(1)  # Hold for fetch stage
        yield self.request(self.pe.ResInst.decode_ports)
        self.fetch_unit.release_fetch()
        self.pe.konata_signature.print_stage(
            "F", "DEC", self.pe.thread_id, self.instr_id
        )
        yield self.hold(1)  # Hold for decode stage
        # Front end Resources
        yield self.request(self.pe.ResInst.rename_resource)
        yield self.request(self.pe.ResInst.rename_ports)
        yield self.request(self.pe.ResInst.rob_resource)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.CTRL:
            if self.pe.performance_counters.CountCtrl.is_enable():
                self.pe.performance_counters.ECInst.increase_counter("decode_branches")
            yield self.request(self.pe.ResInst.brob_resource)
        yield from self.renaming()

    def renaming(self):
        self.pe.konata_signature.print_stage(
            "DEC", "RNM", self.pe.thread_id, self.instr_id
        )
        self.p_sources = [
            self.pe.RFInst.get_reg(src) for src in self.decoded_fields.sources
        ]
        # Request physical destination
        if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
            if self.decoded_fields.dest != 0:
                yield self.request(self.pe.RFInst.FRL_resource)
                self.p_dest = PhysicalRegister(
                    state=False, value=self.decoded_fields.dest
                )
                self.pe.RFInst.set_reg(self.decoded_fields.dest, self.p_dest)
            else:
                self.p_dest = self.pe.RFInst.dummy_reg
        # Create RAT checkpoint
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.CTRL:
            self.pe.RFInst.push_rat(self)
        self.release((self.pe.ResInst.rename_resource, 1))
        self.release((self.pe.ResInst.decode_ports, 1))
        yield self.hold(1)  # Hold for renaming stage

    def arith_queue(self):
        yield from self.dispatch_alloc()
        yield self.request(self.pe.ResInst.int_queue)
        self.release((self.pe.ResInst.alloc_ports, 1))
        # self.pe.konata_signature.print_stage(
        #    "ALL", "QUE", self.pe.thread_id, self.instr_id
        # )
        while not self.psrcs_hit:
            yield from self.issue_logic()
            yield from self.fu_request()
            yield from self.read_registers()
            # Check ready of o p_sources to confirm speculation
            self.check_psrcs_hit()
            if not self.psrcs_hit:
                self.pe.konata_signature.print_stage(
                    "RRE", "DIS", self.pe.thread_id, self.instr_id
                )
                # Release blocking FU
                if not self.decoded_fields.instr_tuple[dec.INTFields.PIPELINED]:
                    self.release((self.pe.ResInst.int_units, 1))
        yield from self.execution()

    def ls_buffer(self):
        yield from self.dispatch_alloc()
        yield self.request(self.pe.ResInst.lsb_slots)
        self.release((self.pe.ResInst.alloc_ports, 1))
        self.pe.konata_signature.print_stage(
            "ALL", "LSB", self.pe.thread_id, self.instr_id
        )
        # Request of cache port
        yield self.request(self.pe.ResInst.cache_ports)
        while not self.psrcs_hit:
            yield from self.issue_logic()
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.STORE
            ):
                yield from self.stores_lock()
            yield from self.read_registers()
            self.check_psrcs_hit()
            if not self.psrcs_hit:
                self.pe.konata_signature.print_stage(
                    "RRE", "LSB", self.pe.thread_id, self.instr_id
                )
        yield from self.data_cache_pipeline()

    def ooo_lsu(self):
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.LOAD:
            yield from self.load_queue()
        else:
            yield from self.store_queue()

    def load_queue(self):
        yield from self.dispatch_alloc()
        yield self.request(self.pe.ResInst.ls_ordering)
        yield self.request(self.pe.ResInst.lsq_slots)
        yield self.request(self.pe.ResInst.int_queue)
        self.release((self.pe.ResInst.alloc_ports, 1))
        self.pe.konata_signature.print_stage(
            "RNM", "DIS", self.pe.thread_id, self.instr_id
        )
        self.pe.ResInst.load_queue.append(self)
        if self.pe.ResInst.store_queue:
            self.older_store = self.pe.ResInst.store_queue[-1]
        self.release((self.pe.ResInst.ls_ordering, 1))
        yield from self.agu_issue()
        self.ls_ready.set(self.load_disambiguation())
        yield self.hold(1)
        yield self.wait(self.ls_ready)
        if self.promoted:
            yield from self.store_to_load_fwd()
        else:
            yield self.request(self.pe.ResInst.mshrs)
            yield self.request(self.pe.ResInst.cache_ports)
            if self.pe.params.HPDC_store_bubble:
                yield self.request(self.pe.ResInst.store_bubble)
            # self.pe.konata_signature.print_stage(
            #     "DIS", "ISS", self.pe.thread_id, self.instr_id
            # )
            # yield self.hold(1)  # Issue of LSU latency
            yield from self.data_cache_pipeline()
        if self.pe.performance_counters.CountCtrl.is_enable():
            self.pe.performance_counters.ECInst.increase_counter("exe_loads")

    def store_to_load_fwd(self):
        self.psrcs_hit = False
        self.request(self.pe.ResInst.s2l_slots)
        while not self.psrcs_hit:
            yield self.wait(self.store_fwd.p_sources[0].reg_state)
            # self.pe.konata_signature.print_stage(
            #     "DIS", "WUP", self.pe.thread_id, self.instr_id
            # )
            # if not self.store_fwd.store_buff:
            #     # Request read port if data is not in Store Data Buffer
            #     yield self.request(self.pe.ResInst.cache_ports)
            #     self.cache_port = True
            # self.pe.konata_signature.print_stage(
            #     "WUP", "ISS", self.pe.thread_id, self.instr_id
            # )
            # yield self.hold(1)  # Issue cycle
            # Request write port only if read port has not been requested
            # if not self.cache_port:
            #     yield self.request(self.pe.ResInst.cache_ports)
            yield self.request(self.pe.ResInst.cache_ports)
            # self.store_fwd.store_buff = True
            self.p_dest.value = self.store_fwd.p_sources[0].value
            self.p_dest.reg_state.set(True)
            yield from self.read_registers()
            self.check_psrcs_hit()
            if not self.psrcs_hit:
                self.pe.konata_signature.print_stage(
                    "FWD", "DIS", self.pe.thread_id, self.instr_id
                )
                # self.release((self.pe.ResInst.cache_ports, 1))
                # self.store_fwd.store_buff = False
            self.release((self.pe.ResInst.cache_ports, 1))
        self.pe.konata_signature.print_stage(
            "RRE", "FWD", self.pe.thread_id, self.instr_id
        )
        # yield self.hold(1)
        self.release((self.pe.ResInst.s2l_slots, 1))
        # self.release((self.pe.ResInst.cache_ports, 1))
        # self.pe.konata_signature.print_stage(
        #     "FWD", "CPL", self.pe.thread_id, self.instr_id
        # )
        yield self.hold(1)
        if self.pe.performance_counters.CountCtrl.is_enable():
            self.pe.performance_counters.ECInst.increase_counter("load_forwards")

    def load_disambiguation(self):
        if not self.older_store:
            return True
        for store in self.pe.ResInst.store_queue:
            if not store.address and not self.pe.params.speculate_on_younger_loads:
                self.ls_collisions[store] = None
            elif store.address == self.address:
                if self.pe.ResInst.s2l_slots.available_quantity.value > 0:
                    self.promoted = True
                    self.store_fwd = store
                else:
                    self.ls_collisions[store] = None
            if store is self.older_store:
                if self.ls_collisions:
                    return False
                else:
                    return True

    def store_queue(self):
        yield from self.dispatch_alloc()
        yield self.request(self.pe.ResInst.ls_ordering)
        yield self.request(self.pe.ResInst.lsq_slots)
        yield self.request(self.pe.ResInst.int_queue)
        self.release((self.pe.ResInst.alloc_ports, 1))
        self.pe.konata_signature.print_stage(
            "RNM", "DIS", self.pe.thread_id, self.instr_id
        )
        self.pe.ResInst.store_queue.append(self)
        self.release((self.pe.ResInst.ls_ordering, 1))
        yield from self.agu_issue()
        self.store_disambiguation()
        # Wait data ready
        yield self.wait(self.p_sources[0].reg_state)
        self.pe.konata_signature.print_stage(
            "AGU", "LSU", self.pe.thread_id, self.instr_id
        )
        yield self.hold(1)  # Issue of LSU latency
        self.pe.konata_signature.print_stage(
            "ISS", "CPL", self.pe.thread_id, self.instr_id
        )
        yield self.hold(1)  # Complete of LSU latency
        # Wait to be in commit window
        yield from self.wait_commit()
        self.release((self.pe.ResInst.commit_ports, 1))
        self.pe.konata_signature.print_stage(
            "CPL", "SBU", self.pe.thread_id, self.instr_id
        )
        # self.store_buff = True
        yield self.hold(1)
        # if self.cache_port:
        #
        yield self.request(self.pe.ResInst.mshrs)
        yield self.request(self.pe.ResInst.cache_ports)
        self.release((self.pe.ResInst.sb_slots, 1))
        # Clean all the collisions generated by this store.
        yield from self.data_cache_pipeline()
        # Pop this entry after cache response
        self.pe.ResInst.store_queue.pop(self.pe.ResInst.store_queue.index(self))
        self.store_clear_collisions()

    def store_disambiguation(self):
        load_flush = False
        younger_loads = False
        for load in self.pe.ResInst.load_queue:
            if self in load.ls_collisions and load.address:
                if self.address != load.address:
                    del load.ls_collisions[self]
                else:
                    if self.pe.ResInst.s2l_slots.available_quantity.value > 0:
                        del load.ls_collisions[self]
                        load.promoted = True
                        load.store_fwd = self
            if not load.ls_collisions and not self.pe.params.speculate_on_younger_loads:
                load.ls_ready.set(True)
            # load flush condition due to memory violation
            younger_loads = self is load.older_store or younger_loads
            if (
                self.pe.params.speculate_on_younger_loads
                and not load_flush
                and younger_loads
                and load.ls_ready.value.value
                and self.address == load.address
            ):
                load_flush = True
                self.pe.ResInst.branch_target = [(load.bb_name, load.offset)]
                self.recovery(load)

    def store_clear_collisions(self):
        for load in self.pe.ResInst.load_queue:
            if self in load.ls_collisions:
                del load.ls_collisions[self]
            if not load.ls_collisions:
                load.ls_ready.set(True)
            if load.older_store == self:
                load.older_store = None

    def agu_issue(self):
        while not self.psrcs_hit:
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.LOAD
            ):
                yield self.wait(self.p_sources[0].reg_state)
            else:
                yield self.wait(self.p_sources[1].reg_state)
            # self.pe.konata_signature.print_stage(
            #     "QUE", "WUP", self.pe.thread_id, self.instr_id
            # )
            yield self.request(self.pe.ResInst.agu_resource)
            self.pe.konata_signature.print_stage(
                "QUE", "ISS", self.pe.thread_id, self.instr_id
            )
            yield self.hold(1)
            self.release((self.pe.ResInst.agu_resource, 1))
            yield from self.read_registers()
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.LOAD
            ):
                self.check_psrcs_hit()
            else:
                self.psrcs_hit = self.p_sources[1].reg_state.value.value
            if not self.psrcs_hit:
                self.pe.konata_signature.print_stage(
                    "RRE", "DIS", self.pe.thread_id, self.instr_id
                )
        self.release((self.pe.ResInst.int_queue, 1))
        self.pe.konata_signature.print_stage(
            "RRE", "AGU", self.pe.thread_id, self.instr_id
        )
        yield self.hold(1)
        self.pe.konata_signature.print_stage(
            "AGU", "LSU", self.pe.thread_id, self.instr_id
        )

    def check_psrcs_hit(self):
        self.psrcs_hit = True
        for x in self.p_sources:
            if not x.reg_state.value.value:
                self.psrcs_hit = False

    def dispatch_alloc(self):
        yield self.request(self.pe.ResInst.dispatch_ports)
        self.release((self.pe.ResInst.rename_ports, 1))
        self.pe.konata_signature.print_stage(
            "RNM", "DIS", self.pe.thread_id, self.instr_id
        )
        yield self.hold(1)  # Hold for dispatch stage
        yield self.request(self.pe.ResInst.alloc_ports)
        self.release((self.pe.ResInst.dispatch_ports, 1))
        # self.pe.konata_signature.print_stage(
        #     "RNM", "ALL", self.pe.thread_id, self.instr_id
        # )
        # yield self.hold(1)  # Hold for allocation stage

    def issue_logic(self):
        # Wake-up
        for x in self.p_sources:
            yield self.wait(x.reg_state)
        self.pe.konata_signature.print_stage(
            "QUE", "WUP", self.pe.thread_id, self.instr_id
        )

    def fu_request(self):
        # FU request
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.INT:
            yield self.request(self.pe.ResInst.int_units)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.CTRL:
            yield self.request(self.pe.ResInst.branch_units)
            if self.pe.params.branch_in_int_alu:
                yield self.request(self.pe.ResInst.int_units)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.ARITH:
            self.pe.konata_signature.print_stage(
                "WUP", "ISS", self.pe.thread_id, self.instr_id
            )
            yield self.hold(1)  # Hold for issue stage
        # Release FU
        if self.decoded_fields.instr_tuple[dec.INTFields.PIPELINED]:
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.INT
            ):
                self.release((self.pe.ResInst.int_units, 1))
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                in dec.InstrLabel.CTRL
            ):
                self.release((self.pe.ResInst.branch_units, 1))
                if self.pe.params.branch_in_int_alu:
                    self.release((self.pe.ResInst.int_units, 1))

    def read_registers(self):
        # self.pe.konata_signature.print_stage(
        #     "ISS", "RRE", self.pe.thread_id, self.instr_id
        # )
        # Do computation, all the values are computed in advance
        # the issue latencies are controlled to match the pipeline latencies
        try:
            self.decoded_fields.instr_tuple[dec.INTFields.EXEC](self)
        except TypeError:
            print("TypeError on instruction:", self.instr_id)
        # Back to back issue arithmetic of latency 1
        if (
            self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.INT
            and self.decoded_fields.instr_tuple[dec.INTFields.DEST]
            and self.decoded_fields.instr_tuple[dec.INTFields.LATENCY] == 1
            or self.promoted
        ):
            self.p_dest.reg_state.set(True)
        yield self.hold(1)  # Hold for rre stage

    def stores_lock(self):
        # Store locks until it is the next head of the ROB
        self.pe.konata_signature.print_stage(
            "WUP", "LCK", self.pe.thread_id, self.instr_id
        )
        self.store_lock.set(self.pe.RoBInst.rob_head(self))
        yield self.wait(self.store_lock)
        self.pe.konata_signature.print_stage(
            "LCK", "QHD", self.pe.thread_id, self.instr_id
        )

    def execution(self):
        # self.pe.konata_signature.print_stage(
        #     "RRE", "EXE", self.pe.thread_id, self.instr_id
        # )
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.CTRL:
            if self.pe.performance_counters.CountCtrl.is_enable():
                self.pe.performance_counters.ECInst.increase_counter("exe_branches")
            self.branch_evaluation()
        # Execution stage
        for x in range(self.decoded_fields.instr_tuple[dec.INTFields.LATENCY]):
            self.fu_last_cycle(x)
            yield self.hold(1)  # Hold for exe stage
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.CTRL:
            self.branch_predictor_write()
        self.release((self.pe.ResInst.int_queue, 1))

    def fu_last_cycle(self, cycles):
        if (
            cycles + self.pe.params.issue_to_exe_latency
            == self.decoded_fields.instr_tuple[dec.INTFields.LATENCY]
        ):
            if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
                self.p_dest.reg_state.set(True)  # Set ready bit to issue
            if not self.decoded_fields.instr_tuple[dec.INTFields.PIPELINED]:
                self.release((self.pe.ResInst.int_units, 1))

    def branch_evaluation(self):
        self.bp_hit = (not self.branch_result and not self.bp_take_branch[0]) or (
            self.branch_result
            and self.bp_take_branch[0]
            and self.decoded_fields.branch_target == self.bp_take_branch[1]
        )
        if not self.bp_hit:
            self.pe.ResInst.miss_branch = [True]
            self.fetch_unit.flushed = True
            if self.branch_result:
                if (
                    self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                    is dec.InstrLabel.JALR
                ):
                    self.pe.ResInst.branch_target = [(self.p_sources[0].value, 0)]
                    self.decoded_fields.branch_target = self.p_sources[0].value
                else:
                    self.pe.ResInst.branch_target = [
                        (self.decoded_fields.branch_target, 0)
                    ]
            else:
                self.pe.ResInst.branch_target = [(self.bb_name, self.offset + 1)]
            self.recovery(self)

    def recovery(self, recovery_instr):
        self.pe.RFInst.recovery_rat(recovery_instr)
        self.pe.RoBInst.recovery_rob(recovery_instr)
        if self.pe.ResInst.finished:
            self.pe.ResInst.finished = False
        if self.fetch_unit.ispassive():
            self.fetch_unit.bb_name = self.pe.InstrCacheInst.get_first_bb()
            self.fetch_unit.offset = 0
            self.fetch_unit.activate()

    def branch_predictor_write(self):
        self.pe.BPInst.write_entry(
            self.bp_tag_index[0],
            self.bp_tag_index[1],
            self.bp_hit,
            self.decoded_fields.branch_target,
        )
        if self.pe.params.exe_brob_release:
            self.pe.RFInst.release_shadow_rat(self)
            self.release((self.pe.ResInst.brob_resource, 1))

    def data_cache_pipeline(self):
        # self.pe.konata_signature.print_stage(
        #     "RRE", "MSH", self.pe.thread_id, self.instr_id
        # )
        # yield self.request(self.pe.ResInst.mshrs)
        self.pe.konata_signature.print_stage(
            "RRE", "MEM", self.pe.thread_id, self.instr_id
        )
        # if self.pe.params.issue_to_exe_latency > 1 and not self.pe.params.OoO_lsu:
        #     self.release((self.pe.ResInst.cache_ports, 1))
        self.address_align = (
            self.address >> self.pe.params.mshr_shamt
        ) << self.pe.params.mshr_shamt
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.LOAD:
            self.cache_store_to_load_fwd()
            latency = self.pe.DataCacheInst.load_latency(
                self.address_align,
                self.decoded_fields.instr_tuple[dec.INTFields.N_BYTES],
            )
        else:
            latency = self.pe.DataCacheInst.store_latency(
                self.address_align,
                self.decoded_fields.instr_tuple[dec.INTFields.N_BYTES],
            )
        self.cache_hit = (
            latency == self.pe.params.dcache_load_hit_latency
            or latency == self.pe.params.dcache_store_hit_latency
        )
        if not self.cache_hit:
            self.pe.DataCacheInst.mshrs[self.address_align] = latency
            self.mshr_owner = True
        mshr_latency = self.pe.DataCacheInst.mshrs.get(self.address_align)
        if mshr_latency:
            self.cache_hit = False
            latency = mshr_latency
        if self.cache_hit:
            self.release((self.pe.ResInst.mshrs, 1))
        if self.pe.performance_counters.CountCtrl.is_enable():
            self.dcache_counters(latency)
        for x in range(latency):
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.LOAD
            ):
                # Execute load a wake-up dependencies 2 cycles before finishing load.
                if (
                    x + self.pe.params.issue_to_exe_latency
                    == self.pe.params.dcache_load_hit_latency
                ):
                    if self.pe.params.speculate_on_load_hit:
                        self.p_dest.reg_state.set(True)
                # if x == self.pe.params.dcache_load_hit_latency - 1:
                #     self.p_dest.reg_state.set(self.cache_hit)
            yield self.hold(1)  # Hold for mem stage
            # if (
            #     x == 0
            #     and self.pe.params.issue_to_exe_latency == 1
            #     and not self.pe.params.OoO_lsu
            # ):
            #     self.release((self.pe.ResInst.cache_ports, 1))
            if self.mshr_owner and x > 2:
                self.pe.DataCacheInst.mshrs[self.address_align] -= 1
            if x == 0:
                if self.pe.params.HPDC_store_bubble:
                    if (
                        self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                        is dec.InstrLabel.STORE
                    ):
                        yield self.request(self.pe.ResInst.store_bubble)
                    else:
                        self.release((self.pe.ResInst.store_bubble, 1))
                self.release((self.pe.ResInst.cache_ports, 1))
            if (
                x == 1
                and self.pe.params.HPDC_store_bubble
                and self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.STORE
            ):
                self.release((self.pe.ResInst.store_bubble, 1))
        if not self.cache_hit:
            yield self.request(self.pe.ResInst.cache_ports)
            yield self.hold(1)
            self.release((self.pe.ResInst.cache_ports, 1))
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.LOAD
            ):
                self.cache_store_to_load_fwd()
                self.p_dest.reg_state.set(True)
            self.release((self.pe.ResInst.mshrs, 1))
            self.cache_hit = True
            if self.mshr_owner:
                self.mshr_owner = False
                try:
                    self.pe.DataCacheInst.mshrs.pop(self.address_align)
                except KeyError:
                    pass
        # if (
        #     self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.LOAD
        #     and not self.pe.params.speculate_on_load_hit
        # ):
        #     self.p_dest.reg_state.set(True)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.STORE:
            if self.pe.performance_counters.CountCtrl.is_enable():
                self.pe.performance_counters.ECInst.increase_counter("exe_stores")
            self.pe.DataCacheInst.dc_store(self.address, self.p_sources[0].value)

    def dcache_counters(self, latency):
        if self.cache_hit:
            self.pe.performance_counters.ECInst.increase_counter("dcache_hits")
        else:
            self.pe.performance_counters.ECInst.increase_counter("dcache_misses")
        if latency == self.pe.params.l3_dcache_miss_latency and self.mshr_owner:
            self.pe.performance_counters.ECInst.increase_counter("l3_misses")
            self.pe.performance_counters.ECInst.increase_counter("l2_misses")
        elif latency == self.pe.params.l2_dcache_miss_latency and self.mshr_owner:
            self.pe.performance_counters.ECInst.increase_counter("l3_hits")
            self.pe.performance_counters.ECInst.increase_counter("l2_misses")
        elif latency == self.pe.params.l1_dcache_miss_latency and self.mshr_owner:
            self.pe.performance_counters.ECInst.increase_counter("l2_hits")

    def cache_store_to_load_fwd(self):
        next_store = self.pe.RoBInst.store_next(self)
        # Store to Load forwarding
        if not next_store:
            self.p_dest.value = self.pe.DataCacheInst.dc_load(self.address)
        elif next_store.address == self.address:
            self.p_dest.value = next_store.p_sources[0].value
        else:
            self.p_dest.value = self.pe.DataCacheInst.dc_load(self.address)

    def wait_commit(self):
        self.pe.konata_signature.print_stage(
            "EXE", "CPL", self.pe.thread_id, self.instr_id
        )
        if (
            not self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            in dec.InstrLabel.LS
        ):
            yield self.hold(1)  # Hold for cmp stage
        # self.pe.konata_signature.print_stage(
        #     "CPL", "ROB", self.pe.thread_id, self.instr_id
        # )
        if (
            self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.LOAD
            and not self.pe.params.speculate_on_load_hit
        ):
            self.p_dest.reg_state.set(True)
        # Pooling to wait rob head
        self.pe.RoBInst.store_next2commit()
        if self.pe.RoBInst.rob_head(self):
            self.commit_head.set(True)
        yield self.wait(self.commit_head)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.STORE:
            #     if not self.store_buff:
            yield self.request(self.pe.ResInst.sb_slots)
        #         self.cache_port = True
        yield from self.commit()
        self.tracer()

    def commit(self):
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.CALL:
            dec.Calls.call_functions(self)
        if self.decoded_fields.is_magic:
            dec.Magics.magic_functions(self)
        # Advance Rob head to commit next instruction
        self.pe.RoBInst.release_instr()
        # check if a store is the following instruction in the ROB after a flush
        self.pe.RoBInst.store_next2commit()
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.LOAD:
            if self.pe.ResInst.load_queue:
                self.pe.ResInst.load_queue.pop(0)
        yield self.request(self.pe.ResInst.commit_ports)
        # Commit
        self.pe.konata_signature.print_stage(
            "ROB", "CMT", self.pe.thread_id, self.instr_id
        )
        yield self.hold(1)  # Commit cycle

    def tracer(self):
        # Counters increment
        if self.pe.performance_counters.CountCtrl.is_enable():
            self.pe.performance_counters.ECInst.increase_counter("commits")
            self.pe.performance_counters.ECInst.set_counter(
                "commit_cycles",
                self.pe.performance_counters.ECInst.read_counter("cycles"),
            )
        # Torture trace
        if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
            self.data = self.p_dest.value
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.STORE:
            self.data = self.p_sources[0].value
        srcs = [
            (self.decoded_fields.sources[i], self.p_sources[i].value)
            for i in range(0, len(self.decoded_fields.sources))
        ]
        self.pe.konata_signature.print_torture(
            self.pe.thread_id,
            self.instr_id,
            self.decoded_fields.line_number,
            self.decoded_fields.instruction,
            self.decoded_fields.dest,
            self.data,
            srcs,
            self.address,
        )

    def finish(self):
        # Remove RAT shadow copy when is a branch
        if (
            not self.pe.params.exe_brob_release
            and self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            in dec.InstrLabel.CTRL
        ):
            self.pe.RFInst.release_shadow_rat(self)
        # Free claimed pe.ResInst
        for resource in self.claimed_resources():
            self.release((resource, 1))
        # if self.pe.ResInst.finished and (self.pe.RobInst.rob_list == []):
        #    print("Program end")
        self.pe.konata_signature.retire_instr(self.pe.thread_id, self.instr_id, False)
