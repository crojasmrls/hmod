import salabim as sim


class KonataSignature(sim.Component):
    def setup(self, konata_out, konata_dump_on):
        self.konata_out = konata_out
        self.f = open('../' + self.konata_out, 'w')
        self.konata_dump_on = konata_dump_on
        self.cycle_count = 0
        self.konata_id_count = 0
        self.konata_ids = {}

    def process(self):
        self.f.write('Kanata\t0004\n')
        while True:
            self.cycle_count += 1
            yield self.hold(1)

    def print_cycle(self):
        self.f.write('C\t' + str(self.cycle_count) + '\n')
        self.cycle_count = 0

    def new_instr(self, thread_id, instr_id, line, instr):
        if type(instr_id) == int and type(thread_id) == int:
            if self.konata_dump_on:
                if self.cycle_count != 0:
                    self.print_cycle()
                # Thread ID and intruction ID are joint to create a unique ID identifier for the konata signature
                self.konata_id_count += 1
                konata_id = self.konata_id_count
                try:
                    self.konata_ids[thread_id].append(konata_id)
                except KeyError:
                    self.konata_ids[thread_id] = [0]
                    print("Thread id field was created")
                    self.konata_ids[thread_id].append(konata_id)
                self.f.write('I\t' + str(konata_id) + '\t' + str(instr_id) + '\t' + str(thread_id) + '\n')
                # Label
                self.f.write('L\t' + str(konata_id) + '\t0\t' + str(line) + ': ' + instr + '\n')
                self.f.write('S\t' + str(konata_id) + '\t0\tFET\n')
        else:
            raise TypeError("Instr id and thread id must be integer values!!")

    def print_stage(self, prev_stage, new_stage, thread_id, instr_id):
        if type(instr_id) == int and type(thread_id) == int:
            if self.konata_dump_on:
                if self.cycle_count != 0:
                    self.print_cycle()
                try:
                    konata_id = self.konata_ids[thread_id][instr_id]
                except KeyError:
                    print("thread_id="+str(thread_id)+" and instr_id=" + str(instr_id)
                          + " Are not in the konata_ids list!!\n")
                    raise
                self.f.write('E\t' + str(konata_id) + '\t0\t' + prev_stage + '\n')
                self.f.write('S\t' + str(konata_id) + '\t0\t' + new_stage + '\n')

        else:
            raise TypeError("Instr id and thread id must be integer values!!")

    def retire_instr(self, thread_id, instr_id, is_flush):
        if type(instr_id) == int and type(thread_id) == int:
            if self.konata_dump_on:
                if self.cycle_count != 0:
                    self.print_cycle()
                try:
                    konata_id = self.konata_ids[thread_id][instr_id]
                except KeyError:
                    print("Thread id: "+str(thread_id)+" and Instr id: " + str(instr_id)
                          + " Are not in the konata_ids list.\n")
                    raise
                if is_flush:
                    self.f.write('R\t' + str(konata_id) + '\t' + str(konata_id) + '\t1\n')
                else:
                    self.f.write('R\t' + str(konata_id) + '\t' + str(konata_id) + '\t0\n')
        else:
            raise TypeError("Instr id and thread id must be integer values!!")
