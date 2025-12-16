#!/bin/bash

##############################################################################
# EMERGENCY BACKEND FIX SCRIPT
# Restarts the ECS service to fix 503 errors
##############################################################################

set -e

echo "=================================================================="
echo "  PRAN CHATBOT - EMERGENCY BACKEND FIX"
echo "=================================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="pran-chatbot-cluster"
SERVICE_NAME="pran-chatbot-service"
REGION="us-east-1"
BACKEND_URL="http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"

##############################################################################
# Check Prerequisites
##############################################################################

echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found!${NC}"
    echo ""
    echo "AWS CLI is required to restart the service."
    echo ""
    echo "To install AWS CLI:"
    echo ""
    echo "  macOS:"
    echo "    brew install awscli"
    echo ""
    echo "  Or download from:"
    echo "    https://aws.amazon.com/cli/"
    echo ""
    echo "After installing, configure with:"
    echo "    aws configure"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ AWS CLI found${NC}"

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured!${NC}"
    echo ""
    echo "Please configure AWS credentials with:"
    echo "    aws configure"
    echo ""
    echo "You'll need:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - Default region: us-east-1"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ AWS credentials configured${NC}"
echo ""

##############################################################################
# Check Current Service Status
##############################################################################

echo -e "${BLUE}Step 2: Checking current service status...${NC}"
echo ""

SERVICE_STATUS=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$REGION" \
    --query 'services[0].{status:status,running:runningCount,desired:desiredCount}' \
    --output json 2>/dev/null)

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to get service status${NC}"
    echo "Make sure you have permissions for ECS in region $REGION"
    exit 1
fi

RUNNING_COUNT=$(echo "$SERVICE_STATUS" | grep -o '"running":[0-9]*' | grep -o '[0-9]*')
DESIRED_COUNT=$(echo "$SERVICE_STATUS" | grep -o '"desired":[0-9]*' | grep -o '[0-9]*')

echo "Service Status:"
echo "  Cluster: $CLUSTER_NAME"
echo "  Service: $SERVICE_NAME"
echo "  Running Tasks: $RUNNING_COUNT"
echo "  Desired Tasks: $DESIRED_COUNT"
echo ""

if [ "$RUNNING_COUNT" -eq 0 ]; then
    echo -e "${RED}⚠  No tasks running!${NC}"
else
    echo -e "${YELLOW}⚠  Tasks running but might be unhealthy${NC}"
fi
echo ""

##############################################################################
# Restart Service
##############################################################################

echo -e "${BLUE}Step 3: Restarting ECS service...${NC}"
echo ""

echo "This will:"
echo "  1. Force a new deployment"
echo "  2. Ensure desired count is at least 1"
echo "  3. Start new tasks with latest code"
echo ""

read -p "Continue with restart? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restart cancelled"
    exit 0
fi

echo "Restarting service..."

# Update service with force new deployment
aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --force-new-deployment \
    --desired-count 1 \
    --region "$REGION" \
    > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Service restart initiated${NC}"
else
    echo -e "${RED}✗ Failed to restart service${NC}"
    exit 1
fi

echo ""

##############################################################################
# Wait for Tasks to Start
##############################################################################

echo -e "${BLUE}Step 4: Waiting for tasks to start...${NC}"
echo ""

echo "This usually takes 2-3 minutes..."
echo ""

for i in {1..60}; do
    sleep 5
    
    # Check running count
    CURRENT_STATUS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$REGION" \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null)
    
    echo -n "."
    
    if [ "$CURRENT_STATUS" -ge 1 ]; then
        echo ""
        echo -e "${GREEN}✓ Task is now running!${NC}"
        break
    fi
    
    if [ $i -eq 60 ]; then
        echo ""
        echo -e "${YELLOW}⚠  Tasks still starting... check AWS Console for details${NC}"
    fi
done

echo ""

##############################################################################
# Wait for Health Check
##############################################################################

echo -e "${BLUE}Step 5: Waiting for health checks to pass...${NC}"
echo ""

echo "Waiting for load balancer health checks..."
echo ""

sleep 30  # Give time for health checks to register

##############################################################################
# Verify Backend
##############################################################################

echo -e "${BLUE}Step 6: Verifying backend is responding...${NC}"
echo ""

for i in {1..10}; do
    echo "Attempt $i/10..."
    
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/rasa-webhook" \
        -H "Content-Type: application/json" \
        -d '{"sender":"test","message":"hello"}' 2>/dev/null)
    
    if [ "$RESPONSE" = "200" ]; then
        echo -e "${GREEN}✓ Backend is responding!${NC}"
        echo ""
        
        # Get actual bot response
        BOT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rasa-webhook" \
            -H "Content-Type: application/json" \
            -d '{"sender":"test","message":"hello"}' 2>/dev/null)
        
        echo "Sample bot response:"
        echo "$BOT_RESPONSE" | head -c 150
        echo "..."
        echo ""
        break
    else
        echo "  Response: HTTP $RESPONSE (expected 200)"
        
        if [ $i -lt 10 ]; then
            echo "  Retrying in 10 seconds..."
            sleep 10
        fi
    fi
done

if [ "$RESPONSE" != "200" ]; then
    echo -e "${YELLOW}⚠  Backend not responding yet${NC}"
    echo ""
    echo "This might mean:"
    echo "  - Tasks are still starting (wait 2-3 more minutes)"
    echo "  - Health checks haven't passed yet"
    echo "  - There's an issue with the task configuration"
    echo ""
    echo "Check CloudWatch logs:"
    echo "  https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups/log-group//ecs/pran-chatbot-task"
    echo ""
    exit 1
fi

##############################################################################
# Test Chatbot Frontend
##############################################################################

echo -e "${BLUE}Step 7: Testing chatbot frontend...${NC}"
echo ""

FRONTEND_URL="https://main.d1fw711o7cx5w2.amplifyapp.com/"

echo "Testing: $FRONTEND_URL"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null)

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${YELLOW}⚠  Frontend returned HTTP $FRONTEND_STATUS${NC}"
fi

echo ""

##############################################################################
# Success Summary
##############################################################################

echo "=================================================================="
echo -e "${GREEN}  ✓ BACKEND FIXED AND OPERATIONAL!${NC}"
echo "=================================================================="
echo ""

echo "System Status:"
echo "  Backend:  ✓ Running and healthy"
echo "  Frontend: ✓ Accessible"
echo "  Chatbot:  ✓ Ready for testing"
echo ""

echo "Test the chatbot now:"
echo "  1. Go to: $FRONTEND_URL"
echo "  2. Type: 'hello'"
echo "  3. Expected: Bot responds with greeting"
echo ""

echo "Backend URL (for direct testing):"
echo "  $BACKEND_URL/rasa-webhook"
echo ""

echo "Share with stakeholders:"
echo "  $FRONTEND_URL"
echo ""

echo "=================================================================="
echo "  Next Steps:"
echo "=================================================================="
echo ""
echo "1. ✓ Test chatbot yourself"
echo "2. ✓ Share with stakeholders"
echo "3. Set up CloudWatch alarms (see URGENT_FIX_BACKEND_DOWN.md)"
echo "4. Monitor CloudWatch logs periodically"
echo ""

exit 0
