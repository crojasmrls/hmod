import salabim as sim
import rv64uih_lib as dec


class ReorderBuffer:
    def __init__(self, rob_entries):
        self.rob_entries = rob_entries
        self.rob_resource = sim.Resource('rob_resource', capacity=self.rob_entries)
        self.rob_list = []

    def instr_end(self, instr):
        return instr != self.rob_list[0]

    def instr_next_end(self, instr):
        if instr == self.rob_list[0]:
            return False
        elif instr == self.rob_list[1]:
            return False
        else:
            return True

    def store_next2commit(self):
        try:
            for x in range(1, 2):
                if self.rob_list[x].instr_tuple[dec.INTFields.LABEL] == dec.InstrLabel.STORE:
                    return True
            return False
        except IndexError:
            return False

    def add_instr(self, instr):
        # yield self.request(self.rob_resource)
        self.rob_list.append(instr)

    def release_instr(self):
        self.rob_list.pop(0)

    def recovery_rob(self, recovery_instr):
        head_instr = self.rob_list[-1]
        while head_instr != recovery_instr:
            self.rob_list.pop()
            self.release_resources(head_instr)
            head_instr = self.rob_list[-1]

    @staticmethod
    def release_resources(instr):
        instr.konata_signature.retire_instr(instr.thread_id, instr.instr_id, True)
        for resource in instr.claimed_resources():
            instr.release((resource, 1))
        instr.fetch_unit.release_fetch()
        instr.cancel()
