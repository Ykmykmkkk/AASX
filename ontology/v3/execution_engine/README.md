# Execution Engine 테스트 가이드

## 개요
이 모듈은 DSL 실행 계획을 실제로 수행하는 Execution Engine을 포함합니다.
- SPARQL 쿼리 실행 (시뮬레이션)
- AAS 서버 통신 (시뮬레이션)
- 외부 AI/시뮬레이션 서비스 호출 (AWS Lambda/Batch 시뮬레이션)
- 각 단계별 입출력 모니터링

## 파일 구조
```
execution_engine/
├── execution_engine.py    # 실행 엔진 핵심 코드
├── test_execution.py      # 4개 Goal 테스트 스크립트
└── README.md             # 이 파일
```

## 설치 및 실행

### 1. 의존성 설치
```bash
# 상위 디렉토리(v2)에서 실행
pip install rdflib
```

### 2. 테스트 실행
```bash
cd /Users/jeongseunghwan/Desktop/aas-project/testing/v2/execution_engine
python3 test_execution.py
```

## 정상 작동 확인 사항

### 1. 초기 온톨로지 로드
```
📚 온톨로지 TTL 파일 로드 중...
✅ 실행 온톨로지 로드 성공: execution-ontology.ttl
✅ 도메인 온톨로지 로드 성공: domain-ontology.ttl
✅ 브리지 온톨로지 로드 성공: bridge-ontology.ttl
```

### 2. 각 Goal별 실행 결과

#### Goal 1: query_failed_jobs_with_cooling
- **정상 출력 예시:**
```
🚀 Executing: query_failed_jobs_with_cooling
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Step 1] BuildFailedJobsQuery
├─ Status: ✓ SUCCESS (0.5s)
└─ Output.query: SELECT ?job ?machine WHERE...

[Step 2] ExecuteJobQuery
├─ Status: ✓ SUCCESS (1.0s)
└─ Output.results: 15 items
```

#### Goal 2: detect_anomaly_for_product
- **정상 출력 예시:**
```
[Step 4] RunAnomalyDetection
├─ Status: ⏳ SIMULATED (AWS Lambda)
└─ Output.result: {
    "anomalies": [
      {"type": "temperature_spike", "severity": "high"},
      {"type": "vibration_pattern", "severity": "medium"}
    ]
  }
```
- **중요:** Step 4가 `SIMULATED` 상태로 표시되어야 함

#### Goal 3: predict_first_completion_time
- **정상 출력 예시:**
```
[Step 3] RunSimulation
├─ Status: ⏳ SIMULATED (AWS Batch)
└─ Output.result: {
    "predicted_completion": "2025-07-29T18:30:00",
    "bottlenecks": ["CoolingMachine-01", "HeatingMachine-03"]
  }
```

#### Goal 4: track_product_position
- **정상 출력 예시:**
```
✅ Execution Complete
├─ Steps: 3
└─ Results: 3 success, 0 simulated, 0 failed
```

### 3. 최종 요약
```
📋 TEST SUMMARY
════════════════════════════════════════════
✅ Query Failed Jobs: COMPLETED (2.5s)
✅ Detect Anomaly: COMPLETED (6.8s)
✅ Predict Completion: COMPLETED (5.2s)
✅ Track Product: COMPLETED (3.1s)

💾 Test results saved to: test_results.json
```

## 결과 파일 확인

### test_results.json
```json
{
  "test_date": "2025-07-28T...",
  "tests_run": 4,
  "tests_passed": 4,
  "total_duration": 17.6,
  "test_results": [...]
}
```

## 문제 해결

### 1. 온톨로지 로드 실패
- 원인: TTL 파일이 상위 디렉토리에 없음
- 해결: v2 디렉토리에 모든 TTL 파일이 있는지 확인

### 2. ModuleNotFoundError
- 원인: 상위 디렉토리 모듈을 찾지 못함
- 해결: execution_engine 디렉토리에서 실행

### 3. 외부 실행이 SIMULATED로 표시되지 않음
- 원인: 실행 엔진 버그
- 확인: Goal 2, 3의 마지막 단계가 SIMULATED 상태인지 확인

## 다음 단계

실제 시스템과 연동하려면:
1. AAS 서버 엔드포인트 설정
2. SPARQL 엔드포인트 설정
3. AWS 크레덴셜 설정
4. Docker 이미지 경로 설정

현재는 모든 외부 시스템이 시뮬레이션 모드로 동작합니다.