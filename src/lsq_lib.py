import salabim as sim


class LoadStoreQueue:
    def __init__(self, lsu_slots):
        self.lsu_slots = sim.Resource('lsu_slots', capacity=lsu_slots)
        #self.entries = sim.Queue("lsu_queue")
