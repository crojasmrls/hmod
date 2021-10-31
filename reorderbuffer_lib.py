class ReorderBuffer:
    def __init__(self):
        self.instrs = []
        self.count_inst = 0

    def instr_end(self):
        self.count_inst = self.count_inst-1

    def add_instr(self):
        self.count_inst = self.count_inst + 1
