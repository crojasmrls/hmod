import salabim as sim
import reorderbuffer_lib as rob
import reg_file_lib as rf
import lsq_lib as lsq
import data_cache_lib as dc


class Resources:
    def __init__(self, fetch_width, physical_registers, int_alus, rob_entries, int_queue_slots, lsu_slots, brob_entries):
        # parameters
        self.fetch_width = fetch_width
        self.physical_registers = physical_registers
        self.int_alus = int_alus
        self.rob_entries = rob_entries
        self.int_queue_slots = int_queue_slots
        self.lsu_slots = lsu_slots
        self.brob_entries = brob_entries
        # resources
        self.fetch_resource = sim.Resource('fetch_resource', capacity=self.fetch_width)
        self.int_units = sim.Resource('int_units', capacity=self.int_alus)
        self.int_queue = sim.Resource('int_queue', capacity=self.int_queue_slots)
        self.LoadStoreQueueInst = lsq.LoadStoreQueue(lsu_slots=self.lsu_slots)
        self.DataCacheInst = dc.DataCache()
        self.brob_resource = sim.Resource('brob_resource', capacity=self.brob_entries)
        # self.h_units = sim.Resource('h_units', capacity=1) not implemented for now
        # instances
        self.RobInst = rob.ReorderBuffer(rob_entries=self.rob_entries)
        self.RegisterFileInst = rf.RegFile(physical_registers=self.physical_registers)
        # states
        self.decode_state = sim.State("decode_ready", value=True)
        self.finished = False
