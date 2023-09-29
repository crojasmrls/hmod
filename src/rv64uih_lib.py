from enum import IntEnum, Flag, auto


class IntRegisterTable:  # Register map of the micro architecture
    registers = {
        "zero": 0,
        "ra": 1,
        "sp": 2,
        "gp": 3,
        "tp": 4,
        "t0": 5,
        "t1": 6,
        "t2": 7,
        "s0": 8,
        "s1": 9,
        "a0": 10,
        "a1": 11,
        "a2": 12,
        "a3": 13,
        "a4": 14,
        "a5": 15,
        "a6": 16,
        "a7": 17,
        "s2": 18,
        "s3": 19,
        "s4": 20,
        "s5": 21,
        "s6": 22,
        "s7": 23,
        "s8": 24,
        "s9": 25,
        "s10": 26,
        "s11": 27,
        "t3": 28,
        "t4": 29,
        "t5": 30,
        "t6": 31,
    }


class InstrLabel(Flag):
    INT = auto()
    FP = auto()
    HILAR = auto()
    CALL = auto()
    LOAD = auto()
    STORE = auto()
    BRANCH = auto()
    LS = LOAD | STORE
    ARITH_INT = INT | BRANCH
    ARITH = ARITH_INT | FP


class INTFields(IntEnum):
    LABEL = 0
    DEST = 1
    N_SOURCES = 2
    IMMEDIATE = 3
    PIPELINED = 4
    LATENCY = 5
    EXEC = 6
    N_BYTES = 7


class ExeFuncts:
    # Compute functions
    @staticmethod
    def exec_add(instr):
        if instr.decoded_fields.instr_tuple[INTFields.IMMEDIATE]:
            if len(instr.decoded_fields.sources) >= 1:
                instr.p_dest.value = (
                    instr.p_sources[0].value + instr.decoded_fields.immediate
                )
            else:
                instr.p_dest.value = instr.decoded_fields.immediate
        elif len(instr.decoded_fields.sources) == 2:
            instr.p_dest.value = instr.p_sources[0].value + instr.p_sources[1].value
        elif len(instr.decoded_fields.sources) == 1:
            instr.p_dest.value = instr.p_sources[0].value

    @staticmethod
    def exec_lui(instr):
        instr.p_dest.value = instr.decoded_fields.immediate << 12

    @staticmethod
    def exec_sll(instr):
        instr.p_dest.value = instr.p_sources[0].value << (
            instr.p_sources[1].value & 0x1F
        )

    @staticmethod
    def exec_slt(instr):
        if instr.p_sources[0].value < instr.p_sources[1].value:
            instr.p_dest.value = 1
        else:
            instr.p_dest.value = 0

    @staticmethod
    def exec_addr(instr):
        if instr.decoded_fields.instr_tuple[INTFields.LABEL] is InstrLabel.LOAD:
            instr.address = instr.p_sources[0].value + instr.decoded_fields.immediate
        else:
            instr.address = instr.p_sources[1].value + instr.decoded_fields.immediate

    @staticmethod
    def exec_nequ(instr):
        instr.branch_result = instr.p_sources[0].value != instr.p_sources[1].value

    @staticmethod
    def exec_equ(instr):
        instr.branch_result = instr.p_sources[0].value == instr.p_sources[1].value

    @staticmethod
    def exec_equz(instr):
        instr.branch_result = instr.p_sources[0].value == 0

    @staticmethod
    def exec_less(instr):
        instr.branch_result = instr.p_sources[0].value < instr.p_sources[1].value

    @staticmethod
    def exec_true(instr):
        instr.branch_result = True


class InstructionTable:
    # Table of tuples
    # fmt: off
    Instructions = \
        {
            # INT    label               destination n_sources immediate pipelined latency computation
            'add':   (InstrLabel.INT,    True,       2,        False,    True,     1,      ExeFuncts.exec_add),
            'mv':    (InstrLabel.INT,    True,       1,        False,    True,     1,      ExeFuncts.exec_add),
            'addi':  (InstrLabel.INT,    True,       1,        True,     True,     1,      ExeFuncts.exec_add),
            'addiw': (InstrLabel.INT,    True,       1,        True,     True,     1,      ExeFuncts.exec_add),
            'li':    (InstrLabel.INT,    True,       0,        True,     True,     1,      ExeFuncts.exec_add),
            'lui':   (InstrLabel.INT,    True,       0,        True,     True,     1,      ExeFuncts.exec_lui),
            'sll':   (InstrLabel.INT,    True,       2,        False,    True,     1,      ExeFuncts.exec_sll),
            'slt':   (InstrLabel.INT,    True,       2,        False,    True,     1,      ExeFuncts.exec_slt),
            'nop':   (InstrLabel.INT,    False,      0,        False,    True,     1,      ExeFuncts.exec_add),
            # MEM    label               destination n_sources immediate pipelined latency computation          n_bytes
            'sd':    (InstrLabel.STORE,  False,      2,        True,     True,     1,      ExeFuncts.exec_addr, 8),
            'ld':    (InstrLabel.LOAD,   True,       1,        True,     True,     1,      ExeFuncts.exec_addr, 8),
            # Branch label               destination n_sources immediate pipelined latency computation
            'bne':   (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_nequ),
            'beq':   (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_equ),
            'bltu':  (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_less),
            'beqz':  (InstrLabel.BRANCH, False,      1,        False,    True,     1,      ExeFuncts.exec_equz),
            'j':     (InstrLabel.BRANCH, False,      0,        False,    True,     1,      ExeFuncts.exec_true),
            'jr':    (InstrLabel.CALL,   False,      0,        False,    True,     1,      ExeFuncts.exec_add),
            # HILAR  label               destination n_sources immediate pipelined latency computation
            'new':   (InstrLabel.HILAR,  False,      0,        False,    True,     1,      ExeFuncts.exec_add),
            # CALLS  label               destination n_sources immediate pipelined latency computation
            'call':  (InstrLabel.CALL,   False,      0,        False,    True,     1,      ExeFuncts.exec_add)
        }
    # fmt: on


class DecodedFields:
    def __init__(self, instruction, line_number):
        self.instruction = instruction
        self.line_number = line_number
        # Decoded Fields
        self.sources = []
        self.dest = None
        self.immediate = None
        self.branch_target = None
        self.instr_tuple = None
        self.set_fields()

    def set_fields(self):
        parsed_instr = self.instruction.replace(",", " ").split()
        try:
            self.instr_tuple = InstructionTable.Instructions[parsed_instr.pop(0)]
        except KeyError:
            print("NameError: Not supported instruction")
            raise
        if self.instr_tuple[INTFields.LABEL] is InstrLabel.INT:
            if self.instr_tuple[INTFields.DEST]:
                try:
                    self.dest = IntRegisterTable.registers[parsed_instr.pop(0)]
                except KeyError:
                    print("NameError: Invalid destination register")
                    raise
            for x in range(self.instr_tuple[INTFields.N_SOURCES]):
                try:
                    self.sources.append(IntRegisterTable.registers[parsed_instr.pop(0)])
                except KeyError:
                    print("NameError: Invalid source register")
                    raise
            if self.instr_tuple[INTFields.IMMEDIATE]:
                try:
                    self.immediate = int(parsed_instr.pop(0))
                except ValueError:
                    print("NameError: Invalid immediate")
                    raise
        # MEM parse data source or destination, addr base source and immediate
        if self.instr_tuple[INTFields.LABEL] in InstrLabel.LS:
            if self.instr_tuple[INTFields.DEST]:
                try:
                    self.dest = IntRegisterTable.registers[parsed_instr.pop(0)]
                except KeyError:
                    print("NameError: Invalid destination register")
                    raise
            else:
                try:
                    self.sources.append(IntRegisterTable.registers[parsed_instr.pop(0)])
                except KeyError:
                    print("NameError: Invalid source register")
                    raise
            parsed_instr = parsed_instr.pop(0).replace("(", " ").split()
            try:
                self.immediate = int(parsed_instr.pop(0))
            except ValueError:
                print("NameError: Invalid immediate")
                raise
            parsed_instr = parsed_instr.pop(0).split(")")[0]
            try:
                self.sources.append(IntRegisterTable.registers[parsed_instr])
            except KeyError:
                print("NameError: Invalid source register")
                raise
        # Branch fields
        if self.instr_tuple[INTFields.LABEL] is InstrLabel.BRANCH:
            for x in range(self.instr_tuple[INTFields.N_SOURCES]):
                try:
                    self.sources.append(IntRegisterTable.registers[parsed_instr.pop(0)])
                except KeyError:
                    print("NameError: Invalid source register")
                    raise
            self.branch_target = parsed_instr.pop(0)


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
