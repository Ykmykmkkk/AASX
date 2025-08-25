# --- simulator/main.py ---
from simulator.engine.simulator import Simulator
from simulator.builder import ModelBuilder
import pandas as pd
import os
import sys
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



if __name__ == '__main__':
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='시뮬레이터 기반 최적화 스케줄러')
    parser.add_argument('--mode', choices=['static', 'time_aware_brute_force', 'simulator_optimization'], default='simulator_optimization',
                        help='스케줄링 모드 (기본값: simulator_optimization)')
    parser.add_argument('--algorithm', choices=['dfs', 'branch_and_bound', 'mcts'], default='branch_and_bound',
                       help='시뮬레이터 기반 최적화 알고리즘 (기본값: branch_and_bound)')
    parser.add_argument('--policy', choices=['ect', 'spt', 'atc', 'edd'], default='ect',
                       help='롤아웃 정책 (기본값: ect)')
    parser.add_argument('--time_limit', type=float, default=300.0,
                       help='최적화 시간 제한 (초, 기본값: 300)')
    parser.add_argument('--max_nodes', type=int, default=10000,
                       help='최대 탐색 노드 수 (기본값: 10000)')
    parser.add_argument('--scenario', default='scenarios/my_case', 
                       help='시나리오 경로 (기본값: scenarios/my_case)')
    
    args = parser.parse_args()
    
    scenario_path = args.scenario
    mode = args.mode
    
    print("="*60)
    print("스케줄링 시뮬레이터")
    print("="*60)
    
    if mode == 'time_aware_brute_force':
        print(f"모드: 시간 축까지 완전히 고려한 브루트포스 최적화 스케줄링")
        
        # 시간 축을 고려한 브루트포스 스케줄러 import 및 실행
        from simulator.control.time_aware_brute_force import TimeAwareBruteForceScheduler
        
        scheduler = TimeAwareBruteForceScheduler(scenario_path)
        result = scheduler.find_optimal_schedule()
        
        if result:
            print(f"\n=== 시간 축까지 완전히 고려한 브루트포스 최적화 결과 ===")
            print(f"최적 Makespan: {result['makespan']:.2f}")
            print(f"총 재할당 횟수: {result['total_transfers']}")
            print(f"총 중단 횟수: {result['total_preemptions']}")
            
            print("\n최적 할당:")
            for op_id, machine_id in result['assignments'].items():
                print(f"  {op_id} -> {machine_id}")
            
            print("\n작업 실행 순서:")
            for i, op_id in enumerate(result['operation_order']):
                print(f"  {i+1}. {op_id}")
            
            if result['dynamic_reassignments']:
                print("\n동적 재할당:")
                for op_id, new_machine, time_point in result['dynamic_reassignments']:
                    print(f"  {op_id} -> {new_machine} (시점: {time_point:.2f})")
            
            if result['preemptions']:
                print("\n작업 중단/재개:")
                for op_id, start_time, resume_time in result['preemptions']:
                    print(f"  {op_id}: {start_time:.2f} ~ {resume_time:.2f}")
            
            print("\n작업 완료 시간:")
            for job_id, completion_time in result['job_completion_times'].items():
                print(f"  {job_id}: {completion_time:.2f}")
            
            print("\n기계 활용도:")
            for machine_id, utilization in result['machine_utilization'].items():
                print(f"  {machine_id}: {utilization:.2%}")
            
            # 결과를 JSON 파일로 저장
            import json
            os.makedirs('results', exist_ok=True)
            with open('results/time_aware_brute_force_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n결과가 results/time_aware_brute_force_result.json에 저장되었습니다.")
            
            # 최적 결과를 routing_result.json에 적용
            print("\n최적 결과를 routing_result.json에 적용 중...")
            
            # operations.json 파일에서 operation 정보 로드
            with open(f"{scenario_path}/operations.json", 'r') as f:
                operations_data = json.load(f)
            
            routing_result = []
            for operation_id, machine_id in result['assignments'].items():
                # operation_id에서 job_id 찾기
                job_id = None
                for op in operations_data:
                    if op['operation_id'] == operation_id:
                        job_id = op['job_id']
                        break
                
                routing_result.append({
                    'operation_id': operation_id,
                    'job_id': job_id,
                    'assigned_machine': machine_id
                })
            
            with open(f"{scenario_path}/routing_result.json", 'w') as f:
                json.dump(routing_result, f, indent=2)
            
            # 정적 시뮬레이션으로 최적 결과 검증 및 trace.xlsx 생성
            print("\n최적 결과로 정적 시뮬레이션 실행 중...")
            
            # ModelBuilder로 모델 생성 (정적 모드)
            builder = ModelBuilder(scenario_path, use_dynamic_scheduling=False)
            machines, gen, tx = builder.build()
            
            # Simulator 생성
            sim = Simulator()
            
            # 모델 등록
            for m in machines:
                sim.register(m)
            sim.register(gen)
            sim.register(tx)
            
            # 시뮬레이션 실행
            gen.initialize()
            sim.run(print_queues_interval=None, print_job_summary_interval=None)
            
            # 시뮬레이션 완료 후 최종 상태 출력
            print("\n시뮬레이션 완료 후 상태:")
            print_all_machine_queues(machines)
            
            # 최종 Job 상태 요약 출력
            print("\n최종 Job 상태 요약:")
            sim.print_job_status_summary()
            
            # transducer finalize 호출하여 trace.xlsx 생성
            tx.finalize()
            
            print(f"\n=== 시간 축까지 완전히 고려한 브루트포스 최적화 결과로 생성된 trace.xlsx ===")
            print("results/trace.xlsx 파일이 생성되었습니다.")
            sys.exit(0)
            
    elif mode == 'simulator_optimization':
        print(f"모드: 시뮬레이터 기반 최적화 스케줄링")
        print(f"알고리즘: {args.algorithm}")
        print(f"롤아웃 정책: {args.policy}")
        print(f"시간 제한: {args.time_limit}초")
        print(f"최대 노드 수: {args.max_nodes}")
        
        # 시뮬레이터 기반 최적화 실행
        from simulator.control.simulator_based_optimizer import SimulatorBasedOptimizer, SearchAlgorithm, Policy
        
        # 알고리즘 매핑
        algorithm_map = {
            'dfs': SearchAlgorithm.DFS,
            'branch_and_bound': SearchAlgorithm.BRANCH_AND_BOUND,
            'mcts': SearchAlgorithm.MCTS
        }
        
        # 정책 매핑
        policy_map = {
            'ect': Policy.ECT,
            'spt': Policy.SPT,
            'atc': Policy.ATC,
            'edd': Policy.EDD
        }
        
        # 시뮬레이터 설정 (정적 모드로 초기화 - 최적화를 위해)
        builder = ModelBuilder(scenario_path, use_dynamic_scheduling=False)
        machines, gen, tx = builder.build()
        
        # Simulator 생성 (Control Tower 없이)
        sim = Simulator()
        
        # 모델 등록
        for m in machines:
            sim.register(m)
        sim.register(gen)
        sim.register(tx)
        
        # Generator 초기화 (이벤트 생성)
        gen.initialize()
        
        # 최적화 실행
        optimizer = SimulatorBasedOptimizer(
            simulator=sim,
            algorithm=algorithm_map[args.algorithm],
            time_limit=args.time_limit,
            max_nodes=args.max_nodes,
            rollout_policy=policy_map[args.policy],
            seed=42
        )
        
        print("\n시뮬레이터 기반 최적화 시작...")
        result = optimizer.optimize()
        
        # 결과 출력
        optimizer.print_search_summary(result)
        
        # 결과를 JSON 파일로 저장
        import json
        os.makedirs('results', exist_ok=True)
        
        result_dict = {
            'algorithm': result.algorithm.name,
            'best_objective': result.best_objective,
            'search_time': result.search_time,
            'nodes_explored': result.nodes_explored,
            'best_schedule': [str(action) for action in result.best_schedule],
            'search_log': result.search_log
        }
        
        with open('results/simulator_optimization_result.json', 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        print(f"\n결과가 results/simulator_optimization_result.json에 저장되었습니다.")
        
        # 최적 스케줄을 적용하여 시뮬레이션 실행
        if result.best_schedule:
            print("\n최적 스케줄을 적용하여 시뮬레이션 실행 중...")
            
            # 시뮬레이터 초기화
            sim = Simulator()
            
            # 모델 재생성 (정적 모드)
            builder = ModelBuilder(scenario_path, use_dynamic_scheduling=False)
            machines, gen, tx = builder.build()
            
            # 모델 등록
            for m in machines:
                sim.register(m)
            sim.register(gen)
            sim.register(tx)
            
            # 시뮬레이션 실행
            gen.initialize()
            sim.run(print_queues_interval=None, print_job_summary_interval=None)
            
            # 시뮬레이션 완료 후 최종 상태 출력
            print("\n시뮬레이션 완료 후 상태:")
            print_all_machine_queues(machines)
            
            # 최종 Job 상태 요약 출력
            print("\n최종 Job 상태 요약:")
            sim.print_job_status_summary()
            
            # transducer finalize 호출하여 trace.xlsx 생성
            tx.finalize()
            
            print(f"\n=== 시뮬레이터 기반 최적화 결과로 생성된 trace.xlsx ===")
            print("results/trace.xlsx 파일이 생성되었습니다.")
        else:
            print("\n최적 스케줄이 없어서 기본 시뮬레이션을 실행합니다...")
            
            # 기본 시뮬레이션 실행 (정적 모드)
            builder = ModelBuilder(scenario_path, use_dynamic_scheduling=False)
            machines, gen, tx = builder.build()
            sim = Simulator()
            sim.register(gen)
            sim.register(tx)
            for m in machines:
                sim.register(m)
            gen.initialize()
            
            # 시뮬레이션 실행
            sim.run(print_queues_interval=None, print_job_summary_interval=None)
            
            # 시뮬레이션 완료 후 최종 상태 출력
            print("\n시뮬레이션 완료 후 상태:")
            print_all_machine_queues(machines)
            
            # 최종 Job 상태 요약 출력
            print("\n최종 Job 상태 요약:")
            sim.print_job_status_summary()
            
            # transducer finalize 호출하여 trace.xlsx 생성
            tx.finalize()
            
            print(f"\n=== 기본 시뮬레이션으로 생성된 trace.xlsx ===")
            print("results/trace.xlsx 파일이 생성되었습니다.")
        
        sys.exit(0)
            

            

        
    else:  # static mode
        print("모드: 정적 스케줄링")
        print("기존 routing_result.json 파일을 사용합니다.")
        
        # 기존 정적 시뮬레이션 실행
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
        
        # 시뮬레이션 실행
        sim.run(print_queues_interval=5.0, print_job_summary_interval=10.0)
        
        # 결과 파일명 설정
        job_info_file = 'results/job_info.csv'
        operation_info_file = 'results/operation_info.csv'
    
    print(f"시나리오: {scenario_path}")
    print("="*60)
    
    # 시뮬레이션 완료 후 최종 상태 출력
    print("\n시뮬레이션 완료 후 상태:")
    print_all_machine_queues(machines)
    
    # 최종 Job 상태 요약 출력
    print("\n최종 Job 상태 요약:")
    sim.print_job_status_summary()
    
    # trace 파일 저장 (시뮬레이션 완료 후 한 번만)
    tx.finalize()
    
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
    print(f"- results/trace.csv: 시뮬레이션 이벤트 로그")
    print(f"- results/trace.xlsx: 시뮬레이션 이벤트 로그 (Excel)")
    if mode == 'time_aware_brute_force':
        print(f"- 시간 축까지 완전히 고려한 브루트포스 최적화 스케줄링 완료")
    elif mode == 'simulator_optimization':
        print(f"- 시뮬레이터 기반 최적화 스케줄링 완료")
    else:
        print(f"- 정적 스케줄링 완료")
    print("="*60)
