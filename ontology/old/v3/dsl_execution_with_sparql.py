#!/usr/bin/env python3
"""
DSL 입력부터 실행 계획 생성 및 SPARQL 쿼리 실행까지
필요 라이브러리: pip install rdflib
필요 파일: 
  - execution-ontology.ttl
  - domain-ontology.ttl  
  - bridge-ontology.ttl
  - aas-test-data/sparql-data/*.ttl
"""

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class OntologyBasedExecutionPlannerWithSPARQL:
    def __init__(self, 
                 exec_ttl: str = "execution-ontology.ttl",
                 domain_ttl: str = "domain-ontology.ttl", 
                 bridge_ttl: str = "bridge-ontology.ttl",
                 test_data_dir: str = "aas-test-data/sparql-data"):
        
        # 네임스페이스 정의
        self.EXEC = Namespace("http://example.org/execution-ontology#")
        self.PROD = Namespace("http://example.org/production-domain#")
        self.BRIDGE = Namespace("http://example.org/bridge-ontology#")
        
        # 3개의 온톨로지 그래프 초기화
        self.exec_graph = Graph()
        self.domain_graph = Graph()
        self.bridge_graph = Graph()
        
        # 테스트 데이터를 위한 통합 그래프
        self.data_graph = Graph()
        
        # 네임스페이스 바인딩
        self._bind_namespaces()
        
        # 실행 파일의 디렉토리 경로 가져오기
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # TTL 파일 경로를 실행 파일 기준으로 설정
        self.exec_ttl = os.path.join(self.base_dir, exec_ttl)
        self.domain_ttl = os.path.join(self.base_dir, domain_ttl)
        self.bridge_ttl = os.path.join(self.base_dir, bridge_ttl)
        self.test_data_dir = os.path.join(self.base_dir, test_data_dir)
        
        # 온톨로지 로드
        self._load_ontologies()
        self._load_action_metadata()
        
        # AAS 테스트 데이터 로드
        self._load_aas_test_data()
        
        # 브리지 온톨로지 내용 확인 (디버깅용)
        self._debug_bridge_ontology()
        
        # SPARQL 쿼리 결과 저장소
        self.sparql_results = {}
        
    def _bind_namespaces(self):
        """네임스페이스 바인딩"""
        for graph in [self.exec_graph, self.domain_graph, self.bridge_graph, self.data_graph]:
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
            raise
        
        # 도메인 온톨로지 로드
        try:
            self.domain_graph.parse(self.domain_ttl, format="turtle")
            print(f"✅ 도메인 온톨로지 로드 성공: {os.path.basename(self.domain_ttl)}")
            print(f"   - {len(self.domain_graph)} 트리플")
        except Exception as e:
            print(f"❌ 도메인 온톨로지 로드 실패: {e}")
            raise
        
        # 브리지 온톨로지 로드
        try:
            self.bridge_graph.parse(self.bridge_ttl, format="turtle")
            print(f"✅ 브리지 온톨로지 로드 성공: {os.path.basename(self.bridge_ttl)}")
            print(f"   - {len(self.bridge_graph)} 트리플")
        except Exception as e:
            print(f"❌ 브리지 온톨로지 로드 실패: {e}")
            raise
        
        print()
        
    def _load_aas_test_data(self):
        """AAS 테스트 데이터 TTL 파일들 로드"""
        print("📊 AAS 테스트 데이터 로드 중...")
        
        # 로드할 데이터 파일들
        data_files = [
            "static/machines-static.ttl",
            "static/products-static.ttl",
            "static/products-additional.ttl",  # 추가 제품 데이터
            "snapshot/operational-snapshot-20250717.ttl",
            "historical/job-history-20250717.ttl",
            "historical/job-history-20250718.ttl"  # 추가 날짜 데이터
        ]
        
        total_triples = 0
        for file_path in data_files:
            full_path = os.path.join(self.test_data_dir, file_path)
            try:
                before_count = len(self.data_graph)
                self.data_graph.parse(full_path, format="turtle")
                after_count = len(self.data_graph)
                added = after_count - before_count
                total_triples += added
                print(f"✅ {file_path}: {added} 트리플 추가")
            except Exception as e:
                print(f"❌ {file_path} 로드 실패: {e}")
                
        print(f"📊 총 {total_triples} 트리플 로드 완료")
        print()
        
    def _debug_bridge_ontology(self):
        """브리지 온톨로지 내용 확인"""
        print("🔍 브리지 온톨로지 디버깅...")
        
        # 모든 브리지 목표 확인
        query = """
        SELECT ?bridgeGoal ?dslGoal ?execGoal WHERE {
            ?bridgeGoal bridge:mapsGoal ?dslGoal ;
                        bridge:toExecutionGoal ?execGoal .
        }
        """
        
        results = self.bridge_graph.query(query)
        print(f"브리지 매핑 개수: {len(list(results))}")
        
        results = self.bridge_graph.query(query)  # 다시 실행 (iterator가 소모됨)
        for row in results:
            print(f"  - DSL Goal: {row.dslGoal} → Exec Goal: {str(row.execGoal).split('#')[-1]}")
        print()
        
    def _load_action_metadata(self):
        """액션 메타데이터 로드"""
        self.action_metadata = {}
        
        # 액션별 메타데이터 쿼리
        query = """
        PREFIX exec: <http://example.org/execution-ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?action ?actionType ?queryTemplate ?enrichmentType ?modelEndpoint
        WHERE {
            ?action rdf:type ?actionClass .
            FILTER(?actionClass IN (exec:QueryBuilder, exec:DataEnricher, exec:ServiceCaller, exec:DataTransform, exec:Action))
            OPTIONAL { ?action exec:actionType ?actionType }
            OPTIONAL { ?action exec:hasQueryTemplate ?queryTemplate }
            OPTIONAL { ?action exec:hasEnrichmentType ?enrichmentType }
            OPTIONAL { ?action exec:usesModel/exec:hasEndpoint ?modelEndpoint }
        }
        """
        
        results = self.exec_graph.query(query)
        print(f"\n📋 액션 메타데이터 로드: {len(list(results))}개 액션")
        
        results = self.exec_graph.query(query)  # 다시 실행
        for row in results:
            action_uri = str(row.action)
            action_name = action_uri.split('#')[-1]
            
            # actionType 결정
            action_type = None
            if row.actionType:
                action_type = str(row.actionType).split('#')[-1]
            elif row.queryTemplate:
                action_type = "QueryAction"
            elif row.enrichmentType:
                action_type = "EnrichmentAction"
            elif row.modelEndpoint:
                action_type = "ServiceAction"
            
            self.action_metadata[action_uri] = {
                'actionType': action_type,
                'queryTemplate': str(row.queryTemplate) if row.queryTemplate else None,
                'enrichmentType': str(row.enrichmentType) if row.enrichmentType else None,
                'modelEndpoint': str(row.modelEndpoint) if row.modelEndpoint else None
            }
            
            if row.queryTemplate:
                print(f"  - {action_name}: QueryAction (has SPARQL template)")
            
    def _execute_sparql_query(self, query_template: str, parameters: Dict[str, Any]) -> List[Dict]:
        """SPARQL 쿼리 실행 및 결과 반환"""
        # 쿼리 템플릿에서 파라미터 치환
        query = self._process_query_template(query_template, parameters)
        
        print("\n🔍 SPARQL 쿼리 실행:")
        print("-" * 60)
        print(query)
        print("-" * 60)
        
        # 쿼리 실행
        try:
            results = self.data_graph.query(query)
            
            # 결과를 딕셔너리 리스트로 변환
            result_list = []
            for row in results:
                result_dict = {}
                for var in results.vars:
                    try:
                        # 변수명은 Variable 객체이므로 문자열로 변환
                        var_name = str(var)
                        value = row[var]  # getattr 대신 딕셔너리 스타일 접근
                        
                        if value is not None:
                            # URI인 경우 마지막 부분만 추출
                            if isinstance(value, URIRef):
                                result_dict[var_name] = str(value).split("#")[-1]
                            else:
                                result_dict[var_name] = str(value)
                        else:
                            result_dict[var_name] = None
                    except Exception as e:
                        print(f"   변수 {var} 접근 오류: {e}")
                        result_dict[str(var)] = None
                result_list.append(result_dict)
                
            print(f"\n✅ 쿼리 결과: {len(result_list)}개 레코드")
            print(f"   변수명: {list(results.vars)}")
            
            # 결과 출력
            if result_list:
                print("\n결과 상세:")
                for i, result in enumerate(result_list, 1):
                    print(f"{i}. ", end="")
                    values = [f"{k}: {v}" for k, v in result.items() if v is not None]
                    if values:
                        print(" | ".join(values))
                    else:
                        print("(모든 필드가 null)")
            else:
                print("\n❌ 쿼리 결과가 없습니다.")
                    
            return result_list
            
        except Exception as e:
            print(f"❌ 쿼리 실행 오류: {e}")
            print(f"   에러 타입: {type(e).__name__}")
            return []
    
    def _process_query_template(self, template: str, parameters: Dict[str, Any]) -> str:
        """쿼리 템플릿 처리 - 파라미터 치환"""
        query = template
        
        # %%FILTERS%% 처리
        if "%%FILTERS%%" in query:
            filters = []
            
            # Goal 1: Failed jobs with cooling
            if parameters.get("goal") == "query_failed_jobs_with_cooling":
                filters.append('?job prod:requiresCooling true .')
                filters.append('FILTER(?status = "Failed")')
                
                # 날짜 필터 처리
                if "date" in parameters:
                    date = parameters["date"]
                    filters.append(f'FILTER(STRSTARTS(STR(?startTime), "{date}"))')
            else:
                # 날짜 필터 처리
                if "date" in parameters:
                    date = parameters["date"]
                    filters.append(f'FILTER(STRSTARTS(STR(?startTime), "{date}"))')
                    
                # 제품 필터 처리
                if "product_id" in parameters:
                    product_id = parameters["product_id"]
                    filters.append(f'FILTER(?product = prod:{product_id})')
                    
                # 머신 필터 처리
                if "target_machine" in parameters:
                    machine = parameters["target_machine"]
                    filters.append(f'FILTER(?machine = prod:{machine})')
                
            filter_string = "\n            ".join(filters) if filters else ""
            query = query.replace("%%FILTERS%%", filter_string)
            
        # %%DATE_FILTER%% 처리
        if "%%DATE_FILTER%%" in query:
            date_filters = []
            if "date_range" in parameters:
                date_range = parameters["date_range"]
                if "start" in date_range:
                    date_filters.append(f'FILTER(?startTime >= "{date_range["start"]}"^^xsd:dateTime)')
                if "end" in date_range:
                    date_filters.append(f'FILTER(?startTime <= "{date_range["end"]}"^^xsd:dateTime)')
            
            date_filter_string = "\n            ".join(date_filters) if date_filters else ""
            query = query.replace("%%DATE_FILTER%%", date_filter_string)
            
        # 기타 파라미터 치환
        for key, value in parameters.items():
            placeholder = f"%%{key.upper()}%%"
            if placeholder in query:
                query = query.replace(placeholder, str(value))
                
        return query
    
    def process_dsl(self, dsl_input: Dict[str, Any]) -> Dict[str, Any]:
        """DSL 입력을 처리하여 실행 계획 생성"""
        print("\n" + "="*60)
        print("🚀 DSL 처리 시작")
        print("="*60)
        
        print(f"\n📥 DSL 입력: {json.dumps(dsl_input, indent=2)}")
        
        # DSL goal을 실행 온톨로지의 Goal로 매핑
        dsl_goal = dsl_input.get("goal")
        execution_goal = self._find_execution_goal(dsl_goal)
        
        if not execution_goal:
            return {"error": f"Unknown goal: {dsl_goal}"}
        
        print(f"\n🎯 실행 목표: {execution_goal}")
        
        # Goal에 필요한 Action들 찾기
        required_actions = self._find_required_actions(execution_goal)
        print(f"\n📋 필요한 액션들: {[a.split('#')[-1] for a in required_actions]}")
        
        # 실행 계획 생성
        execution_plan = self._generate_execution_plan(
            execution_goal, 
            required_actions, 
            dsl_input
        )
        
        # SPARQL 쿼리 실행 (QueryAction이 있는 경우)
        for step in execution_plan["steps"]:
            action_uri = f"{self.EXEC}{step['action']}"
            metadata = self.action_metadata.get(action_uri, {})
            
            # has_query 플래그가 있거나 queryTemplate이 있는 경우
            if step.get("has_query") or metadata.get('queryTemplate'):
                
                if metadata.get('queryTemplate'):
                    # 쿼리 실행
                    results = self._execute_sparql_query(
                        metadata['queryTemplate'],
                        dsl_input
                    )
                    
                    # 결과 저장
                    self.sparql_results[step['action']] = {
                        'query': self._process_query_template(metadata['queryTemplate'], dsl_input),
                        'results': results,
                        'count': len(results)
                    }
                    
                    # 실행 계획에 결과 추가
                    step['sparql_results'] = self.sparql_results[step['action']]
        
        # 전체 SPARQL 결과를 실행 계획에 추가
        execution_plan['sparql_results'] = self.sparql_results
        
        print("\n" + "="*60)
        print("✅ 실행 계획 생성 완료")
        print("="*60)
        
        # 실행 계획 출력
        print(f"\n📄 실행 계획:\n{json.dumps(execution_plan, indent=2, ensure_ascii=False)}")
        
        return execution_plan
    
    def _find_execution_goal(self, dsl_goal: str) -> Optional[str]:
        """DSL goal을 실행 온톨로지의 Goal로 매핑"""
        # 브리지 온톨로지에서 매핑 찾기
        query = f"""
        SELECT ?execGoal WHERE {{
            ?bridgeGoal bridge:mapsGoal "{dsl_goal}" ;
                        bridge:toExecutionGoal ?execGoal .
        }}
        """
        
        print(f"\n🔍 브리지 쿼리 실행:")
        print(query)
        
        results = list(self.bridge_graph.query(query))
        print(f"결과: {len(results)}개")
        
        if results:
            exec_goal = str(results[0].execGoal)
            print(f"매핑된 실행 목표: {exec_goal}")
            return exec_goal
        
        print(f"❌ {dsl_goal}에 대한 매핑을 찾을 수 없습니다.")
        return None
    
    def _find_required_actions(self, goal_uri: str) -> List[str]:
        """Goal에 필요한 Action들 찾기"""
        query = f"""
        SELECT ?action WHERE {{
            <{goal_uri}> exec:requiresAction ?action .
        }}
        ORDER BY ?action
        """
        
        results = self.exec_graph.query(query)
        return [str(row.action) for row in results]
    
    def _generate_execution_plan(self, goal: str, actions: List[str], 
                                parameters: Dict[str, Any]) -> Dict[str, Any]:
        """실행 계획 생성"""
        steps = []
        
        for i, action_uri in enumerate(actions):
            action_name = action_uri.split('#')[-1]
            metadata = self.action_metadata.get(action_uri, {})
            
            step = {
                "step": i + 1,
                "action": action_name,
                "action_type": metadata.get('actionType', 'Unknown'),
                "parameters": parameters
            }
            
            # 액션 타입별 추가 정보
            if metadata.get('queryTemplate'):
                step["has_query"] = True
                
            if metadata.get('enrichmentType'):
                step["enrichment_type"] = metadata['enrichmentType']
                
            if metadata.get('modelEndpoint'):
                step["model_endpoint"] = metadata['modelEndpoint']
                
            steps.append(step)
        
        return {
            "goal": goal.split('#')[-1],
            "timestamp": datetime.now().isoformat(),
            "steps": steps,
            "total_steps": len(steps)
        }


def main():
    """메인 함수 - 4가지 목표 테스트"""
    # 플래너 초기화
    planner = OntologyBasedExecutionPlannerWithSPARQL()
    
    # 테스트할 DSL 입력들
    test_cases = [
        {
            "name": "Goal 1: 냉각이 필요한 실패한 작업 조회",
            "input": {
                "goal": "query_failed_jobs_with_cooling",
                "date": "2025-07-17"
            }
        },
        {
            "name": "Goal 2: 제품 이상 감지",
            "input": {
                "goal": "detect_anomaly_for_product",
                "product_id": "Product-A1",
                "date_range": {
                    "start": "2025-07-17T00:00:00",
                    "end": "2025-07-17T23:59:59"
                },
                "target_machine": "CoolingMachine-01"
            }
        },
        {
            "name": "Goal 3: 첫 완료 시간 예측",
            "input": {
                "goal": "predict_first_completion_time",
                "product_id": "Product-B2",
                "quantity": 100
            }
        },
        {
            "name": "Goal 4: 제품 위치 추적",
            "input": {
                "goal": "track_product_position",
                "product_id": "Product-C1"
            }
        }
    ]
    
    # 각 테스트 케이스 실행
    results = {}
    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"🧪 테스트: {test['name']}")
        print(f"{'='*80}")
        
        result = planner.process_dsl(test["input"])
        results[test["input"]["goal"]] = result
        
        # 결과 저장
        output_file = f"test_result_{test['input']['goal']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 결과 저장: {output_file}")
        
    # 전체 결과 요약
    print(f"\n{'='*80}")
    print("📊 전체 테스트 결과 요약")
    print(f"{'='*80}")
    
    for goal, result in results.items():
        print(f"\n{goal}:")
        if 'sparql_results' in result:
            for action, query_result in result['sparql_results'].items():
                print(f"  - {action}: {query_result['count']}개 결과")
        else:
            print(f"  - 실행 단계: {result.get('total_steps', 0)}개")


if __name__ == "__main__":
    main()