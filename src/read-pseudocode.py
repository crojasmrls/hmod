import time
import salabim as sim
import pe_lib as pe
import pipeline_parameters_1 as par1
import konata_lib as kon
import counters_lib as pec

# In recent version of Salabim it is necessary to disable the yieldless atribute to model with coroutines
try:
    sim.yieldless(False)
except AttributeError:
    pass


program1 = "risc-assembly/stores.asm"
program2 = "risc-assembly/add.asm"
program3 = "risc-assembly/bublesort.asm"
program4 = "c_implementations/bubblesort.s"
konata_out = "konata_signature.txt"
torture_out = "torture_signature.sig"
cycles = 5000
konata_dump_on = True
torture_dump_on = True
params_1 = par1.PipelineParams
mem_map_1 = par1.MemoryMap
perf_counters_en = params_1.perf_counters_en
env = sim.Environment(trace=False)
#
KonataSignatureInst = kon.KonataSignature(
    konata_out=konata_out,
    konata_dump_on=konata_dump_on,
    torture_out=torture_out,
    torture_dump_on=torture_dump_on,
    priority=-2,
)
#
PerformanceCountersInst = pec.PerformanceCounters(perf_counters_en)

PEInst0 = pe.PE(
    params=params_1,
    thread_id=0,
    konata_signature=KonataSignatureInst,
    performance_counters=PerformanceCountersInst,
)
# PEInst1 = pe.PE(fetch_width=2, physical_registers=64, int_alus=2, rob_entries=128,
#                 int_queue_slots=16, lsu_slots=16, brob_entries=32,
#                 program=program2, thread_id=1,
#                 konata_signature=KonataSignatureInst)

PEInst0.ASMParserInst.read_program("../risc-v-examples/" + program4, mem_map_1)
PEInst0.InstrCacheInst.print_program()
# PEInst1.InstrCacheInst.read_program()

# record start time
start = time.time()
env.run(till=cycles)
# record end time
end = time.time()
print("Execution time: ", round(end - start, 2), "s")
print("Cycles: ", cycles)
print("Instructions: ", PEInst0.FetchUnitInst.instr_id)
print("Simulated cycles per second:", round(cycles / (end - start), 2))
print(
    "Simulated instructions per second:",
    round(PEInst0.FetchUnitInst.instr_id / (end - start), 2),
)
print("Data cache dump:")
PEInst0.DataCacheInst.print_data_cache()
if perf_counters_en:
    PerformanceCountersInst.print_metrics()
