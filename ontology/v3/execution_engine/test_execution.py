#!/usr/bin/env python3
"""
Execution Engine 테스트 스크립트
실행 엔진과 DSL 플래너를 통합하여 4개의 Goal을 테스트
"""

import sys
import os
import json
from datetime import datetime

# 상위 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 모듈을 직접 import
import importlib.util
spec = importlib.util.spec_from_file_location(
    "dsl_module", 
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dsl-execution-with-ttl.py")
)
dsl_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dsl_module)
OntologyBasedExecutionPlanner = dsl_module.OntologyBasedExecutionPlanner

from execution_engine import ExecutionEngine, ExecutionMonitor


def test_goal_1_query_failed_jobs():
    """Goal 1: query_failed_jobs_with_cooling 테스트"""
    print("\n" + "="*80)
    print("TEST 1: Query Failed Jobs with Cooling")
    print("="*80)
    
    dsl_input = {
        "goal": "query_failed_jobs_with_cooling",
        "date": "2025-07-17"
    }
    
    # 실행 계획 생성
    planner = OntologyBasedExecutionPlanner()
    execution_plan = planner.process_dsl(dsl_input)
    
    # 실행 엔진으로 실행
    engine = ExecutionEngine()
    report = engine.execute_plan(execution_plan)
    
    # 결과 검증
    print("\n📊 Test Result:")
    print(f"├─ Status: {report['status']}")
    print(f"├─ Duration: {report['totalDuration']}s")
    print(f"└─ Steps Executed: {report['stepsSummary']['total']}")
    
    return report


def test_goal_2_detect_anomaly():
    """Goal 2: detect_anomaly_for_product 테스트"""
    print("\n" + "="*80)
    print("TEST 2: Detect Anomaly for Product")
    print("="*80)
    
    dsl_input = {
        "goal": "detect_anomaly_for_product",
        "product_id": "Product-A1",
        "date_range": {
            "from": "2025-07-15",
            "to": "2025-07-17"
        },
        "target_machine": "CoolingMachine-01"
    }
    
    # 실행 계획 생성
    planner = OntologyBasedExecutionPlanner()
    execution_plan = planner.process_dsl(dsl_input)
    
    # 실행 엔진으로 실행
    engine = ExecutionEngine()
    report = engine.execute_plan(execution_plan)
    
    # 결과 검증
    print("\n📊 Test Result:")
    print(f"├─ Status: {report['status']}")
    print(f"├─ Duration: {report['totalDuration']}s")
    print(f"├─ Simulated Steps: {report['stepsSummary']['simulated']}")
    
    # 최종 결과 확인
    if "finalOutput" in report and "result" in report["finalOutput"]:
        result = report["finalOutput"]["result"]
        print(f"└─ Anomalies Detected: {len(result.get('anomalies', []))}")
        for anomaly in result.get('anomalies', []):
            print(f"   • {anomaly['type']} ({anomaly['severity']}) at {anomaly['timestamp']}")
    
    return report


def test_goal_3_predict_completion():
    """Goal 3: predict_first_completion_time 테스트"""
    print("\n" + "="*80)
    print("TEST 3: Predict First Completion Time")
    print("="*80)
    
    dsl_input = {
        "goal": "predict_first_completion_time",
        "product_id": "Product-B2",
        "quantity": 100
    }
    
    # 실행 계획 생성
    planner = OntologyBasedExecutionPlanner()
    execution_plan = planner.process_dsl(dsl_input)
    
    # 실행 엔진으로 실행
    engine = ExecutionEngine()
    report = engine.execute_plan(execution_plan)
    
    # 결과 검증
    print("\n📊 Test Result:")
    print(f"├─ Status: {report['status']}")
    print(f"├─ Duration: {report['totalDuration']}s")
    
    # 예측 결과 확인
    if "finalOutput" in report and "result" in report["finalOutput"]:
        result = report["finalOutput"]["result"]
        print(f"└─ Predicted Completion: {result.get('predicted_completion', 'N/A')}")
        if "bottlenecks" in result:
            print(f"   Bottlenecks: {', '.join([b['machine'] for b in result['bottlenecks']])}")
    
    return report


def test_goal_4_track_product():
    """Goal 4: track_product_position 테스트"""
    print("\n" + "="*80)
    print("TEST 4: Track Product Position")
    print("="*80)
    
    dsl_input = {
        "goal": "track_product_position",
        "product_id": "Product-C1"
    }
    
    # 실행 계획 생성
    planner = OntologyBasedExecutionPlanner()
    execution_plan = planner.process_dsl(dsl_input)
    
    # 실행 엔진으로 실행
    engine = ExecutionEngine()
    report = engine.execute_plan(execution_plan)
    
    # 결과 검증
    print("\n📊 Test Result:")
    print(f"├─ Status: {report['status']}")
    print(f"├─ Duration: {report['totalDuration']}s")
    print(f"└─ Steps Executed: {report['stepsSummary']['total']}")
    
    return report


def main():
    """메인 테스트 함수"""
    print("🧪 Execution Engine Test Suite")
    print("Testing all 4 goals with monitoring and external simulation")
    
    results = []
    
    # 모든 테스트 실행
    try:
        results.append(("Query Failed Jobs", test_goal_1_query_failed_jobs()))
        results.append(("Detect Anomaly", test_goal_2_detect_anomaly()))
        results.append(("Predict Completion", test_goal_3_predict_completion()))
        results.append(("Track Product", test_goal_4_track_product()))
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 전체 요약
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    for test_name, report in results:
        status_icon = "✅" if report['status'] == "COMPLETED" else "❌"
        print(f"{status_icon} {test_name}: {report['status']} ({report['totalDuration']}s)")
    
    # 최종 결과 파일 저장
    summary = {
        "test_date": datetime.now().isoformat(),
        "tests_run": len(results),
        "tests_passed": sum(1 for _, r in results if r['status'] == "COMPLETED"),
        "total_duration": sum(r['totalDuration'] for _, r in results),
        "test_results": [
            {
                "name": name,
                "status": report['status'],
                "duration": report['totalDuration'],
                "steps": report['stepsSummary']
            }
            for name, report in results
        ]
    }
    
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Test results saved to: test_results.json")


if __name__ == "__main__":
    main()