from simulator.engine.simulator import EoModel, Event
from simulator.dispatch.dispatch import FIFO
from simulator.result.recorder import Recorder
from simulator.domain.domain import JobStatus
from collections import deque
import random
from enum import Enum, auto

class OperationStatus(Enum):
    QUEUED = auto()
    RUNNING = auto()
    TRANSFER = auto()
    DONE = auto()

class OperationInfo:
    def __init__(self, operation_id, status, location, input_timestamp=None, output_timestamp=None):
        self.operation_id = operation_id
        self.status = status  # OperationStatus Enum
        self.location = location
        self.input_timestamp = input_timestamp
        self.output_timestamp = output_timestamp

    def to_dict(self):
        return {
            'operation_id': self.operation_id,
            'status': self.status.name,  # Enum의 이름으로 저장
            'location': self.location,
            'input_timestamp': self.input_timestamp,
            'output_timestamp': self.output_timestamp
        }

class Machine(EoModel):
    def __init__(self, name, transfer_map, initial, dispatch_rule='fifo'):
        super().__init__(name)
        self.status = initial['status']
        self.queue = deque()
        self.running = None
        self.transfer = transfer_map
        self.dispatch = FIFO() if dispatch_rule=='fifo' else FIFO()
        
        # Job 상태 관리를 위한 큐들 (OperationInfo 대신 Job 상태 직접 관리)
        self.queued_jobs = deque()  # 대기 중인 Job들
        self.running_jobs = deque()  # 실행 중인 Job들
        self.finished_jobs = []  # 완료된 Job들

    def handle_event(self, evt):
        et = evt.event_type
        if et in ('material_arrival','part_arrival'):
            part = evt.payload['part']
            self._enqueue(part)

        elif et == 'machine_idle_check':
            self._start_if_possible()

        elif et in ('end_operation','operation_complete'):
            op_id = evt.payload.get('operation_id')
            self._finish(op_id)

    def _enqueue(self, part):
        self.queue.append(part)
        queue_ops = [p.job.current_op().id for p in self.queue]
        op_id = part.job.current_op().id
        current_time = EoModel.get_time()
        
        # Job 상태 업데이트
        part.job.set_status(JobStatus.QUEUED)
        part.job.set_location(self.name)
        
        # 대기 중인 Job으로 추가
        self.queued_jobs.append(part.job)
        
        Recorder.log_queue(part, self.name, current_time, op_id, len(self.queue), queue_ops)

        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)

    def _start_if_possible(self):
        if self.status!='idle' or not self.queue:
            return
        part = self.dispatch.select(self.queue)
        op   = part.job.current_op()
        assigned = op.select_machine()
        assert assigned == self.name, f"Expected {self.name}, got {assigned}"
        dur = op.sample_duration()

        self.status  = 'busy'
        self.running = part
        part.status  = 'processing'
        current_time = EoModel.get_time()
        
        # Job 상태 업데이트
        part.job.set_status(JobStatus.RUNNING)
        part.job.set_location(self.name)
        
        # 대기 중에서 실행 중으로 이동
        if part.job in self.queued_jobs:
            self.queued_jobs.remove(part.job)
        self.running_jobs.append(part.job)
        
        Recorder.log_start(part, self.name, current_time, op.id, len(self.queue))

        ev = Event('end_operation', {'part': part, 'operation_id': op.id}, dest_model=self.name)
        self.schedule(ev, dur)

    def _finish(self, op_id=None):
        part = self.running
        current_time = EoModel.get_time()
        
        # Job 완료 시간 업데이트
        part.job.set_completion_time(current_time)
        
        # 실행 중에서 제거
        if part.job in self.running_jobs:
            self.running_jobs.remove(part.job)
        
        Recorder.log_end(part, self.name, current_time, op_id)

        part.job.advance()
        if part.job.done():
            # Job 완료
            part.job.set_status(JobStatus.DONE)
            part.job.set_location(None)
            self.finished_jobs.append(part.job)
            
            Recorder.log_done(part, EoModel.get_time())
            done_ev = Event('job_completed', {'part': part}, dest_model='transducer')
            self.schedule(done_ev, 0)
        else:
            # 다음 기계로 전송
            nxt  = part.job.current_op().select_machine()
            spec = self.transfer.get(nxt, {})
            dist = spec.get('distribution')
            if dist=='normal':
                delay = max(0, random.gauss(spec['mean'], spec['std']))
            elif dist=='uniform':
                delay = random.uniform(spec.get('low',0), spec.get('high',0))
            elif dist=='exponential':
                delay = random.expovariate(spec['rate'])
            else:
                delay = 0

            # Job 상태를 TRANSFER로 설정
            part.job.set_status(JobStatus.TRANSFER)
            part.job.set_location(f"{self.name}->{nxt}")

            Recorder.log_transfer(part, self.name, nxt, EoModel.get_time(), delay)

            ev = Event('part_arrival', {'part': part}, dest_model=nxt)
            self.schedule(ev, delay)

        self.running = None
        self.status  = 'idle'
        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)

    def get_queue_status(self):
        print(f"\n=== {self.name} 큐 상태 ===")
        print(f"현재 상태: {self.status}")
        print(f"대기 중인 파트 수: {len(self.queue)}")
        
        print(f"\n대기 중인 Job들 (queued_jobs):")
        if self.queued_jobs:
            for i, job in enumerate(self.queued_jobs):
                print(f"  {i+1}. Job {job.id}, Part {job.part_id}, Operation {job.current_op().id if job.current_op() else 'None'}")
                print(f"      상태: {job.status.name}, 위치: {job.current_location}, 진행률: {job.get_progress():.2f}")
        else:
            print("  비어있음")
            
        print(f"\n실행 중인 Job들 (running_jobs):")
        if self.running_jobs:
            for i, job in enumerate(self.running_jobs):
                print(f"  {i+1}. Job {job.id}, Part {job.part_id}, Operation {job.current_op().id if job.current_op() else 'None'}")
                print(f"      상태: {job.status.name}, 위치: {job.current_location}, 진행률: {job.get_progress():.2f}")
        else:
            print("  비어있음")
            
        print(f"\n현재 큐의 operation 목록:")
        if self.queue:
            for i, part in enumerate(self.queue):
                op = part.job.current_op()
                job = part.job
                print(f"  {i+1}. Part {part.id}, Operation {op.id if op else 'None'}")
                print(f"      Job 상태: {job.status.name}, 진행률: {job.get_progress():.2f}")
        else:
            print("  비어있음")
        print("=" * 30)

    def clear_queues(self):
        self.queued_jobs.clear()
        self.running_jobs.clear()
        self.finished_jobs.clear()
        
    def get_job_status_summary(self):
        """현재 머신에서 관리하는 모든 Job의 상태 요약을 반환합니다."""
        summary = {
            'machine_name': self.name,
            'queued_jobs': [job.to_dict() for job in self.queued_jobs],
            'running_jobs': [job.to_dict() for job in self.running_jobs],
            'finished_jobs': [job.to_dict() for job in self.finished_jobs],
            'total_jobs': len(self.queued_jobs) + len(self.running_jobs) + len(self.finished_jobs)
        }
        return summary
