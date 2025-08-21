# --- simulator/engine/simulator.py ---
import heapq

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
    def __init__(self):
        self.current_time = 0.0
        self.event_queue = []
        self.models = {}
        self.machines = []  # 기계 목록 저장
        EoModel.bind(self.push, self.now)

    def push(self, event):
        heapq.heappush(self.event_queue, event)

    def now(self):
        return self.current_time

    def register(self, model):
        self.models[model.name] = model
        # 기계 모델인 경우 별도로 저장 (새로운 Job 상태 관리 구조에 맞게 수정)
        if hasattr(model, 'queued_jobs'):
            self.machines.append(model)

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