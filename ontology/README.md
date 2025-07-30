# AAS (Asset Administration Shell) SPARQL Query Execution System - v3

This project implements a SPARQL query execution system for AAS test data, enabling real-time querying and analysis of production data using semantic web technologies.

## Overview

Version 3 extends the AAS execution planner to support SPARQL query execution against RDF/TTL data. It integrates three ontologies (execution, domain, and bridge) to process DSL inputs and generate execution plans with actual query results.

## Project Structure

```
v3/
├── ontologies/
│   ├── execution-ontology.ttl    # Defines execution workflow and actions
│   ├── domain-ontology.ttl       # Production domain concepts
│   └── bridge-ontology.ttl       # Maps DSL goals to execution goals
├── aas-test-data/
│   └── sparql-data/
│       ├── static/               # Static machine and product data
│       ├── snapshot/             # Operational snapshots
│       └── historical/           # Job history data
├── execution_engine/             # Docker-based execution engine
├── test results/
│   └── test_result_*.json        # Query execution results
└── main scripts/
    ├── dsl_execution_with_sparql.py  # Main execution planner
    ├── test_single_goal.py           # Test individual goals
    └── test_custom_query.py          # Custom query testing
```

## Features

- **Ontology-Based Planning**: Uses RDF/TTL ontologies to define execution workflows
- **SPARQL Query Execution**: Executes parameterized SPARQL queries against RDF data
- **Dynamic Parameter Substitution**: Replaces query placeholders with DSL input values
- **Multi-Format Support**: Handles various RDF data formats and query patterns
- **Comprehensive Testing**: Includes test cases for all four main goals

## Installation

```bash
# Install required Python packages
pip install rdflib

# Verify all TTL files are present
ls *.ttl aas-test-data/sparql-data/*/*.ttl
```

## Usage

### Run All Tests
```bash
python3 dsl_execution_with_sparql.py
```

### Test Single Goal
```bash
python3 test_single_goal.py
```
Edit `goal_number` variable (1-4) to select specific goal.

### Custom Query Testing
```bash
python3 test_custom_query.py
```
Modify parameters in the script for different scenarios.

## Supported Goals

### Goal 1: Query Failed Jobs with Cooling
Finds production jobs that failed and required cooling on a specific date.
```python
{
    "goal": "query_failed_jobs_with_cooling",
    "date": "2025-07-17"
}
```

### Goal 2: Detect Anomaly for Product
Detects anomalies for specific products within a date range.
```python
{
    "goal": "detect_anomaly_for_product",
    "product_id": "Product-A1",
    "date_range": {
        "start": "2025-07-17T00:00:00",
        "end": "2025-07-17T23:59:59"
    },
    "target_machine": "CoolingMachine-01"
}
```

### Goal 3: Predict First Completion Time
Predicts completion time for a product batch (requires additional data).
```python
{
    "goal": "predict_first_completion_time",
    "product_id": "Product-B2",
    "quantity": 100
}
```

### Goal 4: Track Product Position
Tracks current position/status of a product in the production line.
```python
{
    "goal": "track_product_position",
    "product_id": "Product-C1"
}
```

## Technical Details

### SPARQL Query Processing
1. **Template System**: Uses SPARQL templates defined in ontology
2. **Parameter Substitution**: 
   - `%%FILTERS%%`: Dynamic filter conditions
   - `%%DATE_FILTER%%`: Date range filters
   - `%%PRODUCT_ID%%`: Product identifiers
3. **Result Transformation**: Converts RDFLib results to JSON format

### Data Statistics
- **Total Triples**: 705+ (with additional data files)
- **Data Categories**:
  - Static: Machine and product definitions
  - Snapshot: Point-in-time operational data
  - Historical: Job execution history

### Ontology Integration
- **Execution Ontology**: Defines workflow actions and goals
- **Domain Ontology**: Production domain concepts and relationships
- **Bridge Ontology**: Maps DSL goals to execution goals

## Test Results Summary

| Goal | Description | Result Count |
|------|-------------|--------------|
| Goal 1 | Failed jobs with cooling | 3 records |
| Goal 2 | Product anomaly detection | 1 record |
| Goal 3 | Completion time prediction | Needs more data |
| Goal 4 | Product position tracking | 1 record |

## Future Enhancements

1. **Real AAS Server Integration**: Connect to live AAS endpoints
2. **Advanced SPARQL Features**: Support for complex joins, aggregations, and reasoning
3. **Real-time Data Streaming**: Process continuous data streams
4. **SHACL Validation**: Add data shape validation
5. **Performance Optimization**: Query caching and indexing
6. **Extended Analytics**: Machine learning model integration

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure all TTL files are in correct directories
2. **Empty Results**: Check date formats and product IDs in test data
3. **Query Errors**: Validate SPARQL syntax and namespace prefixes

### Debug Mode
Enable detailed debugging in `dsl_execution_with_sparql.py`:
- Check loaded triples count
- View SPARQL query before execution
- Inspect intermediate results

## License

This project is part of the AAS testing framework for production systems.