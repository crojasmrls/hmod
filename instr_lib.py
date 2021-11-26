import salabim as sim


class Instr(sim.Component):
    def setup(self, pe, instruction, fetch_unit):
        self.fetch_unit = fetch_unit
        self.type = 'none'
        self.instruction = instruction
        self.miss_branch_prediction = False
        self.pe = pe
        self.correct_bb_name = ''
        self.has_dest = False
        self.Physical_register = self.pe.register_file.get_reg(0)
        self.virtual_dest = 0
        self.physical_dest = self.pe.register_file.rat[0]
        self.sources = [self.pe.register_file.rat[0], self.pe.register_file.rat[0]]
        self.pipelined=False
        self.latency=1

    def process(self):
        print(self.instruction)
        self.state = 'decode'
        yield self.hold(1)  # Decode
        if self.instruction.split()[0] == 'new':
            for obj in HilarObjects.objects:
                if self.instruction.split()[1] == obj:
                    self.type = 'HILAR'
            for obj in IntObjects.objects:
                if self.instruction.split()[1] == obj:
                    self.type = 'INT'
        if self.instruction.split()[0] == 'call':
            self.type = 'CALL'
        else:
            for hilar_method in HilarMethods.methods:
                if self.instruction.split()[0] == hilar_method:
                    self.type = 'HILAR'
            for int_instr in IntegerISA.instrs:
                if self.instruction.split()[0] == int_instr:
                    self.type = 'INT'
        self.sources = self.set_sources()
        self.fetch_unit.release((self.fetch_unit.fetch_resource, 1))
        yield self.wait(self.pe.decode_state, urgent=True)
        self.pe.decode_state.set(False)
        if self.type == 'INT':
        #   self.enter(self.int_queue)
            if self.has_dest:
                yield self.request(self.pe.reg_file.FRL_resource)
                self.physical_dest = self.Physical_register(False)
                # self.old_dest = self.pe.reg_file.get_reg(self.virtual_reg)
                self.pe.reg_file.set_reg(self.virtual_dest, self.physical_dest)

            self.pe.decode_state.set(True)
            for x in self.sources:
                yield self.wait(x.reg_state)

            yield self.request(self.pe.int_units)
            self.execute()
            if self.pipelined:
                yield self.hold(1)
                self.release(self.pe.int_units)
                yield self.hold(self.latency)
                self.physical_dest.reg_state.set(True)
            else:
                yield self.hold(self.latency)
                self.physical_dest.reg_state.set(True)
                self.release(self.pe.int_units)

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
        return self.sources

    def execute(self):
        pass
# List of objects that will be executed by the HILAR queue

class HilarObjects:
    objects = ['_b_node_']
# List of objects that will be executed by the Integer Queue


class IntObjects:
    objects = ['_array_', '_int_', '_bool_', '_byte_']


class IntegerISA:  # It also includes pseudo assembly
    instrs = ['blt', 'bneq', 'j', 'assign', 'li', 'add']


class HilarMethods:
    """docstring for HilarMethods"""
    methods = ['insert', 'search', 'get_index', 'print_data']


class Calls:
    calls = ['cout']
