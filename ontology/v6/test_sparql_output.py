#!/usr/bin/env python3
"""
Test SPARQL action output variable
"""

import sys
sys.path.append('./src')

from ontology_manager import OntologyManager

def test_sparql_output():
    manager = OntologyManager()
    
    # Get Goal 1 actions
    actions = manager.get_goal_actions("query_failed_jobs_with_cooling")
    
    print("Goal 1 Actions:")
    for action in actions:
        print(f"\n{action['order']}. {action['label']}")
        print(f"   Type: {action['type']}")
        print(f"   URI: {action['uri']}")
        print(f"   Output Variable: {action.get('outputVariable', 'NONE')}")
        
        if action['type'] == 'SPARQL':
            print(f"   Query: {action.get('query', 'NONE')[:50]}...")

if __name__ == "__main__":
    test_sparql_output()