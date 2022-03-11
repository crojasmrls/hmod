import salabim as sim


class ReorderBuffer:
    def __init__(self, rob_entries):
        self.rob_entries = rob_entries
        self.rob_resource = sim.Resource('rob_resource', capacity=self.rob_entries)
        self.rob_queue = sim.Queue("rob_queue")
        self.count_inst = 0

    def instr_end(self, instruction):
        return instruction != self.rob_queue.head()

    def add_instr(self, instruction):
        # yield self.request(self.rob_resource)
        self.count_inst = self.count_inst + 1
        self.rob_queue.add(instruction)

    def release_instr(self):
        self.count_inst = self.count_inst - 1
        self.rob_queue.pop()