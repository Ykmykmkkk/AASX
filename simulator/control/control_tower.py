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
    
    def __init__(self, scheduling_strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCING):
        self.scheduling_strategy = scheduling_strategy
        self.current_time = 0.0
        
        # 실시간 머신 상태 관리 (시뮬레이션 기반)
        self.machine_statuses: Dict[str, Dict] = {}
        
        # Operation 정보
        self.operations: Dict[str, Dict] = {}
        
        # Operation 지속시간 정보
        self.operation_durations: Dict[str, Dict] = {}
        
        # 대기 중인 operation 요청들
        self.pending_operations: List[OperationRequest] = []
        
        # 할당 히스토리
        self.assignment_history: List[AssignmentResult] = []
        
        # Job별 상태 추적
        self.job_status: Dict[str, Dict] = {}
        
        # 머신별 작업 스케줄
        self.machine_schedules: Dict[str, List] = {}
        
        # 통계 정보
        self.stats = {
            'total_assignments': 0,
            'total_processing_time': 0.0,
            'average_wait_time': 0.0,
            'machine_utilizations': {},
            'job_completion_times': {},
            'transfer_count': 0,
            'conflict_resolutions': 0
        }
    
    def _load_scenario_data(self, scenario_path: str):
        """시나리오 데이터를 로드합니다."""
        try:
            # 머신 정보 로드
            with open(f"{scenario_path}/machines.json", 'r') as f:
                machines_data = json.load(f)
                for machine_id, machine_info in machines_ㄱdata.items():
                    self.machine_statuses[machine_id] = {
                        'name': machine_id,
                        'status': machine_info['status'],
                        'next_available_time': machine_info['next_available_time'],
                        'queue_length': 0,
                        'current_time': 0.0
                    }
            
            # Operation 정보 로드 (배열을 딕셔너리로 변환)
            with open(f"{scenario_path}/operations.json", 'r') as f:
                operations_list = json.load(f)
                self.operations = {}
                for op in operations_list:
                    self.operations[op['operation_id']] = op
            
            # Operation 지속시간 정보 로드
            with open(f"{scenario_path}/operation_durations.json", 'r') as f:
                self.operation_durations = json.load(f)
                
            # Job 출시 시간 정보 로드 (추가)
            with open(f"{scenario_path}/job_release.json", 'r') as f:
                self.job_releases = json.load(f)
                
            print(f"[Control Tower] 로드된 Operation 수: {len(self.operations)}")
            print(f"[Control Tower] 로드된 Machine 수: {len(self.machine_statuses)}")
                
        except FileNotFoundError as e:
            print(f"시나리오 파일을 찾을 수 없습니다: {e}")
            raise
    
    def update_machine_status(self, machine_id: str, status: Dict):
        """실시간 머신 상태 업데이트"""
        self.machine_statuses[machine_id] = status
        self.current_time = status.get('current_time', self.current_time)
    
    def update_job_status(self, job_id: str, status: Dict):
        """Job 상태 업데이트"""
        self.job_status[job_id] = status
        print(f"[Control Tower] Job {job_id} 상태 업데이트: {status}")
    
    def get_job_status(self, job_id: str) -> Dict:
        """Job 상태 조회"""
        return self.job_status.get(job_id, {})
    
    def update_machine_schedule(self, machine_id: str, operation_id: str, start_time: float, end_time: float):
        """머신 스케줄 업데이트"""
        if machine_id not in self.machine_schedules:
            self.machine_schedules[machine_id] = []
        
        schedule_entry = {
            'operation_id': operation_id,
            'start_time': start_time,
            'end_time': end_time,
            'machine_id': machine_id
        }
        
        self.machine_schedules[machine_id].append(schedule_entry)
        print(f"[Control Tower] 머신 {machine_id} 스케줄 업데이트: {operation_id} ({start_time:.2f} ~ {end_time:.2f})")
    
    def check_machine_availability(self, machine_id: str, start_time: float, duration: float) -> bool:
        """머신의 특정 시간대 가용성 확인"""
        if machine_id not in self.machine_schedules:
            return True
        
        end_time = start_time + duration
        
        for schedule in self.machine_schedules[machine_id]:
            # 시간 겹침 확인
            if (start_time < schedule['end_time'] and end_time > schedule['start_time']):
                print(f"[Control Tower] 머신 {machine_id} 시간 충돌: {schedule['operation_id']} ({schedule['start_time']:.2f} ~ {schedule['end_time']:.2f})")
                return False
        
        return True
    
    def resolve_scheduling_conflicts(self, operation_id: str, available_machines: List[str], 
                                   current_time: float, estimated_duration: float) -> Optional[str]:
        """스케줄링 충돌 해결"""
        print(f"[Control Tower] 스케줄링 충돌 해결 시도: {operation_id}")
        
        # 1. 즉시 실행 가능한 머신 찾기
        immediate_available = []
        for machine_id in available_machines:
            if self.check_machine_availability(machine_id, current_time, estimated_duration):
                immediate_available.append(machine_id)
        
        if immediate_available:
            print(f"[Control Tower] 즉시 실행 가능한 머신: {immediate_available}")
            return immediate_available[0]
        
        # 2. 가장 빨리 사용 가능한 머신 찾기
        earliest_available = None
        earliest_time = float('inf')
        
        for machine_id in available_machines:
            if machine_id in self.machine_schedules:
                # 가장 늦게 끝나는 작업의 종료 시간 찾기
                latest_end = max(schedule['end_time'] for schedule in self.machine_schedules[machine_id])
                if latest_end < earliest_time:
                    earliest_time = latest_end
                    earliest_available = machine_id
            else:
                # 스케줄이 없는 머신은 즉시 사용 가능
                earliest_available = machine_id
                earliest_time = current_time
                break
        
        if earliest_available:
            print(f"[Control Tower] 가장 빨리 사용 가능한 머신: {earliest_available} (시간: {earliest_time:.2f})")
            self.stats['conflict_resolutions'] += 1
            return earliest_available
        
        return None
    
    def validate_operation_assignment(self, operation_id: str, machine_id: str, 
                                    job_id: str, current_time: float) -> bool:
        """Operation 할당 유효성 검증"""
        # 1. 머신이 존재하는지 확인
        if machine_id not in self.machine_statuses:
            print(f"[Control Tower] 유효성 검증 실패: 머신 {machine_id}가 존재하지 않음")
            return False
        
        # 2. Operation이 해당 머신에서 실행 가능한지 확인
        if operation_id in self.operations:
            operation = self.operations[operation_id]
            if machine_id not in operation.get('machines', []):
                print(f"[Control Tower] 유효성 검증 실패: Operation {operation_id}이 머신 {machine_id}에서 실행 불가")
                return False
        
        # 3. 머신이 현재 작업 중인지 확인
        machine_status = self.machine_statuses[machine_id]
        if machine_status.get('status') == 'busy':
            print(f"[Control Tower] 유효성 검증 실패: 머신 {machine_id}가 현재 작업 중")
            return False
        
        # 4. Job이 이미 다른 머신에서 실행 중인지 확인
        job_status = self.get_job_status(job_id)
        if job_status.get('status') == 'running':
            print(f"[Control Tower] 유효성 검증 실패: Job {job_id}가 이미 실행 중")
            return False
        
        print(f"[Control Tower] 유효성 검증 통과: {operation_id} -> {machine_id}")
        return True
    
    def select_next_job_for_machine(self, machine_id: str, queue) -> Optional[object]:
        """특정 머신의 다음 작업 선택"""
        if not queue:
            return None
            
        # 현재 전략에 따른 작업 선택
        if self.scheduling_strategy == SchedulingStrategy.LOAD_BALANCING:
            # 큐 길이와 대기 시간을 고려한 선택
            return queue[0]  # 기본 FIFO
        elif self.scheduling_strategy == SchedulingStrategy.EARLIEST_AVAILABLE:
            # 가장 빨리 도착한 작업
            return queue[0]
        elif self.scheduling_strategy == SchedulingStrategy.LEAST_LOADED:
            # 가장 적은 작업량을 가진 작업
            return queue[0]
        else:
            # 기본 FIFO
            return queue[0]
    
    def select_optimal_machine_for_operation(self, operation_id: str, job_id: str, 
                                           available_machines: List[str], current_time: float) -> Optional[str]:
        """Operation에 대한 최적 머신 선택"""
        if len(available_machines) == 1:
            # 단일 후보 기계인 경우, 해당 기계가 작업 중인지 확인
            machine_id = available_machines[0]
            machine_status = self.machine_statuses.get(machine_id, {})
            if machine_status.get('status') == 'busy' and machine_status.get('current_job'):
                print(f"[Control Tower] Operation {operation_id} - 단일 후보 기계 {machine_id}가 작업 중: {machine_status.get('current_job')}")
                return None
            print(f"[Control Tower] Operation {operation_id} - 단일 후보 기계: {machine_id}")
            return machine_id
        
        # 작업 중이지 않은 머신들만 필터링
        idle_machines = []
        busy_machines = []
        
        for machine_id in available_machines:
            if machine_id not in self.machine_statuses:
                continue
                
            machine_status = self.machine_statuses[machine_id]
            if machine_status.get('status') == 'busy' and machine_status.get('current_job'):
                busy_machines.append(machine_id)
                print(f"[Control Tower] 기계 {machine_id} 작업 중: {machine_status.get('current_job')}")
            else:
                idle_machines.append(machine_id)
        
        # 우선적으로 idle한 머신들 중에서 선택
        candidate_machines = idle_machines if idle_machines else busy_machines
        
        if not candidate_machines:
            print(f"[Control Tower] Operation {operation_id} - 사용 가능한 기계 없음")
            return None
        
        # 예상 지속시간 계산
        estimated_duration = self._estimate_operation_duration(operation_id, candidate_machines[0])
        
        # 유효성 검증 및 충돌 해결
        valid_machines = []
        for machine_id in candidate_machines:
            if self.validate_operation_assignment(operation_id, machine_id, job_id, current_time):
                valid_machines.append(machine_id)
        
        if not valid_machines:
            print(f"[Control Tower] Operation {operation_id} - 유효한 기계 없음, 충돌 해결 시도")
            resolved_machine = self.resolve_scheduling_conflicts(operation_id, available_machines, current_time, estimated_duration)
            if resolved_machine:
                return resolved_machine
            return None
        
        machine_scores = []
        for machine_id in valid_machines:
            machine_status = self.machine_statuses[machine_id]
            
            if self.scheduling_strategy == SchedulingStrategy.LOAD_BALANCING:
                score = self._calculate_load_balancing_score(machine_id, machine_status, operation_id)
            elif self.scheduling_strategy == SchedulingStrategy.EARLIEST_AVAILABLE:
                score = self._calculate_earliest_available_score(machine_id, machine_status)
            elif self.scheduling_strategy == SchedulingStrategy.LEAST_LOADED:
                score = self._calculate_least_loaded_score(machine_id, machine_status)
            else:
                score = 0
            
            machine_scores.append((machine_id, score))
            print(f"[Control Tower] 기계 {machine_id} 점수: {score:.2f} (전략: {self.scheduling_strategy.value})")
        
        if machine_scores:
            optimal_machine = min(machine_scores, key=lambda x: x[1])[0]
            print(f"[Control Tower] Operation {operation_id} 최적 기계 선택: {optimal_machine}")
            
            # 스케줄 업데이트
            end_time = current_time + estimated_duration
            self.update_machine_schedule(optimal_machine, operation_id, current_time, end_time)
            
            return optimal_machine
        else:
            fallback_machine = valid_machines[0] if valid_machines else None
            print(f"[Control Tower] Operation {operation_id} 폴백 기계: {fallback_machine}")
            return fallback_machine
    
    def _calculate_load_balancing_score(self, machine_id: str, machine_status: Dict, operation_id: str = None) -> float:
        """로드 밸런싱 점수 계산"""
        queue_length = machine_status.get('queue_length', 0)
        next_available_time = machine_status.get('next_available_time', 0.0)
        current_time = machine_status.get('current_time', 0.0)
        
        # 큐 길이 (40%) + 대기 시간 (30%) + 처리 시간 효율성 (30%)
        queue_score = queue_length * 0.4
        wait_score = max(0, next_available_time - current_time) * 0.3
        
        # 처리 시간 효율성 점수 (해당 기계에서의 예상 처리 시간)
        processing_score = 0.0
        if operation_id and operation_id in self.operations:
            op_type = self.operations[operation_id]['type']
            if op_type in self.operation_durations and machine_id in self.operation_durations[op_type]:
                # 처리 시간이 짧을수록 좋은 점수
                duration_info = self.operation_durations[op_type][machine_id]
                if duration_info.get('distribution') == 'normal':
                    expected_duration = duration_info.get('mean', 5.0)
                elif duration_info.get('distribution') == 'uniform':
                    expected_duration = (duration_info.get('low', 3.0) + duration_info.get('high', 7.0)) / 2
                elif duration_info.get('distribution') == 'exponential':
                    expected_duration = 1.0 / duration_info.get('rate', 0.2)
                else:
                    expected_duration = 5.0
                
                # 처리 시간이 짧을수록 낮은 점수 (더 좋음)
                processing_score = expected_duration * 0.3
        
        return queue_score + wait_score + processing_score
    
    def _calculate_earliest_available_score(self, machine_id: str, machine_status: Dict) -> float:
        """가장 빨리 사용 가능한 점수 계산"""
        next_available_time = machine_status.get('next_available_time', 0.0)
        return next_available_time
    
    def _calculate_least_loaded_score(self, machine_id: str, machine_status: Dict) -> float:
        """가장 적은 부하 점수 계산"""
        queue_length = machine_status.get('queue_length', 0)
        return queue_length
    
    def get_available_machines(self, operation_id: str) -> List[str]:
        """Operation에 사용 가능한 머신 목록 반환"""
        if operation_id not in self.operations:
            return []
        
        operation = self.operations[operation_id]
        candidate_machines = operation.get('machines', [])
        
        # 모든 후보 기계를 반환 (idle/busy 모두 고려)
        available_machines = []
        for machine_id in candidate_machines:
            if machine_id in self.machine_statuses:
                available_machines.append(machine_id)
        
        print(f"[Control Tower] Operation {operation_id}의 후보 기계: {available_machines}")
        return available_machines
    
    def update_time(self, current_time: float):
        """시뮬레이션 시간 업데이트"""
        self.current_time = current_time
        
        # 통계 업데이트
        for machine_id in self.machine_statuses:
            if machine_id not in self.stats['machine_utilizations']:
                self.stats['machine_utilizations'][machine_id] = {
                    'total_time': 0.0,
                    'busy_time': 0.0,
                    'utilization': 0.0
                }
            
            # 총 시간 업데이트
            self.stats['machine_utilizations'][machine_id]['total_time'] = current_time
    
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
    
    def assign_operations(self) -> List[AssignmentResult]:
        """대기 중인 operations를 할당합니다."""
        assignments = []
        unassigned_operations = []
        
        for operation_request in self.pending_operations:
            available_machines = self.get_available_machines(operation_request.operation_id)
            
            if available_machines:
                optimal_machine = self.select_optimal_machine_for_operation(
                    operation_request.operation_id,
                    operation_request.job_id,
                    available_machines,
                    self.current_time
                )
                
                if optimal_machine:
                    machine_status = self.machine_statuses[optimal_machine]
                    
                    # 할당 실행
                    estimated_duration = operation_request.estimated_duration
                    end_time = self.current_time + estimated_duration
                    
                    # 머신 상태 업데이트
                    machine_status['status'] = MachineStatus.BUSY.value
                    machine_status['next_available_time'] = end_time
                    machine_status['current_job'] = operation_request.job_id
                    machine_status['current_operation'] = operation_request.operation_id
                    machine_status['queue_length'] += 1
                    
                    # 할당 결과 생성
                    assignment = AssignmentResult(
                        operation_id=operation_request.operation_id,
                        job_id=operation_request.job_id,
                        assigned_machine=optimal_machine,
                        start_time=self.current_time,
                        estimated_end_time=end_time,
                        priority_score=operation_request.priority
                    )
                    
                    assignments.append(assignment)
                    self.assignment_history.append(assignment)
                    
                    # 통계 업데이트
                    self.stats['total_assignments'] += 1
                    self.stats['total_processing_time'] += estimated_duration
                    
                    # 머신 활용도 업데이트
                    self.stats['machine_utilizations'][optimal_machine]['busy_time'] += estimated_duration
                    
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
        for machine_id, machine_status in self.machine_statuses.items():
            utilization = self.stats['machine_utilizations'][machine_id]
            if utilization['total_time'] > 0:
                utilization_rate = utilization['busy_time'] / utilization['total_time']
            else:
                utilization_rate = 0.0
            
            status[machine_id] = {
                'status': machine_status['status'],
                'next_available_time': machine_status['next_available_time'],
                'current_job': machine_status['current_job'],
                'current_operation': machine_status['current_operation'],
                'queue_length': machine_status['queue_length'],
                'utilization_rate': utilization_rate
            }
        
        return status
    
    def get_scheduling_statistics(self) -> Dict:
        """스케줄링 통계를 반환합니다."""
        total_machines = len(self.machine_statuses)
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
            filename = f"dynamic_routing_result.json"
        
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
            'machine_utilizations': {},
            'job_completion_times': {},
            'transfer_count': 0,
            'conflict_resolutions': 0
        }
        self.machine_statuses.clear()

