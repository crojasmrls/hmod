import salabim as sim
import reorderbuffer_lib as rob
import reg_file_lib as rf
import lsq_lib as lsq
import bp_lib as bp


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
        self.brob_resource = sim.Resource('brob_resource', capacity=self.params.brob_entries)
        self.decode_ports = sim.Resource('decode_ports', capacity=self.params.fetch_width)
        # This resource is used to serialize teh renaming procces
        self.rename_resource = sim.Resource('rename_resource', capacity=1)
        # Max number of instructions in renaming
        self.rename_ports = sim.Resource('rename_ports', capacity=self.params.fetch_width)
        self.int_alloc_ports = sim.Resource("int_alloc_ports", capacity=self.params.fetch_width)
        self.cache_ports = sim.Resource("cache_ports", capacity=1)
        self.store_state = sim.State("store_state", value=True)
        self.commit_ports = sim.Resource("commit_ports", capacity=self.params.commit_width)
        # self.h_units = sim.Resource('h_units', capacity=1) not implemented for now
        # instances
        self.RobInst = rob.ReorderBuffer(rob_entries=self.params.rob_entries)
        self.RegisterFileInst = rf.RegFile(physical_registers=self.params.physical_registers)
        # states
        self.finished = False
        # Branch Calculation queues
        self.miss_branch = []
        self.branch_target = []
        # Branch Predictor
        if self.params.branch_predictor == 'bimodal_predictor':
            self.branch_predictor = bp.BimodalPredictor()
