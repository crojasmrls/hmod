import math


class PipelineParams:
    fetch_width = 4
    commit_width = 4
    int_alus = 4
    agus = 2
    fp_alus = 2
    physical_registers = 256
    branch_units = 2
    rob_entries = 192
    int_queue_slots = 64
    lsb_slots = 32
    OoO_lsu = True
    load_queue_slots = 32
    store_queue_slots = 32
    lsq_slots = 64
    store_buffer_slots = 32
    store2load_queue_slots = 32
    brob_entries = 64
    branch_in_int_alu = True
    exe_brob_release = True
    issue_to_exe_latency = 2
    recovery_latency = 4
    bp_enable = True
    branch_predictor = "bimodal_predictor"
    bp_entries = 2048
    # Data cache parameters
    dcache_ports = 2
    dcache_mshrs = 64
    # Dcache latencies
    dcache_load_hit_latency = 2
    dcache_store_hit_latency = 2
    l1_dcache_miss_latency = 27
    l2_dcache_miss_latency = 50
    l3_dcache_miss_latency = 144
    # Dcache dimensions
    dcache_line_bytes = 64
    # Constant to shift the address to point a single cache line
    mshr_shamt = int(math.log(dcache_line_bytes, 2))
    # L1 32KB, LOX tile default
    l1_ways = 4
    l1_sets = 128
    # L2 2MB,
    l2_ways = 8
    l2_sets = 4096
    # L3 16MB
    l3_ways = 16
    l3_sets = 16384
    # speculate with load hits
    speculate_on_load_hit = True
    # HPDC blocking behaivor of loads after stores
    HPDC_store_bubble = False
    # speculation wit OoO loads that does not have all the previus stores calculated
    speculate_on_younger_loads = True
    # Store data dependency before AGU calculation
    store_data_dependencies = False


class MemoryMap:
    TEXT = 0x100E8
    MAIN = 0x10108
    RODATA = 0x1C7C0
    DATA = 0x1E6E0


class RegisterInit:
    init_reg_values = [("ra", ("END", 0)), ("sp", 0x7FFFEFFC), ("gp", 0x10008000)]
