#!/usr/bin/env python3
"""
Dynamic Data Handler for AAS Test Data
Demonstrates how to update dynamic data in both SPARQL and AAS formats
"""

import json
import os
from datetime import datetime, timedelta
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# Namespaces
PROD = Namespace("http://example.org/production-domain#")


class DynamicDataHandler:
    def __init__(self, base_path):
        self.base_path = base_path
        self.sparql_path = os.path.join(base_path, "sparql-data")
        self.aasx_path = os.path.join(base_path, "aasx-data")
        
    def update_machine_status(self, machine_id, status, sensor_data, timestamp=None):
        """Update machine status in both SPARQL and AAS formats"""
        if timestamp is None:
            timestamp = datetime.now().isoformat() + "Z"
            
        # Update SPARQL data (create new snapshot)
        self._update_sparql_snapshot(machine_id, status, sensor_data, timestamp)
        
        # Update AAS operational submodel
        self._update_aas_operational(machine_id, status, sensor_data, timestamp)
        
        # Update time series data
        self._append_timeseries(machine_id, status, sensor_data, timestamp)
        
    def _update_sparql_snapshot(self, machine_id, status, sensor_data, timestamp):
        """Create or update SPARQL snapshot file"""
        date_str = timestamp.split("T")[0]
        snapshot_file = os.path.join(
            self.sparql_path, 
            "snapshot", 
            f"operational-snapshot-{date_str.replace('-', '')}.ttl"
        )
        
        # For demonstration, we'll append to existing file
        # In production, you'd manage this more carefully
        graph = Graph()
        graph.bind("prod", PROD)
        
        machine_uri = PROD[machine_id]
        status_node = graph.resource(machine_uri + "_status_" + timestamp.replace(":", ""))
        
        graph.add((machine_uri, PROD.hasStatus, Literal(status)))
        graph.add((machine_uri, PROD.hasOperationalStatus, status_node))
        graph.add((status_node, RDF.type, PROD.MachineStatus))
        graph.add((status_node, PROD.statusValue, Literal(status)))
        graph.add((status_node, PROD.temperature, Literal(sensor_data.get("temperature", 0), datatype=XSD.float)))
        graph.add((status_node, PROD.pressure, Literal(sensor_data.get("pressure", 0), datatype=XSD.float)))
        graph.add((status_node, PROD.vibration, Literal(sensor_data.get("vibration", 0), datatype=XSD.float)))
        graph.add((status_node, PROD.recordedAt, Literal(timestamp, datatype=XSD.dateTime)))
        
        # Write to file (append mode for demo)
        with open(snapshot_file, "a") as f:
            f.write("\n# Update at " + timestamp + "\n")
            f.write(graph.serialize(format="turtle"))
            
    def _update_aas_operational(self, machine_id, status, sensor_data, timestamp):
        """Update AAS operational submodel"""
        # Map machine ID to AAS submodel ID
        mapping = self._load_ontology_mapping()
        machine_map = mapping["machine_mappings"].get(machine_id, {})
        operational_id = machine_map.get("submodels", {}).get("operational")
        
        if not operational_id:
            print(f"No operational submodel found for {machine_id}")
            return
            
        submodel_file = os.path.join(self.aasx_path, "submodels", f"{operational_id}.json")
        
        if os.path.exists(submodel_file):
            with open(submodel_file, "r") as f:
                submodel = json.load(f)
                
            # Update status
            for element in submodel["submodelElements"]:
                if element["idShort"] == "CurrentStatus":
                    element["value"] = status
                    # Update qualifier
                    for qual in element.get("qualifiers", []):
                        if qual["type"] == "LastUpdate":
                            qual["value"] = timestamp
                            
                elif element["idShort"] == "SensorReadings":
                    # Update sensor values
                    for sensor in element["value"]:
                        if sensor["idShort"] == "Temperature":
                            sensor["value"] = str(sensor_data.get("temperature", 0))
                        elif sensor["idShort"] == "Pressure":
                            sensor["value"] = str(sensor_data.get("pressure", 0))
                        elif sensor["idShort"] == "Vibration":
                            sensor["value"] = str(sensor_data.get("vibration", 0))
                            
            # Write back
            with open(submodel_file, "w") as f:
                json.dump(submodel, f, indent=2)
                
    def _append_timeseries(self, machine_id, status, sensor_data, timestamp):
        """Append to time series data"""
        date_str = timestamp.split("T")[0]
        ts_file = os.path.join(
            self.aasx_path, 
            "timeseries", 
            f"sensor-data-{date_str.replace('-', '')}.json"
        )
        
        if os.path.exists(ts_file):
            with open(ts_file, "r") as f:
                ts_data = json.load(f)
        else:
            ts_data = {
                "description": f"Time series sensor data for {date_str}",
                "timeRange": {
                    "start": f"{date_str}T00:00:00Z",
                    "end": f"{date_str}T23:59:59Z"
                },
                "machines": {}
            }
            
        # Map to AAS ID
        mapping = self._load_ontology_mapping()
        aas_id = mapping["machine_mappings"].get(machine_id, {}).get("aas_id", f"aas-{machine_id.lower()}")
        
        if aas_id not in ts_data["machines"]:
            ts_data["machines"][aas_id] = {
                "ontologyUri": f"http://example.org/production-domain#{machine_id}",
                "dataPoints": []
            }
            
        # Append new data point
        ts_data["machines"][aas_id]["dataPoints"].append({
            "timestamp": timestamp,
            "temperature": sensor_data.get("temperature", 0),
            "pressure": sensor_data.get("pressure", 0),
            "vibration": sensor_data.get("vibration", 0),
            "status": status
        })
        
        # Write back
        with open(ts_file, "w") as f:
            json.dump(ts_data, f, indent=2)
            
    def _load_ontology_mapping(self):
        """Load ontology to AAS mapping"""
        mapping_file = os.path.join(self.base_path, "common", "ontology-mapping.json")
        with open(mapping_file, "r") as f:
            return json.load(f)
            
    def simulate_real_time_updates(self):
        """Simulate real-time sensor updates"""
        print("Starting real-time simulation...")
        
        # Simulate updates for CoolingMachine-01
        base_time = datetime.now()
        
        for i in range(5):
            current_time = (base_time + timedelta(minutes=i*15)).isoformat() + "Z"
            
            # Gradually increasing temperature (simulating problem)
            sensor_data = {
                "temperature": 22.5 + (i * 0.8),
                "pressure": 101.3 + (i * 0.5),
                "vibration": 2.1 + (i * 0.3)
            }
            
            # Status changes based on temperature
            if sensor_data["temperature"] > 24.5:
                status = "Warning"
            elif sensor_data["temperature"] > 25.0:
                status = "Error"
            else:
                status = "Active"
                
            print(f"Update {i+1}: {current_time} - Status: {status}, Temp: {sensor_data['temperature']}")
            self.update_machine_status("CoolingMachine-01", status, sensor_data, current_time)
            
        print("Simulation complete!")


if __name__ == "__main__":
    # Example usage
    handler = DynamicDataHandler("/Users/jeongseunghwan/Desktop/aas-project/testing/v2/aas-test-data")
    
    # Single update example
    handler.update_machine_status(
        "CoolingMachine-02",
        "Active",
        {"temperature": 22.8, "pressure": 101.5, "vibration": 2.2}
    )
    
    # Run simulation
    # handler.simulate_real_time_updates()