import salabim as sim


class GlobalCycles(sim.Component):
    def setup(self, event_counters, count_ctrl):
        self.event_counters = event_counters
        self.count_ctrl = count_ctrl

    def process(self):
        while True:
            if self.count_ctrl.is_enable():
                self.event_counters.increase_counter("cycles")
                yield self.hold(1)
            else:
                yield self.passivate()


class EventCounters:
    def __init__(self):
        self.counters = {}

    def add_counter(self, name, initial_value):
        self.counters[name] = initial_value

    def increase_counter(self, name):
        self.counters[name] += 1

    def set_counter(self, name, value):
        self.counters[name] = value

    def reset_counters(self):
        for counter in self.counters:
            self.set_counter(counter, 0)

    def read_counter(self, name):
        return self.counters[name]


class CountersControl:
    def __init__(self):
        self.perf_counters_en = False

    def is_enable(self):
        return self.perf_counters_en

    def enable(self):
        self.perf_counters_en = True

    def disable(self):
        self.perf_counters_en = False


class PerformanceCounters:
    def __init__(self):
        self.MetricsList = [
            "IPC",
            "Instructions",
            "Cycles",
            "Decoded branches",
            "Taken Branch Predictions",
            "Executed branches",
            "Mispredictions",
            #            "LSB stall cycles",
            #            "WUP wait cycles",
            #            "Issue stall cycles",
            "Executed stores",
            "Executed loads",
            "Dcache requests",
            "Dcache hits",
            "Dcache misses",
            "Dcache hit rate",
            "Load forwards",
            # "L2 requests",
            # "L2 hits",
            # "L2 misses",
            # "L2 hit rate",
            # "L3 requests",
            # "L3 hits",
            # "L3 misses",
            # "L3 hit rate",
        ]
        self.ECInst = EventCounters()
        self.CountCtrl = CountersControl()
        self.GCInst = GlobalCycles(
            event_counters=self.ECInst, count_ctrl=self.CountCtrl
        )
        self.create_counters()

    def create_counters(self):
        counters = [
            ("cycles", 0),
            ("commits", 0),
            ("commit_cycles", 0),
            ("exe_branches", 0),
            ("decode_branches", 0),
            ("taken_branches", 0),
            ("mispredictions", 0),
            ("lsb_stall_cycles", 0),
            ("wup_wait_cycles", 0),
            ("issue_stall_cycles", 0),
            ("exe_stores", 0),
            ("exe_loads", 0),
            ("dcache_hits", 0),
            ("dcache_misses", 0),
            ("load_forwards", 0),
            ("l2_hits", 0),
            ("l2_misses", 0),
            ("l3_hits", 0),
            ("l3_misses", 0),
        ]
        for counter in counters:
            self.ECInst.add_counter(counter[0], counter[1])

    def print_metrics(self):
        for metric in self.MetricsList:
            try:
                print(metric + ": " + f"{self.metric_functions(metric):.{2}f}")
            except ZeroDivisionError:
                print(metric + ": " + f"{0.00:.{2}f}")

    # Metric functions
    def metric_functions(self, metric):
        return {
            "IPC": lambda: self.ECInst.read_counter("commits")
            / self.ECInst.read_counter("commit_cycles"),
            "Instructions": lambda: self.ECInst.read_counter("commits"),
            "Cycles": lambda: self.ECInst.read_counter("commit_cycles"),
            "Decoded branches": lambda: self.ECInst.read_counter("decode_branches"),
            "Taken Branch Predictions": lambda: self.ECInst.read_counter(
                "taken_branches"
            ),
            "Executed branches": lambda: self.ECInst.read_counter("exe_branches"),
            "Mispredictions": lambda: self.ECInst.read_counter("mispredictions"),
            "LSB stall cycles": lambda: self.ECInst.read_counter("lsb_stall_cycles"),
            "WUP wait cycles": lambda: self.ECInst.read_counter("wup_wait_cycles"),
            "Issue stall cycles": lambda: self.ECInst.read_counter(
                "issue_stall_cycles"
            ),
            "Executed stores": lambda: self.ECInst.read_counter("exe_stores"),
            "Executed loads": lambda: self.ECInst.read_counter("exe_loads"),
            "Dcache requests": lambda: self.ECInst.read_counter("dcache_hits")
            + self.ECInst.read_counter("dcache_misses"),
            "Dcache hits": lambda: self.ECInst.read_counter("dcache_hits"),
            "Dcache misses": lambda: self.ECInst.read_counter("dcache_misses"),
            "Dcache hit rate": lambda: (
                self.ECInst.read_counter("dcache_hits")
                / self.metric_functions("Dcache requests")
            )
            * 100,
            "Load forwards": lambda: self.ECInst.read_counter("load_forwards"),
            # "L2 requests": lambda: self.ECInst.read_counter("l2_hits")
            # + self.ECInst.read_counter("l2_misses"),
            # "L2 hits": lambda: self.ECInst.read_counter("l2_hits"),
            # "L2 misses": lambda: self.ECInst.read_counter("l2_misses"),
            # "L2 hit rate": lambda: (
            #     self.ECInst.read_counter("l2_hits")
            #     / self.metric_functions("L2 requests")
            # )
            # * 100,
            # "L3 requests": lambda: self.ECInst.read_counter("l3_hits")
            # + self.ECInst.read_counter("l3_misses"),
            # "L3 hits": lambda: self.ECInst.read_counter("l3_hits"),
            # "L3 misses": lambda: self.ECInst.read_counter("l3_misses"),
            # "L3 hit rate": lambda: (
            #     self.ECInst.read_counter("l3_hits")
            #     / self.metric_functions("L3 requests")
            # )
            # * 100,
        }.get(metric, lambda: None)()
