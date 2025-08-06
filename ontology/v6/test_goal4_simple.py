#!/usr/bin/env python3
"""
Test Goal 4 (Simplified): Track Product Position
단순화된 제품 위치 추적 테스트
"""

import sys
import os
import json
sys.path.append('./src')

from data_collector_v2 import DataCollectorV2


def test_goal4_simple():
    """Goal 4 단순 테스트 - 현재 위치만 조회"""
    print("=" * 60)
    print("🎯 Goal 4 (Simplified): Track Product Current Position")
    print("=" * 60)
    
    collector = DataCollectorV2()
    
    # 테스트할 제품들
    test_products = ["Product-B1", "Product-C1", "Product-A1"]
    
    print("\n📍 Current Product Locations at T4:")
    print("-" * 40)
    
    for product_id in test_products:
        # 단순 위치 조회 (이력 없이)
        location = collector.collect_product_location(
            product_id, 
            include_history=False,  # 이력 제외
            timepoint="T4"
        )
        
        if location:
            current = location.get("current_location", {})
            
            # 핵심 정보만 출력
            print(f"\n{product_id}:")
            print(f"  Location: {current.get('CurrentLocation', current.get('Station', 'Unknown'))}")
            print(f"  Type: {current.get('LocationType', 'Unknown')}")
            print(f"  Status: {current.get('Status', 'Unknown')}")
    
    print("\n" + "=" * 60)
    print("✅ Goal 4 Simple Test Complete")
    print("=" * 60)


def verify_data_consistency():
    """데이터 일관성 검증"""
    print("\n🔍 Verifying Data Consistency...")
    print("-" * 40)
    
    collector = DataCollectorV2()
    
    # T4 시점의 작업 데이터와 비교
    jobs = collector.collect_from_snapshot("T4", "jobs")
    
    if jobs:
        print(f"\n작업 데이터와 위치 데이터 일치 확인:")
        for job in jobs:
            product_id = job.get("product_id")
            machine_id = job.get("machine_id")
            status = job.get("status")
            
            # 제품 위치 조회
            location = collector.collect_product_location(
                product_id,
                include_history=False,
                timepoint="T4"
            )
            
            if location:
                current = location.get("current_location", {})
                location_id = current.get("CurrentLocation", current.get("Station"))
                
                # 일치 여부 확인
                if status in ["RUNNING", "FAILED"]:
                    expected = machine_id
                elif status == "COMPLETED":
                    expected = "QC_Station"
                else:
                    expected = "Buffer_Area"
                
                match = "✅" if location_id == expected else "❌"
                print(f"  {product_id}: Job at {machine_id} ({status}) → Location: {location_id} {match}")
    
    print("\n일관성 검증 완료")


if __name__ == "__main__":
    print("🚀 Starting Goal 4 Simplified Test")
    print("=" * 60)
    
    # 메인 테스트
    test_goal4_simple()
    
    # 데이터 일관성 검증
    verify_data_consistency()
    
    print("\n✨ Test completed!")