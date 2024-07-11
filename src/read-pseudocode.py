import time
import argparse
import os
import salabim as sim
import atomic_model as atm
import pe_lib as pe
import pipeline_parameters_1 as par1
import rv64uih_lib as dec
import konata_lib as kon
import counters_lib as pec

# In recent version of Salabim it is necessary to disable the yieldless attribute to model with coroutines
try:
    sim.yieldless(False)
except AttributeError:
    pass
# Arguments
args_parser = argparse.ArgumentParser(
    prog="HMOD",
    description="Run agile RISC-V microarchitecture simulations",
    epilog="Copyright 2024 Carlos Rojas Morales",
)
args_parser.add_argument(
    "-s",
    "--Assembly",
    help="RISC-V assembly code to execute",
    default="./risc-v-examples/c_implementations/matrix_mul.s",
    type=str,
)
args_parser.add_argument(
    "-o",
    "--Outdir",
    help="output results directory",
    default="./output",
    type=str,
)
args_parser.add_argument(
    "-k",
    "--Konata",
    help="dump konata trace",
    action="store_true",
    default=False,
)
args_parser.add_argument(
    "-t",
    "--Tracer",
    help="dump signature trace",
    action="store_true",
    default=False,
)
args_parser.add_argument(
    "--Konata_name",
    help="konata trace file name",
    default="konata_signature.txt",
    type=str,
)
args_parser.add_argument(
    "--Tracer_name",
    help="signature trace file name",
    default="torture_signature.sig",
    type=str,
)
args_parser.add_argument(
    "-c",
    "--Cycles",
    help="maximun simulation cycles",
    default=400000,
    type=int,
)
args_parser.add_argument(
    "-m",
    "--Metrics",
    help="dump metrics in csv format",
    action="store_true",
    default=False,
)
args_parser.add_argument(
    "--Metrics_name",
    help="metrics file name",
    default="stats.csv",
    type=str,
)

args_parser.add_argument(
    "-a",
    "--Atomic",
    help="execute the program using the atomic model, no metrics or konata trace available",
    action="store_true",
    default=False,
)

args = args_parser.parse_args()
program = args.Assembly
outdir = args.Outdir
cycles = args.Cycles
konata_dump_on = args.Konata
torture_dump_on = args.Tracer
metrics_dump_on = args.Metrics
atomic_model = args.Atomic
if atomic_model:
    konata_dump_on = False
    metrics_dump_on = False
konata_out = f"{outdir}/{args.Konata_name}"
torture_out = f"{outdir}/{args.Tracer_name}"
metrics_out = f"{outdir}/{args.Metrics_name}"
os.makedirs(outdir, exist_ok=True)

params_1 = par1.PipelineParams
mem_map_1 = par1.MemoryMap
init_reg_values = par1.RegisterInit.init_reg_values
register_table = dec.IntRegisterTable.registers

env = sim.Environment(trace=False)

KonataSignatureInst = kon.KonataSignature(
    konata_out=konata_out,
    konata_dump_on=konata_dump_on,
    torture_out=torture_out,
    torture_dump_on=torture_dump_on,
    tracer_with_konata_id=False,
    priority=-2,
)

if atomic_model:
    AtomicModelInst = atm.AtomicModel(
        params=params_1, thread_id=0, konata_signature=KonataSignatureInst
    )

    AtomicModelInst.pe.ASMParserInst.read_program(program, mem_map_1)
    AtomicModelInst.pe.RFInst.init_regs(init_reg_values, register_table)
    start = time.time()
    AtomicModelInst.run()
    end = time.time()
else:
    PerformanceCountersInst = pec.PerformanceCounters()
    PEInst0 = pe.PE(
        params=params_1,
        thread_id=0,
        konata_signature=KonataSignatureInst,
        performance_counters=PerformanceCountersInst,
    )
    PEInst0.ASMParserInst.read_program(program, mem_map_1)
    PEInst0.RFInst.init_regs(init_reg_values, register_table)
    # PEInst0.InstrCacheInst.print_program()
    # record start time
    start = time.time()
    env.run(till=cycles)
    # record end time
    end = time.time()
    if metrics_dump_on:
        PerformanceCountersInst.dump_metrics(metrics_out)
    PerformanceCountersInst.print_metrics()

print("Execution time: ", round(end - start, 2), "s")
print("Cycles: ", cycles)
# print("Instructions: ", PEInst0.FetchUnitInst.instr_id)
print("Simulated cycles per second:", round(cycles / (end - start), 2))
# print(
#     "Simulated instructions per second:",
#     round(PEInst0.FetchUnitInst.instr_id / (end - start), 2),
# )
# print("Data cache dump:")
# PEInst0.DataCacheInst.print_data_cache()
