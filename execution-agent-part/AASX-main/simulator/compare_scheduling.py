#!/usr/bin/env python3
"""
정적 할당과 동적 할당 비교 분석 스크립트
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.control.control_tower import SchedulingStrategy

def load_routing_result(filename):
    """라우팅 결과 파일을 로드합니다."""
    with open(filename, 'r') as f:
        return json.load(f)

def analyze_assignments(assignments):
    """할당 결과를 분석합니다."""
    machine_usage = {}
    job_assignments = {}
    total_operations = len(assignments)
    
    for assignment in assignments:
        machine = assignment['assigned_machine']
        job = assignment['job_id']
        
        # 머신별 사용량
        if machine not in machine_usage:
            machine_usage[machine] = 0
        machine_usage[machine] += 1
        
        # Job별 할당
        if job not in job_assignments:
            job_assignments[job] = []
        job_assignments[job].append(assignment)
    
    return {
        'total_operations': total_operations,
        'machine_usage': machine_usage,
        'job_assignments': job_assignments
    }

def compare_scheduling_methods():
    """정적 할당과 동적 할당을 비교합니다."""
    scenario_path = "simulator/scenarios/my_case"
    
    # 정적 할당 로드
    static_assignments = load_routing_result(f"{scenario_path}/routing_result.json")
    static_analysis = analyze_assignments(static_assignments)
    
    # 동적 할당 로드
    dynamic_assignments = load_routing_result(f"{scenario_path}/dynamic_routing_result.json")
    dynamic_analysis = analyze_assignments(dynamic_assignments)
    
    print("=== 정적 vs 동적 할당 비교 분석 ===")
    print()
    
    # 기본 통계
    print("기본 통계:")
    print(f"  정적 할당: {static_analysis['total_operations']}개 operations")
    print(f"  동적 할당: {dynamic_analysis['total_operations']}개 operations")
    print()
    
    # 머신별 사용량 비교
    print("머신별 사용량 비교:")
    all_machines = set(static_analysis['machine_usage'].keys()) | set(dynamic_analysis['machine_usage'].keys())
    
    for machine in sorted(all_machines):
        static_count = static_analysis['machine_usage'].get(machine, 0)
        dynamic_count = dynamic_analysis['machine_usage'].get(machine, 0)
        difference = dynamic_count - static_count
        
        print(f"  {machine}:")
        print(f"    정적: {static_count}개 operations")
        print(f"    동적: {dynamic_count}개 operations")
        print(f"    차이: {difference:+d}개 operations")
        print()
    
    # Job별 할당 비교
    print("Job별 할당 비교:")
    all_jobs = set(static_analysis['job_assignments'].keys()) | set(dynamic_analysis['job_assignments'].keys())
    
    for job in sorted(all_jobs):
        static_ops = static_analysis['job_assignments'].get(job, [])
        dynamic_ops = dynamic_analysis['job_assignments'].get(job, [])
        
        print(f"  {job}:")
        print(f"    정적: {len(static_ops)}개 operations")
        print(f"    동적: {len(dynamic_ops)}개 operations")
        
        # 동적 할당의 경우 시간 정보도 표시
        if dynamic_ops:
            start_times = [op.get('start_time', 0) for op in dynamic_ops]
            end_times = [op.get('estimated_end_time', 0) for op in dynamic_ops]
            total_duration = max(end_times) - min(start_times) if start_times and end_times else 0
            print(f"    예상 총 처리 시간: {total_duration:.2f} 시간 단위")
        print()
    
    # 동적 할당의 추가 정보
    print("동적 할당 추가 정보:")
    if dynamic_assignments:
        # 우선순위별 분석
        priority_groups = {}
        for assignment in dynamic_assignments:
            priority = assignment.get('priority_score', 0)
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(assignment)
        
        print("  우선순위별 할당:")
        for priority in sorted(priority_groups.keys(), reverse=True):
            ops = priority_groups[priority]
            print(f"    우선순위 {priority}: {len(ops)}개 operations")
        
        # 시간 기반 분석
        start_times = [op.get('start_time', 0) for op in dynamic_assignments]
        end_times = [op.get('estimated_end_time', 0) for op in dynamic_assignments]
        
        if start_times and end_times:
            total_duration = max(end_times) - min(start_times)
            avg_duration = sum(end_times) - sum(start_times)
            print(f"  전체 예상 처리 시간: {total_duration:.2f} 시간 단위")
            print(f"  평균 operation 처리 시간: {avg_duration/len(dynamic_assignments):.2f} 시간 단위")
    
    print()
    print("=== 분석 완료 ===")

def analyze_different_strategies():
    """다양한 스케줄링 전략의 결과를 분석합니다."""
    scenario_path = "simulator/scenarios/my_case"
    strategies = [
        "load_balancing",
        "earliest_available", 
        "least_loaded",
        "shortest_processing_time"
    ]
    
    print("=== 다양한 스케줄링 전략 비교 ===")
    print()
    
    strategy_results = {}
    
    for strategy in strategies:
        filename = f"dynamic_routing_{strategy}.json"
        try:
            assignments = load_routing_result(filename)
            analysis = analyze_assignments(assignments)
            strategy_results[strategy] = analysis
            
            print(f"{strategy} 전략:")
            print(f"  총 operations: {analysis['total_operations']}개")
            
            # 머신별 분포
            machine_dist = analysis['machine_usage']
            for machine, count in sorted(machine_dist.items()):
                print(f"    {machine}: {count}개")
            
            # 총 처리 시간 계산
            if assignments:
                end_times = [op.get('estimated_end_time', 0) for op in assignments]
                total_time = max(end_times) if end_times else 0
                print(f"  총 처리 시간: {total_time:.2f} 시간 단위")
            
            print()
            
        except FileNotFoundError:
            print(f"{strategy} 전략 결과 파일을 찾을 수 없습니다.")
            print()
    
    # 최적 전략 찾기
    if strategy_results:
        print("전략별 성능 비교:")
        for strategy, analysis in strategy_results.items():
            filename = f"dynamic_routing_{strategy}.json"
            try:
                assignments = load_routing_result(filename)
                end_times = [op.get('estimated_end_time', 0) for op in assignments]
                total_time = max(end_times) if end_times else 0
                print(f"  {strategy}: {total_time:.2f} 시간 단위")
            except:
                pass
        
        # 가장 빠른 전략 찾기
        fastest_strategy = min(strategy_results.keys(), 
                             key=lambda s: max([op.get('estimated_end_time', 0) 
                                              for op in load_routing_result(f"dynamic_routing_{s}.json")]))
        print(f"\n가장 빠른 전략: {fastest_strategy}")

if __name__ == "__main__":
    print("스케줄링 방법 비교 분석 시작\n")
    
    try:
        compare_scheduling_methods()
        print()
        analyze_different_strategies()
        
    except Exception as e:
        print(f"분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
