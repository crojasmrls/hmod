import salabim as sim
import reorderbuffer_lib as rob
import reg_file_lib as rf
import lsq_lib as lsq
import data_cache_lib as dc


class Resources:
    def __init__(self, params):
        # parameters
        self.params = params
        # resources
        self.fetch_resource = sim.Resource('fetch_resource', capacity=self.params.fetch_width)
        self.int_units = sim.Resource('int_units', capacity=self.params.int_alus)
        self.branch_units = sim.Resource('branch_units', capacity=self.params.branch_units)
        self.int_queue = sim.Resource('int_queue', capacity=self.params.int_queue_slots)
        self.LoadStoreQueueInst = lsq.LoadStoreQueue(lsu_slots=self.params.lsu_slots)
        self.DataCacheInst = dc.DataCache()
        self.brob_resource = sim.Resource('brob_resource', capacity=self.params.brob_entries)
        # self.h_units = sim.Resource('h_units', capacity=1) not implemented for now
        # instances
        self.RobInst = rob.ReorderBuffer(rob_entries=self.params.rob_entries)
        self.RegisterFileInst = rf.RegFile(physical_registers=self.params.physical_registers)
        # states
        self.decode_state = sim.State("decode_ready", value=True)
        self.finished = False
        self.take_branch = False
        self.branch_target = 'MAIN:'
