# simulator/main.py

from simulator.simulator import Simulator
from simulator.builder   import ModelBuilder

if __name__=='__main__':
    builder  = ModelBuilder('scenarios/my_case')
    machines, gen, tx = builder.build()

    sim = Simulator()
    sim.register_model(gen)
    sim.register_model(tx)
    for m in machines:
        sim.register_model(m)

    gen.initialize()
    sim.run()
    tx.report()
