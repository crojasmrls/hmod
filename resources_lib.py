import salabim as sim
import reorderbuffer_lib as rob
import reg_file_lib as rf


class Resources(sim.Component):
    def setup(self, fetch_width, physical_registers, int_alus, rob_entries, int_queue_slots):
        # parameters
        self.fetch_width = fetch_width
        self.physical_registers = physical_registers
        self.int_alus = int_alus
        self.rob_entries = rob_entries
        self.int_queue_slots = int_queue_slots
        # resources
        self.fetch_resource = sim.Resource('fetch_resource1', capacity=self.fetch_width)
        self.int_units = sim.Resource('int_units', capacity=self.int_alus)
        self.int_queue = sim.Resource('int_queue', capacity=int_queue_slots)
        # self.h_units = sim.Resource('h_units', capacity=1) not implemented for now
        # instances
        self.RobInst = rob.ReorderBuffer(rob_entries=self.rob_entries)
        self.RegisterFileInst = rf.RegFile(physical_registers=self.physical_registers)
        # states
        self.decode_state = sim.State("decode_ready", value=True)

    def process(self):
        while True:
            yield self.hold(1)
