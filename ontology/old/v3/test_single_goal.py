#!/usr/bin/env python3
"""
단일 목표 테스트용 스크립트
"""

from dsl_execution_with_sparql import OntologyBasedExecutionPlannerWithSPARQL
import json

# 플래너 초기화
planner = OntologyBasedExecutionPlannerWithSPARQL()

# 테스트할 목표 선택 (1~4 중 선택)
goal_number = 1  # 이 숫자를 변경하여 다른 목표 테스트

test_inputs = {
    1: {
        "name": "Goal 1: 냉각이 필요한 실패한 작업 조회",
        "input": {
            "goal": "query_failed_jobs_with_cooling",
            "date": "2025-07-17"
        }
    },
    2: {
        "name": "Goal 2: 제품 이상 감지",
        "input": {
            "goal": "detect_anomaly_for_product",
            "product_id": "Product-A1",
            "date_range": {
                "start": "2025-07-17T00:00:00",
                "end": "2025-07-17T23:59:59"
            },
            "target_machine": "CoolingMachine-01"
        }
    },
    3: {
        "name": "Goal 3: 첫 완료 시간 예측",
        "input": {
            "goal": "predict_first_completion_time",
            "product_id": "Product-B2",
            "quantity": 100
        }
    },
    4: {
        "name": "Goal 4: 제품 위치 추적",
        "input": {
            "goal": "track_product_position",
            "product_id": "Product-C1"
        }
    }
}

# 선택한 목표 실행
test = test_inputs[goal_number]
print(f"\n{'='*80}")
print(f"🧪 테스트: {test['name']}")
print(f"{'='*80}")

# DSL 처리
result = planner.process_dsl(test["input"])

# 결과 저장
output_file = f"test_result_{test['input']['goal']}.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\n💾 결과 저장: {output_file}")

# SPARQL 결과 요약 출력
if 'sparql_results' in result:
    print("\n📊 SPARQL 쿼리 결과 요약:")
    for action, query_result in result['sparql_results'].items():
        print(f"\n{action}:")
        print(f"  - 결과 개수: {query_result['count']}개")
        if query_result['count'] > 0:
            print("  - 결과 샘플:")
            for i, row in enumerate(query_result['results'][:3], 1):  # 최대 3개만 표시
                print(f"    {i}. ", end="")
                values = [f"{k}: {v}" for k, v in row.items() if v is not None]
                print(" | ".join(values))