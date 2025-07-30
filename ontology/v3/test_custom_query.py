#!/usr/bin/env python3
"""
사용자 정의 쿼리 테스트 스크립트
다양한 날짜와 제품으로 테스트 가능
"""

import sys
sys.path.append('.')
from dsl_execution_with_sparql import OntologyBasedExecutionPlannerWithSPARQL
import json
import sys

def test_goal1_custom(planner, date="2025-07-17"):
    """Goal 1: 특정 날짜의 냉각 실패 작업 조회"""
    print(f"\n🔍 Goal 1: {date} 날짜의 냉각 실패 작업 조회")
    
    dsl_input = {
        "goal": "query_failed_jobs_with_cooling",
        "date": date
    }
    
    result = planner.process_dsl(dsl_input)
    
    if 'sparql_results' in result and 'BuildJobQuery' in result['sparql_results']:
        query_result = result['sparql_results']['BuildJobQuery']
        print(f"✅ 결과: {query_result['count']}개 작업 발견")
        for i, job in enumerate(query_result['results'], 1):
            print(f"  {i}. {job.get('job')} | {job.get('machine')} | {job.get('startTime')}")
    
    return result

def test_goal2_custom(planner, product_id="Product-A1", date_start="2025-07-17T00:00:00", date_end="2025-07-17T23:59:59"):
    """Goal 2: 특정 제품의 이상 감지"""
    print(f"\n🔍 Goal 2: {product_id}의 이상 감지 ({date_start} ~ {date_end})")
    
    dsl_input = {
        "goal": "detect_anomaly_for_product",
        "product_id": product_id,
        "date_range": {
            "start": date_start,
            "end": date_end
        },
        "target_machine": "CoolingMachine-01"
    }
    
    result = planner.process_dsl(dsl_input)
    
    if 'sparql_results' in result and 'BuildProductTraceQuery' in result['sparql_results']:
        query_result = result['sparql_results']['BuildProductTraceQuery']
        print(f"✅ 결과: {query_result['count']}개 작업 발견")
        for i, job in enumerate(query_result['results'], 1):
            print(f"  {i}. {job.get('job')} | {job.get('status')} | {job.get('startTime')}")
    
    return result

def test_goal3_custom(planner, product_id="Product-D1", quantity=50):
    """Goal 3: 특정 제품의 완료 시간 예측"""
    print(f"\n🔍 Goal 3: {product_id}의 완료 시간 예측 (수량: {quantity})")
    
    dsl_input = {
        "goal": "predict_first_completion_time",
        "product_id": product_id,
        "quantity": quantity
    }
    
    result = planner.process_dsl(dsl_input)
    
    if 'sparql_results' in result and 'BuildJobTemplateQuery' in result['sparql_results']:
        query_result = result['sparql_results']['BuildJobTemplateQuery']
        print(f"✅ 결과: {query_result['count']}개 작업 단계 발견")
        total_duration = 0
        for i, op in enumerate(query_result['results'], 1):
            duration = int(op.get('duration', 0))
            total_duration += duration
            print(f"  {i}. {op.get('operation')} | {op.get('machine')} | {duration}분")
        if query_result['count'] > 0:
            print(f"📊 총 예상 시간: {total_duration}분")
    
    return result

def test_goal4_custom(planner, product_id="Product-C1"):
    """Goal 4: 특정 제품의 위치 추적"""
    print(f"\n🔍 Goal 4: {product_id}의 현재 위치 추적")
    
    dsl_input = {
        "goal": "track_product_position",
        "product_id": product_id
    }
    
    result = planner.process_dsl(dsl_input)
    
    if 'sparql_results' in result and 'BuildProductLocationQuery' in result['sparql_results']:
        query_result = result['sparql_results']['BuildProductLocationQuery']
        print(f"✅ 결과: {query_result['count']}개 작업 발견")
        for i, job in enumerate(query_result['results'], 1):
            print(f"  {i}. {job.get('job')} | {job.get('machine')} | 작업 단계: {job.get('opIndex', 'N/A')}")
    
    return result

def main():
    # 플래너 초기화
    planner = OntologyBasedExecutionPlannerWithSPARQL()
    
    print("="*80)
    print("🧪 사용자 정의 쿼리 테스트")
    print("="*80)
    
    # 다양한 테스트 시나리오
    print("\n### 시나리오 1: 2025-07-17 날짜 테스트 ###")
    test_goal1_custom(planner, "2025-07-17")
    
    print("\n### 시나리오 2: 2025-07-18 날짜 테스트 ###")
    test_goal1_custom(planner, "2025-07-18")
    
    print("\n### 시나리오 3: Product-A2 이상 감지 (07-18) ###")
    test_goal2_custom(planner, "Product-A2", "2025-07-18T00:00:00", "2025-07-18T23:59:59")
    
    print("\n### 시나리오 4: Product-D1 완료 시간 예측 ###")
    test_goal3_custom(planner, "Product-D1", 50)
    
    print("\n### 시나리오 5: Product-D1 위치 추적 ###")
    test_goal4_custom(planner, "Product-D1")
    
    print("\n" + "="*80)
    print("✅ 모든 테스트 완료")
    print("="*80)

if __name__ == "__main__":
    main()