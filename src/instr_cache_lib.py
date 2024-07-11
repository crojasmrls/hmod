class BasicInstrBlock:
    def __init__(self, name):
        self.name = name
        self.next_block = "END"
        # Basic block instruction list
        self.instructions = []

    def add_instr(self, new_instr):
        self.instructions.append(new_instr)

    def set_next_block(self, next_block):
        self.next_block = next_block

    def get_instr(self, offset):
        return self.instructions[offset]


class InstrCache:
    def __init__(self):
        self.bb_dict = {}
        self.first_block = ""

    def add_bb(self, bb_name, bb_name_prev):
        if len(self.bb_dict) > 0:
            self.bb_dict[bb_name_prev].set_next_block(bb_name)
        if len(self.bb_dict) == 0:
            self.first_block = bb_name
        self.bb_dict[bb_name] = BasicInstrBlock(bb_name)

    def del_bb(self, bb_name, bb_name_prev):
        self.bb_dict[bb_name_prev].set_next_block(self.get_next_block(bb_name))
        del self.bb_dict[bb_name]

    def add_instr(self, bb_name, new_instr):
        self.bb_dict[bb_name].add_instr(new_instr)

    def get_instr(self, bb_name, offset):
        return self.bb_dict[bb_name].get_instr(offset)

    def get_next_block(self, bb_name):
        return self.bb_dict[bb_name].next_block

    def get_block_len(self, bb_name):
        return len(self.bb_dict[bb_name].instructions)

    def print_program(self):
        bb_name = self.first_block
        while bb_name != "END":
            print(self.bb_dict[bb_name].name)
            for instr in self.bb_dict[bb_name].instructions:
                print("    " + instr[0])
            bb_name = self.bb_dict[bb_name].next_block

    def get_first_bb(self):
        return self.first_block
