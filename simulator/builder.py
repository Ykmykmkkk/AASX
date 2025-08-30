# --- simulator/builder.py ---# --- simulator/builder.py ---
import os, json
from simulator.domain.domain import Job, Operation
from simulator.model.machine import Machine
from simulator.model.generator import Generator
from simulator.model.transducer import Transducer

def load(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        return json.load(f)

class ModelBuilder:
    def __init__(self, subpath, use_dynamic_scheduling=False):
        # 절대 경로로 변환
        if os.path.isabs(subpath):
            self.path = subpath
        else:
            base = os.path.dirname(__file__)
            self.path = os.path.join(base, subpath)
        
        self.use_dynamic_scheduling = use_dynamic_scheduling

    def build(self):
        jobs_j   = load(os.path.join(self.path, 'jobs.json'))
        ops_j    = load(os.path.join(self.path, 'operations.json'))
        dur_j    = load(os.path.join(self.path, 'operation_durations.json'))
        trans    = load(os.path.join(self.path, 'machine_transfer_time.json'))
        # machines.json이 있으면 사용, 없으면 initial_machine_status.json 사용
        machines_file = os.path.join(self.path, 'machines.json')
        init_machines_file = os.path.join(self.path, 'initial_machine_status.json')
        
        if os.path.exists(machines_file):
            init_m = load(machines_file)
        else:
            init_m = load(init_machines_file)
        releases = load(os.path.join(self.path, 'job_release.json'))

        op_map    = {o['operation_id']: o for o in ops_j}
        
        # 동적 라우팅 사용 (정적 라우팅 제거)
        route_map = {}  # 빈 맵으로 초기화 (동적 할당)

        # release_time 매핑 생성
        release_map = {r['job_id']: r['release_time'] for r in releases}
        
        # 디버깅 정보 제거
        
        jobs = {}
        for j in jobs_j:
            ops = []
            for oid in j['operations']:
                om   = op_map[oid]
                
                # 동적 라우팅 사용 (assigned_machine을 None으로 설정)
                assigned_machine = None  # 동적 할당을 위해 None으로 설정
                
                # 기본 분포 정보 (첫 번째 후보 기계 기준)
                default_machine = om['machines'][0] if om['machines'] else None
                spec = dur_j[om['type']][default_machine] if default_machine else {}
                
                # Operation에 라우팅된 기계와 후보 리스트, 분포를 전달
                ops.append(Operation(
                    op_id=oid,
                    assigned_machine=assigned_machine,  # 동적 모드에서는 None
                    candidate_machines=om['machines'],
                    distribution=spec
                ))
            
            # Job 생성 시 release_time 포함
            job_release_time = release_map.get(j['job_id'], 0.0)
            jobs[j['job_id']] = Job(j['job_id'], j['part_id'], ops, job_release_time)

        machines = []
        for mname, info in init_m.items():
            # 각 머신별 transfer map만 전달
            machine_transfer = trans.get(mname, {})
            machines.append(Machine(mname, machine_transfer, info))

        # 디버깅 정보 제거

        gen = Generator(releases, jobs)
        tx  = Transducer()
        return machines, gen, tx
