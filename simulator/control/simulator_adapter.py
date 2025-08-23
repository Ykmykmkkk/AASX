"""
기존 시뮬레이터와 Control Tower를 연결하는 어댑터
"""

import json
from typing import Dict, List, Optional
from .control_tower import ControlTower, SchedulingStrategy
from simulator.engine.simulator import EoModel, Event
from simulator.model.machine import Machine
from simulator.domain.domain import Job, JobStatus

class SimulatorAdapter:
    """기존 시뮬레이터와 Control Tower를 연결하는 어댑터 클래스"""
    
    def __init__(self, scenario_path: str, strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCING):
        self.control_tower = ControlTower(scenario_path, strategy)
        self.scenario_path = scenario_path
        self.machines: Dict[str, Machine] = {}
        self.jobs: Dict[str, Job] = {}
        
        # 동적 할당 결과를 저장할 딕셔너리
        self.dynamic_assignments: Dict[str, str] = {}  # operation_id -> machine_id
        
    def register_machines(self, machines: List[Machine]):
        """시뮬레이터의 머신들을 등록합니다."""
        for machine in machines:
            self.machines[machine.name] = machine
    
    def register_jobs(self, jobs: List[Job]):
        """시뮬레이터의 job들을 등록합니다."""
        for job in jobs:
            self.jobs[job.id] = job
    
    def setup_dynamic_routing(self):
        """동적 라우팅을 설정합니다."""
        print("=== 동적 라우팅 설정 ===")
        
        # 모든 job의 operations를 Control Tower에 추가
        for job in self.jobs.values():
            operations = [op.id for op in job.operations]
            self.control_tower.add_job_operations(job.id, operations)
            print(f"Job {job.id}: {len(operations)}개 operations 추가")
        
        # 동적 할당 실행
        assignments = self.control_tower.assign_operations()
        
        # 할당 결과를 딕셔너리로 저장
        for assignment in assignments:
            self.dynamic_assignments[assignment.operation_id] = assignment.assigned_machine
        
        print(f"총 {len(assignments)}개 operations 할당 완료")
        
        # 할당 결과 출력
        for operation_id, machine_id in self.dynamic_assignments.items():
            print(f"  {operation_id} -> {machine_id}")
    
    def get_dynamic_assignment(self, operation_id: str) -> Optional[str]:
        """동적 할당 결과를 반환합니다."""
        return self.dynamic_assignments.get(operation_id)
    
    def update_machine_status(self, current_time: float):
        """머신 상태를 Control Tower에 업데이트합니다."""
        self.control_tower.update_time(current_time)
        
        # 시뮬레이터의 머신 상태를 Control Tower에 반영
        for machine_id, machine in self.machines.items():
            if machine_id in self.control_tower.machines:
                control_machine = self.control_tower.machines[machine_id]
                
                # 상태 업데이트
                if machine.status == 'idle':
                    control_machine.status = self.control_tower.MachineStatus.IDLE
                elif machine.status == 'busy':
                    control_machine.status = self.control_tower.MachineStatus.BUSY
                
                # 큐 길이 업데이트
                control_machine.queue_length = len(machine.queue)
    
    def export_dynamic_routing(self, filename: str = None) -> str:
        """동적 라우팅 결과를 파일로 내보냅니다."""
        if filename is None:
            filename = f"{self.scenario_path}/dynamic_routing_result.json"
        
        routing_data = []
        for operation_id, machine_id in self.dynamic_assignments.items():
            routing_data.append({
                "operation_id": operation_id,
                "assigned_machine": machine_id
            })
        
        with open(filename, 'w') as f:
            json.dump(routing_data, f, indent=2)
        
        return filename

class DynamicMachine(Machine):
    """동적 할당을 지원하는 머신 클래스"""
    
    def __init__(self, name, transfer_map, initial, dispatch_rule='fifo', control_tower=None):
        super().__init__(name, transfer_map, initial, dispatch_rule)
        self.control_tower = control_tower
    
    def _start_if_possible(self):
        """동적 할당을 고려하여 작업을 시작합니다."""
        if self.status != 'idle' or not self.queue:
            return
        
        part = self.dispatch.select(self.queue)
        op = part.job.current_op()
        
        # 동적 할당 확인
        if self.control_tower:
            dynamic_assignment = self.control_tower.get_dynamic_assignment(op.id)
            if dynamic_assignment and dynamic_assignment != self.name:
                # 다른 머신에 할당되어야 하는 경우, 해당 머신으로 전송
                target_machine = dynamic_assignment
                if target_machine in self.transfer:
                    transfer_time = self.transfer[target_machine]
                    ev = Event('material_arrival', dest_model=target_machine, payload={'part': part})
                    self.schedule(ev, transfer_time)
                    
                    # 현재 큐에서 제거
                    self.queue.remove(part)
                    return
        
        # 기존 로직 실행
        super()._start_if_possible()

def create_dynamic_simulator(scenario_path: str, strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCING):
    """동적 할당을 지원하는 시뮬레이터를 생성합니다."""
    from simulator.builder import ModelBuilder
    
    # 어댑터 생성
    adapter = SimulatorAdapter(scenario_path, strategy)
    
    # 기존 빌더로 모델 생성
    builder = ModelBuilder(scenario_path)
    machines, gen, tx = builder.build()
    
    # 어댑터에 머신들 등록
    adapter.register_machines(machines)
    
    # 동적 라우팅 설정
    adapter.setup_dynamic_routing()
    
    # 머신들을 동적 머신으로 교체
    dynamic_machines = []
    for machine in machines:
        dynamic_machine = DynamicMachine(
            machine.name,
            machine.transfer,
            {'status': machine.status, 'next_available_time': 0.0},
            'fifo',
            adapter
        )
        dynamic_machines.append(dynamic_machine)
    
    return dynamic_machines, gen, tx, adapter

def run_dynamic_simulation(scenario_path: str, strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCING):
    """동적 할당을 사용하여 시뮬레이션을 실행합니다."""
    from simulator.engine.simulator import Simulator
    
    print("=== 동적 할당 시뮬레이션 시작 ===")
    print(f"스케줄링 전략: {strategy.value}")
    
    # 동적 시뮬레이터 생성
    machines, gen, tx, adapter = create_dynamic_simulator(scenario_path, strategy)
    
    # 시뮬레이터 생성 및 등록
    sim = Simulator()
    sim.register(gen)
    sim.register(tx)
    for machine in machines:
        sim.register(machine)
    
    # 초기화
    gen.initialize()
    
    # 시뮬레이션 실행
    sim.run(print_queues_interval=5.0, print_job_summary_interval=10.0)
    
    # 동적 라우팅 결과 내보내기
    result_file = adapter.export_dynamic_routing()
    print(f"\n동적 라우팅 결과가 {result_file}에 저장되었습니다.")
    
    return sim, adapter

if __name__ == "__main__":
    # 테스트 실행
    scenario_path = "scenarios/my_case"
    
    # 동적 시뮬레이션 실행
    sim, adapter = run_dynamic_simulation(scenario_path, SchedulingStrategy.LOAD_BALANCING)
