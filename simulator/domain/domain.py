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
        :param assigned_machine: 실제 라우팅된 기계 이름 (동적 모드에서는 None)
        :param candidate_machines: 가능한 기계 리스트
        :param distribution: 작업 소요 시간 분포 파라미터
        """
        self.id = op_id
        self.assigned_machine = assigned_machine
        self.candidates = candidate_machines
        self.distribution = distribution

    def select_machine(self):
        # 동적 할당 모드에서는 None 반환 (실시간 결정 필요)
        if self.assigned_machine is None:
            return None
        # 정적 할당 모드에서는 고정된 기계 반환
        return self.assigned_machine

    def sample_duration(self, machine_id=None):
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
    def __init__(self, job_id, part_id, operations, release_time=0.0):
        """
        :param job_id: Job identifier
        :param part_id: Part identifier
        :param operations: list of Operation instances
        :param release_time: Job release time
        """
        self.id = job_id
        self.part_id = part_id
        self.ops = operations
        self.idx = 0
        self.release_time = release_time
        
        # 상태 관리
        self.status = JobStatus.QUEUED
        self.current_location = None
        self.last_completion_time = None
        self.completion_time = None  # makespan 계산을 위한 속성
        self.total_operations = len(operations)
        self.completed_operations = 0

    def current_op(self):
        return self.ops[self.idx] if self.idx < len(self.ops) else None

    def advance(self):
        self.idx += 1
        self.completed_operations += 1

    def done(self):
        return self.idx >= len(self.ops)
    
    def set_status(self, status):
        self.status = status
    
    def set_location(self, location):
        self.current_location = location
    
    def set_completion_time(self, timestamp):
        self.last_completion_time = timestamp
        self.completion_time = timestamp  # makespan 계산을 위한 속성
    
    def get_progress(self):
        if self.total_operations == 0:
            return 1.0
        return self.completed_operations / self.total_operations
    
    def get_remaining_operations(self):
        return self.total_operations - self.completed_operations
    
    def to_dict(self):
        current_op = self.current_op()
        return {
            'job_id': self.id,
            'part_id': self.part_id,
            'status': self.status.name,
            'current_location': self.current_location,
            'last_completion_time': self.last_completion_time,
            'total_operations': self.total_operations,
            'completed_operations': self.completed_operations,
            'current_operation': current_op.id if current_op else None,
            'progress': self.get_progress(),
            'remaining_operations': self.get_remaining_operations()
        }
    
    def save_state(self):
        """최소한의 상태 정보만 저장"""
        return {
            'job_id': self.id,
            'idx': self.idx,
            'status': self.status,
            'current_location': self.current_location,
            'last_completion_time': self.last_completion_time,
            'completed_operations': self.completed_operations
        }
    
    def restore_state(self, state):
        self.idx = state['idx']
        self.status = state['status']
        self.current_location = state['current_location']
        self.last_completion_time = state['last_completion_time']
        self.completed_operations = state['completed_operations']

class Part:
    def __init__(self, part_id, job):
        """
        :param part_id: Part identifier
        :param job: Job instance this part belongs to
        """
        self.id = part_id
        self.job = job
        self.status = 'new'