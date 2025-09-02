# api/main.py
from fastapi import FastAPI, HTTPException
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.schemas import DslRequest, ApiResponse
from execution_engine.planner import ExecutionPlanner
from execution_engine.agent import ExecutionAgent
import requests

app = FastAPI(
    title="Smart Factory Automation Prototype",
    description="DSL을 입력받아 온톨로지와 AAS를 이용해 작업을 수행하는 API",
    version="2.0.0",
)

try:
    planner = ExecutionPlanner()
    agent = ExecutionAgent()
    print("✅ Planner and Agent are ready.")
except Exception as e:
    print(f"❌ CRITICAL: Failed to initialize. Error: {e}")
    planner = None
    agent = None

@app.post("/execute-goal", response_model=ApiResponse)
def execute_goal(request: DslRequest):
    if not planner or not agent:
         raise HTTPException(status_code=503, detail="Server is not ready. Check initialization logs.")
         
    try:
        action_plan = planner.create_plan(request.goal)
        
        if not action_plan:
            raise HTTPException(status_code=404, detail=f"Goal '{request.goal}' could not be resolved into an action plan.")

        result_data = agent.run(action_plan, request.dict())

        return ApiResponse(
            goal=request.goal,
            params=request.dict(),
            result=result_data.get("final_result", "Process completed, but no final result was marked.")
        )
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to communicate with AAS Server. Error: {e}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")