#!/usr/bin/env python3
"""
Debug Goal 1 execution to find why jobs are not being filtered
"""

import sys
import os
import json
sys.path.append('./src')

from data_collector import DataCollector
from ontology_manager import OntologyManager

def debug_snapshot_data():
    """스냅샷 데이터 디버깅"""
    collector = DataCollector()
    
    print("=" * 60)
    print("🔍 DEBUGGING SNAPSHOT DATA")
    print("=" * 60)
    
    # T4 시점 jobs 데이터 확인
    print("\n📋 Jobs at T4 (Failure time):")
    jobs = collector.collect_from_snapshot("T4", "jobs")
    if jobs:
        for job in jobs:
            print(f"  - Job: {job.get('job_id')}")
            print(f"    Product: {job.get('product_id')}")
            print(f"    Machine: {job.get('machine_id')}")
            print(f"    Status: {job.get('status')}")
            print(f"    Failure: {job.get('failure_reason', 'N/A')}")
            print()
    
    # T2 시점 machines 데이터 확인
    print("\n🏭 Machines at T2:")
    machines = collector.collect_from_snapshot("T2", "machines")
    if machines:
        for machine_id, machine in machines.items():
            if machine.get("cooling_required"):
                print(f"  - {machine_id}: cooling_required={machine.get('cooling_required')}")
    
    # 냉각 필요 제품 하드코딩
    print("\n❄️ Products requiring cooling (hardcoded):")
    cooling_products = ["Product-B1", "Product-C1"]
    print(f"  {cooling_products}")
    
    # 필터링 테스트
    print("\n🔍 Testing filter:")
    cooling_machines = [m for mid, m in machines.items() if m.get("cooling_required")]
    print(f"  Cooling machines: {[m['machine_id'] for m in cooling_machines]}")
    print(f"  Cooling products: {cooling_products}")
    
    failed_jobs = collector.filter_failed_jobs(jobs, cooling_products, cooling_machines)
    print(f"\n✅ Result: Found {len(failed_jobs)} failed jobs")
    
    for job in failed_jobs:
        print(f"  - {job['job_id']}: {job['product_id']} on {job['machine_id']}")


if __name__ == "__main__":
    debug_snapshot_data()