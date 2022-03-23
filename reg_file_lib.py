import salabim as sim


class RegFile:
    def __init__(self, physical_registers):
        self.FRL_resource = sim.Resource('FRL_resource', capacity=physical_registers-32)
        self.rat = [PhysicalRegister(state=True, value=i) for i in range(32)]

    def set_reg(self, arch_reg, physical_reg):
        self.rat[arch_reg] = physical_reg

    def get_reg(self, arch_reg):
        return self.rat[arch_reg]


class PhysicalRegister:
    def __init__(self, state=False, value=0):
        self.reg_state = sim.State("ready_bit", value=state)
        self.value = value
