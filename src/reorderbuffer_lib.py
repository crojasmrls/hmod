import salabim as sim


class ReorderBuffer:
    def __init__(self, rob_entries):
        self.rob_entries = rob_entries
        self.rob_resource = sim.Resource('rob_resource', capacity=self.rob_entries)
        self.rob_list = []
        self.rob_queue = sim.Queue("rob_queue")

    def instr_end(self, instruction):
        return instruction != self.rob_queue.head()

    def add_instr(self, instr, instr_id):
        # yield self.request(self.rob_resource)
        self.rob_list.append((instr, instr_id))
        instr.enter("rob_queue")

    def release_instr(self):
        self.rob_list.pop(0)
        self.rob_queue.pop()

    def recovery_rob(self, instr_id):
        instr = self.rob_list.pop()
        while instr[1] != instr_id:
            self.release_resources(instr[0])
            instr = self.rob_list.pop()

    @staticmethod
    def release_resources(instr):
        instr.leave("rob_queue")
