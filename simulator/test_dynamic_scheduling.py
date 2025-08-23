#!/usr/bin/env python3
"""
동적 스케줄링 시스템 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.control.control_tower import ControlTower, SchedulingStrategy
from simulator.control.dynamic_scheduler import DynamicScheduler

def test_basic_functionality():
    """기본 기능 테스트"""
    print("=== 기본 기능 테스트 ===")
    
    scenario_path = "simulator/scenarios/my_case"
    
    # Control Tower 생성
    control_tower = ControlTower(scenario_path, SchedulingStrategy.LOAD_BALANCING)
    
    # 머신 상태 확인
    print("초기 머신 상태:")
    status = control_tower.get_machine_status()
    for machine_id, info in status.items():
        print(f"  {machine_id}: {info['status']}")
    
    # Job operations 추가
    print("\nJob operations 추가:")
    control_tower.add_job_operations("J1", ["O11", "O12", "O13"], priority=3)
    control_tower.add_job_operations("J2", ["O21", "O22"], priority=2)
    control_tower.add_job_operations("J3", ["O31", "O32"], priority=1)
    
    print(f"대기 중인 operations: {len(control_tower.pending_operations)}")
    
    # 스케줄링 실행
    assignments = control_tower.assign_operations()
    
    print(f"\n할당된 operations: {len(assignments)}")
    for assignment in assignments:
        print(f"  {assignment.operation_id} -> {assignment.assigned_machine}")
    
    # 결과 내보내기
    result_file = control_tower.export_routing_result()
    print(f"\n결과가 {result_file}에 저장되었습니다.")

def test_different_strategies():
    """다양한 스케줄링 전략 테스트"""
    print("\n=== 다양한 스케줄링 전략 테스트 ===")
    
    scenario_path = "simulator/scenarios/my_case"
    strategies = [
        SchedulingStrategy.LOAD_BALANCING,
        SchedulingStrategy.EARLIEST_AVAILABLE,
        SchedulingStrategy.LEAST_LOADED,
        SchedulingStrategy.SHORTEST_PROCESSING_TIME
    ]
    
    for strategy in strategies:
        print(f"\n--- {strategy.value} 전략 ---")
        
        scheduler = DynamicScheduler(scenario_path, strategy)
        
        # 모든 job 스케줄링
        assignments = scheduler.schedule_jobs()
        
        print(f"할당된 operations: {len(assignments)}")
        
        # 머신별 할당 현황
        machine_assignments = {}
        for assignment in assignments:
            machine = assignment['assigned_machine']
            machine_assignments[machine] = machine_assignments.get(machine, 0) + 1
        
        for machine, count in sorted(machine_assignments.items()):
            print(f"  {machine}: {count}개 operations")

def test_priority_scheduling():
    """우선순위 기반 스케줄링 테스트"""
    print("\n=== 우선순위 기반 스케줄링 테스트 ===")
    
    scenario_path = "simulator/scenarios/my_case"
    scheduler = DynamicScheduler(scenario_path, SchedulingStrategy.PRIORITY_BASED)
    
    # 우선순위 설정 (J3 > J2 > J1)
    priorities = {"J3": 3, "J2": 2, "J1": 1}
    
    assignments = scheduler.schedule_jobs(priorities=priorities)
    
    print("우선순위별 할당 결과:")
    job_assignments = {}
    for assignment in assignments:
        job = assignment['job_id']
        if job not in job_assignments:
            job_assignments[job] = []
        job_assignments[job].append(assignment)
    
    for job in ["J3", "J2", "J1"]:
        if job in job_assignments:
            print(f"  {job} (우선순위: {priorities.get(job, 0)}): {len(job_assignments[job])}개 operations")

def test_machine_utilization():
    """머신 활용도 테스트"""
    print("\n=== 머신 활용도 테스트 ===")
    
    scenario_path = "simulator/scenarios/my_case"
    scheduler = DynamicScheduler(scenario_path, SchedulingStrategy.LOAD_BALANCING)
    
    # 스케줄링 실행
    assignments = scheduler.schedule_jobs()
    
    # 통계 출력
    stats = scheduler.control_tower.get_scheduling_statistics()
    print(f"평균 머신 활용도: {stats['average_machine_utilization']:.2%}")
    print(f"총 처리 시간: {stats['total_processing_time']:.2f}")
    
    # 머신별 활용도
    machine_status = scheduler.control_tower.get_machine_status()
    for machine_id, info in machine_status.items():
        print(f"  {machine_id}: {info['utilization_rate']:.2%}")

if __name__ == "__main__":
    print("동적 스케줄링 시스템 테스트 시작\n")
    
    try:
        test_basic_functionality()
        test_different_strategies()
        test_priority_scheduling()
        test_machine_utilization()
        
        print("\n=== 모든 테스트 완료 ===")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
