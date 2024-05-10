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
    arg_registers = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]


class InstrLabel(Flag):
    INT = auto()
    FP = auto()
    HILAR = auto()
    CALL = auto()
    LOAD = auto()
    STORE = auto()
    BRANCH = auto()
    JALR = auto()
    CTRL = BRANCH | JALR
    LS = LOAD | STORE
    ARITH_INT = INT | CTRL
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
    def exec_andbit(instr):
        if instr.decoded_fields.instr_tuple[INTFields.IMMEDIATE]:
            instr.p_dest.value = instr.p_sources[0].value & ExeFuncts.sing_extend(
                instr.decoded_fields.immediate, 12
            )
        elif len(instr.decoded_fields.sources) == 2:
            instr.p_dest.value = instr.p_sources[0].value & instr.p_sources[1].value

    @staticmethod
    def exec_sub(instr):
        instr.p_dest.value = instr.p_sources[0].value - instr.p_sources[1].value

    @staticmethod
    def exec_sext(instr):
        instr.p_dest.value = ExeFuncts.sing_extend(
            instr.p_sources[0].value,
            instr.decoded_fields.instr_tuple[INTFields.N_BYTES] * 8,
        )

    @staticmethod
    def exec_mul(instr):
        instr.p_dest.value = instr.p_sources[0].value * instr.p_sources[1].value

    @staticmethod
    def exec_lui(instr):
        instr.p_dest.value = instr.decoded_fields.immediate << 12

    @staticmethod
    def exec_sll(instr):
        if instr.decoded_fields.instr_tuple[INTFields.IMMEDIATE]:
            instr.p_dest.value = instr.p_sources[0].value << (
                instr.decoded_fields.immediate & 0x1F
            )
        else:
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
    def exec_gequ(instr):
        instr.branch_result = instr.p_sources[0].value >= instr.p_sources[1].value

    @staticmethod
    def exec_equz(instr):
        instr.branch_result = instr.p_sources[0].value == 0

    @staticmethod
    def exec_less(instr):
        instr.branch_result = instr.p_sources[0].value < instr.p_sources[1].value

    @staticmethod
    def exec_lequ(instr):
        instr.branch_result = instr.p_sources[0].value <= instr.p_sources[1].value

    @staticmethod
    def exec_true(instr):
        instr.branch_result = True

    @staticmethod
    def exec_nop(instr):
        pass

    @staticmethod
    def sing_extend(value, bits):
        mask = (1 << bits) - 1
        masked_value = value & mask
        if masked_value & (1 << (bits - 1)):
            return masked_value | (-1 << 12)
        else:
            return masked_value


class InstructionTable:
    # Table of tuples
    # fmt: off
    Instructions = \
        {
            # INT     label               destination n_sources immediate pipelined latency computation          n_bytes
            'add':    (InstrLabel.INT,    True,       2,        False,    True,     1,      ExeFuncts.exec_add),
            'sub':    (InstrLabel.INT,    True,       2,        False,    True,     1,      ExeFuncts.exec_sub),
            'mul':    (InstrLabel.INT,    True,       2,        False,    True,     2,      ExeFuncts.exec_mul),
            'sll':    (InstrLabel.INT,    True,       2,        False,    True,     1,      ExeFuncts.exec_sll),
            'mv':     (InstrLabel.INT,    True,       1,        False,    True,     1,      ExeFuncts.exec_add),
            'sext.w': (InstrLabel.INT,    True,       1,        False,    True,     1,      ExeFuncts.exec_sext, 4),
            'addi':   (InstrLabel.INT,    True,       1,        True,     True,     1,      ExeFuncts.exec_add),
            'addiw':  (InstrLabel.INT,    True,       1,        True,     True,     1,      ExeFuncts.exec_add),
            'andi':   (InstrLabel.INT,    True,       1,        True,     True,     1,      ExeFuncts.exec_andbit),
            'li':     (InstrLabel.INT,    True,       0,        True,     True,     1,      ExeFuncts.exec_add),
            'lui':    (InstrLabel.INT,    True,       0,        True,     True,     1,      ExeFuncts.exec_lui),
            'slli':   (InstrLabel.INT,    True,       1,        True,     True,     1,      ExeFuncts.exec_sll),
            'slt':    (InstrLabel.INT,    True,       2,        False,    True,     1,      ExeFuncts.exec_slt),
            'nop':    (InstrLabel.INT,    False,      0,        False,    True,     1,      ExeFuncts.exec_add),
            # MEM     label               destination n_sources immediate pipelined latency computation          n_bytes
            'sd':     (InstrLabel.STORE,  False,      2,        True,     True,     1,      ExeFuncts.exec_addr, 8),
            'ld':     (InstrLabel.LOAD,   True,       1,        True,     True,     1,      ExeFuncts.exec_addr, 8),
            # Branch  label               destination n_sources immediate pipelined latency computation
            'bne':    (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_nequ),
            'beq':    (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_equ),
            'bge':    (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_gequ),
            'bltu':   (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_less),
            'ble':    (InstrLabel.BRANCH, False,      2,        False,    True,     1,      ExeFuncts.exec_lequ),
            'beqz':   (InstrLabel.BRANCH, False,      1,        False,    True,     1,      ExeFuncts.exec_equz),
            'j':      (InstrLabel.BRANCH, False,      0,        False,    True,     1,      ExeFuncts.exec_true),
            'jr':     (InstrLabel.JALR,   False,      1,        False,    True,     1,      ExeFuncts.exec_true),
            # HILAR   label               destination n_sources immediate pipelined latency computation
            'new':    (InstrLabel.HILAR,  False,      0,        False,    True,     1,      ExeFuncts.exec_nop),
            # CALLS   label               destination n_sources immediate pipelined latency computation
            'call':   (InstrLabel.CALL,   False,      8,        False,    True,     1,      ExeFuncts.exec_nop),
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
        self.call_code = None
        self.is_magic = False
        self.set_fields()

    def set_fields(self):
        parsed_instr = self.instruction.replace(",", " ").split()
        tag = parsed_instr.pop(0)
        try:
            self.instr_tuple = InstructionTable.Instructions[tag]
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
            if tag == "addi" and self.dest == 0:
                self.is_magic = True

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
        # JALR fields
        if self.instr_tuple[INTFields.LABEL] is InstrLabel.JALR:
            for x in range(self.instr_tuple[INTFields.N_SOURCES]):
                try:
                    self.sources.append(IntRegisterTable.registers[parsed_instr.pop(0)])
                except KeyError:
                    print("NameError: Invalid source register")
                    raise
        # System calls
        if self.instr_tuple[INTFields.LABEL] is InstrLabel.CALL:
            self.call_code = parsed_instr.pop(0)
            self.sources = [
                IntRegisterTable.registers[i] for i in IntRegisterTable.arg_registers
            ]


class Calls:
    # call functions
    @staticmethod
    def call_functions(instr):
        return {
            "printf": lambda: Calls.printf_call(
                instr.p_sources.copy(), instr.pe.DataCacheInst
            ),
            "puts": lambda: Calls.puts_call(
                instr.p_sources.copy(), instr.pe.DataCacheInst
            ),
            "putchar": lambda: Calls.putschar_call(
                instr.p_sources.copy(), instr.pe.DataCacheInst
            ),
        }.get(instr.decoded_fields.call_code, lambda: None)()

    @staticmethod
    def puts_call(sources, data_cache):
        print(Calls.replace_end_line(data_cache.dc_load(sources[0].value)))

    @staticmethod
    def putschar_call(sources, data_cache):
        print(chr(sources[0].value), end="")

    @staticmethod
    def printf_call(sources, data_cache):
        text = data_cache.dc_load(sources.pop(0).value)
        while text.count("%d") != 0:
            text = text.replace("%d", str(sources.pop(0).value), 1)
        print(Calls.replace_end_line(text), end="")

    @staticmethod
    def replace_end_line(text):
        return text[::-1].replace("n\\", "", 1)[::-1].replace("\\n", "\n")


class Magics:
    # call functions
    @staticmethod
    def magic_functions(instr):
        return {
            1: lambda: Magics.perf_count_start(
                instr.pe.performance_counters, instr.instr_id
            ),
            2: lambda: Magics.perf_count_stop(
                instr.pe.performance_counters, instr.instr_id
            ),
            3: lambda: Magics.perf_count_reset(
                instr.pe.performance_counters, instr.instr_id
            ),
        }.get(instr.decoded_fields.immediate, lambda: None)()

    @staticmethod
    def perf_count_start(performance_counters, instr_id):
        performance_counters.CountCtrl.enable()
        if performance_counters.GCInst.ispassive():
            performance_counters.GCInst.activate()
        print("Performance counters have started with instruction id: " + str(instr_id))

    @staticmethod
    def perf_count_stop(performance_counters, instr_id):
        performance_counters.CountCtrl.disable()
        print("Performance counters have stopped with instruction id: " + str(instr_id))

    @staticmethod
    def perf_count_reset(performance_counters, instr_id):
        performance_counters.ECInst.reset_counters()
        print("Performance counters have reset with instruction id: " + str(instr_id))


# # Not used

# # List of objects that will be executed by the HILAR queue


# class HilarObjects:
#     objects = ['_b_node_']
# # List of objects that will be executed by the Integer Queue


# class IntObjects:
#     objects = ['_array_', '_int_', '_bool_', '_byte_']


# class HilarMethods:
#     methods = ['insert', 'search', 'get_index', 'print_data']
