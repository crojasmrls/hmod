
import salabim as sim
import fetch_lib as fetch
import reorderbuffer_lib as rob

program = 'binary_search.HS'

env = sim.Environment(trace=True)

# Queues creation

IntQueue = sim.Queue("IntQueue")
HQueue = sim.Queue("HQueue")
Rob = rob.ReorderBuffer()
InstrCache_inst = fetch.InstrCache(program=program, env1=env, rob=Rob)
InstrCache_inst.read_program()

program_begin = InstrCache_inst.send_first_bb()

env.run(till=500)
