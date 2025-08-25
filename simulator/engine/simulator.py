# --- simulator/engine/simulator.py ---
import heapq
import copy
import random
from enum import Enum, auto

class DecisionEpoch(Enum):
    MACHINE_IDLE = auto()
    JOB_RELEASE = auto()
    OPERATION_COMPLETE = auto()

class Action:
    def __init__(self, operation_id, machine_id, insert_position=None):
        self.operation_id = operation_id
        self.machine_id = machine_id
        self.insert_position = insert_position  # 기계 내 삽입 위치 (None이면 큐 끝)
    
    def __repr__(self):
        return f"Action({self.operation_id} -> {self.machine_id}, pos={self.insert_position})"

class SimulatorState:
    def __init__(self, current_time, event_queue, models_state, machines_state, rng_state):
        self.current_time = current_time
        self.event_queue = event_queue
        self.models_state = models_state
        self.machines_state = machines_state
        self.rng_state = rng_state

class Event:
    __slots__ = ('time','event_type','payload','src_model','dest_model')

    def __init__(self, event_type, payload=None, dest_model=None, time=0.0):
        self.time = time
        self.event_type = event_type
        self.payload = payload or {}
        self.src_model = None
        self.dest_model = dest_model

    def __lt__(self, other):
        return self.time < other.time

    def set_src(self, name):
        self.src_model = name

    def set_time(self, t):
        self.time = t

    def __repr__(self):
        return f"Event(time={self.time:.2f}, type={self.event_type}, from={self.src_model}, to={self.dest_model}, payload={self.payload})"

class EoModel:
    push_event = None
    get_time = None

    @classmethod
    def bind(cls, push_fn, time_fn):
        cls.push_event = push_fn
        cls.get_time = time_fn

    def __init__(self, name):
        self.name = name

    def schedule(self, event, delay=0.0):
        if not EoModel.push_event:
            raise RuntimeError("Simulator not bound")
        event.set_src(self.name)
        event.set_time(EoModel.get_time() + delay)
        EoModel.push_event(event)

    def handle_event(self, event):
        raise NotImplementedError

class Simulator:
    def __init__(self, control_tower=None):
        self.current_time = 0.0
        self.event_queue = []
        self.models = {}
        self.machines = []  # 기계 목록 저장
        self.control_tower = control_tower  # Control Tower 연결
        self.decision_epochs = []  # 결정 시점들
        self.best_objective = float('inf')
        self.best_schedule = None
        EoModel.bind(self.push, self.now)

    def push(self, event):
        heapq.heappush(self.event_queue, event)

    def now(self):
        return self.current_time

    def register(self, model):
        self.models[model.name] = model
        # 기계 모델인 경우 별도로 저장 및 Control Tower 연결
        if hasattr(model, 'queued_jobs'):
            self.machines.append(model)
            # Machine에 Control Tower 연결
            if self.control_tower and hasattr(model, 'control_tower'):
                model.control_tower = self.control_tower

    def snapshot(self):
        """현재 시뮬레이터 상태의 스냅샷을 생성합니다."""
        # 이벤트 큐 복사
        event_queue_copy = []
        for event in self.event_queue:
            event_copy = Event(
                event.event_type,
                copy.deepcopy(event.payload),
                event.dest_model,
                event.time
            )
            event_copy.src_model = event.src_model
            event_queue_copy.append(event_copy)
        
        # 모델 상태 복사
        models_state = {}
        for name, model in self.models.items():
            if hasattr(model, 'snapshot'):
                models_state[name] = model.snapshot()
            else:
                # 기본 상태 복사
                models_state[name] = {
                    'name': model.name,
                    'status': getattr(model, 'status', None),
                    'queue': copy.deepcopy(getattr(model, 'queue', [])),
                    'running': getattr(model, 'running', None),
                    'queued_jobs': copy.deepcopy(getattr(model, 'queued_jobs', [])),
                    'running_jobs': copy.deepcopy(getattr(model, 'running_jobs', [])),
                    'finished_jobs': copy.deepcopy(getattr(model, 'finished_jobs', [])),
                    'next_available_time': getattr(model, 'next_available_time', 0.0)
                }
        
        # 기계 상태 복사 (Job 객체 대신 Job 상태만 저장)
        machines_state = {}
        for machine in self.machines:
            # Job 객체들을 상태 정보로 변환
            queued_jobs_state = [job.save_state() for job in machine.queued_jobs]
            running_jobs_state = [job.save_state() for job in machine.running_jobs]
            finished_jobs_state = [job.save_state() for job in machine.finished_jobs]
            
            machines_state[machine.name] = {
                'status': machine.status,
                'queue': copy.deepcopy(machine.queue),
                'running': machine.running,
                'queued_jobs': queued_jobs_state,
                'running_jobs': running_jobs_state,
                'finished_jobs': finished_jobs_state,
                'next_available_time': machine.next_available_time,
                'transfer_counts': copy.deepcopy(getattr(machine, 'transfer_counts', {}))
            }
        
        # RNG 상태 저장
        rng_state = random.getstate()
        
        return SimulatorState(
            self.current_time,
            event_queue_copy,
            models_state,
            machines_state,
            rng_state
        )

    def restore(self, state):
        """스냅샷에서 상태를 복원합니다."""
        self.current_time = state.current_time
        
        # 이벤트 큐 복원
        self.event_queue = []
        for event in state.event_queue:
            self.push(event)
        
        # 모델 상태 복원
        for name, model_state in state.models_state.items():
            if name in self.models:
                model = self.models[name]
                if hasattr(model, 'restore'):
                    model.restore(model_state)
                else:
                    # 기본 상태 복원
                    if 'status' in model_state:
                        model.status = model_state['status']
                    if 'queue' in model_state:
                        model.queue = model_state['queue']
                    if 'running' in model_state:
                        model.running = model_state['running']
                    if 'queued_jobs' in model_state:
                        model.queued_jobs = model_state['queued_jobs']
                    if 'running_jobs' in model_state:
                        model.running_jobs = model_state['running_jobs']
                    if 'finished_jobs' in model_state:
                        model.finished_jobs = model_state['finished_jobs']
                    if 'next_available_time' in model_state:
                        model.next_available_time = model_state['next_available_time']
        
        # 기계 상태 복원
        for machine_name, machine_state in state.machines_state.items():
            for machine in self.machines:
                if machine.name == machine_name:
                    machine.status = machine_state['status']
                    machine.queue = machine_state['queue']
                    machine.running = machine_state['running']
                    machine.next_available_time = machine_state['next_available_time']
                    if 'transfer_counts' in machine_state:
                        machine.transfer_counts = machine_state['transfer_counts']
                    
                    # Job 상태 복원 (Job 객체들을 찾아서 상태만 복원)
                    # 모든 Job 객체들을 수집
                    all_jobs = []
                    for m in self.machines:
                        all_jobs.extend(m.queued_jobs)
                        all_jobs.extend(m.running_jobs)
                        all_jobs.extend(m.finished_jobs)
                    
                    # queued_jobs 복원
                    machine.queued_jobs = []
                    for job_state in machine_state['queued_jobs']:
                        # 해당 Job 객체 찾기
                        for job in all_jobs:
                            if job.id == job_state.get('job_id', job_state.get('id')):
                                job.restore_state(job_state)
                                machine.queued_jobs.append(job)
                                break
                    
                    # running_jobs 복원
                    machine.running_jobs = []
                    for job_state in machine_state['running_jobs']:
                        for job in all_jobs:
                            if job.id == job_state.get('job_id', job_state.get('id')):
                                job.restore_state(job_state)
                                machine.running_jobs.append(job)
                                break
                    
                    # finished_jobs 복원
                    machine.finished_jobs = []
                    for job_state in machine_state['finished_jobs']:
                        for job in all_jobs:
                            if job.id == job_state.get('job_id', job_state.get('id')):
                                job.restore_state(job_state)
                                machine.finished_jobs.append(job)
                                break
                    break
        
        # RNG 상태 복원
        random.setstate(state.rng_state)

    def legal_actions(self):
        """현재 결정 시점에서 가능한 모든 액션을 반환합니다."""
        actions = []
        action_set = set()  # 중복 제거를 위한 set
        
        # 기계가 idle한 시점에서 가능한 액션들
        for machine in self.machines:
            if machine.status == 'idle' and machine.queued_jobs:
                # 현재 기계의 큐에 있는 작업들에 대해 가능한 액션들
                for job in machine.queued_jobs:
                    current_op = job.current_op()
                    if current_op:
                        # 현재 기계에서 실행
                        action = Action(current_op.id, machine.name)
                        action_key = f"{current_op.id}->{machine.name}"
                        if action_key not in action_set:
                            actions.append(action)
                            action_set.add(action_key)
                        
                        # 다른 가능한 기계들로 전송
                        for candidate_machine in current_op.candidates:
                            if candidate_machine != machine.name:
                                action = Action(current_op.id, candidate_machine)
                                action_key = f"{current_op.id}->{candidate_machine}"
                                if action_key not in action_set:
                                    actions.append(action)
                                    action_set.add(action_key)
        
        return actions

    def apply(self, action):
        """액션을 적용하여 상태를 전이시킵니다."""
        # 액션 적용을 위한 변경사항 기록
        changes = []
        
        # 해당 operation을 찾아서 지정된 기계로 할당
        operation_id = action.operation_id
        target_machine = action.machine_id
        
        # operation을 포함하는 job 찾기
        target_job = None
        source_machine = None
        
        for machine in self.machines:
            for job in machine.queued_jobs:
                if job.current_op() and job.current_op().id == operation_id:
                    target_job = job
                    source_machine = machine
                    break
            if target_job:
                break
        
        if target_job and source_machine:
            # 기존 상태 저장
            changes.append({
                'type': 'job_transfer',
                'job': target_job,
                'from_machine': source_machine.name,
                'to_machine': target_machine,
                'original_queue': copy.deepcopy(source_machine.queued_jobs)
            })
            
            # job을 source machine에서 제거
            if target_job in source_machine.queued_jobs:
                source_machine.queued_jobs.remove(target_job)
            
            # job을 target machine에 추가
            target_machine_obj = None
            for machine in self.machines:
                if machine.name == target_machine:
                    target_machine_obj = machine
                    break
            
            if target_machine_obj:
                if action.insert_position is not None:
                    # 지정된 위치에 삽입
                    target_machine_obj.queued_jobs.insert(action.insert_position, target_job)
                else:
                    # 큐 끝에 추가
                    target_machine_obj.queued_jobs.append(target_job)
                
                # 디버깅 출력
                print(f"    액션 적용: {operation_id} -> {target_machine}")
                print(f"    {source_machine.name} 큐 길이: {len(source_machine.queued_jobs)}")
                print(f"    {target_machine} 큐 길이: {len(target_machine_obj.queued_jobs)}")
        
        return changes

    def undo(self, changes):
        """변경사항을 되돌립니다."""
        for change in reversed(changes):
            if change['type'] == 'job_transfer':
                job = change['job']
                from_machine_name = change['from_machine']
                to_machine_name = change['to_machine']
                original_queue = change['original_queue']
                
                # to_machine에서 job 제거
                for machine in self.machines:
                    if machine.name == to_machine_name and job in machine.queued_jobs:
                        machine.queued_jobs.remove(job)
                        break
                
                # from_machine에 job 복원
                for machine in self.machines:
                    if machine.name == from_machine_name:
                        machine.queued_jobs = original_queue
                        break

    def is_terminal(self):
        """모든 작업이 완료되었는지 확인합니다."""
        for machine in self.machines:
            if machine.queued_jobs or machine.running_jobs:
                return False
        return True

    def objective(self):
        """목적함수 (makespan)를 계산합니다."""
        # 모든 작업이 완료되었는지 확인
        all_jobs_completed = True
        for machine in self.machines:
            if machine.queued_jobs or machine.running_jobs:
                all_jobs_completed = False
                break
        
        if not all_jobs_completed:
            return float('inf')
        
        # 모든 job의 완료 시간 중 최대값
        max_completion_time = 0.0
        for machine in self.machines:
            for job in machine.finished_jobs:
                if hasattr(job, 'completion_time'):
                    max_completion_time = max(max_completion_time, job.completion_time)
        
        # 완료된 작업이 있으면 그 시간을 반환, 없으면 현재 시간을 반환
        if max_completion_time > 0:
            return max_completion_time
        else:
            return self.current_time

    def lower_bound(self):
        """현재 상태에서의 하한을 계산합니다."""
        # 남은 작업들의 최소 처리 시간 기반 하한
        remaining_work = 0.0
        
        for machine in self.machines:
            # 큐에 있는 작업들
            for job in machine.queued_jobs:
                current_op = job.current_op()
                if current_op:
                    # 최소 처리 시간 계산
                    min_duration = self._get_min_duration(current_op)
                    remaining_work += min_duration
            
            # 실행 중인 작업들
            for job in machine.running_jobs:
                current_op = job.current_op()
                if current_op:
                    # 남은 처리 시간 추정
                    remaining_work += self._estimate_remaining_time(job)
        
        return self.current_time + remaining_work

    def _get_min_duration(self, operation):
        """operation의 최소 처리 시간을 반환합니다."""
        # 간단한 추정: 평균 처리 시간의 80%
        if hasattr(operation, 'distribution'):
            dist = operation.distribution
            if dist['distribution'] == 'normal':
                return max(0, dist['mean'] - dist['std'])
            elif dist['distribution'] == 'uniform':
                return dist['low']
            elif dist['distribution'] == 'exponential':
                return 0.1  # 최소값
        return 1.0  # 기본값

    def _estimate_remaining_time(self, job):
        """job의 남은 처리 시간을 추정합니다."""
        # 간단한 추정: 평균 처리 시간의 50%
        current_op = job.current_op()
        if current_op:
            return self._get_min_duration(current_op) * 0.5
        return 0.0

    def rollout_value(self, policy="ECT"):
        """휴리스틱 롤아웃을 통해 상한을 계산합니다."""
        # 현재 상태를 스냅샷
        original_state = self.snapshot()
        
        # 간단한 휴리스틱으로 시뮬레이션 실행
        self._run_heuristic_simulation(policy)
        
        # 목적함수 계산
        upper_bound = self.objective()
        
        # 상태 복원
        self.restore(original_state)
        
        print(f"    롤아웃 완료: 정책={policy}, 상한={upper_bound}")
        return upper_bound

    def _run_heuristic_simulation(self, policy):
        """휴리스틱 정책으로 시뮬레이션을 실행합니다."""
        print(f"    휴리스틱 시뮬레이션 시작: 정책={policy}")
        
        # 시뮬레이터 기반 최적화 전용 간단한 휴리스틱
        max_iterations = 1000  # 무한 루프 방지
        iteration = 0
        
        while not self.is_terminal() and len(self.event_queue) > 0 and iteration < max_iterations:
            iteration += 1
            
            # 다음 이벤트 처리
            if self.event_queue:
                evt = heapq.heappop(self.event_queue)
                self.current_time = evt.time
                print(f"    이벤트 처리: {evt.event_type} at {evt.time}")
                
                # 시뮬레이터 기반 최적화에서는 간단한 이벤트 처리
                if evt.event_type == 'material_arrival':
                    # Job이 기계에 도착
                    job = evt.payload.get('job')
                    if job:
                        target_machine = None
                        for machine in self.machines:
                            if machine.name == evt.dest_model:
                                target_machine = machine
                                break
                        
                        if target_machine and job not in target_machine.queued_jobs:
                            target_machine.queued_jobs.append(job)
                            print(f"    Job {job.id}가 {target_machine.name}에 도착")
                
                elif evt.event_type == 'end_operation':
                    # 작업 완료
                    job = evt.payload.get('job')
                    if job:
                        # 작업을 완료된 기계에서 제거
                        for machine in self.machines:
                            if job in machine.running_jobs:
                                machine.running_jobs.remove(job)
                                machine.status = 'idle'
                                print(f"    Job {job.id}가 {machine.name}에서 완료")
                                
                                # 다음 작업으로 진행
                                job.advance()
                                if not job.done():
                                    next_op = job.current_op()
                                    if next_op:
                                        # 다음 작업을 적절한 기계로 전송
                                        for target_machine in self.machines:
                                            if target_machine.name in next_op.candidates:
                                                transfer_evt = Event('material_arrival', {'job': job}, dest_model=target_machine.name)
                                                self.push(transfer_evt)
                                                transfer_evt.set_time(self.current_time + 0.1)
                                                break
                                else:
                                    # 모든 작업이 완료된 경우 finished_jobs에 추가
                                    machine.finished_jobs.append(job)
                                    print(f"    Job {job.id}가 모든 작업 완료")
                                break
            
            # 결정 시점에서 휴리스틱 적용
            if policy == "ECT":
                self._apply_ect_policy()
            elif policy == "SPT":
                self._apply_spt_policy()
        
        print(f"    휴리스틱 시뮬레이션 완료: 현재시간={self.current_time}, 터미널={self.is_terminal()}, 반복횟수={iteration}")
        
        if self.is_terminal():
            return self.objective()
        else:
            # 터미널이 아닌 경우 현재 시간 + 예상 완료 시간을 반환
            estimated_completion = self.current_time
            for machine in self.machines:
                for job in machine.queued_jobs + machine.running_jobs:
                    remaining_ops = job.get_remaining_operations()
                    estimated_completion += remaining_ops * 5.0  # 평균 작업 시간 추정
            return estimated_completion

    def _apply_ect_policy(self):
        """ECT (Earliest Completion Time) 정책을 적용합니다."""
        for machine in self.machines:
            if machine.status == 'idle' and machine.queued_jobs:
                # 가장 빨리 완료될 수 있는 작업 선택
                best_job = None
                best_completion_time = float('inf')
                
                for job in machine.queued_jobs:
                    current_op = job.current_op()
                    if current_op:
                        # 예상 완료 시간 계산
                        estimated_duration = self._get_min_duration(current_op)
                        completion_time = self.current_time + estimated_duration
                        
                        if completion_time < best_completion_time:
                            best_completion_time = completion_time
                            best_job = job
                
                if best_job:
                    # 작업 시작
                    machine.running_jobs.append(best_job)
                    machine.queued_jobs.remove(best_job)
                    machine.status = 'busy'
                    print(f"    ECT 정책: {best_job.id}를 {machine.name}에서 시작")
                    
                    # 작업 완료 이벤트 스케줄링
                    current_op = best_job.current_op()
                    if current_op:
                        duration = self._get_min_duration(current_op)
                        completion_time = self.current_time + duration
                        
                        # 작업 완료 이벤트 생성
                        evt = Event('end_operation', {'job': best_job, 'operation': current_op.id}, dest_model=machine.name)
                        self.push(evt)
                        evt.set_time(completion_time)

    def _apply_spt_policy(self):
        """SPT (Shortest Processing Time) 정책을 적용합니다."""
        for machine in self.machines:
            if machine.status == 'idle' and machine.queued_jobs:
                # 가장 짧은 처리 시간을 가진 작업 선택
                best_job = None
                shortest_duration = float('inf')
                
                for job in machine.queued_jobs:
                    current_op = job.current_op()
                    if current_op:
                        duration = self._get_min_duration(current_op)
                        if duration < shortest_duration:
                            shortest_duration = duration
                            best_job = job
                
                if best_job:
                    # 작업 시작
                    machine.running_jobs.append(best_job)
                    machine.queued_jobs.remove(best_job)
                    machine.status = 'busy'

    def print_machine_queues(self):
        """모든 기계의 큐 상태를 출력"""
        if not self.machines:
            return
            
        print(f"\n=== 시뮬레이션 시간: {self.current_time:.2f} ===")
        for machine in self.machines:
            machine.get_queue_status()

    def get_all_job_status(self):
        """모든 기계에서 관리하는 Job들의 상태를 수집하여 반환합니다."""
        all_jobs = {
            'simulation_time': self.current_time,
            'machines': {}
        }
        
        for machine in self.machines:
            machine_summary = machine.get_job_status_summary()
            all_jobs['machines'][machine.name] = machine_summary
            
        return all_jobs
    
    def print_job_status_summary(self):
        """모든 Job의 상태 요약을 출력합니다."""
        all_jobs = self.get_all_job_status()
        
        print(f"\n=== 전체 Job 상태 요약 (시뮬레이션 시간: {self.current_time:.2f}) ===")
        
        total_queued = 0
        total_running = 0
        total_finished = 0
        
        for machine_name, machine_data in all_jobs['machines'].items():
            queued_count = len(machine_data['queued_jobs'])
            running_count = len(machine_data['running_jobs'])
            finished_count = len(machine_data['finished_jobs'])
            
            total_queued += queued_count
            total_running += running_count
            total_finished += finished_count
            
            print(f"\n{machine_name}:")
            print(f"  대기 중: {queued_count}, 실행 중: {running_count}, 완료: {finished_count}")
            
            if running_count > 0:
                print("  실행 중인 Job들:")
                for job in machine_data['running_jobs']:
                    print(f"    - Job {job['job_id']} (Part {job['part_id']}): {job['current_operation']} - 진행률 {job['progress']:.2f}")
        
        print(f"\n전체 요약:")
        print(f"  총 대기 중: {total_queued}, 총 실행 중: {total_running}, 총 완료: {total_finished}")
        print("=" * 50)

    def run(self, print_queues_interval=None, print_job_summary_interval=None):
        """
        시뮬레이션 실행
        :param print_queues_interval: 큐 상태를 출력할 시간 간격 (초)
        :param print_job_summary_interval: Job 상태 요약을 출력할 시간 간격 (초)
        """
        last_print_time = 0.0
        last_summary_time = 0.0
        
        while self.event_queue:
            evt = heapq.heappop(self.event_queue)
            self.current_time = evt.time
            
            # 주기적으로 큐 상태 출력
            if print_queues_interval and self.current_time - last_print_time >= print_queues_interval:
                self.print_machine_queues()
                last_print_time = self.current_time
            
            # 주기적으로 Job 상태 요약 출력
            if print_job_summary_interval and self.current_time - last_summary_time >= print_job_summary_interval:
                self.print_job_status_summary()
                last_summary_time = self.current_time
            
            m = self.models.get(evt.dest_model)
            if not m:
                raise KeyError(f"No model: {evt.dest_model}")
            m.handle_event(evt)