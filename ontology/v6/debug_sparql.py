#!/usr/bin/env python3
"""
Debug SPARQL action execution
"""

import sys
sys.path.append('./src')

from execution_planner import ExecutionPlanner

def debug_sparql():
    planner = ExecutionPlanner()
    
    # Test SPARQL action directly
    action = {
        "uri": "http://example.org/execution#G1_QueryCoolingProducts",
        "type": "SPARQL",
        "query": None
    }
    
    print("Testing SPARQL action:")
    result = planner._execute_sparql_action(action)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")

if __name__ == "__main__":
    debug_sparql()