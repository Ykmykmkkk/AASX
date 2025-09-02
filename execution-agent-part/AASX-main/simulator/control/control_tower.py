import json
import heapq
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math

class MachineStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    BREAKDOWN = "breakdown"

@dataclass
class MachineState:
    """머신의 현재 상태를 관리하는 클래스"""
    machine_id: str
    status: MachineStatus
    next_available_time: float
    current_job: Optional[str] = None
    current_operation: Optional[str] = None
    queue_length: int = 0
    total_processing_time: float = 0.0
    utilization_rate: float = 0.0

@dataclass
class OperationRequest:
    """Operation 할당 요청을 나타내는 클래스"""
    operation_id: str
    job_id: str
    operation_type: str
    available_machines: List[str]
    priority: int = 0
    estimated_duration: float = 0.0
    deadline: Optional[float] = None

@dataclass
class AssignmentResult:
    """할당 결과를 나타내는 클래스"""
    operation_id: str
    job_id: str
    assigned_machine: str
    start_time: float
    estimated_end_time: float
    priority_score: float

class SchedulingStrategy(Enum):
    EARLIEST_AVAILABLE = "earliest_available"
    LEAST_LOADED = "least_loaded"
    SHORTEST_PROCESSING_TIME = "shortest_processing_time"
    PRIORITY_BASED = "priority_based"
    LOAD_BALANCING = "load_balancing"

class ControlTower:
    """머신 상태를 관리하고 동적으로 operation을 할당하는 Control Tower 클래스"""
    
    def __init__(self, scenario_path: str, scheduling_strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCING):
        self.scenario_path = scenario_path
        self.scheduling_strategy = scheduling_strategy
        self.current_time = 0.0
        
        # 머신 상태 관리
        self.machines: Dict[str, MachineState] = {}
        
        # Operation 정보
        self.operations: Dict[str, Dict] = {}
        
        # Operation 지속시간 정보
        self.operation_durations: Dict[str, Dict] = {}
        
        # 대기 중인 operation 요청들
        self.pending_operations: List[OperationRequest] = []
        
        # 할당 히스토리
        self.assignment_history: List[AssignmentResult] = []
        
        # 통계 정보
        self.stats = {
            'total_assignments': 0,
            'total_processing_time': 0.0,
            'average_wait_time': 0.0,
            'machine_utilizations': {}
        }
        
        self._load_scenario_data()
        self._initialize_machines()
    
    def _load_scenario_data(self):
        """시나리오 데이터를 로드합니다."""
        try:
            # 머신 정보 로드
            with open(f"{self.scenario_path}/machines.json", 'r') as f:
                machines_data = json.load(f)
                for machine_id, machine_info in machines_data.items():
                    self.machines[machine_id] = MachineState(
                        machine_id=machine_id,
                        status=MachineStatus(machine_info['status']),
                        next_available_time=machine_info['next_available_time']
                    )
            
            # Operation 정보 로드
            with open(f"{self.scenario_path}/operations.json", 'r') as f:
                operations_data = json.load(f)
                for op in operations_data:
                    self.operations[op['operation_id']] = op
            
            # Operation 지속시간 정보 로드
            with open(f"{self.scenario_path}/operation_durations.json", 'r') as f:
                self.operation_durations = json.load(f)
                
        except FileNotFoundError as e:
            raise FileNotFoundError(f"시나리오 파일을 찾을 수 없습니다: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파일 형식이 잘못되었습니다: {e}")
    
    def _initialize_machines(self):
        """머신들을 초기화합니다."""
        for machine_id in self.machines:
            self.stats['machine_utilizations'][machine_id] = {
                'total_time': 0.0,
                'busy_time': 0.0,
                'utilization': 0.0
            }
    
    def update_time(self, current_time: float):
        """현재 시간을 업데이트하고 머신 상태를 갱신합니다."""
        self.current_time = current_time
        
        # 머신 상태 업데이트
        for machine in self.machines.values():
            if machine.status == MachineStatus.BUSY and machine.next_available_time <= current_time:
                machine.status = MachineStatus.IDLE
                machine.current_job = None
                machine.current_operation = None
    
    def add_job_operations(self, job_id: str, operations: List[str], priority: int = 0):
        """새로운 job의 operations를 추가합니다."""
        for operation_id in operations:
            if operation_id in self.operations:
                op_info = self.operations[operation_id]
                
                # 예상 지속시간 계산
                estimated_duration = self._estimate_operation_duration(
                    op_info['type'], 
                    op_info['machines'][0] if op_info['machines'] else None
                )
                
                operation_request = OperationRequest(
                    operation_id=operation_id,
                    job_id=job_id,
                    operation_type=op_info['type'],
                    available_machines=op_info['machines'].copy(),
                    priority=priority,
                    estimated_duration=estimated_duration
                )
                
                self.pending_operations.append(operation_request)
        
        # 우선순위에 따라 정렬
        self.pending_operations.sort(key=lambda x: x.priority, reverse=True)
    
    def _estimate_operation_duration(self, operation_type: str, machine_id: str) -> float:
        """Operation의 예상 지속시간을 계산합니다."""
        if operation_type not in self.operation_durations:
            return 5.0  # 기본값
        
        if machine_id not in self.operation_durations[operation_type]:
            return 5.0  # 기본값
        
        duration_info = self.operation_durations[operation_type][machine_id]
        distribution = duration_info.get('distribution', 'normal')
        
        if distribution == 'normal':
            mean = duration_info.get('mean', 5.0)
            std = duration_info.get('std', 1.0)
            return random.normalvariate(mean, std)
        elif distribution == 'uniform':
            low = duration_info.get('low', 3.0)
            high = duration_info.get('high', 7.0)
            return random.uniform(low, high)
        elif distribution == 'exponential':
            rate = duration_info.get('rate', 0.2)
            return random.expovariate(rate)
        else:
            return duration_info.get('mean', 5.0)
    
    def get_available_machines(self, operation_request: OperationRequest) -> List[Tuple[str, float]]:
        """주어진 operation에 대해 사용 가능한 머신들과 예상 시작 시간을 반환합니다."""
        available_machines = []
        
        for machine_id in operation_request.available_machines:
            if machine_id not in self.machines:
                continue
                
            machine = self.machines[machine_id]
            
            # 머신이 사용 가능한지 확인
            if machine.status == MachineStatus.IDLE:
                start_time = max(self.current_time, machine.next_available_time)
                available_machines.append((machine_id, start_time))
            elif machine.status == MachineStatus.BUSY:
                start_time = max(self.current_time, machine.next_available_time)
                available_machines.append((machine_id, start_time))
        
        return available_machines
    
    def select_optimal_machine(self, operation_request: OperationRequest, available_machines: List[Tuple[str, float]]) -> Optional[Tuple[str, float]]:
        """스케줄링 전략에 따라 최적의 머신을 선택합니다."""
        if not available_machines:
            return None
        
        if self.scheduling_strategy == SchedulingStrategy.EARLIEST_AVAILABLE:
            return min(available_machines, key=lambda x: x[1])
        
        elif self.scheduling_strategy == SchedulingStrategy.LEAST_LOADED:
            # 가장 적은 작업량을 가진 머신 선택
            machine_loads = []
            for machine_id, start_time in available_machines:
                machine = self.machines[machine_id]
                load_score = machine.queue_length + (1 if machine.status == MachineStatus.BUSY else 0)
                machine_loads.append((machine_id, start_time, load_score))
            
            return min(machine_loads, key=lambda x: x[2])[:2]
        
        elif self.scheduling_strategy == SchedulingStrategy.SHORTEST_PROCESSING_TIME:
            # 가장 짧은 처리 시간을 가진 머신 선택
            machine_durations = []
            for machine_id, start_time in available_machines:
                duration = self._estimate_operation_duration(operation_request.operation_type, machine_id)
                machine_durations.append((machine_id, start_time, duration))
            
            return min(machine_durations, key=lambda x: x[2])[:2]
        
        elif self.scheduling_strategy == SchedulingStrategy.PRIORITY_BASED:
            # 우선순위 기반 선택 (현재는 earliest available과 동일)
            return min(available_machines, key=lambda x: x[1])
        
        elif self.scheduling_strategy == SchedulingStrategy.LOAD_BALANCING:
            # 부하 분산을 위한 복합 점수 계산
            machine_scores = []
            for machine_id, start_time in available_machines:
                machine = self.machines[machine_id]
                
                # 부하 점수 (큐 길이 + 현재 작업 여부)
                load_score = machine.queue_length + (1 if machine.status == MachineStatus.BUSY else 0)
                
                # 대기 시간 점수
                wait_time = start_time - self.current_time
                
                # 복합 점수 (낮을수록 좋음)
                composite_score = load_score * 0.6 + wait_time * 0.4
                
                machine_scores.append((machine_id, start_time, composite_score))
            
            return min(machine_scores, key=lambda x: x[2])[:2]
        
        else:
            return min(available_machines, key=lambda x: x[1])
    
    def assign_operations(self) -> List[AssignmentResult]:
        """대기 중인 operations를 할당합니다."""
        assignments = []
        unassigned_operations = []
        
        for operation_request in self.pending_operations:
            available_machines = self.get_available_machines(operation_request)
            
            if available_machines:
                optimal_machine = self.select_optimal_machine(operation_request, available_machines)
                
                if optimal_machine:
                    machine_id, start_time = optimal_machine
                    machine = self.machines[machine_id]
                    
                    # 할당 실행
                    estimated_duration = operation_request.estimated_duration
                    end_time = start_time + estimated_duration
                    
                    # 머신 상태 업데이트
                    machine.status = MachineStatus.BUSY
                    machine.next_available_time = end_time
                    machine.current_job = operation_request.job_id
                    machine.current_operation = operation_request.operation_id
                    machine.queue_length += 1
                    
                    # 할당 결과 생성
                    assignment = AssignmentResult(
                        operation_id=operation_request.operation_id,
                        job_id=operation_request.job_id,
                        assigned_machine=machine_id,
                        start_time=start_time,
                        estimated_end_time=end_time,
                        priority_score=operation_request.priority
                    )
                    
                    assignments.append(assignment)
                    self.assignment_history.append(assignment)
                    
                    # 통계 업데이트
                    self.stats['total_assignments'] += 1
                    self.stats['total_processing_time'] += estimated_duration
                    
                    # 머신 활용도 업데이트
                    self.stats['machine_utilizations'][machine_id]['busy_time'] += estimated_duration
                    
                else:
                    unassigned_operations.append(operation_request)
            else:
                unassigned_operations.append(operation_request)
        
        # 할당되지 않은 operations를 다시 pending_operations에 저장
        self.pending_operations = unassigned_operations
        
        return assignments
    
    def get_machine_status(self) -> Dict[str, Dict]:
        """모든 머신의 현재 상태를 반환합니다."""
        status = {}
        for machine_id, machine in self.machines.items():
            utilization = self.stats['machine_utilizations'][machine_id]
            if utilization['total_time'] > 0:
                utilization_rate = utilization['busy_time'] / utilization['total_time']
            else:
                utilization_rate = 0.0
            
            status[machine_id] = {
                'status': machine.status.value,
                'next_available_time': machine.next_available_time,
                'current_job': machine.current_job,
                'current_operation': machine.current_operation,
                'queue_length': machine.queue_length,
                'utilization_rate': utilization_rate
            }
        
        return status
    
    def get_scheduling_statistics(self) -> Dict:
        """스케줄링 통계를 반환합니다."""
        total_machines = len(self.machines)
        total_utilization = sum(
            util['utilization'] for util in self.stats['machine_utilizations'].values()
        )
        avg_utilization = total_utilization / total_machines if total_machines > 0 else 0.0
        
        return {
            'current_time': self.current_time,
            'total_assignments': self.stats['total_assignments'],
            'total_processing_time': self.stats['total_processing_time'],
            'pending_operations': len(self.pending_operations),
            'average_machine_utilization': avg_utilization,
            'machine_utilizations': self.stats['machine_utilizations']
        }
    
    def export_routing_result(self, filename: str = None) -> str:
        """할당 결과를 routing_result.json 형식으로 내보냅니다."""
        if filename is None:
            filename = f"{self.scenario_path}/dynamic_routing_result.json"
        
        routing_data = []
        for assignment in self.assignment_history:
            routing_data.append({
                "operation_id": assignment.operation_id,
                "job_id": assignment.job_id,
                "assigned_machine": assignment.assigned_machine,
                "start_time": assignment.start_time,
                "estimated_end_time": assignment.estimated_end_time,
                "priority_score": assignment.priority_score
            })
        
        with open(filename, 'w') as f:
            json.dump(routing_data, f, indent=2)
        
        return filename
    
    def reset(self):
        """Control Tower를 초기 상태로 리셋합니다."""
        self.current_time = 0.0
        self.pending_operations.clear()
        self.assignment_history.clear()
        self.stats = {
            'total_assignments': 0,
            'total_processing_time': 0.0,
            'average_wait_time': 0.0,
            'machine_utilizations': {}
        }
        self._initialize_machines()

