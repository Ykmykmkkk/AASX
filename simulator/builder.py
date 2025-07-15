# builder.py
import os
import json
from domain import Job, Operation
from models import Machine, Generator, Transducer

class ModelBuilder:
    def __init__(self, scenario_path: str):
        self.scenario_path = scenario_path

    def load_json(self, filename: str):
        with open(os.path.join(self.scenario_path, filename), 'r') as f:
            return json.load(f)

    def build_models(self):
        # Load scenario files
        releases = self.load_json('job_release.json')
        templates = self.load_json('job_templates.json')
        durations = self.load_json('operation_durations.json')
        machine_names = self.load_json('machines.json')

        # Build jobs
        jobs = {}
        for job_id, tmpl in templates.items():
            ops = [
                Operation(op['op_id'], op['machine'],
                          durations[op['op_type']][op['machine']])
                for op in tmpl['operations']
            ]
            # Assign machine for each operation
            for op in ops:
                op.assigned_machine = op.candidate_machine
            jobs[job_id] = Job(job_id, ops)

        # Build machines
        machines = [Machine(name) for name in machine_names]

        # Generator & Transducer
        generator = Generator(releases, jobs)
        transducer = Transducer()

        return machines, generator, transducer