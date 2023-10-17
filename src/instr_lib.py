import salabim as sim
import rv64uih_lib as dec
from reg_file_lib import PhysicalRegister


class Instr(sim.Component):
    def setup(
        self,
        decoded_fields,
        params,
        resources,
        konata_signature,
        performance_counters,
        thread_id,
        instr_id,
        fetch_unit,
        data_cache,
        bb_name,
        offset,
        bp_take_branch,
        bp_tag_index,
    ):
        self.decoded_fields = decoded_fields
        self.params = params
        # Resources pointer
        self.resources = resources
        self.fetch_unit = fetch_unit
        self.data_cache = data_cache
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
        self.data = None
        # Speculative Issue
        self.back2back = False
        # Event Trace
        self.thread_id = thread_id
        self.instr_id = instr_id
        self.konata_signature = konata_signature
        self.performance_counters = performance_counters

    def process(self):
        yield from self.front_end()
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.ARITH:
            yield from self.arith_queue()
        elif self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.LS:
            yield from self.ls_buffer()
        else:
            yield from self.dispatch_alloc()
        yield from self.read_registers()
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.ARITH:
            yield from self.execution()
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.LS:
            yield from self.data_cache_stages()
        yield from self.wait_commit()
        yield from self.commit()
        self.tracer()
        self.finish()

    def front_end(self):
        yield self.hold(1)  # Hold for fetch stage
        yield self.request(self.resources.decode_ports)
        self.fetch_unit.release_fetch()
        self.konata_signature.print_stage("FET", "DEC", self.thread_id, self.instr_id)
        yield self.hold(1)  # Hold for decode stage
        # Front end Resourses
        yield self.request(self.resources.rename_ports)
        yield self.request(self.resources.RobInst.rob_resource)
        yield self.request(self.resources.rename_resource)
        yield from self.renaming()

    def renaming(self):
        self.konata_signature.print_stage("DEC", "RNM", self.thread_id, self.instr_id)
        self.release((self.resources.decode_ports, 1))
        self.p_sources = [
            self.resources.RegisterFileInst.get_reg(src)
            for src in self.decoded_fields.sources
        ]
        # Request physical destination
        if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
            if self.decoded_fields.dest != 0:
                yield self.request(self.resources.RegisterFileInst.FRL_resource)
                self.p_dest = PhysicalRegister(
                    state=False, value=self.decoded_fields.dest
                )
                self.resources.RegisterFileInst.set_reg(
                    self.decoded_fields.dest, self.p_dest
                )
            else:
                self.p_dest = self.resources.RegisterFileInst.dummy_reg
        # Create RAT chekpoit
        if (
            self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            is dec.InstrLabel.BRANCH
        ):
            self.resources.RegisterFileInst.push_rat(self)
        self.release((self.resources.rename_resource, 1))
        yield self.hold(1)  # Hold for renaming stage
        self.release((self.resources.rename_ports, 1))

    def arith_queue(self):
        yield self.request(self.resources.int_queue)
        yield from self.dispatch_alloc()
        self.konata_signature.print_stage("ALL", "QUE", self.thread_id, self.instr_id)
        yield from self.issue_logic()
        yield from self.fu_request()

    def ls_buffer(self):
        yield self.request(self.resources.LoadStoreQueueInst.lsu_slots)
        yield from self.dispatch_alloc()
        self.konata_signature.print_stage("ALL", "LSB", self.thread_id, self.instr_id)
        # Request of cache port
        yield self.request(self.resources.cache_ports)
        yield from self.issue_logic()
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.STORE:
            yield from self.stores_lock()

    def dispatch_alloc(self):
        self.konata_signature.print_stage("RNM", "DIS", self.thread_id, self.instr_id)
        yield self.hold(1)  # Hold for dispatch stage
        yield self.request(self.resources.int_alloc_ports)
        self.konata_signature.print_stage("DIS", "ALL", self.thread_id, self.instr_id)
        yield self.hold(1)  # Hold for allocation stage
        self.release((self.resources.int_alloc_ports, 1))

    def issue_logic(self):
        # Wake-up
        for x in self.p_sources:
            yield self.wait(x.reg_state)
        self.konata_signature.print_stage("QUE", "WUP", self.thread_id, self.instr_id)

    def fu_request(self):
        # FU request
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.INT:
            yield self.request(self.resources.int_units)
        if (
            self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            is dec.InstrLabel.BRANCH
        ):
            yield self.request(self.resources.branch_units)
            if self.params.branch_in_int_alu:
                yield self.request(self.resources.int_units)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] in dec.InstrLabel.ARITH:
            self.konata_signature.print_stage(
                "WUP", "ISS", self.thread_id, self.instr_id
            )
            yield self.hold(1)  # Hold for issue stage
        # Release FU
        if self.decoded_fields.instr_tuple[dec.INTFields.PIPELINED]:
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.INT
            ):
                self.release((self.resources.int_units, 1))
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.BRANCH
            ):
                self.release((self.resources.branch_units, 1))
                if self.params.branch_in_int_alu:
                    self.release((self.resources.int_units, 1))

    def read_registers(self):
        self.konata_signature.print_stage("ISS", "RRE", self.thread_id, self.instr_id)
        # Do computation, all the values are computed in advance
        # the issue latencies are controlled to match the pipeline latencies
        self.decoded_fields.instr_tuple[dec.INTFields.EXEC](self)
        # Back to back issue arithmetic of latency 1
        if (
            self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.INT
            and self.decoded_fields.instr_tuple[dec.INTFields.DEST]
            and self.decoded_fields.instr_tuple[dec.INTFields.LATENCY] == 1
        ):
            self.p_dest.reg_state.set(True)
        # Back to back issue of stores, It checks if a store is the following instruction in the ROB
        self.resources.RobInst.store_next2commit(self)
        yield self.hold(1)  # Hold for rre stage

    def stores_lock(self):
        # Store locks untill it is the next head of the ROB
        if self.resources.RobInst.instr_end(self) and not self.back2back:
            self.resources.store_state.set(False)
            self.konata_signature.print_stage(
                "WUP", "LCK", self.thread_id, self.instr_id
            )
            yield self.wait(self.resources.store_state)

    def execution(self):
        self.konata_signature.print_stage("RRE", "EXE", self.thread_id, self.instr_id)
        if (
            self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            is dec.InstrLabel.BRANCH
        ):
            self.branch_evaluation()
        # Execution stage
        for x in range(self.decoded_fields.instr_tuple[dec.INTFields.LATENCY]):
            self.fu_last_cycle(x)
            yield self.hold(1)  # Hold for exe stage
        if (
            self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            is dec.InstrLabel.BRANCH
        ):
            self.branch_predictor_write()
        self.release((self.resources.int_queue, 1))

    def fu_last_cycle(self, cycles):
        if self.decoded_fields.instr_tuple[dec.INTFields.LATENCY] - cycles - 2 == 0:
            if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
                self.p_dest.reg_state.set(True)  # Set ready bit to issue
            if not self.decoded_fields.instr_tuple[dec.INTFields.PIPELINED]:
                self.release((self.resources.int_units, 1))

    def branch_evaluation(self):
        self.bp_hit = (not self.branch_result and not self.bp_take_branch[0]) or (
            self.branch_result
            and self.bp_take_branch[0]
            and self.decoded_fields.branch_target == self.bp_take_branch[1]
        )
        if not self.bp_hit:
            self.resources.miss_branch = [True]
            self.fetch_unit.flushed = True
            if self.branch_result:
                self.resources.branch_target = [(self.decoded_fields.branch_target, 0)]
            else:
                self.resources.branch_target = [(self.bb_name, self.offset + 1)]
            self.recovery()

    def recovery(self):
        self.resources.RegisterFileInst.recovery_rat(self)
        self.resources.RobInst.recovery_rob(self)
        if self.resources.finished:
            self.resources.finished = False
        if self.fetch_unit.ispassive():
            self.fetch_unit.bb_name = self.fetch_unit.instr_cache.get_first_bb()
            self.fetch_unit.offset = 0
            self.fetch_unit.activate()

    def branch_predictor_write(self):
        self.resources.branch_predictor.write_entry(
            self.bp_tag_index[0],
            self.bp_tag_index[1],
            self.bp_hit,
            self.decoded_fields.branch_target,
        )
        if self.params.exe_brob_release:
            self.resources.RegisterFileInst.release_shadow_rat(self)

    def data_cache_stages(self):
        self.konata_signature.print_stage("RRE", "MEM", self.thread_id, self.instr_id)
        self.release((self.resources.cache_ports, 1))
        for x in range(self.params.l1_dcache_latency):
            # Execute load a wake-up dependencies 2 cycles before finishing load.
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.LOAD
                and x + 2 == self.params.l1_dcache_latency
            ):
                self.store_to_load_fwd()
                self.p_dest.reg_state.set(True)
            yield self.hold(1)  # Hold for mem stage
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.STORE:
            self.data_cache.dc_store(self.address, self.p_sources[0].value)

    def store_to_load_fwd(self):
        next_store = self.resources.RobInst.store_next(self)
        # Store to Load forwarding
        if not next_store:
            self.p_dest.value = self.data_cache.dc_load(self.address)
        elif next_store.address == self.address:
            self.p_dest.value = next_store.p_sources[0].value
        else:
            self.p_dest.value = self.data_cache.dc_load(self.address)

    def wait_commit(self):
        self.konata_signature.print_stage("EXE", "CMP", self.thread_id, self.instr_id)
        yield self.hold(1)  # # Hold for cmp stage
        self.konata_signature.print_stage("CMP", "ROB", self.thread_id, self.instr_id)
        # Pooling to wait rob head
        while self.resources.RobInst.instr_end(self):
            yield self.hold(1)

    def commit(self):
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.CALL:
            dec.Calls.call_functions(self)
        # Advance Rob head to commit next instruction
        self.resources.RobInst.release_instr()
        yield self.request(self.resources.commit_ports)
        # Commit
        self.konata_signature.print_stage("ROB", "COM", self.thread_id, self.instr_id)
        yield self.hold(1)

    def tracer(self):
        # Counters increment
        if self.params.perf_counters_en:
            self.performance_counters.ECInst.increase_counter("commits")
            self.performance_counters.ECInst.set_counter(
                "commit_cycles", self.performance_counters.ECInst.read_counter("cycles")
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
        self.konata_signature.print_torture(
            self.thread_id,
            self.instr_id,
            self.decoded_fields.line_number,
            self.decoded_fields.instruction,
            self.decoded_fields.dest,
            self.data,
            srcs,
            self.address,
        )

    def finish(self):
        # Free claimed resources
        for resource in self.claimed_resources():
            self.release((resource, 1))
        # Remove RAT shadow copy when is a branch
        if (
            not self.params.exe_brob_release
            and self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
            is dec.InstrLabel.BRANCH
        ):
            self.resources.RegisterFileInst.release_shadow_rat(self)
        if self.resources.finished and (self.resources.RobInst.rob_list == []):
            print("Program end")
        self.konata_signature.retire_instr(self.thread_id, self.instr_id, False)
