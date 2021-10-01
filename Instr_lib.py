

import salabim as sim

class Instr(sim.Component):
    def setup(self, fetch_unit):
        self.fetch_unit = fetch_unit
        self.type = 'none'
    def proccess(self):
        self.state = 'decode'
        yield self.hold(1)#Decode

        #Verificar espacio en cola
        self.state = 'enqued'
        #Check dependencies, wake up logic
        #selec unit, esperar a que la unidad este libre, issue logic
        #esperar, Tiempo de ejecucion.

        if self.type == 'branch' and self.miss_branch_prediction:
            self.fetch_unit.change_pc(self.correct_bb_name)
            #elf.fetch_unit_
        #liberar la unidad 
        self.fetch_unit.rob.instr_end()

    def flush(self):
        self.fetch_unit.rob.instr_end()


