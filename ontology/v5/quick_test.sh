#!/bin/bash

# Quick test script for AAS Integration v5
# Assumes mock server is already running

echo "⚡ AAS Integration v5 - Quick Test"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if mock server is running
curl -s http://localhost:5001/health > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Mock server is not running!${NC}"
    echo "Please start it with: python3 -m aas_integration.mock_server_v2"
    exit 1
fi

echo -e "${GREEN}✅ Mock server is running${NC}"
echo ""

# Test Goal 1
echo -e "${BLUE}Testing Goal 1: Query Failed Jobs with Cooling${NC}"
echo "----------------------------------------------"

python3 -c "
from aas_integration.executor_v2 import AASExecutorV2
import json

executor = AASExecutorV2()
result = executor.execute({
    'goal': 'query_failed_jobs_with_cooling',
    'parameters': {'date': '2025-07-17'}
})

if result.get('success'):
    data = result.get('data', [])
    print(f'✅ Found {len(data)} failed jobs requiring cooling')
    for job in data[:3]:  # Show first 3
        print(f'  - {job[\"job_id\"]}: {job[\"product_id\"]} on {job[\"machine_id\"]}')
else:
    print(f'❌ Goal 1 failed: {result.get(\"message\")}')
"

echo ""

# Test Goal 4
echo -e "${BLUE}Testing Goal 4: Track Product Position${NC}"
echo "--------------------------------------"

python3 -c "
from aas_integration.executor_v2 import AASExecutorV2

executor = AASExecutorV2()
result = executor.execute({
    'goal': 'track_product_position',
    'parameters': {'product_id': 'Product-C1'}
})

if result.get('success'):
    data = result.get('data', {})
    print(f'✅ Product C1 location: {data.get(\"current_location\", \"Unknown\")}')
    print(f'   Status: {data.get(\"status\", \"Unknown\")}')
else:
    print(f'❌ Goal 4 failed: {result.get(\"message\")}')
"

echo ""
echo -e "${GREEN}Quick test completed!${NC}"