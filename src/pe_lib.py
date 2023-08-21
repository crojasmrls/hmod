import fetch_lib as fetch
import resources_lib as res
import data_cache_lib as dc
import instr_cache_lib as ic
import asm_parser_lib as par


class PE:
    def __init__(self, params, thread_id, konata_signature, performance_counters):
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
        # Instr cache
        self.InstrCacheInst = ic.InstrCache()
        # Program parser and memory initialization
        self.ASMParserInst = par.ASMParser(data_cache=self.DataCacheInst, instr_cache=self.InstrCacheInst)
        # Fetch engine
        self.FetchUnitInst = fetch.FetchUnit(instr_cache=self.InstrCacheInst, params=params, resources=self.ResInst,
                                             thread_id=self.thread_id, konata_signature=self.konata_signature,
                                             performance_counters=self.performance_counters,
                                             data_cache=self.DataCacheInst, priority=100)
