# External Service Interface Documentation

## Overview
This document describes the input/output data structures for AI models and simulators in the execution engine.

## 1. AI Model Interface (Anomaly Detection)

### Input Structure
```json
{
    "input_files": {
        "sensor_data": {
            "source": "step_3_output",
            "data": {
                "sensor_readings": [
                    {
                        "timestamp": "2025-07-17T10:00:00",
                        "temperature": 25.3,
                        "vibration": 2.1,
                        "pressure": 105.2
                    }
                ],
                "count": 50
            }
        },
        "job_history": {
            "source": "step_2_output",
            "data": {
                "results": [
                    {
                        "job": "Job-101",
                        "machine": "CoolingMachine-01",
                        "status": "Failed",
                        "startTime": "2025-07-17T08:00:00"
                    }
                ],
                "count": 10
            }
        },
        "machine_status": {
            "source": "machines.json",
            "data": [
                {
                    "id": "CoolingMachine-01",
                    "status": "Active",
                    "efficiency": 0.92,
                    "lastMaintenance": "2025-06-15T00:00:00"
                }
            ]
        },
        "product_specs": {
            "source": "products.json",
            "product_id": "Product-A1",
            "data": [
                {
                    "product_id": "Product-A1",
                    "name": "Product A1",
                    "requirements": ["cooling", "heating"],
                    "tolerance": {
                        "temperature": {"min": 20, "max": 30},
                        "pressure": {"min": 100, "max": 110}
                    }
                }
            ]
        }
    },
    "parameters": {
        "target_machine": "CoolingMachine-01",
        "date_range": {
            "from": "2025-07-15",
            "to": "2025-07-17"
        },
        "anomaly_threshold": 0.85,
        "detection_algorithms": ["isolation_forest", "lstm_autoencoder", "statistical_analysis"]
    }
}
```

### Output Structure
```json
{
    "anomalies": [
        {
            "timestamp": "2025-07-17T14:30:00",
            "type": "temperature_spike",
            "severity": "high",
            "confidence": 0.92,
            "affected_sensors": ["TEMP_001", "TEMP_002"],
            "deviation": "+15.3°C from baseline",
            "context": {
                "preceding_events": ["Job-101 failed", "Vibration increased"],
                "machine_state": "Active but degraded"
            }
        }
    ],
    "overall_confidence": 0.87,
    "recommendation": "Schedule maintenance check",
    "risk_score": 7.5,
    "analysis_metadata": {
        "algorithms_used": ["isolation_forest", "lstm_autoencoder"],
        "processing_time": 1.8,
        "data_quality_score": 0.95
    }
}
```

## 2. Simulator Interface (Production Planning)

### Input Structure
```json
{
    "input_files": {
        "job_template": {
            "source": "step_2_output",
            "data": {
                "operations": [
                    {
                        "name": "Cooling",
                        "duration": 30,
                        "machine": "CoolingMachine",
                        "requirements": {
                            "temperature": 5,
                            "power": 1500
                        }
                    },
                    {
                        "name": "Heating",
                        "duration": 45,
                        "machine": "HeatingMachine",
                        "requirements": {
                            "temperature": 80,
                            "power": 2000
                        }
                    }
                ],
                "total_operations": 3
            }
        },
        "machine_schedule": {
            "source": "step_3_output",
            "data": {
                "machines": [
                    {
                        "id": "CoolingMachine-01",
                        "status": "Active",
                        "utilization": 0.75,
                        "scheduled_jobs": [
                            {"job_id": "Job-200", "start": "08:00", "end": "09:00"}
                        ]
                    }
                ],
                "count": 5
            }
        },
        "historical_jobs": {
            "source": "jobs.json",
            "data": [
                {
                    "id": "Job-001",
                    "product_id": "Product-B2",
                    "actual_duration": 125,
                    "planned_duration": 120,
                    "delays": [
                        {"reason": "machine_breakdown", "duration": 5}
                    ]
                }
            ]
        },
        "machine_specs": {
            "source": "machines.json",
            "data": [
                {
                    "id": "CoolingMachine-01",
                    "capacity": 100,
                    "efficiency": 0.92,
                    "mtbf": 720,
                    "mttr": 2
                }
            ]
        },
        "scenarios": {
            "source": "scenarios.json",
            "scenario_type": "production_planning",
            "data": [
                {
                    "id": "scenario-1",
                    "type": "production_planning",
                    "complexity": "high",
                    "variables": {
                        "machine_failure_probability": 0.02,
                        "demand_variability": 0.15,
                        "setup_time_factor": 1.1
                    }
                }
            ]
        }
    },
    "simulation_parameters": {
        "product_id": "Product-B2",
        "quantity": 100,
        "start_time": "2025-07-28T08:00:00",
        "optimization_goals": ["minimize_time", "balance_load"],
        "constraints": {
            "max_overtime_hours": 4,
            "maintenance_windows": [
                "2025-07-28T18:00:00",
                "2025-07-29T06:00:00"
            ],
            "resource_limits": {
                "operators": 10,
                "power_capacity": 5000
            }
        },
        "monte_carlo_runs": 1000,
        "confidence_level": 0.95
    }
}
```

### Output Structure
```json
{
    "predicted_completion": "2025-07-29T18:30:00",
    "confidence_interval": {
        "lower": "2025-07-29T17:00:00",
        "upper": "2025-07-29T20:00:00",
        "confidence_level": 0.95
    },
    "bottlenecks": [
        {
            "machine": "CoolingMachine-01",
            "utilization": 0.95,
            "queue_time": 45,
            "impact": "Critical path - 30% of total delay"
        }
    ],
    "production_schedule": [
        {
            "batch": 1,
            "quantity": 20,
            "operations": [
                {
                    "operation": "Cooling",
                    "machine": "CoolingMachine-02",
                    "start": "2025-07-28T08:00:00",
                    "end": "2025-07-28T08:30:00",
                    "operator": "Team-A"
                }
            ]
        }
    ],
    "estimated_cost": 2450.00,
    "cost_breakdown": {
        "labor": 1200,
        "machine_time": 950,
        "energy": 300
    },
    "resource_efficiency": 0.82,
    "risk_analysis": {
        "machine_failure_risk": 0.15,
        "delay_probability": 0.22,
        "contingency_plans": [
            {
                "trigger": "CoolingMachine-01 failure",
                "action": "Redirect to CoolingMachine-02",
                "impact": "+2 hours"
            }
        ]
    },
    "optimization_results": {
        "original_duration": 720,
        "optimized_duration": 630,
        "improvement": "12.5%"
    }
}
```

## Integration Notes

### For AI Model Development
1. **Multiple Data Sources**: The AI model receives data from multiple JSON files and previous execution steps
2. **Contextual Information**: Include machine status, product specifications, and historical patterns
3. **Algorithm Selection**: Support multiple detection algorithms based on the parameters
4. **Rich Output**: Provide not just anomalies but also context, confidence, and recommendations

### For Simulator Development
1. **Complex Inputs**: Handle job templates, machine schedules, historical data, and scenarios
2. **Monte Carlo Simulation**: Run multiple iterations for statistical confidence
3. **Optimization**: Support multiple optimization goals (time, cost, resource balance)
4. **Detailed Schedule**: Output specific machine assignments and timings
5. **Risk Analysis**: Include contingency planning and risk assessment

### Real Implementation Considerations
```python
# Example: How to call the actual services

# For AI Model (AWS Lambda)
lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='anomaly-detection-v2',
    InvocationType='RequestResponse',
    Payload=json.dumps(ai_input_data)
)
result = json.loads(response['Payload'].read())

# For Simulator (AWS Batch)
batch_client = boto3.client('batch')
response = batch_client.submit_job(
    jobName='production-simulation',
    jobQueue='simulation-queue',
    jobDefinition='production-simulator:latest',
    parameters=simulator_input_data
)
```