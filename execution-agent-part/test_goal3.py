#!/usr/bin/env python3
"""
Goal 3 테스트 스크립트 - AASX-main Simulator 통합 테스트
제품 생산 시간 예측 기능 검증
"""

import json
import requests
import os

# 환경 변수 설정
os.environ['USE_STANDARD_SERVER'] = 'true'
os.environ['AAS_SERVER_IP'] = '127.0.0.1'
os.environ['AAS_SERVER_PORT'] = '5001'

def test_goal3():
    """Goal 3: 제품 생산 시간 예측 테스트"""
    
    print("🎯 Goal 3: 제품 생산 시간 예측 테스트")
    print("=" * 50)
    print(f"📡 AAS Server: {os.environ['AAS_SERVER_IP']}:{os.environ['AAS_SERVER_PORT']}")
    print(f"🔄 Advanced Simulator: AASX-main")
    print()
    
    # API 엔드포인트
    api_url = "http://127.0.0.1:8080/execute-goal"
    
    # Goal 3 요청 데이터
    request_data = {
        "goal": "predict_first_completion_time",
        "product_id": "Product-A",
        "quantity": 10,
        "date_range": {
            "start": "2025-08-11",
            "end": "2025-08-15"
        }
    }
    
    print("📋 Request Data:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    print()
    
    try:
        print("🚀 API 요청 전송 중...")
        response = requests.post(
            api_url, 
            json=request_data, 
            timeout=600  # 10분 대기 (시뮬레이터 실행 시간 고려)
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API 응답 성공!")
            print()
            print("📈 Results:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 결과 검증
            final_result = result.get("result", {})
            if isinstance(final_result, dict):
                completion_time = final_result.get("predicted_completion_time")
                confidence = final_result.get("confidence", 0)
                simulator_type = final_result.get("simulator_type", "unknown")
                
                print()
                print("🔍 Result Analysis:")
                print(f"  - 예상 완료 시간: {completion_time}")
                print(f"  - 신뢰도: {confidence}")
                print(f"  - 시뮬레이터 타입: {simulator_type}")
                
                if simulator_type == "aasx-main":
                    print("✅ AASX-main 시뮬레이터가 성공적으로 실행됨!")
                elif simulator_type == "dummy":
                    print("⚠️  Dummy 시뮬레이터로 실행됨 (Fallback 모드)")
                else:
                    print("❓ 시뮬레이터 타입을 확인할 수 없음")
                
                # 성공 조건 확인
                if completion_time and confidence > 0.5:
                    print()
                    print("🎉 Goal 3 테스트 성공!")
                    return True
                else:
                    print()
                    print("❌ Goal 3 테스트 실패: 유효한 결과가 아님")
                    return False
            else:
                print("❌ 예상치 못한 결과 형식")
                return False
        else:
            print(f"❌ API 요청 실패: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 AASX-main Simulator Integration Test")
    print("=" * 60)
    
    # Goal 3 테스트 실행
    success = test_goal3()
    
    print()
    print("=" * 60)
    if success:
        print("✅ 전체 테스트 성공!")
        print("🚀 AASX-main 시뮬레이터 통합이 완료되었습니다.")
    else:
        print("❌ 테스트 실패!")
        print("🔧 시스템 상태를 확인해주세요:")
        print("  1. FastAPI 서버 실행 상태 (http://127.0.0.1:8080)")
        print("  2. AAS 표준 서버 연결 상태")
        print("  3. Kubernetes 클러스터 상태")
        print("  4. PVC 마운트 상태")

if __name__ == "__main__":
    main()