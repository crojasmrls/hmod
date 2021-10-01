
import salabim as sim
import fetch_lib as fetch
import Instr_lib as instr
import ReorderBuffer_lib as ROB

program = 'binary_search.HS'


env = sim.Environment(trace=True)
rob= ROB.ReorderBuffer()
InstrCache_inst = fetch.InstrCache(program=program, env1=env, rob=rob)
InstrCache_inst.read_program()

program_begin = InstrCache_inst.send_first_bb()

env.run(till=500)
