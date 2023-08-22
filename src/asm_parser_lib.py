class ASMParser:
    def __init__(self, data_cache, instr_cache):
        self.data_cache = data_cache
        self.instr_cache = instr_cache
        self.constant_dict = {}

    def read_program(self, program):
        bb_name_prev = ''
        bb_name = ''
        instr_count = 0
        lines = self.get_file_lines(program)
        line_number = 0
        for line in lines:
            line_number += 1
            line = self.clean_line(line)
            # If the line is a code segment tag
            if line.find(':') != -1:
                instr_count = 0
                # Remove the code segment tag indicator
                bb_name = line.split(':')[0].split()[0]
                if len(bb_name) != 0:
                    self.instr_cache.add_bb(bb_name, bb_name_prev)
                    bb_name_prev = bb_name
            else:
                if len(line.replace(" ", "")) != 0:
                    self.instr_cache.add_instr(bb_name, (line, line_number))
                    instr_count = instr_count + 1

    def fill_constant_dict(self, program):
        lines = self.get_file_lines(program)
        for line in lines:
            pass

    @staticmethod
    def get_file_lines(program):
        file = open(program, "r")
        lines = file.readlines()
        file.close()
        return lines

    @staticmethod
    def clean_line(line):
        line = line.replace("\n", "")
        line = line.replace("\t", " ")
        line = line.split('#')[0]
        return line
