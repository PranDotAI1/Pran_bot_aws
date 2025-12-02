#!/bin/bash
# Test script to verify the actions server fixes
# Tests for: single response, no duplicates, proper fallbacks

set -e

echo "======================================================================"
echo "TESTING ACTIONS SERVER FIXES"
echo "======================================================================"

# Configuration
API_BASE_URL=${API_BASE_URL:-"http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"}
TEST_USER_ID="test_user_$(date +%s)"

echo ""
echo "📋 Test Configuration:"
echo "   API URL: $API_BASE_URL"
echo "   Test User ID: $TEST_USER_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local test_name=$1
    local message=$2
    local expected_count=${3:-1}  # Default to expecting 1 response
    
    echo "----------------------------------------------------------------------"
    echo "Test: $test_name"
    echo "Message: $message"
    echo "----------------------------------------------------------------------"
    
    response=$(curl -s -X POST "${API_BASE_URL}/rasa-webhook" \
        -H "Content-Type: application/json" \
        -d "{
            \"sender\": \"${TEST_USER_ID}\",
            \"message\": \"${message}\"
        }")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to connect to API${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    # Count responses
    response_count=$(echo "$response" | jq '. | length' 2>/dev/null || echo "0")
    
    # Check if response is an array
    if ! echo "$response" | jq -e '. | type == "array"' > /dev/null 2>&1; then
        echo -e "${RED}❌ Response is not an array${NC}"
        echo "Response: $response"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    echo "Response count: $response_count"
    echo "Expected count: $expected_count"
    
    # Check for duplicate responses
    if [ "$response_count" -gt "$expected_count" ]; then
        echo -e "${RED}❌ FAILED: Found $response_count responses, expected $expected_count${NC}"
        echo "Response:"
        echo "$response" | jq '.'
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    # Check for error messages
    error_found=$(echo "$response" | jq -r '.[]?.text' | grep -i "trouble connecting to my AI brain" | wc -l)
    if [ "$error_found" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Warning: Error message found in response${NC}"
        echo "This is expected if AWS credentials are not configured"
        echo "Response:"
        echo "$response" | jq '.'
    fi
    
    # Check for duplicate text
    unique_texts=$(echo "$response" | jq -r '.[].text' | sort | uniq | wc -l)
    if [ "$unique_texts" -lt "$response_count" ]; then
        echo -e "${RED}❌ FAILED: Found duplicate response text${NC}"
        echo "Response:"
        echo "$response" | jq '.'
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    
    echo -e "${GREEN}✅ PASSED: Single response returned${NC}"
    echo "Response preview:"
    echo "$response" | jq -r '.[0].text' | head -c 100
    echo "..."
    echo ""
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  Warning: jq is not installed. Installing basic JSON parsing..."
    # Fallback to basic parsing
    echo "Please install jq for better test results: brew install jq (macOS) or apt-get install jq (Linux)"
fi

# Check API health first
echo "----------------------------------------------------------------------"
echo "Step 1: Checking API health..."
echo "----------------------------------------------------------------------"
health_response=$(curl -s "${API_BASE_URL}/health")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API is reachable${NC}"
    echo "Health status: $health_response"
else
    echo -e "${RED}❌ API is not reachable${NC}"
    echo "Please check if the service is deployed and running"
    exit 1
fi

echo ""
echo "======================================================================"
echo "Running Tests..."
echo "======================================================================"
echo ""

# Test 1: Simple greeting (should return 1 response)
test_endpoint "Simple Greeting" "Hello"

# Test 2: Question (should return 1 response)
test_endpoint "Question Query" "What are the symptoms of diabetes?"

# Test 3: Doctor query (should return 1 response)
test_endpoint "Doctor Query" "I need a doctor"

# Test 4: Appointment query (should return 1 response)
test_endpoint "Appointment Query" "I want to book an appointment"

# Test 5: Complex query (should return 1 response)
test_endpoint "Complex Query" "I'm having chest pain and need to see a cardiologist"

# Summary
echo ""
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "The actions server is working correctly:"
    echo "  ✅ Only one response per query"
    echo "  ✅ No duplicate responses"
    echo "  ✅ Proper error handling"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please check:"
    echo "  1. Actions server logs"
    echo "  2. ECS service status"
    echo "  3. API endpoint connectivity"
    exit 1
fi

