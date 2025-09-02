# --- simulator/builder.py ---# --- simulator/builder.py ---
import os, json
from simulator.domain.domain import Job, Operation
from simulator.model.machine import Machine
from simulator.model.generator import Generator
from simulator.model.transducer import Transducer

def load(fp):
    return json.load(open(fp))

class ModelBuilder:
    def __init__(self, subpath):
        # 절대 경로로 변환
        if os.path.isabs(subpath):
            self.path = subpath
        else:
            base = os.path.dirname(__file__)
            self.path = os.path.join(base, subpath)

    def build(self):
        jobs_j   = load(os.path.join(self.path, 'jobs.json'))
        ops_j    = load(os.path.join(self.path, 'operations.json'))
        dur_j    = load(os.path.join(self.path, 'operation_durations.json'))
        rout     = load(os.path.join(self.path, 'routing_result.json'))
        trans    = load(os.path.join(self.path, 'machine_transfer_time.json'))
        init_m   = load(os.path.join(self.path, 'initial_machine_status.json'))
        releases = load(os.path.join(self.path, 'job_release.json'))

        op_map    = {o['operation_id']: o for o in ops_j}
        route_map = {r['operation_id']: r['assigned_machine'] for r in rout}

        jobs = {}
        for j in jobs_j:
            ops = []
            for oid in j['operations']:
                om   = op_map[oid]
                routed = route_map[oid]
                spec = dur_j[om['type']][routed]
                # Operation에 라우팅된 기계와 후보 리스트, 분포를 전달
                ops.append(Operation(
                    op_id=oid,
                    assigned_machine=routed,
                    candidate_machines=om['machines'],
                    distribution=spec
                ))
            jobs[j['job_id']] = Job(j['job_id'], j['part_id'], ops)

        machines = []
        for mname, info in init_m.items():
            # 각 머신별 transfer map만 전달
            machine_transfer = trans.get(mname, {})
            machines.append(Machine(mname, machine_transfer, info))

        gen = Generator(releases, jobs)
        tx  = Transducer()
        return machines, gen, tx
