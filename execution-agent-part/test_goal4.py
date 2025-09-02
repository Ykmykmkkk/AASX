#!/usr/bin/env python3
"""
Goal 4 Test - Product Location Tracking
제품 ID를 입력받아 현재 위치와 추적 이력을 조회합니다.
"""
import requests
import json
import sys

def test_goal4(product_id="product-c"):
    print("=" * 60)
    print("🔍 Goal 4: Product Location Tracking Test")
    print("=" * 60)
    
    # Kubernetes 환경에서 실행 중인 API 서버 주소 (포트 포워딩: 8080 -> 80)
    url = "http://localhost:8080/execute-goal"
    
    # Goal 4 요청 데이터
    payload = {
        "goal": "track_product_position",
        "product_id": product_id
    }
    
    print(f"\n📤 Request:")
    print(json.dumps(payload, indent=2))
    print(f"\n🔗 API Endpoint: {url}")
    
    try:
        # API 요청 전송
        print("\n⏳ Sending request to API server...")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! Product tracking data retrieved.")
            print("\n📊 Full Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 결과 파싱 및 표시
            if "result" in result:
                tracking_data = result["result"]
                
                if isinstance(tracking_data, dict):
                    print("\n📍 Product Tracking Summary:")
                    print(f"  • Product ID: {tracking_data.get('product_id', 'N/A')}")
                    print(f"  • Current Location: {tracking_data.get('current_location', 'N/A')}")
                    print(f"  • Status: {tracking_data.get('status', 'N/A')}")
                    print(f"  • Last Update: {tracking_data.get('last_update', 'N/A')}")
                    
                    # 추적 이력 표시
                    history = tracking_data.get('tracking_history', [])
                    if history:
                        print(f"\n📜 Tracking History ({len(history)} entries):")
                        for i, entry in enumerate(history, 1):
                            print(f"  {i}. {entry.get('timestamp', 'N/A')} - {entry.get('location', 'N/A')} [{entry.get('status', 'N/A')}]")
                    
                    print("\n✅ Goal 4 test completed successfully!")
                else:
                    print(f"\n⚠️ Unexpected result format: {type(tracking_data)}")
                    print("Result:", tracking_data)
            
        elif response.status_code == 404:
            print("\n❌ 404 Not Found - Goal or product not found")
            print(f"Response: {response.json()}")
            
        elif response.status_code == 502:
            print("\n❌ 502 Bad Gateway - AAS Server communication failed")
            print(f"Response: {response.json()}")
            
        elif response.status_code == 500:
            print("\n❌ 500 Internal Server Error")
            print(f"Response: {response.json()}")
            
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n⏱️ Request timed out after 30 seconds")
        print("The API server might be processing or there could be a network issue.")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to API server")
        print("Please ensure:")
        print("  1. API server is running in Kubernetes")
        print("  2. Port forwarding is active: kubectl port-forward service/api-service 8080:80")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def main():
    # 명령줄 인자로 product_id 받기 (선택사항)
    if len(sys.argv) > 1:
        product_id = sys.argv[1]
        print(f"Using custom product ID: {product_id}")
    else:
        product_id = "product-c"
        print(f"Using default product ID: {product_id}")
    
    test_goal4(product_id)

if __name__ == "__main__":
    main()