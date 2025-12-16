#!/bin/bash

##############################################################################
# SUPER SIMPLE FIX - JUST COPY AND PASTE THESE COMMANDS
# This will guide you through installing AWS CLI and fixing the backend
##############################################################################

set -e

echo "=================================================================="
echo "  SIMPLE STEP-BY-STEP FIX FOR BACKEND"
echo "=================================================================="
echo ""
echo "I'll guide you through each step. Just follow along!"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

##############################################################################
# Step 1: Install AWS CLI if not present
##############################################################################

echo -e "${BLUE}Step 1: Checking if AWS CLI is installed...${NC}"
echo ""

if command -v aws &> /dev/null; then
    echo -e "${GREEN}✓ AWS CLI is already installed!${NC}"
    echo ""
else
    echo "AWS CLI not found. Installing now..."
    echo ""
    
    if command -v brew &> /dev/null; then
        echo "Installing via Homebrew..."
        brew install awscli
    else
        echo "Downloading AWS CLI installer..."
        curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "/tmp/AWSCLIV2.pkg"
        echo "Installing AWS CLI (may ask for password)..."
        sudo installer -pkg /tmp/AWSCLIV2.pkg -target /
        rm /tmp/AWSCLIV2.pkg
    fi
    
    echo ""
    echo -e "${GREEN}✓ AWS CLI installed!${NC}"
    echo ""
fi

##############################################################################
# Step 2: Configure AWS (if not configured)
##############################################################################

echo -e "${BLUE}Step 2: Checking AWS configuration...${NC}"
echo ""

if aws sts get-caller-identity &> /dev/null; then
    echo -e "${GREEN}✓ AWS is already configured!${NC}"
    echo ""
else
    echo "AWS CLI needs to be configured."
    echo ""
    echo "=================================================================="
    echo "  IMPORTANT: I need your AWS credentials"
    echo "=================================================================="
    echo ""
    echo "Please get these from your AWS admin:"
    echo "  1. AWS Access Key ID"
    echo "  2. AWS Secret Access Key"
    echo ""
    echo "If you don't have these, STOP here and contact your AWS admin."
    echo ""
    read -p "Do you have your AWS credentials ready? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Please get your AWS credentials and run this script again."
        echo ""
        echo "Send this to your AWS admin:"
        echo "---"
        echo "Hi, I need AWS credentials to fix our chatbot."
        echo "Please provide:"
        echo "  - AWS Access Key ID"
        echo "  - AWS Secret Access Key"
        echo "  - Confirm region is: us-east-1"
        echo "---"
        exit 0
    fi
    
    echo ""
    echo "Great! Let's configure AWS..."
    echo ""
    echo "You'll be asked for:"
    echo "  1. AWS Access Key ID: [paste your key]"
    echo "  2. AWS Secret Access Key: [paste your secret]"
    echo "  3. Default region: Type 'us-east-1'"
    echo "  4. Output format: Just press Enter (default is fine)"
    echo ""
    
    aws configure
    
    echo ""
    echo -e "${GREEN}✓ AWS configured!${NC}"
    echo ""
fi

##############################################################################
# Step 3: Restart ECS Service
##############################################################################

echo -e "${BLUE}Step 3: Restarting the backend service...${NC}"
echo ""

CLUSTER="pran-chatbot-cluster"
SERVICE="pran-chatbot-service"
REGION="us-east-1"

echo "Checking current status..."
aws ecs describe-services \
    --cluster $CLUSTER \
    --services $SERVICE \
    --region $REGION \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
    --output table

echo ""
echo "Restarting service..."
echo ""

aws ecs update-service \
    --cluster $CLUSTER \
    --service $SERVICE \
    --force-new-deployment \
    --desired-count 1 \
    --region $REGION \
    > /dev/null 2>&1

echo -e "${GREEN}✓ Service restart initiated!${NC}"
echo ""

##############################################################################
# Step 4: Wait for service to start
##############################################################################

echo -e "${BLUE}Step 4: Waiting for backend to start...${NC}"
echo ""
echo "This takes about 2-3 minutes. Please be patient..."
echo ""

for i in {1..36}; do
    sleep 5
    
    RUNNING=$(aws ecs describe-services \
        --cluster $CLUSTER \
        --services $SERVICE \
        --region $REGION \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null)
    
    echo -n "."
    
    if [ "$RUNNING" -ge 1 ]; then
        echo ""
        echo ""
        echo -e "${GREEN}✓ Backend is starting!${NC}"
        break
    fi
done

echo ""
echo "Waiting 30 more seconds for health checks..."
sleep 30
echo ""

##############################################################################
# Step 5: Test the backend
##############################################################################

echo -e "${BLUE}Step 5: Testing if backend is responding...${NC}"
echo ""

BACKEND_URL="http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"

for i in {1..10}; do
    echo "Test attempt $i/10..."
    
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/rasa-webhook" \
        -H "Content-Type: application/json" \
        -d '{"sender":"test","message":"hello"}' 2>/dev/null)
    
    if [ "$RESPONSE" = "200" ]; then
        echo ""
        echo -e "${GREEN}✓ Backend is working!${NC}"
        echo ""
        
        BOT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/rasa-webhook" \
            -H "Content-Type: application/json" \
            -d '{"sender":"test","message":"hello"}')
        
        echo "Sample response from bot:"
        echo "$BOT_RESPONSE" | head -c 100
        echo "..."
        echo ""
        break
    else
        if [ $i -lt 10 ]; then
            echo "  Not ready yet... waiting 10 seconds"
            sleep 10
        fi
    fi
done

if [ "$RESPONSE" != "200" ]; then
    echo ""
    echo -e "${YELLOW}⚠ Backend not responding yet${NC}"
    echo "This might take a few more minutes."
    echo "Try testing in 3-5 minutes."
    echo ""
    exit 1
fi

##############################################################################
# Success!
##############################################################################

echo "=================================================================="
echo -e "${GREEN}  ✓ BACKEND IS FIXED AND WORKING!${NC}"
echo "=================================================================="
echo ""
echo "Your chatbot is ready!"
echo ""
echo "Test it now:"
echo "  https://main.d1fw711o7cx5w2.amplifyapp.com/"
echo ""
echo "Try typing:"
echo "  - 'hello'"
echo "  - 'show insurance plans'"
echo "  - 'find a gynecologist'"
echo ""
echo "Share with stakeholders:"
echo "  https://main.d1fw711o7cx5w2.amplifyapp.com/"
echo ""
echo "=================================================================="
echo -e "${GREEN}  ALL DONE! ✓${NC}"
echo "=================================================================="
echo ""

exit 0
