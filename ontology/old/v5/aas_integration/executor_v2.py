"""
AAS Executor v2
Executes DSL queries using ontology-based planning and AAS API calls
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.plugins.sparql import prepareQuery
from datetime import datetime

from .client_v2 import AASClientV2
from .fallback import FallbackHandler
from .utils import (
    validate_dsl_input, format_error_response, format_success_response,
    merge_results, filter_by_date, calculate_duration
)


class AASExecutorV2:
    """Execute DSL queries with ontology planning and AAS integration"""
    
    def __init__(self, base_url: str = "http://localhost:5001", 
                 fallback_strategy: str = "sequential"):
        """
        Initialize executor
        
        Args:
            base_url: AAS server base URL
            fallback_strategy: Fallback strategy to use
        """
        self.client = AASClientV2(base_url)
        self.fallback_handler = FallbackHandler(
            strategy=fallback_strategy,
            config={
                "data_path": str(Path(__file__).parent.parent / "aas-test-data")
            }
        )
        
        # Initialize ontology
        self.graph = Graph()
        self._load_ontologies()
        
        # Define namespaces
        self.EX = Namespace("http://example.com/execution#")
        self.DSL = Namespace("http://example.com/dsl#")
        
    def _load_ontologies(self):
        """Load ontology files"""
        ontology_files = [
            Path(__file__).parent.parent / "bridge-ontology.ttl",
            Path(__file__).parent.parent / "domain-ontology.ttl",
            Path(__file__).parent.parent / "ontology_extensions" / "execution-ext.ttl",
            Path(__file__).parent.parent / "ontology_extensions" / "bridge-ext.ttl"
        ]
        
        for onto_file in ontology_files:
            if onto_file.exists():
                try:
                    self.graph.parse(str(onto_file), format="turtle")
                    print(f"✅ Loaded ontology: {onto_file.name}")
                except Exception as e:
                    print(f"⚠️ Failed to load {onto_file.name}: {e}")
    
    def execute(self, dsl_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute DSL query
        
        Args:
            dsl_input: DSL input with goal and parameters
            
        Returns:
            Execution result
        """
        # Validate input
        is_valid, error_msg = validate_dsl_input(dsl_input)
        if not is_valid:
            return format_error_response("VALIDATION_ERROR", error_msg)
        
        goal = dsl_input["goal"]
        parameters = dsl_input["parameters"]
        
        print(f"\n🎯 Executing goal: {goal}")
        print(f"📋 Parameters: {parameters}")
        
        # Execute based on goal
        try:
            if goal == "query_failed_jobs_with_cooling":
                return self._execute_goal1(parameters)
            elif goal == "track_product_position":
                return self._execute_goal4(parameters)
            elif goal == "detect_product_anomalies":
                return self._execute_goal2(parameters)
            elif goal == "predict_job_completion_time":
                return self._execute_goal3(parameters)
            else:
                return format_error_response("UNKNOWN_GOAL", f"Goal not implemented: {goal}")
        except Exception as e:
            print(f"❌ Execution error: {e}")
            return format_error_response("EXECUTION_ERROR", str(e))
    
    def _execute_goal1(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Goal 1: Query failed jobs with cooling requirements
        """
        date = parameters["date"]
        print(f"\n🔍 Goal 1: Finding failed jobs requiring cooling on {date}")
        
        results = []
        
        # Step 1: Get products requiring cooling
        print("\n📦 Step 1: Getting products that require cooling...")
        cooling_products = []
        
        try:
            # Try AAS API first
            api_products = self.client.get_products_requiring_cooling()
            cooling_products = [p['id'] for p in api_products]
            print(f"✅ Found {len(cooling_products)} products requiring cooling via API")
        except Exception as e:
            print(f"⚠️ API call failed: {e}")
            # Fallback will be handled in step 3
        
        # Step 2: Get machines requiring cooling
        print("\n🏭 Step 2: Getting machines that require cooling...")
        cooling_machines = []
        
        try:
            api_machines = self.client.get_machines_requiring_cooling()
            cooling_machines = [m['id'] for m in api_machines]
            print(f"✅ Found {len(cooling_machines)} machines requiring cooling via API")
        except Exception as e:
            print(f"⚠️ API call failed: {e}")
        
        # Step 3: Get failed jobs for the date
        print(f"\n📅 Step 3: Getting failed jobs for {date}...")
        failed_jobs = []
        
        try:
            # Get all machines first
            shells = self.client.get_all_shells()
            machine_shells = [s for s in shells if s['id'].startswith('urn:aas:Machine:')]
            
            for shell in machine_shells:
                machine_id = shell['idShort']
                jobs = self.client.get_job_history(machine_id, date)
                failed = [j for j in jobs if j.get('status') == 'FAILED']
                failed_jobs.extend(failed)
            
            print(f"✅ Found {len(failed_jobs)} failed jobs via API")
        except Exception as e:
            print(f"⚠️ API call failed: {e}")
            # Try fallback
            print("🔄 Attempting fallback to TTL data...")
            fallback_jobs = self.fallback_handler.query_failed_jobs_with_cooling(date)
            failed_jobs = fallback_jobs
            print(f"✅ Found {len(failed_jobs)} failed jobs via fallback")
        
        # Step 4: Filter jobs that require cooling
        print("\n🔍 Step 4: Filtering jobs that require cooling...")
        
        for job in failed_jobs:
            product_id = job.get('product_id')
            machine_id = job.get('machine_id')
            
            # Check if product requires cooling
            requires_cooling = False
            
            if product_id in cooling_products:
                requires_cooling = True
            else:
                # Check via fallback if not in API results
                product_info = self.fallback_handler.get_product_info(product_id)
                if product_info and product_info.get('requires_cooling'):
                    requires_cooling = True
            
            if requires_cooling:
                # Enhance job data
                job['requires_cooling'] = True
                job['cooling_equipment'] = machine_id in cooling_machines
                
                # Calculate duration
                if 'start_time' in job and 'end_time' in job:
                    job['duration_minutes'] = calculate_duration(
                        job['start_time'], job['end_time']
                    )
                
                results.append(job)
        
        print(f"\n✅ Found {len(results)} failed jobs requiring cooling")
        
        # Return formatted response
        metadata = {
            "query_date": date,
            "total_failed_jobs": len(failed_jobs),
            "cooling_required_jobs": len(results),
            "products_requiring_cooling": len(cooling_products),
            "machines_with_cooling": len(cooling_machines)
        }
        
        return format_success_response(
            results,
            f"Found {len(results)} failed jobs requiring cooling on {date}",
            metadata
        )
    
    def _execute_goal4(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Goal 4: Track product position
        """
        product_id = parameters["product_id"]
        print(f"\n📍 Goal 4: Tracking position of product {product_id}")
        
        result = None
        
        # Try AAS API first
        try:
            response = self.client.session.get(
                f"{self.client.base_url}/api/product/{product_id}/location"
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Found product location via API")
        except Exception as e:
            print(f"⚠️ API call failed: {e}")
        
        # Try fallback if API failed
        if not result:
            print("🔄 Attempting fallback to TTL data...")
            result = self.fallback_handler.track_product_position(product_id)
            if result:
                print(f"✅ Found product location via fallback")
        
        if not result:
            return format_error_response(
                "PRODUCT_NOT_FOUND",
                f"Product {product_id} not found in system"
            )
        
        # Enhance result with additional information
        if result.get('location_type') == 'machine':
            # Get machine info
            machine_id = result.get('current_location')
            if machine_id:
                try:
                    machine_shell = self.client.get_shell(f"urn:aas:Machine:{machine_id}")
                    if machine_shell:
                        result['location_details'] = {
                            'type': 'machine',
                            'id': machine_id,
                            'name': machine_shell.get('idShort', machine_id)
                        }
                except:
                    pass
        
        # Add timestamp
        result['query_timestamp'] = datetime.now().isoformat()
        
        return format_success_response(
            result,
            f"Successfully tracked product {product_id}"
        )
    
    def _execute_goal2(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Goal 2: Detect product anomalies (placeholder)
        """
        timeframe = parameters.get("timeframe", "24h")
        
        # Placeholder implementation
        result = {
            "message": "Goal 2 (detect_product_anomalies) not yet implemented",
            "timeframe": timeframe,
            "anomalies": []
        }
        
        return format_success_response(
            result,
            "Anomaly detection not yet implemented"
        )
    
    def _execute_goal3(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Goal 3: Predict job completion time (placeholder)
        """
        job_id = parameters.get("job_id")
        
        # Placeholder implementation
        result = {
            "message": "Goal 3 (predict_job_completion_time) not yet implemented",
            "job_id": job_id,
            "predicted_completion": None
        }
        
        return format_success_response(
            result,
            "Job completion prediction not yet implemented"
        )
    
    def query_ontology(self, goal: str) -> Optional[Dict[str, Any]]:
        """
        Query ontology for execution plan
        
        Args:
            goal: Goal identifier
            
        Returns:
            Execution plan or None
        """
        # Query for goal information
        query = f"""
        PREFIX ex: <http://example.com/execution#>
        PREFIX dsl: <http://example.com/dsl#>
        
        SELECT ?endpoint ?method ?params
        WHERE {{
            ex:{goal} a ex:Goal ;
                      ex:hasEndpoint ?endpoint ;
                      ex:hasMethod ?method ;
                      ex:hasParameters ?params .
        }}
        """
        
        results = list(self.graph.query(query))
        if results:
            row = results[0]
            return {
                "endpoint": str(row.endpoint),
                "method": str(row.method),
                "parameters": str(row.params)
            }
        
        return None


def main():
    """Test executor with sample queries"""
    executor = AASExecutorV2()
    
    # Test Goal 1
    print("=" * 80)
    print("Testing Goal 1: Query Failed Jobs with Cooling")
    print("=" * 80)
    
    result1 = executor.execute({
        "goal": "query_failed_jobs_with_cooling",
        "parameters": {
            "date": "2025-07-17"
        }
    })
    
    print("\nResult:")
    print(json.dumps(result1, indent=2))
    
    # Test Goal 4
    print("\n" + "=" * 80)
    print("Testing Goal 4: Track Product Position")
    print("=" * 80)
    
    result4 = executor.execute({
        "goal": "track_product_position",
        "parameters": {
            "product_id": "Product-C1"
        }
    })
    
    print("\nResult:")
    print(json.dumps(result4, indent=2))


if __name__ == "__main__":
    main()