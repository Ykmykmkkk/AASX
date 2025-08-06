"""
Fallback Handler for AAS Integration
Implements 3-tier fallback strategy: AAS Server → Mock Server → TTL Data
"""

import os
import json
from typing import Dict, Any, Optional, List
from rdflib import Graph, Namespace, RDF
from rdflib.plugins.sparql import prepareQuery
from pathlib import Path


class FallbackHandler:
    """Handle fallback strategies when primary data sources are unavailable"""
    
    def __init__(self, strategy: str = "sequential", config: Optional[Dict[str, Any]] = None):
        """
        Initialize fallback handler
        
        Args:
            strategy: Fallback strategy ("sequential", "parallel", "cache_first")
            config: Configuration dictionary with data paths
        """
        self.strategy = strategy
        self.config = config or {}
        
        # Get data path from config
        self.data_path = Path(self.config.get("data_path", "aas-test-data"))
        
        # Initialize RDF graph for TTL fallback
        self.graph = None
        self._init_rdf_graph()
        
        # Define namespaces
        self.AAS = Namespace("https://example.com/aas/")
        self.MACHINE = Namespace("https://example.com/machine/")
        self.PRODUCT = Namespace("https://example.com/product/")
        self.JOB = Namespace("https://example.com/job/")
        
    def _init_rdf_graph(self):
        """Initialize RDF graph with TTL data"""
        self.graph = Graph()
        
        # Load TTL files if they exist
        ttl_files = [
            "static/machines.ttl",
            "static/products.ttl",
            "snapshot/machine-states-20250717.ttl",
            "historical/job-history-20250717.ttl",
            "products-additional.ttl",
            "job-history-20250718.ttl"
        ]
        
        for ttl_file in ttl_files:
            file_path = self.data_path / ttl_file
            if file_path.exists():
                try:
                    self.graph.parse(str(file_path), format="turtle")
                    print(f"✅ Loaded TTL data from: {ttl_file}")
                except Exception as e:
                    print(f"⚠️ Failed to load {ttl_file}: {e}")
        
        if len(self.graph) > 0:
            print(f"📊 Total triples loaded: {len(self.graph)}")
    
    def query_failed_jobs_with_cooling(self, date: str) -> List[Dict[str, Any]]:
        """
        Fallback query for failed jobs with cooling requirements
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of failed jobs that require cooling
        """
        print(f"🔄 Fallback: Querying failed jobs from TTL data for date: {date}")
        
        if not self.graph or len(self.graph) == 0:
            print("⚠️ No TTL data available for fallback")
            return []
        
        # SPARQL query for failed jobs
        query = """
        PREFIX aas: <https://example.com/aas/>
        PREFIX machine: <https://example.com/machine/>
        PREFIX product: <https://example.com/product/>
        PREFIX job: <https://example.com/job/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT ?job ?machine ?product ?startTime ?endTime ?status ?errorCode
        WHERE {
            ?job a job:ProductionJob ;
                 job:machine ?machine ;
                 job:product ?product ;
                 job:startTime ?startTime ;
                 job:endTime ?endTime ;
                 job:status ?status .
            
            OPTIONAL { ?job job:errorCode ?errorCode }
            
            # Filter for failed status
            FILTER(?status = "FAILED")
            
            # Filter by date
            FILTER(STRSTARTS(STR(?startTime), "%s"))
            
            # Check if product requires cooling
            ?product product:requiresCoolingDuringProduction ?cooling .
            FILTER(?cooling = true)
        }
        ORDER BY ?startTime
        """ % date
        
        results = []
        try:
            for row in self.graph.query(query):
                job_id = str(row.job).split("/")[-1]
                machine_id = str(row.machine).split("/")[-1]
                product_id = str(row.product).split("/")[-1]
                
                result = {
                    "job_id": job_id,
                    "machine_id": machine_id,
                    "product_id": product_id,
                    "start_time": str(row.startTime),
                    "end_time": str(row.endTime),
                    "status": str(row.status),
                    "error_code": str(row.errorCode) if row.errorCode else None
                }
                results.append(result)
            
            print(f"✅ Found {len(results)} failed jobs requiring cooling")
        except Exception as e:
            print(f"❌ Error executing SPARQL query: {e}")
        
        return results
    
    def track_product_position(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback query for product position tracking
        
        Args:
            product_id: Product identifier
            
        Returns:
            Current position/status of the product
        """
        print(f"🔄 Fallback: Tracking product position from TTL data: {product_id}")
        
        if not self.graph or len(self.graph) == 0:
            print("⚠️ No TTL data available for fallback")
            return None
        
        # SPARQL query for latest job with this product
        query = """
        PREFIX job: <https://example.com/job/>
        PREFIX product: <https://example.com/product/>
        PREFIX machine: <https://example.com/machine/>
        
        SELECT ?job ?machine ?startTime ?endTime ?status
        WHERE {
            ?job a job:ProductionJob ;
                 job:product product:%s ;
                 job:machine ?machine ;
                 job:startTime ?startTime ;
                 job:endTime ?endTime ;
                 job:status ?status .
        }
        ORDER BY DESC(?endTime)
        LIMIT 1
        """ % product_id
        
        try:
            for row in self.graph.query(query):
                job_id = str(row.job).split("/")[-1]
                machine_id = str(row.machine).split("/")[-1]
                
                result = {
                    "product_id": product_id,
                    "current_location": machine_id,
                    "last_job_id": job_id,
                    "last_update": str(row.endTime),
                    "status": str(row.status),
                    "location_type": "machine"
                }
                
                print(f"✅ Found product at: {machine_id}")
                return result
        except Exception as e:
            print(f"❌ Error executing SPARQL query: {e}")
        
        # If no job found, check if product exists
        product_query = """
        PREFIX product: <https://example.com/product/>
        
        SELECT ?product
        WHERE {
            ?product a product:Product .
            FILTER(?product = product:%s)
        }
        LIMIT 1
        """ % product_id
        
        for row in self.graph.query(product_query):
            print(f"ℹ️ Product {product_id} exists but has no job history")
            return {
                "product_id": product_id,
                "current_location": "warehouse",
                "status": "IN_STORAGE",
                "location_type": "storage"
            }
        
        print(f"⚠️ Product {product_id} not found in TTL data")
        return None
    
    def get_machine_info(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """
        Get machine information from TTL data
        
        Args:
            machine_id: Machine identifier
            
        Returns:
            Machine information dictionary
        """
        if not self.graph:
            return None
        
        query = """
        PREFIX machine: <https://example.com/machine/>
        
        SELECT ?name ?manufacturer ?requiresCooling
        WHERE {
            machine:%s a machine:Machine ;
                      machine:name ?name ;
                      machine:manufacturer ?manufacturer ;
                      machine:requiresCoolingDuringProduction ?requiresCooling .
        }
        LIMIT 1
        """ % machine_id
        
        for row in self.graph.query(query):
            return {
                "id": machine_id,
                "name": str(row.name),
                "manufacturer": str(row.manufacturer),
                "requires_cooling": bool(row.requiresCooling)
            }
        
        return None
    
    def get_product_info(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product information from TTL data
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product information dictionary
        """
        if not self.graph:
            return None
        
        query = """
        PREFIX product: <https://example.com/product/>
        
        SELECT ?name ?type ?material ?requiresCooling
        WHERE {
            product:%s a product:Product ;
                      product:name ?name ;
                      product:type ?type ;
                      product:material ?material ;
                      product:requiresCoolingDuringProduction ?requiresCooling .
        }
        LIMIT 1
        """ % product_id
        
        for row in self.graph.query(query):
            return {
                "id": product_id,
                "name": str(row.name),
                "type": str(row.type),
                "material": str(row.material),
                "requires_cooling": bool(row.requiresCooling)
            }
        
        return None