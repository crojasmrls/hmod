import salabim as sim


class RegFile:
    def __init__(self, physical_registers):
        self.FRL_resource = sim.Resource(
            "FRL_resource", capacity=physical_registers - 32
        )
        self.rat = [PhysicalRegister(state=True, value=i) for i in range(32)]
        self.rat_stack = []
        self.dummy_reg = PhysicalRegister(state=False, value=0)

    def set_reg(self, arch_reg, physical_reg):
        self.rat[arch_reg] = physical_reg

    def get_reg(self, arch_reg):
        return self.rat[arch_reg]

    def push_rat(self, instr):
        self.rat_stack.append((self.rat.copy(), instr))

    def recovery_rat(self, recovery_instr):
        shadow_rat = self.rat_stack.pop()
        while shadow_rat[1] != recovery_instr:
            shadow_rat = self.rat_stack.pop()
        self.rat = shadow_rat[0].copy()

    def release_shadow_rat(self, instr):
        for shadow_rat in self.rat_stack:
            if shadow_rat[1] == instr:
                self.rat_stack.remove(shadow_rat)
                break

    def print_register_file(self):
        for i, register in enumerate(self.rat, start=0):
            print(i, ":", register.value)


class PhysicalRegister:
    def __init__(self, state=False, value=0):
        self.reg_state = sim.State("ready_bit", value=state)
        self.value = value
