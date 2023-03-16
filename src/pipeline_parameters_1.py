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
    branch_in_int_alu = True
    exe_brob_release = True
    bp_enable = True
    branch_predictor = 'bimodal_predictor'
    bp_entries = 128
    perf_counters_en = True
