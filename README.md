# AASX (Advanced Assembly System Simulator)

고급 조립 시스템 시뮬레이터로, 정적 및 동적 머신 할당을 지원하는 제조 시스템 시뮬레이션 도구입니다.

## 주요 기능

### 1. 정적 스케줄링
- 기존의 `routing_result.json` 파일을 통한 정적 operation 할당
- 미리 정의된 머신 할당으로 예측 가능한 스케줄링

### 2. 동적 스케줄링 (신규)
- **Control Tower**를 통한 실시간 머신 상태 관리
- 다양한 스케줄링 전략 지원
- 최적화된 머신 할당으로 효율성 향상

## 동적 스케줄링 시스템

### Control Tower
머신들의 현재 상태를 실시간으로 관리하고, operation을 동적으로 최적 할당하는 핵심 시스템입니다.

#### 주요 기능
- **실시간 머신 상태 모니터링**: 각 머신의 상태, 가용 시간, 큐 길이 등을 추적
- **다양한 스케줄링 전략**: 부하 분산, 최단 처리 시간, 우선순위 기반 등
- **동적 할당**: 현재 시스템 상태를 고려한 최적 머신 선택
- **통계 및 분석**: 머신 활용도, 처리 시간, 대기 시간 등 분석

#### 지원하는 스케줄링 전략
1. **LOAD_BALANCING**: 부하 분산을 통한 균등한 머신 활용
2. **EARLIEST_AVAILABLE**: 가장 빨리 사용 가능한 머신 선택
3. **LEAST_LOADED**: 가장 적은 작업량을 가진 머신 선택
4. **SHORTEST_PROCESSING_TIME**: 가장 짧은 처리 시간을 가진 머신 선택
5. **PRIORITY_BASED**: 우선순위 기반 머신 선택

### 사용 방법

#### 1. 기본 동적 스케줄링
```python
from control.control_tower import ControlTower, SchedulingStrategy

# Control Tower 생성
control_tower = ControlTower("scenarios/my_case", SchedulingStrategy.LOAD_BALANCING)

# Job operations 추가
control_tower.add_job_operations("J1", ["O11", "O12", "O13"], priority=3)
control_tower.add_job_operations("J2", ["O21", "O22"], priority=2)

# 동적 할당 실행
assignments = control_tower.assign_operations()

# 결과 내보내기
control_tower.export_routing_result("dynamic_routing_result.json")
```

#### 2. DynamicScheduler 사용
```python
from control.dynamic_scheduler import DynamicScheduler

# 스케줄러 생성
scheduler = DynamicScheduler("scenarios/my_case", SchedulingStrategy.LOAD_BALANCING)

# 우선순위 설정
priorities = {"J1": 3, "J2": 2, "J3": 1}

# 스케줄링 실행
assignments = scheduler.schedule_jobs(priorities=priorities)

# 결과 내보내기
scheduler.export_results()
```

#### 3. 기존 시뮬레이터와 통합
```python
from control.simulator_adapter import run_dynamic_simulation

# 동적 할당을 사용한 시뮬레이션 실행
sim, adapter = run_dynamic_simulation("scenarios/my_case", SchedulingStrategy.LOAD_BALANCING)
```

### 테스트 실행

```bash
# 기본 테스트
python simulator/test_dynamic_scheduling.py

# 동적 스케줄러 테스트
python simulator/control/dynamic_scheduler.py

# 시뮬레이터 통합 테스트
python simulator/control/simulator_adapter.py
```

## 프로젝트 구조

```
AASX/
├── simulator/
│   ├── control/                    # 동적 스케줄링 시스템
│   │   ├── control_tower.py       # Control Tower 클래스
│   │   ├── dynamic_scheduler.py   # 동적 스케줄러
│   │   └── simulator_adapter.py   # 시뮬레이터 통합 어댑터
│   ├── scenarios/
│   │   └── my_case/               # 시나리오 데이터
│   │       ├── jobs.json          # Job 정의
│   │       ├── operations.json    # Operation 정의
│   │       ├── machines.json      # 머신 상태
│   │       ├── operation_durations.json  # 처리 시간 정보
│   │       └── routing_result.json       # 정적 할당 결과
│   └── test_dynamic_scheduling.py # 테스트 스크립트
└── results/                       # 시뮬레이션 결과
```

## 시나리오 파일 형식

### jobs.json
```json
[
  {
    "job_id": "J1",
    "part_id": "P1",
    "operations": ["O11", "O12", "O13"]
  }
]
```

### operations.json
```json
[
  {
    "operation_id": "O11",
    "job_id": "J1",
    "type": "drilling",
    "machines": ["M1", "M2"]
  }
]
```

### machines.json
```json
{
  "M1": { "status": "idle", "next_available_time": 0.0 },
  "M2": { "status": "idle", "next_available_time": 0.0 }
}
```

### operation_durations.json
```json
{
  "drilling": {
    "M1": { "distribution": "normal", "mean": 3.0, "std": 0.5 },
    "M2": { "distribution": "uniform", "low": 2.5, "high": 3.5 }
  }
}
```

## 성능 비교

동적 스케줄링 시스템은 다음과 같은 이점을 제공합니다:

1. **머신 활용도 향상**: 부하 분산을 통한 균등한 머신 활용
2. **처리 시간 단축**: 최적 머신 선택으로 전체 처리 시간 단축
3. **유연성**: 실시간 시스템 상태에 따른 동적 대응
4. **확장성**: 새로운 스케줄링 전략 쉽게 추가 가능

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.