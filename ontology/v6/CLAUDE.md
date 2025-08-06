# CLAUDE.md - AAS Integration v6 프로젝트 현황

## 🎯 프로젝트 개요

### 비전: 온톨로지 기반 "나침반" 시스템
온톨로지가 전체 시스템의 **나침반** 역할을 하여 DSL 입력부터 최종 결과까지 모든 과정을 안내하고 지휘하는 Industry 4.0 표준 준수 제조 데이터 처리 시스템

### 현재 상태 (2025-08-06)
- **구현 완료**: Goal 1 (냉각 실패 조회), Goal 4 (제품 위치 추적)
- **구현 대기**: Goal 2 (이상 감지), Goal 3 (완료 예측)
- **아키텍처**: 스냅샷 기반 시뮬레이션 → AAS 표준 변환 → Mock Server API 제공
- **테스트 전략**: 5개 시점(T1-T5) 냉각 실패 시나리오

## 🏗️ v6 아키텍처 (구현 완료)

### 시스템 구조
```
DSL Input → DataCollector v2 → AAS Client → Mock Server → AAS Data
                    ↓ (Fallback)
               Local Snapshots → Direct Processing
```

### 핵심 개선사항 (v5 → v6)
1. **스냅샷 → AAS 변환**: `aas_data/converter.py`가 스냅샷을 표준 AAS Shell/Submodel로 변환
2. **Mock Server 구현**: `src/mock_server.py`가 REST API 제공 (Flask 기반)
3. **Fallback 메커니즘**: AAS Server 실패 시 로컬 스냅샷 직접 사용
4. **TrackingInfo Submodel**: Goal 4를 위한 제품 위치 추적 서브모델 추가
5. **통합 검증**: Goal 1과 4가 하나의 시스템으로 동작 확인

## 📁 프로젝트 구조

### 디렉토리 구성
```
v6/
├── aas_data/               # AAS 데이터 및 변환
│   ├── converter.py        # 스냅샷 → AAS 변환기
│   ├── shells/            # AAS Shell JSON (기계, 제품)
│   └── submodels/         # Submodel JSON (동적/정적 데이터)
├── snapshots/             # 시점별 제조 데이터 (T1-T5)
├── src/                   # 핵심 모듈
│   ├── mock_server.py     # Mock AAS Server (Flask)
│   ├── aas_client.py      # AAS REST API 클라이언트
│   ├── data_collector_v2.py # 다중 소스 데이터 수집
│   └── standards/         # AAS 표준 모델 정의
└── test_*.py              # 테스트 스크립트
```

### 핵심 모듈 역할

| 모듈 | 역할 | 참고 메서드 |
|------|------|------------|
| `converter.py` | 스냅샷을 AAS 표준으로 변환 | `convert_snapshot()`, `create_product_tracking_data()` |
| `mock_server.py` | REST API 엔드포인트 제공 | Flask 라우트 정의 |
| `aas_client.py` | HTTP 통신 및 응답 파싱 | `get_shell()`, `get_product_location()` |
| `data_collector_v2.py` | 데이터 수집 및 폴백 처리 | `collect_cooling_products()`, `collect_product_location()` |

## 🔄 실행 흐름

### Goal 1: 냉각 실패 작업 조회
```
1. DataCollectorV2.collect_cooling_products()
   → AAS Client 시도 → 실패 시 로컬 스냅샷
   → 결과: ["Product-B1", "Product-C1"]

2. DataCollectorV2.collect_machines_with_cooling()
   → 스냅샷 T2에서 기계 정보 수집
   → 결과: ["CNC001", "CNC002"]

3. DataCollectorV2.collect_job_history()
   → Mock Server 또는 스냅샷 T4
   → 결과: 3개 실패 작업

4. 필터링 및 결과 생성
   → 냉각 제품 + 냉각 기계 + 실패 상태
   → 최종: JOB-001, JOB-002, JOB-003
```

### Goal 4: 제품 위치 추적
```
1. DataCollectorV2.collect_product_location()
   → AAS Client 시도 (TrackingInfo 서브모델)
   → 실패 시 스냅샷에서 작업 상태 확인

2. 위치 결정 로직 (converter.py)
   - FAILED/RUNNING → 기계 위치
   - COMPLETED → QC_Station
   - 기타 → Warehouse

3. TrackingInfo 서브모델 생성
   → CurrentLocation, LocationType, Status, LastUpdate
   → T4 시점 기준 저장
```

## 📸 스냅샷 테스트 시나리오

### 냉각 실패 시나리오 (T1-T5)
```
T1 (08:00): 작업 시작 - 모든 기계 IDLE
T2 (10:00): 정상 작동 - CNC001 RUNNING
T3 (12:00): 이상 징후 - 온도 상승 감지
T4 (14:00): 냉각 실패 - 3개 작업 FAILED ← Goal 테스트 시점
T5 (16:00): 복구 시작 - 유지보수 진행
```

### 테스트 데이터
- **기계**: CNC001, CNC002 (냉각 필요), CNC003 (자체 냉각)
- **제품**: Product-B1, Product-C1 (냉각 필요), Product-A1 (냉각 불필요)
- **실패 작업**: JOB-001, JOB-002, JOB-003 (T4 시점)

## 🏭 AAS 표준 구현

### AAS Metamodel 3.0 구현
```python
# src/standards/aas_models.py
- AssetAdministrationShell
- Submodel, SubmodelElement  
- Property, Reference, Key
```

### 표준 Submodel 템플릿
- **Nameplate**: 제품/기계 명판 정보
- **TechnicalData**: 기술 사양 (cooling_required 포함)
- **OperationalData**: 운영 데이터 (센서 데이터)
- **JobHistory**: 작업 이력 (T1-T5 시점별)
- **TrackingInfo**: 제품 위치 추적 (Goal 4용)

## 🔗 TrackingInfo 서브모델 상세

### 설계 목적
제품의 현재 위치와 상태를 추적하는 표준 서브모델

### 핵심 속성 (4개)
```json
{
  "CurrentLocation": "CNC002",     // 현재 위치
  "LocationType": "Machine",       // 위치 타입
  "Status": "ERROR",               // 현재 상태
  "LastUpdate": "2025-07-17T14:00" // 마지막 업데이트
}
```

### 다른 Goal에서의 활용
- **Goal 1**: 실패한 제품의 현재 위치 파악
- **Goal 2**: 이상 감지된 제품의 격리 필요성 판단
- **Goal 3**: 현재 위치 기반 남은 공정 계산

### 실제 쿼리 예시
```http
GET /api/shells/urn:aas:Product:Product-B1/submodels/urn:aas:sm:Product-B1:TrackingInfo

응답:
{
  "CurrentLocation": "CNC002",
  "LocationType": "Machine",
  "Status": "ERROR",
  "LastUpdate": "2025-07-17T14:00:00"
}
```

## 📋 Fallback 메커니즘

### 3단계 폴백 전략
```
1차: AAS Server REST API
     ↓ (실패 시)
2차: Local Snapshot JSON
     ↓ (실패 시)
3차: Hardcoded Defaults
```

### 구현 위치
`data_collector_v2.py`의 각 collect 메서드에서 try-except로 처리

## 🚀 테스트 실행 방법

### 1. 데이터 변환
```bash
cd aas_data
python3 converter.py  # 스냅샷 → AAS 변환
```

### 2. Mock Server 실행 (선택적)
```bash
python3 start_server.py  # Flask 필요
```

### 3. 테스트 실행
```bash
python3 test_integrated_goals.py  # Goal 1 & 4 통합
python3 test_goal4_simple.py      # Goal 4 단순
```

## 📦 Goal 구현 상태

### Goal 1: 냉각 실패 작업 조회
- ✅ 구현 완료
- 핵심 로직: `data_collector_v2.py`의 `collect_cooling_products()`, `collect_job_history()`
- 테스트: 3개 실패 작업 정상 검출

### Goal 4: 제품 위치 추적  
- ✅ 구현 완료 (최적화 완료)
- 핵심 로직: `converter.py`의 `create_product_tracking_data()`
- TrackingInfo 서브모델 4개 속성으로 단순화

### Goal 2: 이상 감지
- ❌ 미구현
- 필요: Docker 컨테이너 시뮬레이션

### Goal 3: 완료 시간 예측
- ❌ 미구현
- 필요: ML 모델 통합

## 🔮 향후 계획

### 즉시 개선 사항
1. **ExecutionPlanner 통합**: 온톨로지 기반 실행 계획 수립
2. **실제 AAS Server 연동**: Eclipse BaSyx 등 실제 서버 연동

### 중기 목표
1. **Goal 2, 3 구현**: 컨테이너 기반 AI/ML 통합
2. **실시간 데이터**: WebSocket/SSE 구현
3. **시각화 대시보드**: 제품 이동 경로 시각화

---

**작성일**: 2025-08-06  
**버전**: v6  
**상태**: Goal 1, 4 구현 완료, Goal 2, 3 대기