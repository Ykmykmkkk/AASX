# --- simulator/main.py ---
from simulator.engine.simulator import Simulator
from simulator.builder import ModelBuilder

if __name__ == '__main__':
    builder = ModelBuilder('scenarios/my_case')
    machines, gen, tx = builder.build()
    sim = Simulator()
    sim.register(gen)
    sim.register(tx)
    for m in machines:
        sim.register(m)
    gen.initialize()
    sim.run()  # Transducer will save results
