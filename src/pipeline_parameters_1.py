class PipelineParams:
    fetch_width = 2
    physical_registers = 128
    int_alus = 2
    branch_units = 1
    rob_entries = 128
    int_queue_slots = 32
    lsu_slots = 64
    brob_entries = 32
    branch_in_int_alu = True
    exe_brob_release = True
    bp_enable = True
    branch_predictor = 'bimodal_predictor'
    bp_entries = 1024
