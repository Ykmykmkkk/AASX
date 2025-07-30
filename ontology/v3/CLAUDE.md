# CLAUDE.md - v3 버전 개발 내용

## v3 버전 개요
v3 버전은 AAS(Asset Administration Shell) 테스트 데이터를 활용하여 실제 SPARQL 쿼리를 실행하고 결과를 확인하는 기능을 구현했습니다.

## 주요 변경사항

### 1. SPARQL 쿼리 실행 기능 추가
- `dsl_execution_with_sparql.py`: 기존 execution planner를 확장하여 SPARQL 쿼리 실행 기능 추가
- RDFLib의 내장 SPARQL 엔진을 사용하여 TTL 데이터 직접 쿼리
- 쿼리 템플릿의 파라미터를 DSL 입력값으로 동적 치환

### 2. AAS 테스트 데이터 통합
- TTL 형식의 테스트 데이터 로드 기능 구현
- 4개 카테고리의 데이터 파일:
  - `static/`: 기계, 제품 정적 정보
  - `snapshot/`: 특정 시점의 운영 데이터
  - `historical/`: 작업 이력 데이터
  - 추가 데이터: `products-additional.ttl`, `job-history-20250718.ttl`

### 3. 테스트 결과
- **Goal 1 (냉각 실패 작업)**: 3개 레코드 조회 성공
- **Goal 2 (제품 이상 감지)**: 1개 레코드 조회 성공
- **Goal 3 (완료 시간 예측)**: 테스트 데이터 보완 필요
- **Goal 4 (제품 위치 추적)**: 1개 레코드 조회 성공

## 실행 방법

### 전체 테스트
```bash
python3 dsl_execution_with_sparql.py
```

### 단일 목표 테스트
```bash
python3 test_single_goal.py  # goal_number 변수로 목표 선택
```

### 사용자 정의 쿼리 테스트
```bash
python3 test_custom_query.py  # 다양한 날짜/제품으로 테스트
```

## 기술적 특징

### SPARQL 쿼리 처리
1. **쿼리 템플릿 시스템**: 온톨로지에 정의된 SPARQL 템플릿 활용
2. **파라미터 치환**: `%%FILTERS%%`, `%%DATE_FILTER%%`, `%%PRODUCT_ID%%` 등 동적 치환
3. **결과 변환**: RDFLib 쿼리 결과를 JSON 형식으로 변환

### 데이터 구조
- 총 705개의 트리플 로드 (추가 데이터 포함 시 더 많음)
- URI는 마지막 부분만 추출하여 가독성 향상
- 날짜/시간 데이터는 xsd:dateTime 형식 준수

## 향후 개선사항
1. 실제 AAS 서버와의 연동
2. 더 복잡한 SPARQL 쿼리 (조인, 집계 등) 지원
3. 실시간 데이터 스트리밍 지원
4. SHACL 검증 추가