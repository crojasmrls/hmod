from enum import IntEnum, Enum, auto


class IntRegisterTable:  # Register map of the micro architecture
    registers = {'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3,
                 'tp': 4, 't0': 5, 't1': 6, 't2': 7,
                 's0': 8, 's1': 9, 'a0': 10, 'a1': 11,
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
    LOAD = auto()
    STORE = auto()


class ALUCode(Enum):
    OR = auto()
    ADD = auto()
    SUB = auto()
    MULT = auto()


class INTFields(IntEnum):
    LABEL = 0
    DEST = 1
    N_SOURCES = 2
    IMMEDIATE = 3
    ALU_CODE = 4
    PIPELINED = 5
    LATENCY = 6
    EXEC = 7
    WIDTH = 8


class InstructionTable:
    # Compute functions
    def exec_add(instr):
        if instr.instr_touple[INTFields.IMMEDIATE]:
            if len(instr.sources) >= 1:
                instr.p_dest.value = \
                    instr.resources.RegisterFileInst.get_reg(instr.sources[0]).value + \
                    instr.immediate
            else:
                instr.p_dest.value = instr.immediate
        elif len(instr.sources) == 2:
            instr.p_dest.value = \
                instr.resources.RegisterFileInst.get_reg(instr.sources[0]).value + \
                instr.resources.RegisterFileInst.get_reg(instr.sources[1]).value

    def exec_addr(instr):
        if instr.instr_touple[INTFields.IMMEDIATE]:
            if len(instr.sources) >= 1:
                instr.address = \
                    instr.resources.RegisterFileInst.get_reg(instr.sources[0]).value + \
                    instr.immediate
            else:
                instr.address.value = instr.immediate
    # Table of tuples
    Instructions = \
        {
            # INT Instruction       destination n_sources immediate alu code     pipelined latency computation
            'add': (InstrLabel.INT, True,       2,        False,    ALUCode.ADD, True,     1,      exec_add),
            'addi': (InstrLabel.INT, True,       1,        True,     ALUCode.ADD, True,     1,      exec_add),
            'li': (InstrLabel.INT,  True,       0,        True,     ALUCode.ADD, True,     1,      exec_add),
            'nop': (InstrLabel.INT, False,      0,        False,    ALUCode.ADD, True,     1,      exec_add),
            # MEM Instruction       destination n_sources immediate alu code     pipelined latency computation width
            'sd': (InstrLabel.STORE,  False,     1,        True,     ALUCode.ADD, True,     1,    exec_addr,   64),
            # HILAR
            'new': (InstrLabel.HILAR, True)}

# # Not used

# # List of objects that will be executed by the HILAR queue


# class HilarObjects:
#     objects = ['_b_node_']
# # List of objects that will be executed by the Integer Queue


# class IntObjects:
#     objects = ['_array_', '_int_', '_bool_', '_byte_']


# class HilarMethods:
#     methods = ['insert', 'search', 'get_index', 'print_data']


# class Calls:
#     calls = ['cout']
