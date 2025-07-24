# --- simulator/builder.py ---
import os, json
from simulator.domain.domain import Job, Operation
from simulator.model.machine import Machine
from simulator.model.generator import Generator
from simulator.model.transducer import Transducer

def load(fp): return json.load(open(fp))

class ModelBuilder:
    def __init__(self, subpath):
        base=os.path.dirname(__file__)
        self.path=os.path.join(base, subpath)

    def build(self):
        jobs_j = load(self.path+'/jobs.json')
        ops_j = load(self.path+'/operations.json')
        dur_j = load(self.path+'/operation_durations.json')
        rout  = load(self.path+'/routing_result.json')
        trans = load(self.path+'/machine_transfer_time.json')
        init  = load(self.path+'/initial_machine_status.json')
        rel   = load(self.path+'/job_release.json')

        op_map = {o['operation_id']:o for o in ops_j}
        route_map = {r['operation_id']:r['assigned_machine'] for r in rout}

        jobs={} 
        for j in jobs_j:
            ops=[]
            for oid in j['operations']:
                om=op_map[oid]
                m=route_map[oid]
                spec=dur_j[om['type']][m]
                ops.append(Operation(oid, om['machines'], spec))
            jobs[j['job_id']]=Job(j['job_id'],j['part_id'],ops)

        machines=[]
        for mname, info in init.items():
            machines.append(Machine(mname, trans, info))

        gen=Generator(rel, jobs)
        tx = Transducer()
        return machines, gen, tx
