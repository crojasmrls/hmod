import math


class PipelineParams:
    fetch_width = 2
    commit_width = 2
    int_alus = 2
    physical_registers = 128
    branch_units = 1
    rob_entries = 128
    int_queue_slots = 32
    lsb_slots = 32
    OoO_lsu = False
    load_queue_slots = 16
    store_queue_slots = 16
    store_buffer_slots = 32
    brob_entries = 16
    branch_in_int_alu = True
    exe_brob_release = True
    issue_to_exe_latency = 2
    bp_enable = True
    branch_predictor = "bimodal_predictor"
    bp_entries = 128
    # Data cache parameters
    dcache_mshrs = 4
    # Dcache latencies
    cache_hit_latency = 3
    l1_dcache_miss_latency = 12
    l2_dcache_miss_latency = 30
    l3_dcache_miss_latency = 144
    # Dcache dimensions
    dcache_line_bytes = 16
    # Constant to shift the address to point a single cache line
    mshr_shamt = int(math.log(dcache_line_bytes, 2))
    # L1 8KB
    l1_ways = 8
    l1_sets = 64
    # L2 64KB
    l2_ways = 8
    l2_sets = 512
    # L3 5MB
    l3_ways = 16
    l3_sets = 20480

    speculate_on_load = True


class MemoryMap:
    TEXT = 0x100E8
    MAIN = 0x10108
    RODATA = 0x1C7C0
    DATA = 0x1E6E0


class RegisterInit:
    init_reg_values = [("ra", "END"), ("sp", 0x7FFFEFFC), ("gp", 0x10008000)]
