import rv64uih_lib as dec


class ReorderBuffer:
    def __init__(self):
        self.rob_list = []

    def rob_head(self, instr):
        return instr == self.rob_list[0]

    def store_next2commit(self):
        try:
            store = self.rob_list[1]
        except IndexError:
            pass
        else:
            if (
                store.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                == dec.InstrLabel.STORE
            ):
                store.store_lock.set(True)

    def issue_next_store(self):
        try:
            store = self.rob_list[1]
        except IndexError:
            pass
        else:
            if (
                store.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                == dec.InstrLabel.STORE
            ):
                store.pe.konata_signature.print_stage(
                    "DIS", "ISS", store.pe.thread_id, store.instr_id
                )

    def store_next(self, reference_instr):
        store_instr = None
        for instr in self.rob_list:
            if (
                instr.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                == dec.InstrLabel.STORE
            ):
                store_instr = instr
            if instr == reference_instr:
                return store_instr
        return None

    def add_instr(self, instr):
        # yield self.request(self.rob_resource)
        self.rob_list.append(instr)

    def release_instr(self):
        self.rob_list.pop(0)
        try:
            self.rob_list[0].commit_head.set(True)
        except IndexError:
            pass

    def recovery_rob(self, recovery_instr):
        head_instr = self.rob_list[-1]
        while head_instr != recovery_instr:
            self.rob_list.pop()
            self.release_resources(head_instr)
            head_instr = self.rob_list[-1]

    @staticmethod
    def release_resources(instr):
        instr.pe.konata_signature.retire_instr(instr.pe.thread_id, instr.instr_id, True)
        # Release LS Queues
        if instr.pe.ResInst.load_queue:
            if instr is instr.pe.ResInst.load_queue[-1]:
                instr.pe.ResInst.load_queue.pop()
        if instr.pe.ResInst.store_queue:
            if instr is instr.pe.ResInst.store_queue[-1]:
                instr.pe.ResInst.store_queue.pop()
        # Release MSHR
        if instr.mshr_owner:
            instr.mshr_owner = False
            try:
                instr.pe.DataCacheInst.mshrs.pop(instr.address_align)
            except KeyError:
                pass
        for resource in instr.claimed_resources():
            instr.release((resource, 1))
        instr.fetch_unit.release_fetch()
        instr.cancel()
