
import salabim as sim
import pe_lib as pe
import pipeline_parameters_1 as par1
import konata_lib as kon


program1 = 'risc-assembly/stores.asm'
program2 = 'risc-assembly/add.asm'
program3 = 'risc-assembly/bublesort.asm'
konata_out = 'konata_signature.txt'
params_1 = par1.PipelineParams
env = sim.Environment(trace=True)

#
KonataSignatureInst = kon.KonataSignature(konata_out=konata_out,
                                          konata_dump_on=True, priority=-2)

PEInst0 = pe.PE(params=params_1, program=program3, thread_id=0, konata_signature=KonataSignatureInst)
# PEInst1 = pe.PE(fetch_width=2, physical_registers=64, int_alus=2, rob_entries=128,
#                 int_queue_slots=16, lsu_slots=16, brob_entries=32,
#                 program=program2, thread_id=1,
#                 konata_signature=KonataSignatureInst)

PEInst0.InstrCacheInst.read_program()
# PEInst1.InstrCacheInst.read_program()


env.run(till=500)
