import random
from cachesim import CacheSimulator, Cache, MainMemory


class DataCache:
    def __init__(self, params):
        self.params = params
        self.mem = {}
        self.mshrs = {}
        # pycachesim Model
        self.main_mem = MainMemory()
        # self.l3 = Cache(
        #     "L3",
        #     self.params.l3_sets,
        #     self.params.l3_ways,
        #     self.params.dcache_line_bytes,
        #     "LRU",
        # )
        # self.main_mem.load_to(self.l3)
        # self.main_mem.store_from(self.l3)
        # self.l2 = Cache(
        #     "L2",
        #     self.params.l2_sets,
        #     self.params.l2_ways,
        #     self.params.dcache_line_bytes,
        #     "LRU",
        #     store_to=self.l3,
        #     load_from=self.l3,
        # )
        self.l1 = Cache(
            "L1",
            self.params.l1_sets,
            self.params.l1_ways,
            self.params.dcache_line_bytes,
            "LRU",
            # store_to=self.l2,
            # load_from=self.l2,
        )
        self.main_mem.load_to(self.l1)
        self.main_mem.store_from(self.l1)
        self.mem_sim = CacheSimulator(self.l1, self.main_mem)
        self.miss_count = [0, 0, 0]

    def dc_load(self, addr):
        return self.mem.get(addr, random.randint(1 << 9, 1 << 99))

    def dc_store(self, addr, data):
        self.mem[addr] = data

    def print_data_cache(self):
        for addr, data in sorted(self.mem.items()):
            print(addr, ":", data)

    def load_latency(self, addr, length):
        self.mem_sim.load(addr, length=length)
        return self.get_latency(True)

    def store_latency(self, addr, length):
        self.mem_sim.store(addr, length=length)
        return self.get_latency(False)

    def get_latency(self, is_load):
        if is_load:
            latency = self.params.dcache_load_hit_latency
        else:
            latency = self.params.dcache_store_hit_latency
        miss_count = self.l1.backend.MISS_count
        if miss_count != self.miss_count[0]:
            latency = self.params.l1_dcache_miss_latency
            self.miss_count[0] = miss_count
        # miss_count = self.l2.backend.MISS_count
        # if miss_count != self.miss_count[1]:
        #     latency = self.params.l2_dcache_miss_latency
        #     self.miss_count[1] = miss_count
        # miss_count = self.l3.backend.MISS_count
        # if miss_count != self.miss_count[2]:
        #     latency = self.params.l3_dcache_miss_latency
        #     self.miss_count[2] = miss_count
        return latency
