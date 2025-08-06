# CLAUDE.md - AAS Integration v6: 온톨로지 기반 통합 오케스트레이션 시스템

## 🎯 프로젝트 비전: "나침반" 시스템

### 핵심 컨셉
온톨로지는 전체 시스템의 **"나침반"**입니다. 사용자의 의도부터 최종 결과까지 모든 과정을 안내하고 지휘합니다.

```
사용자 의도 → [온톨로지 나침반] → 실행 계획 → 데이터 수집 → 처리 → 결과
                     ↑
              "무엇을, 어디서, 어떻게"
```

### 나침반의 역할
1. **의도 해석**: 사용자 DSL 입력을 이해하고 목표(Goal) 매핑
2. **경로 안내**: 목표 달성을 위한 단계별 실행 계획 수립
3. **자원 파악**: 필요한 데이터가 어디에 있는지 파악
4. **방법 제시**: 데이터를 어떻게 가져오고 처리할지 결정
5. **대안 제공**: 실패 시 폴백 전략 제시
6. **통합 지휘**: 여러 소스의 데이터를 통합하여 결과 생성

---

## 📊 제조 도메인 데이터 계층 구조

### 1. Scenario (생산 시나리오)
**정의**: 특정 제품을 목표 수량만큼 생산하기 위한 전체 계획

```yaml
Scenario:
  id: "SCENARIO-2025-001"
  description: "Widget 1000개 생산"
  product: "PART-N-WIDGET"
  target_quantity: 1000
  deadline: "2025-08-01T00:00:00"
  priority: "HIGH"
  jobs: [JOB-001, JOB-002, ..., JOB-100]
  constraints:
    - max_parallel_jobs: 5
    - required_quality_level: 0.99
  estimated_completion: "2025-07-28T15:30:00"
```

### 2. Part (제품/부품)
**정의**: 생산되는 제품 또는 부품의 사양 및 요구사항

```yaml
Part:
  id: "PART-N-WIDGET"
  name: "Advanced Widget Model N"
  type: "ASSEMBLY"
  version: "3.2.1"
  
  bill_of_materials:
    - component: "COMP-A-FRAME"
      quantity: 1
    - component: "COMP-B-CIRCUIT"
      quantity: 2
    - component: "COMP-C-SENSOR"
      quantity: 4
  
  manufacturing_requirements:
    requires_cooling: true
    temperature_range:
      min: 15
      max: 25
      unit: "celsius"
    humidity_range:
      min: 30
      max: 60
      unit: "percent"
    clean_room_level: "ISO-7"
  
  quality_specifications:
    tolerance: 0.01
    inspection_points: ["dimensional", "electrical", "thermal"]
    certification_required: ["CE", "UL"]
  
  operations_sequence:
    - "OP-CUTTING"
    - "OP-COOLING"
    - "OP-ASSEMBLY"
    - "OP-TESTING"
    - "OP-PACKAGING"
```

### 3. Job (작업)
**정의**: 하나의 제품을 생산하기 위한 작업 단위

```yaml
Job:
  id: "JOB-001"
  scenario: "SCENARIO-2025-001"
  product: "PART-N-WIDGET"
  batch_size: 10
  priority: "NORMAL"
  
  status: "IN_PROGRESS"
  progress: 60  # percent
  
  timeline:
    scheduled_start: "2025-07-17T08:00:00"
    actual_start: "2025-07-17T08:15:00"
    estimated_end: "2025-07-17T16:00:00"
    actual_end: null
  
  operations:
    - operation_instance: "JOB-001-OP-001"
      operation_type: "OP-CUTTING"
      status: "COMPLETED"
    - operation_instance: "JOB-001-OP-002"
      operation_type: "OP-COOLING"
      status: "FAILED"
    - operation_instance: "JOB-001-OP-003"
      operation_type: "OP-ASSEMBLY"
      status: "PENDING"
  
  assigned_resources:
    machines: ["CNC001", "COOL001", "ASM001"]
    operators: ["OP-JOHN", "OP-JANE"]
    tools: ["TOOL-SET-A"]
  
  quality_metrics:
    defect_rate: 0.02
    rework_count: 1
    inspection_passed: false
  
  failure_log:
    - timestamp: "2025-07-17T10:30:00"
      operation: "OP-COOLING"
      reason: "cooling_system_error"
      error_code: "ERR-COOL-001"
      recovery_action: "manual_intervention"
```

### 4. Operation (공정)
**정의**: Job 내의 개별 작업 단계

```yaml
Operation:
  id: "JOB-001-OP-002"
  type: "OP-COOLING"
  job: "JOB-001"
  sequence: 2
  
  machine_assignment:
    required_capability: "COOLING"
    assigned_machine: "COOL001"
    alternative_machines: ["COOL002", "COOL003"]
  
  parameters:
    target_temperature: 20
    cooling_rate: 5  # degrees/minute
    hold_time: 30  # minutes
    coolant_type: "WATER"
    flow_rate: 10  # liters/minute
  
  execution:
    status: "FAILED"
    start_time: "2025-07-17T10:00:00"
    end_time: "2025-07-17T10:30:00"
    duration: 30  # minutes
    
  sensor_data:
    temperature_readings: [25, 24, 23, 22, 21, 20, 19, 18, 25, 30]  # spike at end
    pressure_readings: [1.0, 1.0, 1.0, 0.9, 0.8, 0.5, 0.3, 0.1, 0.0, 0.0]
    flow_rate_readings: [10, 10, 10, 9, 8, 5, 2, 0, 0, 0]
  
  failure_details:
    failure_mode: "coolant_pump_failure"
    root_cause: "pump_bearing_wear"
    detection_method: "pressure_sensor_alert"
    impact: "temperature_overshoot"
    corrective_action: "pump_replacement"
```

### 5. Machine (기계/장비)
**정의**: 생산에 사용되는 기계 및 장비

```yaml
Machine:
  id: "CNC001"
  name: "DMG MORI DMU 50"
  type: "CNC_MILLING"
  
  capabilities:
    - "CUTTING"
    - "DRILLING"
    - "MILLING"
  
  specifications:
    power: 15.5  # kW
    weight: 3500  # kg
    workspace:
      x: 500  # mm
      y: 450  # mm
      z: 400  # mm
    spindle_speed:
      min: 20
      max: 12000  # rpm
    tool_capacity: 20
  
  operational_requirements:
    requires_cooling: true
    power_supply: "3-phase-400V"
    compressed_air: true
    maintenance_interval: 500  # hours
  
  current_status:
    state: "IDLE"
    health: 85  # percent
    utilization: 0.75  # last 24 hours
    last_maintenance: "2025-07-01"
    next_maintenance: "2025-08-01"
    total_operating_hours: 4523
  
  current_job: null
  job_queue: []
  
  performance_metrics:
    mtbf: 720  # hours (Mean Time Between Failures)
    mttr: 2    # hours (Mean Time To Repair)
    oee: 0.85  # Overall Equipment Effectiveness
    quality_rate: 0.98
    performance_rate: 0.92
    availability_rate: 0.94
```

---

## 🗺️ 온톨로지 구조: 4개 레이어

### Layer 1: Domain Ontology (도메인 온톨로지)
**역할**: 제조 도메인의 개념과 관계 정의 (WHAT)

```turtle
# domain-ontology.ttl
prod:Scenario
    prod:hasProduct prod:Part ;
    prod:generatesJobs prod:Job ;
    prod:hasDeadline xsd:dateTime ;
    prod:hasTargetQuantity xsd:integer .

prod:Part
    prod:hasBOM prod:Component ;
    prod:requiresOperations prod:OperationType ;
    prod:hasManufacturingRequirements prod:Requirement .

prod:Job
    prod:belongsToScenario prod:Scenario ;
    prod:producesProduct prod:Part ;
    prod:consistsOfOperations prod:Operation ;
    prod:executedOnMachines prod:Machine .

prod:Operation
    prod:hasSequence xsd:integer ;
    prod:requiresCapability prod:Capability ;
    prod:hasParameters prod:OperationParameter ;
    prod:generatesData prod:SensorData .

prod:Machine
    prod:providesCapability prod:Capability ;
    prod:hasOperationalStatus prod:Status ;
    prod:executesOperations prod:Operation .
```

### Layer 2: Execution Ontology (실행 온톨로지)
**역할**: 실행 방법과 액션 정의 (HOW)

```turtle
# execution-ontology.ttl
exec:Goal
    exec:requiresActions exec:Action ;
    exec:hasExecutionPlan exec:ExecutionPlan ;
    exec:producesResult exec:Result .

exec:Action
    exec:hasType exec:ActionType ;
    exec:requiresInput exec:DataRequirement ;
    exec:hasExecutionOrder xsd:integer ;
    exec:hasTimeout xsd:duration .

exec:ActionType
    owl:oneOf (
        exec:DataQuery      # 데이터 조회
        exec:DataTransform  # 데이터 변환
        exec:ExternalCall   # 외부 서비스 호출
        exec:Computation    # 계산/처리
        exec:Integration    # 데이터 통합
    ) .

exec:ExecutionPlan
    exec:hasSteps exec:ExecutionStep ;
    exec:hasDataFlow exec:DataFlow ;
    exec:hasErrorHandling exec:ErrorStrategy .
```

### Layer 3: Data Source Ontology (데이터 소스 온톨로지)
**역할**: 데이터 위치와 접근 방법 정의 (WHERE)

```turtle
# data-source-ontology.ttl
ds:DataSource
    ds:providesDataType prod:DataType ;
    ds:hasAccessMethod ds:AccessMethod ;
    ds:hasEndpoint xsd:string ;
    ds:hasFallback ds:DataSource .

ds:AccessMethod
    owl:oneOf (
        ds:REST_API
        ds:SPARQL_QUERY
        ds:FILE_READ
        ds:CONTAINER_EXEC
        ds:STREAMING
    ) .

ds:DataMapping
    ds:fromSource ds:DataSource ;
    ds:toTarget exec:DataRequirement ;
    ds:hasTransformation ds:TransformationRule .
```

### Layer 4: Bridge Ontology (브리지 온톨로지)
**역할**: DSL과 실행을 연결 (MAPPING)

```turtle
# bridge-ontology.ttl
bridge:DSLGoal
    bridge:mapsToExecutionGoal exec:Goal ;
    bridge:hasParameterMapping bridge:ParameterMap ;
    bridge:hasResultMapping bridge:ResultMap .

bridge:ParameterMap
    bridge:fromDSLParam bridge:DSLParameter ;
    bridge:toExecParam exec:Parameter ;
    bridge:hasTransformation bridge:Transform .
```

---

## 🔄 실행 계획 생성 프로세스

### Phase 1: 의도 분석 (Intent Analysis)
```python
DSL Input: {
    "goal": "query_failed_jobs_with_cooling",
    "parameters": {
        "date": "2025-07-17",
        "product_filter": "requires_cooling"
    }
}
    ↓
온톨로지 쿼리:
    "이 goal은 어떤 실행 목표와 매핑되는가?"
    ↓
Execution Goal: exec:QueryFailedCoolingJobs
```

### Phase 2: 실행 계획 수립 (Planning)
```python
온톨로지 쿼리:
    "이 Goal을 달성하기 위해 필요한 Action들은?"
    ↓
Actions:
    1. exec:IdentifyCoolingProducts (SPARQL)
    2. exec:GetMachineCapabilities (AAS API)
    3. exec:QueryJobHistory (SPARQL + AAS)
    4. exec:FilterFailedJobs (In-memory)
    5. exec:AnalyzeFailurePatterns (Docker AI)
    6. exec:GenerateReport (Integration)
```

### Phase 3: 데이터 요구사항 파악 (Data Requirements)
```python
각 Action별 필요 데이터:
    Action 1: Product specifications (cooling requirements)
    Action 2: Machine capabilities and status
    Action 3: Job execution history
    Action 4: Failure criteria
    Action 5: Sensor data for AI analysis
    Action 6: All previous results
```

### Phase 4: 데이터 소스 결정 (Source Selection)
```python
온톨로지 쿼리:
    "각 데이터는 어디서 가져올 수 있는가?"
    ↓
Data Sources:
    Product specs: SPARQL (primary) → Local TTL (fallback)
    Machine data: AAS API (primary) → Mock Server (fallback)
    Job history: AAS Submodel → SPARQL → Local cache
    Sensor data: S3 TimeSeries → AAS API → Local files
```

### Phase 5: 실행 흐름 구성 (Execution Flow)
```yaml
ExecutionPlan:
  goal: "QueryFailedCoolingJobs"
  total_steps: 6
  estimated_duration: "PT5M"  # 5 minutes
  
  steps:
    - step: 1
      action: "IdentifyCoolingProducts"
      method: "SPARQL"
      source: "LocalTTL"  # Fuseki not available, using fallback
      query: |
        SELECT ?product ?cooling WHERE {
          ?product a prod:Part ;
                   prod:requiresCooling ?cooling .
          FILTER(?cooling = true)
        }
      output: "cooling_products_list"
      
    - step: 2
      action: "GetMachineCapabilities"
      method: "REST_API"
      source: "MockAASServer"
      endpoint: "/api/machines/cooling-required"
      output: "cooling_machines_list"
      
    - step: 3
      action: "QueryJobHistory"
      method: "PARALLEL"  # 병렬 실행
      sources:
        - type: "REST_API"
          endpoint: "/shells/{machine_id}/submodels/JobHistory"
        - type: "SPARQL"
          query: "SELECT ?job WHERE { ?job prod:hasDate '2025-07-17' }"
      output: "all_jobs_data"
      
    - step: 4
      action: "FilterFailedJobs"
      method: "IN_MEMORY"
      input: ["cooling_products_list", "cooling_machines_list", "all_jobs_data"]
      filter_criteria:
        - "job.status == 'FAILED'"
        - "job.product IN cooling_products_list"
        - "job.machine IN cooling_machines_list"
      output: "failed_cooling_jobs"
      
    - step: 5
      action: "AnalyzeFailurePatterns"
      method: "DOCKER"
      container: "anomaly-detector:latest"
      input: 
        jobs: "failed_cooling_jobs"
        sensor_data: "FROM_S3"
      model: "failure_pattern_lstm"
      output: "failure_analysis"
      
    - step: 6
      action: "GenerateReport"
      method: "INTEGRATION"
      input: ["failed_cooling_jobs", "failure_analysis"]
      format: "structured_json"
      output: "final_report"
```

---

## 🔌 다중 데이터 소스 통합 전략

### 1. 병렬 데이터 수집 (Parallel Collection)
```python
# 여러 소스에서 동시에 데이터 수집
async def collect_data_parallel():
    tasks = [
        aas_client.get_machines(),      # AAS API
        sparql_client.query_products(), # SPARQL
        s3_client.get_sensor_data(),    # S3
        local_db.get_job_history()      # Local
    ]
    results = await asyncio.gather(*tasks)
    return integrate_results(results)
```

### 2. 계층적 폴백 (Hierarchical Fallback)
```python
# 각 데이터 소스별 독립적 폴백
DataSourceHierarchy:
  MachineData:
    1. Live AAS Server (http://production-aas:8080)
    2. Mock AAS Server (http://localhost:5001)
    3. Local JSON Cache (./cache/machines.json)
    4. Static Default Data
    
  JobHistory:
    1. SPARQL Endpoint (http://fuseki:3030)
    2. AAS Submodel API
    3. Local TTL Files
    4. Emergency CSV Backup
```

### 3. 데이터 일관성 보장 (Consistency)
```yaml
ConsistencyRules:
  - TimestampAlignment: "모든 데이터를 동일 시점으로 정렬"
  - VersionMatching: "스키마 버전 호환성 검증"
  - ReferenceIntegrity: "ID 참조 무결성 확인"
  - ConflictResolution: "충돌 시 우선순위 규칙 적용"
```

---

## 🐳 외부 실행 환경 정의

### 1. Docker 컨테이너 실행
```yaml
Containers:
  ProductionSimulator:
    image: "production-simulator:latest"
    purpose: "제조 공정 시뮬레이션"
    input:
      - scenario_definition
      - machine_status
      - job_queue
    output:
      - execution_timeline
      - resource_utilization
      - bottleneck_analysis
    resources:
      cpu: 2
      memory: "4Gi"
      timeout: "300s"
  
  AnomalyDetector:
    image: "anomaly-detector:latest"
    purpose: "이상 패턴 감지"
    input:
      - sensor_timeseries
      - job_history
      - machine_logs
    output:
      - anomaly_scores
      - root_cause_analysis
      - predictive_alerts
    model:
      type: "LSTM_Autoencoder"
      version: "2.3.1"
      accuracy: 0.94
  
  CompletionPredictor:
    image: "completion-predictor:latest"
    purpose: "완료 시간 예측"
    input:
      - job_template
      - machine_schedule
      - historical_performance
    output:
      - predicted_completion_time
      - confidence_interval
      - risk_factors
```

### 2. AWS Lambda 함수
```yaml
LambdaFunctions:
  QuickCalculation:
    arn: "arn:aws:lambda:us-east-1:123456789:function:quick-calc"
    purpose: "간단한 계산 작업"
    max_duration: "15s"
    
  DataTransformation:
    arn: "arn:aws:lambda:us-east-1:123456789:function:data-transform"
    purpose: "데이터 형식 변환"
    max_duration: "60s"
```

### 3. Kubernetes Jobs
```yaml
K8sJobs:
  BatchProcessing:
    namespace: "production"
    job_template: "batch-processor"
    purpose: "대용량 배치 처리"
    parallelism: 10
    completions: 100
```

---

## 🎮 시스템 통합 아키텍처

### 전체 흐름도
```
┌─────────────┐
│  사용자 DSL  │
└──────┬──────┘
       ↓
┌──────────────────────────────────────┐
│         온톨로지 나침반                │
│  ┌──────────┐  ┌──────────┐          │
│  │의도 분석  │→│실행 계획  │          │
│  └──────────┘  └──────────┘          │
│       ↓              ↓                │
│  ┌──────────┐  ┌──────────┐          │
│  │데이터요구 │→│소스 결정  │          │
│  └──────────┘  └──────────┘          │
└──────────────────┬───────────────────┘
                   ↓
    ┌──────────────┴──────────────┐
    ↓              ↓              ↓
┌────────┐    ┌────────┐    ┌────────┐
│AAS API │    │ SPARQL │    │   S3   │
└────────┘    └────────┘    └────────┘
    ↓              ↓              ↓
    └──────────────┬──────────────┘
                   ↓
         ┌─────────────────┐
         │  데이터 통합     │
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │  외부 처리       │
         │ (Docker/Lambda) │
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │   최종 결과      │
         └─────────────────┘
```

### 핵심 컴포넌트
```python
class OntologyNavigator:
    """온톨로지 기반 나침반 시스템"""
    
    def __init__(self):
        # 4개 레이어 온톨로지
        self.domain_ontology = DomainOntology()
        self.execution_ontology = ExecutionOntology()
        self.datasource_ontology = DataSourceOntology()
        self.bridge_ontology = BridgeOntology()
        
        # 실행 컴포넌트
        self.planner = ExecutionPlanner()
        self.data_collector = MultiSourceCollector()
        self.external_executor = ExternalExecutor()
        self.result_integrator = ResultIntegrator()
    
    def navigate(self, user_intent):
        """사용자 의도부터 결과까지 안내"""
        # 1. 의도 → Goal
        goal = self.bridge_ontology.map_intent_to_goal(user_intent)
        
        # 2. Goal → Plan
        plan = self.execution_ontology.generate_plan(goal)
        
        # 3. Plan → Data Collection
        data = self.datasource_ontology.collect_required_data(plan)
        
        # 4. Data → Processing
        processed = self.external_executor.process(data, plan)
        
        # 5. Processing → Result
        result = self.result_integrator.integrate(processed)
        
        return result
```

---

## 📈 성공 지표

### 기술적 지표
- **응답 시간**: < 5초 (95 percentile)
- **데이터 정확도**: > 99%
- **시스템 가용성**: > 99.9%
- **폴백 성공률**: > 95%

### 비즈니스 지표
- **생산 효율성 향상**: 20%
- **장애 예측 정확도**: 85%
- **다운타임 감소**: 30%
- **품질 개선**: 15%

---

## 🚀 구현 로드맵

### Phase 1: 기반 구축 (2주)
- [ ] 온톨로지 파일 완성
- [ ] 데이터 모델 정의
- [ ] 기본 실행 엔진

### Phase 2: 통합 구현 (3주)
- [ ] 다중 소스 어댑터
- [ ] 실행 계획 생성기
- [ ] 폴백 메커니즘

### Phase 3: 외부 연동 (2주)
- [ ] Docker 컨테이너 통합
- [ ] AI 모델 연동
- [ ] 실시간 데이터 스트리밍

### Phase 4: 최적화 (2주)
- [ ] 성능 튜닝
- [ ] 캐싱 전략
- [ ] 모니터링 대시보드

### Phase 5: 검증 (1주)
- [ ] 통합 테스트
- [ ] 성능 벤치마크
- [ ] 문서화

---

## 📝 핵심 차별점

### v5와의 차이
1. **온톨로지 중심**: 하드코딩 제거, 모든 것이 온톨로지 기반
2. **계층 구조**: Scenario → Part → Job → Operation 명확한 정의
3. **다중 소스**: 단일 AAS가 아닌 여러 데이터 소스 통합
4. **외부 처리**: Docker/Lambda를 통한 확장 가능한 처리
5. **나침반 역할**: 온톨로지가 전체 프로세스를 안내

### 핵심 혁신
- **동적 실행**: 온톨로지 변경만으로 동작 변경 가능
- **확장성**: 새로운 Goal, Action, DataSource 쉽게 추가
- **복원력**: 계층적 폴백으로 높은 가용성
- **지능화**: AI 모델 통합으로 예측 및 최적화

---

## 🎯 4개 Goal 상세 구현 계획

### Goal 1: 냉각 실패 작업 조회 (query_failed_jobs_with_cooling)

#### 정보 요구사항
```yaml
Required Data:
  1. Cooling Products:
     - What: 냉각이 필요한 제품 목록
     - Where: In-memory SPARQL (products.ttl)
     - How: SPARQL Query
     - Schema: {product_id, name, requires_cooling, temperature_range}
  
  2. Cooling Machines:
     - What: 냉각 기능이 있는 기계 목록
     - Where: Mock AAS Server
     - How: REST API GET /api/machines/cooling-required
     - Schema: {machine_id, name, capability: "COOLING", status}
  
  3. Job History:
     - What: 특정 날짜의 작업 이력
     - Where: Mock AAS Server + In-memory TTL
     - How: GET /shells/{machine}/submodels/JobHistory
     - Schema: {job_id, product_id, machine_id, status, date, failure_reason}

Output Format:
  - failed_jobs: [{job_id, product, machine, failure_reason, timestamp}]
  - summary: {total_failed, cooling_related, date_range}
```

#### 온톨로지 액션 시퀀스
```turtle
exec:Goal1_QueryFailedCoolingJobs
    exec:step1 exec:QueryCoolingProducts ;
    exec:step2 exec:FetchCoolingMachines ;
    exec:step3 exec:CollectJobHistory ;
    exec:step4 exec:FilterFailedJobs ;
    exec:step5 exec:GenerateReport .
```

### Goal 2: 제품 이상 감지 (detect_anomaly_for_product)

#### 정보 요구사항
```yaml
Required Data:
  1. Product Manufacturing History:
     - What: 특정 제품의 제조 이력
     - Where: Mock AAS Server
     - How: GET /shells/Product-{id}/submodels/ManufacturingHistory
     - Schema: {product_id, operations: [{timestamp, values}]}
  
  2. Sensor Time Series:
     - What: 센서 시계열 데이터
     - Where: Local Files (시뮬레이션)
     - How: File read from ./timeseries/{date}/{product}.json
     - Schema: {timestamp, temperature, pressure, vibration}
  
  3. Normal Pattern Baseline:
     - What: 정상 패턴 기준값
     - Where: In-memory SPARQL
     - How: SPARQL Query
     - Schema: {metric, min, max, mean, std_dev}

Container Execution:
  - Image: anomaly-detector:latest
  - Input: {sensor_data, baseline, threshold: 0.85}
  - Output: {anomaly_score, detected_anomalies: [{timestamp, metric, score}]}
```

#### 온톨로지 액션 시퀀스
```turtle
exec:Goal2_DetectAnomalyForProduct
    exec:step1 exec:FetchProductHistory ;
    exec:step2 exec:LoadSensorData ;
    exec:step3 exec:QueryNormalBaseline ;
    exec:step4 exec:RunAnomalyDetection ;  # Docker container
    exec:step5 exec:InterpretResults .
```

### Goal 3: 완료 시간 예측 (predict_first_completion_time)

#### 정보 요구사항
```yaml
Required Data:
  1. Job Template:
     - What: 제품의 표준 작업 템플릿
     - Where: Mock AAS Server
     - How: GET /shells/Product-{id}/submodels/JobTemplate
     - Schema: {operations: [{name, duration, machine_type, sequence}]}
  
  2. Machine Schedule:
     - What: 기계 일정 및 가용성
     - Where: Mock AAS Server
     - How: GET /api/machines/schedule
     - Schema: {machine_id, current_job, queue: [], availability}
  
  3. Historical Performance:
     - What: 과거 수행 시간 통계
     - Where: In-memory SPARQL
     - How: SPARQL Query
     - Schema: {operation, avg_duration, min, max, variance}

Container Execution:
  - Image: production-simulator:latest
  - Input: {job_template, machine_schedule, quantity, constraints}
  - Output: {predicted_completion, confidence, critical_path, bottlenecks}
```

#### 온톨로지 액션 시퀀스
```turtle
exec:Goal3_PredictCompletionTime
    exec:step1 exec:FetchJobTemplate ;
    exec:step2 exec:CheckMachineSchedule ;
    exec:step3 exec:AnalyzeHistoricalData ;
    exec:step4 exec:RunSimulation ;  # Docker container
    exec:step5 exec:CalculatePrediction .
```

### Goal 4: 제품 위치 추적 (track_product_position)

#### 정보 요구사항
```yaml
Required Data:
  1. Product Shell:
     - What: 제품 AAS Shell 정보
     - Where: Mock AAS Server
     - How: GET /shells/Product-{id}
     - Schema: {product_id, current_status, last_updated}
  
  2. Current Operation:
     - What: 현재 진행 중인 작업
     - Where: Mock AAS Server
     - How: GET /shells/Product-{id}/submodels/CurrentOperation
     - Schema: {operation_id, type, machine_id, progress}
  
  3. Location Info:
     - What: 물리적 위치 정보
     - Where: In-memory SPARQL or AAS
     - How: Query or API call
     - Schema: {location_type, coordinates, zone, machine_id}

Output Format:
  - current_position: {zone, machine, coordinates}
  - status: {operation, progress, estimated_remaining}
  - history: [{timestamp, location, operation}]
```

#### 온톨로지 액션 시퀀스
```turtle
exec:Goal4_TrackProductPosition
    exec:step1 exec:FetchProductShell ;
    exec:step2 exec:GetCurrentOperation ;
    exec:step3 exec:QueryLocationInfo ;
    exec:step4 exec:CompileTrackingData ;
    exec:step5 exec:FormatResponse .
```

---

## 🐳 컨테이너 실행 모듈 설계

### 기본 구조
```python
# container_executor.py

class ContainerExecutor:
    """외부 컨테이너 실행 모듈"""
    
    def __init__(self):
        self.docker_client = None  # Docker SDK client
        self.available_images = {
            'anomaly-detector': 'anomaly-detector:latest',
            'production-simulator': 'production-simulator:latest',
            'completion-predictor': 'completion-predictor:latest'
        }
    
    def execute_container(self, 
                         container_type: str,
                         input_data: Dict[str, Any],
                         timeout: int = 300) -> Dict[str, Any]:
        """
        컨테이너 실행 인터페이스
        
        Args:
            container_type: 실행할 컨테이너 타입
            input_data: 컨테이너에 전달할 입력 데이터
            timeout: 실행 제한 시간 (초)
            
        Returns:
            실행 결과 딕셔너리
        """
        
        # 실제 구현은 주석으로 대체
        """
        1. Docker 이미지 확인
        2. 입력 데이터를 JSON으로 직렬화
        3. 컨테이너 실행
        4. 결과 수집
        5. 정리 및 반환
        """
        
        # 테스트용 더미 응답
        print(f"🐳 Executing container: {container_type}")
        print(f"📦 Input data keys: {list(input_data.keys())}")
        
        # 컨테이너별 더미 응답 생성
        if container_type == 'anomaly-detector':
            return self._mock_anomaly_detection(input_data)
        elif container_type == 'production-simulator':
            return self._mock_simulation(input_data)
        else:
            return {"status": "success", "message": f"Container {container_type} executed"}
    
    def _mock_anomaly_detection(self, input_data: Dict) -> Dict:
        """Goal 2용 모의 이상 감지 결과"""
        return {
            "anomaly_score": 0.23,
            "is_anomaly": False,
            "detected_patterns": [
                {"timestamp": "2025-07-17T10:30:00", "metric": "temperature", "score": 0.15},
                {"timestamp": "2025-07-17T11:45:00", "metric": "vibration", "score": 0.31}
            ],
            "confidence": 0.87,
            "message": "No significant anomalies detected"
        }
    
    def _mock_simulation(self, input_data: Dict) -> Dict:
        """Goal 3용 모의 시뮬레이션 결과"""
        import random
        from datetime import datetime, timedelta
        
        # 입력에서 수량 추출
        quantity = input_data.get('quantity', 100)
        
        # 현재 시간 기준으로 완료 예상 시간 계산
        now = datetime.now()
        hours_per_unit = random.uniform(0.5, 1.5)
        completion_time = now + timedelta(hours=hours_per_unit * quantity)
        
        return {
            "predicted_completion": completion_time.isoformat(),
            "confidence_interval": {
                "lower": (completion_time - timedelta(hours=quantity*0.1)).isoformat(),
                "upper": (completion_time + timedelta(hours=quantity*0.1)).isoformat()
            },
            "confidence": 0.82,
            "critical_path": ["Cutting", "Cooling", "Assembly"],
            "bottlenecks": [
                {"resource": "CNC001", "utilization": 0.95},
                {"resource": "COOL001", "utilization": 0.88}
            ],
            "message": f"Simulation completed for {quantity} units"
        }
```

---

## 📊 데이터 소스 접근 방법

### 1. Mock AAS Server (v5 활용)
```python
# v5의 기존 Mock Server 사용
# 포트: 5001
# 엔드포인트:
#   - /shells: 모든 Shell 조회
#   - /shells/{id}: 특정 Shell 조회
#   - /shells/{id}/submodels: Submodel 목록
#   - /api/machines/cooling-required: 냉각 기계 조회
#   - /api/snapshot/{timestamp}: 특정 시점 스냅샷 조회 (추가)
```

### 2. In-memory SPARQL
```python
# sparql_engine.py
from rdflib import Graph, Namespace

class InMemorySPARQL:
    def __init__(self):
        self.graph = Graph()
        self.load_test_data()
    
    def load_test_data(self):
        # TTL 파일 로드
        self.graph.parse("./test-data/products.ttl", format="turtle")
        self.graph.parse("./test-data/jobs.ttl", format="turtle")
    
    def query(self, sparql_query: str) -> List[Dict]:
        # SPARQL 쿼리 실행
        results = self.graph.query(sparql_query)
        return [dict(row) for row in results]
```

---

## 📸 스냅샷 데이터 전략

### 개념
실제 기기 연동 없이 시간에 따른 상태 변화를 표현하기 위한 **시점별 상태 저장** 방식

### 스냅샷 시나리오
```yaml
시나리오: "Widget 100개 생산 중 냉각 실패 발생"

스냅샷 시점:
  T1 (2025-07-17 08:00): 작업 시작
    - JOB-001: PENDING
    - 모든 기계: IDLE
    - 센서: 정상 범위
  
  T2 (2025-07-17 10:00): 정상 작동
    - JOB-001: IN_PROGRESS (30%)
    - CNC001: RUNNING
    - 센서: 온도 22°C, 압력 1.0 bar
  
  T3 (2025-07-17 12:00): 이상 징후
    - JOB-001: IN_PROGRESS (60%)
    - COOL001: WARNING
    - 센서: 온도 28°C (상승), 압력 0.8 bar (하락)
  
  T4 (2025-07-17 14:00): 냉각 실패
    - JOB-001: FAILED
    - COOL001: ERROR
    - 센서: 온도 35°C (과열), 압력 0.3 bar
  
  T5 (2025-07-17 16:00): 복구 후 재시작
    - JOB-002: IN_PROGRESS
    - COOL001: MAINTENANCE
    - 센서: 정상화 진행 중
```

### 스냅샷 데이터 구조
```json
// snapshots/2025-07-17T10:00:00.json
{
  "timestamp": "2025-07-17T10:00:00",
  "scenario": "cooling_failure_scenario",
  "jobs": [
    {
      "id": "JOB-001",
      "product": "Product-B1",
      "status": "IN_PROGRESS",
      "progress": 30,
      "machine": "CNC001",
      "operation": "Cutting"
    }
  ],
  "machines": [
    {
      "id": "CNC001",
      "status": "RUNNING",
      "current_job": "JOB-001",
      "health": 95
    },
    {
      "id": "COOL001",
      "status": "IDLE",
      "health": 85
    }
  ],
  "sensor_data": {
    "CNC001": {
      "temperature": 22.5,
      "pressure": 1.01,
      "vibration": 0.5
    }
  }
}
```

### Goal별 스냅샷 활용

#### Goal 1: 냉각 실패 조회
```python
# T4 시점 스냅샷에서 실패 작업 조회
snapshot = get_snapshot("2025-07-17T14:00:00")
failed_jobs = [j for j in snapshot["jobs"] if j["status"] == "FAILED"]
```

#### Goal 2: 이상 감지
```python
# T2, T3 시점 비교로 이상 패턴 감지
snapshot_t2 = get_snapshot("2025-07-17T10:00:00")
snapshot_t3 = get_snapshot("2025-07-17T12:00:00")
# 온도 상승, 압력 하락 추세 분석
```

#### Goal 3: 완료 시간 예측
```python
# 현재 시점 스냅샷 + 과거 패턴으로 예측
current = get_snapshot("2025-07-17T10:00:00")
# 남은 작업량과 기계 가용성 기반 계산
```

#### Goal 4: 위치 추적
```python
# 특정 시점의 제품 위치 확인
snapshot = get_snapshot("2025-07-17T12:00:00")
location = snapshot["jobs"][0]["machine"]  # CNC001
```

---

## 🔧 통합 실행 엔진 구조

```python
class OntologyNavigator:
    """온톨로지 기반 실행 엔진"""
    
    def __init__(self):
        # 데이터 소스
        self.aas_client = AASClient("http://localhost:5001")
        self.sparql = InMemorySPARQL()
        self.container = ContainerExecutor()
        
        # 온톨로지
        self.ontology = OntologyManager()
    
    def execute(self, dsl_input: Dict) -> Dict:
        # 1. Goal 매핑
        goal = dsl_input['goal']
        
        # 2. 온톨로지에서 실행 계획 조회
        plan = self.ontology.get_execution_plan(goal)
        
        # 3. 단계별 실행
        results = {}
        for step in plan:
            if step.type == "SPARQL":
                results[step.id] = self.sparql.query(step.query)
            elif step.type == "AAS_API":
                results[step.id] = self.aas_client.get(step.endpoint)
            elif step.type == "CONTAINER":
                results[step.id] = self.container.execute(step.container, step.input)
            elif step.type == "FILTER":
                results[step.id] = self.filter_data(results, step.criteria)
        
        # 4. 결과 통합
        return self.integrate_results(results)
```

---

## 📅 구현 우선순위

### Phase 1: 기초 인프라 구축
```yaml
우선순위: HIGH
목표: 온톨로지 기반 실행 가능한 최소 시스템

1. 온톨로지 파일 작성:
   - execution-ontology.ttl: 4개 Goal과 Action 정의
   - domain-ontology.ttl: 제조 도메인 개념
   - bridge-ontology.ttl: DSL 매핑
   
2. 스냅샷 데이터 생성:
   - 5개 시점 스냅샷 JSON 파일
   - 제품/기계 기본 데이터 TTL
   
3. 기본 실행 엔진:
   - OntologyManager: 온톨로지 로드 및 쿼리
   - ExecutionPlanner: 실행 계획 생성
   - DataCollector: 데이터 수집 인터페이스
```

### Phase 2: Mock Server 확장
```yaml
우선순위: HIGH
목표: 스냅샷 기반 데이터 제공

1. 스냅샷 엔드포인트 추가:
   - GET /api/snapshot/{timestamp}
   - GET /api/snapshots/list
   
2. v5 Mock Server 수정:
   - 스냅샷 데이터 로드 기능
   - 시점별 상태 조회 API
```

### Phase 3: Goal 1 구현 (가장 단순)
```yaml
우선순위: HIGH
목표: 전체 파이프라인 검증

1. SPARQL 엔진 구현:
   - 냉각 필요 제품 조회
   
2. AAS Client 구현:
   - 냉각 기계 조회
   - 작업 이력 조회
   
3. 통합 테스트:
   - DSL 입력 → 온톨로지 → 실행 → 결과
```

### Phase 4: Goal 4 구현 (두 번째 단순)
```yaml
우선순위: MEDIUM
목표: 위치 추적 기능

1. 스냅샷 기반 위치 조회
2. 진행 상태 계산
3. 통합 테스트
```

### Phase 5: 컨테이너 통합 준비
```yaml
우선순위: MEDIUM
목표: 외부 실행 환경 구축

1. ContainerExecutor 구현
2. 테스트용 Python 컨테이너 생성
3. Mock 응답 구현
```

### Phase 6: Goal 2, 3 구현
```yaml
우선순위: LOW
목표: 컨테이너 기반 처리

1. Goal 2: 이상 감지 (컨테이너 실행)
2. Goal 3: 시간 예측 (시뮬레이터)
3. 통합 테스트
```

---

## 🚀 즉시 시작할 작업

### 1. 온톨로지 파일 생성 (execution-ontology.ttl)
```turtle
@prefix exec: <http://example.org/execution#> .
@prefix prod: <http://example.org/production#> .

# Goal 1 정의
exec:QueryFailedCoolingJobs
    a exec:Goal ;
    exec:hasStep exec:Step1_QueryProducts ;
    exec:hasStep exec:Step2_GetMachines ;
    exec:hasStep exec:Step3_GetJobs ;
    exec:hasStep exec:Step4_Filter ;
    exec:hasStep exec:Step5_Report .

exec:Step1_QueryProducts
    a exec:Action ;
    exec:actionType "SPARQL" ;
    exec:query "SELECT ?product WHERE { ?product prod:requiresCooling true }" ;
    exec:order 1 .
```

### 2. 스냅샷 데이터 디렉토리 구조
```
v6/
├── ontology/
│   ├── execution-ontology.ttl
│   ├── domain-ontology.ttl
│   └── bridge-ontology.ttl
├── snapshots/
│   ├── 2025-07-17T08:00:00.json  # T1: 시작
│   ├── 2025-07-17T10:00:00.json  # T2: 정상
│   ├── 2025-07-17T12:00:00.json  # T3: 경고
│   ├── 2025-07-17T14:00:00.json  # T4: 실패
│   └── 2025-07-17T16:00:00.json  # T5: 복구
├── test-data/
│   ├── products.ttl
│   ├── machines.ttl
│   └── jobs.ttl
└── src/
    ├── ontology_manager.py
    ├── execution_planner.py
    ├── container_executor.py
    └── main.py
```

### 3. 첫 번째 실행 가능한 코드
```python
# main.py
from ontology_manager import OntologyManager
from execution_planner import ExecutionPlanner

def test_goal1():
    # 1. DSL 입력
    dsl_input = {
        "goal": "query_failed_jobs_with_cooling",
        "parameters": {"date": "2025-07-17"}
    }
    
    # 2. 온톨로지 기반 계획 생성
    manager = OntologyManager()
    planner = ExecutionPlanner(manager)
    plan = planner.create_plan(dsl_input)
    
    # 3. 계획 실행
    result = planner.execute(plan)
    
    print(f"Result: {result}")

if __name__ == "__main__":
    test_goal1()
```

---

**작성일**: 2025-08-06  
**버전**: v6 초기 설계  
**상태**: 구현 우선순위 확정  
**다음 단계**: 온톨로지 파일 작성 → 스냅샷 데이터 생성 → Goal 1 구현