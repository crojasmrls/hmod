import salabim as sim
import rv64uih_lib as dec
from reg_file_lib import PhysicalRegister


class Instr(sim.Component):
    def setup(self, decoded_fields, params, resources, konata_signature, performance_counters, thread_id,
              instr_id, fetch_unit, bb_name, offset, bp_take_branch, bp_tag_index):
        self.decoded_fields = decoded_fields
        self.params = params
        # Resources pointer
        self.resources = resources
        self.fetch_unit = fetch_unit
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
        yield self.hold(1) # Hold for fetch stage
        yield self.request(self.resources.decode_ports)
        self.fetch_unit.release_fetch()
        self.konata_signature.print_stage('FET', 'DEC', self.thread_id, self.instr_id)
        yield self.hold(1) # Hold for decode stage
        # Front end Resourses
        yield self.request(self.resources.rename_ports)
        yield self.request(self.resources.RobInst.rob_resource)
        yield self.request(self.resources.rename_resource)
        self.konata_signature.print_stage('DEC', 'RNM', self.thread_id, self.instr_id)
        self.release((self.resources.decode_ports, 1))
        self.p_sources = [self.resources.RegisterFileInst.get_reg(src) for src in self.decoded_fields.sources]
        # Request physical destination
        if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
            yield self.request(self.resources.RegisterFileInst.FRL_resource)
            self.p_dest = PhysicalRegister(state=False, value=self.decoded_fields.dest)
            self.resources.RegisterFileInst.set_reg(self.decoded_fields.dest, self.p_dest)
        # Create RAT chekpoit
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            self.resources.RegisterFileInst.push_rat(self)
        # Request Instruction Queue slot
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT \
                or self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            yield self.request(self.resources.int_queue)
        # Request LSU slot
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD \
                or self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE:
            yield self.request(self.resources.LoadStoreQueueInst.lsu_slots)
        self.release((self.resources.rename_resource, 1))
        yield self.hold(1)  # Hold for renaming stage
        self.release((self.resources.rename_ports, 1))
        self.konata_signature.print_stage('RNM', 'DIS', self.thread_id, self.instr_id)
        yield self.hold(1)  # Hold for dispatch stage
        yield self.request(self.resources.int_alloc_ports)
        self.konata_signature.print_stage('DIS', 'ALL', self.thread_id, self.instr_id)
        yield self.hold(1) # Hold for allocation stage
        self.release((self.resources.int_alloc_ports, 1))
        # Queue stage
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT \
                or self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            self.konata_signature.print_stage('ALL', 'QUE', self.thread_id, self.instr_id)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD \
                or self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE:
            self.konata_signature.print_stage('ALL', 'LSB', self.thread_id, self.instr_id)
            # Request of cache port
            yield self.request(self.resources.cache_ports)
        # Wake-up
        for x in self.p_sources:
            yield self.wait(x.reg_state)
        self.konata_signature.print_stage('QUE', 'WUP', self.thread_id, self.instr_id)
        # FU request
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT:
            yield self.request(self.resources.int_units)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            yield self.request(self.resources.branch_units)
            if self.params.branch_in_int_alu:
                yield self.request(self.resources.int_units)
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT \
                or self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            self.konata_signature.print_stage('WUP', 'ISS', self.thread_id, self.instr_id)
            yield self.hold(1)  # Hold for issue stage
        # Release FU
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT:
            self.release((self.resources.int_units, 1))
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            self.release((self.resources.branch_units, 1))
            if self.params.branch_in_int_alu:
                self.release((self.resources.int_units, 1))
        # Store locks untill it is the next head of the ROB
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE \
                and self.resources.RobInst.instr_end(self) and not self.back2back:
            self.resources.store_state.set(False)
            self.konata_signature.print_stage('WUP', 'LCK', self.thread_id, self.instr_id)
            yield self.wait(self.resources.store_state)
        self.konata_signature.print_stage('ISS', 'RRE', self.thread_id, self.instr_id)
        # Do computation, all the values are computed in advance
        # the issue latencies are controlled to match the pipeline latencies
        self.decoded_fields.instr_tuple[dec.INTFields.EXEC](self)
        # Back to back issue arithmetic of latency 1
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT \
                and self.decoded_fields.instr_tuple[dec.INTFields.DEST] \
                and self.decoded_fields.instr_tuple[dec.INTFields.LATENCY] == 1:
            self.p_dest.reg_state.set(True)
        # Back to back issue of stores, It checks if a store is the following instruction in the ROB
        self.resources.RobInst.store_next2commit(self)
        yield self.hold(1)  # Hold for rre stage
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT \
                or self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            self.konata_signature.print_stage('RRE', 'EXE', self.thread_id, self.instr_id)
            if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
                bp_hit = (not self.branch_result and not self.bp_take_branch[0]) \
                    or (self.branch_result and self.bp_take_branch[0]
                        and self.decoded_fields.branch_target == self.bp_take_branch[1])
                if not bp_hit:
                    self.resources.miss_branch = [True]
                    self.fetch_unit.flushed = True
                    if self.branch_result:
                        self.resources.branch_target = [(self.decoded_fields.branch_target, 0)]
                    else:
                        self.resources.branch_target = [(self.bb_name, self.offset + 1)]
                    self.recovery()
            # Execution stage
            for x in range(self.decoded_fields.instr_tuple[dec.INTFields.LATENCY]):
                if self.decoded_fields.instr_tuple[dec.INTFields.LATENCY] > 1:
                    if self.decoded_fields.instr_tuple[dec.INTFields.LATENCY] - x - 2 == 0:
                        if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:  # Set ready bit to issue
                            self.p_dest.reg_state.set(True)
                        if not self.decoded_fields.instr_tuple[dec.INTFields.PIPELINED]:
                            self.release((self.resources.int_units, 1))
                yield self.hold(1)  # Hold for exe stage
            if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
                self.resources.branch_predictor.write_entry(self.bp_tag_index[0], self.bp_tag_index[1], bp_hit,
                                                            self.decoded_fields.branch_target)
                if self.params.exe_brob_release:
                    self.resources.RegisterFileInst.release_shadow_rat(self)
            self.release((self.resources.int_queue, 1))
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD \
                or self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE:
            self.konata_signature.print_stage('RRE', 'MEM', self.thread_id, self.instr_id)
            self.release((self.resources.cache_ports, 1))
            for x in range(self.params.l1_dcache_latency):
                # Execute load a wake-up dependencies 2 cycles before finishing load.
                if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD\
                        and x+2 == self.params.l1_dcache_latency:
                    next_store = self.resources.RobInst.store_next(self)
                    # Store to Load forwarding
                    if next_store:
                        if next_store.address == self.address:
                            self.p_dest.value = next_store.p_sources[0].value
                        else:
                            self.p_dest.value = self.resources.DataCacheInst.dc_load(self.address)
                    else:
                        self.p_dest.value = self.resources.DataCacheInst.dc_load(self.address)
                    self.p_dest.reg_state.set(True)
                yield self.hold(1)# Hold for mem stage
            if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE:
                self.resources.DataCacheInst.dc_store(self.address, self.p_sources[0].value)
                self.data = self.p_sources[0].value
        if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
            self.data = self.p_dest.value
        self.konata_signature.print_stage('EXE', 'CMP', self.thread_id, self.instr_id)
        yield self.hold(1)  # # Hold for cmp stage
        self.konata_signature.print_stage('CMP', 'ROB', self.thread_id, self.instr_id)
        # Pooling to wait rob head
        while self.resources.RobInst.instr_end(self):
            yield self.hold(1)
        # Advance Rob head to commit next instruction
        self.resources.RobInst.release_instr()
        yield self.request(self.resources.commit_ports)
        # Commit
        self.konata_signature.print_stage('ROB', 'COM', self.thread_id, self.instr_id)
        # Counters increment
        yield self.hold(1)
        if self.params.perf_counters_en:
            self.performance_counters.ECInst.increase_counter('commits')
            self.performance_counters.ECInst.set_counter('commit_cycles',
                                                         self.performance_counters.ECInst.read_counter('cycles'))
        # Torture trace
        srcs = [(self.decoded_fields.sources[i], self.p_sources[i].value) for i in
                range(0, len(self.decoded_fields.sources))]
        self.konata_signature.print_torture(self.thread_id, self.instr_id, self.decoded_fields.line_number,
                                            self.decoded_fields.instruction, self.decoded_fields.dest, self.data, srcs,
                                            self.address)
        # Free claimed resources
        for resource in self.claimed_resources():
            self.release((resource, 1))
        # Remove RAT shadow copy when is a branch
        if not self.params.exe_brob_release and \
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            self.resources.RegisterFileInst.release_shadow_rat(self)
        if self.resources.finished and (self.resources.RobInst.rob_list == []):
            print('Program end')
        self.konata_signature.retire_instr(self.thread_id, self.instr_id, False)

    #        elif self.type == 'HILAR':
    #            # self.enter(self.h_queue)
    #            yield self.request(self.resources.h_units)
    #            self.resources.decode_state.set(True)
    #        self.state = 'enqued'
    #        yield self.passivate()
    #        if self.type == 'BRANCH' and self.miss_branch_prediction:
    # self.fetch_unit.change_pc(self.correct_bb_name)
    # flush pipeline
    # elf.fetch_unit_
    # liberar la unidad

    def recovery(self):
        self.resources.RegisterFileInst.recovery_rat(self)
        self.resources.RobInst.recovery_rob(self)
        if self.resources.finished:
            self.resources.finished = False
        if self.fetch_unit.ispassive():
            self.fetch_unit.bb_name = self.fetch_unit.send_first_bb()
            self.fetch_unit.offset = 0
            self.fetch_unit.activate()
