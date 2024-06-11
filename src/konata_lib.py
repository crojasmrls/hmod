import salabim as sim


class KonataSignature(sim.Component):
    def setup(
        self,
        konata_out,
        konata_dump_on,
        torture_out,
        torture_dump_on,
        tracer_with_konata_id,
    ):
        self.konata_out = konata_out
        self.konata_dump_on = konata_dump_on
        self.torture_out = torture_out
        self.torture_dump_on = torture_dump_on
        self.tracer_with_konata_id = tracer_with_konata_id
        if self.konata_dump_on:
            self.fk = open(self.konata_out, "w")
        if self.torture_dump_on:
            self.ft = open(self.torture_out, "w")
        self.cycle_count = 0
        self.konata_id_count = 0
        self.konata_ids = {}

    def process(self):
        if self.konata_dump_on:
            self.fk.write("Kanata\t0004\n")
            while True:
                self.cycle_count += 1
                yield self.hold(1)

    def print_cycle(self):
        self.fk.write("C\t" + str(self.cycle_count) + "\n")
        self.cycle_count = 0

    def new_instr(self, thread_id, instr_id, line, instr):
        if type(instr_id) == int and type(thread_id) == int:
            # Thread ID and instruction ID are joint to create a unique ID identifier for the konata signature
            self.konata_id_count += 1
            konata_id = self.konata_id_count
            try:
                self.konata_ids[thread_id].append(konata_id)
            except KeyError:
                self.konata_ids[thread_id] = [0]
                print("Thread id field was created")
                self.konata_ids[thread_id].append(konata_id)
            if self.konata_dump_on:
                if self.cycle_count != 0:
                    self.print_cycle()
                self.fk.write(
                    "I\t"
                    + str(konata_id)
                    + "\t"
                    + str(instr_id)
                    + "\t"
                    + str(thread_id)
                    + "\n"
                )
                # Label
                self.fk.write(
                    "L\t" + str(konata_id) + "\t0\t" + str(line) + ": " + instr + "\n"
                )
                self.fk.write("S\t" + str(konata_id) + "\t0\tF\n")
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
                    print(
                        "thread_id="
                        + str(thread_id)
                        + " and instr_id="
                        + str(instr_id)
                        + " Are not in the konata_ids list!!\n"
                    )
                    raise
                self.fk.write("E\t" + str(konata_id) + "\t0\t" + prev_stage + "\n")
                self.fk.write("S\t" + str(konata_id) + "\t0\t" + new_stage + "\n")

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
                    print(
                        "Thread id: "
                        + str(thread_id)
                        + " and Instr id: "
                        + str(instr_id)
                        + " Are not in the konata_ids list.\n"
                    )
                    raise
                if is_flush:
                    self.fk.write(
                        "R\t" + str(konata_id) + "\t" + str(konata_id) + "\t1\n"
                    )
                else:
                    self.fk.write(
                        "R\t" + str(konata_id) + "\t" + str(konata_id) + "\t0\n"
                    )
        else:
            raise TypeError("Instr id and thread id must be integer values!!")

    def print_torture(
        self, thread_id, instr_id, line_number, instr, dest, data, srcs, address
    ):
        if type(instr_id) == int and type(thread_id) == int:
            if self.torture_dump_on:
                if self.tracer_with_konata_id:
                    try:
                        konata_id = self.konata_ids[thread_id][instr_id]
                    except KeyError:
                        print(
                            "thread_id="
                            + str(thread_id)
                            + " and instr_id="
                            + str(instr_id)
                            + " Are not in the konata_ids list!!\n"
                        )
                        raise
                    knid = "k" + str(konata_id) + ": "
                    self.ft.write(f"core    {str(thread_id)}: {knid}\n")
                ln = "l" + str(line_number)
                self.ft.write(f"{ln}{instr}\n")
                out = ""
                if dest:
                    out = out + " 0x" + "{:02d}".format(dest) + ": " + str(data)
                if srcs:
                    for src in srcs:
                        out = out + " 0x" + "{:02d}".format(src[0]) + ": " + str(src[1])
                if address:
                    out = out + " addr:" + str(address)
                if data and not dest:
                    out = out + " data:" + str(data)
                self.ft.write(ln + "    " + out + "\n")
        else:
            raise TypeError("Instr id and thread id must be integer values!!")
