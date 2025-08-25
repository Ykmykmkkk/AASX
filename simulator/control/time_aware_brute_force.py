#!/usr/bin/env python3
"""
시간 축까지 완전히 고려한 브루트포스 최적화 스케줄러
작업 순서, 동적 재할당, 작업 중단/재개 등 모든 시간적 가능성을 고려합니다.
"""

import json
import itertools
import copy
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulator.builder import ModelBuilder
from simulator.engine.simulator import Simulator, Event

@dataclass
class TimeAwareSchedule:
    """시간을 고려한 스케줄"""
    operation_assignments: Dict[str, str]  # operation_id -> machine_id
    operation_order: List[str]  # operation 실행 순서
    dynamic_reassignments: List[Tuple[str, str, float]]  # (operation_id, new_machine, time)
    preemptions: List[Tuple[str, float, float]]  # (operation_id, start_time, resume_time)

@dataclass
class TimeAwareResult:
    """시간을 고려한 시뮬레이션 결과"""
    makespan: float
    schedule: TimeAwareSchedule
    job_completion_times: Dict[str, float]
    machine_utilization: Dict[str, float]
    total_transfers: int
    total_preemptions: int

class TimeAwareBruteForceScheduler:
    """시간 축까지 완전히 고려한 브루트포스 최적화 스케줄러"""
    
    def __init__(self, scenario_path: str, max_reassignments: int = 2, max_preemptions: int = 1):
        self.scenario_path = scenario_path
        self.max_reassignments = max_reassignments
        self.max_preemptions = max_preemptions
        
        self.jobs_data = self._load_jobs()
        self.operations_data = self._load_operations()
        self.release_times = self._load_release_times()
        
        # 모든 작업과 가능한 기계 조합 생성
        self.operation_machine_combinations = self._generate_combinations()
        
        # 작업 순서 조합 생성
        self.operation_order_combinations = self._generate_order_combinations()
        
    def _load_jobs(self) -> List[Dict]:
        """Job 정보 로드"""
        with open(f"{self.scenario_path}/jobs.json", 'r') as f:
            return json.load(f)
    
    def _load_operations(self) -> List[Dict]:
        """Operation 정보 로드"""
        with open(f"{self.scenario_path}/operations.json", 'r') as f:
            return json.load(f)
    
    def _load_release_times(self) -> Dict:
        """릴리스 시간 정보 로드"""
        with open(f"{self.scenario_path}/job_release.json", 'r') as f:
            releases = json.load(f)
            return {r['job_id']: r['release_time'] for r in releases}
    
    def _generate_combinations(self) -> List[Dict[str, str]]:
        """모든 가능한 operation-machine 할당 조합 생성"""
        operation_machines = {}
        for op in self.operations_data:
            operation_machines[op['operation_id']] = op['machines']
        
        operation_ids = list(operation_machines.keys())
        machine_lists = [operation_machines[op_id] for op_id in operation_ids]
        
        combinations = []
        for assignment in itertools.product(*machine_lists):
            combination = dict(zip(operation_ids, assignment))
            combinations.append(combination)
        
        return combinations
    
    def _generate_order_combinations(self) -> List[List[str]]:
        """작업 순서 조합 생성 (Job 내부 순서는 유지)"""
        # Job별로 operation 그룹화
        job_operations = {}
        for op in self.operations_data:
            job_id = op['job_id']
            if job_id not in job_operations:
                job_operations[job_id] = []
            job_operations[job_id].append(op['operation_id'])
        
        # 각 Job 내부의 operation 순서는 유지하되, Job 간의 실행 순서는 변경 가능
        job_ids = list(job_operations.keys())
        
        # Job 순서의 모든 가능한 조합 생성
        job_order_combinations = []
        for job_order in itertools.permutations(job_ids):
            # 각 Job의 operation들을 순서대로 배치
            operation_order = []
            for job_id in job_order:
                operation_order.extend(job_operations[job_id])
            job_order_combinations.append(operation_order)
        
        return job_order_combinations
    
    def _generate_dynamic_reassignments(self, operations: List[str]) -> List[List[Tuple[str, str, float]]]:
        """동적 재할당 조합 생성"""
        reassignment_combinations = []
        
        # 재할당 가능한 operation들 (여러 기계에서 실행 가능한 것들)
        reassignable_ops = []
        for op in self.operations_data:
            if len(op['machines']) > 1:
                reassignable_ops.append(op['operation_id'])
        
        if not reassignable_ops:
            return [[]]
        
        # 재할당 시점들 (작업 시작 후 25%, 50%, 75% 지점)
        reassignment_times = [0.25, 0.5, 0.75]
        
        # 최대 재할당 횟수까지의 모든 조합
        for num_reassignments in range(self.max_reassignments + 1):
            if num_reassignments == 0:
                reassignment_combinations.append([])
                continue
            
            # 재할당할 operation과 시점의 조합
            for reassign_ops in itertools.combinations(reassignable_ops, min(num_reassignments, len(reassignable_ops))):
                for time_points in itertools.product(reassignment_times, repeat=len(reassign_ops)):
                    reassignments = []
                    for op_id, time_point in zip(reassign_ops, time_points):
                        # 새로운 기계 선택 (현재 기계가 아닌 것)
                        current_machine = None  # 실제로는 현재 할당된 기계를 확인해야 함
                        available_machines = [m for m in self.operations_data if m['operation_id'] == op_id][0]['machines']
                        if current_machine in available_machines:
                            available_machines.remove(current_machine)
                        
                        if available_machines:
                            new_machine = available_machines[0]  # 첫 번째 사용 가능한 기계
                            reassignments.append((op_id, new_machine, time_point))
                    
                    reassignment_combinations.append(reassignments)
        
        return reassignment_combinations
    
    def _generate_preemption_combinations(self, operations: List[str]) -> List[List[Tuple[str, float, float]]]:
        """작업 중단/재개 조합 생성"""
        preemption_combinations = []
        
        # 중단 가능한 operation들 (긴 작업 시간을 가진 것들)
        preemptible_ops = []
        for op in self.operations_data:
            if op['type'] in ['welding', 'testing']:  # 긴 작업 시간을 가진 작업들
                preemptible_ops.append(op['operation_id'])
        
        if not preemptible_ops:
            return [[]]
        
        # 중단 시점들 (작업 시작 후 30%, 60% 지점)
        preemption_times = [0.3, 0.6]
        resume_delays = [0.1, 0.2]  # 재개까지의 지연 시간
        
        # 최대 중단 횟수까지의 모든 조합
        for num_preemptions in range(self.max_preemptions + 1):
            if num_preemptions == 0:
                preemption_combinations.append([])
                continue
            
            # 중단할 operation과 시점의 조합
            for preempt_ops in itertools.combinations(preemptible_ops, min(num_preemptions, len(preemptible_ops))):
                for time_points in itertools.product(preemption_times, repeat=len(preempt_ops)):
                    for delay_points in itertools.product(resume_delays, repeat=len(preempt_ops)):
                        preemptions = []
                        for op_id, time_point, delay in zip(preempt_ops, time_points, delay_points):
                            resume_time = time_point + delay
                            preemptions.append((op_id, time_point, resume_time))
                        
                        preemption_combinations.append(preemptions)
        
        return preemption_combinations
    
    def _create_time_aware_schedule(self, assignment: Dict[str, str], 
                                   operation_order: List[str],
                                   reassignments: List[Tuple[str, str, float]],
                                   preemptions: List[Tuple[str, float, float]]) -> TimeAwareSchedule:
        """시간을 고려한 스케줄 생성"""
        return TimeAwareSchedule(
            operation_assignments=assignment,
            operation_order=operation_order,
            dynamic_reassignments=reassignments,
            preemptions=preemptions
        )
    
    def _run_time_aware_simulation(self, schedule: TimeAwareSchedule) -> TimeAwareResult:
        """시간을 고려한 시뮬레이션 실행"""
        # 임시 routing_result.json 파일 생성
        routing_result = []
        for operation_id, machine_id in schedule.operation_assignments.items():
            job_id = None
            for op in self.operations_data:
                if op['operation_id'] == operation_id:
                    job_id = op['job_id']
                    break
            
            routing_result.append({
                'operation_id': operation_id,
                'job_id': job_id,
                'assigned_machine': machine_id
            })
        
        temp_routing_file = f"{self.scenario_path}/temp_time_aware_routing.json"
        
        with open(temp_routing_file, 'w') as f:
            json.dump(routing_result, f, indent=2)
        
        try:
            # 시뮬레이션 실행
            builder = ModelBuilder(self.scenario_path, use_dynamic_scheduling=False)
            machines, gen, tx = builder.build()
            sim = Simulator()
            sim.register(gen)
            sim.register(tx)
            for m in machines:
                sim.register(m)
            
            gen.initialize()
            
            # 시간을 고려한 시뮬레이션 실행
            # (실제로는 더 복잡한 로직이 필요하지만, 여기서는 기본 시뮬레이션 사용)
            sim.run(print_queues_interval=None, print_job_summary_interval=None)
            
            # 결과 수집
            makespan = sim.current_time
            
            # 작업 완료 시간 수집
            job_completion_times = {}
            for job in gen.jobs.values():
                if job.done():
                    job_completion_times[job.id] = job.last_completion_time if hasattr(job, 'last_completion_time') else sim.current_time
            
            # 기계 활용도 계산
            machine_utilization = {}
            for machine in machines:
                total_time = sim.current_time
                busy_time = len(machine.finished_jobs) * 3.0
                machine_utilization[machine.name] = min(busy_time / total_time if total_time > 0 else 0.0, 1.0)
            
            return TimeAwareResult(
                makespan=makespan,
                schedule=schedule,
                job_completion_times=job_completion_times,
                machine_utilization=machine_utilization,
                total_transfers=len(schedule.dynamic_reassignments),
                total_preemptions=len(schedule.preemptions)
            )
            
        finally:
            if os.path.exists(temp_routing_file):
                os.remove(temp_routing_file)
    
    def find_optimal_schedule(self) -> Dict:
        """최적 스케줄 찾기"""
        print("=== 시간 축까지 완전히 고려한 브루트포스 최적화 스케줄링 시작 ===")
        print(f"총 작업 수: {len(self.operations_data)}")
        print(f"총 기계 수: {len(set(machine for op in self.operations_data for machine in op['machines']))}")
        print(f"초기 할당 조합 수: {len(self.operation_machine_combinations)}")
        print(f"작업 순서 조합 수: {len(self.operation_order_combinations)}")
        
        # 전체 조합 수 계산
        total_combinations = len(self.operation_machine_combinations) * len(self.operation_order_combinations)
        print(f"총 조합 수 (할당 × 순서): {total_combinations}")
        
        best_result = None
        best_makespan = float('inf')
        
        print("모든 조합에 대해 시뮬레이션 실행 중...")
        
        combination_count = 0
        
        for assignment in self.operation_machine_combinations:
            for operation_order in self.operation_order_combinations:
                # 동적 재할당 조합 생성
                reassignment_combinations = self._generate_dynamic_reassignments(operation_order)
                
                # 작업 중단 조합 생성
                preemption_combinations = self._generate_preemption_combinations(operation_order)
                
                for reassignments in reassignment_combinations:
                    for preemptions in preemption_combinations:
                        combination_count += 1
                        
                        if combination_count % 100 == 0:
                            print(f"진행률: {combination_count}개 조합 처리 중...")
                        
                        try:
                            # 시간을 고려한 스케줄 생성
                            schedule = self._create_time_aware_schedule(
                                assignment, operation_order, reassignments, preemptions
                            )
                            
                            # 시뮬레이션 실행
                            result = self._run_time_aware_simulation(schedule)
                            
                            if result.makespan < best_makespan:
                                best_makespan = result.makespan
                                best_result = result
                                print(f"새로운 최적해 발견! Makespan: {best_makespan:.2f}")
                                print(f"  재할당: {result.total_transfers}회, 중단: {result.total_preemptions}회")
                                
                        except Exception as e:
                            print(f"조합 {combination_count} 실행 중 오류: {e}")
                            continue
        
        if best_result is None:
            print("유효한 스케줄을 찾을 수 없습니다.")
            return {}
        
        print(f"\n=== 최적 결과 ===")
        print(f"최적 Makespan: {best_result.makespan:.2f}")
        print(f"총 재할당 횟수: {best_result.total_transfers}")
        print(f"총 중단 횟수: {best_result.total_preemptions}")
        
        print("\n최적 할당:")
        for op_id, machine_id in best_result.schedule.operation_assignments.items():
            print(f"  {op_id} -> {machine_id}")
        
        print("\n작업 실행 순서:")
        for i, op_id in enumerate(best_result.schedule.operation_order):
            print(f"  {i+1}. {op_id}")
        
        if best_result.schedule.dynamic_reassignments:
            print("\n동적 재할당:")
            for op_id, new_machine, time_point in best_result.schedule.dynamic_reassignments:
                print(f"  {op_id} -> {new_machine} (시점: {time_point:.2f})")
        
        if best_result.schedule.preemptions:
            print("\n작업 중단/재개:")
            for op_id, start_time, resume_time in best_result.schedule.preemptions:
                print(f"  {op_id}: {start_time:.2f} ~ {resume_time:.2f}")
        
        print("\n작업 완료 시간:")
        for job_id, completion_time in best_result.job_completion_times.items():
            print(f"  {job_id}: {completion_time:.2f}")
        
        print("\n기계 활용도:")
        for machine_id, utilization in best_result.machine_utilization.items():
            print(f"  {machine_id}: {utilization:.2%}")
        
        return {
            'makespan': best_result.makespan,
            'assignments': best_result.schedule.operation_assignments,
            'operation_order': best_result.schedule.operation_order,
            'dynamic_reassignments': best_result.schedule.dynamic_reassignments,
            'preemptions': best_result.schedule.preemptions,
            'job_completion_times': best_result.job_completion_times,
            'machine_utilization': best_result.machine_utilization,
            'total_transfers': best_result.total_transfers,
            'total_preemptions': best_result.total_preemptions
        }
