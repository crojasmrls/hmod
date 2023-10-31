class PipelineParams:
    fetch_width = 2
    commit_width = 2
    int_alus = 2
    physical_registers = 128
    branch_units = 1
    rob_entries = 128
    int_queue_slots = 32
    int_queue_alloc_ports = 2
    lsu_slots = 32
    brob_entries = 16
    l1_dcache_latency = 2
    l1_dcache_mis_latency = 20
    l1_dcache_mshrs = 2
    speculate_on_load = True
    branch_in_int_alu = True
    exe_brob_release = True
    issue_to_exe_latency = 2
    bp_enable = True
    branch_predictor = "bimodal_predictor"
    bp_entries = 128


class MemoryMap:
    TEXT = 0x100E8
    MAIN = 0x10108
    RODATA = 0x1C7C0
    DATA = 0x1E6E0


class RegisterInit:
    init_reg_values = [("ra", "END"), ("sp", 0x7FFFEFFC), ("gp", 0x10008000)]
