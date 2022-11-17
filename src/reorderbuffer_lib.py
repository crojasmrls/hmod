import salabim as sim


class ReorderBuffer:
    def __init__(self, rob_entries):
        self.rob_entries = rob_entries
        self.rob_resource = sim.Resource('rob_resource', capacity=self.rob_entries)
        self.rob_list = []

    def instr_end(self, instr_id):
        return instr_id != self.rob_list[0][1]

    def add_instr(self, instr, instr_id):
        # yield self.request(self.rob_resource)
        self.rob_list.append((instr, instr_id))

    def release_instr(self):
        self.rob_list.pop(0)

    def recovery_rob(self, instr_id):
        instr = self.rob_list[-1]
        instr[0].resources.decode_state.set(True)
        while instr[1] != instr_id:
            self.rob_list.pop()
            self.release_resources(instr[0])
            instr = self.rob_list[-1]

    @staticmethod
    def release_resources(instr):
        instr.konata_signature.retire_instr(instr.thread_id, instr.instr_id, True)
        for resource in instr.claimed_resources():
            instr.release((resource, 1))
        instr.cancel()
