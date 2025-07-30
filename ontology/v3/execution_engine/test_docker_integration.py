#!/usr/bin/env python3
"""
Docker 통합 테스트
간단한 Job 처리를 Docker 컨테이너로 실행
"""

import os
import sys
import json
from docker_executor import DockerExecutor

def test_docker_executor():
    """Docker Executor 테스트"""
    print("=== Docker Executor Test ===")
    
    # Docker Executor 초기화
    executor = DockerExecutor()
    
    # Jobs 데이터 준비
    jobs_data = [
        {
            "id": "Job-101",
            "product_id": "Product-A1",
            "status": "Completed",
            "requiresCooling": True,
            "requiresHeating": True,
            "executedOn": ["CoolingMachine-01", "HeatingMachine-01"]
        },
        {
            "id": "Job-102",
            "product_id": "Product-B2",
            "status": "Failed",
            "requiresCooling": True,
            "requiresHeating": False,
            "executedOn": ["CoolingMachine-02"]
        },
        {
            "id": "Job-103",
            "product_id": "Product-A1",
            "status": "Completed",
            "requiresCooling": False,
            "requiresHeating": True,
            "executedOn": ["HeatingMachine-03"]
        }
    ]
    
    # 입력 데이터
    input_data = {
        "jobs": jobs_data,
        "request_id": "test-001",
        "timestamp": "2025-07-28T10:00:00"
    }
    
    # Jobs 파일 경로
    jobs_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs.json")
    
    print("\n1. Testing with job-processor container...")
    print(f"   Input: {len(jobs_data)} jobs")
    
    # Docker 컨테이너 실행
    result = executor.execute_container(
        image_name="job-processor:latest",
        input_data=input_data,
        input_files={"jobs.json": jobs_file_path}
    )
    
    # 결과 출력
    print("\n2. Execution Result:")
    print(json.dumps(result, indent=2))
    
    # 결과 검증
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        if "suggestion" in result:
            print(f"   Suggestion: {result['suggestion']}")
    else:
        print(f"\n✅ Success!")
        print(f"   Service: {result.get('service', 'Unknown')}")
        print(f"   Total Jobs: {result.get('total_jobs', 0)}")
        print(f"   Processed: {result.get('processed_jobs', 0)}")
        
        # 통계 출력
        if "statistics" in result:
            stats = result["statistics"]
            print(f"\n   Statistics:")
            print(f"   - Failed: {stats.get('failed_count', 0)}")
            print(f"   - Completed: {stats.get('completed_count', 0)}")
            print(f"   - Cooling Required: {stats.get('cooling_required', 0)}")
            print(f"   - Heating Required: {stats.get('heating_required', 0)}")
    
    # 시뮬레이션 모드 테스트
    print("\n3. Testing simulation mode...")
    sim_result = executor.simulate_docker_execution("job-processor", input_data)
    print(f"   Mode: {sim_result.get('mode', 'Unknown')}")
    print(f"   Service: {sim_result.get('service', 'Unknown')}")

def main():
    """메인 함수"""
    print("Docker Integration Test")
    print("=" * 50)
    
    # Docker 이미지 존재 여부 안내
    print("\nNote: Make sure to build the Docker image first:")
    print("  cd ../docker-services/job-processor")
    print("  ./build.sh")
    print("")
    
    try:
        test_docker_executor()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())