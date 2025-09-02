# 🏭 Smart Factory Automation - Complete Setup & Testing Guide

이 가이드는 Smart Factory Automation 시스템을 처음부터 완전히 구축하고 테스트하는 방법을 단계별로 안내합니다.

## 🚀 빠른 시작 (Quick Start)

이미 Docker Desktop과 Kubernetes가 설치되어 있다면:

```bash
# 1. 프로젝트 클론
cd ~/Desktop/aas-project/gemini-ver/factory-automation-k8s

# 2. Docker 이미지 빌드
docker build -f api.Dockerfile -t api-server:latest .
docker build -f aasx_simple.Dockerfile -t aasx-simple:latest .

# 3. Kubernetes 배포
kubectl apply -f k8s/

# 4. 포트 포워딩 (기존 프로세스 종료 후)
lsof -ti :8080 | xargs kill -9 2>/dev/null || echo "8080 포트 사용 중인 프로세스 없음"
kubectl port-forward service/api-service 8080:80 &

# 5. Goal 테스트
python test_goal1.py  # Goal 1: 실패한 Job 조회
python test_goal3_simple.py  # Goal 3: 생산 시간 예측
python test_goal4.py  # Goal 4: 제품 추적
```

## 📋 목차

1. [사전 준비 사항](#1-사전-준비-사항)
2. [프로젝트 구조 이해](#2-프로젝트-구조-이해)
3. [환경 설정](#3-환경-설정)
4. [Docker 이미지 빌드](#4-docker-이미지-빌드)
5. [Kubernetes 배포](#5-kubernetes-배포)
6. [Goal 1 테스트: 실패한 냉각 Job 조회](#6-goal-1-테스트-실패한-냉각-job-조회)
7. [Goal 3 테스트: 생산 시간 예측](#7-goal-3-테스트-생산-시간-예측)
8. [Goal 4 테스트: 제품 위치 추적](#8-goal-4-테스트-제품-위치-추적)
9. [모니터링 및 디버깅](#9-모니터링-및-디버깅)
10. [문제 해결 가이드](#10-문제-해결-가이드)

---

## 1. 사전 준비 사항

### 필수 소프트웨어 설치

#### Docker Desktop (Kubernetes 포함)
```bash
# macOS (Homebrew 사용)
brew install --cask docker

# Docker Desktop 실행 후 Settings > Kubernetes > Enable Kubernetes 체크
```

#### Python 3.8+
```bash
# macOS
brew install python@3.8

# 버전 확인
python3 --version
```

#### kubectl
```bash
# macOS
brew install kubectl

# 버전 확인
kubectl version --client
```

#### Git
```bash
# macOS
brew install git
```

### 시스템 요구사항
- RAM: 최소 8GB (16GB 권장)
- 디스크 공간: 최소 10GB
- Docker Desktop에 최소 4GB RAM 할당

---

## 2. 프로젝트 구조 이해

### 주요 디렉토리 구조
```
factory-automation-k8s/
├── api/                       # FastAPI 메인 서버
│   ├── main.py               # API 엔드포인트
│   └── schemas.py            # 데이터 모델 정의
├── execution_engine/          # 실행 엔진
│   ├── planner.py            # 온톨로지 기반 계획 수립
│   └── agent.py              # 액션 실행 에이전트
├── k8s/                      # Kubernetes 매니페스트 파일
│   ├── 00-rbac.yaml         # RBAC 설정
│   ├── 01-pvc.yaml          # PersistentVolumeClaim
│   └── 02-api-server.yaml   # API 서버 배포
├── AASX-main/                # AASX 시뮬레이터
│   └── simulatePlant_AASX_v3.py  # 시뮬레이터 코드
├── ontology/                 # 온톨로지 파일
│   └── factory_ontology_v2.ttl  # RDF/Turtle 온톨로지
├── simulation_data_converter.py  # AAS → AASX 변환기
├── config.py                 # 설정 파일
└── test_goal*.py            # 테스트 스크립트들
```

### 핵심 컴포넌트

1. **API Server (포트 8000)**
   - FastAPI 기반 REST API
   - DSL 요청을 온톨로지 기반 실행 계획으로 변환
   - Kubernetes Job 동적 생성
   - 외부 AAS 서버(localhost:5001)에 접근

2. **AASX Simulator**
   - Docker 컨테이너로 실행
   - JSON 형식 입력 데이터 처리
   - 생산 시간 예측 시뮬레이션

---

## 3. 환경 설정

### 3.1 프로젝트 클론
```bash
# 프로젝트 디렉토리 생성
mkdir -p ~/Desktop/aas-project/gemini-ver
cd ~/Desktop/aas-project/gemini-ver

# Git 클론 (실제 리포지토리 URL로 변경)
git clone <repository-url> factory-automation-k8s
cd factory-automation-k8s
```

### 3.2 Python 가상환경 설정
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 3.3 설정 파일 확인
```bash
# config.py 확인
cat config.py
```

`config.py` 파일 내용:
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# AAS 서버 설정
USE_STANDARD_SERVER = os.environ.get('USE_STANDARD_SERVER', 'true').lower() == 'true'
AAS_SERVER_IP = os.environ.get('AAS_SERVER_IP', '127.0.0.1')
AAS_SERVER_PORT = os.environ.get('AAS_SERVER_PORT', '5001')

# 파일 경로
ONTOLOGY_FILE_PATH = BASE_DIR / "ontology" / "factory_ontology_v2.ttl"
AAS_DATA_FILE_PATH = BASE_DIR / "aas_mock_server" / "data" / "aas_model_v2.json"
```

---

## 4. Docker 이미지 빌드

### 4.1 API Server 이미지 빌드
```bash
# api.Dockerfile 작성 확인
cat api.Dockerfile

# 이미지 빌드
docker build -f api.Dockerfile -t api-server:latest .

# 빌드 확인
docker images | grep api-server
```


### 4.2 AASX Simulator 이미지 빌드
```bash
# aasx_simple.Dockerfile 작성 확인
cat aasx_simple.Dockerfile

# 이미지 빌드
docker build -f aasx_simple.Dockerfile -t aasx-simple:latest .

# 빌드 확인
docker images | grep aasx-simple
```

---

## 5. Kubernetes 배포

### 5.1 Kubernetes 클러스터 확인
```bash
# Docker Desktop Kubernetes가 실행 중인지 확인
kubectl cluster-info

# 노드 확인
kubectl get nodes
```

### 5.2 네임스페이스 생성 (선택사항)
```bash
# factory 네임스페이스 생성
kubectl create namespace factory

# 기본 네임스페이스로 설정
kubectl config set-context --current --namespace=factory
```

### 5.3 Kubernetes 리소스 배포
```bash
# 1. RBAC 설정 (API 서버가 Job을 생성할 권한)
kubectl apply -f k8s/00-rbac.yaml

# 2. PersistentVolumeClaim 생성 (데이터 공유용)
kubectl apply -f k8s/01-pvc.yaml

# 3. API 서버 배포
kubectl apply -f k8s/02-api-server.yaml

# 배포 상태 확인
kubectl get all
```

### 5.4 서비스 포트 포워딩
```bash
# 기존 8080 포트 사용 프로세스 종료 (필요시)
lsof -ti :8080 | xargs kill -9 2>/dev/null || echo "8080 포트 사용 중인 프로세스 없음"

# API 서버 포트 포워딩 (8080 → 80)
kubectl port-forward service/api-service 8080:80 &

# 포트 포워딩 확인
lsof -i :8080
```

---

## 6. Goal 1 테스트: 실패한 냉각 Job 조회

### 6.1 테스트 개요
Goal 1은 특정 날짜에 cooling 프로세스에서 실패한 Job을 조회합니다.

### 6.2 테스트 실행

#### 방법 1: curl 사용
```bash
curl -X POST "http://localhost:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "query_failed_jobs_with_cooling",
    "date": "2025-07-17"
  }'
```

#### 방법 2: Python 스크립트 사용
```python
# test_goal1.py 실행
python test_goal1.py
```

### 6.3 예상 결과
```json
{
  "goal": "query_failed_jobs_with_cooling",
  "params": {
    "goal": "query_failed_jobs_with_cooling",
    "date": "2025-07-17"
  },
  "result": [
    {
      "job_id": "J-1002",
      "date": "2025-07-17",
      "status": "FAILED",
      "process_steps": ["cutting", "cooling", "assembly"],
      "failed_at": "cooling"
    }
  ]
}
```

---

## 7. Goal 3 테스트: 생산 시간 예측

### 7.1 테스트 개요
Goal 3는 제품 ID와 수량을 입력받아 생산 완료 시간을 예측합니다.
이 과정에서 Kubernetes Job이 동적으로 생성되고 시뮬레이션이 실행됩니다.

### 7.2 테스트 실행

#### 방법 1: curl 사용
```bash
curl -X POST "http://localhost:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "predict_first_completion_time",
    "product_id": "P1",
    "quantity": 100
  }'
```

#### 방법 2: Python 스크립트 사용
```bash
# 간단한 테스트
python test_goal3_simple.py

# 상세한 디버그 정보 포함
python test_goal3_debug.py
```

### 7.3 실행 과정 모니터링
```bash
# 생성된 Job 확인
kubectl get jobs -w

# Job 로그 확인 (Job 이름은 aasx-simulator-{uuid} 형식)
kubectl logs job/aasx-simulator-xxxxx

# Pod 상태 확인
kubectl get pods | grep aasx-simulator
```

### 7.4 예상 결과
```json
{
  "goal": "predict_first_completion_time",
  "params": {
    "goal": "predict_first_completion_time",
    "product_id": "P1",
    "quantity": 100
  },
  "result": {
    "predicted_completion_time": 450.0,
    "confidence": 0.85,
    "simulator_type": "AASX Plant Simulator v3",
    "simulation_details": {
      "total_products": 100,
      "completion_time": 450.0,
      "average_time_per_product": 4.5
    }
  }
}
```

---

## 8. Goal 4 테스트: 제품 위치 추적

### 8.1 테스트 개요
Goal 4는 특정 제품 ID의 현재 위치와 상태를 추적합니다.

### 8.2 테스트 실행

#### 방법 1: curl 사용
```bash
curl -X POST "http://localhost:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "track_product_location",
    "product_id": "P-12345"
  }'
```

#### 방법 2: Python 스크립트 작성
```python
# test_goal4.py 생성
cat > test_goal4.py << 'EOF'
#!/usr/bin/env python3
import requests
import json

def test_goal4():
    print("=" * 60)
    print("🔍 Goal 4: Product Location Tracking Test")
    print("=" * 60)
    
    url = "http://localhost:8080/execute-goal"
    payload = {
        "goal": "track_product_location",
        "product_id": "P-12345"
    }
    
    print(f"\n📤 Request:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ Error: {response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_goal4()
EOF

# 실행
python test_goal4.py
```

### 8.3 예상 결과
```json
{
  "goal": "track_product_location",
  "params": {
    "goal": "track_product_location",
    "product_id": "P-12345"
  },
  "result": {
    "product_id": "P-12345",
    "current_location": "Assembly Station 2",
    "status": "IN_PROGRESS",
    "last_update": "2025-07-17T14:30:00Z",
    "tracking_history": [
      {
        "timestamp": "2025-07-17T10:00:00Z",
        "location": "Raw Material Storage",
        "status": "STARTED"
      },
      {
        "timestamp": "2025-07-17T12:00:00Z",
        "location": "Cutting Station",
        "status": "PROCESSING"
      },
      {
        "timestamp": "2025-07-17T14:30:00Z",
        "location": "Assembly Station 2",
        "status": "IN_PROGRESS"
      }
    ]
  }
}
```

---

## 9. 모니터링 및 디버깅

### 9.1 Kubernetes 리소스 모니터링
```bash
# 전체 리소스 상태
kubectl get all

# Pod 상태 실시간 모니터링
kubectl get pods -w

# 특정 Pod 로그 확인
kubectl logs -f deployment/api-deployment
kubectl logs -f deployment/aas-mock-deployment

# Pod 상세 정보
kubectl describe pod <pod-name>
```

### 9.2 서비스 헬스 체크
```bash
# API 서버 헬스 체크
curl http://localhost:8080/health

# 외부 AAS 서버 테스트 (localhost:5001에 실제 AAS 서비스가 실행 중이어야 함)
curl http://localhost:5001/health
```

### 9.3 Job 모니터링 (Goal 3)
```bash
# Job 목록
kubectl get jobs

# Job 상세 정보
kubectl describe job aasx-simulator-xxxxx

# Job Pod 로그
kubectl logs job/aasx-simulator-xxxxx

# 완료된 Job 삭제
kubectl delete job aasx-simulator-xxxxx
```

### 9.4 PVC 확인
```bash
# PVC 상태
kubectl get pvc

# PVC 상세 정보
kubectl describe pvc factory-shared-pvc

# PVC에 마운트된 데이터 확인 (디버그 Pod 사용)
kubectl run debug --rm -i --tty --image=busybox --restart=Never -- sh
# Pod 내부에서
ls -la /data
cat /data/simulation_input.json
exit
```

---

## 10. 문제 해결 가이드

### 10.1 일반적인 문제들

#### 문제: API 서버가 AAS 서버에 연결할 수 없음
```bash
# 해결 방법
# 1. API 서버 Pod 상태 확인
kubectl get pods | grep api

# 2. 서비스 확인
kubectl get svc api-service

# 3. 외부 AAS 서버(localhost:5001) 접근 가능 여부 확인
curl -f http://localhost:5001/health || echo "외부 AAS 서버가 실행 중인지 확인하세요"
```

#### 문제: Goal 3 실행 시 타임아웃
```bash
# 해결 방법
# 1. Job 상태 확인
kubectl get jobs

# 2. Job Pod 로그 확인
kubectl logs job/aasx-simulator-xxxxx

# 3. PVC 권한 문제 확인
kubectl describe pvc factory-shared-pvc

# 4. Docker 이미지 확인
docker images | grep aasx-simple
```

#### 문제: 404 Not Found 에러
```bash
# 해결 방법
# 1. 온톨로지 파일 확인
ls -la ontology/factory_ontology_v2.ttl

# 2. 외부 AAS 서버 접근 확인
curl -f http://localhost:5001/health

# 3. 환경 변수 확인
env | grep AAS
env | grep USE_STANDARD_SERVER
```

### 10.2 로그 수집
```bash
# 모든 Pod 로그 수집
kubectl logs deployment/api-deployment > api.log

# 이벤트 확인
kubectl get events --sort-by='.lastTimestamp'
```

### 10.3 완전 재시작
```bash
# 1. 모든 리소스 삭제
kubectl delete -f k8s/

# 2. Docker 이미지 재빌드
docker build -f api.Dockerfile -t api-server:latest .
docker build -f aasx_simple.Dockerfile -t aasx-simple:latest .

# 3. 재배포
kubectl apply -f k8s/

# 4. 포트 포워딩 (기존 프로세스 종료 후)
lsof -ti :8080 | xargs kill -9 2>/dev/null || echo "8080 포트 사용 중인 프로세스 없음"
kubectl port-forward service/api-service 8080:80 &
```

---

## 📝 요약

이 가이드를 따라 Smart Factory Automation 시스템을 구축하고 테스트할 수 있습니다:

1. **Goal 1**: 실패한 냉각 Job 조회 - AAS 데이터 필터링
2. **Goal 3**: 생산 시간 예측 - Kubernetes Job 동적 생성 및 시뮬레이션
3. **Goal 4**: 제품 위치 추적 - 실시간 추적 데이터 조회

모든 컴포넌트는 Kubernetes에서 실행되며, 온톨로지 기반 실행 계획과 AAS v3.0 표준을 따릅니다.

### 주요 포트
- API Server: `localhost:8080`
- 외부 AAS Server: `localhost:5001` (별도 실행 필요)

### 중요 파일 경로
- 온톨로지: `ontology/factory_ontology_v2.ttl`
- 시뮬레이터: `AASX-main/simulatePlant_AASX_v3.py`

### 외부 의존성
- AAS Server가 `localhost:5001`에서 실행 중이어야 합니다

---

**작성일**: 2025-08-25  
**버전**: 1.0.0