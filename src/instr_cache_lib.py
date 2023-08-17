import random

class BasicInstrBlock:
    def __init__(self, name):
        self.name = name
        self.next_block = 'END'
        # Basic block instruction list
        self.instr = []

    def add_instr(self, new_instr):
        self.instr.append(new_instr)

    def set_next_block(self, next_block):
        self.next_block = next_block

    def get_instr(self, index):
        return self.instr[index]

class InstrCache:
    def __init__(self):
        self.bb_dict = {}

    def add_bb(self, bb_name, bb_name_prev):
        self.bb_dict[bb_name] = BasicInstrBlock(bb_name)
        if len(self.bb_dict) > 0:
            self.bb_dict[bb_name_prev].set_next_block(bb_name)

    def add_instr(self, bb_name, new_instr):
        self.bb_dict[bb_name].add_instr(new_instr)
