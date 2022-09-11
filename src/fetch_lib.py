import salabim as sim
import instr_lib as instr
# from watchpoints import watch


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
    def setup(self, program, resources, thread_id, konata_signature):
        self.program = program
        self.bb_dict = {}
        self.first_block = 'END'
        self.offset = 0
        self.bb_name = 'main'
        self.branch_taken = False
        self.take_branch = False
        self.resources = resources
        self.thread_id = thread_id
        self.konata_signature = konata_signature
        self.instr_id = 0
        # watch(self.fetch_resource.claimed_quantity.value)

    def read_program(self):
        bb_name_prev = ''
        bb_name = ''
        instr_count = 0
        f = open('../programs/' + self.program, "r")
        lines = f.readlines()
        line_number = 0
        for line in lines:
            line_number += 1
            line = line.replace("\n", "")
            line = line.split('#')[0]
            # If the line is a code segment tag
            if line.find(':') != -1:
                instr_count = 0
                # Remove the code segment tag indicator
                bb_name = line.split(':')[0]
                if len(bb_name) != 0:
                    if len(self.bb_dict) > 0:
                        self.bb_dict[bb_name_prev].set_next_block(bb_name)
                    if len(self.bb_dict) == 0:
                        self.first_block = bb_name
                    self.bb_dict[bb_name] = BasicInstrBlock(bb_name)
                    bb_name_prev = bb_name
            else:
                if len(line.replace(" ", "")) != 0:
                    self.bb_dict[bb_name].add_instr((line, line_number))
                    instr_count = instr_count + 1

    def print_program(self):
        bb_name = self.first_block
        while bb_name != 'END':
            print(self.bb_dict[bb_name].name)
            for instr_aux in self.bb_dict[bb_name].instr:
                print('    ' + instr_aux)
            bb_name = self.bb_dict[bb_name].next_block

    def send_first_bb(self):
        return self.first_block

    def create_instr(self, bb_name, offset):
        self.instr_id += 1
        new_instr = instr.Instr(instruction=self.bb_dict[bb_name].instr[offset][0],
                                line_number=self.bb_dict[bb_name].instr[offset][1],
                                resources=self.resources, thread_id=self.thread_id,
                                instr_id=self.instr_id,
                                konata_signature=self.konata_signature, fetch_unit=self)
        self.konata_signature.new_instr(self.thread_id, self.instr_id, self.bb_dict[bb_name].instr[offset][1],
                                        self.bb_dict[bb_name].instr[offset][0])
        self.next_inst = self.bb_dict[bb_name].instr[offset]
        self.resources.RobInst.add_instr(new_instr)

    def change_pc(self, bb_name_branch):
        self.branch_taken = True
        yield from self.create_instr(self.bb_name, self.offset)

    def release_rob(self):
        self.release((self.resources.RobInst.rob_resource, 1))

    def release_fetch(self):
        self.release((self.resources.fetch_resource, 1))

    def process(self):
        while self.bb_name != 'END' or self.resources.RobInst.count_inst != 0:
            yield self.request(self.resources.fetch_resource)
            if not self.take_branch:
                # self.offset = self.offset + 1
                pass
            else:
                pass
            if self.bb_name == 'END':
                self.resources.finished = True
                yield self.passivate()
            else:
                yield self.wait(self.resources.decode_state)
                yield self.request(self.resources.RobInst.rob_resource)
                self.create_instr(self.bb_name, self.offset)
                # self.next_inst = self.send_instr(self.bb_name, self.offset)
            if self.offset == len(self.bb_dict[self.bb_name].instr) - 1:

                self.bb_name = self.bb_dict[self.bb_name].next_block
                self.offset = 0
                while len(self.bb_dict[self.bb_name].instr) == 0:
                    if self.bb_name == 'END':
                        self.resources.finished = True
                        yield self.passivate()
                    self.bb_name = self.bb_dict[self.bb_name].next_block
            else:
                self.offset = self.offset + 1
            # yield self.hold(1)
