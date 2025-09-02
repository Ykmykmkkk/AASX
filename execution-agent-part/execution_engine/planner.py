# execution_engine/planner.py
import sys
from pathlib import Path
from rdflib import Graph, Namespace

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import ONTOLOGY_FILE_PATH

# 네임스페이스는 온톨로지 파일 내부와 일치해야 합니다.
FACTORY = Namespace("http://example.org/factory#")

class ExecutionPlanner:
    def __init__(self):
        self.g = Graph()
        self.g.parse(str(ONTOLOGY_FILE_PATH), format="turtle")
        self.g.bind("factory", FACTORY)
        print("✅ Ontology file (v2_final) loaded successfully.")

    def create_plan(self, goal: str) -> list:
        """
        주어진 Goal에 대한 Action Plan을 동적으로 생성합니다. (일반화된 버전)
        """
        query = f"""
            PREFIX factory: <{str(FACTORY)}>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            
            SELECT ?action ?execType ?targetSubmodelId
            WHERE {{
                factory:{goal} factory:hasActionSequence ?list .
                ?list rdf:rest*/rdf:first ?action .
                OPTIONAL {{ ?action factory:hasExecutionType ?execType . }}
                OPTIONAL {{ ?action factory:targetsSubmodelId ?targetSubmodelId . }}
            }}
            ORDER BY ?list
        """
        results = self.g.query(query)
        action_plan = []
        for row in results:
            step = {
                "action_id": str(row.action).split('#')[-1],
                "type": str(row.execType),
                "target_submodel_id": str(row.targetSubmodelId) if row.targetSubmodelId else None
            }
            action_plan.append(step)
        
        return action_plan