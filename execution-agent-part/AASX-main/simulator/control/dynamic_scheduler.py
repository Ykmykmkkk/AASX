#!/usr/bin/env python3
"""
동적 머신 할당 스케줄러
Control Tower를 사용하여 operation을 동적으로 최적 할당합니다.
"""

import json
import time
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from simulator.control.control_tower import ControlTower, SchedulingStrategy

class DynamicScheduler:
    """동적 스케줄링을 수행하는 메인 클래스"""
    
    def __init__(self, scenario_path: str, strategy: SchedulingStrategy = SchedulingStrategy.LOAD_BALANCING):
        self.control_tower = ControlTower(scenario_path, strategy)
        self.scenario_path = scenario_path
        self.jobs_data = self._load_jobs()
    
    def _load_jobs(self) -> List[Dict]:
        """Job 정보를 로드합니다."""
        try:
            with open(f"{self.scenario_path}/jobs.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"경고: {self.scenario_path}/jobs.json 파일을 찾을 수 없습니다.")
            return []
    
    def schedule_jobs(self, job_ids: List[str] = None, priorities: Dict[str, int] = None) -> List[Dict]:
        """
        지정된 job들을 스케줄링합니다.
        
        Args:
            job_ids: 스케줄링할 job ID 리스트 (None이면 모든 job)
            priorities: job별 우선순위 딕셔너리
        
        Returns:
            할당 결과 리스트
        """
        if job_ids is None:
            job_ids = [job['job_id'] for job in self.jobs_data]
        
        if priorities is None:
            priorities = {}
        
        print(f"=== 동적 스케줄링 시작 ===")
        print(f"스케줄링 전략: {self.control_tower.scheduling_strategy.value}")
        print(f"스케줄링할 Job 수: {len(job_ids)}")
        
        # Job operations 추가
        for job in self.jobs_data:
            if job['job_id'] in job_ids:
                priority = priorities.get(job['job_id'], 0)
                self.control_tower.add_job_operations(
                    job['job_id'], 
                    job['operations'], 
                    priority
                )
                print(f"Job {job['job_id']} 추가 (우선순위: {priority})")
        
        # 초기 머신 상태 출력
        print("\n=== 초기 머신 상태 ===")
        self._print_machine_status()
        
        # 스케줄링 실행
        assignments = self.control_tower.assign_operations()
        
        print(f"\n=== 스케줄링 결과 ===")
        print(f"총 할당된 Operation 수: {len(assignments)}")
        
        # 할당 결과 출력
        for assignment in assignments:
            print(f"Operation {assignment.operation_id} (Job {assignment.job_id}) -> "
                  f"Machine {assignment.assigned_machine} "
                  f"[{assignment.start_time:.2f} ~ {assignment.estimated_end_time:.2f}]")
        
        # 최종 머신 상태 출력
        print("\n=== 최종 머신 상태 ===")
        self._print_machine_status()
        
        # 통계 출력
        self._print_statistics()
        
        return [assignment.__dict__ for assignment in assignments]
    
    def _print_machine_status(self):
        """머신 상태를 출력합니다."""
        status = self.control_tower.get_machine_status()
        for machine_id, machine_info in status.items():
            print(f"Machine {machine_id}:")
            print(f"  상태: {machine_info['status']}")
            print(f"  다음 가용 시간: {machine_info['next_available_time']:.2f}")
            print(f"  현재 Job: {machine_info['current_job'] or 'None'}")
            print(f"  현재 Operation: {machine_info['current_operation'] or 'None'}")
            print(f"  큐 길이: {machine_info['queue_length']}")
            print(f"  활용도: {machine_info['utilization_rate']:.2%}")
            print()
    
    def _print_statistics(self):
        """스케줄링 통계를 출력합니다."""
        stats = self.control_tower.get_scheduling_statistics()
        print("=== 스케줄링 통계 ===")
        print(f"총 할당 수: {stats['total_assignments']}")
        print(f"총 처리 시간: {stats['total_processing_time']:.2f}")
        print(f"대기 중인 Operation 수: {stats['pending_operations']}")
        print(f"평균 머신 활용도: {stats['average_machine_utilization']:.2%}")
        print()
    
    def export_results(self, filename: str = None) -> str:
        """결과를 파일로 내보냅니다."""
        return self.control_tower.export_routing_result(filename)
    
    def compare_with_static(self, static_routing_file: str = "routing_result.json"):
        """정적 할당과 동적 할당을 비교합니다."""
        try:
            with open(f"{self.scenario_path}/{static_routing_file}", 'r') as f:
                static_assignments = json.load(f)
            
            dynamic_assignments = self.control_tower.assignment_history
            
            print("=== 정적 vs 동적 할당 비교 ===")
            print(f"정적 할당 수: {len(static_assignments)}")
            print(f"동적 할당 수: {len(dynamic_assignments)}")
            
            # 머신별 할당 비교
            static_machine_usage = {}
            dynamic_machine_usage = {}
            
            for assignment in static_assignments:
                machine = assignment['assigned_machine']
                static_machine_usage[machine] = static_machine_usage.get(machine, 0) + 1
            
            for assignment in dynamic_assignments:
                machine = assignment.assigned_machine
                dynamic_machine_usage[machine] = dynamic_machine_usage.get(machine, 0) + 1
            
            print("\n머신별 할당 비교:")
            all_machines = set(static_machine_usage.keys()) | set(dynamic_machine_usage.keys())
            for machine in sorted(all_machines):
                static_count = static_machine_usage.get(machine, 0)
                dynamic_count = dynamic_machine_usage.get(machine, 0)
                print(f"Machine {machine}: 정적 {static_count}개, 동적 {dynamic_count}개")
            
        except FileNotFoundError:
            print(f"정적 할당 파일을 찾을 수 없습니다: {static_routing_file}")

def main():
    """메인 실행 함수"""
    scenario_path = "simulator/scenarios/my_case"
    
    # 다양한 스케줄링 전략으로 테스트
    strategies = [
        SchedulingStrategy.LOAD_BALANCING,
        SchedulingStrategy.EARLIEST_AVAILABLE,
        SchedulingStrategy.LEAST_LOADED,
        SchedulingStrategy.SHORTEST_PROCESSING_TIME
    ]
    
    for strategy in strategies:
        print(f"\n{'='*60}")
        print(f"스케줄링 전략: {strategy.value}")
        print(f"{'='*60}")
        
        scheduler = DynamicScheduler(scenario_path, strategy)
        
        # 우선순위 설정 (예: J1 > J2 > J3)
        priorities = {"J1": 3, "J2": 2, "J3": 1}
        
        # 스케줄링 실행
        assignments = scheduler.schedule_jobs(priorities=priorities)
        
        # 결과 내보내기
        result_file = scheduler.export_results(f"dynamic_routing_{strategy.value}.json")
        print(f"\n결과가 {result_file}에 저장되었습니다.")
        
        # 정적 할당과 비교
        scheduler.compare_with_static()
        
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
