# SPARQL 쿼리 실행 테스트 결과

## 개요
v3 버전에서는 AAS 테스트 데이터(TTL 형식)를 로드하고 실제 SPARQL 쿼리를 실행하여 결과를 확인하는 기능을 구현했습니다.

## 테스트 데이터 로드
- 총 705개의 트리플 로드 완료
  - `static/machines-static.ttl`: 144 트리플
  - `static/products-static.ttl`: 216 트리플
  - `snapshot/operational-snapshot-20250717.ttl`: 156 트리플
  - `historical/job-history-20250717.ttl`: 189 트리플

## 테스트 결과

### Goal 1: 냉각이 필요한 실패한 작업 조회
**입력:**
```json
{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-07-17"
}
```

**SPARQL 쿼리:**
```sparql
SELECT ?job ?machine ?startTime ?status
WHERE {
    ?job rdf:type prod:Job .
    ?job prod:hasStartTime ?startTime .
    ?job prod:hasStatus ?status .
    ?job prod:requiresCooling true .
    FILTER(?status = "Failed")
    FILTER(STRSTARTS(STR(?startTime), "2025-07-17"))
    OPTIONAL { ?job prod:executedOn ?machine }
}
ORDER BY DESC(?startTime)
```

**결과: 3개 레코드 조회 성공**
1. Job-2003 | CoolingMachine-04 | 2025-07-17T11:30:00 | Failed
2. Job-2002 | CoolingMachine-02 | 2025-07-17T09:15:00 | Failed
3. Job-2001 | CoolingMachine-01 | 2025-07-17T08:00:00 | Failed

### Goal 2: 제품 이상 감지
**입력:**
```json
{
  "goal": "detect_anomaly_for_product",
  "product_id": "Product-A1",
  "date_range": {
    "start": "2025-07-17T00:00:00",
    "end": "2025-07-17T23:59:59"
  },
  "target_machine": "CoolingMachine-01"
}
```

**SPARQL 쿼리:**
```sparql
SELECT ?job ?machine ?startTime ?status
WHERE {
    ?job rdf:type prod:Job .
    ?job prod:forProduct prod:Product-A1 .
    ?job prod:executedOn ?machine .
    ?job prod:hasStartTime ?startTime .
    ?job prod:hasStatus ?status .
    FILTER(?startTime >= "2025-07-17T00:00:00"^^xsd:dateTime)
    FILTER(?startTime <= "2025-07-17T23:59:59"^^xsd:dateTime)
}
ORDER BY ?startTime
```

**결과: 1개 레코드 조회 성공**
- Job-2001 | CoolingMachine-01 | 2025-07-17T08:00:00 | Failed

### Goal 3: 첫 완료 시간 예측
**입력:**
```json
{
  "goal": "predict_first_completion_time",
  "product_id": "Product-B2",
  "quantity": 100
}
```

**SPARQL 쿼리:**
```sparql
SELECT ?operation ?machine ?duration
WHERE {
    prod:Product-B2 prod:hasJobTemplate ?template .
    ?template prod:hasOperation ?operation .
    ?operation prod:canBeExecutedOn ?machine ;
              prod:hasDuration ?duration .
}
```

**결과: 0개 레코드**
- 현재 테스트 데이터에 Product-B2의 JobTemplate 정보가 없음

### Goal 4: 제품 위치 추적
**입력:**
```json
{
  "goal": "track_product_position",
  "product_id": "Product-C1"
}
```

**SPARQL 쿼리:**
```sparql
SELECT ?job ?status ?machine ?opIndex
WHERE {
    ?job rdf:type prod:Job .
    ?job prod:forProduct prod:Product-C1 .
    ?job prod:hasStatus "Processing" .
    ?job prod:executedOn ?machine .
    OPTIONAL { ?job prod:currentOperationIndex ?opIndex }
}
```

**결과: 1개 레코드 조회 성공**
- Job-2008 | HeatingMachine-02 | opIndex: 2

## 주요 성과

1. **SPARQL 쿼리 실행 통합**: 온톨로지 기반 실행 계획에 실제 SPARQL 쿼리 실행 기능 추가
2. **AAS 테스트 데이터 활용**: TTL 형식의 테스트 데이터를 로드하여 실제 쿼리 가능
3. **파라미터 치환 기능**: 쿼리 템플릿의 플레이스홀더를 DSL 입력값으로 동적 치환
4. **결과 시각화**: 쿼리 결과를 구조화된 형태로 실행 계획에 포함

## 개선 사항

1. **Goal 3 테스트 데이터 보완**: Product-B2의 JobTemplate 정보 추가 필요
2. **쿼리 최적화**: 복잡한 조인이나 집계 함수를 사용하는 고급 쿼리 템플릿 추가 가능
3. **실시간 데이터 연동**: 정적 TTL 파일 대신 실제 AAS 서버와 연동 가능

## 결론

v3 버전은 성공적으로 SPARQL 쿼리를 실행하고 실제 데이터를 조회할 수 있음을 확인했습니다. 4개 목표 중 3개에서 유의미한 결과를 얻었으며, Goal 3의 경우 테스트 데이터 보완이 필요합니다.