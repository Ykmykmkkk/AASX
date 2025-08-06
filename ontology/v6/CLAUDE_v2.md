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

## 📋 Goals 2-4 구현 계획 (2025-08-06)

### Goal 2: Detect Anomaly for Product

#### 목표
제품의 센서 데이터를 분석하여 이상 패턴을 감지하고 예측

#### 데이터 소스
1. **AAS Server (정적)**
   - Product Shell 정보
   - Specification Submodel (정상 범위)
   - Requirements Submodel (품질 기준)

2. **Snapshots (동적)**
   - T1-T5 시점별 센서 데이터
   - Temperature, Pressure, Vibration 측정값
   - 품질 측정 데이터

3. **Docker Container (AI/ML)**
   - 이상 감지 모델 실행
   - TensorFlow/PyTorch 기반 분석
   - 시계열 패턴 분석

#### 실행 계획
```python
def execute_goal2(self, product_id: str, timepoint: str = "T4"):
    # 1. AAS에서 제품 정보 조회
    product_shell = self.aas_client.get_shell(f"urn:aas:Product:{product_id}")
    spec = self.aas_client.get_submodel(f"urn:aas:sm:{product_id}:Specification")
    
    # 2. 시점별 센서 데이터 수집
    sensor_data = []
    for tp in ["T1", "T2", "T3", "T4", "T5"]:
        timestamp = self.timepoint_to_timestamp(tp)
        data = self.aas_client.get_submodel(
            f"urn:aas:sm:{product_id}:SensorData",
            timestamp
        )
        sensor_data.append(data)
    
    # 3. Docker 컨테이너로 이상 감지 실행
    container_result = self.run_docker_container(
        image="anomaly-detector:latest",
        data={
            "sensor_data": sensor_data,
            "specification": spec,
            "threshold": 0.95
        }
    )
    
    # 4. 결과 분석 및 리포트 생성
    anomalies = container_result.get("anomalies", [])
    confidence = container_result.get("confidence", 0)
    
    return {
        "product_id": product_id,
        "anomalies_detected": len(anomalies) > 0,
        "anomaly_points": anomalies,
        "confidence": confidence,
        "recommendation": self.generate_recommendation(anomalies)
    }
```

#### AAS Submodel 확장
```json
// SensorData Submodel (시점별)
{
  "modelType": "Submodel",
  "id": "urn:aas:sm:Product-B1:SensorData",
  "idShort": "SensorData",
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "Temperature",
      "value": "85.2",
      "valueType": "xs:float",
      "unit": "°C",
      "timestamp": "2025-07-17T14:00:00"
    },
    {
      "modelType": "Property",
      "idShort": "Pressure",
      "value": "2.8",
      "valueType": "xs:float",
      "unit": "bar"
    },
    {
      "modelType": "Property",
      "idShort": "Vibration",
      "value": "0.45",
      "valueType": "xs:float",
      "unit": "mm/s"
    },
    {
      "modelType": "Property",
      "idShort": "QualityScore",
      "value": "0.92",
      "valueType": "xs:float"
    }
  ]
}
```

### Goal 3: Predict Completion Time

#### 목표
현재 작업 상태와 이력 데이터를 기반으로 작업 완료 시간 예측

#### 데이터 소스
1. **AAS Server**
   - Machine Shell (장비 사양)
   - TechnicalData (처리 능력)
   - MaintenanceHistory (유지보수 이력)

2. **Snapshots**
   - JobHistory (과거 작업 이력)
   - Current Job Status
   - Queue Status

3. **Docker Container**
   - 시간 예측 ML 모델
   - 회귀 분석 엔진

#### 실행 계획
```python
def execute_goal3(self, job_id: str, machine_id: str):
    # 1. 현재 작업 상태 조회
    current_job = self.aas_client.get_submodel(
        f"urn:aas:sm:{machine_id}:CurrentJob"
    )
    
    # 2. 기계 성능 데이터
    tech_data = self.aas_client.get_submodel(
        f"urn:aas:sm:{machine_id}:TechnicalData"
    )
    
    # 3. 과거 작업 이력 (학습 데이터)
    job_history = self.aas_client.get_submodel(
        f"urn:aas:sm:{machine_id}:JobHistory"
    )
    
    # 4. Docker 컨테이너로 예측 실행
    prediction = self.run_docker_container(
        image="completion-predictor:latest",
        data={
            "current_job": current_job,
            "machine_specs": tech_data,
            "historical_jobs": job_history,
            "algorithm": "xgboost"
        }
    )
    
    # 5. 예측 결과 처리
    return {
        "job_id": job_id,
        "machine_id": machine_id,
        "current_progress": current_job.get("progress", 0),
        "predicted_completion": prediction.get("completion_time"),
        "confidence_interval": prediction.get("confidence_interval"),
        "factors": prediction.get("influencing_factors", [])
    }
```

#### CurrentJob Submodel
```json
{
  "modelType": "Submodel",
  "id": "urn:aas:sm:CNC001:CurrentJob",
  "idShort": "CurrentJob",
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "JobId",
      "value": "JOB-005"
    },
    {
      "modelType": "Property",
      "idShort": "ProductId",
      "value": "Product-A1"
    },
    {
      "modelType": "Property",
      "idShort": "StartTime",
      "value": "2025-07-17T08:00:00"
    },
    {
      "modelType": "Property",
      "idShort": "Progress",
      "value": "65",
      "valueType": "xs:integer",
      "unit": "%"
    },
    {
      "modelType": "Property",
      "idShort": "EstimatedRemaining",
      "value": "45",
      "valueType": "xs:integer",
      "unit": "minutes"
    }
  ]
}
```

### Goal 4: Track Product Position

#### 목표
제품의 실시간 위치와 이동 경로를 추적하고 시각화

#### 데이터 소스
1. **AAS Server**
   - Product Shell
   - TrackingInfo Submodel
   - LocationHistory Submodel

2. **Snapshots**
   - 시점별 위치 데이터
   - RFID/바코드 스캔 이력

3. **실시간 업데이트**
   - WebSocket 또는 SSE
   - 위치 센서 데이터

#### 실행 계획
```python
def execute_goal4(self, product_id: str, include_history: bool = True):
    # 1. 제품 Shell 조회
    product_shell = self.aas_client.get_shell(
        f"urn:aas:Product:{product_id}"
    )
    
    # 2. 현재 위치 조회
    current_location = self.aas_client.get_submodel(
        f"urn:aas:sm:{product_id}:TrackingInfo"
    )
    
    # 3. 위치 이력 조회 (옵션)
    location_history = []
    if include_history:
        for tp in ["T1", "T2", "T3", "T4", "T5"]:
            timestamp = self.timepoint_to_timestamp(tp)
            location = self.aas_client.get_submodel(
                f"urn:aas:sm:{product_id}:TrackingInfo",
                timestamp
            )
            if location:
                location_history.append({
                    "timepoint": tp,
                    "location": location.get("CurrentLocation"),
                    "timestamp": timestamp
                })
    
    # 4. 이동 경로 분석
    movement_pattern = self.analyze_movement(location_history)
    
    # 5. 다음 위치 예측 (선택적)
    next_location = self.predict_next_location(
        current_location, 
        movement_pattern
    )
    
    return {
        "product_id": product_id,
        "current_location": {
            "zone": current_location.get("Zone"),
            "station": current_location.get("Station"),
            "coordinates": current_location.get("Coordinates"),
            "last_update": current_location.get("LastUpdate")
        },
        "location_history": location_history,
        "movement_pattern": movement_pattern,
        "predicted_next": next_location,
        "status": current_location.get("Status", "IN_TRANSIT")
    }
```

#### TrackingInfo Submodel
```json
{
  "modelType": "Submodel",
  "id": "urn:aas:sm:Product-B1:TrackingInfo",
  "idShort": "TrackingInfo",
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "Zone",
      "value": "Production"
    },
    {
      "modelType": "Property",
      "idShort": "Station",
      "value": "CNC001"
    },
    {
      "modelType": "Property",
      "idShort": "Coordinates",
      "value": "{'x': 120.5, 'y': 45.2, 'z': 0}"
    },
    {
      "modelType": "Property",
      "idShort": "LastUpdate",
      "value": "2025-07-17T14:30:00"
    },
    {
      "modelType": "Property",
      "idShort": "Status",
      "value": "PROCESSING"
    },
    {
      "modelType": "Property",
      "idShort": "RFID",
      "value": "TAG-001234"
    }
  ]
}
```

### Docker Container Integration

#### Container 구조
```yaml
# docker-compose.yml
version: '3.8'
services:
  anomaly-detector:
    image: anomaly-detector:latest
    ports:
      - "5002:5000"
    environment:
      - MODEL_PATH=/models/anomaly_model.pkl
      - THRESHOLD=0.95
    volumes:
      - ./models:/models
      - ./data:/data
  
  completion-predictor:
    image: completion-predictor:latest
    ports:
      - "5003:5000"
    environment:
      - MODEL_TYPE=xgboost
      - TRAINING_DATA=/data/historical_jobs.csv
    volumes:
      - ./models:/models
      - ./data:/data
```

#### Container 실행 로직
```python
class ContainerExecutor:
    def __init__(self):
        self.docker_client = docker.from_env()
    
    def run_container(self, image: str, data: Dict, timeout: int = 30):
        """Docker 컨테이너 실행 및 결과 반환"""
        try:
            # 데이터를 임시 파일로 저장
            input_file = f"/tmp/input_{uuid.uuid4()}.json"
            with open(input_file, 'w') as f:
                json.dump(data, f)
            
            # 컨테이너 실행
            container = self.docker_client.containers.run(
                image,
                command=f"python analyze.py {input_file}",
                volumes={'/tmp': {'bind': '/data', 'mode': 'rw'}},
                detach=True
            )
            
            # 결과 대기 (timeout)
            result = container.wait(timeout=timeout)
            output = container.logs()
            
            # 결과 파싱
            return json.loads(output)
            
        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            # Fallback to simple analysis
            return self.simple_analysis(data)
    
    def simple_analysis(self, data: Dict):
        """Docker 실패 시 간단한 분석 수행"""
        # 기본 규칙 기반 분석
        return {
            "status": "fallback",
            "result": "basic_analysis",
            "confidence": 0.7
        }
```

### Mock Server 확장 (Goals 2-4)

```python
# Mock Server에 추가할 엔드포인트

@app.route('/api/products/<product_id>/sensor-data', methods=['GET'])
def get_product_sensor_data(product_id):
    """제품 센서 데이터 조회 (Goal 2)"""
    timepoint = request.args.get('timepoint', 'T4')
    sensor_data_id = f"urn:aas:sm:{product_id}:SensorData"
    
    data = server.get_submodel_at_time(sensor_data_id, timepoint)
    if data:
        return jsonify(data)
    return jsonify({"error": "Sensor data not found"}), 404

@app.route('/api/machines/<machine_id>/current-job', methods=['GET'])
def get_current_job(machine_id):
    """현재 작업 조회 (Goal 3)"""
    job_id = f"urn:aas:sm:{machine_id}:CurrentJob"
    job = server.get_latest_submodel(job_id)
    
    if job:
        return jsonify(job)
    return jsonify({"error": "No current job"}), 404

@app.route('/api/products/<product_id>/location', methods=['GET'])
def get_product_location(product_id):
    """제품 위치 조회 (Goal 4)"""
    include_history = request.args.get('history', 'false').lower() == 'true'
    
    tracking_id = f"urn:aas:sm:{product_id}:TrackingInfo"
    current = server.get_latest_submodel(tracking_id)
    
    result = {
        "product_id": product_id,
        "current_location": current
    }
    
    if include_history:
        history = []
        for tp in ["T1", "T2", "T3", "T4", "T5"]:
            location = server.get_submodel_at_time(tracking_id, tp)
            if location:
                history.append({
                    "timepoint": tp,
                    "location": location
                })
        result["history"] = history
    
    return jsonify(result)
```

### 테스트 시나리오

#### Goal 2 테스트
```python
# test_goal2.py
def test_goal2_anomaly_detection():
    executor = ExecutionPlanner()
    
    result = executor.execute_goal({
        "goal": "detect_anomaly",
        "parameters": {
            "product_id": "Product-B1",
            "timepoint": "T4"
        }
    })
    
    assert result["anomalies_detected"] == True
    assert result["confidence"] > 0.9
    assert "temperature_spike" in result["anomaly_points"]
```

#### Goal 3 테스트
```python
# test_goal3.py
def test_goal3_completion_prediction():
    executor = ExecutionPlanner()
    
    result = executor.execute_goal({
        "goal": "predict_completion",
        "parameters": {
            "job_id": "JOB-005",
            "machine_id": "CNC001"
        }
    })
    
    assert "predicted_completion" in result
    assert result["current_progress"] == 65
    assert result["confidence_interval"][0] < result["predicted_completion"]
```

#### Goal 4 테스트
```python
# test_goal4.py
def test_goal4_product_tracking():
    executor = ExecutionPlanner()
    
    result = executor.execute_goal({
        "goal": "track_product",
        "parameters": {
            "product_id": "Product-B1",
            "include_history": True
        }
    })
    
    assert result["current_location"]["station"] == "CNC001"
    assert len(result["location_history"]) == 5
    assert result["status"] == "PROCESSING"
```

### 구현 우선순위

1. **Phase 1: Goal 4 (가장 간단)**
   - AAS Submodel 확장 (TrackingInfo)
   - Mock Server 엔드포인트 추가
   - 위치 추적 로직 구현
   - 테스트 작성

2. **Phase 2: Goal 2 (중간 복잡도)**
   - SensorData Submodel 추가
   - 이상 감지 로직 (규칙 기반)
   - Docker 컨테이너 시뮬레이션
   - 테스트 및 검증

3. **Phase 3: Goal 3 (가장 복잡)**
   - CurrentJob Submodel
   - 예측 모델 시뮬레이션
   - 이력 데이터 분석
   - 통합 테스트

### 예상 일정
- Goal 4: 1일 (위치 추적)
- Goal 2: 2일 (이상 감지)
- Goal 3: 2일 (완료 시간 예측)
- 통합 테스트: 1일
- 문서화: 1일

**총 예상 기간**: 1주일

---

**작성일**: 2025-08-06  
**버전**: v6 Goals 2-4 구현 계획  
**상태**: Goal 1 완료, Goals 2-4 계획 수립 완료