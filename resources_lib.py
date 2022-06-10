import salabim as sim
import reorderbuffer_lib as rob
import reg_file_lib as rf


class Resources:
    def __init__(self, fetch_width, physical_registers, int_alus, rob_entries, int_queue_slots, store_buffer_slots):
        # parameters
        self.fetch_width = fetch_width
        self.physical_registers = physical_registers
        self.int_alus = int_alus
        self.rob_entries = rob_entries
        self.int_queue_slots = int_queue_slots
        self.store_buffer_slots = store_buffer_slots
        # resources
        self.fetch_resource = sim.Resource('fetch_resource', capacity=self.fetch_width)
        self.int_units = sim.Resource('int_units', capacity=self.int_alus)
        self.int_queue = sim.Resource('int_queue', capacity=self.int_queue_slots)
        self.store_buffer = sim.Resource('store_buffer', capacity=self.store_buffer_slots)
        # self.h_units = sim.Resource('h_units', capacity=1) not implemented for now
        # instances
        self.RobInst = rob.ReorderBuffer(rob_entries=self.rob_entries)
        self.RegisterFileInst = rf.RegFile(physical_registers=self.physical_registers)
        # states
        self.decode_state = sim.State("decode_ready", value=True)
        self.finished = False
