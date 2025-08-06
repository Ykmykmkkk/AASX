#!/usr/bin/env python3
"""
Test Goal 1: Query Failed Jobs with Cooling
v6 AAS Integration 테스트
"""

import sys
import os
sys.path.append('./src')

from execution_planner import ExecutionPlanner
import json


def test_goal1():
    """Goal 1 테스트: 냉각 실패 작업 조회"""
    print("=" * 60)
    print("🎯 Goal 1: Query Failed Jobs with Cooling Requirements")
    print("=" * 60)
    
    # 실행 계획 생성
    planner = ExecutionPlanner()
    
    # DSL 입력 시뮬레이션
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
        
    print(f"✅ Plan created with {len(plan['actions'])} actions:")
    for action in plan["actions"]:
        print(f"   {action['order']}. {action['label']} ({action['type']})")
    
    # 실행
    print(f"\n🚀 Executing Plan...")
    result = planner.execute_plan(plan)
    
    # 결과 출력
    print(f"\n📊 Execution Result:")
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
        print(f"   Error: {result.get('error')}")
    
    print("=" * 60)
    print("✅ Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_goal1()