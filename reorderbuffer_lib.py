import salabim as sim


class ReorderBuffer(sim.Component):
    def setup(self, rob_entries):
        self.rob_entries = rob_entries
        self.rob_resource = sim.Resource('rob_resource', capacity=self.rob_entries)
        self.count_inst = 0

    def instr_end(self):
        self.count_inst = self.count_inst-1

    def add_instr(self):
        self.count_inst = self.count_inst + 1
