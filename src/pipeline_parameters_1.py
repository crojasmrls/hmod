import math


class PipelineParams:
    fetch_width = 4
    commit_width = 4
    int_alus = 4
    physical_registers = 256
    branch_units = 2
    rob_entries = 192
    int_queue_slots = 64
    lsb_slots = 32
    OoO_lsu = True
    load_queue_slots = 32
    store_queue_slots = 32
    store_buffer_slots = 32
    store2load_queue_slots = 32
    brob_entries = 64
    branch_in_int_alu = True
    exe_brob_release = True
    issue_to_exe_latency = 2
    bp_enable = True
    branch_predictor = "bimodal_predictor"
    bp_entries = 2048
    # Data cache parameters
    dcache_ports = 1
    dcache_mshrs = 4
    # Dcache latencies
    dcache_load_hit_latency = 1
    dcache_store_hit_latency = 1
    l1_dcache_miss_latency = 20
    l2_dcache_miss_latency = 50
    l3_dcache_miss_latency = 144
    # Dcache dimensions
    dcache_line_bytes = 64
    # Constant to shift the address to point a single cache line
    mshr_shamt = int(math.log(dcache_line_bytes, 2))
    # L1 64KB
    l1_ways = 2
    l1_sets = 512
    # L2 2MB,
    l2_ways = 8
    l2_sets = 4096
    # L3 16MB
    l3_ways = 16
    l3_sets = 16384

    speculate_on_load = False


class MemoryMap:
    TEXT = 0x100E8
    MAIN = 0x10108
    RODATA = 0x1C7C0
    DATA = 0x1E6E0


class RegisterInit:
    init_reg_values = [("ra", "END"), ("sp", 0x7FFFEFFC), ("gp", 0x10008000)]
