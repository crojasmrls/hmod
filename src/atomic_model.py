import reg_file_lib as rf
import data_cache_lib as dc
import instr_cache_lib as ic
import asm_parser_lib as par
import rv64_arch_lib as dec


class PE:
    def __init__(self, params):
        self.params = params
        # Data cache
        self.DataCacheInst = dc.DataCache(params=self.params)
        # Instr cache
        self.InstrCacheInst = ic.InstrCache()
        # Register File
        self.RFInst = rf.RegFile(
            architectural_registers=len(dec.RegisterTable.registers),
            physical_registers=self.params.physical_registers,
        )
        # Program parser and memory initialization
        self.ASMParserInst = par.ASMParser(
            data_cache=self.DataCacheInst, instr_cache=self.InstrCacheInst
        )


class AtomicModel:
    def __init__(self, params, thread_id, konata_signature):
        # Parameters
        self.params = params
        self.thread_id = thread_id
        self.pe = PE(params)
        # Tracer
        self.konata_signature = konata_signature
        self.instr = None
        self.decoded_fields = None
        self.bb_name = "main"
        self.offset = 0
        self.instr_id = 0
        # Registers
        self.p_sources = []
        self.p_dest = None
        self.srcs = None
        # Branch
        self.branch_result = False
        # LS
        self.address = None
        self.data = None

    def run(self):
        while self.bb_name != "END":
            # Get instruction from icache
            self.instr_id += 1
            self.address = None
            self.data = None
            try:
                self.instr = self.pe.InstrCacheInst.get_instr(self.bb_name, self.offset)
            except KeyError:
                print(f"bb name:{self.bb_name}, offset: {self.offset}")
                raise
            self.decoded_fields = dec.DecodedFields(
                instruction=self.instr[0], line_number=self.instr[1]
            )
            # Crate tracer ID
            self.konata_signature.new_instr(
                self.thread_id, self.instr_id, self.instr[1], self.instr[0]
            )
            # Assign registers from register file
            self.p_sources = []
            self.p_dest = None
            self.srcs = None
            self.p_sources = [
                self.pe.RFInst.get_reg(src) for src in self.decoded_fields.sources
            ]
            if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
                if self.decoded_fields.dest != 0:
                    self.p_dest = self.pe.RFInst.get_reg(self.decoded_fields.dest)
                else:
                    self.p_dest = self.pe.RFInst.dummy_reg
            self.srcs = [
                (self.decoded_fields.sources[i], self.p_sources[i].value)
                for i in range(0, len(self.decoded_fields.sources))
            ]
            # Do computation
            self.decoded_fields.instr_tuple[dec.INTFields.EXEC](self)
            # Change Program counter
            self.branch_evaluation()
            # If Load execute load
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.LOAD
            ):
                self.p_dest.value = dec.ExeFuncts.check_fp_cast(
                    self.pe.DataCacheInst.dc_load(self.address),
                    self.decoded_fields.dest,
                )
            # If store execute store
            elif (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.STORE
            ):
                self.pe.DataCacheInst.dc_store(self.address, self.p_sources[0].value)
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.CALL
            ):
                dec.Calls.call_functions(self)
            # Trace dump
            self.tracer()

    def branch_evaluation(self):
        # if branch result, take branch
        if self.branch_result:
            if (
                self.decoded_fields.instr_tuple[dec.INTFields.LABEL]
                is dec.InstrLabel.JALR
            ):
                self.bb_name = self.p_sources[0].value[0]
                self.offset = self.p_sources[0].value[1]
                self.decoded_fields.branch_target = self.p_sources[0].value
            else:
                self.bb_name = self.decoded_fields.branch_target
                self.offset = 0
            self.branch_result = False
        # else increase Program Counter
        elif (self.offset + 1) == self.pe.InstrCacheInst.get_block_len(self.bb_name):
            self.bb_name = self.pe.InstrCacheInst.get_next_block(self.bb_name)
            self.offset = 0
        else:
            self.offset = self.offset + 1

    def tracer(self):
        if self.decoded_fields.instr_tuple[dec.INTFields.DEST]:
            self.data = self.p_dest.value
        if self.decoded_fields.instr_tuple[dec.INTFields.LABEL] is dec.InstrLabel.STORE:
            # store dara is in src 0 tuple index 1
            self.data = self.srcs[0][1]
        self.konata_signature.print_torture(
            self.thread_id,
            self.instr_id,
            self.decoded_fields.line_number,
            self.decoded_fields.instruction,
            self.decoded_fields.dest,
            self.data,
            self.srcs,
            self.address,
        )
