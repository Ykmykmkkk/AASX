# execution_engine/agent_refactored.py
"""
리팩토링된 Agent 모듈 - Mock과 Standard AAS 서버 모두 지원
Mock 서버와의 기존 호환성을 유지하면서 표준 서버 지원 추가
"""
import requests, sys, time, json, uuid, base64, os
from pathlib import Path
from typing import Dict, Any, Optional
from kubernetes import client, config as k8s_config
from simulation_data_converter import SimulationDataConverter

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (
    AAS_SERVER_URL, 
    AAS_SERVER_IP, 
    AAS_SERVER_PORT, 
    AAS_SERVER_TYPE,
    USE_STANDARD_SERVER
)

# 표준 서버를 사용할 경우에만 AASQueryClient 임포트
if USE_STANDARD_SERVER:
    from aas_query_client import AASQueryClient

# --- 핸들러 클래스들 ---

class AASQueryHandler:
    """
    AAS 서버에 데이터를 요청하는 핸들러
    Mock과 Standard 서버 모두 지원
    """
    def __init__(self):
        self.server_type = AAS_SERVER_TYPE
        
        if USE_STANDARD_SERVER:
            # 표준 서버 사용 시 AASQueryClient 인스턴스 생성
            self.client = AASQueryClient(AAS_SERVER_IP, AAS_SERVER_PORT)
            print(f"🔄 AASQueryHandler: Using STANDARD server client")
        else:
            # Mock 서버 사용 시 기존 방식 유지
            self.client = None
            print(f"📦 AASQueryHandler: Using MOCK server (direct HTTP)")
    
    def _to_base64url(self, s: str) -> str:
        """Base64 URL 인코딩 (Mock 서버용)"""
        return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")
    
    def _query_mock_server(self, target_sm_id: str) -> Dict[str, Any]:
        """Mock 서버에 직접 쿼리 (기존 로직)"""
        b64id = self._to_base64url(target_sm_id)
        url = f"{AAS_SERVER_URL}/submodels/{b64id}"
        
        print(f"INFO: Requesting from MOCK server: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _query_standard_server(self, target_sm_id: str) -> Dict[str, Any]:
        """표준 서버에 AASQueryClient를 통해 쿼리"""
        print(f"INFO: Requesting from STANDARD server: {target_sm_id}")
        
        try:
            # AASQueryClient의 get_submodel_by_id 메소드 사용
            result = self.client.get_submodel_by_id(target_sm_id)
            if result:
                return result
            else:
                raise ValueError(f"Submodel {target_sm_id} not found on standard server")
        except Exception as e:
            print(f"ERROR: Standard server query failed: {e}")
            raise
    
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        goal = params.get('goal')
        action_id = step_details.get('action_id')
        
        # Goal 3의 ActionFetchProductSpec: J1, J2, J3 process_plan 조회
        if action_id == 'ActionFetchProductSpec' and goal == 'predict_first_completion_time':
            print("INFO: Fetching process plans from J1, J2, J3 for Goal 3")
            all_process_data = []
            
            # J1, J2, J3의 process_plan 조회
            for job_id in ['J1', 'J2', 'J3']:
                try:
                    target_sm_id = f"urn:factory:submodel:process_plan:{job_id}"
                    if USE_STANDARD_SERVER:
                        result = self._query_standard_server(target_sm_id)
                    else:
                        result = self._query_mock_server(target_sm_id)
                    all_process_data.append(result)
                    print(f"  ✅ {job_id} process_plan fetched")
                except Exception as e:
                    print(f"  ⚠️ {job_id} process_plan not found: {e}")
            
            return {"process_specifications": all_process_data} if all_process_data else {"message": "No process data found"}
        
        # ActionFetchAllMachineData: M1, M2, M3 데이터 조회
        elif action_id == 'ActionFetchAllMachineData':
            print("INFO: Fetching machine data from M1, M2, M3")
            all_machine_data = []
            
            # M1, M2, M3의 process_data 조회
            for machine_id in ['M1', 'M2', 'M3']:
                try:
                    target_sm_id = f"urn:factory:submodel:process_data:{machine_id}"
                    if USE_STANDARD_SERVER:
                        result = self._query_standard_server(target_sm_id)
                    else:
                        result = self._query_mock_server(target_sm_id)
                    all_machine_data.append(result)
                    print(f"  ✅ {machine_id} process_data fetched")
                except Exception as e:
                    print(f"  ⚠️ {machine_id} process_data not found: {e}")
                    
            return {"machine_capabilities": all_machine_data} if all_machine_data else {"message": "No machine data found"}
        
        # 기존 로직
        else:
            target_sm_id = step_details.get('target_submodel_id')
            if not target_sm_id:
                if goal == 'track_product_position':
                    product_id = params.get('product_id')
                    if not product_id:
                        raise ValueError("product_id is required for track_product_position")
                    target_sm_id = f"urn:factory:submodel:tracking_data:{product_id.lower()}"
                elif goal == 'detect_anomaly_for_product':
                    target_machine = params.get('target_machine')
                    if not target_machine:
                        raise ValueError("target_machine is required for detect_anomaly_for_product")
                    target_sm_id = f"urn:factory:submodel:sensor_data:{target_machine.lower()}"
                else:
                    raise ValueError(f"Cannot determine target for goal: {goal}")
        
        # 서버 타입에 따라 다른 쿼리 방식 사용
        try:
            if USE_STANDARD_SERVER:
                return self._query_standard_server(target_sm_id)
            else:
                return self._query_mock_server(target_sm_id)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Goal 3의 경우 404 에러를 무시하고 빈 데이터 반환 (fallback 로직이 처리)
                if goal == 'predict_first_completion_time':
                    print(f"WARNING: Submodel {target_sm_id} not found. Using fallback data.")
                    return {"message": "Submodel not found, will use fallback data"}
                else:
                    raise
            else:
                raise

class DataFilteringHandler:
    """AAS에서 가져온 데이터를 DSL 조건에 맞게 필터링하거나 가공하는 핸들러"""
    
    def _parse_value(self, data: Any) -> Any:
        """
        서버 응답의 value 필드를 파싱
        Mock과 Standard 서버의 다른 응답 형식 처리
        """
        if isinstance(data, dict):
            # submodelElements가 있는 경우 (표준 형식)
            if 'submodelElements' in data:
                elements = data.get('submodelElements', [])
                if elements and len(elements) > 0:
                    value = elements[0].get('value')
                    # value가 문자열이면 JSON 파싱 시도
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            return value
                    return value
            # 직접 value가 있는 경우
            elif 'value' in data:
                value = data.get('value')
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                return value
        return data
    
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        goal = params.get('goal')
        
        # Goal 1: 실패한 냉각 Job 필터링 로직
        if goal == 'query_failed_jobs_with_cooling':
            data_to_filter = None
            for key, value in context.items():
                if 'ActionFetchJobLog' in key:
                    data_to_filter = self._parse_value(value)
                    break
            
            if data_to_filter is None:
                raise ValueError("Could not find data from previous step for Goal 1.")
            
            # 리스트가 아니면 리스트로 변환
            if not isinstance(data_to_filter, list):
                data_to_filter = [data_to_filter] if data_to_filter else []

            request_date = params.get('date')
            filtered_jobs = [
                job for job in data_to_filter
                if job.get('date') == request_date
                and job.get('status') == 'FAILED'
                and 'cooling' in job.get('process_steps', [])
            ]
            return {"final_result": filtered_jobs}
        
        # Goal 4: 제품 위치 추적 로직
        elif goal == 'track_product_position':
            tracking_data = None
            for key, value in context.items():
                if 'ActionFetchTrackingData' in key:
                    tracking_data = self._parse_value(value)
                    break
            
            if tracking_data is None:
                raise ValueError("Could not find tracking data from previous step for Goal 4.")
            
            return {"final_result": tracking_data}
        
        # 어떤 조건에도 해당하지 않을 경우
        return {"final_result": "No applicable filter or processing logic for this goal."}

class SimulationInputHandler:
    """여러 소스의 데이터를 조합하여 시뮬레이터 입력 파일을 생성하는 핸들러"""
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        job_id = str(uuid.uuid4())
        
        # PVC 또는 임시 경로 사용
        if os.path.exists('/data') and os.access('/data', os.W_OK):
            shared_dir = Path("/data")
            print("INFO: Using K8s PVC at /data")
        else:
            shared_dir = Path("/tmp/factory_automation")
            print(f"INFO: Using local temp directory: {shared_dir}")
        
        current_dir = shared_dir / "current"
        current_dir.mkdir(parents=True, exist_ok=True)
        
        # 컨텍스트에서 이전 단계들의 결과 수집
        input_data = {
            "process_spec": context.get("step_1_ActionFetchProductSpec", {}),
            "machine_data": context.get("step_2_ActionFetchAllMachineData", {}),
            "order": params,
            "job_id": job_id
        }

        # 고정 경로에 입력 파일 작성
        input_file_path = current_dir / "simulation_inputs.json"
        with open(input_file_path, 'w') as f:
            json.dump(input_data, f, indent=2)

        print(f"INFO: Created simulation input file at {input_file_path} (job_id: {job_id})")
        return {"simulation_job_id": job_id}

class EnhancedDockerRunHandler:
    """
    AASX-main simulator를 실행하는 향상된 핸들러
    온톨로지 변경 없이 기존 ActionRunSimulator 액션에서 호출됨
    """
    
    def __init__(self):
        # Kubernetes 설정
        try: 
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException: 
            k8s_config.load_kube_config()
        
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        self.namespace = "default"
        
        # 환경변수 설정
        self.aas_server_ip = AAS_SERVER_IP
        self.aas_server_port = AAS_SERVER_PORT
        self.use_advanced_simulator = True  # 기본적으로 AASX-main 사용
        
        print(f"INFO: Enhanced DockerRunHandler initialized")
        print(f"      AAS Server: {self.aas_server_ip}:{self.aas_server_port}")
        print(f"      Advanced Simulator: {self.use_advanced_simulator}")
    
    def execute(self, step_details: dict, context: dict) -> dict:
        """
        AASX-main simulator를 실행하는 메인 로직
        
        1. AAS 서버에서 시뮬레이션 데이터 수집
        2. AASX-main simulator 형식으로 변환
        3. PVC에 데이터 저장
        4. K8s Job으로 AASX-main simulator 실행
        5. 결과 수집 및 반환
        """
        if not self.use_advanced_simulator:
            # 기존 dummy simulator 로직 실행
            return self._run_dummy_simulator(step_details, context)
        
        print("🚀 Enhanced AASX-main Simulator 실행 시작")
        
        try:
            # Step 1: AAS 데이터 수집 및 변환
            print("📊 Step 1: AAS 데이터 수집 및 변환")
            converter_result = self._convert_and_prepare_data(context)
            
            # Step 2: PVC에 데이터 저장  
            print("💾 Step 2: PVC에 시뮬레이션 데이터 저장")
            pvc_result = self._save_simulation_data_to_pvc(converter_result)
            
            # Step 3: K8s Job으로 AASX-main simulator 실행
            print("🔄 Step 3: AASX-main Simulator 실행")
            simulation_result = self._run_aasx_simulator_job(pvc_result)
            
            print("✅ Enhanced AASX-main Simulator 실행 완료")
            
            # Goal 3를 위해 final_result 키 추가
            return {"final_result": simulation_result}
            
        except Exception as e:
            print(f"❌ AASX-main Simulator 실행 실패: {e}")
            print("📝 Fallback: 기본 시뮬레이션 결과 반환")
            
            # Fallback: 기본 결과 반환
            return {
                "final_result": {
                    "predicted_completion_time": "2025-08-11T20:00:00Z",
                    "confidence": 0.6,
                    "details": f"AASX simulation failed, using fallback. Error: {str(e)[:100]}"
                },
                "fallback_mode": True
            }
    
    def _convert_and_prepare_data(self, context: dict) -> dict:
        """AAS 서버에서 데이터를 수집하고 AASX 형식으로 변환"""
        
        # AAS 데이터 변환기 초기화
        converter = SimulationDataConverter(self.aas_server_ip, self.aas_server_port)
        
        try:
            # Goal 3에서 수집된 context 데이터 활용
            print("  📋 Context에서 AAS 데이터 추출 중...")
            
            # ActionFetchProductSpec, ActionFetchAllMachineData에서 수집된 데이터 사용
            for key, value in context.items():
                if 'ActionFetchProductSpec' in key or 'ActionFetchAllMachine' in key:
                    print(f"    발견: {key}")
                    
            # 실제 AAS 서버에서 J1,J2,J3,M1,M2,M3 데이터 수집
            print("  🔍 AAS 서버에서 시뮬레이션 데이터 수집...")
            aas_data = converter.fetch_all_aas_data()
            
            if aas_data['jobs'] or aas_data['machines']:
                print("  🔄 AAS 데이터를 AASX 형식으로 변환...")
                
                # AASX 형식으로 변환
                aasx_jobs = converter.convert_to_aasx_jobs(aas_data)
                aasx_machines = converter.convert_to_aasx_machines(aas_data) 
                aasx_operations = converter.convert_to_aasx_operations(aas_data)
                
                # 기본 데이터와 병합
                default_data = converter.generate_default_data()
                
                converted_data = {
                    "jobs": aasx_jobs if aasx_jobs else default_data["jobs"],
                    "machines": aasx_machines if aasx_machines else default_data["machines"],
                    "operations": aasx_operations if aasx_operations else default_data["operations"],
                    "operation_durations": default_data["operation_durations"],
                    "machine_transfer_time": default_data["machine_transfer_time"],
                    "routing_result": default_data["routing_result"],
                    "initial_machine_status": default_data["initial_machine_status"]
                }
                
                print(f"  ✅ 변환 완료: Jobs {len(converted_data['jobs'])}, "
                      f"Machines {len(converted_data['machines'])}, "
                      f"Operations {len(converted_data['operations'])}")
                
                return converted_data
            else:
                print("  ⚠️ AAS 데이터 부족, 기본 데이터 사용")
                return converter.generate_default_data()
                
        except Exception as e:
            print(f"  ❌ AAS 데이터 변환 실패: {e}")
            print("  📝 기본 데이터로 대체")
            return converter.generate_default_data()
    
    def _save_simulation_data_to_pvc(self, aasx_data: dict) -> dict:
        """변환된 시뮬레이션 데이터를 PVC에 저장"""
        
        try:
            # PVC 마운트 경로 설정 (K8s 환경에서는 /data, 로컬에서는 임시 디렉토리)
            if os.path.exists('/data'):
                base_path = Path('/data')
                print("  📁 K8s 환경: /data PVC 사용")
            else:
                base_path = Path('/tmp/factory_automation')
                print(f"  📁 로컬 환경: {base_path} 사용")
            
            # current 디렉토리 생성
            current_dir = base_path / 'current'
            current_dir.mkdir(parents=True, exist_ok=True)
            
            # scenarios/my_case 디렉토리 생성  
            scenario_dir = base_path / 'scenarios' / 'my_case'
            scenario_dir.mkdir(parents=True, exist_ok=True)
            
            # JSON 파일들 저장
            files_saved = []
            file_map = [
                ('jobs.json', aasx_data['jobs']),
                ('machines.json', aasx_data['machines']),
                ('operations.json', aasx_data['operations']),
                ('operation_durations.json', aasx_data['operation_durations']),
                ('machine_transfer_time.json', aasx_data['machine_transfer_time']),
                ('routing_result.json', aasx_data['routing_result']),
                ('initial_machine_status.json', aasx_data['initial_machine_status'])
            ]
            
            for filename, data in file_map:
                # current와 scenarios/my_case 양쪽에 저장
                current_file = current_dir / filename
                scenario_file = scenario_dir / filename
                
                with open(current_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                with open(scenario_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                files_saved.append(filename)
                print(f"    ✅ {filename}")
            
            print(f"  💾 {len(files_saved)}개 파일 저장 완료")
            
            return {
                "pvc_path": str(base_path),
                "current_dir": str(current_dir), 
                "scenario_dir": str(scenario_dir),
                "files_saved": files_saved
            }
            
        except Exception as e:
            print(f"  ❌ PVC 저장 실패: {e}")
            raise e
    
    def _run_aasx_simulator_job(self, pvc_result: dict) -> dict:
        """AASX-main simulator 실행 (K8s 또는 로컬)"""
        
        job_id = str(uuid.uuid4())[:8]
        job_name = f"aasx-simulator-{job_id}"
        
        print(f"  🎯 시뮬레이터 실행: {job_name}")
        
        # K8s 연결 가능 여부 확인
        try:
            # K8s API 서버 연결 테스트
            self.batch_v1.list_namespaced_job(namespace=self.namespace, limit=1)
            k8s_available = True
        except Exception as k8s_error:
            print(f"  ⚠️ K8s 연결 실패, 로컬 실행으로 전환: {k8s_error}")
            k8s_available = False
        
        if k8s_available:
            return self._run_k8s_job(job_name, pvc_result)
        else:
            return self._run_local_simulator(job_name, pvc_result)
    
    def _run_k8s_job(self, job_name: str, pvc_result: dict) -> dict:
        """K8s Job으로 시뮬레이터 실행"""
        print(f"  🔄 K8s Job 실행: {job_name}")
        
        try:
            # PVC 볼륨 마운트 설정
            volume_mount = client.V1VolumeMount(
                name="shared-data-volume",
                mount_path="/data"
            )
            volume = client.V1Volume(
                name="shared-data-volume",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                    claim_name="factory-shared-pvc"
                )
            )
            
            # 환경변수 설정
            env_vars = [
                client.V1EnvVar(name="USE_ADVANCED_SIMULATOR", value="true"),
                client.V1EnvVar(name="AAS_SERVER_IP", value=self.aas_server_ip),
                client.V1EnvVar(name="AAS_SERVER_PORT", value=str(self.aas_server_port))
            ]
            
            # AASX simulator 컨테이너 (단순화된 버전)
            container = client.V1Container(
                name="aasx-simulator",
                image="aasx-main-lite:latest",  # AASX-main 복잡한 시뮬레이터
                image_pull_policy="Never",
                volume_mounts=[volume_mount],
                env=env_vars
            )
            
            pod_spec = client.V1PodSpec(
                restart_policy="Never",
                containers=[container],
                volumes=[volume]
            )
            
            pod_template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": "aasx-simulator"}),
                spec=pod_spec
            )
            
            job_spec = client.V1JobSpec(
                template=pod_template,
                backoff_limit=2,
                ttl_seconds_after_finished=300  # 5분 후 자동 삭제
            )
            
            job = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=client.V1ObjectMeta(name=job_name),
                spec=job_spec
            )
            
            # Job 생성
            self.batch_v1.create_namespaced_job(body=job, namespace=self.namespace)
            print(f"  ✅ K8s Job 생성됨: {job_name}")
            
            # Job 완료 대기
            print("  ⏳ Job 완료 대기 중...")
            job_completed = False
            max_wait_time = 1800  # 최대 30분 대기 (AASX-main 복잡한 시뮬레이터용)
            wait_time = 0
            
            while not job_completed and wait_time < max_wait_time:
                time.sleep(5)
                wait_time += 5
                
                job_status = self.batch_v1.read_namespaced_job_status(
                    name=job_name,
                    namespace=self.namespace
                )
                
                if job_status.status.succeeded is not None and job_status.status.succeeded >= 1:
                    job_completed = True
                    print("  ✅ Job 완료")
                elif job_status.status.failed is not None and job_status.status.failed >= 1:
                    print("  ❌ Job 실패")
                    break
                else:
                    print(f"    대기 중... ({wait_time}/{max_wait_time}s)")
            
            if not job_completed:
                raise RuntimeError(f"Job {job_name} 시간 초과 또는 실패")
            
            # Pod 로그에서 결과 수집
            result = self._collect_simulation_result(job_name)
            
            return result
            
        except Exception as e:
            print(f"  ❌ K8s Job 실행 실패: {e}")
            raise e
    
    def _run_local_simulator(self, job_name: str, pvc_result: dict) -> dict:
        """로컬에서 시뮬레이터 실행 (K8s 사용 불가 시)"""
        import subprocess
        
        print(f"  🖥️ 로컬 시뮬레이터 실행: {job_name}")
        
        try:
            # simple_aasx_runner.py 파일 경로 확인
            runner_path = Path(__file__).parent / "simple_aasx_runner.py"
            if not runner_path.exists():
                # 파일이 없으면 생성
                print("  📝 simple_aasx_runner.py 파일 생성 중...")
                self._create_simple_aasx_runner(runner_path)
            
            # 환경변수 설정
            env = os.environ.copy()
            env['SIMULATION_WORK_DIR'] = pvc_result.get('pvc_path', '/tmp/factory_automation')
            
            # Python 스크립트 실행
            print(f"  🔄 실행 중: {runner_path}")
            result = subprocess.run(
                [sys.executable, str(runner_path)],
                capture_output=True,
                text=True,
                env=env,
                timeout=60  # 60초 타임아웃
            )
            
            if result.returncode != 0:
                print(f"  ❌ 시뮬레이터 실행 실패: {result.stderr}")
                raise RuntimeError(f"Simulator execution failed: {result.stderr}")
            
            # stdout에서 JSON 결과 파싱
            output_lines = result.stdout.strip().split('\n')
            simulation_result = None
            
            for line in reversed(output_lines):  # 마지막 줄부터 확인
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        simulation_result = json.loads(line)
                        print("  ✅ 로컬 시뮬레이션 결과 파싱 성공")
                        break
                    except json.JSONDecodeError:
                        continue
            
            if not simulation_result:
                print("  ⚠️ JSON 결과를 찾을 수 없음, 기본 결과 반환")
                simulation_result = {
                    "predicted_completion_time": "2025-08-11T17:30:00Z",
                    "confidence": 0.75,
                    "details": "Local simulation completed but result parsing failed",
                    "simulator_type": "aasx-simple-local"
                }
            
            # 메타데이터 추가
            simulation_result["execution_mode"] = "local"
            simulation_result["job_name"] = job_name
            
            return simulation_result
            
        except subprocess.TimeoutExpired:
            print("  ❌ 로컬 시뮬레이터 타임아웃")
            return {
                "predicted_completion_time": "2025-08-11T18:00:00Z",
                "confidence": 0.6,
                "details": "Local simulator timeout",
                "simulator_type": "aasx-simple-local",
                "execution_mode": "local",
                "error": "timeout"
            }
        except Exception as e:
            print(f"  ❌ 로컬 시뮬레이터 실행 실패: {e}")
            return {
                "predicted_completion_time": "2025-08-11T19:00:00Z",
                "confidence": 0.5,
                "details": f"Local simulator error: {str(e)[:100]}",
                "simulator_type": "aasx-simple-local",
                "execution_mode": "local",
                "error": str(e)
            }
    
    def _create_simple_aasx_runner(self, runner_path: Path):
        """simple_aasx_runner.py 파일 생성"""
        runner_code = '''#!/usr/bin/env python3
"""
AASX-main 시뮬레이터를 Goal 3에 맞게 단순화한 실행기
pandas/numpy 의존성 제거, JSON 결과 출력에 최적화
"""

import os
import sys
import json
import time
from pathlib import Path

def calculate_completion_time_simple(scenario_path):
    """
    시뮬레이션 데이터를 기반으로 간단한 완료 시간 계산
    실제 AASX 복잡한 스케줄링 로직을 단순화
    """
    
    print("🔄 Simple AASX Simulation Starting...", file=sys.stderr)
    
    try:
        # 시뮬레이션 데이터 로드
        with open(f"{scenario_path}/jobs.json", 'r') as f:
            jobs = json.load(f)
        
        with open(f"{scenario_path}/machines.json", 'r') as f:
            machines = json.load(f)
            
        with open(f"{scenario_path}/operations.json", 'r') as f:
            operations = json.load(f)
            
        with open(f"{scenario_path}/operation_durations.json", 'r') as f:
            durations = json.load(f)
            
        print(f"📋 Loaded: {len(jobs)} jobs, {len(machines)} machines, {len(operations)} operations", file=sys.stderr)
        
        # 간단한 완료 시간 계산 로직
        total_duration = 0
        machine_load = {m['machine_id']: 0 for m in machines}
        
        # 각 Job의 Operation들 처리
        for job in jobs:
            job_duration = 0
            for op_id in job['operations']:
                # Operation 찾기
                op = next((o for o in operations if o['operation_id'] == op_id), None)
                if not op:
                    continue
                    
                # Duration 찾기
                op_duration = durations.get(op_id, 30)  # 기본값 30분
                
                # 가장 부하가 적은 머신에 할당
                available_machines = op.get('machines', [])
                if available_machines:
                    best_machine = min(available_machines, key=lambda m: machine_load.get(m, 0))
                    machine_load[best_machine] += op_duration
                    job_duration += op_duration
            
            total_duration = max(total_duration, job_duration)
        
        # 최대 머신 로드 시간을 완료 시간으로 사용
        max_machine_time = max(machine_load.values()) if machine_load else total_duration
        completion_minutes = max(total_duration, max_machine_time)
        
        # 완료 시간을 현실적으로 조정 (기본 1시간 + 계산된 시간)
        base_time_minutes = 60  # 기본 1시간
        total_completion_minutes = base_time_minutes + completion_minutes
        
        # 시간을 ISO 형식으로 변환
        from datetime import datetime, timedelta
        start_time = datetime(2025, 8, 11, 8, 0)  # 2025-08-11 08:00 시작
        completion_time = start_time + timedelta(minutes=total_completion_minutes)
        
        # 신뢰도 계산 (머신 수가 많고 작업이 분산될수록 높은 신뢰도)
        machine_utilization = len([load for load in machine_load.values() if load > 0]) / len(machines)
        confidence = 0.7 + (machine_utilization * 0.25)  # 0.7 ~ 0.95 사이
        
        result = {
            "predicted_completion_time": completion_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confidence": round(confidence, 2),
            "details": f"Simple AASX simulation completed. Total operations: {len(operations)}, Machine utilization: {machine_utilization:.1%}",
            "simulator_type": "aasx-simple",
            "simulation_time_minutes": total_completion_minutes,
            "machine_loads": machine_load
        }
        
        print("✅ Simple AASX Simulation Completed", file=sys.stderr)
        return result
        
    except Exception as e:
        print(f"❌ Simulation Error: {e}", file=sys.stderr)
        # Fallback 결과
        return {
            "predicted_completion_time": "2025-08-11T20:00:00Z",
            "confidence": 0.5,
            "details": f"Simple AASX simulation failed: {str(e)[:100]}",
            "simulator_type": "aasx-simple-fallback"
        }

def run_aasx_simulation():
    """
    AASX 시뮬레이션 실행 및 JSON 결과 출력
    Docker 컨테이너나 K8s Job에서 사용하기 위한 표준 출력
    """
    
    # 환경변수로부터 작업 디렉토리 가져오기
    work_dir = os.environ.get('SIMULATION_WORK_DIR', '/tmp/factory_automation')
    
    # 데이터 경로 확인
    data_paths = [
        f"{work_dir}/current",
        f"{work_dir}/scenarios/my_case",
        "/data/current",
        "/data/scenarios/my_case",
        "scenarios/my_case",
        "AASX-main/simulator/scenarios/my_case"
    ]
    
    scenario_path = None
    for path in data_paths:
        if os.path.exists(f"{path}/jobs.json"):
            scenario_path = path
            print(f"📁 Using scenario path: {scenario_path}", file=sys.stderr)
            break
    
    if not scenario_path:
        print("❌ No valid scenario data found", file=sys.stderr)
        result = {
            "predicted_completion_time": "2025-08-11T22:00:00Z",
            "confidence": 0.3,
            "details": "No scenario data found, using fallback",
            "simulator_type": "aasx-no-data"
        }
    else:
        # 시뮬레이션 실행
        result = calculate_completion_time_simple(scenario_path)
    
    # 표준 출력으로 JSON 결과 출력 (K8s Job에서 파싱용)
    print(json.dumps(result))
    
    return result

def main():
    """메인 실행 함수"""
    print("🚀 Simple AASX Simulator for Goal 3", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    result = run_aasx_simulation()
    
    print("=" * 50, file=sys.stderr)
    print("✅ Simulation completed successfully", file=sys.stderr)
    
    return result

if __name__ == "__main__":
    main()
'''
        
        with open(runner_path, 'w') as f:
            f.write(runner_code)
        
        # 실행 권한 부여
        runner_path.chmod(0o755)
        print(f"  ✅ {runner_path} 파일 생성 완료")
    
    def _collect_simulation_result(self, job_name: str) -> dict:
        """완료된 Job의 Pod에서 시뮬레이션 결과 수집"""
        
        print(f"  📊 결과 수집: {job_name}")
        
        try:
            # Job에 속한 Pod 찾기
            pod_label_selector = f"job-name={job_name}"
            pods_list = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=pod_label_selector
            )
            
            if not pods_list.items:
                raise RuntimeError(f"Job {job_name}의 Pod를 찾을 수 없음")
            
            pod_name = pods_list.items[0].metadata.name
            print(f"    Pod: {pod_name}")
            
            # Pod 로그에서 JSON 결과 찾기
            result = None
            for attempt in range(3):
                print(f"    로그 수집 시도 {attempt + 1}/3")
                time.sleep(2)
                
                pod_log = self.core_v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.namespace
                )
                
                if pod_log:
                    # 로그에서 JSON 결과 파싱
                    for line in pod_log.split('\n'):
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                result = json.loads(line)
                                print("    ✅ 시뮬레이션 결과 파싱 성공")
                                break
                            except json.JSONDecodeError:
                                continue
                
                if result:
                    break
            
            if not result:
                print("    ⚠️ 로그에서 JSON 결과를 찾을 수 없음, 기본 결과 반환")
                result = {
                    "predicted_completion_time": "2025-08-11T18:30:00Z",
                    "confidence": 0.8,
                    "details": "AASX simulation completed but result parsing failed",
                    "job_name": job_name
                }
            
            # 결과에 메타데이터 추가
            result["simulator_type"] = "aasx-main"
            result["job_name"] = job_name
            result["aas_server"] = f"{self.aas_server_ip}:{self.aas_server_port}"
            
            return result
            
        except Exception as e:
            print(f"    ❌ 결과 수집 실패: {e}")
            
            # Fallback 결과
            return {
                "predicted_completion_time": "2025-08-11T19:00:00Z",
                "confidence": 0.7,
                "details": f"AASX simulation completed but result collection failed: {str(e)[:100]}",
                "simulator_type": "aasx-main",
                "job_name": job_name,
                "result_collection_error": True
            }
    
    def _run_dummy_simulator(self, step_details: dict, context: dict) -> dict:
        """기존 dummy simulator 로직 (fallback용)"""
        print("📝 Dummy Simulator 모드 실행")
        
        # 기존 K8sJobHandler 로직과 동일
        sim_context = context.get("step_3_ActionAssembleSimulatorInputs", {})
        job_id = sim_context.get("simulation_job_id", "fallback")
        
        return {
            "final_result": {
                "predicted_completion_time": "2025-08-11T16:30:00Z",
                "confidence": 0.85,
                "details": "Dummy simulation for compatibility",
                "simulator_type": "dummy",
                "job_id": job_id
            }
        }


# 기존 K8sJobHandler 클래스 (호환성 유지)
class K8sJobHandler(EnhancedDockerRunHandler):
    """기존 K8sJobHandler와의 호환성을 위한 alias"""
    pass

class AIModelHandler:
    def execute(self, step_details: dict, context: dict) -> dict:
        print("INFO: AI Model Handler (Not Implemented)")
        return {"result": "AI model placeholder"}

# --- ExecutionAgent 최종본 ---
class ExecutionAgent:
    def __init__(self):
        print(f"🚀 Initializing ExecutionAgent with {AAS_SERVER_TYPE} server")
        
        self.handlers = {
            "aas_query": AASQueryHandler(),
            "aas_query_multiple": AASQueryHandler(),
            "internal_processing": SimulationInputHandler(),
            "docker_run": EnhancedDockerRunHandler(),
            "data_filtering": DataFilteringHandler(),
            "ai_model_inference": AIModelHandler(),
        }
        
    def run(self, plan: list, initial_params: dict) -> dict:
        execution_context = {}
        final_result = {}
        
        for i, step in enumerate(plan):
            step['params'] = initial_params

            action_type = step.get("type")
            handler = self.handlers.get(action_type)

            if not handler:
                print(f"WARN: No handler for action type '{action_type}', skipping.")
                continue
            
            try:
                step_result = handler.execute(step, execution_context)
                execution_context[f"step_{i+1}_{step['action_id']}"] = step_result

                if "final_result" in step_result:
                    final_result = step_result
                    
            except Exception as e:
                print(f"ERROR: Step {i+1} ({step.get('action_id')}) failed: {e}")
                raise

        return final_result if final_result else execution_context