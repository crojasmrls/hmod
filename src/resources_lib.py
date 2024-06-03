import salabim as sim


class Resources:
    def __init__(self, params):
        # parameters
        self.params = params
        # resources
        self.fetch_resource = sim.Resource(
            "fetch_resource", capacity=self.params.fetch_width
        )
        self.int_units = sim.Resource("int_units", capacity=self.params.int_alus)
        self.branch_units = sim.Resource(
            "branch_units", capacity=self.params.branch_units
        )
        self.rob_resource = sim.Resource(
            "rob_resource", capacity=self.params.rob_entries
        )
        self.int_queue = sim.Resource("int_queue", capacity=self.params.int_queue_slots)
        self.lsb_slots = sim.Resource("lsb_slots", capacity=self.params.lsb_slots)
        self.lq_slots = sim.Resource("lq_slots", capacity=self.params.load_queue_slots)
        self.sq_slots = sim.Resource("sq_slots", capacity=self.params.store_queue_slots)
        self.lsq_slots = sim.Resource("lsq_slots", capacity=self.params.lsq_slots)
        self.sb_slots = sim.Resource(
            "sb_slots", capacity=self.params.store_buffer_slots
        )
        self.s2l_slots = sim.Resource(
            "s2l_slots", capacity=self.params.store2load_queue_slots
        )
        self.ls_ordering = sim.Resource("ls_ordering", capacity=1)
        self.agu_resource = sim.Resource("agu_resource", capacity=1)
        self.brob_resource = sim.Resource(
            "brob_resource", capacity=self.params.brob_entries
        )
        self.decode_ports = sim.Resource(
            "decode_ports", capacity=self.params.fetch_width
        )
        # This resource is used to serialize teh renaming process
        self.rename_resource = sim.Resource("rename_resource", capacity=1)
        # Max number of instructions in renaming
        self.rename_ports = sim.Resource(
            "rename_ports", capacity=self.params.fetch_width
        )
        self.dispatch_ports = sim.Resource(
            "dispatch_ports", capacity=self.params.fetch_width
        )
        self.alloc_ports = sim.Resource("alloc_ports", capacity=self.params.fetch_width)
        self.cache_ports = sim.Resource(
            "cache_ports", capacity=self.params.dcache_ports
        )
        self.store_bubble = sim.Resource("store_bubble", capacity=1)
        self.mshrs = sim.Resource("mshrs", capacity=self.params.dcache_mshrs)
        self.store_state = sim.State("store_state", value=True)
        self.commit_ports = sim.Resource(
            "commit_ports", capacity=self.params.commit_width
        )
        # self.h_units = sim.Resource('h_units', capacity=1) not implemented for now
        # states
        self.finished = False
        # Branch Calculation queues
        self.miss_branch = []
        self.branch_target = []
        # Store list used to track the order of the stores.
        self.store_queue = []
        self.load_queue = []
