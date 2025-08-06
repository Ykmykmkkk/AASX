#!/usr/bin/env python3
"""
Integration tests for AAS v2 implementation
Tests the complete flow from DSL input to results
"""

import json
import time
import subprocess
import requests
from typing import Dict, Any, Optional
from aas_integration.executor_v2 import AASExecutorV2
from aas_integration.client_v2 import AASClientV2


class TestColors:
    """ANSI color codes for test output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{TestColors.BLUE}{'=' * 80}{TestColors.RESET}")
    print(f"{TestColors.BOLD}{test_name}{TestColors.RESET}")
    print(f"{TestColors.BLUE}{'=' * 80}{TestColors.RESET}")


def print_result(success: bool, message: str):
    """Print colored test result"""
    if success:
        print(f"{TestColors.GREEN}✅ {message}{TestColors.RESET}")
    else:
        print(f"{TestColors.RED}❌ {message}{TestColors.RESET}")


def check_mock_server() -> bool:
    """Check if mock server is running"""
    try:
        response = requests.get("http://localhost:5001/health")
        return response.status_code == 200
    except:
        return False


def test_mock_server_endpoints():
    """Test Mock Server v2 endpoints"""
    print_test_header("Testing Mock Server v2 Endpoints")
    
    client = AASClientV2()
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Get all shells
    tests_total += 1
    try:
        shells = client.get_all_shells()
        if len(shells) > 0:
            print_result(True, f"Get all shells: Found {len(shells)} shells")
            tests_passed += 1
        else:
            print_result(False, "Get all shells: No shells found")
    except Exception as e:
        print_result(False, f"Get all shells failed: {e}")
    
    # Test 2: Get specific shell
    tests_total += 1
    try:
        shell = client.get_shell("urn:aas:Machine:CNC001")
        if shell and shell.get('idShort') == 'CNC001':
            print_result(True, f"Get specific shell: Found {shell['idShort']}")
            tests_passed += 1
        else:
            print_result(False, "Get specific shell: Shell not found or incorrect")
    except Exception as e:
        print_result(False, f"Get specific shell failed: {e}")
    
    # Test 3: Get cooling machines
    tests_total += 1
    try:
        response = requests.get("http://localhost:5001/api/machines/cooling-required")
        if response.status_code == 200:
            machines = response.json()
            print_result(True, f"Get cooling machines: Found {len(machines)} machines")
            tests_passed += 1
        else:
            print_result(False, f"Get cooling machines: HTTP {response.status_code}")
    except Exception as e:
        print_result(False, f"Get cooling machines failed: {e}")
    
    # Test 4: Get cooling products
    tests_total += 1
    try:
        response = requests.get("http://localhost:5001/api/products/cooling-required")
        if response.status_code == 200:
            products = response.json()
            expected_products = ['Product-B1', 'Product-C1']
            found_ids = [p['id'] for p in products]
            if all(pid in found_ids for pid in expected_products):
                print_result(True, f"Get cooling products: Found {products}")
                tests_passed += 1
            else:
                print_result(False, f"Get cooling products: Missing expected products. Found: {found_ids}")
        else:
            print_result(False, f"Get cooling products: HTTP {response.status_code}")
    except Exception as e:
        print_result(False, f"Get cooling products failed: {e}")
    
    # Test 5: Get failed jobs
    tests_total += 1
    try:
        response = requests.get("http://localhost:5001/api/jobs/failed?date=2025-07-17")
        if response.status_code == 200:
            jobs = response.json()
            print_result(True, f"Get failed jobs: Found {len(jobs)} failed jobs")
            tests_passed += 1
        else:
            print_result(False, f"Get failed jobs: HTTP {response.status_code}")
    except Exception as e:
        print_result(False, f"Get failed jobs failed: {e}")
    
    print(f"\n{TestColors.BOLD}Mock Server Tests: {tests_passed}/{tests_total} passed{TestColors.RESET}")
    return tests_passed == tests_total


def test_goal1_execution():
    """Test Goal 1: Query failed jobs with cooling"""
    print_test_header("Testing Goal 1: Query Failed Jobs with Cooling")
    
    executor = AASExecutorV2()
    
    # Execute Goal 1
    result = executor.execute({
        "goal": "query_failed_jobs_with_cooling",
        "parameters": {
            "date": "2025-07-17"
        }
    })
    
    # Check results
    if result.get('success'):
        data = result.get('data', [])
        metadata = result.get('metadata', {})
        
        print(f"\n{TestColors.BOLD}Results:{TestColors.RESET}")
        print(f"Total failed jobs: {metadata.get('total_failed_jobs', 0)}")
        print(f"Jobs requiring cooling: {metadata.get('cooling_required_jobs', 0)}")
        print(f"Products requiring cooling: {metadata.get('products_requiring_cooling', 0)}")
        print(f"Machines with cooling: {metadata.get('machines_with_cooling', 0)}")
        
        if len(data) > 0:
            print(f"\n{TestColors.BOLD}Failed Jobs Detail:{TestColors.RESET}")
            for job in data:
                print(f"- Job {job['job_id']}: {job['product_id']} on {job['machine_id']}")
                print(f"  Error: {job.get('error_code', 'Unknown')}")
                print(f"  Duration: {job.get('duration_minutes', 'N/A')} minutes")
            
            # Verify expected results
            expected_jobs = ['JOB-001', 'JOB-002', 'JOB-003']
            found_jobs = [j['job_id'] for j in data]
            
            if all(job_id in found_jobs for job_id in expected_jobs):
                print_result(True, "All expected failed jobs found")
                return True
            else:
                print_result(False, f"Missing expected jobs. Found: {found_jobs}")
                return False
        else:
            print_result(False, "No failed jobs found")
            return False
    else:
        print_result(False, f"Goal execution failed: {result.get('message', 'Unknown error')}")
        return False


def test_goal4_execution():
    """Test Goal 4: Track product position"""
    print_test_header("Testing Goal 4: Track Product Position")
    
    executor = AASExecutorV2()
    
    test_products = ['Product-B1', 'Product-C1', 'Product-A1']
    tests_passed = 0
    
    for product_id in test_products:
        print(f"\n{TestColors.BOLD}Tracking {product_id}:{TestColors.RESET}")
        
        result = executor.execute({
            "goal": "track_product_position",
            "parameters": {
                "product_id": product_id
            }
        })
        
        if result.get('success'):
            data = result.get('data', {})
            location = data.get('current_location', 'Unknown')
            status = data.get('status', 'Unknown')
            location_type = data.get('location_type', 'Unknown')
            
            print(f"Location: {location}")
            print(f"Status: {status}")
            print(f"Type: {location_type}")
            
            if 'last_job_id' in data:
                print(f"Last Job: {data['last_job_id']}")
            
            print_result(True, f"Successfully tracked {product_id}")
            tests_passed += 1
        else:
            print_result(False, f"Failed to track {product_id}: {result.get('message')}")
    
    return tests_passed == len(test_products)


def test_data_validation():
    """Test data validation and error handling"""
    print_test_header("Testing Data Validation and Error Handling")
    
    executor = AASExecutorV2()
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Missing parameters
    tests_total += 1
    result = executor.execute({
        "goal": "query_failed_jobs_with_cooling",
        "parameters": {}  # Missing date
    })
    
    if not result.get('success') and result.get('error_type') == 'VALIDATION_ERROR':
        print_result(True, "Correctly handled missing parameters")
        tests_passed += 1
    else:
        print_result(False, "Failed to catch missing parameters")
    
    # Test 2: Invalid date format
    tests_total += 1
    result = executor.execute({
        "goal": "query_failed_jobs_with_cooling",
        "parameters": {
            "date": "2025/07/17"  # Wrong format
        }
    })
    
    if not result.get('success') and result.get('error_type') == 'VALIDATION_ERROR':
        print_result(True, "Correctly handled invalid date format")
        tests_passed += 1
    else:
        print_result(False, "Failed to catch invalid date format")
    
    # Test 3: Unknown goal
    tests_total += 1
    result = executor.execute({
        "goal": "unknown_goal",
        "parameters": {}
    })
    
    if not result.get('success') and result.get('error_type') == 'VALIDATION_ERROR':
        print_result(True, "Correctly handled unknown goal")
        tests_passed += 1
    else:
        print_result(False, "Failed to catch unknown goal")
    
    # Test 4: Non-existent product
    tests_total += 1
    result = executor.execute({
        "goal": "track_product_position",
        "parameters": {
            "product_id": "Product-X99"
        }
    })
    
    if not result.get('success') and result.get('error_type') == 'PRODUCT_NOT_FOUND':
        print_result(True, "Correctly handled non-existent product")
        tests_passed += 1
    else:
        print_result(False, "Failed to handle non-existent product properly")
    
    print(f"\n{TestColors.BOLD}Validation Tests: {tests_passed}/{tests_total} passed{TestColors.RESET}")
    return tests_passed == tests_total


def run_all_tests():
    """Run all integration tests"""
    print(f"{TestColors.BOLD}AAS Integration Tests v2{TestColors.RESET}")
    print(f"{TestColors.BLUE}{'=' * 80}{TestColors.RESET}")
    
    # Check if mock server is running
    if not check_mock_server():
        print(f"{TestColors.YELLOW}⚠️  Mock server not running!{TestColors.RESET}")
        print("Please start the mock server with:")
        print("  python3 -m aas_integration.mock_server_v2")
        return False
    
    print(f"{TestColors.GREEN}✅ Mock server is running{TestColors.RESET}")
    
    # Run test suites
    test_results = []
    
    test_results.append(("Mock Server Endpoints", test_mock_server_endpoints()))
    test_results.append(("Goal 1 Execution", test_goal1_execution()))
    test_results.append(("Goal 4 Execution", test_goal4_execution()))
    test_results.append(("Data Validation", test_data_validation()))
    
    # Summary
    print(f"\n{TestColors.BLUE}{'=' * 80}{TestColors.RESET}")
    print(f"{TestColors.BOLD}Test Summary:{TestColors.RESET}")
    print(f"{TestColors.BLUE}{'=' * 80}{TestColors.RESET}")
    
    total_passed = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = f"{TestColors.GREEN}PASSED{TestColors.RESET}" if passed else f"{TestColors.RED}FAILED{TestColors.RESET}"
        print(f"{test_name}: {status}")
    
    print(f"\n{TestColors.BOLD}Overall: {total_passed}/{total_tests} test suites passed{TestColors.RESET}")
    
    if total_passed == total_tests:
        print(f"\n{TestColors.GREEN}{TestColors.BOLD}🎉 All tests passed!{TestColors.RESET}")
        return True
    else:
        print(f"\n{TestColors.RED}{TestColors.BOLD}❌ Some tests failed{TestColors.RESET}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)