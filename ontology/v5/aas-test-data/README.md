# AAS-Standard Compliant Test Data

This directory contains test data in two formats:
1. **SPARQL Data (TTL)**: For use with the built-in rdflib SPARQL engine
2. **AAS Data (JSON)**: For use with AAS server implementations

## Directory Structure

```
aas-test-data/
├── common/
│   └── ontology-mapping.json      # Maps between ontology URIs and AAS IDs
├── sparql-data/                   # TTL files for SPARQL engine
│   ├── static/                    # Static machine and product data
│   │   ├── machines-static.ttl    # 16 machines with all properties
│   │   └── products-static.ttl    # 18 products (A1-F3)
│   ├── snapshot/                  # Point-in-time operational data
│   │   └── operational-snapshot-20250717.ttl
│   └── historical/                # Historical job execution data
│       └── job-history-20250717.ttl
└── aasx-data/                     # AAS-standard JSON files
    ├── registry.json              # Central registry of all AAS shells
    ├── shells/                    # AAS shell definitions
    │   ├── aas-cooling-machine-01.json
    │   └── aas-product-c1-batch-001.json
    ├── submodels/                 # Submodel definitions
    │   ├── sm-nameplate-cm01.json
    │   ├── sm-operational-cm01.json
    │   ├── sm-capability-cm01.json
    │   ├── sm-history-cm01.json
    │   ├── sm-maintenance-cm01.json
    │   └── sm-tracking-c1-001.json
    └── timeseries/                # Time series sensor data
        └── sensor-data-20250717.json
```

## Data Synchronization

Both SPARQL and AAS data represent the same information:
- Machine IDs and properties are consistent
- Status values match at the same timestamps
- Job history is identical in both formats
- Product requirements align

## Goal Support

### Goal 1: Query Failed Jobs with Cooling
- **SPARQL**: `job-history-20250717.ttl` contains Job-2001, Job-2002, Job-2003 (failed + cooling)
- **AAS**: `sm-history-cm01.json` references the same job failures

### Goal 2: Detect Anomaly for Product
- **SPARQL**: `operational-snapshot-20250717.ttl` contains sensor readings
- **AAS**: `sm-operational-cm01.json` has current sensor data with error states

### Goal 3: Predict First Completion Time
- **SPARQL**: Product capabilities in `products-static.ttl`
- **AAS**: Process capabilities in `sm-capability-*.json` submodels

### Goal 4: Track Product Position
- **SPARQL**: Job-2008 in `job-history-20250717.ttl` shows current processing
- **AAS**: `sm-tracking-c1-001.json` provides real-time product location

## Static vs Dynamic Data

### Static Data (Rarely Changes)
- Machine specifications (Nameplate submodel)
- Product definitions and requirements
- Process capabilities
- Physical locations

### Dynamic Data (Frequently Updated)
- Operational status (OperationalData submodel)
- Sensor readings (Temperature, Pressure, Vibration)
- Job execution status
- Product location tracking

### Historical Data Storage
- **Time Series**: Stored in separate TimeSeries submodels or external databases
- **Reference**: `DetailedHistoryEndpoint` in history submodels points to external storage
- **Aggregated Metrics**: Daily/hourly summaries for performance analysis

## Usage

### With Built-in SPARQL Engine
```python
# Load all TTL files into RDF graph
graph = Graph()
graph.parse("sparql-data/static/machines-static.ttl", format="ttl")
graph.parse("sparql-data/static/products-static.ttl", format="ttl")
graph.parse("sparql-data/snapshot/operational-snapshot-20250717.ttl", format="ttl")
graph.parse("sparql-data/historical/job-history-20250717.ttl", format="ttl")
```

### With AAS Server
```python
# Use registry.json to discover available shells
# Access shells and submodels via their endpoints
# Example: GET http://aas-server/api/shells/aas-cooling-machine-01
```

## Ontology Compliance

All data strictly follows the existing ontology structure:
- `domain-ontology.ttl`: Machine, Product, Job concepts
- `execution-ontology.ttl`: Goal and Action definitions
- `bridge-ontology.ttl`: DSL to ontology mappings

Properties like `hasCapability`, `hasStatus`, `requiresCooling` are used consistently across both data formats.