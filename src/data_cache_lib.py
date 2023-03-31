import random


class DataCache:
    def __init__(self):
        self.mem = {}

    def dc_load(self, addr):
        return self.mem.get(addr, random.randint(1 << 9, 1 << 99))

    def dc_store(self, addr, data):
        self.mem[addr] = data

    def print_data_cache(self):
        for addr, data in self.mem.items():
            print(addr, ':', data)
