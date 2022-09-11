
class DataCache:
    def __init__(self):
        self.mem = {}

    def dc_load(self, addr):
        return self.mem.get(addr, 'Invalid Addres at rd operation')

    def dc_store(self, addr, data):
        self.mem[addr] = data



