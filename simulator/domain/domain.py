# --- simulator/domain/domain.py ---
import random
from enum import Enum, auto

class JobStatus(Enum):
    QUEUED = auto()
    RUNNING = auto()
    TRANSFER = auto()
    DONE = auto()

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
        
        # 상태 관리 추가
        self.status = JobStatus.QUEUED
        self.current_location = None  # 현재 위치 (머신 이름 또는 "src->dest" 형태)
        self.last_completion_time = None  # 가장 최근에 일을 마쳤을 때의 timestamp
        self.total_operations = len(operations)  # 수행해야 하는 operation의 개수
        self.completed_operations = 0  # 완료된 operation의 개수

    def current_op(self):
        return self.ops[self.idx] if self.idx < len(self.ops) else None

    def advance(self):
        self.idx += 1
        self.completed_operations += 1

    def done(self):
        return self.idx >= len(self.ops)
    
    def set_status(self, status):
        """상태를 설정합니다."""
        self.status = status
    
    def set_location(self, location):
        """현재 위치를 설정합니다."""
        self.current_location = location
    
    def set_completion_time(self, timestamp):
        """최근 완료 시간을 설정합니다."""
        self.last_completion_time = timestamp
    
    def get_progress(self):
        """작업 진행률을 반환합니다 (0.0 ~ 1.0)."""
        if self.total_operations == 0:
            return 1.0
        return self.completed_operations / self.total_operations
    
    def get_remaining_operations(self):
        """남은 operation 개수를 반환합니다."""
        return self.total_operations - self.completed_operations
    
    def to_dict(self):
        """Job의 현재 상태를 딕셔너리로 반환합니다."""
        return {
            'job_id': self.id,
            'part_id': self.part_id,
            'status': self.status.name,
            'current_location': self.current_location,
            'last_completion_time': self.last_completion_time,
            'total_operations': self.total_operations,
            'completed_operations': self.completed_operations,
            'current_operation': self.current_op().id if self.current_op() else None,
            'progress': self.get_progress(),
            'remaining_operations': self.get_remaining_operations()
        }

class Part:
    def __init__(self, part_id, job):
        """
        :param part_id: Part identifier
        :param job: Job instance this part belongs to
        """
        self.id = part_id
        self.job = job
        self.status = 'new'