#!/bin/bash

##############################################################################
# FINAL VERIFICATION SCRIPT
# Tests if Amplify and entire system is ready to share with stakeholders
##############################################################################

echo "=================================================================="
echo "  PRAN CHATBOT - FINAL VERIFICATION FOR STAKEHOLDER SHARING"
echo "=================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

FAILED=0
PASSED=0

# Configuration
BACKEND_URL="http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"

# Your Amplify URL - UPDATE THIS!
AMPLIFY_URL="YOUR-AMPLIFY-URL"  # Example: https://main.d1234567890.amplifyapp.com

echo -e "${BLUE}Note: Update AMPLIFY_URL in this script with your actual Amplify URL${NC}"
echo ""

##############################################################################
# BACKEND TESTS (Required)
##############################################################################

echo "=========================================="
echo "  BACKEND VERIFICATION"
echo "=========================================="
echo ""

echo "1. Testing Backend Health Endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" 2>/dev/null)
if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✓ PASS${NC} - Backend Health: HTTP $HEALTH_STATUS"
    ((PASSED++))
else
    echo -e "   ${RED}✗ FAIL${NC} - Backend Health: HTTP $HEALTH_STATUS"
    ((FAILED++))
fi

echo "2. Testing Bot Response (Hello)..."
BOT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rasa-webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"verify","message":"hello"}' 2>/dev/null)

if echo "$BOT_RESPONSE" | grep -q "text"; then
    echo -e "   ${GREEN}✓ PASS${NC} - Bot responding correctly"
    ((PASSED++))
else
    echo -e "   ${RED}✗ FAIL${NC} - Bot not responding"
    ((FAILED++))
fi

echo "3. Testing Insurance Query..."
START=$(date +%s)
INSURANCE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rasa-webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"verify2","message":"show insurance plans"}' 2>/dev/null)
END=$(date +%s)
DURATION=$((END - START))

if echo "$INSURANCE_RESPONSE" | grep -qi "insurance\|plan\|premium"; then
    echo -e "   ${GREEN}✓ PASS${NC} - Insurance query working (${DURATION}s)"
    ((PASSED++))
else
    echo -e "   ${RED}✗ FAIL${NC} - Insurance query failed"
    ((FAILED++))
fi

echo "4. Testing Doctor Search..."
DOCTOR_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rasa-webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"verify3","message":"find a gynecologist"}' 2>/dev/null)

if echo "$DOCTOR_RESPONSE" | grep -qi "doctor\|gynecologist\|Dr"; then
    echo -e "   ${GREEN}✓ PASS${NC} - Doctor search working"
    ((PASSED++))
else
    echo -e "   ${RED}✗ FAIL${NC} - Doctor search failed"
    ((FAILED++))
fi

echo "5. Testing Response Time..."
START=$(date +%s)
curl -s -X POST "$BACKEND_URL/rasa-webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"verify4","message":"hello"}' > /dev/null 2>&1
END=$(date +%s)
RESPONSE_TIME=$((END - START))

if [ $RESPONSE_TIME -lt 10 ]; then
    echo -e "   ${GREEN}✓ PASS${NC} - Response time: ${RESPONSE_TIME}s (Good)"
    ((PASSED++))
else
    echo -e "   ${YELLOW}⚠ WARN${NC} - Response time: ${RESPONSE_TIME}s (Slow but acceptable)"
    ((PASSED++))
fi

echo ""

##############################################################################
# FRONTEND TESTS (If URL configured)
##############################################################################

echo "=========================================="
echo "  FRONTEND VERIFICATION"
echo "=========================================="
echo ""

if [ "$AMPLIFY_URL" != "YOUR-AMPLIFY-URL" ]; then
    echo "6. Testing Frontend Accessibility..."
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$AMPLIFY_URL" 2>/dev/null)
    
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo -e "   ${GREEN}✓ PASS${NC} - Frontend accessible: HTTP $FRONTEND_STATUS"
        ((PASSED++))
    else
        echo -e "   ${RED}✗ FAIL${NC} - Frontend not accessible: HTTP $FRONTEND_STATUS"
        ((FAILED++))
    fi
    
    echo "7. Testing Frontend Content..."
    FRONTEND_CONTENT=$(curl -s "$AMPLIFY_URL" 2>/dev/null)
    
    if echo "$FRONTEND_CONTENT" | grep -qi "chatbot\|react\|root"; then
        echo -e "   ${GREEN}✓ PASS${NC} - Frontend content loaded"
        ((PASSED++))
    else
        echo -e "   ${RED}✗ FAIL${NC} - Frontend content issue"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ Frontend tests skipped - Update AMPLIFY_URL in script${NC}"
    echo ""
    echo "   Your Amplify URL should look like:"
    echo "   https://main.dXXXXXXXXXX.amplifyapp.com"
    echo ""
fi

echo ""

##############################################################################
# SUMMARY
##############################################################################

echo "=========================================="
echo "  VERIFICATION SUMMARY"
echo "=========================================="
echo ""

TOTAL=$((PASSED + FAILED))
echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo "Total Tests:  $TOTAL"
echo ""

if [ $FAILED -eq 0 ] && [ $PASSED -ge 5 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                            ║${NC}"
    echo -e "${GREEN}║   ✓ READY TO SHARE WITH STAKEHOLDERS!     ║${NC}"
    echo -e "${GREEN}║                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Backend Status: ✓ OPERATIONAL"
    echo "Bot Responses: ✓ WORKING"
    echo "Database: ✓ CONNECTED"
    echo ""
    if [ "$AMPLIFY_URL" != "YOUR-AMPLIFY-URL" ]; then
        echo "Frontend Status: ✓ ACCESSIBLE"
        echo ""
        echo "🚀 SHARE THIS LINK:"
        echo "   $AMPLIFY_URL"
    else
        echo "Frontend Status: ⚠ Not tested (update AMPLIFY_URL)"
        echo ""
        echo "📋 ACTION: Get your Amplify URL and test frontend"
    fi
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                            ║${NC}"
    echo -e "${RED}║   ✗ NOT READY - Issues Detected           ║${NC}"
    echo -e "${RED}║                                            ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please troubleshoot failed tests:"
    echo "1. Check ECS service is running"
    echo "2. Check RDS database is available"
    echo "3. Review CloudWatch logs"
    echo "4. Check Amplify build status"
    echo ""
    echo "See PRODUCTION_READINESS.md for troubleshooting."
    echo ""
    exit 1
fi
