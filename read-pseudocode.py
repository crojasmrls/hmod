
import salabim as sim
import fetch_lib as fetch
import reorderbuffer_lib as rob

program = 'binary_search.HS'

env = sim.Environment(trace=True)

# Queues creation

int_queue = sim.Queue("int_queue")
h_queue = sim.Queue("h_queue")
Rob = rob.ReorderBuffer()
InstrCache_inst = fetch.InstrCache(program=program, env1=env, rob=Rob, int_queue=int_queue, h_queue=h_queue)
InstrCache_inst.read_program()

program_begin = InstrCache_inst.send_first_bb()

env.run(till=500)
