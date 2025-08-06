# AAS Integration v5

Asset Administration Shell (AAS) Integration System implementing Industry 4.0 standards with hybrid ontology-based architecture.

## Quick Start

### 1. Generate Mock Data
```bash
python3 -m aas_integration.standards.mock_data_generator
```

### 2. Start Mock Server
```bash
python3 -m aas_integration.mock_server_v2
```

### 3. Run Tests
```bash
# Full test suite
./run_all_tests.sh

# Quick test (server must be running)
./quick_test.sh
```

## Project Structure

```
v5/
├── aas_integration/          # Core implementation
│   ├── client_v2.py         # AAS REST client
│   ├── executor_v2.py       # DSL executor
│   ├── mock_server_v2.py    # Mock AAS server
│   ├── fallback.py          # Fallback handler
│   ├── utils.py             # Utilities
│   └── standards/           # AAS standards
├── test_v2_integration.py   # Integration tests
├── run_all_tests.sh         # Test runner
└── CLAUDE.md               # Full documentation
```

## Goals

- **Goal 1**: Query failed jobs with cooling requirements ✅
- **Goal 2**: Detect product anomalies (placeholder)
- **Goal 3**: Predict job completion time (placeholder)  
- **Goal 4**: Track product position ✅

## Key Features

- Industry 4.0 AAS Metamodel 3.0 compliance
- 3-tier fallback strategy (AAS Server → Mock → TTL)
- Hybrid architecture (Ontology + AAS)
- BASE64-URL encoding for identifiers
- Standard submodels (Nameplate, TechnicalData, OperationalData, Documentation)

## Example Usage

```python
from aas_integration.executor_v2 import AASExecutorV2

executor = AASExecutorV2()

# Query failed jobs
result = executor.execute({
    "goal": "query_failed_jobs_with_cooling",
    "parameters": {"date": "2025-07-17"}
})

# Track product
result = executor.execute({
    "goal": "track_product_position",
    "parameters": {"product_id": "Product-C1"}
})
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for comprehensive documentation including:
- Architecture details
- API reference
- Development guide
- Troubleshooting

## Status

✅ Core implementation complete  
✅ Mock data generation  
✅ AAS standard compliance  
⏸️ Goals 2 & 3 pending  
📋 Full test coverage needed