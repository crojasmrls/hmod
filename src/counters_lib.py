import salabim as sim


class GlobalCycles(sim.Component):
    def setup(self, event_counters, perf_counters_en):
        self.perf_counters_en = perf_counters_en
        self.cycles_en = True
        self.event_counters = event_counters

    def process(self):
        if self.perf_counters_en:
            while True:
                if self.cycles_en:
                    self.event_counters.increase_counter('cycles')
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

    def read_counter(self, name):
        return self.counters[name]


class PerformanceCounters:
    def __init__(self, perf_counters_en):
        self.MetricsList = ['IPC', 'Instructions', 'Cycles']
        self.ECInst = EventCounters()
        self.GCInst = GlobalCycles(event_counters=self.ECInst, perf_counters_en=perf_counters_en)
        self.create_counters()

    def create_counters(self):
        counters = [('cycles', 0), ('commits', 0), ('commit_cycles', 0), ('stores', 0)]
        for counter in counters:
            self.ECInst.add_counter(counter[0], counter[1])

    def print_metrics(self):
        for metric in self.MetricsList:
            print(metric + ': ' + f'{self.metric_functions(metric):.{2}f}')

    # Metric functions
    def metric_functions(self, metric):
        return {
            'IPC': lambda: self.ECInst.read_counter('commits') / self.ECInst.read_counter('commit_cycles'),
            'Instructions': lambda: self.ECInst.read_counter('commits'),
            'Cycles': lambda: self.ECInst.read_counter('commit_cycles'),
        }.get(metric, lambda: None)()
