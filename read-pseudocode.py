
import salabim as sim
import pe_lib as pe


program = 'add.HS'

env = sim.Environment(trace=True)

# 

processor_node1 = pe.PE(fetch_width=2, physical_registers=64, int_alus=3, rob_entries=128, program=program)


processor_node1.InstrCache_inst.read_program()


env.run(till=500)
