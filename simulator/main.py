# main.py
from builder import ModelBuilder
from simulator import Simulator

if __name__ == '__main__':
    # Initialize builder
    builder = ModelBuilder('scenarios/my_case')
    machines, generator, transducer = builder.build_models()

    # Setup simulator
    sim = Simulator()
    sim.register_model(generator)
    sim.register_model(transducer)
    for m in machines:
        sim.register_model(m)

    # Start simulation
    generator.initialize()
    sim.run()

    # Report results
    transducer.report()
