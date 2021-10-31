import salabim as sim
import instr_lib as instr


class BasicInstrBlock:
    def __init__(self, name):
        self.name = name
        self.next_block = 'END'
        self.instr = []

    def add_instr(self, new_instr):
        self.instr.append(new_instr)

    def set_next_block(self, next_block):
        self.next_block = next_block

    def get_instr(self, index):
        return self.instr[index]


class InstrCache(sim.Component):
    """docstring for InstrCache"""
    def setup(self, program, env1, rob, int_queue, h_queue):
        self.program = program
        self.bb_dict = {}
        self.first_block = 'END'
        self.offset = 0
        self.bb_name = 'main'
        self.env = env1
        self.branch_taken = False
        self.rob = rob
        self.take_branch = False
        self.int_queue = int_queue
        self.h_queue = h_queue

    def read_program(self):
        with sim.ItemFile('../programs/'+self.program) as f:
            bb_name_prev = ''
            bb_name = ''
            instr_count = 0
            while True:
                try:
                    read_item = f.read_item()
                    if read_item[0] == ':':
                        instr_count = 0
                        bb_name = read_item[1:len(read_item)]
                        if len(self.bb_dict) > 0:
                            self.bb_dict[bb_name_prev].set_next_block(bb_name)
                        if len(self.bb_dict) == 0:
                            self.first_block = bb_name
                        self.bb_dict[bb_name] = BasicInstrBlock(bb_name)
                        bb_name_prev = bb_name
                    else:
                        instr_buf = ''
                        while read_item != ':':
                            if instr_buf == '':
                                instr_buf = read_item
                            else:
                                instr_buf = instr_buf + ' ' + read_item
                            read_item = f.read_item()
                        self.bb_dict[bb_name].add_instr(instr_buf)
                        instr_count = instr_count + 1
                except EOFError:
                    break

    def print_program(self):
        bb_name = self.first_block
        while bb_name != 'END':
            print(self.bb_dict[bb_name].name)
            for instr_aux in self.bb_dict[bb_name].instr:
                print('    ' + instr_aux)
            bb_name = self.bb_dict[bb_name].next_block

    def send_first_bb(self):
        return self.first_block

    def send_instr(self, bb_name, offset):
        instr.Instr(fetch_unit=self, instruction=self.bb_dict[bb_name].instr[offset], int_queue=self.int_queue, h_queue=self.h_queue)
        self.rob.add_instr()
        return self.bb_dict[bb_name].instr[offset]

    def change_pc(self, bb_name_branch):
        self.branch_taken = True
        self.next_inst = self.send_instr(bb_name_branch, 0)

    def process(self):
        while self.bb_name != 'END' or self.rob.count_inst != 0:
            if not self.take_branch:
                # self.offset = self.offset + 1
                pass
            else:
                pass
            if self.bb_name == 'END':
                break
            else:
                self.next_inst = self.send_instr(self.bb_name, self.offset)
            if self.offset == len(self.bb_dict[self.bb_name].instr) - 1:

                self.bb_name = self.bb_dict[self.bb_name].next_block
                self.offset = 0
                while len(self.bb_dict[self.bb_name].instr) == 0:
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
