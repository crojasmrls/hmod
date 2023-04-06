import salabim as sim
import instr_lib as instr
import rv64uih_lib as dec
# from watchpoints import watch


class BasicInstrBlock:
    def __init__(self, name):
        self.name = name
        self.next_block = 'END'
        # Basic block instruction list
        self.instr = []

    def add_instr(self, new_instr):
        self.instr.append(new_instr)

    def set_next_block(self, next_block):
        self.next_block = next_block

    def get_instr(self, index):
        return self.instr[index]


class InstrCache(sim.Component):
    """docstring for InstrCache"""
    def setup(self, program, params, resources, thread_id, konata_signature, performance_counters):
        self.program = program
        self.params = params
        self.bb_dict = {}
        self.first_block = 'END'
        self.offset = 0
        self.bb_name = 'main'
        self.branch_taken = False
        self.resources = resources
        self.thread_id = thread_id
        self.konata_signature = konata_signature
        self.performance_counters = performance_counters
        self.instr_id = 0
        self.bp_take_branch = False, None
        self.flushed = False
        # watch(self.fetch_resource.claimed_quantity.value)

    def read_program(self):
        bb_name_prev = ''
        bb_name = ''
        instr_count = 0
        f = open('../programs/' + self.program, "r")
        lines = f.readlines()
        line_number = 0
        for line in lines:
            line_number += 1
            line = line.replace("\n", "")
            line = line.replace("\t", " ")
            line = line.split('#')[0]
            # If the line is a code segment tag
            if line.find(':') != -1:
                instr_count = 0
                # Remove the code segment tag indicator
                bb_name = line.split(':')[0].split()[0]
                if len(bb_name) != 0:
                    if len(self.bb_dict) > 0:
                        self.bb_dict[bb_name_prev].set_next_block(bb_name)
                    if len(self.bb_dict) == 0:
                        self.first_block = bb_name
                    self.bb_dict[bb_name] = BasicInstrBlock(bb_name)
                    bb_name_prev = bb_name
            else:
                if len(line.replace(" ", "")) != 0:
                    self.bb_dict[bb_name].add_instr((line, line_number))
                    instr_count = instr_count + 1

    def print_program(self):
        bb_name = self.first_block
        while bb_name != 'END':
            print(self.bb_dict[bb_name].name)
            for instr_aux in self.bb_dict[bb_name].instr:
                print('    ' + instr_aux)
            bb_name = self.bb_dict[bb_name].next_block

    def send_first_bb(self):
        return self.first_block

    def create_instr(self):
        self.instr_id += 1
        if self.params.bp_enable:
            bp_tag_index = self.bp_tag_index(self.bb_dict[self.bb_name].instr[self.offset][1], self.params.bp_entries)
            self.bp_take_branch = self.resources.branch_predictor.read_entry(bp_tag_index[0], bp_tag_index[1])
        else:
            bp_tag_index = 0, 0
            self.bp_take_branch = False, None
        new_instr = instr.Instr(decoded_fields=dec.DecodedFields(instruction=self.bb_dict[self.bb_name].instr[self.offset][0],
                                line_number=self.bb_dict[self.bb_name].instr[self.offset][1]), params=self.params,
                                resources=self.resources,  thread_id=self.thread_id, instr_id=self.instr_id,
                                konata_signature=self.konata_signature, performance_counters=self.performance_counters,
                                fetch_unit=self, bb_name=self.bb_name,
                                offset=self.offset, bp_take_branch=self.bp_take_branch, bp_tag_index=bp_tag_index,
                                priority=0)
        self.resources.RobInst.add_instr(new_instr)
        self.konata_signature.new_instr(self.thread_id, self.instr_id, self.bb_dict[self.bb_name].instr[self.offset][1],
                                        self.bb_dict[self.bb_name].instr[self.offset][0])

    @staticmethod
    def bp_tag_index(line_number, bp_entries):
        index_bits = bp_entries.bit_length() - 1
        tag = line_number >> index_bits
        index = line_number % bp_entries
        return tag, index

    def release_fetch(self):
        for resource in self.claimed_resources():
            self.release((resource, 1))

    def process(self):
        # Condition to end fetch process, if the bb_name pointer reach END and the ROB is empty the fetch process
        # is terminated
        while self.bb_name != 'END' or self.resources.RobInst.count_inst != 0:
            # Request fetch width port
            yield self.request(self.resources.fetch_resource)
            if len(self.resources.miss_branch) != 0:
                self.flushed = False
                if self.resources.miss_branch.pop(0):
                    branch_target = self.resources.branch_target.pop(0)
                    self.bb_name = branch_target[0]
                    self.offset = branch_target[1]
                else:
                    self.resources.branch_target.pop(0)
            # If fetch process reach end of file passivate it
            if self.bb_name == 'END':
                self.resources.finished = True
                yield self.passivate()
            else:
                # Create new instruction
                if self.flushed:
                    self.flushed = False
                    self.release_fetch()
                else:
                    self.create_instr()
            # Condition to advance to next basic block
            if self.bp_take_branch[0]:
                self.bb_name = self.bp_take_branch[1]
                self.offset = 0
            else:
                if self.offset == len(self.bb_dict[self.bb_name].instr) - 1:
                    self.bb_name = self.bb_dict[self.bb_name].next_block
                    self.offset = 0
                    # Check if the basic block is empty
                    while len(self.bb_dict[self.bb_name].instr) == 0:
                        # If fetch process reach end of file passivate it
                        if self.bb_name == 'END':
                            self.resources.finished = True
                            yield self.passivate()
                        self.bb_name = self.bb_dict[self.bb_name].next_block
                else:
                    self.offset = self.offset + 1
            # yield self.hold(1)
