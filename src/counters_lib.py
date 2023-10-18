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
        self.MetricsList = ["IPC", "Instructions", "Cycles"]
        self.ECInst = EventCounters()
        self.CountCtrl = CountersControl()
        self.GCInst = GlobalCycles(
            event_counters=self.ECInst, count_ctrl=self.CountCtrl
        )
        self.create_counters()

    def create_counters(self):
        counters = [("cycles", 0), ("commits", 0), ("commit_cycles", 0), ("stores", 0)]
        for counter in counters:
            self.ECInst.add_counter(counter[0], counter[1])

    def print_metrics(self):
        for metric in self.MetricsList:
            print(metric + ": " + f"{self.metric_functions(metric):.{2}f}")

    # Metric functions
    def metric_functions(self, metric):
        return {
            "IPC": lambda: self.ECInst.read_counter("commits")
            / self.ECInst.read_counter("commit_cycles"),
            "Instructions": lambda: self.ECInst.read_counter("commits"),
            "Cycles": lambda: self.ECInst.read_counter("commit_cycles"),
        }.get(metric, lambda: None)()
