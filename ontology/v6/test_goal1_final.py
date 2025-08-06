#!/usr/bin/env python3
"""
Final Test for Goal 1: Query Failed Jobs with Cooling
"""

import sys
import os
import json
sys.path.append('./src')

from execution_planner import ExecutionPlanner


def test_goal1_final():
    """Goal 1 최종 테스트"""
    print("=" * 60)
    print("🎯 Goal 1: Query Failed Jobs with Cooling Requirements")
    print("=" * 60)
    
    planner = ExecutionPlanner()
    
    # DSL 입력
    dsl_input = {
        "goal": "query_failed_jobs_with_cooling",
        "parameters": {
            "date": "2025-07-17"
        }
    }
    
    print(f"\n📥 DSL Input:")
    print(json.dumps(dsl_input, indent=2))
    
    # 실행 계획 수립
    print(f"\n📋 Creating Execution Plan...")
    plan = planner.create_execution_plan(
        dsl_input["goal"],
        dsl_input["parameters"]
    )
    
    if not plan:
        print("❌ Failed to create execution plan")
        return
        
    print(f"✅ Plan created with {len(plan['actions'])} actions")
    
    # 실행 (디버깅 정보 포함)
    print(f"\n🚀 Executing Plan with Debug Info...")
    print("-" * 40)
    
    # 각 액션 실행 후 컨텍스트 출력
    result = planner.execute_plan(plan)
    
    # 실행 컨텍스트 확인
    print("-" * 40)
    print("\n📦 Execution Context:")
    print(f"  cooling_products: {planner.execution_context.get('cooling_products', [])}")
    print(f"  cooling_machines: {len(planner.execution_context.get('cooling_machines', {}))} machines")
    print(f"  all_jobs: {len(planner.execution_context.get('all_jobs', []))} jobs")
    print(f"  failed_cooling_jobs: {len(planner.execution_context.get('failed_cooling_jobs', []))} failed")
    
    # 결과 출력
    print(f"\n📊 Final Result:")
    print(f"   Status: {result['status']}")
    
    if result["status"] == "SUCCESS":
        data = result.get("data", {})
        summary = data.get("summary", {})
        failed_jobs = data.get("failed_jobs", [])
        
        print(f"\n📈 Summary:")
        print(f"   Date: {summary.get('date')}")
        print(f"   Total Failed Jobs: {summary.get('total_failed', 0)}")
        print(f"   Cooling Related: {summary.get('cooling_related', False)}")
        
        if failed_jobs:
            print(f"\n❌ Failed Jobs Detail:")
            for job in failed_jobs:
                print(f"   - Job ID: {job.get('job_id')}")
                print(f"     Product: {job.get('product_id')}")
                print(f"     Machine: {job.get('machine_id')}")
                print(f"     Failure: {job.get('failure_reason')}")
                print(f"     Details: {job.get('error_details')}")
                print()
        else:
            print(f"\n⚠️ No failed jobs found, but we expected 3!")
            print(f"   Expected: JOB-001, JOB-002, JOB-003")
            
            # 추가 디버깅
            print(f"\n🔍 Debugging why jobs weren't filtered:")
            cooling_products = planner.execution_context.get('cooling_products', [])
            cooling_machines = planner.execution_context.get('cooling_machines', {})
            all_jobs = planner.execution_context.get('all_jobs', [])
            
            if not cooling_products:
                print("   ❌ No cooling products found")
            else:
                print(f"   ✅ Cooling products: {cooling_products}")
                
            if not cooling_machines:
                print("   ❌ No cooling machines found")
            else:
                cooling_machine_ids = [m.get("machine_id") for m in cooling_machines.values()] if isinstance(cooling_machines, dict) else [m.get("machine_id") for m in cooling_machines]
                print(f"   ✅ Cooling machines: {cooling_machine_ids}")
                
            if not all_jobs:
                print("   ❌ No jobs found")
            else:
                print(f"   ✅ Jobs found: {len(all_jobs)}")
                for job in all_jobs:
                    if job.get("status") == "FAILED":
                        print(f"      Failed job: {job.get('job_id')} - Product: {job.get('product_id')}, Machine: {job.get('machine_id')}")
    else:
        print(f"   Error: {result.get('error')}")
    
    print("=" * 60)
    print("✅ Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_goal1_final()