import fetch_lib as fetch
import resources_lib as res


class PE:
    def __init__(self, params, program, thread_id, konata_signature):
        # Konata
        self.konata_signature=konata_signature
        # Parameters
        self.params = params
        self.thread_id = thread_id
        # Resources
        self.ResInst = res.Resources(params=self.params)
        # Instr cache + fetch engine
        self.InstrCacheInst = fetch.InstrCache(program=program, params=params, resources=self.ResInst, thread_id=self.thread_id,
            konata_signature=self.konata_signature)
