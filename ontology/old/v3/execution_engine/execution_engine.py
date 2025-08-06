#!/usr/bin/env python3
"""
Execution Engine - 실행 계획을 받아서 실제로 수행하는 엔진
모니터링 기능이 강화된 프로토타입 버전
"""

import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import os
from docker_executor import DockerExecutor


class StepStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SIMULATED = "SIMULATED"


@dataclass
class StepExecutionResult:
    """단계 실행 결과"""
    step_id: int
    action: str
    status: StepStatus
    start_time: str
    end_time: str
    duration: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    logs: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None


class ExecutionContext:
    """실행 컨텍스트 - 단계간 데이터 공유"""
    def __init__(self):
        self.data = {}
        self.step_outputs = {}
        
    def set_step_output(self, step_id: int, output: Any):
        """단계 출력 저장"""
        self.step_outputs[f"step_{step_id}"] = output
        
    def get_step_output(self, step_id: int) -> Any:
        """단계 출력 조회"""
        return self.step_outputs.get(f"step_{step_id}")
        
    def set_data(self, key: str, value: Any):
        """데이터 저장"""
        self.data[key] = value
        
    def get_data(self, key: str) -> Any:
        """데이터 조회"""
        return self.data.get(key)


class ExecutionMonitor:
    """실행 모니터링"""
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.step_results: List[StepExecutionResult] = []
        
    def log_step_start(self, step_id: int, action: str):
        """단계 시작 로그"""
        if self.verbose:
            print(f"\n[Step {step_id}] {action}")
            print("├─ Status: ⏳ RUNNING")
    
    def log_step_input(self, input_data: Dict):
        """입력 데이터 로그"""
        if self.verbose:
            if isinstance(input_data, dict):
                for key, value in input_data.items():
                    if isinstance(value, (list, dict)):
                        print(f"├─ Input.{key}: {type(value).__name__} ({len(value)} items)")
                    else:
                        print(f"├─ Input.{key}: {value}")
            else:
                print(f"├─ Input: {input_data}")
    
    def log_step_output(self, output_data: Dict):
        """출력 데이터 로그"""
        if self.verbose:
            if isinstance(output_data, dict):
                for key, value in output_data.items():
                    if isinstance(value, list):
                        print(f"└─ Output.{key}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"└─ Output.{key}: {json.dumps(value, indent=2)[:100]}...")
                    else:
                        print(f"└─ Output.{key}: {value}")
            else:
                print(f"└─ Output: {output_data}")
    
    def log_step_complete(self, result: StepExecutionResult):
        """단계 완료 로그"""
        if self.verbose:
            status_icon = "✓" if result.status == StepStatus.SUCCESS else "✗"
            print(f"├─ Status: {status_icon} {result.status.value} ({result.duration:.3f}s)")
        
        self.step_results.append(result)
    
    def print_summary(self, execution_id: str, total_duration: float):
        """실행 요약 출력"""
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"✅ Execution Complete")
            print(f"├─ ID: {execution_id}")
            print(f"├─ Total Duration: {total_duration:.3f}s")
            print(f"├─ Steps: {len(self.step_results)}")
            
            success_count = sum(1 for r in self.step_results if r.status == StepStatus.SUCCESS)
            simulated_count = sum(1 for r in self.step_results if r.status == StepStatus.SIMULATED)
            failed_count = sum(1 for r in self.step_results if r.status == StepStatus.FAILED)
            
            print(f"└─ Results: {success_count} success, {simulated_count} simulated, {failed_count} failed")


class ExecutionEngine:
    """실행 엔진"""
    def __init__(self, monitor: Optional[ExecutionMonitor] = None):
        self.monitor = monitor or ExecutionMonitor()
        self.context = ExecutionContext()
        self.docker_executor = DockerExecutor()
        
    def execute_plan(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """실행 계획 수행"""
        execution_id = execution_plan.get("executionId", f"exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        goal = execution_plan.get("goal", "Unknown")
        
        print(f"\n🚀 Executing: {goal}")
        print("━" * 50)
        
        start_time = time.time()
        
        # 초기 파라미터를 컨텍스트에 저장
        self.context.set_data("input_parameters", execution_plan.get("inputParameters", {}))
        self.context.set_data("parameter_mappings", execution_plan.get("parameterMappings", {}))
        
        # 각 단계 실행
        for step in execution_plan.get("executionSteps", []):
            result = self._execute_step(step)
            if result.status == StepStatus.FAILED:
                break
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 요약 출력
        self.monitor.print_summary(execution_id, total_duration)
        
        # 최종 결과 생성
        return self._generate_execution_report(execution_id, goal, total_duration)
    
    def _execute_step(self, step: Dict[str, Any]) -> StepExecutionResult:
        """단계 실행"""
        step_id = step.get("stepId", 0)
        action = step.get("action", "Unknown")
        
        self.monitor.log_step_start(step_id, action)
        
        start_time = datetime.now()
        
        # 입력 데이터 준비
        input_data = self._prepare_input(step)
        self.monitor.log_step_input(input_data)
        
        # 액션 타입별 실행
        try:
            if "Query" in action and "Build" in action:
                output_data = self._execute_query_builder(step, input_data)
            elif "Execute" in action and "Query" in action:
                output_data = self._execute_sparql_query(step, input_data)
            elif "Fetch" in action:
                output_data = self._execute_aas_fetch(step, input_data)
            elif ("RunAnomalyDetection" in action or "RunSimulation" in action):
                output_data = self._simulate_external_execution(step, input_data)
            elif "Enrich" in action:
                output_data = self._execute_data_enrichment(step, input_data)
            else:
                output_data = {"message": f"Action {action} not implemented"}
            
            status = StepStatus.SUCCESS
            error = None
            
        except Exception as e:
            output_data = {"error": str(e)}
            status = StepStatus.FAILED
            error = str(e)
            print(f"❌ Error in {action}: {e}")
            import traceback
            traceback.print_exc()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 결과 생성
        result = StepExecutionResult(
            step_id=step_id,
            action=action,
            status=status,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=duration,
            input_data=input_data,
            output_data=output_data,
            error=error
        )
        
        # 출력 저장
        self.context.set_step_output(step_id, output_data)
        
        self.monitor.log_step_output(output_data)
        self.monitor.log_step_complete(result)
        
        return result
    
    def _prepare_input(self, step: Dict) -> Dict[str, Any]:
        """단계 입력 준비"""
        input_data = {}
        
        # 파라미터 추가
        if "parameters" in step:
            input_data.update(step["parameters"])
        
        # 이전 단계 출력 참조
        if "input" in step:
            input_ref = step["input"]
            if isinstance(input_ref, str) and input_ref.startswith("step_"):
                step_num = int(input_ref.split("_")[1].split(".")[0])
                prev_output = self.context.get_step_output(step_num)
                if prev_output:
                    input_data["from_previous_step"] = prev_output
            elif isinstance(input_ref, dict):
                input_data["input_config"] = input_ref
        
        # 컨텍스트 데이터 추가
        input_data["context"] = {
            "input_parameters": self.context.get_data("input_parameters"),
            "parameter_mappings": self.context.get_data("parameter_mappings")
        }
        
        return input_data
    
    def _execute_query_builder(self, step: Dict, input_data: Dict) -> Dict[str, Any]:
        """쿼리 빌더 실행"""
        time.sleep(0.5)  # 시뮬레이션 지연
        
        # step에 이미 generatedQuery가 있으면 사용
        if "generatedQuery" in step:
            return {
                "query": step["generatedQuery"],
                "query_type": "SPARQL",
                "size": f"{len(step['generatedQuery'])} bytes"
            }
        
        # 없으면 샘플 쿼리 생성
        return {
            "query": "SELECT ?job ?machine WHERE { ?job rdf:type prod:Job . }",
            "query_type": "SPARQL",
            "size": "128 bytes"
        }
    
    def _execute_sparql_query(self, step: Dict, input_data: Dict) -> Dict[str, Any]:
        """SPARQL 쿼리 실행 (시뮬레이션)"""
        time.sleep(1.0)  # 시뮬레이션 지연
        
        # step에 sampleResults가 있으면 사용
        if "sampleResults" in step:
            return {
                "results": step["sampleResults"],
                "count": step.get("expectedResultCount", len(step["sampleResults"]))
            }
        
        # 없으면 랜덤 결과 생성
        num_results = random.randint(5, 20)
        results = []
        
        for i in range(num_results):
            results.append({
                "job": f"Job-{100 + i}",
                "machine": f"Machine-{random.choice(['01', '02', '03'])}",
                "status": random.choice(["Success", "Failed", "Processing"])
            })
        
        return {
            "results": results,
            "count": num_results
        }
    
    def _execute_aas_fetch(self, step: Dict, input_data: Dict) -> Dict[str, Any]:
        """AAS 데이터 조회 (시뮬레이션)"""
        time.sleep(1.5)  # 시뮬레이션 지연
        
        action = step.get("action", "")
        
        if "Sensor" in action:
            # 센서 데이터 시뮬레이션
            sensor_data = []
            for i in range(50):
                sensor_data.append({
                    "timestamp": f"2025-07-17T{10+i%14:02d}:{i%60:02d}:00",
                    "temperature": 20 + random.random() * 10,
                    "vibration": random.random() * 5,
                    "pressure": 100 + random.random() * 20
                })
            return {
                "sensor_readings": sensor_data,
                "count": len(sensor_data)
            }
        
        elif "Template" in action:
            # Job 템플릿 시뮬레이션
            return {
                "operations": [
                    {"name": "Cooling", "duration": 30, "machine": "CoolingMachine"},
                    {"name": "Heating", "duration": 45, "machine": "HeatingMachine"},
                    {"name": "Assembly", "duration": 20, "machine": "AssemblyMachine"}
                ],
                "total_operations": 3
            }
        
        elif "Schedule" in action:
            # 머신 스케줄 시뮬레이션
            return {
                "machines": [
                    {"id": "Machine-01", "status": "Active", "utilization": 0.75},
                    {"id": "Machine-02", "status": "Maintenance", "utilization": 0.0},
                    {"id": "Machine-03", "status": "Active", "utilization": 0.82}
                ],
                "count": 3
            }
        
        return {"message": "AAS fetch completed"}
    
    def _simulate_external_execution(self, step: Dict, input_data: Dict) -> Dict[str, Any]:
        """외부 실행 시뮬레이션 (AWS Lambda/Batch)"""
        action = step.get("action", "")
        input_params = self.context.get_data("input_parameters") or {}
        goal = input_params.get("goal", "")
        
        # Docker 실행 가능 여부 확인
        use_docker = os.environ.get("USE_DOCKER", "false").lower() == "true"
        
        # 상태를 SIMULATED로 변경
        self.monitor.step_results[-1].status = StepStatus.SIMULATED
        
        if "Anomaly" in action:
            # AI 모델 입력 데이터 준비 (여러 데이터 소스 통합)
            ai_input_data = {
                "input_files": {
                    "sensor_data": {
                        "source": "step_3_output",  # FetchSensorData 결과
                        "data": self.context.get_step_output(3) or {"sensor_readings": [], "count": 0}
                    },
                    "job_history": {
                        "source": "step_2_output",  # ExecuteProductTrace 결과
                        "data": self.context.get_step_output(2) or {"results": [], "count": 0}
                    },
                    "machine_status": {
                        "source": "machines.json",
                        "data": self._load_json_file("machines.json", sample_size=5)
                    },
                    "product_specs": {
                        "source": "products.json",
                        "product_id": input_params.get("product_id", "Unknown"),
                        "data": self._load_json_file("products.json", filter_key="product_id", filter_value=input_params.get("product_id"))
                    }
                },
                "parameters": {
                    "target_machine": input_params.get("target_machine"),
                    "date_range": input_params.get("date_range"),
                    "anomaly_threshold": 0.85,
                    "detection_algorithms": ["isolation_forest", "lstm_autoencoder", "statistical_analysis"]
                }
            }
            
            # Docker 실행 또는 시뮬레이션
            if use_docker:
                # Docker 컨테이너로 실행 (아직 anomaly-detector 이미지가 없으므로 job-processor로 테스트)
                print("🐳 Attempting to run anomaly detection in Docker container...")
                docker_result = self.docker_executor.execute_container(
                    image_name="anomaly-detector:latest",  # 실제 AI 모델 컨테이너
                    input_data=ai_input_data,
                    input_files={
                        "machines.json": os.path.join(os.path.dirname(os.path.dirname(__file__)), "machines.json"),
                        "products.json": os.path.join(os.path.dirname(os.path.dirname(__file__)), "products.json")
                    }
                )
                
                if "error" in docker_result:
                    print(f"⚠️ Docker execution failed: {docker_result['error']}")
                    print("📦 Falling back to simulation mode...")
                else:
                    return docker_result
            
            # 이상 탐지 결과 시뮬레이션
            return {
                "service": "AWS Lambda",
                "function": "anomaly-detection-v2",
                "execution_time": 1.8,
                "input_summary": {
                    "sensor_readings": ai_input_data["input_files"]["sensor_data"]["data"].get("count", 0),
                    "job_records": ai_input_data["input_files"]["job_history"]["data"].get("count", 0),
                    "machine_records": len(ai_input_data["input_files"]["machine_status"]["data"]) if isinstance(ai_input_data["input_files"]["machine_status"]["data"], list) else 0,
                    "total_input_size": f"{len(str(ai_input_data))} bytes"
                },
                "result": {
                    "anomalies": [
                        {
                            "timestamp": "2025-07-17T14:30:00",
                            "type": "temperature_spike",
                            "severity": "high",
                            "confidence": 0.92,
                            "affected_sensors": ["TEMP_001", "TEMP_002"],
                            "deviation": "+15.3°C from baseline"
                        },
                        {
                            "timestamp": "2025-07-17T15:45:00",
                            "type": "vibration_pattern",
                            "severity": "medium",
                            "confidence": 0.78,
                            "frequency_band": "120-150Hz",
                            "pattern": "periodic_spike"
                        }
                    ],
                    "overall_confidence": 0.87,
                    "recommendation": "Schedule maintenance check",
                    "risk_score": 7.5
                }
            }
        
        elif "Simulation" in action:
            # 시뮬레이터 입력 데이터 준비
            simulator_input_data = {
                "input_files": {
                    "job_template": {
                        "source": "step_2_output",  # FetchJobTemplate 결과
                        "data": self.context.get_step_output(2) or {"operations": [], "total_operations": 0}
                    },
                    "machine_schedule": {
                        "source": "step_3_output",  # FetchMachineSchedule 결과
                        "data": self.context.get_step_output(3) or {"machines": [], "count": 0}
                    },
                    "historical_jobs": {
                        "source": "jobs.json",
                        "data": self._load_json_file("jobs.json", sample_size=100)
                    },
                    "machine_specs": {
                        "source": "machines.json",
                        "data": self._load_json_file("machines.json")
                    },
                    "scenarios": {
                        "source": "scenarios.json",
                        "scenario_type": "production_planning",
                        "data": self._load_json_file("scenarios.json", filter_key="type", filter_value="production_planning")
                    }
                },
                "simulation_parameters": {
                    "product_id": input_params.get("product_id"),
                    "quantity": input_params.get("quantity", 1),
                    "start_time": "2025-07-28T08:00:00",
                    "optimization_goals": ["minimize_time", "balance_load"],
                    "constraints": {
                        "max_overtime_hours": 4,
                        "maintenance_windows": ["2025-07-28T18:00:00", "2025-07-29T06:00:00"]
                    },
                    "monte_carlo_runs": 1000
                }
            }
            
            # Docker 실행 또는 시뮬레이션
            if use_docker:
                # Docker 컨테이너로 실행 (job-processor로 테스트)
                print("🐳 Attempting to run production simulation in Docker container...")
                docker_result = self.docker_executor.execute_container(
                    image_name="job-processor:latest",  # 테스트용으로 job-processor 사용
                    input_data=simulator_input_data,
                    input_files={
                        "jobs.json": os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs.json"),
                        "machines.json": os.path.join(os.path.dirname(os.path.dirname(__file__)), "machines.json"),
                        "scenarios.json": os.path.join(os.path.dirname(os.path.dirname(__file__)), "scenarios.json")
                    }
                )
                
                if "error" in docker_result:
                    print(f"⚠️ Docker execution failed: {docker_result['error']}")
                    print("📦 Falling back to simulation mode...")
                else:
                    return docker_result
            
            # 시뮬레이션 결과
            return {
                "service": "AWS Batch",
                "job_name": "production-simulation-job",
                "execution_time": 3.5,
                "input_summary": {
                    "operations": simulator_input_data["input_files"]["job_template"]["data"].get("total_operations", 0),
                    "available_machines": simulator_input_data["input_files"]["machine_schedule"]["data"].get("count", 0),
                    "historical_data_points": len(simulator_input_data["input_files"]["historical_jobs"]["data"]) if isinstance(simulator_input_data["input_files"]["historical_jobs"]["data"], list) else 0,
                    "scenarios_evaluated": 5
                },
                "result": {
                    "predicted_completion": "2025-07-29T18:30:00",
                    "confidence_interval": {
                        "lower": "2025-07-29T17:00:00",
                        "upper": "2025-07-29T20:00:00",
                        "confidence_level": 0.95
                    },
                    "bottlenecks": [
                        {"machine": "CoolingMachine-01", "utilization": 0.95, "queue_time": 45},
                        {"machine": "HeatingMachine-03", "utilization": 0.88, "queue_time": 30}
                    ],
                    "production_schedule": [
                        {"operation": "Cooling", "machine": "CoolingMachine-02", "start": "2025-07-28T08:00:00", "end": "2025-07-28T08:30:00"},
                        {"operation": "Heating", "machine": "HeatingMachine-01", "start": "2025-07-28T08:35:00", "end": "2025-07-28T09:20:00"},
                        {"operation": "Assembly", "machine": "AssemblyMachine-04", "start": "2025-07-28T09:25:00", "end": "2025-07-28T09:45:00"}
                    ],
                    "estimated_cost": 2450.00,
                    "resource_efficiency": 0.82
                }
            }
        
        return {"message": "External execution completed"}
    
    def _load_json_file(self, filename: str, filter_key: str = None, filter_value: Any = None, sample_size: int = None) -> Any:
        """JSON 파일 로드 헬퍼 (시뮬레이션용)"""
        try:
            # 실제 구현에서는 파일 시스템에서 읽어옴
            # 여기서는 시뮬레이션을 위한 샘플 데이터 반환
            if filename == "machines.json":
                data = [
                    {"id": "CoolingMachine-01", "status": "Active", "efficiency": 0.92},
                    {"id": "CoolingMachine-02", "status": "Active", "efficiency": 0.95},
                    {"id": "HeatingMachine-01", "status": "Active", "efficiency": 0.88},
                    {"id": "HeatingMachine-03", "status": "Maintenance", "efficiency": 0.85},
                    {"id": "AssemblyMachine-04", "status": "Active", "efficiency": 0.90}
                ]
            elif filename == "jobs.json":
                data = [{"id": f"Job-{i}", "status": random.choice(["Success", "Failed"]), "duration": random.randint(20, 60)} for i in range(100)]
            elif filename == "products.json":
                data = [
                    {"product_id": "Product-A1", "name": "Product A1", "requirements": ["cooling", "heating"]},
                    {"product_id": "Product-B2", "name": "Product B2", "requirements": ["cooling", "heating", "assembly"]}
                ]
            elif filename == "scenarios.json":
                data = [
                    {"id": "scenario-1", "type": "production_planning", "complexity": "high"},
                    {"id": "scenario-2", "type": "maintenance_planning", "complexity": "medium"}
                ]
            else:
                data = []
            
            # 필터링 적용
            if filter_key and filter_value:
                data = [item for item in data if item.get(filter_key) == filter_value]
            
            # 샘플 크기 제한
            if sample_size and isinstance(data, list):
                data = data[:sample_size]
            
            return data
        except Exception:
            return []
    
    def _execute_data_enrichment(self, step: Dict, input_data: Dict) -> Dict[str, Any]:
        """데이터 보강"""
        time.sleep(0.8)  # 시뮬레이션 지연
        
        enrichments = step.get("enrichments", [])
        results = {}
        
        for enrichment in enrichments:
            etype = enrichment.get("type", "")
            if etype == "fetchMachineDetails":
                results[etype] = {
                    "machines_enriched": 5,
                    "details_added": ["location", "efficiency", "maintenance_schedule"]
                }
            elif etype == "parseErrorLogs":
                results[etype] = {
                    "errors_parsed": 12,
                    "categories": ["timeout", "temperature_exceeded", "connection_lost"]
                }
            elif etype == "calculateProgress":
                results[etype] = {
                    "overall_progress": 0.67,
                    "completed_operations": 4,
                    "total_operations": 6
                }
        
        return {
            "enrichments_applied": len(enrichments),
            "results": results
        }
    
    def _generate_execution_report(self, execution_id: str, goal: str, duration: float) -> Dict[str, Any]:
        """실행 리포트 생성"""
        success_count = sum(1 for r in self.monitor.step_results if r.status == StepStatus.SUCCESS)
        simulated_count = sum(1 for r in self.monitor.step_results if r.status == StepStatus.SIMULATED)
        failed_count = sum(1 for r in self.monitor.step_results if r.status == StepStatus.FAILED)
        
        # 최종 결과 추출
        final_output = {}
        if self.monitor.step_results:
            last_result = self.monitor.step_results[-1]
            if last_result.status in [StepStatus.SUCCESS, StepStatus.SIMULATED]:
                final_output = last_result.output_data
        
        return {
            "executionId": execution_id,
            "goal": goal,
            "status": "COMPLETED" if failed_count == 0 else "FAILED",
            "totalDuration": round(duration, 3),
            "stepsSummary": {
                "total": len(self.monitor.step_results),
                "succeeded": success_count,
                "simulated": simulated_count,
                "failed": failed_count
            },
            "steps": [
                {
                    "stepId": r.step_id,
                    "action": r.action,
                    "status": r.status.value,
                    "duration": r.duration,
                    "inputSize": len(str(r.input_data)),
                    "outputSize": len(str(r.output_data))
                }
                for r in self.monitor.step_results
            ],
            "finalOutput": final_output,
            "timestamp": datetime.now().isoformat()
        }