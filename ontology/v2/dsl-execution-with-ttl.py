#!/usr/bin/env python3
"""
DSL 입력부터 실행 계획 생성까지 - TTL 파일 로드 버전
필요 라이브러리: pip install rdflib
필요 파일: 
  - execution-ontology.ttl
  - domain-ontology.ttl  
  - bridge-ontology.ttl
  - test_data.json (선택사항)
"""

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os,json

class OntologyBasedExecutionPlanner:
    def __init__(self, 
                 exec_ttl: str = "execution-ontology.ttl",
                 domain_ttl: str = "domain-ontology.ttl", 
                 bridge_ttl: str = "bridge-ontology.ttl",
                 test_data_json: str = "test_data.json"):
        
        # 네임스페이스 정의
        self.EXEC = Namespace("http://example.org/execution-ontology#")
        self.PROD = Namespace("http://example.org/production-domain#")
        self.BRIDGE = Namespace("http://example.org/bridge-ontology#")
        
        # 3개의 그래프 초기화
        self.exec_graph = Graph()
        self.domain_graph = Graph()
        self.bridge_graph = Graph()
        
        # 네임스페이스 바인딩
        self._bind_namespaces()
        
        # 실행 파일의 디렉토리 경로 가져오기
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # TTL 파일 경로를 실행 파일 기준으로 설정
        self.exec_ttl = os.path.join(self.base_dir, exec_ttl)
        self.domain_ttl = os.path.join(self.base_dir, domain_ttl)
        self.bridge_ttl = os.path.join(self.base_dir, bridge_ttl)
        self.test_data_json = os.path.join(self.base_dir, test_data_json)
        
        # 온톨로지 로드
        self._load_ontologies()
        self._load_action_metadata()  # ← 새로 추가
        # 테스트 데이터 로드
        self._load_test_data()
        
    def _bind_namespaces(self):
        """네임스페이스 바인딩"""
        for graph in [self.exec_graph, self.domain_graph, self.bridge_graph]:
            graph.bind("exec", self.EXEC)
            graph.bind("prod", self.PROD)
            graph.bind("bridge", self.BRIDGE)
            graph.bind("rdf", RDF)
            graph.bind("rdfs", RDFS)
            graph.bind("owl", OWL)
            graph.bind("xsd", XSD)
    
    def _load_ontologies(self):
        """3개의 온톨로지 TTL 파일 로드"""
        print("📚 온톨로지 TTL 파일 로드 중...")
        print(f"   기준 디렉토리: {self.base_dir}")
        
        # 실행 온톨로지 로드
        try:
            self.exec_graph.parse(self.exec_ttl, format="turtle")
            print(f"✅ 실행 온톨로지 로드 성공: {os.path.basename(self.exec_ttl)}")
            print(f"   - {len(self.exec_graph)} 트리플")
        except Exception as e:
            print(f"❌ 실행 온톨로지 로드 실패: {e}")
            print(f"   파일 경로: {self.exec_ttl}")
            raise
        
        # 도메인 온톨로지 로드
        try:
            self.domain_graph.parse(self.domain_ttl, format="turtle")
            print(f"✅ 도메인 온톨로지 로드 성공: {os.path.basename(self.domain_ttl)}")
            print(f"   - {len(self.domain_graph)} 트리플")
        except Exception as e:
            print(f"❌ 도메인 온톨로지 로드 실패: {e}")
            print(f"   파일 경로: {self.domain_ttl}")
            raise
        
        # 브리지 온톨로지 로드
        try:
            self.bridge_graph.parse(self.bridge_ttl, format="turtle")
            print(f"✅ 브리지 온톨로지 로드 성공: {os.path.basename(self.bridge_ttl)}")
            print(f"   - {len(self.bridge_graph)} 트리플")
        except Exception as e:
            print(f"❌ 브리지 온톨로지 로드 실패: {e}")
            print(f"   파일 경로: {self.bridge_ttl}")
            raise
        
        # 온톨로지 내용 검증
        self._validate_ontologies()
    
    def _validate_ontologies(self):
        """로드된 온톨로지 검증"""
        print("\n🔍 온톨로지 검증 중...")
        
        # Goal 확인 - rdf:type 사용
        query = """
        PREFIX exec: <http://example.org/execution-ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?goal ?label WHERE {
            ?goal rdf:type ?goalType .
            ?goalType rdfs:subClassOf* exec:Goal .
            OPTIONAL { ?goal rdfs:label ?label }
        }
        """
        goals = list(self.exec_graph.query(query))
        print(f"   - Goal 개수: {len(goals)}")
        for goal, label in goals:
            print(f"     • {label if label else str(goal).split('#')[-1]}")
        
        # Action 확인 - rdf:type 사용
        query = """
        PREFIX exec: <http://example.org/execution-ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?action WHERE {
            ?action rdf:type ?actionType .
            ?actionType rdfs:subClassOf* exec:Action .
        }
        """
        actions = list(self.exec_graph.query(query))
        print(f"   - Action 개수: {len(actions)}")
        
        # Machine 확인
        query = """
        PREFIX prod: <http://example.org/production-domain#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?machine WHERE {
            ?machine rdf:type prod:Machine .
        }
        """
        machines = list(self.domain_graph.query(query))
        print(f"   - Machine 개수: {len(machines)}")
    
    def _load_test_data(self):
        """테스트 데이터 로드"""
        print("\n📊 테스트 데이터 로드 중...")
        print(f"   기준 디렉토리: {self.base_dir}")
        
        # JSON 파일에서 테스트 데이터 로드
        if os.path.exists(self.test_data_json):
            try:
                with open(self.test_data_json, "r", encoding="utf-8") as f:
                    test_data = json.load(f)
                self._load_json_to_graph(test_data)
                print(f"✅ 테스트 데이터 로드 성공: {os.path.basename(self.test_data_json)}")
            except Exception as e:
                print(f"⚠️ 테스트 데이터 로드 실패: {e}")
                print("   샘플 데이터를 생성합니다...")
                self._create_sample_test_data()
        else:
            print(f"⚠️ 테스트 데이터 파일이 없습니다: {os.path.basename(self.test_data_json)}")
            print("   샘플 데이터를 생성합니다...")
            self._create_sample_test_data()
    
    def _load_json_to_graph(self, test_data: Dict):
        """JSON 테스트 데이터를 그래프에 추가"""
        # Machine 데이터 추가
        if "machines" in test_data:
            for machine in test_data["machines"]:
                machine_uri = self.PROD[machine["id"]]
                self.domain_graph.add((machine_uri, RDF.type, self.PROD.Machine))
                self.domain_graph.add((machine_uri, self.PROD.hasStatus, Literal(machine["status"])))
                self.domain_graph.add((machine_uri, self.PROD.hasCapability, 
                                     self.PROD[machine["capability"].title() + "Capability"]))
                if "aasEndpoint" in machine:
                    endpoint = URIRef(machine["aasEndpoint"])
                    self.domain_graph.add((machine_uri, self.PROD.hasAASEndpoint, endpoint))
        
        # Job 데이터 추가
        if "jobs" in test_data:
            for job in test_data["jobs"]:
                job_uri = self.PROD[job["id"]]
                self.domain_graph.add((job_uri, RDF.type, self.PROD.Job))
                self.domain_graph.add((job_uri, self.PROD.hasStatus, Literal(job["status"])))
                
                if job.get("requiresCooling"):
                    self.domain_graph.add((job_uri, self.PROD.requiresCooling, 
                                         Literal(True, datatype=XSD.boolean)))
                if job.get("requiresHeating"):
                    self.domain_graph.add((job_uri, self.PROD.requiresHeating, 
                                         Literal(True, datatype=XSD.boolean)))
                
                if "startTime" in job:
                    self.domain_graph.add((job_uri, self.PROD.hasStartTime, 
                                         Literal(job["startTime"], datatype=XSD.dateTime)))
                
                if job.get("executedOn"):
                    if isinstance(job["executedOn"], list):
                        machine_id = job["executedOn"][0] if job["executedOn"] else None
                    else:
                        machine_id = job["executedOn"]
                    
                    if machine_id:
                        self.domain_graph.add((job_uri, self.PROD.executedOn, self.PROD[machine_id]))
                
                if job.get("forProduct"):
                    self.domain_graph.add((job_uri, self.PROD.forProduct, self.PROD[job["forProduct"]]))
                
                if job.get("currentOperationIndex"):
                    self.domain_graph.add((job_uri, self.PROD.currentOperationIndex, 
                                         Literal(job["currentOperationIndex"], datatype=XSD.integer)))
    
    def _create_sample_test_data(self):
        """샘플 테스트 데이터 생성"""
        # 기본 샘플 데이터 추가
        sample_data = {
            "machines": [
                {"id": "CoolingMachine-01", "capability": "cooling", "status": "Active"},
                {"id": "CoolingMachine-02", "capability": "cooling", "status": "Active"}
            ],
            "jobs": [
                {
                    "id": "Job-101",
                    "status": "Failed",
                    "requiresCooling": True,
                    "startTime": "2025-07-17T10:00:00",
                    "executedOn": "CoolingMachine-01"
                },
                {
                    "id": "Job-102",
                    "status": "Success",
                    "requiresCooling": True,
                    "startTime": "2025-07-17T11:00:00",
                    "executedOn": "CoolingMachine-02"
                }
            ]
        }
        self._load_json_to_graph(sample_data)
    
    def process_dsl(self, dsl_input: Dict[str, Any]) -> Dict[str, Any]:
        """DSL 입력을 처리하여 실행 계획 생성"""
        print(f"\n🚀 DSL 처리 시작: {dsl_input['goal']}")
        print(f"입력: {json.dumps(dsl_input, indent=2)}")
        
        # Step 1: Goal 매핑 찾기
        goal_name = dsl_input["goal"]
        execution_goal = self._find_execution_goal(goal_name)
        
        if not execution_goal:
            return {"error": f"Unknown goal: {goal_name}"}
        
        print(f"\n✅ Step 1: Goal 매핑 완료")
        print(f"   {goal_name} → {execution_goal}")
        
        # Step 2: 필요한 Action들 찾기
        actions = self._find_required_actions(execution_goal)
        print(f"\n✅ Step 2: 필요한 Action 식별")
        for action in actions:
            print(f"   - {action['name']} (order: {action['order']})")
        
        # Step 3: 파라미터 매핑
        parameter_mappings = self._map_parameters(goal_name, dsl_input)
        print(f"\n✅ Step 3: 파라미터 매핑")
        for key, value in parameter_mappings.items():
            print(f"   {key}: {value}")
        
        # Step 4: 실행 계획 생성
        execution_plan = self._generate_execution_plan(
            goal_name,
            dsl_input,
            execution_goal,
            actions,
            parameter_mappings
        )
        
        print(f"\n✅ Step 4: 실행 계획 생성 완료")
        
        return execution_plan
    
    def _find_execution_goal(self, goal_name: str) -> Optional[URIRef]:
        """Goal 이름으로 실행 Goal 찾기"""
        # Bridge 온톨로지에서 매핑 찾기
        query = f"""
        PREFIX bridge: <{self.BRIDGE}>
        PREFIX exec: <{self.EXEC}>
        
        SELECT ?execGoal
        WHERE {{
            ?mapping bridge:mapsGoal "{goal_name}" ;
                     bridge:toExecutionGoal ?execGoal .
        }}
        """
        
        results = list(self.bridge_graph.query(query))
        if results:
            return results[0][0]
        
        # 직접 매핑 시도
        query2 = f"""
        PREFIX exec: <{self.EXEC}>
        PREFIX rdfs: <{RDFS}>
        
        SELECT ?goal
        WHERE {{
            ?goal rdfs:label "{goal_name}" .
        }}
        """
        
        results2 = list(self.exec_graph.query(query2))
        if results2:
            return results2[0][0]
        
        return None
    
    def _find_required_actions(self, execution_goal: URIRef) -> List[Dict]:
        """Goal에 필요한 Action들 찾기"""
        query = f"""
        PREFIX exec: <{self.EXEC}>
        PREFIX rdfs: <{RDFS}>
        
        SELECT ?action ?type ?order
        WHERE {{
            <{execution_goal}> exec:requiresAction ?action .
            OPTIONAL {{ ?action exec:actionType ?type }}
            OPTIONAL {{ ?action exec:executionOrder ?order }}
        }}
        ORDER BY ?order
        """
        
        results = self.exec_graph.query(query)
        
        actions = []
        for action, action_type, order in results:
            actions.append({
                "uri": action,
                "name": str(action).split('#')[-1],
                "type": str(action_type).split('#')[-1] if action_type else "Unknown",
                "order": int(order) if order else 0
            })
        
        return sorted(actions, key=lambda x: x["order"])
    
    def _map_parameters(self, goal_name: str, dsl_input: Dict) -> Dict:
        """DSL 파라미터를 도메인 개념으로 매핑"""
        mappings = {}
        
        # Bridge 온톨로지에서 암묵적 필터 찾기
        query = f"""
        PREFIX bridge: <{self.BRIDGE}>
        PREFIX prod: <{self.PROD}>
        
        SELECT ?property ?value
        WHERE {{
            ?mapping bridge:mapsGoal "{goal_name}" .
            ?mapping bridge:hasImplicitFilter ?filter .
            ?filter bridge:filterProperty ?property .
            ?filter bridge:filterValue ?value .
        }}
        """
        
        results = self.bridge_graph.query(query)
        
        for prop, value in results:
            prop_name = str(prop).split('#')[-1]
            mappings[prop_name] = value.value if hasattr(value, 'value') else str(value)
        
        # DSL 파라미터 추가
        if "date" in dsl_input:
            mappings["dateFilter"] = dsl_input["date"]
        
        # Goal별 추가 매핑
        if goal_name == "detect_anomaly_for_product":
            mappings["product_id"] = dsl_input.get("product_id")
            mappings["date_range"] = dsl_input.get("date_range")
            mappings["target_machine"] = dsl_input.get("target_machine")
        elif goal_name == "predict_first_completion_time":
            mappings["product_id"] = dsl_input.get("product_id")
            mappings["quantity"] = dsl_input.get("quantity")
        elif goal_name == "track_product_position":
            mappings["product_id"] = dsl_input.get("product_id")
            mappings["statusFilter"] = "Processing"
        
        return mappings
    
    def _generate_execution_plan(self, goal_name: str, dsl_input: Dict, 
                            execution_goal: URIRef, actions: List[Dict],
                            parameter_mappings: Dict) -> Dict:
        """실행 계획 생성"""
        
        execution_steps = []
        
        for idx, action in enumerate(actions):
            action_name = action["name"]
            metadata = self.action_metadata.get(action_name, {})
            
            step = {
                "stepId": idx + 1,
                "action": action_name,
                "type": action["type"],
                "parameters": {}
            }
            
            # 온톨로지에서 로드한 메타데이터 사용
            if metadata.get('outputName'):
                step["output"] = metadata['outputName']
            
            # Action 타입별 처리
            if "QueryBuilder" in action_name or action_name.startswith("Build"):
                # 쿼리 빌더 처리
                if metadata.get('queryTemplate'):
                    step["generatedQuery"] = self._process_query_template(
                        metadata['queryTemplate'], 
                        parameter_mappings, 
                        dsl_input
                    )
                
            elif ("Execute" in action_name and "Query" in action_name) or action_name == "ExecuteProductTrace":
                # 쿼리 실행 처리
                step["input"] = metadata.get('inputMapping', '')
                step["endpoint"] = metadata.get('endpointTemplate', '')
                
                # 실제 쿼리 실행 (시뮬레이션)
                if action_name == "ExecuteJobQuery":
                    sample_results = self._execute_job_query(parameter_mappings)
                elif action_name == "ExecuteProductTrace":
                    sample_results = self._execute_product_trace_query(dsl_input)
                elif action_name == "ExecuteLocationQuery":
                    sample_results = self._execute_location_query(dsl_input)
                else:
                    sample_results = []
                
                step["expectedResultCount"] = len(sample_results)
                step["sampleResults"] = sample_results[:3]
                
            elif action_name == "FetchSensorData":
                # AAS 커넥터 처리
                endpoint = metadata.get('endpointTemplate', '')
                step["endpoint"] = endpoint.format(**dsl_input)
    
            elif action_name == "FetchJobTemplate":
                # FetchJobTemplate 특별 처리
                step["input"] = metadata.get('inputMapping', '')
                step["endpoint"] = metadata.get('endpointTemplate', '')
                
                sample_results = self._execute_job_template_query(dsl_input)
                step["expectedResultCount"] = len(sample_results)
                step["sampleResults"] = sample_results[:3]
                
            elif action_name == "FetchMachineSchedule":
                # 머신 스케줄 처리
                if metadata.get('queryTemplate'):
                    step["generatedQuery"] = metadata['queryTemplate']
                    
            elif "RunAnomalyDetection" in action_name or "RunSimulation" in action_name:
                # Docker 실행 처리
                step["model"] = metadata.get('dockerImage', '')
                
                if metadata.get('inputMapping'):
                    input_mapping = metadata['inputMapping']
                    # JSON 문자열을 파싱하고 템플릿 변수 치환
                    import json
                    try:
                        input_dict = json.loads(input_mapping)
                        # 템플릿 변수 치환
                        for key, value in input_dict.items():
                            if isinstance(value, str):
                                value = value.replace("%%PRODUCT_ID%%", dsl_input.get('product_id', ''))
                                value = value.replace("%%QUANTITY%%", str(dsl_input.get('quantity', 1)))
                            input_dict[key] = value
                        step["input"] = input_dict
                    except:
                        processed_input = input_mapping
                        processed_input = processed_input.replace("%%PRODUCT_ID%%", dsl_input.get('product_id', ''))
                        processed_input = processed_input.replace("%%QUANTITY%%", str(dsl_input.get('quantity', 1)))
                        try:
                            step["input"] = json.loads(processed_input)
                        except:
                            step["input"] = processed_input
                        
            elif "Enrich" in action_name:
                # 데이터 보강 처리
                step["input"] = metadata.get('inputMapping', '')
                if metadata.get('enrichmentType'):
                    enrichment_types = metadata['enrichmentType'].split(',')
                    step["enrichments"] = []
                    for etype in enrichment_types:
                        if etype == "fetchMachineDetails":
                            step["enrichments"].append({"type": etype, "source": "AAS"})
                        elif etype == "parseErrorLogs":
                            step["enrichments"].append({"type": etype, "source": "Domain"})
                        elif etype == "addOperationDetails":
                            step["enrichments"].append({"type": etype, "source": "Domain"})
                        elif etype == "calculateProgress":
                            step["enrichments"].append({"type": etype, "source": "Compute"})
            
            execution_steps.append(step)
        
        # 최종 실행 계획 (기존과 동일)
        execution_plan = {
            "executionId": f"exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "goal": goal_name,
            "inputParameters": dsl_input,
            "parameterMappings": parameter_mappings,
            "executionSteps": execution_steps,
            "expectedOutput": {
                "type": self._get_result_type(goal_name),
                "format": "JSON"
            },
            "estimatedDuration": f"~{len(actions) * 0.5 + 1} seconds"
        }
        
        return execution_plan
    
    def _build_job_query(self, params: Dict) -> str:
        """Job 조회 쿼리 생성"""
        filters = []
        if params.get("requiresCooling"):
            filters.append("?job prod:requiresCooling true")
        if params.get("hasStatus"):
            filters.append(f'?job prod:hasStatus "{params["hasStatus"]}"')
        if params.get("dateFilter"):
            filters.append(f'FILTER(STRSTARTS(STR(?startTime), "{params["dateFilter"]}"))')
        
        query = f"""
        PREFIX prod: <{self.PROD}>
        PREFIX rdf: <{RDF}>
        
        SELECT ?job ?machine ?startTime ?status
        WHERE {{
            ?job rdf:type prod:Job .
            ?job prod:hasStartTime ?startTime .
            ?job prod:hasStatus ?status .
            {' . '.join(filters)}
            OPTIONAL {{ ?job prod:executedOn ?machine }}
        }}
        ORDER BY DESC(?startTime)
        LIMIT 100
        """
        
        return query.strip()
    
    def _build_product_trace_query(self, dsl_input: Dict) -> str:
        """제품 추적 쿼리 생성"""
        product_id = dsl_input.get("product_id", "Unknown")
        date_range = dsl_input.get("date_range", {})
        
        query = f"""
        PREFIX prod: <{self.PROD}>
        PREFIX rdf: <{RDF}>
        
        SELECT ?job ?machine ?startTime ?status
        WHERE {{
            ?job rdf:type prod:Job .
            ?job prod:forProduct prod:{product_id} .
            ?job prod:executedOn ?machine .
            ?job prod:hasStartTime ?startTime .
            ?job prod:hasStatus ?status .
        """
        
        if date_range:
            # 날짜에 시간 정보 추가
            from_date = f"{date_range.get('from')}T00:00:00"
            to_date = f"{date_range.get('to')}T23:59:59"
            
            query += f"""
            FILTER(?startTime >= "{from_date}"^^xsd:dateTime && 
                ?startTime <= "{to_date}"^^xsd:dateTime)
            """
        
        query += """
        }
        ORDER BY ?startTime
        """
        
        return query.strip()
    
    def _build_job_template_query(self, dsl_input: Dict) -> str:
        """Job 템플릿 조회 쿼리"""
        product_id = dsl_input.get("product_id", "Unknown")
        
        query = f"""
        PREFIX prod: <{self.PROD}>
        PREFIX rdf: <{RDF}>
        
        SELECT ?operation ?machine ?duration
        WHERE {{
            prod:{product_id} prod:hasJobTemplate ?template .
            ?template prod:hasOperation ?operation .
            ?operation prod:canBeExecutedOn ?machine ;
                      prod:hasDuration ?duration .
        }}
        """
        
        return query.strip()
    
    def _build_location_query(self, dsl_input: Dict) -> str:
        """위치 조회 쿼리"""
        product_id = dsl_input.get("product_id", "Unknown")
        
        query = f"""
        PREFIX prod: <{self.PROD}>
        PREFIX rdf: <{RDF}>
        
        SELECT ?job ?status ?machine ?opIndex
        WHERE {{
            ?job rdf:type prod:Job .
            ?job prod:forProduct prod:{product_id} .
            ?job prod:hasStatus "Processing" .
            ?job prod:executedOn ?machine .
            OPTIONAL {{ ?job prod:currentOperationIndex ?opIndex }}
        }}
        """
        
        return query.strip()
    
    def _execute_job_query(self, params: Dict) -> List[Dict]:
        """Job 쿼리 실행 (시뮬레이션)"""
        # 실제 SPARQL 쿼리 실행
        query = self._build_job_query(params)
        
        # 쿼리를 도메인 그래프에서 실행
        results = []
        try:
            query_result = self.domain_graph.query(query)
            for row in query_result:
                results.append({
                    "job": str(row.job).split('#')[-1] if row.job else None,
                    "status": str(row.status) if hasattr(row, 'status') else None,
                    "machine": str(row.machine).split('#')[-1] if hasattr(row, 'machine') and row.machine else None,
                    "startTime": str(row.startTime) if hasattr(row, 'startTime') else None
                })
        except Exception as e:
            print(f"⚠️ 쿼리 실행 오류: {e}")
        
        return results
    
    def _execute_product_trace_query(self, dsl_input: Dict) -> List[Dict]:
        """제품 추적 쿼리 실행"""
        query = self._build_product_trace_query(dsl_input)
        
        results = []
        try:
            query_result = self.domain_graph.query(query)
            for row in query_result:
                results.append({
                    "job": str(row.job).split('#')[-1] if hasattr(row, 'job') and row.job else None,
                    "machine": str(row.machine).split('#')[-1] if hasattr(row, 'machine') and row.machine else None,
                    "startTime": str(row.startTime) if hasattr(row, 'startTime') else None,
                    "status": str(row.status) if hasattr(row, 'status') else None
                })
        except Exception as e:
            print(f"⚠️ 제품 추적 쿼리 실행 오류: {e}")
        
        return results
    
    def _execute_job_template_query(self, dsl_input: Dict) -> List[Dict]:
        """Job 템플릿 쿼리 실행"""
        query = self._build_job_template_query(dsl_input)
        
        results = []
        try:
            query_result = self.domain_graph.query(query)
            for row in query_result:
                results.append({
                    "operation": str(row.operation).split('#')[-1] if hasattr(row, 'operation') and row.operation else None,
                    "machine": str(row.machine).split('#')[-1] if hasattr(row, 'machine') and row.machine else None,
                    "duration": float(row.duration) if hasattr(row, 'duration') and row.duration else None
                })
        except Exception as e:
            print(f"⚠️ Job 템플릿 쿼리 실행 오류: {e}")
        
        return results
    
    def _execute_location_query(self, dsl_input: Dict) -> List[Dict]:
        """위치 쿼리 실행"""
        query = self._build_location_query(dsl_input)
        
        results = []
        try:
            query_result = self.domain_graph.query(query)
            for row in query_result:
                results.append({
                    "job": str(row.job).split('#')[-1] if hasattr(row, 'job') and row.job else None,
                    "status": str(row.status) if hasattr(row, 'status') else None,
                    "machine": str(row.machine).split('#')[-1] if hasattr(row, 'machine') and row.machine else None,
                    "operationIndex": int(row.opIndex) if hasattr(row, 'opIndex') and row.opIndex else None
                })
        except Exception as e:
            print(f"⚠️ 위치 쿼리 실행 오류: {e}")
        
        return results
    
    def _build_machine_schedule_query(self) -> str:
        """머신 스케줄 조회 쿼리"""
        query = f"""
        PREFIX prod: <{self.PROD}>
        PREFIX rdf: <{RDF}>
        
        SELECT ?machine ?status ?capability
        WHERE {{
            ?machine rdf:type prod:Machine .
            ?machine prod:hasStatus ?status .
            OPTIONAL {{ ?machine prod:hasCapability ?capability }}
        }}
        """
        
        return query.strip()
    
    def _get_result_type(self, goal_name: str) -> str:
        """Goal에 따른 결과 타입 반환"""
        result_types = {
            "query_failed_jobs_with_cooling": "JobReport",
            "detect_anomaly_for_product": "AnomalyReport",
            "predict_first_completion_time": "CompletionTimePrediction",
            "track_product_position": "ProductLocationReport"
        }
        return result_types.get(goal_name, "UnknownReport")
    
    def _load_action_metadata(self):
        """온톨로지에서 Action 메타데이터 로드"""
        query = """
        PREFIX exec: <http://example.org/execution-ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?action ?outputName ?endpointTemplate ?queryTemplate 
            ?dockerImage ?inputMapping ?enrichmentType
        WHERE {
            ?action rdf:type ?actionClass .
            ?actionClass rdfs:subClassOf* exec:Action .
            OPTIONAL { ?action exec:hasOutputName ?outputName }
            OPTIONAL { ?action exec:hasEndpointTemplate ?endpointTemplate }
            OPTIONAL { ?action exec:hasQueryTemplate ?queryTemplate }
            OPTIONAL { ?action exec:hasDockerImage ?dockerImage }
            OPTIONAL { ?action exec:hasInputMapping ?inputMapping }
            OPTIONAL { ?action exec:hasEnrichmentType ?enrichmentType }
        }
        """
        
        self.action_metadata = {}
        results = self.exec_graph.query(query)
        
        for row in results:
            action_name = str(row.action).split('#')[-1]
            self.action_metadata[action_name] = {
                'outputName': str(row.outputName) if row.outputName else None,
                'endpointTemplate': str(row.endpointTemplate) if row.endpointTemplate else None,
                'queryTemplate': str(row.queryTemplate) if row.queryTemplate else None,
                'dockerImage': str(row.dockerImage) if row.dockerImage else None,
                'inputMapping': str(row.inputMapping) if row.inputMapping else None,
                'enrichmentType': str(row.enrichmentType) if row.enrichmentType else None
            }

    def _process_query_template(self, template: str, parameter_mappings: Dict, dsl_input: Dict) -> str:
        """쿼리 템플릿 처리"""
        query = template
        
        # %%FILTERS%% 처리
        if "%%FILTERS%%" in query:
            filters = []
            if parameter_mappings.get("requiresCooling"):
                filters.append("?job prod:requiresCooling true")
            if parameter_mappings.get("hasStatus"):
                filters.append(f'?job prod:hasStatus "{parameter_mappings["hasStatus"]}"')
            if parameter_mappings.get("dateFilter"):
                filters.append(f'FILTER(STRSTARTS(STR(?startTime), "{parameter_mappings["dateFilter"]}"))')
            
            query = query.replace("%%FILTERS%%", " . ".join(filters))
        
        # %%PRODUCT_ID%% 처리
        if "%%PRODUCT_ID%%" in query:
            product_id = dsl_input.get("product_id", "Unknown")
            query = query.replace("%%PRODUCT_ID%%", product_id)
        
        # %%DATE_FILTER%% 처리
        if "%%DATE_FILTER%%" in query:
            date_range = dsl_input.get("date_range", {})
            if date_range:
                from_date = f"{date_range.get('from')}T00:00:00"
                to_date = f"{date_range.get('to')}T23:59:59"
                date_filter = f"""
                FILTER(?startTime >= "{from_date}"^^xsd:dateTime && 
                    ?startTime <= "{to_date}"^^xsd:dateTime)
                """
                query = query.replace("%%DATE_FILTER%%", date_filter)
            else:
                query = query.replace("%%DATE_FILTER%%", "")
        
        # %%QUANTITY%% 처리
        if "%%QUANTITY%%" in query:
            quantity = dsl_input.get("quantity", 1)
            query = query.replace("%%QUANTITY%%", str(quantity))
        
        return query.strip()

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("🚀 DSL to Execution Plan - TTL 파일 로드 버전")
    print("=" * 80)
    
    # 플래너 초기화
    try:
        planner = OntologyBasedExecutionPlanner()
    except Exception as e:
        print(f"\n❌ 온톨로지 로드 실패: {e}")
        print("\n필요한 TTL 파일 (실행 파일과 같은 디렉토리에 위치):")
        print("  - execution-ontology.ttl")
        print("  - domain-ontology.ttl")
        print("  - bridge-ontology.ttl")
        print("\n선택적 파일:")
        print("  - test_data.json")
        return
    
    # 테스트할 DSL 입력들
    test_cases = [
        {
            "goal": "query_failed_jobs_with_cooling",
            "date": "2025-07-17"
        },
        {
            "goal": "detect_anomaly_for_product",
            "product_id": "Product-A1",
            "date_range": {
                "from": "2025-07-15",
                "to": "2025-07-17"
            },
            "target_machine": "CoolingMachine-01"
        },
        {
            "goal": "predict_first_completion_time",
            "product_id": "Product-B2",
            "quantity": 100
        },
        {
            "goal": "track_product_position",
            "product_id": "Product-C1"
        }
    ]
    
    # 모든 케이스 실행
    for i, dsl_input in enumerate(test_cases):
        print(f"\n{'='*80}")
        print(f"테스트 케이스 {i+1}: {dsl_input['goal']}")
        print("="*80)
        
        execution_plan = planner.process_dsl(dsl_input)
        
        print("\n📋 최종 실행 계획:")
        print(json.dumps(execution_plan, indent=2, ensure_ascii=False))
        
        # 실행 단계별 설명
        if "executionSteps" in execution_plan:
            print("\n📊 실행 단계 상세:")
            for step in execution_plan["executionSteps"]:
                print(f"\n[Step {step['stepId']}] {step['action']}")
                print(f"  Type: {step['type']}")
                
                if 'generatedQuery' in step:
                    print(f"  Generated Query:")
                    print(f"    {step['generatedQuery'][:200]}..." if len(step['generatedQuery']) > 200 else f"    {step['generatedQuery']}")
                
                if 'expectedResultCount' in step:
                    print(f"  Expected Results: {step['expectedResultCount']} items")
                
                if 'sampleResults' in step:
                    print(f"  Sample Results:")
                    for result in step['sampleResults']:
                        print(f"    - {result}")
                
                if 'model' in step:
                    print(f"  Model: {step['model']}")
                
                if 'endpoint' in step:
                    print(f"  Endpoint: {step['endpoint']}")

if __name__ == "__main__":
    main()