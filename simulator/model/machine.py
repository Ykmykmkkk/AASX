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
        self.control_tower = None  # Control Tower 연결
        self.next_available_time = 0.0  # 다음 사용 가능 시간
        
        # Job 상태 관리를 위한 큐들 (OperationInfo 대신 Job 상태 직접 관리)
        self.queued_jobs = deque()  # 대기 중인 Job들
        self.running_jobs = deque()  # 실행 중인 Job들
        self.finished_jobs = []  # 완료된 Job들
        
        # 무한 루프 방지를 위한 전송 횟수 추적
        self.transfer_counts = {}  # {job_id: transfer_count}
        self.max_transfers = 1  # 최대 전송 횟수 (1번 전송 후 현재 기계에서 실행)

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
        
        # current_op()이 None인 경우를 처리
        queue_ops = []
        for p in self.queue:
            current_op = p.job.current_op()
            if current_op:
                queue_ops.append(current_op.id)
            else:
                queue_ops.append('DONE')
        
        current_op = part.job.current_op()
        op_id = current_op.id if current_op else 'DONE'
        current_time = EoModel.get_time()
        
        # Job 상태 업데이트
        part.job.set_status(JobStatus.QUEUED)
        part.job.set_location(self.name)
        
        # 대기 중인 Job으로 추가 (중복 방지)
        if part.job not in self.queued_jobs:
            self.queued_jobs.append(part.job)
        
        # Control Tower에 상태 업데이트 전송
        if self.control_tower:
            self._update_control_tower_status()
        
        Recorder.log_queue(part, self.name, current_time, op_id, len(self.queue), queue_ops)

        ev = Event('machine_idle_check', dest_model=self.name)
        self.schedule(ev, 0)

    def _start_if_possible(self):
        if self.status!='idle' or not self.queue:
            return
        
        # release_time이 지난 작업만 처리 가능한지 확인
        current_time = EoModel.get_time()
        available_parts = []
        for part in self.queue:
            if current_time >= part.job.release_time:
                available_parts.append(part)
        
        if not available_parts:
            # 아직 릴리스되지 않은 작업들만 있는 경우 대기
            return
            
        # 동적 스케줄링 사용 여부 확인
        if self.control_tower:
            # Control Tower를 통한 동적 할당 (릴리스된 작업만 대상)
            assignment = self._get_dynamic_assignment(available_parts)
            if assignment:
                part, target_machine = assignment
                if target_machine != self.name:
                    # 다른 기계로 전송
                    self._transfer_to_other_machine(part, target_machine)
                    return
                # 현재 기계에서 실행 - 동적 할당에서 이미 결정됨
                print(f"[Machine {self.name}] 동적 할당으로 현재 기계에서 실행 결정")
            else:
                # 동적 할당 실패 시 기본 FIFO (릴리스된 작업 중에서)
                part = self.dispatch.select(available_parts)
        else:
            # 기존 정적 스케줄링 (릴리스된 작업 중에서)
            part = self.dispatch.select(available_parts)
            
        op = part.job.current_op()
        if op is None:
            print(f"[Machine {self.name}] Job {part.job.id}의 현재 Operation이 없음 - 큐에서 제거")
            # 완료된 Job을 큐에서 제거
            if part in self.queue:
                self.queue.remove(part)
            if part.job in self.queued_jobs:
                self.queued_jobs.remove(part.job)
            # 다음 작업 처리
            ev = Event('machine_idle_check', dest_model=self.name)
            self.schedule(ev, 0)
            return
            
        # 정적 스케줄링 모드에서만 assigned 체크
        if not self.control_tower:
            assigned = op.select_machine()
            if assigned != self.name:
                print(f"[Machine {self.name}] Operation {op.id}이 {assigned}에 할당되어 있음")
                # 다른 기계로 전송
                self._transfer_to_other_machine(part, assigned)
                return
            
        dur = op.sample_duration()

        self.status = 'busy'
        self.running = part
        part.status = 'processing'
        current_time = EoModel.get_time()
        
        # Job 상태 업데이트
        part.job.set_status(JobStatus.RUNNING)
        part.job.set_location(self.name)
        
        # Control Tower에 Job 상태 업데이트
        if self.control_tower:
            job_status = {
                'status': 'running',
                'current_machine': self.name,
                'current_operation': op.id,
                'start_time': current_time,
                'estimated_duration': dur
            }
            self.control_tower.update_job_status(part.job.id, job_status)
        
        # 대기 중에서 실행 중으로 이동
        if part.job in self.queued_jobs:
            self.queued_jobs.remove(part.job)
        self.running_jobs.append(part.job)
        
        # Control Tower에 상태 업데이트 전송
        if self.control_tower:
            self._update_control_tower_status()
        
        Recorder.log_start(part, self.name, current_time, op.id, len(self.queue))
        
        # 작업 완료 이벤트 스케줄링
        ev = Event('end_operation', {'part': part, 'operation_id': op.id}, dest_model=self.name)
        self.schedule(ev, dur)

    def _get_dynamic_assignment(self, available_parts=None):
        """Control Tower를 통해 동적 할당 결정"""
        if available_parts is None:
            available_parts = self.queue
            
        if not self.control_tower or not available_parts:
            print(f"[Machine {self.name}] 동적 할당 불가: control_tower={self.control_tower is not None}, available_parts={len(available_parts) if available_parts else 0}")
            return None
            
        current_time = EoModel.get_time()
        print(f"[Machine {self.name}] 동적 할당 시도 (큐 길이: {len(available_parts)})")
        
        # 현재 기계가 이미 작업 중인지 확인
        if self.status == 'busy' and self.running:
            print(f"[Machine {self.name}] 현재 작업 중: {self.running.job.id} - 다른 작업 할당 불가")
            return None
        
        # 현재 기계의 상태 정보 수집
        machine_status = {
            'name': self.name,
            'status': self.status,
            'queue_length': len(available_parts),
            'next_available_time': self.next_available_time,
            'current_time': current_time,
            'current_job': self.running.job.id if self.running else None,
            'current_operation': self.running.job.current_op().id if self.running and self.running.job.current_op() else None
        }
        
        # Control Tower에 상태 업데이트
        self.control_tower.update_machine_status(self.name, machine_status)
        
        # 다음 작업 선택 (릴리스된 작업만 대상)
        next_part = self.control_tower.select_next_job_for_machine(self.name, available_parts)
        if not next_part:
            print(f"[Machine {self.name}] 다음 작업 없음")
            return None
            
        # Part에서 Job으로 접근
        next_job = next_part.job
        current_op = next_job.current_op()
        
        # 현재 Operation이 없는 경우 (Job 완료 또는 오류)
        if current_op is None:
            print(f"[Machine {self.name}] Job {next_job.id}의 현재 Operation이 없음 (완료됨)")
            return None
            
        print(f"[Machine {self.name}] 다음 작업: {next_job.id}, Operation: {current_op.id}")
        
        # 최적 기계 선택
        operation_id = current_op.id
        job_id = next_job.id
        available_machines = self.control_tower.get_available_machines(operation_id)
        
        # 무한 루프 방지: 전송 횟수 확인
        transfer_count = self.transfer_counts.get(job_id, 0)
        if transfer_count >= self.max_transfers:
            print(f"[Machine {self.name}] Job {job_id} 전송 횟수 초과 ({transfer_count}), 현재 기계에서 실행")
            return (next_part, self.name)
        
        optimal_machine = self.control_tower.select_optimal_machine_for_operation(
            operation_id, job_id, available_machines, current_time
        )
        
        if optimal_machine:
            print(f"[Machine {self.name}] 동적 할당 결과: {optimal_machine}")
            if optimal_machine != self.name:
                print(f"[Machine {self.name}] 전송 필요: {self.name} → {optimal_machine}")
                # 전송 횟수 증가
                self.transfer_counts[job_id] = transfer_count + 1
            else:
                print(f"[Machine {self.name}] 현재 기계에서 실행")
                # 현재 기계에서 실행하면 전송 횟수 초기화
                if job_id in self.transfer_counts:
                    del self.transfer_counts[job_id]
        
        return (next_part, optimal_machine) if optimal_machine else None

    def _transfer_to_other_machine(self, part, target_machine):
        """다른 기계로 작업 전송"""
        # 현재 큐에서 제거
        if part in self.queue:
            self.queue.remove(part)
        if part.job in self.queued_jobs:
            self.queued_jobs.remove(part.job)
        
        # 전송 시간 계산 (분포에서 샘플링)
        transfer_spec = self.transfer.get(target_machine, {})
        if transfer_spec:
            dist = transfer_spec.get('distribution')
            if dist == 'normal':
                transfer_time = max(0, random.gauss(transfer_spec['mean'], transfer_spec['std']))
            elif dist == 'uniform':
                transfer_time = random.uniform(transfer_spec.get('low', 0), transfer_spec.get('high', 0))
            elif dist == 'exponential':
                transfer_time = random.expovariate(transfer_spec['rate'])
            else:
                transfer_time = 0.0
        else:
            transfer_time = 0.0
        
        # 전송 이벤트 스케줄링
        ev = Event('part_arrival', {'part': part}, dest_model=target_machine)
        self.schedule(ev, transfer_time)
        
        # 전송 횟수 로그
        transfer_count = self.transfer_counts.get(part.job.id, 0)
        print(f"[전송] {self.name} → {target_machine}: {part.job.id} (전송시간: {transfer_time:.2f}, 전송횟수: {transfer_count})")

    def _update_control_tower_status(self):
        """Control Tower에 현재 상태 업데이트"""
        if not self.control_tower:
            return
            
        current_time = EoModel.get_time()
        machine_status = {
            'name': self.name,
            'status': self.status,
            'queue_length': len(self.queue),
            'next_available_time': self.next_available_time,
            'current_time': current_time,
            'queued_jobs': [job.id for job in self.queued_jobs],
            'running_jobs': [job.id for job in self.running_jobs]
        }
        
        self.control_tower.update_machine_status(self.name, machine_status)

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
            
            # queue와 queued_jobs에서 제거
            if part in self.queue:
                self.queue.remove(part)
            if part.job in self.queued_jobs:
                self.queued_jobs.remove(part.job)
            
            # Control Tower에 Job 완료 상태 업데이트
            if self.control_tower:
                job_status = {
                    'status': 'completed',
                    'completion_time': current_time,
                    'final_machine': self.name
                }
                self.control_tower.update_job_status(part.job.id, job_status)
            
            Recorder.log_done(part, EoModel.get_time())
            done_ev = Event('job_completed', {'part': part}, dest_model='transducer')
            self.schedule(done_ev, 0)
        else:
            # 다음 기계로 전송
            current_op = part.job.current_op()
            nxt = current_op.select_machine() if current_op else None
            
            # 동적 스케줄링 모드에서 nxt가 None인 경우
            if nxt is None:
                # 첫 번째 후보 기계로 전송 (임시 할당)
                candidates = part.job.current_op().candidates
                if candidates:
                    nxt = candidates[0]  # 첫 번째 후보 기계 선택
                else:
                    print(f"경고: Job {part.job.id}의 Operation {part.job.current_op().id}에 후보 기계가 없습니다.")
                    # Job을 완료된 것으로 처리
                    part.job.set_status(JobStatus.DONE)
                    part.job.set_location(None)
                    self.finished_jobs.append(part.job)
                    
                    # Control Tower에 Job 완료 상태 업데이트
                    if self.control_tower:
                        job_status = {
                            'status': 'completed',
                            'completion_time': current_time,
                            'final_machine': self.name
                        }
                        self.control_tower.update_job_status(part.job.id, job_status)
                    
                    Recorder.log_done(part, EoModel.get_time())
                    done_ev = Event('job_completed', {'part': part}, dest_model='transducer')
                    self.schedule(done_ev, 0)
                    self.running = None
                    self.status = 'idle'
                    ev = Event('machine_idle_check', dest_model=self.name)
                    self.schedule(ev, 0)
                    return
            
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
            
            # queued_jobs에서 제거 (전송 중이므로)
            if part.job in self.queued_jobs:
                self.queued_jobs.remove(part.job)
            
            # Control Tower에 Job 전송 상태 업데이트
            if self.control_tower:
                job_status = {
                    'status': 'transfer',
                    'from_machine': self.name,
                    'to_machine': nxt,
                    'transfer_time': delay,
                    'next_operation': part.job.current_op().id
                }
                self.control_tower.update_job_status(part.job.id, job_status)

            Recorder.log_transfer(part, self.name, nxt, EoModel.get_time(), delay)

            ev = Event('part_arrival', {'part': part}, dest_model=nxt)
            self.schedule(ev, delay)
        
        self.running = None
        self.status = 'idle'
        
        # Control Tower에 상태 업데이트
        if self.control_tower:
            self._update_control_tower_status()
        
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
