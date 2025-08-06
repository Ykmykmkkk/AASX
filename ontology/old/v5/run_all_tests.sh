#!/bin/bash

# Run all tests for AAS Integration v5
# This script ensures mock server is running and executes all tests

echo "🧪 AAS Integration v5 - Complete Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if we're in the v5 directory
if [[ ! $(pwd) =~ "v5" ]]; then
    echo -e "${RED}❌ Please run this script from the v5 directory${NC}"
    exit 1
fi

# Function to check if mock server is running
check_mock_server() {
    curl -s http://localhost:5001/health > /dev/null 2>&1
    return $?
}

# Function to start mock server
start_mock_server() {
    echo -e "${BLUE}Starting Mock Server v2...${NC}"
    
    # Kill any existing mock server
    pkill -f "mock_server_v2" 2>/dev/null
    
    # Generate mock data if needed
    if [ ! -d "aas_integration/mock_data/shells" ]; then
        echo -e "${YELLOW}Generating mock data...${NC}"
        python3 -m aas_integration.standards.mock_data_generator
    fi
    
    # Start mock server in background
    python3 -m aas_integration.mock_server_v2 > mock_server.log 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    echo -n "Waiting for server to start"
    for i in {1..30}; do
        if check_mock_server; then
            echo ""
            echo -e "${GREEN}✅ Mock server started (PID: $SERVER_PID)${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo ""
    echo -e "${RED}❌ Failed to start mock server${NC}"
    return 1
}

# Step 1: Check or start mock server
echo -e "${BLUE}Step 1: Checking Mock Server${NC}"
echo "----------------------------"

if check_mock_server; then
    echo -e "${GREEN}✅ Mock server is already running${NC}"
else
    echo -e "${YELLOW}⚠️  Mock server not running${NC}"
    if start_mock_server; then
        STARTED_SERVER=true
    else
        echo -e "${RED}Failed to start mock server. Check mock_server.log${NC}"
        exit 1
    fi
fi

echo ""

# Step 2: Run integration tests
echo -e "${BLUE}Step 2: Running Integration Tests${NC}"
echo "---------------------------------"

python3 test_v2_integration.py
TEST_RESULT=$?

echo ""

# Step 3: Run specific goal tests if available
if [ -f "test_goal1_v2.py" ]; then
    echo -e "${BLUE}Step 3: Running Goal-Specific Tests${NC}"
    echo "-----------------------------------"
    
    echo -e "${YELLOW}Testing Goal 1...${NC}"
    python3 test_goal1_v2.py
    
    if [ -f "test_goal4_v2.py" ]; then
        echo -e "${YELLOW}Testing Goal 4...${NC}"
        python3 test_goal4_v2.py
    fi
else
    echo -e "${YELLOW}ℹ️  Goal-specific tests not found${NC}"
fi

echo ""

# Step 4: Summary
echo -e "${BLUE}Test Summary${NC}"
echo "============"

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ All integration tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
fi

# Cleanup
if [ "$STARTED_SERVER" = true ]; then
    echo ""
    echo -e "${YELLOW}Mock server will continue running for manual testing${NC}"
    echo "To stop it, run: pkill -f mock_server_v2"
fi

echo ""
echo "📋 Logs available at:"
echo "   - mock_server.log (server output)"
echo ""

exit $TEST_RESULT