#!/bin/bash

##############################################################################
# PRAN Chatbot Health Check Script
# Run this before sharing with stakeholders or before demos
##############################################################################

echo "=========================================="
echo "  PRAN Chatbot Health Check"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"
AMPLIFY_URL="YOUR-AMPLIFY-URL"  # Update this with your actual Amplify URL

# Counter for failed checks
FAILED=0

##############################################################################
# Check 1: Backend Health Endpoint
##############################################################################
echo "1. Checking Backend Health..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" 2>/dev/null)

if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✓${NC} Backend Health: OK (HTTP $BACKEND_STATUS)"
else
    echo -e "   ${RED}✗${NC} Backend Health: FAILED (HTTP $BACKEND_STATUS)"
    ((FAILED++))
fi

##############################################################################
# Check 2: Backend Rasa Webhook
##############################################################################
echo "2. Checking Rasa Webhook..."
WEBHOOK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/rasa-webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"healthcheck","message":"hello"}' 2>/dev/null)

if [ "$WEBHOOK_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✓${NC} Rasa Webhook: OK (HTTP $WEBHOOK_STATUS)"
else
    echo -e "   ${RED}✗${NC} Rasa Webhook: FAILED (HTTP $WEBHOOK_STATUS)"
    ((FAILED++))
fi

##############################################################################
# Check 3: Test Bot Response
##############################################################################
echo "3. Testing Bot Response..."
BOT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rasa-webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"healthcheck","message":"hello"}' 2>/dev/null)

if [ ! -z "$BOT_RESPONSE" ]; then
    echo -e "   ${GREEN}✓${NC} Bot Response: Received"
    echo "   Sample: $(echo $BOT_RESPONSE | cut -c1-60)..."
else
    echo -e "   ${RED}✗${NC} Bot Response: Empty or failed"
    ((FAILED++))
fi

##############################################################################
# Check 4: Response Time Test
##############################################################################
echo "4. Testing Response Time..."
START_TIME=$(date +%s)
curl -s -X POST "$BACKEND_URL/rasa-webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"healthcheck","message":"show insurance plans"}' > /dev/null 2>&1
END_TIME=$(date +%s)
RESPONSE_TIME=$((END_TIME - START_TIME))

if [ $RESPONSE_TIME -lt 10 ]; then
    echo -e "   ${GREEN}✓${NC} Response Time: ${RESPONSE_TIME}s (Good)"
elif [ $RESPONSE_TIME -lt 20 ]; then
    echo -e "   ${YELLOW}⚠${NC} Response Time: ${RESPONSE_TIME}s (Acceptable)"
else
    echo -e "   ${RED}✗${NC} Response Time: ${RESPONSE_TIME}s (Too Slow)"
    ((FAILED++))
fi

##############################################################################
# Check 5: Frontend (if Amplify URL configured)
##############################################################################
echo "5. Checking Frontend..."
if [ "$AMPLIFY_URL" != "YOUR-AMPLIFY-URL" ]; then
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$AMPLIFY_URL" 2>/dev/null)
    
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo -e "   ${GREEN}✓${NC} Frontend: OK (HTTP $FRONTEND_STATUS)"
    else
        echo -e "   ${RED}✗${NC} Frontend: FAILED (HTTP $FRONTEND_STATUS)"
        ((FAILED++))
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Frontend: Skipped (Configure AMPLIFY_URL in script)"
fi

##############################################################################
# Summary
##############################################################################
echo ""
echo "=========================================="
echo "  Health Check Summary"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    echo ""
    echo "Status: READY FOR STAKEHOLDERS"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $FAILED check(s) failed!${NC}"
    echo ""
    echo "Status: NOT READY - Please investigate issues"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check ECS service is running (AWS Console > ECS)"
    echo "2. Check RDS database is available (AWS Console > RDS)"
    echo "3. Review CloudWatch logs: /ecs/pran-chatbot-task"
    echo "4. Verify Load Balancer targets are healthy"
    echo ""
    exit 1
fi
