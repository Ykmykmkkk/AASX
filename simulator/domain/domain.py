# --- simulator/domain/domain.py ---
import random

class Operation:
    def __init__(self, op_id, assigned_machine, candidate_machines, distribution):
        """
        :param op_id: Operation ID
        :param assigned_machine: 실제 라우팅된 기계 이름
        :param candidate_machines: 가능한 기계 리스트
        :param distribution: 작업 소요 시간 분포 파라미터
        """
        self.id = op_id
        self.assigned_machine = assigned_machine
        self.candidates = candidate_machines
        self.distribution = distribution

    def select_machine(self):
        # 항상 라우팅된 기계를 반환
        return self.assigned_machine

    def sample_duration(self):
        d = self.distribution
        t = d['distribution']
        if t == 'normal':
            return max(0, random.gauss(d['mean'], d['std']))
        if t == 'uniform':
            return random.uniform(d['low'], d['high'])
        if t == 'exponential':
            return random.expovariate(d['rate'])
        raise RuntimeError('Unknown distribution')

class Job:
    def __init__(self, job_id, part_id, operations):
        """
        :param job_id: Job identifier
        :param part_id: Part identifier
        :param operations: list of Operation instances
        """
        self.id = job_id
        self.part_id = part_id
        self.ops = operations
        self.idx = 0

    def current_op(self):
        return self.ops[self.idx] if self.idx < len(self.ops) else None

    def advance(self):
        self.idx += 1

    def done(self):
        return self.idx >= len(self.ops)

class Part:
    def __init__(self, part_id, job):
        """
        :param part_id: Part identifier
        :param job: Job instance this part belongs to
        """
        self.id = part_id
        self.job = job
        self.status = 'new'