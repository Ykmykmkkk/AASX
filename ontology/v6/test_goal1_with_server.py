#!/usr/bin/env python3
"""
Test Goal 1 with AAS Server
실제 Mock Server와 통신하는 통합 테스트
"""

import sys
import os
import json
import time
sys.path.append('./src')

from execution_planner import ExecutionPlanner
from data_collector_v2 import DataCollectorV2
from aas_client import AASClient


def check_server_status():
    """서버 상태 확인"""
    client = AASClient()
    try:
        if client.health_check():
            print("✅ AAS Server is running")
            return True
        else:
            print("❌ AAS Server is not responding")
            print("   Please start the server with:")
            print("   cd src && python3 mock_server.py")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Please start the server with:")
        print("   cd src && python3 mock_server.py")
        return False


def test_goal1_with_aas():
    """Goal 1 테스트 with AAS Server"""
    print("=" * 60)
    print("🎯 Goal 1: Query Failed Jobs with Cooling (AAS Server)")
    print("=" * 60)
    
    # 서버 상태 확인
    if not check_server_status():
        print("\n⚠️ Test aborted: Server not available")
        return
    
    # ExecutionPlanner 수정 필요 (DataCollectorV2 사용)
    # 여기서는 직접 DataCollectorV2 테스트
    collector = DataCollectorV2()
    
    print("\n📊 Collecting data from AAS Server...")
    print("-" * 40)
    
    # 1. 냉각 제품 조회
    print("\n1️⃣ Getting cooling products...")
    cooling_products = collector.collect_cooling_products()
    print(f"   Found {len(cooling_products)} products: {cooling_products}")
    
    # 2. 냉각 기계 조회
    print("\n2️⃣ Getting cooling machines...")
    cooling_machines = collector.collect_machines_with_cooling()
    print(f"   Found {len(cooling_machines)} machines:")
    for machine in cooling_machines:
        print(f"     - {machine.get('machine_id')}")
    
    # 3. 작업 이력 조회
    print("\n3️⃣ Getting job history (failed jobs)...")
    failed_jobs = collector.collect_job_history("2025-07-17")
    print(f"   Found {len(failed_jobs)} jobs:")
    for job in failed_jobs[:3]:  # 처음 3개만 출력
        print(f"     - {job.get('job_id')}: {job.get('status')} ({job.get('failure_reason')})")
    
    # 4. 필터링
    print("\n4️⃣ Filtering failed jobs with cooling...")
    filtered_jobs = collector.filter_failed_jobs(
        failed_jobs, 
        cooling_products,
        cooling_machines
    )
    
    print(f"   Filtered {len(filtered_jobs)} jobs")
    
    # 5. 결과 출력
    print("\n" + "=" * 60)
    print("📈 Final Result:")
    print("=" * 60)
    print(f"Total Failed Jobs: {len(filtered_jobs)}")
    print(f"Date: 2025-07-17")
    print(f"Cooling Related: True")
    
    if filtered_jobs:
        print(f"\n❌ Failed Jobs Detail:")
        for job in filtered_jobs:
            print(f"  - Job ID: {job.get('job_id')}")
            print(f"    Product: {job.get('product_id')}")
            print(f"    Machine: {job.get('machine_id')}")
            print(f"    Failure: {job.get('failure_reason')}")
            print(f"    Details: {job.get('error_details')}")
            print()
    
    print("=" * 60)
    print("✅ Test Complete")
    print("=" * 60)


def test_aas_client_only():
    """AAS Client만 테스트"""
    print("\n🔍 Testing AAS Client directly...")
    print("-" * 40)
    
    client = AASClient()
    
    # Shell 조회
    shells = client.get_shells()
    print(f"Shells: {len(shells)}")
    
    # 냉각 기계
    machines = client.get_cooling_machines()
    print(f"Cooling machines: {len(machines)}")
    
    # 냉각 제품
    products = client.get_cooling_products()
    print(f"Cooling products: {products}")
    
    # 실패 작업
    jobs = client.get_failed_jobs("2025-07-17")
    print(f"Failed jobs: {len(jobs)}")


if __name__ == "__main__":
    # 서버 연결 테스트
    print("🔌 Checking server connection...")
    
    if check_server_status():
        # 메인 테스트
        test_goal1_with_aas()
        
        # 추가 테스트 (선택적)
        # test_aas_client_only()
    else:
        print("\n⚠️ Running in fallback mode (local snapshots)...")
        collector = DataCollectorV2()
        
        # fallback 모드에서도 동작 확인
        products = collector.collect_cooling_products()
        print(f"Cooling products (fallback): {products}")
        
        machines = collector.collect_machines_with_cooling()
        print(f"Cooling machines (fallback): {len(machines)}")