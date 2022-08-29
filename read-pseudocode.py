
import salabim as sim
import pe_lib as pe
import konata_lib as kon


program1 = 'risc-assembly/stores.asm'
program2 = 'risc-assembly/add.asm'
konata_out = 'konata_signature.txt'

env = sim.Environment(trace=True)

#
KonataSignatureInst = kon.KonataSignature(konata_out=konata_out,
                                          konata_dump_on=True, priority=-1)

PEInst0 = pe.PE(fetch_width=2, physical_registers=64, int_alus=2, rob_entries=128,
                int_queue_slots=16, lsu_slots=16, brob_entries=32,
                program=program1, thread_id=0,
                konata_signature=KonataSignatureInst)

PEInst0.InstrCacheInst.read_program()


env.run(till=500)
