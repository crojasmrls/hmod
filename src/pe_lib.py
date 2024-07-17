import fetch_lib as fetch
import resources_lib as res
import reorderbuffer_lib as rob
import reg_file_lib as rf
import bp_lib as bp
import data_cache_lib as dc
import instr_cache_lib as ic
import asm_parser_lib as par
import rv64_arch_lib as dec


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
        # Branch Predictor
        if self.params.branch_predictor == "bimodal_predictor":
            self.BPInst = bp.BimodalPredictor()
        # Reorder Buffer
        self.RoBInst = rob.ReorderBuffer()
        # Register File
        self.RFInst = rf.RegFile(
            architectural_registers=len(dec.RegisterTable.registers),
            physical_registers=self.params.physical_registers,
        )
        # Data cache
        self.DataCacheInst = dc.DataCache(params=self.params)
        # Instr cache
        self.InstrCacheInst = ic.InstrCache()
        # Program parser and memory initialization
        self.ASMParserInst = par.ASMParser(
            data_cache=self.DataCacheInst, instr_cache=self.InstrCacheInst
        )
        # Fetch engine
        self.FetchUnitInst = fetch.FetchUnit(
            pe=self,
            priority=100,
        )
