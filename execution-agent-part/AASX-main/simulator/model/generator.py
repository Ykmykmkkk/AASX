# --- simulator/model/generator.py ---
from simulator.engine.simulator import EoModel, Event
from simulator.domain.domain import Part

class Generator(EoModel):
    def __init__(self, releases, jobs):
        super().__init__('generator')
        self.releases, self.jobs = releases, jobs

    def initialize(self):
        for r in self.releases:
            job = self.jobs[r['job_id']]
            part = Part(r['part_id'], job)
            dest = job.current_op().select_machine()
            ev = Event('material_arrival', {'part':part}, dest_model=dest)
            self.schedule(ev, r['release_time'])

    def handle_event(self, evt): pass