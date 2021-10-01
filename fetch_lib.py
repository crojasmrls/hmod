import salabim as sim
import Instr_lib as instr

class BasicInstrBlock:
    def __init__(self, name):
        self.name = name
        self.next_block = 'END'
        self.instr = []
    def add_instr(self, instr):
        self.instr.append(instr)
    def set_next_block(self, next_block):
        self.next_block = next_block
    def get_instr(self, index):
        return self.instr[index]

class InstrCache(sim.Component):
    """docstring for InstrCache"""
    def setup(self, program, env1, rob):
        self.program = program
        self.bb_dict = {}
        self.first_block = 'END'
        self.offset = 0
        self.bb_name = 'main'
        self.env = env1
        self.branch_taken = False
        self.rob = rob
        self.take_branch = False
    def read_program(self):
        with sim.ItemFile('../programs/'+self.program) as f:
            bb_nameprev = ''
            bb_name = ''
            instr_count = 0
            while True:
                try:
                    read_item = f.read_item()
                    if read_item[0] == ':':
                        instr_count = 0
                        bb_name = read_item[1:len(read_item)]
                        if len(self.bb_dict) > 0:
                            self.bb_dict[bb_nameprev].set_next_block(bb_name)
                        if len(self.bb_dict) == 0:
                            self.first_block = bb_name
                        self.bb_dict[bb_name] = BasicInstrBlock(bb_name)
                        bb_nameprev = bb_name
                    else:
                        instr = ''
                        while read_item != ':':
                            if instr == '':
                                instr = read_item
                            else:
                                instr = instr + ' ' + read_item
                            read_item = f.read_item()
                        self.bb_dict[bb_name].add_instr(instr)
                        instr_count = instr_count + 1
                except EOFError:
                    break
    def print_program(self):
        bb_name = self.first_block
        while (bb_name != 'END'):
            print(self.bb_dict[bb_name].name)
            for instr in self.bb_dict[bb_name].instr:
                print('    ' + instr)
            bb_name = self.bb_dict[bb_name].next_block
    def send_first_bb(self):
        return self.first_block
    def send_intrs(self, bb_name, offset):
        instr.Instr(fetch_unit=self)
        print(self.bb_dict[bb_name].instr[offset])
        self.rob.add_instr()
        #return self.bb_dict[bb_name].instr[offset]

    def change_pc(self, bb_name_branch):
        self.branch_taken = True
        self.next_inst = self.send_intrs(bb_name_branch, 0)


    
    def process(self):
       # while self.bb_name != 'END':
        while self.bb_name != 'END' or self.rob.count_inst != 0:
            if self.take_branch == False:
                #self.offset = self.offset + 1
                pass
            else:
                pass
            if self.bb_name == 'END':
                break
            else:
                self.next_inst = self.send_intrs(self.bb_name, self.offset)
            if self.offset == len(self.bb_dict[self.bb_name].instr) - 1:

                self.bb_name = self.bb_dict[self.bb_name].next_block
                self.offset = 0
                while(len(self.bb_dict[self.bb_name].instr)==0):
                    if self.bb_name == 'END':
                        break
                    self.bb_name = self.bb_dict[self.bb_name].next_block
            else:
                self.offset = self.offset + 1
            yield self.hold(1)


# class fetch_requestor(sim.Component):
#     def proccess(self):
#         request=Icache_request()
#         print(request.instr)
#         yield self.passivate


# class request(sim.Component):
#     def __init__(self, arg):
#         super(request, self).__init__()
#         self.arg = arg
#         