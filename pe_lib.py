import salabim as sim
import reorderbuffer_lib as rob
import fetch_lib as fetch
import reg_file_lib as rf


class PE(sim.Component):
    def setup(self, fetch_width, physical_registers, int_alus, rob_entries, program):
        self.fetch_width = fetch_width
        self.physical_registers = physical_registers
        self.int_alus = int_alus
        self.rob_entries = rob_entries
        self.program = program
        self.decode_state = sim.State("decode_ready", value=True)
        self.int_units = sim.Resource('int_units', capacity=3)
        self.h_units = sim.Resource('h_units', capacity=1)
        self.register_file = rf.RegFile(physical_registers=self.physical_registers)
        self.Rob = rob.ReorderBuffer(rob_entries=self.rob_entries)
        self.InstrCache_inst = fetch.InstrCache(program=program, rob=self.Rob, pe=self)
