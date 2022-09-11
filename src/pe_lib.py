import fetch_lib as fetch
import resources_lib as res


class PE:
    def __init__(self, fetch_width, physical_registers, int_alus, rob_entries, int_queue_slots, lsu_slots, brob_entries,
                 program, thread_id, konata_signature):
        # Konata
        self.konata_signature=konata_signature
        # Parameters
        self.fetch_width = fetch_width
        self.physical_registers = physical_registers
        self.int_alus = int_alus
        self.rob_entries = rob_entries
        self.program = program
        self.int_queue_slots = int_queue_slots
        self.lsu_slots = lsu_slots
        self.thread_id = thread_id
        self.brob_entries = brob_entries
        # Resources
        self.ResInst = res.Resources(fetch_width=self.fetch_width, physical_registers=self.physical_registers,
                                     int_alus=self.int_alus, rob_entries=self.rob_entries,
                                     int_queue_slots=self.int_queue_slots, lsu_slots=self.lsu_slots,
                                     brob_entries=self.brob_entries)
        # Instr cache + fetch engine
        self.InstrCacheInst = fetch.InstrCache(program=program, resources=self.ResInst, thread_id=self.thread_id,
            konata_signature=self.konata_signature)
