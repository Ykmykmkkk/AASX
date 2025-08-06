# CLAUDE.md - AAS Integration v5 Project Documentation

## 프로젝트 개요

### 미션
DSL 입력을 받아 온톨로지 기반 실행 계획을 수립하고, AAS(Asset Administration Shell) Server와 연동하여 Industry 4.0 표준을 준수하는 데이터를 조회하고 처리하는 시스템 구축.

### v5 개선사항
- v4의 파일 구조 문제 해결
- 깔끔한 프로젝트 구조로 처음부터 재구성
- 모든 핵심 파일이 올바른 위치에 배치
- 테스트 및 실행 스크립트 정리

### 핵심 아키텍처
**하이브리드 접근법**: 온톨로지가 워크플로우와 로직을 담당하고, AAS가 데이터 관리를 담당하는 명확한 역할 분리.

```
DSL Input → Ontology Query → Execution Plan → AAS API Calls → Result Processing
```

## 아키텍처 상세

### 3단계 아키텍처
1. **온톨로지 레이어**: 실행 계획 수립, 워크플로우 정의, 의미론적 추론
2. **AAS 레이어**: Industry 4.0 표준 데이터 모델, REST API, 정적/동적 데이터 관리
3. **실행 레이어**: DSL 파싱, API 조정, 결과 통합, 폴백 처리

### 폴백 전략
```
1차: AAS Server REST API (실제 서버)
     ↓ (실패 시)
2차: Mock AAS Server (로컬 시뮬레이터)  
     ↓ (실패 시)
3차: 정적 TTL 데이터 직접 조회
```

## v4에서 v5로의 개선

### v4의 문제점
- 파일 정리 과정에서 핵심 v2 파일들 삭제
- 중복된 디렉토리 구조
- 온톨로지 파일 위치 혼란
- 테스트 스크립트 오류

### v5의 해결책
1. **명확한 구조**: 처음부터 올바른 디렉토리 구조 생성
2. **파일 무결성**: 모든 필수 파일이 올바른 위치에 존재
3. **단순화**: 불필요한 중복 제거
4. **문서화**: 명확한 실행 가이드

## 현재 구현 상태

### 완료된 기능
- ✅ AAS 표준 데이터 모델 (`aas_models.py`)
- ✅ Submodel 템플릿 (Nameplate, TechnicalData, OperationalData, Documentation)
- ✅ Mock Server v2 (표준 API)
- ✅ Client v2 (표준 파싱)
- ✅ Executor v2 (Goal 1, 4 완전 구현)
- ✅ Fallback 메커니즘
- ✅ Utility 함수

### Goal 구현 상태
| Goal | 설명 | 구현 상태 | 테스트 상태 |
|------|------|-----------|-------------|
| Goal 1 | 냉각 실패 작업 조회 | ✅ 완료 | 테스트 필요 |
| Goal 2 | 제품 이상 감지 | ⏸️ 구조만 | - |
| Goal 3 | 완료 시간 예측 | ⏸️ 구조만 | - |
| Goal 4 | 제품 위치 추적 | ✅ 완료 | 테스트 필요 |

## AAS 표준 준수 상세

### 구현된 AAS Metamodel 3.0 요소

#### 1. Core Classes
```python
# aas_integration/standards/aas_models.py
- AssetAdministrationShell
- AssetInformation  
- Submodel
- SubmodelElement (Property, MultiLanguageProperty, SubmodelElementCollection)
- Reference, Key
- AdministrativeInformation
```

#### 2. 표준 Submodel 템플릿
```python
# aas_integration/standards/submodel_templates.py
- Nameplate (ZVEI Digital Nameplate)
- TechnicalData (기술 사양)
- OperationalData (운영 데이터)
- Documentation (VDI 2770)
```

#### 3. SemanticId 사용
- IRDI 형식: `0173-1#02-AAW001#001`
- GlobalReference 타입
- 표준 컨셉 참조

## 테스트 데이터 아키텍처

### 기계 장비 (5대)
```python
# CNC 기계 (냉각 필요)
- CNC001: DMG MORI DMU 50 (15.5kW, 3500kg)
- CNC002: HAAS VF-2SS (20.0kW, 4200kg)

# CNC 기계 (자체 냉각)
- CNC003: Mazak VARIAXIS i-700 (18.0kW, 5800kg)

# 3D 프린터
- 3DP001: Stratasys F370 (2.5kW, 227kg)

# 조립 로봇
- ASM001: KUKA KR 10 R1100 (3.0kW, 54kg)
```

### 제품 (4개)
```python
# 냉각 불필요
- Product-A1: Precision Gear (Steel)
- Product-D1: Plastic Prototype (ABS)

# 냉각 필요
- Product-B1: Aluminum Housing
- Product-C1: Titanium Component
```

### 작업 이력 시나리오
```python
# 2025-07-17 실패 작업 (3건)
- JOB-001: Product-B1 @ CNC002 - cooling_system_error
- JOB-002: Product-C1 @ CNC001 - temperature_exceeded
- JOB-003: Product-B1 @ CNC002 - coolant_flow_insufficient

# 성공 작업 (2건)
- JOB-004: Product-A1 @ CNC003
- JOB-005: Product-D1 @ 3DP001
```

## 파일 구조 및 역할

### v5 디렉토리 구조
```
v5/
├── aas_integration/              # 핵심 모듈
│   ├── __init__.py
│   ├── standards/                # AAS 표준 구현
│   │   ├── __init__.py
│   │   ├── aas_models.py        # Metamodel 3.0 클래스
│   │   ├── submodel_templates.py # 표준 Submodel
│   │   └── mock_data_generator.py # 테스트 데이터 생성
│   ├── client_v2.py             # 표준 준수 REST 클라이언트
│   ├── executor_v2.py           # Goal 실행 엔진
│   ├── mock_server_v2.py        # 표준 API Mock 서버
│   ├── fallback.py              # 폴백 처리 로직
│   └── utils.py                 # 유틸리티 함수
├── ontology_extensions/          # 온톨로지 확장
│   ├── execution-ext.ttl        # AAS 엔드포인트 정의
│   └── bridge-ext.ttl           # 브리지 확장
├── aas-test-data/               # 테스트 데이터 (TTL)
├── bridge-ontology.ttl          # DSL-온톨로지 매핑
├── domain-ontology.ttl          # 도메인 개념 정의
├── test_*.py                    # 테스트 파일들
├── scripts/                     # 실행 스크립트
└── CLAUDE.md                    # 이 문서
```

## 실행 가이드

### 1. Mock 데이터 생성
```bash
cd /Users/jeongseunghwan/Desktop/aas-project/testing/v5
python3 -m aas_integration.standards.mock_data_generator
```

### 2. Mock Server v2 시작
```bash
python3 -m aas_integration.mock_server_v2
```

### 3. 테스트 실행

#### 통합 테스트
```bash
python3 test_v2_integration.py
```

#### Goal별 개별 테스트
```bash
# Goal 1 테스트
python3 test_goal1_v2.py

# Goal 4 테스트  
python3 test_goal4_v2.py
```

### 4. Python에서 직접 사용
```python
from aas_integration.executor_v2 import AASExecutorV2

executor = AASExecutorV2()

# Goal 1: 냉각 실패 작업 조회
result = executor.execute({
    "goal": "query_failed_jobs_with_cooling",
    "parameters": {"date": "2025-07-17"}
})

# Goal 4: 제품 위치 추적
result = executor.execute({
    "goal": "track_product_position",
    "parameters": {"product_id": "Product-C1"}
})
```

## 개발 가이드

### 새로운 Goal 추가하기
1. `executor_v2.py`에 `_execute_goalX()` 메서드 추가
2. `execute()` 메서드에 Goal 라우팅 추가
3. 필요한 AAS API 호출 구현
4. 테스트 케이스 작성

### 새로운 장비/제품 추가하기
```python
# mock_data_generator.py의 generate_machine_shells()에 추가
{
    "id": "NEW001",
    "name": "New Machine",
    "manufacturer": "Company",
    "cooling_required": True,
    # ... 기타 속성
}
```

## 문제 해결 가이드

### Mock Server 연결 실패
```bash
# 포트 확인
lsof -i :5001

# 프로세스 종료
pkill -f mock_server_v2

# 다시 시작
python3 -m aas_integration.mock_server_v2
```

### 모듈 import 오류
```bash
# Python 경로 확인
echo $PYTHONPATH

# 현재 디렉토리에서 실행
cd /Users/jeongseunghwan/Desktop/aas-project/testing/v5
python3 -m aas_integration.executor_v2
```

## 핵심 개선사항 (v4 → v5)

1. **파일 구조 정리**: 모든 파일이 올바른 위치에 배치
2. **중복 제거**: 온톨로지 파일 중복 제거
3. **명확한 네이밍**: v2 suffix로 버전 명확화
4. **완전한 구현**: 누락된 파일 없이 전체 구현
5. **향상된 문서화**: 실행 가이드 개선

## ⚠️ 긴급 개선 필요사항

### 1. 하드코딩된 ID 제거 (최우선)
**문제**: 현재 테스트 코드와 executor에서 machine ID가 하드코딩되어 있음

#### 현재 문제점
```python
# test_v2_integration.py Line 73 (수정됨)
shell = client.get_shell("urn:aas:Machine:CNC001")  # 하드코딩

# executor_v2.py Line 247  
machine_shell = self.client.get_shell(f"urn:aas:Machine:{machine_id}")  # 동적이지만 제한적
```

#### 개선 방안
1. **온톨로지 기반 동적 조회**
   ```python
   # executor_v2.py의 query_ontology() 메서드 활용
   def get_target_machines_from_ontology(self, goal: str) -> List[str]:
       """온톨로지에서 goal에 필요한 machine ID들을 동적으로 조회"""
       query = f"""
       PREFIX ex: <http://example.com/execution#>
       PREFIX aas: <http://example.com/aas#>
       
       SELECT ?machineId
       WHERE {{
           ex:{goal} ex:requiresMachine ?machine .
           ?machine aas:id ?machineId .
       }}
       """
       # 구현 필요
   ```

2. **Configuration 파일 분리**
   ```yaml
   # config/test_targets.yml
   test_machines:
     - id: "CNC001"
       purpose: ["cooling_test", "primary_cnc"]
     - id: "CNC002" 
       purpose: ["cooling_test", "backup_cnc"]
   
   test_products:
     - id: "Product-B1"
       requires_cooling: true
   ```

3. **Dynamic Discovery via API**
   ```python
   def discover_test_targets(self) -> Dict[str, List[str]]:
       """AAS Server에서 실제 존재하는 shells 조회"""
       shells = self.client.get_all_shells()
       machines = [s for s in shells if s['id'].startswith('urn:aas:Machine:')]
       return {
           'cooling_machines': [m for m in machines if self._requires_cooling(m)],
           'all_machines': machines
       }
   ```

### 2. 온톨로지 연동 완성
**문제**: `query_ontology()` 메서드가 구현되어 있지만 실제로 사용되지 않음

#### 작업 내용
1. **온톨로지에 machine 정보 추가**
   ```turtle
   # execution-ext.ttl에 추가
   ex:query_failed_jobs_with_cooling ex:requiresMachine ex:CNC001, ex:CNC002 ;
                                     ex:targetProductType ex:CoolingRequired .
   
   ex:CNC001 a aas:Machine ;
            aas:id "CNC001" ;
            aas:requiresCooling true .
   ```

2. **Executor에서 온톨로지 쿼리 활용**
   ```python
   def _execute_goal1(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
       # 온톨로지에서 대상 machines 조회
       target_machines = self.get_target_machines_from_ontology("query_failed_jobs_with_cooling")
       
       for machine_id in target_machines:
           shell = self.client.get_shell(f"urn:aas:Machine:{machine_id}")
           # ...
   ```

### 3. 테스트 데이터 일관성 확보
**문제**: Mock 데이터와 테스트 코드 간 ID 불일치 가능성

#### 작업 내용
1. **테스트 데이터 검증**
   ```python
   def validate_test_data_consistency():
       """Mock 데이터와 테스트 코드의 ID 일관성 검증"""
       # aas_integration/mock_data/ 의 모든 shell ID 추출
       # 테스트 파일들의 하드코딩된 ID 추출  
       # 불일치 보고
   ```

2. **동적 테스트 ID 생성**
   ```python
   # test_v2_integration.py 개선
   def get_test_machine_id(self) -> str:
       """실제 존재하는 machine 중 첫 번째 반환"""
       shells = self.client.get_all_shells()
       machine_shells = [s for s in shells if s['id'].startswith('urn:aas:Machine:')]
       return machine_shells[0]['id'] if machine_shells else None
   ```

## 향후 개발 계획

### Phase 1: 긴급 개선 (1-2일)
- [x] 하드코딩된 테스트 ID 수정 (완료)
- [ ] 온톨로지 기반 동적 machine ID 조회 구현
- [ ] Configuration 파일 기반 테스트 대상 관리
- [ ] 테스트 데이터 일관성 검증 스크립트 작성

### Phase 2: 테스트 및 검증 (2-3일)
- [ ] 전체 테스트 스위트 작성
- [ ] 스크립트 자동화
- [ ] 성능 벤치마크

### Phase 3: Goal 2, 3 구현 (1주)
- [ ] Goal 2: 머신러닝 기반 이상 감지
- [ ] Goal 3: 작업 시간 예측 모델

### Phase 4: 실제 AAS 서버 연동 (2주)
- [ ] Eclipse BaSyx 연동
- [ ] 인증/권한 처리
- [ ] 실시간 데이터 지원

---

**작성일**: 2025-08-05  
**버전**: v5 초기 구현  
**상태**: 핵심 기능 구현 완료, 테스트 필요