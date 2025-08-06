"""
Ontology Manager for v6 AAS Integration
온톨로지 로드 및 SPARQL 쿼리 실행
"""

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD
import os
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OntologyManager:
    """온톨로지 관리 및 쿼리 실행"""
    
    def __init__(self, ontology_dir: str = "./ontology"):
        self.ontology_dir = ontology_dir
        self.graph = Graph()
        
        # 네임스페이스 정의
        self.EXEC = Namespace("http://example.org/execution#")
        self.PROD = Namespace("http://example.org/production#")
        self.BRIDGE = Namespace("http://example.org/bridge#")
        self.DS = Namespace("http://example.org/data-source#")
        
        # 네임스페이스 바인딩
        self.graph.bind("exec", self.EXEC)
        self.graph.bind("prod", self.PROD)
        self.graph.bind("bridge", self.BRIDGE)
        self.graph.bind("ds", self.DS)
        
        # 온톨로지 로드
        self.load_ontologies()
        
    def load_ontologies(self):
        """모든 온톨로지 파일 로드"""
        ontology_files = [
            "execution-ontology.ttl",
            "domain-ontology.ttl",
            "bridge-ontology.ttl"
        ]
        
        for filename in ontology_files:
            filepath = os.path.join(self.ontology_dir, filename)
            if os.path.exists(filepath):
                try:
                    self.graph.parse(filepath, format="turtle")
                    logger.info(f"✅ Loaded: {filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to load {filename}: {e}")
            else:
                logger.warning(f"⚠️ File not found: {filepath}")
                
        logger.info(f"📊 Total triples loaded: {len(self.graph)}")
        
    def get_goal_actions(self, goal_name: str) -> List[Dict[str, Any]]:
        """특정 Goal의 Action들을 순서대로 조회"""
        query = """
        PREFIX exec: <http://example.org/execution#>
        PREFIX bridge: <http://example.org/bridge#>
        
        SELECT ?action ?label ?type ?order ?dataSource ?endpoint ?query ?snapshotTime ?dataPath ?outputVariable
        WHERE {
            ?dslGoal bridge:dslName ?goalName ;
                    bridge:mapsToExecutionGoal ?execGoal .
            
            ?execGoal exec:hasAction ?action .
            
            ?action rdfs:label ?label ;
                   exec:actionType ?type ;
                   exec:executionOrder ?order .
                   
            OPTIONAL { ?action exec:dataSource ?dataSource }
            OPTIONAL { ?action exec:endpoint ?endpoint }
            OPTIONAL { ?action exec:query ?query }
            OPTIONAL { ?action exec:snapshotTime ?snapshotTime }
            OPTIONAL { ?action exec:dataPath ?dataPath }
            OPTIONAL { ?action exec:outputVariable ?outputVariable }
            
            FILTER(?goalName = "%s")
        }
        ORDER BY ?order
        """ % goal_name
        
        results = []
        for row in self.graph.query(query):
            action = {
                "uri": str(row.action),
                "label": str(row.label),
                "type": str(row.type),
                "order": int(row.order),
                "dataSource": str(row.dataSource) if row.dataSource else None,
                "endpoint": str(row.endpoint) if row.endpoint else None,
                "query": str(row.query) if row.query else None,
                "snapshotTime": str(row.snapshotTime) if row.snapshotTime else None,
                "dataPath": str(row.dataPath) if row.dataPath else None,
                "outputVariable": str(row.outputVariable) if row.outputVariable else None
            }
            results.append(action)
            
        return results
    
    def get_parameter_mappings(self, goal_name: str) -> Dict[str, Dict[str, Any]]:
        """Goal의 파라미터 매핑 정보 조회"""
        query = """
        PREFIX bridge: <http://example.org/bridge#>
        
        SELECT ?dslParam ?execParam ?type ?required ?default
        WHERE {
            ?dslGoal bridge:dslName ?goalName ;
                    bridge:hasParameterMapping ?mapping .
            
            ?mapping bridge:dslParameterName ?dslParam ;
                    bridge:executionParameterName ?execParam ;
                    bridge:parameterType ?type ;
                    bridge:isRequired ?required .
                    
            OPTIONAL { ?mapping bridge:defaultValue ?default }
            
            FILTER(?goalName = "%s")
        }
        """ % goal_name
        
        mappings = {}
        for row in self.graph.query(query):
            mappings[str(row.dslParam)] = {
                "execution_name": str(row.execParam),
                "type": str(row.type),
                "required": bool(row.required),
                "default": str(row.default) if row.default else None
            }
            
        return mappings
    
    def query_cooling_products(self) -> List[str]:
        """냉각이 필요한 제품 조회"""
        query = """
        PREFIX prod: <http://example.org/production#>
        
        SELECT ?productId ?productName
        WHERE {
            ?product a prod:Product ;
                    prod:productId ?productId ;
                    prod:productName ?productName ;
                    prod:requiresCooling true .
        }
        """
        
        products = []
        for row in self.graph.query(query):
            products.append(str(row.productId))
            
        return products
    
    def query_normal_patterns(self, product_id: str) -> Dict[str, Any]:
        """제품의 정상 패턴 조회"""
        query = """
        PREFIX prod: <http://example.org/production#>
        
        SELECT ?metric ?min ?max ?mean
        WHERE {
            ?product prod:productId "%s" ;
                    prod:hasNormalPattern ?pattern .
            ?pattern prod:metric ?metric ;
                    prod:minValue ?min ;
                    prod:maxValue ?max ;
                    prod:meanValue ?mean .
        }
        """ % product_id
        
        patterns = {}
        for row in self.graph.query(query):
            patterns[str(row.metric)] = {
                "min": float(row.min),
                "max": float(row.max),
                "mean": float(row.mean)
            }
            
        return patterns
    
    def get_data_source_config(self, source_type: str) -> Dict[str, Any]:
        """데이터 소스 설정 조회"""
        query = """
        PREFIX ds: <http://example.org/data-source#>
        
        SELECT ?source ?endpoint ?fallback
        WHERE {
            ?source a ds:%s ;
                   ds:hasEndpoint ?endpoint .
            OPTIONAL { ?source ds:hasFallback ?fallback }
        }
        LIMIT 1
        """ % source_type
        
        for row in self.graph.query(query):
            return {
                "endpoint": str(row.endpoint),
                "fallback": str(row.fallback) if row.fallback else None
            }
            
        return None
    
    def execute_sparql(self, query: str) -> List[Dict[str, Any]]:
        """일반 SPARQL 쿼리 실행"""
        results = []
        try:
            for row in self.graph.query(query):
                result = {}
                for var in row.labels:
                    result[var] = str(row[var]) if row[var] else None
                results.append(result)
        except Exception as e:
            logger.error(f"SPARQL query failed: {e}")
            
        return results


if __name__ == "__main__":
    # 테스트
    manager = OntologyManager()
    
    # Goal 1의 액션들 조회
    print("\n📋 Goal 1 Actions:")
    actions = manager.get_goal_actions("query_failed_jobs_with_cooling")
    for action in actions:
        print(f"  {action['order']}. {action['label']} ({action['type']})")
    
    # 파라미터 매핑 조회
    print("\n🔗 Parameter Mappings:")
    mappings = manager.get_parameter_mappings("query_failed_jobs_with_cooling")
    for param, config in mappings.items():
        print(f"  {param} → {config['execution_name']} ({config['type']})")
    
    # 냉각 제품 조회
    print("\n❄️ Products requiring cooling:")
    products = manager.query_cooling_products()
    print(f"  {products}")