# Factory Automation with AAS Integration

Smart factory automation system using external AAS (Asset Administration Shell) server with ontology-based execution engine.

## System Requirements

- **External AAS Server**: Must be running at `http://localhost:5001`
- **Python 3.8+** for local development
- **Docker & Kubernetes** for containerized deployment

## Quick Start

For detailed setup instructions, please refer to [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md).

### 1. Start External AAS Server
Ensure your standard AAS server is running at `localhost:5001` before proceeding.

### 2. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn api.main:app --reload --port 8000
```

### 3. Test the System
```bash
# Test Goal 1: Query failed cooling jobs
python test_goal1.py

# Test Goal 4: Track product position  
python test_goal4.py
```

## Working Features

| Goal | Description | Status | Test Command |
|------|-------------|--------|--------------|
| Goal 1 | Query failed cooling jobs | ✅ Working | `python test_goal1.py` |
| Goal 3 | Production time prediction | ✅ Working (Fallback) | Manual test via API |
| Goal 4 | Product position tracking | ✅ Working | `python test_goal4.py` |
| Goal 2 | Anomaly detection | ⏳ Needs ML model | Not available |

## API Endpoints

### POST `/execute-goal`
Execute goal-based operations using ontology-driven workflow.

**Request:**
```json
{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-08-11"
}
```

**Supported Goals:**
- `query_failed_jobs_with_cooling` - Query failed jobs with cooling process
- `track_product_position` - Track product location in factory
- `predict_first_completion_time` - Predict production completion time

## Architecture

```
External AAS Server (localhost:5001)
           ↑
           |
    FastAPI Service (port 8000)
           |
    ┌──────┴──────┐
    ↓             ↓
Execution     Ontology
Engine        (RDF/TTL)
```

## Project Structure

```
factory-automation-k8s/
├── api/                    # FastAPI application
│   ├── main.py            # API endpoints  
│   └── schemas.py         # Request/response models
├── execution_engine/       # Core logic
│   ├── planner.py         # Ontology-based planning
│   └── agent.py           # Action execution
├── ontology/              # RDF ontology files
├── k8s/                   # Kubernetes manifests
├── config.py              # Configuration
└── test_*.py              # Test scripts
```

## Configuration

The system is configured to use an external standard AAS server. Mock server functionality has been deprecated.

**Environment Variables:**
- `USE_STANDARD_SERVER=true` (default)
- `AAS_SERVER_IP=127.0.0.1`
- `AAS_SERVER_PORT=5001`

## Kubernetes Deployment

For Kubernetes deployment instructions, see [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md).

## Testing

Run individual goal tests:
```bash
# Test with external AAS server
USE_STANDARD_SERVER=true python test_goal1.py
USE_STANDARD_SERVER=true python test_goal4.py
```

## Troubleshooting

### Connection Refused to localhost:5001
- Verify external AAS server is running
- Check firewall settings
- Confirm port 5001 is accessible

### Module Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

## Development

For detailed setup and development instructions, refer to [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md).

## License

MIT