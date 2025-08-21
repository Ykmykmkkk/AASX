# --- simulator/main.py ---
from simulator.engine.simulator import Simulator
from simulator.builder import ModelBuilder
import pandas as pd
import os

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
    builder = ModelBuilder('scenarios/my_case')
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
    save_all_job_info(machines)
    
    # 기존 호환성을 위한 Operation 정보 저장
    save_all_operation_info(machines)
