#!/usr/bin/env python3
"""
Goal 1 Test - Query Failed Jobs with Cooling Process
특정 날짜에 cooling 프로세스에서 실패한 Job을 조회합니다.
"""
import requests
import json
import sys
from datetime import datetime

def test_goal1(date=None):
    print("=" * 60)
    print("🧪 Goal 1: Query Failed Jobs with Cooling Process")
    print("=" * 60)
    
    # 날짜가 제공되지 않으면 기본값 사용
    if date is None:
        date = "2025-07-17"
    
    # Kubernetes 환경에서 실행 중인 API 서버 주소 (포트 포워딩: 8080 -> 80)
    url = "http://localhost:8080/execute-goal"
    
    # Goal 1 요청 데이터
    payload = {
        "goal": "query_failed_jobs_with_cooling",
        "date": date
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
            print("\n✅ SUCCESS! Failed jobs retrieved.")
            print("\n📊 Full Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 결과 파싱 및 표시
            if "result" in result:
                failed_jobs = result["result"]
                
                if isinstance(failed_jobs, list):
                    print(f"\n📋 Found {len(failed_jobs)} failed job(s) on {date}:")
                    
                    for i, job in enumerate(failed_jobs, 1):
                        print(f"\n  Job #{i}:")
                        print(f"    • Job ID: {job.get('job_id', 'N/A')}")
                        print(f"    • Date: {job.get('date', 'N/A')}")
                        print(f"    • Status: {job.get('status', 'N/A')}")
                        print(f"    • Process Steps: {', '.join(job.get('process_steps', []))}")
                        print(f"    • Failed At: {job.get('failed_at', 'N/A')}")
                    
                    # 검증: J-1002가 포함되어 있는지 확인
                    job_ids = [job.get('job_id') for job in failed_jobs]
                    if 'J-1002' in job_ids:
                        print("\n✅ Test PASSED: Found expected job J-1002")
                    else:
                        print("\n⚠️ Test WARNING: Expected job J-1002 not found")
                        print(f"   Found jobs: {job_ids}")
                        
                elif failed_jobs == []:
                    print(f"\n📭 No failed jobs found for date: {date}")
                else:
                    print(f"\n⚠️ Unexpected result format: {type(failed_jobs)}")
                    print("Result:", failed_jobs)
            
        elif response.status_code == 404:
            print("\n❌ 404 Not Found - Goal not found in ontology")
            print(f"Response: {response.json()}")
            
        elif response.status_code == 502:
            print("\n❌ 502 Bad Gateway - AAS Server communication failed")
            print(f"Response: {response.json()}")
            print("\nTroubleshooting tips:")
            print("  1. Check if AAS Mock server is running: kubectl get pods | grep aas-mock")
            print("  2. Check port forwarding: lsof -i :5001")
            
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
    # 명령줄 인자로 날짜 받기 (선택사항)
    if len(sys.argv) > 1:
        date = sys.argv[1]
        # 날짜 형식 검증
        try:
            datetime.strptime(date, "%Y-%m-%d")
            print(f"Using custom date: {date}")
        except ValueError:
            print(f"⚠️ Invalid date format: {date}")
            print("Using default date: 2025-07-17")
            date = "2025-07-17"
    else:
        date = "2025-07-17"
        print(f"Using default date: {date}")
    
    test_goal1(date)

if __name__ == "__main__":
    main()