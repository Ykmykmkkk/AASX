# CLAUDE_v2.md - AAS Integration v6: 개선된 아키텍처 설계

## 📋 v6 아키텍처 개선 계획 (2025-08-06)

### 1. 문제점 분석

#### 초기 구현의 문제
- ❌ Mock Server가 실행되지 않음
- ❌ 스냅샷 데이터가 로컬 파일로만 존재
- ❌ AAS 표준 Shell/Submodel 구조 미사용
- ❌ 실제 REST API 호출 없음
- ❌ v5의 검증된 구조 미활용

#### 근본 원인
1. 스냅샷을 별도 JSON으로 저장 (AAS Server와 분리)
2. DataCollector가 로컬 파일 직접 읽기
3. Mock Server 미구현으로 API 테스트 불가

### 2. 올바른 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  온톨로지 (나침반)                    │
│  - Goal → Execution Plan 매핑                        │
│  - Action 시퀀스 정의                                │
│  - Data Source 결정                                  │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              Execution Planner                       │
│  - 온톨로지 쿼리                                     │
│  - 실행 계획 생성                                    │
│  - Action 오케스트레이션                             │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│               AAS Client v2                          │
│  - HTTP REST API 호출                                │
│  - 표준 AAS 응답 파싱                                │
│  - 에러 처리 및 재시도                               │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│            Mock AAS Server v6                        │
│  - Flask 기반 REST API                               │
│  - AAS Metamodel 3.0 준수                            │
│  - 시점별 동적 데이터 (T1-T5)                        │
│  - v5 구조 재사용                                    │
└─────────────────────────────────────────────────────┘
```

### 3. 데이터 모델 재설계

#### 3.1 AAS Shell 구조
```json
{
  "modelType": "AssetAdministrationShell",
  "id": "urn:aas:Machine:CNC001",
  "idShort": "CNC001",
  "assetInformation": {
    "assetKind": "Instance",
    "globalAssetId": "urn:company:machines:cnc001"
  },
  "submodels": [
    {
      "type": "ModelReference",
      "keys": [{
        "type": "Submodel",
        "value": "urn:aas:sm:CNC001:Nameplate"
      }]
    },
    {
      "type": "ModelReference",
      "keys": [{
        "type": "Submodel",
        "value": "urn:aas:sm:CNC001:OperationalData"
      }]
    },
    {
      "type": "ModelReference",
      "keys": [{
        "type": "Submodel",
        "value": "urn:aas:sm:CNC001:JobHistory"
      }]
    }
  ]
}
```

#### 3.2 OperationalData Submodel (시점별)
```json
{
  "modelType": "Submodel",
  "id": "urn:aas:sm:CNC001:OperationalData",
  "idShort": "OperationalData",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{
      "type": "GlobalReference",
      "value": "0173-1#02-AAV232#002"
    }]
  },
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "Status",
      "value": "ERROR",
      "valueType": "xs:string",
      "timestamp": "2025-07-17T14:00:00"
    },
    {
      "modelType": "Property",
      "idShort": "Temperature",
      "value": "32.5",
      "valueType": "xs:float",
      "unit": "°C",
      "timestamp": "2025-07-17T14:00:00"
    },
    {
      "modelType": "Property",
      "idShort": "CoolantFlow",
      "value": "2.1",
      "valueType": "xs:float",
      "unit": "L/min",
      "timestamp": "2025-07-17T14:00:00"
    }
  ]
}
```

#### 3.3 JobHistory Submodel
```json
{
  "modelType": "Submodel",
  "id": "urn:aas:sm:CNC001:JobHistory",
  "idShort": "JobHistory",
  "submodelElements": [
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "JOB-002",
      "value": [
        {
          "modelType": "Property",
          "idShort": "ProductId",
          "value": "Product-C1"
        },
        {
          "modelType": "Property",
          "idShort": "Status",
          "value": "FAILED"
        },
        {
          "modelType": "Property",
          "idShort": "FailureReason",
          "value": "temperature_exceeded"
        },
        {
          "modelType": "Property",
          "idShort": "Timestamp",
          "value": "2025-07-17T14:00:00"
        }
      ]
    }
  ]
}
```

### 4. 구현 계획

#### Phase 3-1: 스냅샷 → AAS 변환
```python
# aas_data/converter.py
class SnapshotToAASConverter:
    def convert_machine(self, machine_data, timepoint):
        """기계 데이터를 AAS Shell로 변환"""
        return {
            "modelType": "AssetAdministrationShell",
            "id": f"urn:aas:Machine:{machine_data['machine_id']}",
            "submodels": [
                self.create_nameplate(machine_data),
                self.create_operational_data(machine_data, timepoint),
                self.create_job_history(machine_data, timepoint)
            ]
        }
    
    def convert_product(self, product_data):
        """제품 데이터를 AAS Shell로 변환"""
        return {
            "modelType": "AssetAdministrationShell",
            "id": f"urn:aas:Product:{product_data['product_id']}",
            "submodels": [
                self.create_specification(product_data),
                self.create_requirements(product_data)
            ]
        }
```

#### Phase 3-2: Mock Server 구현
```python
# src/mock_server.py
from flask import Flask, jsonify, request
import json
from datetime import datetime

app = Flask(__name__)

class AASMockServer:
    def __init__(self):
        self.shells = {}  # 변환된 AAS Shell 데이터
        self.submodels = {}  # 변환된 Submodel 데이터
        self.load_data()
    
    def load_data(self):
        """스냅샷 데이터를 AAS 형식으로 로드"""
        converter = SnapshotToAASConverter()
        for timepoint in ["T1", "T2", "T3", "T4", "T5"]:
            snapshot = load_snapshot(timepoint)
            self.process_snapshot(snapshot, timepoint, converter)
    
    def get_operational_data(self, machine_id, timestamp):
        """시점별 운영 데이터 반환"""
        timepoint = self.map_timestamp_to_timepoint(timestamp)
        submodel_id = f"urn:aas:sm:{machine_id}:OperationalData"
        return self.submodels[timepoint].get(submodel_id)

@app.route('/shells', methods=['GET'])
def get_shells():
    """모든 AAS Shell 조회"""
    return jsonify(list(server.shells.values()))

@app.route('/shells/<aas_id>', methods=['GET'])
def get_shell(aas_id):
    """특정 AAS Shell 조회"""
    shell = server.shells.get(aas_id)
    if shell:
        return jsonify(shell)
    return jsonify({"error": "Shell not found"}), 404

@app.route('/submodels/<submodel_id>', methods=['GET'])
def get_submodel(submodel_id):
    """Submodel 조회 (시점별)"""
    timestamp = request.args.get('timestamp')
    if timestamp:
        # 시점별 데이터 반환
        timepoint = map_timestamp_to_timepoint(timestamp)
        submodel = server.get_submodel_at_time(submodel_id, timepoint)
    else:
        # 최신 데이터 반환
        submodel = server.get_latest_submodel(submodel_id)
    
    if submodel:
        return jsonify(submodel)
    return jsonify({"error": "Submodel not found"}), 404

@app.route('/api/machines/cooling-required', methods=['GET'])
def get_cooling_machines():
    """냉각 필요 기계 조회 (Goal 1)"""
    cooling_machines = []
    for shell in server.shells.values():
        if "Machine" in shell['id']:
            # TechnicalData에서 cooling_required 확인
            tech_data = server.get_submodel(f"{shell['id']}:TechnicalData")
            if tech_data and tech_data.get('cooling_required'):
                cooling_machines.append(shell)
    return jsonify(cooling_machines)

@app.route('/api/jobs/failed', methods=['GET'])
def get_failed_jobs():
    """실패한 작업 조회 (Goal 1)"""
    date = request.args.get('date', '2025-07-17')
    timepoint = "T4"  # 실패 시점
    
    failed_jobs = []
    for machine_id in server.get_machine_ids():
        job_history = server.get_submodel_at_time(
            f"urn:aas:sm:{machine_id}:JobHistory", 
            timepoint
        )
        if job_history:
            for element in job_history.get('submodelElements', []):
                if element.get('Status') == 'FAILED':
                    failed_jobs.append(element)
    
    return jsonify(failed_jobs)
```

#### Phase 3-3: AAS Client 구현
```python
# src/aas_client.py
import requests
from typing import Dict, List, Optional, Any
import logging

class AASClient:
    """AAS REST API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
    
    def get_shells(self) -> List[Dict[str, Any]]:
        """모든 Shell 조회"""
        try:
            response = self.session.get(f"{self.base_url}/shells")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get shells: {e}")
            return []
    
    def get_shell(self, aas_id: str) -> Optional[Dict[str, Any]]:
        """특정 Shell 조회"""
        try:
            response = self.session.get(f"{self.base_url}/shells/{aas_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get shell {aas_id}: {e}")
            return None
    
    def get_submodel(self, submodel_id: str, 
                    timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Submodel 조회"""
        try:
            url = f"{self.base_url}/submodels/{submodel_id}"
            params = {"timestamp": timestamp} if timestamp else {}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get submodel {submodel_id}: {e}")
            return None
    
    def get_cooling_machines(self) -> List[Dict[str, Any]]:
        """냉각 필요 기계 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/machines/cooling-required")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get cooling machines: {e}")
            return []
    
    def get_failed_jobs(self, date: str) -> List[Dict[str, Any]]:
        """실패한 작업 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/jobs/failed",
                params={"date": date}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get failed jobs: {e}")
            return []
```

#### Phase 3-4: DataCollector 수정
```python
# src/data_collector.py (수정)
class DataCollector:
    def __init__(self):
        self.aas_client = AASClient()
        self.fallback_to_local = False
    
    def collect_from_aas(self, endpoint: str, params: Dict = None):
        """AAS Server에서 데이터 수집"""
        # 1차: AAS REST API
        if endpoint.startswith("/shells"):
            return self.aas_client.get_shell(endpoint.split("/")[-1])
        elif endpoint.startswith("/submodels"):
            submodel_id = endpoint.split("/")[-1]
            timestamp = params.get("timestamp") if params else None
            return self.aas_client.get_submodel(submodel_id, timestamp)
        elif "cooling-required" in endpoint:
            return self.aas_client.get_cooling_machines()
        elif "failed" in endpoint:
            date = params.get("date", "2025-07-17")
            return self.aas_client.get_failed_jobs(date)
        
        # 2차: Fallback to local snapshot
        if self.fallback_to_local:
            return self.collect_from_snapshot(...)
```

#### Phase 3-5: ExecutionPlanner 통합
```python
# src/execution_planner.py (수정)
class ExecutionPlanner:
    def __init__(self):
        self.ontology_manager = OntologyManager()
        self.data_collector = DataCollector()
        self.aas_client = AASClient()
    
    def _execute_aas_action(self, action: Dict, parameters: Dict):
        """AAS API 액션 실행"""
        endpoint = action.get("endpoint")
        
        # 파라미터 치환
        for key, value in parameters.items():
            endpoint = endpoint.replace(f"{{{key}}}", str(value))
        
        # 시점 정보 추가
        params = {}
        if action.get("snapshotTime"):
            params["timestamp"] = action["snapshotTime"]
        
        # AAS Client로 API 호출
        return self.data_collector.collect_from_aas(endpoint, params)
    
    def _execute_snapshot_action(self, action: Dict):
        """스냅샷 액션 실행 (AAS Server 경유)"""
        timepoint = self.extract_timepoint(action.get("snapshotTime"))
        data_path = action.get("dataPath")
        
        # AAS Server에서 시점별 Submodel 조회
        if data_path == "jobs":
            return self.aas_client.get_failed_jobs("2025-07-17")
        elif data_path == "machines":
            timestamp = self.timepoint_to_timestamp(timepoint)
            machines = []
            for shell in self.aas_client.get_shells():
                if "Machine" in shell['id']:
                    machine_id = shell['idShort']
                    operational_data = self.aas_client.get_submodel(
                        f"urn:aas:sm:{machine_id}:OperationalData",
                        timestamp
                    )
                    machines.append(operational_data)
            return machines
```

### 5. 파일 구조

```
v6/
├── ontology/               ✅ 완료
│   ├── execution-ontology.ttl
│   ├── domain-ontology.ttl
│   └── bridge-ontology.ttl
├── snapshots/              ✅ 완료
│   └── snapshot_T*.json
├── aas_data/              🔄 추가 필요
│   ├── converter.py       # 스냅샷 → AAS 변환
│   ├── shells/            # 변환된 AAS Shell JSON
│   └── submodels/         # 변환된 Submodel JSON
├── src/
│   ├── mock_server.py     🔄 새로 구현
│   ├── aas_client.py      🔄 새로 구현
│   ├── aas_models.py      🔄 v5에서 복사
│   ├── ontology_manager.py ✅ 완료
│   ├── data_collector.py   🔄 수정 필요
│   └── execution_planner.py 🔄 수정 필요
├── scripts/
│   ├── start_server.sh    🔄 서버 시작 스크립트
│   └── setup_env.sh       🔄 환경 설정 스크립트
└── test_*.py              🔄 테스트 수정

```

### 6. 테스트 시나리오

#### Goal 1 실행 흐름
```
1. Start Mock Server
   $ python src/mock_server.py

2. Run Test
   $ python test_goal1_with_server.py

3. Execution Flow:
   a. 온톨로지 → 5단계 실행 계획
   b. SPARQL → 냉각 제품 조회
   c. AAS API → GET /api/machines/cooling-required
   d. SNAPSHOT → GET /submodels/JobHistory?timestamp=T4
   e. FILTER → 실패 작업 필터링
   f. TRANSFORM → 리포트 생성

4. Expected Result:
   - 3 failed jobs found (JOB-001, JOB-002, JOB-003)
   - All from cooling-required machines
   - All cooling-required products
```

### 7. 주요 개선사항

1. **AAS 표준 준수**
   - Metamodel 3.0 구조 사용
   - 표준 REST API 엔드포인트
   - SemanticId 사용

2. **v5 자산 활용**
   - 검증된 Mock Server 구조
   - AAS 모델 클래스
   - 표준 템플릿

3. **동적 데이터 처리**
   - 시점별 Submodel 조회
   - timestamp 파라미터 지원
   - 실시간 상태 시뮬레이션

4. **온톨로지 통합**
   - dataSource 정보 활용
   - endpoint 동적 구성
   - fallback 체인 구현

---

**작성일**: 2025-08-06  
**버전**: v6 개선 계획  
**상태**: 구현 준비 완료