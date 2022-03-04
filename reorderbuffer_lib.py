import salabim as sim


class ReorderBuffer(sim.Component):
    def setup(self, rob_entries):
        self.rob_entries = rob_entries
        self.rob_resource = sim.Resource('rob_resource', capacity=self.rob_entries)
        self.rob_queue = sim.Queue("rob_queue")
        self.count_inst = 0

    def instr_end(self, instruction):
        while (instruction != self.rob_queue.head()):
            yield self.hold(1)
        self.count_inst = self.count_inst-1
        self.rob_queue.pop()
        self.rob_resource.release(1)

    def add_instr(self, instruction):
        yield self.request(self.rob_resource)
        self.count_inst = self.count_inst + 1
        self.rob_queue.add(instruction)

    def process(self):
         while True:
            yield self.hold(1)
