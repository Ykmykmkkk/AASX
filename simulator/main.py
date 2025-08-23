# --- simulator/main.py ---
from simulator.engine.simulator import Simulator
from simulator.builder import ModelBuilder
from simulator.control.dynamic_scheduler import DynamicScheduler
from simulator.control.control_tower import SchedulingStrategy
import pandas as pd
import os
import json
import argparse

def print_all_machine_queues(machines):
    """모든 기계의 큐 상태를 출력"""
    print("\n" + "="*50)
    print("모든 기계의 큐 상태")
    print("="*50)
    for machine in machines:
        machine.get_queue_status()

def save_all_job_info(machines, filename='results/job_info.csv'):
    """모든 Job의 정보를 CSV 파일로 저장"""
    all_jobs = []
    for machine in machines:
        # 대기 중인 Job들
        for job in machine.queued_jobs:
            job_dict = job.to_dict()
            job_dict['machine'] = machine.name
            job_dict['queue_type'] = 'queued'
            all_jobs.append(job_dict)
        
        # 실행 중인 Job들
        for job in machine.running_jobs:
            job_dict = job.to_dict()
            job_dict['machine'] = machine.name
            job_dict['queue_type'] = 'running'
            all_jobs.append(job_dict)
        
        # 완료된 Job들
        for job in machine.finished_jobs:
            job_dict = job.to_dict()
            job_dict['machine'] = machine.name
            job_dict['queue_type'] = 'finished'
            all_jobs.append(job_dict)
    
    if all_jobs:
        os.makedirs('results', exist_ok=True)
        df = pd.DataFrame(all_jobs)
        df.to_csv(filename, index=False)
        print(f"[저장 완료] {filename}")
        print(f"총 {len(all_jobs)}개의 Job 정보가 저장되었습니다.")
    else:
        print("[경고] 저장할 Job 정보가 없습니다.")

def save_all_operation_info(machines, filename='results/operation_info.csv'):
    """기존 호환성을 위한 함수 - Job 정보를 Operation 형태로 변환하여 저장"""
    all_ops = []
    for machine in machines:
        # 실행 중인 Job들에서 현재 Operation 정보 추출
        for job in machine.running_jobs:
            if job.current_op():
                op_dict = {
                    'operation_id': job.current_op().id,
                    'status': job.status.name,
                    'location': job.current_location,
                    'input_timestamp': job.last_completion_time,
                    'output_timestamp': None  # 아직 실행 중이므로 None
                }
                all_ops.append(op_dict)
        
        # 완료된 Job들에서 Operation 정보 추출
        for job in machine.finished_jobs:
            if job.current_op():
                op_dict = {
                    'operation_id': job.current_op().id,
                    'status': job.status.name,
                    'location': job.current_location,
                    'input_timestamp': job.last_completion_time,
                    'output_timestamp': job.last_completion_time
                }
                all_ops.append(op_dict)
    
    if all_ops:
        os.makedirs('results', exist_ok=True)
        df = pd.DataFrame(all_ops)
        df.to_csv(filename, index=False)
        print(f"[저장 완료] {filename}")
    else:
        print("[경고] 저장할 operation 정보가 없습니다.")

def apply_dynamic_scheduling(scenario_path, strategy=SchedulingStrategy.LOAD_BALANCING):
    """동적 스케줄링을 적용하고 결과를 저장"""
    print(f"=== 동적 스케줄링 적용 ({strategy.value}) ===")
    
    # 동적 스케줄러 생성
    scheduler = DynamicScheduler(scenario_path, strategy)
    
    # 스케줄링 실행
    assignments = scheduler.schedule_jobs()
    
    # 결과를 routing_result.json 형식으로 변환
    routing_result = []
    for assignment in assignments:
        routing_result.append({
            "operation_id": assignment['operation_id'],
            "job_id": assignment['job_id'],
            "assigned_machine": assignment['assigned_machine']
        })
    
    # 동적 스케줄링 결과 저장
    dynamic_routing_file = f"{scenario_path}/dynamic_routing_result.json"
    with open(dynamic_routing_file, 'w') as f:
        json.dump(routing_result, f, indent=2)
    
    print(f"동적 스케줄링 결과가 {dynamic_routing_file}에 저장되었습니다.")
    
    return routing_result

def backup_and_apply_routing(scenario_path, routing_result, use_dynamic=False):
    """기존 routing_result.json을 백업하고 새로운 결과로 교체"""
    original_routing_file = f"{scenario_path}/routing_result.json"
    backup_routing_file = f"{scenario_path}/routing_result_backup.json"
    
    # 기존 파일 백업
    if os.path.exists(original_routing_file):
        with open(original_routing_file, 'r') as f:
            original_data = json.load(f)
        with open(backup_routing_file, 'w') as f:
            json.dump(original_data, f, indent=2)
        print(f"기존 스케줄링 결과를 {backup_routing_file}에 백업했습니다.")
    
    # 새로운 결과로 교체
    with open(original_routing_file, 'w') as f:
        json.dump(routing_result, f, indent=2)
    
    if use_dynamic:
        print("동적 스케줄링 결과를 적용했습니다.")
    else:
        print("정적 스케줄링 결과를 적용했습니다.")

if __name__ == '__main__':
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='스케줄링 시뮬레이터')
    parser.add_argument('--dynamic', action='store_true', 
                       help='동적 스케줄링 사용 (기본값: 정적 스케줄링)')
    parser.add_argument('--strategy', choices=['load_balancing', 'earliest_available', 'least_loaded', 'shortest_processing_time', 'priority_based'],
                       default='load_balancing', help='동적 스케줄링 전략 (기본값: load_balancing)')
    parser.add_argument('--scenario', default='scenarios/my_case', 
                       help='시나리오 경로 (기본값: scenarios/my_case)')
    
    args = parser.parse_args()
    
    scenario_path = args.scenario
    use_dynamic = args.dynamic
    
    print("="*60)
    print("스케줄링 시뮬레이터")
    print("="*60)
    
    if use_dynamic:
        print(f"모드: 동적 스케줄링")
        print(f"전략: {args.strategy}")
        
        # 동적 스케줄링 적용
        strategy_map = {
            'load_balancing': SchedulingStrategy.LOAD_BALANCING,
            'earliest_available': SchedulingStrategy.EARLIEST_AVAILABLE,
            'least_loaded': SchedulingStrategy.LEAST_LOADED,
            'shortest_processing_time': SchedulingStrategy.SHORTEST_PROCESSING_TIME,
            'priority_based': SchedulingStrategy.PRIORITY_BASED
        }
        
        strategy = strategy_map[args.strategy]
        dynamic_routing = apply_dynamic_scheduling(scenario_path, strategy)
        backup_and_apply_routing(scenario_path, dynamic_routing, use_dynamic=True)
        
        # 결과 파일명 설정
        job_info_file = 'results/dynamic_job_info.csv'
        operation_info_file = 'results/dynamic_operation_info.csv'
        
    else:
        print("모드: 정적 스케줄링")
        print("기존 routing_result.json 파일을 사용합니다.")
        
        # 결과 파일명 설정
        job_info_file = 'results/job_info.csv'
        operation_info_file = 'results/operation_info.csv'
    
    print(f"시나리오: {scenario_path}")
    print("="*60)
    
    # 시뮬레이션 실행
    # 절대 경로로 변환
    import os
    if not os.path.isabs(scenario_path):
        scenario_path = os.path.abspath(scenario_path)
    builder = ModelBuilder(scenario_path)
    machines, gen, tx = builder.build()
    sim = Simulator()
    sim.register(gen)
    sim.register(tx)
    for m in machines:
        sim.register(m)
    gen.initialize()
    
    # 시뮬레이션 실행 전 초기 상태 출력
    print("시뮬레이션 시작 전 상태:")
    print_all_machine_queues(machines)
    
    # 시뮬레이션 실행 (5초마다 큐 상태 출력, 10초마다 Job 상태 요약 출력)
    sim.run(print_queues_interval=5.0, print_job_summary_interval=10.0)
    
    # 시뮬레이션 완료 후 최종 상태 출력
    print("\n시뮬레이션 완료 후 상태:")
    print_all_machine_queues(machines)
    
    # 최종 Job 상태 요약 출력
    print("\n최종 Job 상태 요약:")
    sim.print_job_status_summary()
    
    # 모든 Job 정보 저장
    save_all_job_info(machines, job_info_file)
    
    # 기존 호환성을 위한 Operation 정보 저장
    save_all_operation_info(machines, operation_info_file)
    
    print("\n" + "="*60)
    print("시뮬레이션 완료!")
    print("="*60)
    print(f"결과 파일:")
    print(f"- {job_info_file}: Job 정보")
    print(f"- {operation_info_file}: Operation 정보")
    if use_dynamic:
        print(f"- {scenario_path}/dynamic_routing_result.json: 동적 스케줄링 결과")
        print(f"- {scenario_path}/routing_result_backup.json: 기존 스케줄링 백업")
    print("="*60)
