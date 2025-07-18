# simulator/builder.py

import os, json
from .domain import Job, Operation
from .models import Machine, Generator, Transducer

def load(fp): return json.load(open(fp))

class ModelBuilder:
    def __init__(self, subpath):
        base = os.path.dirname(__file__)
        self.path = os.path.join(base, subpath)

    def build(self):
        # JSON 로드
        jobs_j    = load(self.path+'/jobs.json')
        ops_j     = load(self.path+'/operations.json')
        dur_j     = load(self.path+'/operation_durations.json')
        rout      = load(self.path+'/routing_result.json')
        transfer  = load(self.path+'/machine_transfer_time.json')
        init_m    = load(self.path+'/initial_machine_status.json')
        releases  = load(self.path+'/job_release.json')

        # operation map, routing map
        op_map    = {o['operation_id']: o for o in ops_j}
        route_map = {r['operation_id']: r['assigned_machine'] for r in rout}

        # Job & Part
        jobs = {}
        for j in jobs_j:
            ops = []
            for oid in j['operations']:
                om  = op_map[oid]
                m   = route_map[oid]
                spec= dur_j[om['type']][m]
                ops.append(Operation(oid, m, spec))
            jobs[j['job_id']] = Job(j['job_id'], j['part_id'], ops)

        # Machines
        machines = []
        for m, info in init_m.items():
            machines.append(Machine(m, transfer[m], info))

        gen = Generator(releases, jobs)
        tx  = Transducer()

        return machines, gen, tx
