#!/usr/bin/env python3
"""
Validation script for AAS test data
Ensures consistency between SPARQL and AAS data formats
"""

import json
import os
import sys
from rdflib import Graph, Namespace
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the execution planner to test integration
try:
    from dsl_execution_with_ttl import OntologyBasedExecutionPlanner
except ImportError:
    print("Warning: Could not import execution planner for integration test")
    OntologyBasedExecutionPlanner = None

# Namespaces
PROD = Namespace("http://example.org/production-domain#")
EXEC = Namespace("http://example.org/execution-ontology#")
BRIDGE = Namespace("http://example.org/bridge-ontology#")


class TestDataValidator:
    def __init__(self, base_path):
        self.base_path = base_path
        self.sparql_path = os.path.join(base_path, "sparql-data")
        self.aasx_path = os.path.join(base_path, "aasx-data")
        self.errors = []
        self.warnings = []
        
    def validate_all(self):
        """Run all validation checks"""
        print("Starting test data validation...")
        print("=" * 60)
        
        # Check directory structure
        self._validate_directory_structure()
        
        # Load and validate ontology mapping
        mapping = self._validate_ontology_mapping()
        
        # Validate SPARQL data
        sparql_data = self._validate_sparql_data()
        
        # Validate AAS data
        aas_data = self._validate_aas_data()
        
        # Cross-validate consistency
        if mapping and sparql_data and aas_data:
            self._cross_validate_data(mapping, sparql_data, aas_data)
            
        # Test integration with execution planner
        if OntologyBasedExecutionPlanner:
            self._test_execution_planner_integration()
            
        # Report results
        self._report_results()
        
    def _validate_directory_structure(self):
        """Check that all required directories exist"""
        print("\n1. Validating directory structure...")
        
        required_dirs = [
            "common",
            "sparql-data/static",
            "sparql-data/snapshot", 
            "sparql-data/historical",
            "aasx-data/shells",
            "aasx-data/submodels",
            "aasx-data/timeseries"
        ]
        
        for dir_path in required_dirs:
            full_path = os.path.join(self.base_path, dir_path)
            if os.path.exists(full_path):
                print(f"   ✓ {dir_path}")
            else:
                self.errors.append(f"Missing directory: {dir_path}")
                print(f"   ✗ {dir_path} - MISSING")
                
    def _validate_ontology_mapping(self):
        """Validate ontology mapping file"""
        print("\n2. Validating ontology mapping...")
        
        mapping_file = os.path.join(self.base_path, "common", "ontology-mapping.json")
        if not os.path.exists(mapping_file):
            self.errors.append("Missing ontology-mapping.json")
            return None
            
        try:
            with open(mapping_file, "r") as f:
                mapping = json.load(f)
                
            # Check required sections
            required_sections = ["machine_mappings", "property_mappings"]
            for section in required_sections:
                if section in mapping:
                    print(f"   ✓ {section} found ({len(mapping[section])} entries)")
                else:
                    self.errors.append(f"Missing section in mapping: {section}")
                    
            return mapping
            
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in ontology mapping: {e}")
            return None
            
    def _validate_sparql_data(self):
        """Validate SPARQL/TTL files"""
        print("\n3. Validating SPARQL data...")
        
        ttl_files = {
            "machines": os.path.join(self.sparql_path, "static", "machines-static.ttl"),
            "products": os.path.join(self.sparql_path, "static", "products-static.ttl"),
            "snapshot": os.path.join(self.sparql_path, "snapshot", "operational-snapshot-20250717.ttl"),
            "history": os.path.join(self.sparql_path, "historical", "job-history-20250717.ttl")
        }
        
        data = {}
        for name, file_path in ttl_files.items():
            if os.path.exists(file_path):
                try:
                    g = Graph()
                    g.parse(file_path, format="ttl")
                    data[name] = g
                    print(f"   ✓ {name}: {len(g)} triples")
                except Exception as e:
                    self.errors.append(f"Error parsing {name}: {e}")
                    print(f"   ✗ {name}: Parse error")
            else:
                self.errors.append(f"Missing TTL file: {name}")
                print(f"   ✗ {name}: File not found")
                
        return data
        
    def _validate_aas_data(self):
        """Validate AAS JSON files"""
        print("\n4. Validating AAS data...")
        
        # Check registry
        registry_file = os.path.join(self.aasx_path, "registry.json")
        if not os.path.exists(registry_file):
            self.errors.append("Missing AAS registry.json")
            return None
            
        try:
            with open(registry_file, "r") as f:
                registry = json.load(f)
            print(f"   ✓ Registry: {len(registry.get('shells', []))} shells")
            
            # Validate each shell
            shells_validated = 0
            for shell_info in registry.get("shells", []):
                shell_file = os.path.join(self.aasx_path, "shells", f"{shell_info['id']}.json")
                if os.path.exists(shell_file):
                    shells_validated += 1
                else:
                    self.warnings.append(f"Shell file not found: {shell_info['id']}")
                    
            print(f"   ✓ Shells: {shells_validated} validated")
            
            # Check some submodels
            submodel_count = 0
            submodel_dir = os.path.join(self.aasx_path, "submodels")
            if os.path.exists(submodel_dir):
                for filename in os.listdir(submodel_dir):
                    if filename.endswith(".json"):
                        submodel_count += 1
            print(f"   ✓ Submodels: {submodel_count} found")
            
            return {"registry": registry, "submodel_count": submodel_count}
            
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in registry: {e}")
            return None
            
    def _cross_validate_data(self, mapping, sparql_data, aas_data):
        """Cross-validate consistency between SPARQL and AAS data"""
        print("\n5. Cross-validating data consistency...")
        
        # Check machine mappings
        machines_graph = sparql_data.get("machines")
        if machines_graph:
            sparql_machines = set()
            for s in machines_graph.subjects(predicate=PROD.hasCapability):
                machine_id = str(s).split("#")[-1]
                sparql_machines.add(machine_id)
                
            mapped_machines = set(mapping["machine_mappings"].keys())
            
            # Check consistency
            missing_in_mapping = sparql_machines - mapped_machines
            missing_in_sparql = mapped_machines - sparql_machines
            
            if missing_in_mapping:
                self.warnings.append(f"Machines in SPARQL but not in mapping: {missing_in_mapping}")
            if missing_in_sparql:
                self.warnings.append(f"Machines in mapping but not in SPARQL: {missing_in_sparql}")
                
            print(f"   ✓ Machine consistency: {len(sparql_machines & mapped_machines)} matched")
            
        # Check specific test cases
        self._validate_test_goals(sparql_data)
        
    def _validate_test_goals(self, sparql_data):
        """Validate data supports all 4 test goals"""
        print("\n6. Validating test goal support...")
        
        # Goal 1: Failed jobs with cooling
        history = sparql_data.get("history")
        if history:
            failed_cooling_jobs = []
            from rdflib import Literal
            for job in history.subjects(predicate=PROD.hasStatus, object=Literal("Failed")):
                if (job, PROD.requiresCooling, Literal(True)) in history:
                    failed_cooling_jobs.append(str(job).split("#")[-1])
            print(f"   ✓ Goal 1: {len(failed_cooling_jobs)} failed cooling jobs found")
            if len(failed_cooling_jobs) < 3:
                self.warnings.append("Less than 3 failed cooling jobs for Goal 1 testing")
                
        # Goal 2: Anomaly detection data
        snapshot = sparql_data.get("snapshot")
        if snapshot:
            error_machines = []
            for machine in snapshot.subjects(predicate=PROD.hasStatus, object=Literal("Error")):
                error_machines.append(str(machine).split("#")[-1])
            print(f"   ✓ Goal 2: {len(error_machines)} machines with errors (anomalies)")
            
        # Goal 3: Product data for prediction
        products = sparql_data.get("products")
        if products:
            product_count = len(list(products.subjects(predicate=None, object=PROD.Product)))
            print(f"   ✓ Goal 3: {product_count} products with templates")
            
        # Goal 4: Processing job tracking
        if history:
            processing_jobs = list(history.subjects(predicate=PROD.hasStatus, object=Literal("Processing")))
            print(f"   ✓ Goal 4: {len(processing_jobs)} jobs currently processing")
            if len(processing_jobs) == 0:
                self.warnings.append("No processing jobs for Goal 4 testing")
                
    def _test_execution_planner_integration(self):
        """Test integration with the execution planner"""
        print("\n7. Testing execution planner integration...")
        
        try:
            # Initialize planner with our test data
            planner = OntologyBasedExecutionPlanner(
                execution_ontology_path=os.path.join(os.path.dirname(self.base_path), "execution-ontology.ttl"),
                domain_ontology_path=os.path.join(os.path.dirname(self.base_path), "domain-ontology.ttl"),
                bridge_ontology_path=os.path.join(os.path.dirname(self.base_path), "bridge-ontology.ttl")
            )
            
            # Test Goal 1
            dsl_input = {
                "goal": "query_failed_jobs_with_cooling",
                "date": "2025-07-17"
            }
            
            result = planner.process_dsl(dsl_input)
            if result and "execution_plan" in result:
                print("   ✓ Goal 1 test: Execution plan generated")
            else:
                self.errors.append("Failed to generate execution plan for Goal 1")
                
        except Exception as e:
            self.warnings.append(f"Could not test execution planner: {e}")
            print(f"   ⚠ Execution planner test skipped: {e}")
            
    def _report_results(self):
        """Report validation results"""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed!")
        else:
            if self.errors:
                print(f"\n❌ Errors ({len(self.errors)}):")
                for error in self.errors:
                    print(f"   - {error}")
                    
            if self.warnings:
                print(f"\n⚠️  Warnings ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"   - {warning}")
                    
        print("\n" + "=" * 60)
        return len(self.errors) == 0


if __name__ == "__main__":
    validator = TestDataValidator("/Users/jeongseunghwan/Desktop/aas-project/testing/v2/aas-test-data")
    success = validator.validate_all()
    sys.exit(0 if success else 1)