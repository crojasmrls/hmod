import salabim as sim
from enum import Enum


class Instr(sim.Component):
    def setup(self, pe, instruction, fetch_unit):
        self.fetch_unit = fetch_unit
        self.type = 'none'
        self.instruction = instruction
        self.miss_branch_prediction = False
        self.pe = pe
        self.correct_bb_name = ''
        self.has_dest = False
        self.has_Src1 = False
        self.has_Src2 = False
        self.Physical_register = self.pe.register_file.get_reg(0)
        self.virtual_dest = 0
        self.physical_dest = self.pe.register_file.rat[0]
        self.sources = [self.pe.register_file.rat[0], self.pe.register_file.rat[0]]
        self.pipelined=False
        self.latency=1
        self.set_fields ()

    def process(self):
        print(self.instruction)
        self.state = 'decode'
        yield self.hold(1)  # Decode
        self.sources = self.set_sources()
        self.fetch_unit.release((self.fetch_unit.fetch_resource, 1))
        yield self.wait(self.pe.decode_state, urgent=True)
        self.pe.decode_state.set(False)
        if self.type == 'INT': # Put enum value
            yield self.request(self.pe.int_queue)
        #   self.enter(self.int_queue)
            if self.has_dest:
                yield self.request(self.pe.reg_file.FRL_resource)
                self.physical_dest = self.Physical_register(False)
                self.old_dest = self.pe.reg_file.get_reg(self.virtual_reg)
                self.pe.reg_file.set_reg(self.virtual_dest, self.physical_dest) 

            self.pe.decode_state.set(True)
            yield self.hold(1) # Hold for dispath stage
            for x in self.sources:
                yield self.wait(x.reg_state)
            yield self.request(self.pe.int_units,1)
            self.execute()
            self.release(self.pe.int_queue,1)
            if self.pipelined:
                yield self.hold(1)
                self.release(self.pe.int_units,1)
                yield self.hold(self.latency-1)
                self.physical_dest.reg_state.set(True)
            else:
                yield self.hold(self.latency)
                self.physical_dest.reg_state.set(True)
                self.release(self.pe.int_units,1)

            yield from self.pe.Rob.instr_end(self)




        elif self.type == 'HILAR':
            # self.enter(self.h_queue)
            yield self.request(self.pe.h_units)
            self.pe.decode_state.set(True)
        self.state = 'enqued'
        yield self.passivate()
        if self.type == 'BRANCH' and self.miss_branch_prediction:
            self.fetch_unit.change_pc(self.correct_bb_name)
            # flush pipeline
            # elf.fetch_unit_
        # liberar la unidad
        self.fetch_unit.rob.instr_end()

    def flush(self):
        self.fetch_unit.rob.instr_end()

    def set_sources(self):
        x = self.instruction.split(",")
        for int_instr in HasSrc1.instrs:
            if self.instruction.split()[0] == int_instr:
                y = x[0].split()[1]
                register = IntRegisterTable.registers[y]
                self.sources = [self.pe.register_file.rat[register]]
        for int_instr in HasSrc2.instrs:

            self.sources.append(self.pe.register_file.rat[register])


    def execute(self):
        pass
        # set the execution value
        # calculate the result

    def set_fields(self):
        # This determines if it is an object creation or a new instruction.
        # if self.instruction.split()[0] == 'new':
        #     for obj in HilarObjects.objects:
        #         if self.instruction.split()[1] == obj:
        #             self.type = 'HILAR'
        #     for obj in IntObjects.objects:
        #         if self.instruction.split()[1] == obj:
        #             self.type = 'INT'
        # if self.instruction.split()[0] == 'call':
        #     self.type = 'CALL'
        # else:
        #     for hilar_method in HilarMethods.methods:
        #         if self.instruction.split()[0] == hilar_method:
        #             self.type = 'HILAR'
        #     for int_instr in IntegerISA.instrs:
        #         if self.instruction.split()[0] == int_instr:
        #             self.type = 'INT'
        #             self.set_sources()
        #             for int_instr_dest in HasSrc1.instrs:
        #                 if self.instruction.split()[0] == int_instr_dest:
        #                     self.has_dest = True
        # Change for loops by hash table with the decoded intrs
        ints_touple = IntRegisterTable[self.instruction.split()[0]]


# List of objects that will be executed by the HILAR queue
class HilarObjects:
    objects = ['_b_node_']
# List of objects that will be executed by the Integer Queue


class IntObjects:
    objects = ['_array_', '_int_', '_bool_', '_byte_']


class IntegerISA:  # It also includes pseudo assembly
    instrs = ['blt', 'bneq', 'j', 'assign', 'li', 'add', 'nop']

class HasSrc1:  # All intructions that have destination
    instrs = ['assign', 'li', 'add']

class HasSrc2:  # All intructions that have destination
    instrs = ['add']


class HasDest:
    instrs = ['']


class IntRegisterTable:  # Register map of the micro architecture
    registers = {'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3,
                 'tp': 4, 't0': 5, 't1': 6, 't2': 7,
                 's0:': 8, 's1': 9, 'a0': 10, 'a1': 11,
                 'a2': 12, 'a3': 13, 'a4': 14, 'a5': 15,
                 'a6': 16, 'a7': 17, 's2': 18, 's3': 19,
                 's4': 20, 's5': 21, 's6': 22, 's7': 23,
                 's8': 24, 's9': 25, 's10': 26, 's11': 27,
                 't3': 28, 't4': 29, 't5': 30, 't6': 31}
class InstLabel(Enum):
    INT = 0
    FP = 1
    HILAR = 3
    CALL = 4

class ALUCode(Enum):
    OR = 0
    ADD = 1
    SUB = 2
    MULT = 3


class Insrtruction_Table: # (Instruction label, n_sources, n_dests, alu_op label)
    Instructions ={'add': (InstLabel.INT, 2, 1, ALUCode.ADD),
                   'li': (InstLabel.INT,1,1,ALUCode.ADD),
                   'nop': (InstLabel.INT,0,0,ALUCode.ADD),
                   'new': (InstLabel.HILAR)
                   }


class HilarMethods:
    methods = ['insert', 'search', 'get_index', 'print_data']


class Calls:
    calls = ['cout']
