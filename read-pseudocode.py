
import salabim as sim
import pe_lib as pe


program = 'risc-assembly/add.asm'

env = sim.Environment(trace=True)

# 

PEInst0 = pe.PE(fetch_width=2, physical_registers=64, int_alus=3, rob_entries=128,
                int_queue_slots=16, store_buffer_slots=16, program=program)


PEInst0.InstrCacheInst.read_program()


env.run(till=50)
