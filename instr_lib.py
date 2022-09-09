import salabim as sim
import rv64uih_lib as dec
from reg_file_lib import PhysicalRegister


class Instr(sim.Component):
    def setup(self, instruction, line_number, resources, konata_signature, thread_id, instr_id, fetch_unit):
        # Instruction String
        self.instruction = instruction
        self.line_number = line_number
        # Resources pointer
        self.resources = resources
        self.fetch_unit = fetch_unit
        self.thread_id = thread_id
        self.instr_id = instr_id
        self.konata_signature = konata_signature
        # Decoded Fields
        self.sources = []
        self.p_sources = []
        self.set_fields()

    def process(self):
        print(self.instruction)
        self.state = 'DEC'
        yield self.hold(1)  # Decode
        self.konata_signature.print_stage('FET', self.state, self.thread_id, self.instr_id)
        self.fetch_unit.release_fetch()
        yield self.hold(1)  # Decode
        self.konata_signature.print_stage('DEC', 'RNM', self.thread_id, self.instr_id)
        yield self.wait(self.resources.decode_state, urgent=True)
        self.resources.decode_state.set(False)
        # Aritmethic Datapath
        if self.instr_touple[dec.INTFields.DEST]:
            yield self.request(self.resources.RegisterFileInst.FRL_resource)
            self.p_dest = PhysicalRegister(state=False, value=self.dest)
            self.p_old_dest = self.resources.RegisterFileInst.get_reg(self.dest)
            self.resources.RegisterFileInst.set_reg(self.dest, self.p_dest)
        if self.instr_touple[dec.INTFields.LABEL] == dec.InstrLabel.INT:
            yield self.request(self.resources.int_queue)
        #   self.enter(self.int_queue)
            # If there is destination a physical register is requested and created
            self.resources.decode_state.set(True)
            yield self.hold(1)  # Hold for renaming stage
            self.konata_signature.print_stage('RNM', 'DIS', self.thread_id, self.instr_id)
            yield self.hold(1)
            self.konata_signature.print_stage('DIS', 'ALL', self.thread_id, self.instr_id)
            yield self.hold(1)
            self.konata_signature.print_stage('ALL', 'QUE', self.thread_id, self.instr_id)
            for x in self.p_sources:
                yield self.wait(x.reg_state)
            self.konata_signature.print_stage('QUE', 'WUP', self.thread_id, self.instr_id)
            yield self.request(self.resources.int_units)
            self.konata_signature.print_stage('WUP', 'ISS', self.thread_id, self.instr_id)
            yield self.hold(1)  # Hold for issue stage
            if self.instr_touple[dec.INTFields.PIPELINED]:
                self.release((self.resources.int_units, 1))
            self.konata_signature.print_stage('ISS', 'RRE', self.thread_id, self.instr_id)
            yield self.hold(1)  # Hold for rre stage
            self.konata_signature.print_stage('RRE', 'EXE', self.thread_id, self.instr_id)
            self.compute()
            if self.instr_touple[dec.INTFields.PIPELINED]:  # If operation is pipelined
                yield self.hold(1)
                yield self.hold(self.instr_touple[dec.INTFields.LATENCY]-1)  # Latency - 1
                if self.instr_touple[dec.INTFields.DEST]:  # Set executed bit
                    self.p_dest.reg_state.set(True)
            else:
                yield self.hold(self.instr_touple[dec.INTFields.LATENCY])
                yield self.hold(self.instr_touple[dec.INTFields.LATENCY]-1)  # Latency - 1
                if self.instr_touple[dec.INTFields.DEST]:  # Set executed bit
                    self.p_dest.reg_state.set(True)
                self.release(self.resources.int_units, 1)
            self.release(self.resources.int_queue)
            self.konata_signature.print_stage('EXE', 'CMP', self.thread_id, self.instr_id)
        # LSU datapath
        elif self.instr_touple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD \
                or self.instr_touple[dec.INTFields.LABEL] == dec.InstrLabel.STORE:
            yield self.request(self.resources.LoadStoreQueueInst.lsu_slots)
            self.resources.decode_state.set(True)
            yield self.hold(1)  # Hold for dispatch stage
            self.konata_signature.print_stage('DEC', 'DIS', self.thread_id, self.instr_id)
            yield self.hold(1)  # Hold for dispatch stage
            self.konata_signature.print_stage('DIS', 'LSB', self.thread_id, self.instr_id)
            yield self.hold(1)
            # self.enter(self.resources.LoadStoreQueueInst.entries)
            #  Waiting for commit
            while self.resources.RobInst.instr_end(self):
                yield self.hold(1)
            self.konata_signature.print_stage('RRE', 'MEM', self.thread_id, self.instr_id)
            if self.instr_touple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD:
                address = self.p_sources[0].value + self.immediate
                self.p_dest.value = self.resources.DataCacheInst.dc_load(address)
                self.p_dest.reg_state.set(True)
            else:
                address = self.p_sources[1].value + self.immediate
                self.resources.DataCacheInst.dc_store(address, self.p_sources[0].value)
            yield self.hold(3)
            self.konata_signature.print_stage('MEM', 'CMP', self.thread_id, self.instr_id)
        yield self.hold(1)  # WB cycle
        while self.resources.RobInst.instr_end(self):
            yield self.hold(1)
    # Commit
        self.konata_signature.print_stage('CMP', 'COM', self.thread_id, self.instr_id)
        self.resources.RobInst.release_instr()
        self.fetch_unit.release_rob()
        yield self.hold(1)
        if self.resources.finished and (self.resources.RobInst.count_inst == 0):
            print('Program end')
        self.konata_signature.retire_instr(self.thread_id, self.instr_id, False)
        print('Instruction finished: ', self.instruction)
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

    def flush(self):
        self.resources.RobInst.instr_end()

    def compute(self):
        self.instr_touple[dec.INTFields.EXEC](self)

        # set the execution value
        # calculate the result

    def set_fields(self):
        parsed_instr = self.instruction.replace(',', ' ').split()
        try:
            self.instr_touple = dec.InstructionTable.Instructions[parsed_instr.pop(0)]
        except:
            print("NameError: Not supported instruction")
            raise
        if self.instr_touple[dec.INTFields.LABEL] == dec.InstrLabel.INT:
            if self.instr_touple[dec.INTFields.DEST]:
                try:
                    self.dest = dec.IntRegisterTable.registers[parsed_instr.pop(0)]
                except:
                    print("NameError: Invalid destination register")
                    raise
            for x in range(self.instr_touple[dec.INTFields.N_SOURCES]):
                try:
                    self.sources.append(dec.IntRegisterTable.registers[parsed_instr.pop(0)])
                except:
                    print("NameError: Invalid source register")
                    raise
            if self.instr_touple[dec.INTFields.IMMEDIATE]:
                try:
                    self.immediate = int(parsed_instr.pop(0))
                except:
                    print("NameError: Invalid immediate")
                    raise
        # MEM parse data source or destination, addr base source and immediate
        if self.instr_touple[dec.INTFields.LABEL] == dec.InstrLabel.STORE \
                or self.instr_touple[dec.INTFields.LABEL] == dec.InstrLabel.LOAD:
            if self.instr_touple[dec.INTFields.DEST]:
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
        self.p_sources = [self.resources.RegisterFileInst.get_reg(x) for x in self.sources]

