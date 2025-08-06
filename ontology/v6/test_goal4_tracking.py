#!/usr/bin/env python3
"""
Test Goal 4: Track Product Position
제품 위치 추적 테스트
"""

import sys
import os
import json
import time
sys.path.append('./src')

from data_collector_v2 import DataCollectorV2
from aas_client import AASClient


def test_goal4_with_server():
    """Goal 4 테스트 - AAS Server 사용"""
    print("=" * 60)
    print("🎯 Goal 4: Track Product Position")
    print("=" * 60)
    
    # AAS Client 초기화
    client = AASClient()
    
    # 서버 상태 확인
    if not client.health_check():
        print("❌ AAS Server is not running")
        print("   Please start the server with:")
        print("   python3 start_server.py")
        return False
    
    print("✅ AAS Server is running")
    
    # DataCollector 초기화
    collector = DataCollectorV2()
    
    print("\n" + "-" * 40)
    print("📍 Test 1: Single Product Tracking")
    print("-" * 40)
    
    # 1. 특정 제품 위치 조회 (이력 포함)
    product_id = "Product-B1"
    print(f"\n📦 Tracking {product_id}...")
    
    location = collector.collect_product_location(
        product_id, 
        include_history=True,
        timepoint="T4"
    )
    
    if location:
        current = location.get("current_location", {})
        print(f"\n🔍 Current Location (T4):")
        print(f"   Zone: {current.get('Zone')}")
        print(f"   Station: {current.get('Station')}")
        print(f"   Status: {current.get('Status')}")
        print(f"   Job ID: {current.get('JobId')}")
        print(f"   Progress: {current.get('Progress')}%")
        print(f"   RFID: {current.get('RFID')}")
        print(f"   Coordinates: {current.get('Coordinates')}")
        
        # 이력 출력
        if "history" in location:
            print(f"\n📜 Location History:")
            for hist in location["history"]:
                tp = hist["timepoint"]
                loc = hist["location"]
                print(f"\n   {tp}:")
                print(f"     Zone: {loc.get('Zone')}")
                print(f"     Station: {loc.get('Station')}")
                print(f"     Status: {loc.get('Status')}")
                print(f"     Progress: {loc.get('Progress')}%")
    else:
        print(f"❌ Failed to get location for {product_id}")
    
    print("\n" + "-" * 40)
    print("📍 Test 2: All Products Tracking")
    print("-" * 40)
    
    # 2. 모든 제품 위치 조회
    print("\n🌍 Getting all product locations at T4...")
    
    all_tracking = collector.collect_all_product_tracking("T4")
    
    if all_tracking:
        print(f"\n📊 Tracking {len(all_tracking)} products:")
        
        # 상태별 그룹화
        status_groups = {}
        for track in all_tracking:
            status = track.get("Status", "UNKNOWN")
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(track)
        
        # 상태별 출력
        for status, products in status_groups.items():
            print(f"\n   {status} ({len(products)} products):")
            for product in products:
                print(f"     - {product.get('product_id')}: {product.get('Zone')} / {product.get('Station')}")
    else:
        print("❌ Failed to get all product tracking")
    
    print("\n" + "-" * 40)
    print("📍 Test 3: Tracking at Different Timepoints")
    print("-" * 40)
    
    # 3. 다른 시점에서의 위치 조회
    product_id = "Product-C1"
    print(f"\n⏰ Tracking {product_id} across timepoints...")
    
    for timepoint in ["T1", "T2", "T3", "T4", "T5"]:
        location = collector.collect_product_location(
            product_id,
            include_history=False,
            timepoint=timepoint
        )
        
        if location:
            current = location.get("current_location", {})
            print(f"\n   {timepoint}: {current.get('Zone')} / {current.get('Station')} ({current.get('Status')})")
    
    print("\n" + "-" * 40)
    print("📍 Test 4: Movement Pattern Analysis")
    print("-" * 40)
    
    # 4. 이동 패턴 분석
    product_id = "Product-B1"
    print(f"\n🔄 Analyzing movement pattern for {product_id}...")
    
    location = collector.collect_product_location(
        product_id,
        include_history=True,
        timepoint="T4"
    )
    
    if location and "history" in location:
        history = location["history"]
        
        # 이동 경로 추출
        movement_path = []
        for i, hist in enumerate(history):
            tp = hist["timepoint"]
            loc = hist["location"]
            station = loc.get("Station")
            status = loc.get("Status")
            
            if i > 0:
                prev_station = history[i-1]["location"].get("Station")
                if station != prev_station:
                    movement_path.append(f"{tp}: {prev_station} → {station}")
            
            # 상태 변화 감지
            if i > 0:
                prev_status = history[i-1]["location"].get("Status")
                if status != prev_status:
                    print(f"   Status change at {tp}: {prev_status} → {status}")
        
        if movement_path:
            print(f"\n   Movement Path:")
            for move in movement_path:
                print(f"     {move}")
    
    print("\n" + "=" * 60)
    print("✅ Goal 4 Test Complete")
    print("=" * 60)
    
    return True


def test_goal4_fallback():
    """Goal 4 테스트 - Fallback 모드 (서버 없이)"""
    print("\n" + "=" * 60)
    print("🎯 Goal 4: Track Product Position (Fallback Mode)")
    print("=" * 60)
    
    collector = DataCollectorV2()
    
    print("\n⚠️ Running in fallback mode (local snapshots)")
    
    # Fallback 모드에서도 동일한 테스트
    product_id = "Product-B1"
    print(f"\n📦 Tracking {product_id} (from snapshots)...")
    
    location = collector.collect_product_location(
        product_id,
        include_history=True,
        timepoint="T4"
    )
    
    if location:
        current = location.get("current_location", {})
        print(f"\n🔍 Current Location (T4):")
        print(f"   Zone: {current.get('Zone')}")
        print(f"   Station: {current.get('Station')}")
        print(f"   Status: {current.get('Status')}")
        
        if "history" in location:
            print(f"\n📜 History: {len(location['history'])} timepoints found")
    
    return True


def analyze_results():
    """결과 분석 및 요약"""
    print("\n" + "=" * 60)
    print("📊 Goal 4 Analysis Summary")
    print("=" * 60)
    
    collector = DataCollectorV2()
    
    # T4 시점의 전체 상황 분석
    all_tracking = collector.collect_all_product_tracking("T4")
    
    if all_tracking:
        # 통계 계산
        total_products = len(all_tracking)
        status_counts = {}
        zone_counts = {}
        
        for track in all_tracking:
            # 상태별 카운트
            status = track.get("Status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 구역별 카운트
            zone = track.get("Zone", "Unknown")
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        
        print(f"\n📈 Statistics at T4:")
        print(f"   Total Products: {total_products}")
        
        print(f"\n   By Status:")
        for status, count in status_counts.items():
            percentage = (count / total_products) * 100
            print(f"     {status}: {count} ({percentage:.1f}%)")
        
        print(f"\n   By Zone:")
        for zone, count in zone_counts.items():
            percentage = (count / total_products) * 100
            print(f"     {zone}: {count} ({percentage:.1f}%)")
        
        # 실패 제품 특별 분석
        failed_products = [t for t in all_tracking if t.get("Status") == "ERROR"]
        if failed_products:
            print(f"\n⚠️ Failed Products ({len(failed_products)}):")
            for product in failed_products:
                print(f"   - {product.get('product_id')}: {product.get('Station')}")


if __name__ == "__main__":
    # 메인 실행
    print("🚀 Starting Goal 4 Test")
    print("=" * 60)
    
    # AAS Server 테스트
    server_success = test_goal4_with_server()
    
    if not server_success:
        # Fallback 모드 테스트
        test_goal4_fallback()
    
    # 결과 분석
    analyze_results()
    
    print("\n✨ All tests completed!")