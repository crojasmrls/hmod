from enum import Enum, IntEnum, auto
import re


class Sections(Enum):
    TEXT = auto()
    MAIN = auto()
    DATA = auto()
    RODATA = auto()
    HEAD = auto()


class Bytes(IntEnum):
    DWORD = 8
    WORD = 4
    HALF = 2
    BYTE = 1


class RegularExpr:
    re_lo = r"%lo\(?(.*?)\)"
    re_hi = r"%hi\(?(.*?)\)"


class ASMParser:
    def __init__(self, data_cache, instr_cache):
        self.data_cache = data_cache
        self.instr_cache = instr_cache
        self.constant_dict = {}

    def read_program(self, program, mem_map):
        self.fill_data(program, mem_map)
        bb_name_prev = ""
        bb_name = ""
        instr_count = 0
        lines = self.get_file_lines(program)
        line_number = 0
        line_number_offset = 0
        section = Sections.HEAD
        for line in lines:
            line_number += 1
            line = self.clean_line(line)
            # If the line is a code segment tag
            if section is Sections.TEXT:
                if ".-main" in line:
                    break
                if (
                    ":" in line
                    and not ".string" in line
                    and len(self.get_tag_name(line)) != 0
                ):
                    instr_count = 0
                    # Remove the code segment tag indicator
                    if len(bb_name) != 0 and len(bb_name_prev) != 0:
                        if self.instr_cache.get_block_len(bb_name) == 0:
                            self.instr_cache.del_bb(bb_name, bb_name_prev)
                            bb_name = bb_name_prev
                    bb_name_prev = bb_name
                    bb_name = self.get_tag_name(line)
                    self.instr_cache.add_bb(bb_name, bb_name_prev)
                else:
                    if len(line.split(".")[0].replace(" ", "")) != 0:
                        if "%hi" in line:
                            address = self.get_address(line, RegularExpr.re_hi)
                            offset = self.get_offset(line, RegularExpr.re_hi)
                            immediate = self.get_hi(address, offset)
                            line = self.replace_immediate(
                                line, immediate, RegularExpr.re_hi
                            )
                        if "%lo" in line:
                            address = self.get_address(line, RegularExpr.re_lo)
                            offset = self.get_offset(line, RegularExpr.re_lo)
                            immediate = self.get_lo(address, offset)
                            line = self.replace_immediate(
                                line, immediate, RegularExpr.re_lo
                            )
                        line = line.replace("ret", "jr ra")
                        if "call" in line:
                            call_funct = line.replace("call", "").replace(" ", "")
                            if call_funct in self.constant_dict:
                                line = line.replace("call", "jal")
                        if "tail" in line:
                            call_funct = line.replace("tail", "").replace(" ", "")
                            if call_funct in self.constant_dict:
                                line = line.replace("tail", "j")
                            else:
                                line = line.replace("tail", "call")
                                self.instr_cache.add_instr(
                                    bb_name, (line, line_number + line_number_offset)
                                )
                                instr_count += 1
                                line_number_offset += 1
                                line = "jr ra"
                        self.instr_cache.add_instr(
                            bb_name, (line, line_number + line_number_offset)
                        )
                        instr_count += 1
            else:
                if ".text" in line:
                    section = Sections.TEXT
        try:
            self.instr_cache.get_next_block("END")
        except KeyError:
            self.instr_cache.add_bb("END", bb_name)

    def fill_data(self, program, mem_map):
        section = Sections.HEAD
        address = 0
        tagged = False
        lines = self.get_file_lines(program)
        # This variables are used to intialize WORD data varaibales as DWORD
        word_count = False
        word_data = 0
        for line in lines:
            line = self.clean_line(line)
            if section is Sections.DATA:
                if ".set" in line:
                    self.constant_dict[self.get_data_tag_name(line)] = address
                    tagged = True
                elif not tagged and ":" in line.split('"')[0]:
                    self.constant_dict[self.get_tag_name(line)] = address
                elif ".word" in line:
                    if word_count:
                        word_data = (
                            self.get_int_data(line, Bytes.WORD.value) << 32
                        ) | word_data
                        self.data_cache.dc_store(address, word_data)
                        address += Bytes.DWORD.value
                        word_count = False
                    else:
                        # Save 32 low bits of data
                        word_data = self.get_int_data(line, Bytes.WORD.value)
                        word_count = True
                elif ".dword" in line:
                    self.data_cache.dc_store(
                        address, self.get_int_data(line, Bytes.DWORD.value)
                    )
                    address += Bytes.DWORD.value
                elif ".zero" in line:  # Zero memory
                    for _ in range(
                        int(
                            self.get_int_data(line, Bytes.DWORD.value)
                            / Bytes.DWORD.value
                        )
                    ):
                        self.data_cache.dc_store(address, 0)
                        address += Bytes.DWORD.value
            if section is Sections.RODATA:
                if ".data" in line:
                    section = Sections.DATA
                    address = mem_map.DATA
                elif ".set" in line:
                    self.constant_dict[self.get_data_tag_name(line)] = address
                elif not tagged and ":" in line.split('"')[0]:
                    self.constant_dict[self.get_tag_name(line)] = address
                elif ".word" in line:
                    if word_count:
                        word_data = (
                            self.get_int_data(line, Bytes.WORD.value) << 32
                        ) | word_data
                        self.data_cache.dc_store(address, word_data)
                        address += Bytes.DWORD.value
                        word_count = False
                    else:
                        # Save 32 low bits of data
                        word_data = self.get_int_data(line, Bytes.WORD.value)
                        word_count = True
                elif ".dword" in line:
                    self.data_cache.dc_store(
                        address, self.get_int_data(line, Bytes.DWORD.value)
                    )
                    address += Bytes.DWORD.value
                elif ".zero" in line:  # Zero memory
                    for _ in range(
                        int(
                            self.get_int_data(line, Bytes.DWORD.value)
                            / Bytes.DWORD.value
                        )
                    ):
                        self.data_cache.dc_store(address, 0)
                        address += Bytes.DWORD.value
            elif section is Sections.MAIN:
                if ".-main" in line:
                    section = Sections.RODATA
            elif section is Sections.TEXT:
                if "main:" in line:
                    section = Sections.MAIN
                elif ":" in line.split('"')[0]:
                    self.constant_dict[self.get_tag_name(line)] = address
                elif ".string" in line:
                    self.data_cache.dc_store(address, self.get_string_data(line))
                    address += len(self.get_string_data(line))
            else:
                if ".text" in line:
                    section = Sections.TEXT
                    address = mem_map.RODATA

    def get_address(self, line, re_pattern):
        tag = re.findall(re_pattern, line)[0].split("+")[0].split("-")[0].split()[0]
        return self.constant_dict[tag]

    @staticmethod
    def get_offset(line, re_pattern):
        tag = re.findall(re_pattern, line)[0]
        try:
            offset = tag.split("+")[1]
        except IndexError:
            try:
                offset = tag.split("-")[1]
            except IndexError:
                return 0
            else:
                try:
                    return -int(offset)
                except ValueError:
                    print(f"Negative offset is not a valid integer in line: {line}")
                    return 0
        else:
            try:
                return int(offset)
            except ValueError:
                print(f"Offset is not a valid integer in line: {line}")
                return 0

    @staticmethod
    def get_hi(address, offset):
        return str(((address + offset) & 0xFFFFF000) >> 12)

    @staticmethod
    def get_lo(address, offset):
        return str((address + offset) & 0x00000FFF)

    @staticmethod
    def replace_immediate(line, immediate, re_pattern):
        return re.sub(re_pattern, immediate, line)

    @staticmethod
    def get_tag_name(line):
        return line.split(":")[0].split()[0]

    @staticmethod
    def get_data_tag_name(line):
        return line.split(",")[0].split()[1]

    @staticmethod
    def get_string_data(line):
        return line.split('"')[1]

    @staticmethod
    def get_int_data(line, n_bytes):
        return int(line.split()[1].split()[0]) & (pow(2, n_bytes << 3) - 1)

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
        line = line.split("#")[0]
        return line
