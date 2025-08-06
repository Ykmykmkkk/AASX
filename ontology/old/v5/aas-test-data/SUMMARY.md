# AAS Test Data Summary

## Overview

This test data package provides both SPARQL-compatible (TTL) and AAS-standard (JSON) formats for testing the ontology-based execution planner. The data is fully synchronized and compliant with the existing ontology structure.

## Key Features

### 1. Dual Format Support
- **SPARQL Data**: TTL files that can be loaded directly into rdflib's in-memory graph
- **AAS Data**: JSON files following the Asset Administration Shell standard

### 2. Complete Test Coverage
- **Goal 1**: 3 failed jobs with cooling requirements (Job-2001, Job-2002, Job-2003)
- **Goal 2**: 6 machines with error states and sensor anomalies
- **Goal 3**: 18 products with complete specifications and templates
- **Goal 4**: 1 job currently processing with real-time tracking (Job-2008)

### 3. Static vs Dynamic Data Separation
- **Static**: Machine specifications, product definitions (rarely changes)
- **Dynamic**: Operational status, sensor readings (frequently updated)
- **Historical**: Time-series data with external database references

### 4. Ontology Compliance
All data strictly follows the existing ontology structure:
- Uses properties from `domain-ontology.ttl` (hasCapability, hasStatus, requiresCooling, etc.)
- Maintains URI consistency (`http://example.org/production-domain#`)
- Supports all SPARQL queries defined in `execution-ontology.ttl`

## Data Statistics

### Machines (16 total)
- 5 Cooling Machines
- 3 Heating Machines  
- 4 Assembly Machines
- 2 Cutting Machines
- 2 Welding Machines

### Products (18 total)
- Type A: Cutting + Assembly + Cooling (3 variants)
- Type B: Heating + Welding + Cooling (3 variants)
- Type C: Cutting + Heating + Assembly (3 variants)
- Type D: Assembly + Cooling (3 variants)
- Type E: Welding + Heating + Cooling (3 variants)
- Type F: All operations (3 variants)

### Job History (8 jobs on 2025-07-17)
- 3 Failed with cooling requirement
- 2 Successful with cooling
- 1 Failed without cooling
- 1 Successful without cooling
- 1 Currently processing

## Usage Examples

### Loading SPARQL Data
```python
from rdflib import Graph

# Load all data
graph = Graph()
for ttl_file in ["machines-static.ttl", "products-static.ttl", 
                 "operational-snapshot-20250717.ttl", "job-history-20250717.ttl"]:
    graph.parse(f"sparql-data/{category}/{ttl_file}", format="ttl")
```

### Accessing AAS Data
```python
import json

# Load registry
with open("aasx-data/registry.json") as f:
    registry = json.load(f)

# Access specific shell
with open("aasx-data/shells/aas-cooling-machine-01.json") as f:
    shell = json.load(f)

# Get operational data
with open("aasx-data/submodels/sm-operational-cm01.json") as f:
    operational_data = json.load(f)
```

### Dynamic Updates
```python
from dynamic_data_handler import DynamicDataHandler

handler = DynamicDataHandler("aas-test-data")
handler.update_machine_status(
    "CoolingMachine-01",
    "Active", 
    {"temperature": 22.5, "pressure": 101.3, "vibration": 2.1}
)
```

## Files Included

### Core Files
- `README.md`: Detailed documentation
- `SUMMARY.md`: This summary file
- `validate_test_data.py`: Validation script
- `dynamic-data-handler.py`: Dynamic update handler

### Data Files
- `common/ontology-mapping.json`: Maps ontology URIs to AAS IDs
- `sparql-data/`: TTL files for SPARQL engine
- `aasx-data/`: JSON files for AAS server

## Validation Results

Running `python3 validate_test_data.py`:
- ✅ All directory structures present
- ✅ Ontology mapping validated (16 machines, 11 properties)
- ✅ SPARQL data parsed successfully (705 total triples)
- ✅ Test goals fully supported
- ⚠️  Only 1 complete AAS shell example (others can be generated similarly)

## Next Steps

1. **Complete AAS Shells**: Generate remaining 15 machine shells following the CoolingMachine-01 pattern
2. **Integration Testing**: Test with real execution planner and external services
3. **Performance Testing**: Validate with larger datasets
4. **Real AAS Server**: Deploy to actual AAS server implementation

## Notes

- Test data uses 2025-07-17 as the reference date
- All timestamps are in ISO 8601 format with UTC timezone
- Sensor values are realistic but simulated
- Error conditions are designed to test anomaly detection