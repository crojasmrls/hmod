import fetch_lib as fetch
import resources_lib as res
import data_cache_lib as dc
class PE:
    def __init__(self, params, program, thread_id, konata_signature, performance_counters):
        # Konata
        self.konata_signature = konata_signature
        # Performance Counters
        self.performance_counters = performance_counters
        # Parameters
        self.params = params
        self.thread_id = thread_id
        # Resources
        self.ResInst = res.Resources(params=self.params)
        # Data cache
        self.DataCacheInst = dc.DataCache()
        # Instr cache + fetch engine
        self.InstrCacheInst = fetch.InstrCache(program=program, params=params, resources=self.ResInst,
                                               thread_id=self.thread_id, konata_signature=self.konata_signature,
                                               performance_counters=self.performance_counters,
                                               data_cache=self.DataCacheInst, priority=100)

