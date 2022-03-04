import salabim as sim
from enum import IntEnum, Enum, auto

from reg_file_lib import PhysicalRegister


class Instr(sim.Component):
    def setup(self, instruction, resources, fetch_unit):
        # Instruction String
        self.instruction = instruction
        # Resources pointer
        self.resources = resources
        self.fetch_unit = fetch_unit
        # Decoded Fields
        self.sources = []
        self.set_fields()

    def process(self):
        print(self.instruction)
        self.state = 'decode'
        yield self.hold(1)  # Decode
        # self.resources.fetch_resource.release()
        self.release(self.resources.fetch_resource, 1)
        yield self.wait(self.resources.decode_state, urgent=True)
        self.resources.decode_state.set(False)
        if self.instr_touple[INTFields.LABEL] == InstrLabel.INT:  # Put enum value
            yield self.request(self.resources.int_queue)
        #   self.enter(self.int_queue)
            # If there is destination a physical register is requested and created
            if self.instr_touple[INTFields.DEST]:
                yield self.request(self.resources.reg_file.FRL_resource)
                self.p_dest = PhysicalRegister(state=False, value=self.dest)
                self.p_old_dest = self.resources.reg_file.get_reg(self.dest)
                self.resources.reg_file.set_reg(self.dest, self.p_dest)

            self.resources.decode_state.set(True)
            yield self.hold(1)  # Hold for dispatch stage
            for x in self.sources:
                yield self.wait(self.resources.reg_file.get_reg(x).reg_state)
            yield self.request(self.resources.int_units, 1)
            self.release(self.resources.int_queue, 1)
            if self.instr_touple[INTFields.PIPELINED]:  # If operation is pipelined
                yield self.hold(1)
                self.release(self.resources.int_units, 1)
                yield self.hold(self.instr_touple[INTFields.LATENCY]-1)  # Latency - 1
                self.p_dest.reg_state.set(True)
            else:
                yield self.hold(self.instr_touple[INTFields.LATENCY])
                self.p_dest.reg_state.set(True)
                self.release(self.resources.int_units, 1)
            self.compute()

            yield from self.resources.RobInst.instr_end(self)

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
        self.resources.RobInst.instr_end()

    def flush(self):
        self.resources.RobInst.instr_end()

    def compute(self):
        if self.instr_touple[INTFields.ALU_CODE] == ALUCode.ADD:
            self.p_dest.value = \
                self.resources.reg_file.get_reg(self.sources[0]).value + \
                self.resources.reg_file.get_reg(self.sources[0]).value

        # set the execution value
        # calculate the result

    def set_fields(self):
        parsed_instr = self.instruction.replace(',', ' ').split()
        try:
            self.instr_touple = InsrtructionTable.Instructions[parsed_instr.pop(0)]
        except NameError:
            print("NameError: Not supported instruction")
        if self.instr_touple[INTFields.LABEL] == InstrLabel.INT:
            if self.instr_touple[INTFields.DEST]:
                try:
                    self.dest = IntRegisterTable.registers[parsed_instr.pop(0)]
                except NameError:
                    print("NameError: Invalid destination register")
            for x in range(self.instr_touple[INTFields.N_SOURCES]):
                try:
                    self.sources[x] = IntRegisterTable.registers[parsed_instr.pop(0)]
                except NameError:
                    print("NameError: Invalid source register")
            if self.instr_touple[INTFields.IMEDIATE]:
                try:
                    self.imediate = int(parsed_instr.pop(0))
                except NameError:
                    print("NameError: Invalid imediate")


class IntRegisterTable:  # Register map of the micro architecture
    registers = {'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3,
                 'tp': 4, 't0': 5, 't1': 6, 't2': 7,
                 's0:': 8, 's1': 9, 'a0': 10, 'a1': 11,
                 'a2': 12, 'a3': 13, 'a4': 14, 'a5': 15,
                 'a6': 16, 'a7': 17, 's2': 18, 's3': 19,
                 's4': 20, 's5': 21, 's6': 22, 's7': 23,
                 's8': 24, 's9': 25, 's10': 26, 's11': 27,
                 't3': 28, 't4': 29, 't5': 30, 't6': 31}


class InstrLabel(Enum):
    INT = auto()
    FP = auto()
    HILAR = auto()
    CALL = auto()


class ALUCode(Enum):
    OR = auto()
    ADD = auto()
    SUB = auto()
    MULT = auto()


class INTFields(IntEnum):
    LABEL = 0
    DEST = 1
    N_SOURCES = 2
    IMEDIATE = 3
    ALU_CODE = 4
    PIPELINED = 5
    LATENCY = 6


class InsrtructionTable:  # (Instruction label, destination, n_sources,imediate, alu code, pipelined, latency)
    Instructions = {'add': (InstrLabel.INT, True, 2, False, ALUCode.ADD, True, 1),
                    'li': (InstrLabel.INT, True, 0, True, ALUCode.ADD, True, 1),
                    'nop': (InstrLabel.INT, False, 0, False, ALUCode.ADD, True, 1),
                    'new': (InstrLabel.HILAR, True)}

# Not used

# List of objects that will be executed by the HILAR queue


class HilarObjects:
    objects = ['_b_node_']
# List of objects that will be executed by the Integer Queue


class IntObjects:
    objects = ['_array_', '_int_', '_bool_', '_byte_']


class HilarMethods:
    methods = ['insert', 'search', 'get_index', 'print_data']


class Calls:
    calls = ['cout']
