import salabim as sim
import rv64uih_lib as dec
from reg_file_lib import PhysicalRegister


class Instr(sim.Component):
    def setup(self, instruction, line_number, params, resources, konata_signature, performance_counters, thread_id,
              instr_id, fetch_unit, bb_name, offset, bp_take_branch, bp_tag_index):
        # Instruction String
        self.instruction = instruction
        self.line_number = line_number
        self.params = params
        # Resources pointer
        self.resources = resources
        self.fetch_unit = fetch_unit
        self.thread_id = thread_id
        self.instr_id = instr_id
        self.konata_signature = konata_signature
        self.performance_counters = performance_counters
        self.bb_name = bb_name
        self.offset = offset
        self.bp_take_branch = bp_take_branch
        self.bp_tag_index = bp_tag_index
        self.back2back = False
        # Decoded Fields
        self.sources = []
        self.p_sources = []
        self.branch_result = False
        self.flushed = False
        self.dest = None
        self.address = None
        self.data = None
        self.set_fields()

    def process(self):
        yield self.hold(1)  # Decode
        yield self.request(self.resources.decode_ports)
        self.fetch_unit.release_fetch()
        self.konata_signature.print_stage('FET', 'DEC', self.thread_id, self.instr_id)
        yield self.hold(1)  # Decode
        # Front end Resourses
        yield self.request(self.resources.rename_ports)
        yield self.request(self.resources.RobInst.rob_resource)
        yield self.request(self.resources.rename_resource)
        self.konata_signature.print_stage('DEC', 'RNM', self.thread_id, self.instr_id)
        self.release((self.resources.decode_ports, 1))
        # Arithmetic Datapath
        self.p_sources = [self.resources.RegisterFileInst.get_reg(src) for src in self.sources]
        if self.instr_tuple[dec.INTFields.DEST]:
            yield self.request(self.resources.RegisterFileInst.FRL_resource)
            self.p_dest = PhysicalRegister(state=False, value=self.dest)
            self.p_old_dest = self.resources.RegisterFileInst.get_reg(self.dest)
            self.resources.RegisterFileInst.set_reg(self.dest, self.p_dest)
        if self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT:
            yield self.request(self.resources.int_queue)
            #   self.enter(self.int_queue)
            # If there is destination a physical register is requested and created
            self.release((self.resources.rename_resource, 1))
            yield self.hold(1)  # Hold for renaming stage
            self.release((self.resources.rename_ports, 1))
            self.konata_signature.print_stage('RNM', 'DIS', self.thread_id, self.instr_id)
            yield self.hold(1)
            yield self.request(self.resources.int_alloc_ports)
            self.konata_signature.print_stage('DIS', 'ALL', self.thread_id, self.instr_id)
            yield self.hold(1)
            self.release((self.resources.int_alloc_ports, 1))
            self.konata_signature.print_stage('ALL', 'QUE', self.thread_id, self.instr_id)
            for x in self.p_sources:
                yield self.wait(x.reg_state)
            self.konata_signature.print_stage('QUE', 'WUP', self.thread_id, self.instr_id)
            yield self.request(self.resources.int_units)
            self.konata_signature.print_stage('WUP', 'ISS', self.thread_id, self.instr_id)
            yield self.hold(1)  # Hold for issue stage
            if self.instr_tuple[dec.INTFields.PIPELINED]:
                self.release((self.resources.int_units, 1))
            self.konata_signature.print_stage('ISS', 'RRE', self.thread_id, self.instr_id)
            #back2back issue of stores, It check if a store is the following instruction in the rob
            self.resources.RobInst.store_next2commit(self)
            # Wake-up at EXE stage
            self.compute()
            if self.instr_tuple[dec.INTFields.DEST]:  # Set executed bit
                self.p_dest.reg_state.set(True)
            yield self.hold(1)  # Hold for rre stage
            self.konata_signature.print_stage('RRE', 'EXE', self.thread_id, self.instr_id)
            if self.instr_tuple[dec.INTFields.PIPELINED]:  # If operation is pipelined
                for x in range(self.instr_tuple[dec.INTFields.LATENCY]):
                    yield self.hold(1)
            else:
                for x in range(self.instr_tuple[dec.INTFields.LATENCY]):
                    # Non pipelining operations must have 2 cycles or more of latency
                    if self.instr_tuple[dec.INTFields.LATENCY] - x - 2 == 0:  # Early release condition
                        self.release((self.resources.int_units, 1))
                    yield self.hold(1)
            if self.instr_tuple[dec.INTFields.DEST]:
                self.data = self.p_dest.value
            self.release((self.resources.int_queue, 1))
            self.konata_signature.print_stage('EXE', 'CMP', self.thread_id, self.instr_id)
        # Branch datapath
        if self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            self.resources.RegisterFileInst.push_rat(self)
            yield self.request(self.resources.int_queue)
            self.release((self.resources.rename_resource, 1))
            yield self.hold(1)  # Hold for renaming stage
            self.release((self.resources.rename_ports, 1))
            self.konata_signature.print_stage('RNM', 'DIS', self.thread_id, self.instr_id)
            yield self.hold(1)
            yield self.request(self.resources.int_alloc_ports)
            self.konata_signature.print_stage('DIS', 'ALL', self.thread_id, self.instr_id)
            yield self.hold(1)
            self.release((self.resources.int_alloc_ports, 1))
            self.konata_signature.print_stage('ALL', 'QUE', self.thread_id, self.instr_id)
            for x in self.p_sources:
                yield self.wait(x.reg_state)
            self.konata_signature.print_stage('QUE', 'WUP', self.thread_id, self.instr_id)
            yield self.request(self.resources.branch_units)
            if self.params.branch_in_int_alu:
                yield self.request(self.resources.int_units)
            self.konata_signature.print_stage('WUP', 'ISS', self.thread_id, self.instr_id)
            yield self.hold(1)  # Hold for issue stage
            self.release((self.resources.branch_units, 1))
            if self.params.branch_in_int_alu:
                self.release((self.resources.int_units, 1))
            self.konata_signature.print_stage('ISS', 'RRE', self.thread_id, self.instr_id)
            #back2back issue of stores, It check if a store is the following instruction in the rob
            self.resources.RobInst.store_next2commit(self)
            yield self.hold(1)  # Hold for rre stage
            self.konata_signature.print_stage('RRE', 'EXE', self.thread_id, self.instr_id)
            self.compute()
            bp_hit = (not self.branch_result and not self.bp_take_branch[0]) \
                or (self.branch_result and self.bp_take_branch[0] and self.branch_target == self.bp_take_branch[1])
            if not bp_hit:
                self.resources.miss_branch = [True]
                self.fetch_unit.flushed = True
                if self.branch_result:
                    self.resources.branch_target = [(self.branch_target, 0)]
                else:
                    self.resources.branch_target = [(self.bb_name, self.offset + 1)]
                self.recovery()
            for x in range(self.instr_tuple[dec.INTFields.LATENCY]):
                yield self.hold(1)
            self.resources.branch_predictor.write_entry(self.bp_tag_index[0], self.bp_tag_index[1], bp_hit,
                                                        self.branch_target)
            self.release((self.resources.int_queue, 1))
            if self.params.exe_brob_release:
                self.resources.RegisterFileInst.release_shadow_rat(self)
            self.konata_signature.print_stage('EXE', 'CMP', self.thread_id, self.instr_id)
        # LSU datapath
        elif self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD \
                or self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE:
            yield self.request(self.resources.LoadStoreQueueInst.lsu_slots)
            self.release((self.resources.rename_resource, 1))
            yield self.hold(1)  # Hold for dispatch stage
            self.release((self.resources.rename_ports, 1))
            self.konata_signature.print_stage('RNM', 'DIS', self.thread_id, self.instr_id)
            yield self.hold(1)  # Hold for dispatch stage
            yield self.request(self.resources.int_alloc_ports)
            self.konata_signature.print_stage('DIS', 'ALL', self.thread_id, self.instr_id)
            yield self.hold(1)
            self.release((self.resources.int_alloc_ports, 1))
            # self.enter(self.resources.LoadStoreQueueInst.entries)
            self.konata_signature.print_stage('ALL', 'LSB', self.thread_id, self.instr_id)
            # Issue LSU/Memory-pipeline
            yield self.request(self.resources.cache_ports)
            for x in self.p_sources:
                yield self.wait(x.reg_state)
            self.konata_signature.print_stage('LSB', 'WUP', self.thread_id, self.instr_id)
            if self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE and \
                    self.resources.RobInst.instr_end(self) and not self.back2back:
                self.resources.store_state.set(False)
                self.konata_signature.print_stage('WUP', 'LCK', self.thread_id, self.instr_id)
                yield self.wait(self.resources.store_state)
            self.konata_signature.print_stage('WUP', 'RRE', self.thread_id, self.instr_id)
            self.compute()
            #back2back issue of stores, It check if a store is the following instruction in the rob
            self.resources.RobInst.store_next2commit(self)
            yield self.hold(1)
            self.release((self.resources.cache_ports, 1))
            self.konata_signature.print_stage('RRE', 'MEM', self.thread_id, self.instr_id)
            yield self.hold(1)
            if self.instr_tuple[dec.INTFields.DEST]:  # Set executed bit
                self.p_dest.reg_state.set(True)
            yield self.hold(1)  # Use two yield hold functions to avoid errors.
            if self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD:
                self.p_dest.value = self.resources.DataCacheInst.dc_load(self.address)
                # To print signature
                self.data = self.p_dest.value
            else:
                self.resources.DataCacheInst.dc_store(self.address, self.p_sources[0].value)
                # To print signature
                self.data = self.p_sources[0].value
            self.konata_signature.print_stage('MEM', 'CMP', self.thread_id, self.instr_id)
        yield self.hold(1)  # WB cycle
        self.konata_signature.print_stage('CMP', 'ROB', self.thread_id, self.instr_id)
        # pooling to wait rob head
        while self.resources.RobInst.instr_end(self):
            yield self.hold(1)
        # advance Rob head to commit next intruction
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
        # torture trace
        srcs = [(self.sources[i], self.p_sources[i].value) for i in range(0, len(self.sources))]
        self.konata_signature.print_torture(self.thread_id, self.instr_id, self.line_number, self.instruction,
                                            self.dest, self.data, srcs, self.address)
        # free claimed resources
        for resource in self.claimed_resources():
            self.release((resource, 1))
        # Remove RAT shadow copy when is a branch
        if not self.params.exe_brob_release and self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
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

    def compute(self):
        self.instr_tuple[dec.INTFields.EXEC](self)
        # set the execution value
        # calculate the result

    def set_fields(self):
        parsed_instr = self.instruction.replace(',', ' ').split()
        try:
            self.instr_tuple = dec.InstructionTable.Instructions[parsed_instr.pop(0)]
        except:
            print("NameError: Not supported instruction")
            raise
        if self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.INT:
            if self.instr_tuple[dec.INTFields.DEST]:
                try:
                    self.dest = dec.IntRegisterTable.registers[parsed_instr.pop(0)]
                except:
                    print("NameError: Invalid destination register")
                    raise
            for x in range(self.instr_tuple[dec.INTFields.N_SOURCES]):
                try:
                    self.sources.append(dec.IntRegisterTable.registers[parsed_instr.pop(0)])
                except:
                    print("NameError: Invalid source register")
                    raise
            if self.instr_tuple[dec.INTFields.IMMEDIATE]:
                try:
                    self.immediate = int(parsed_instr.pop(0))
                except:
                    print("NameError: Invalid immediate")
                    raise
        # MEM parse data source or destination, addr base source and immediate
        if self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE \
                or self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD:
            if self.instr_tuple[dec.INTFields.DEST]:
                try:
                    self.dest = dec.IntRegisterTable.registers[parsed_instr.pop(0)]
                except:
                    print("NameError: Invalid destination register")
                    raise
            else:
                try:
                    self.sources.append(dec.IntRegisterTable.registers[parsed_instr.pop(0)])
                except:
                    print("NameError: Invalid source register")
                    raise
            parsed_instr = parsed_instr.pop(0).replace('(', ' ').split()
            try:
                self.immediate = int(parsed_instr.pop(0))
            except:
                print("NameError: Invalid immediate")
                raise
            parsed_instr = parsed_instr.pop(0).split(')')[0]
            try:
                self.sources.append(dec.IntRegisterTable.registers[parsed_instr])
            except:
                print("NameError: Invalid source register")
                raise
        # Branch fields
        if self.instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.BRANCH:
            for x in range(self.instr_tuple[dec.INTFields.N_SOURCES]):
                try:
                    self.sources.append(dec.IntRegisterTable.registers[parsed_instr.pop(0)])
                except:
                    print("NameError: Invalid source register")
                    raise
            self.branch_target = parsed_instr.pop(0)
