import salabim as sim

class Instr(sim.Component):
    def setup(self, fetch_unit, instr):
        self.fetch_unit = fetch_unit
        self.type = 'none'
        self.instr = instr
        self.miss_branch_prediction = False
    def proccess(self):
        print(self.instr)
        self.state = 'decode'
        yield self.hold(1)#Decode
        if self.instr.split()[0] == 'new':
            for obj in HilarObjects.objects:
                if self.instr.split()[1] == obj:
                    self.type = 'HILAR'
            for obj in IntObjects.objects:
                if self.instr.split()[1] == obj:
                    self.type = 'INT'
        if self.instr.split()[0] == 'call':
            self.type = 'CALL'
        else:
            for hilar_method in HilarMethods.methods:
                if self.instrs.split()[0] == hilar_method:
                    self.type = 'HILAR'
            for int_instr in IntegerISA.instrs:
                if self.instrs.split()[0] == int_instr:
                    self.type = 'INT'
        #Verificar espacio en cola
        if self.type == 'INT':
            self.enter(IntQueue)
        elif self.type == 'HILAR':
            self.enter(HQueue)
        self.state = 'enqued'
        yield self.passivate()
        #Check dependencies, wake up logic
        #selec unit, esperar a que la unidad este libre, issue logic
        #esperar, Tiempo de ejecucion.
        if self.type == 'BRANCH' and self.miss_branch_prediction:
            self.fetch_unit.change_pc(self.correct_bb_name)
            #flush pipeline
            #elf.fetch_unit_
        #liberar la unidad
        self.fetch_unit.rob.instr_end()

    def flush(self):
        self.fetch_unit.rob.instr_end()


#List of objects that will be executed by the HILAR queue
class HilarObjects:
    objects = ['_b_node_']
#List of objects that will be executed by the Integer Queue
class IntObjects:
    objects = ['_array_','_int_', '_bool_', '_byte_']

class IntegerISA:##It also includes pseudo assembly
    instrs = ['blt','bneq', 'j', 'assign']

class HilarMethods:
    """docstring for HilarMethods"""
    methods = ['insert','search', 'get_index', 'print_data']
class Calls:
    calls = ['cout']
