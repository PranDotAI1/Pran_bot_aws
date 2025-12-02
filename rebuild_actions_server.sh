#!/bin/bash
# Script to rebuild and redeploy the Rasa Actions Server with fixes
# Uses Docker Desktop path

set -e

# Find Docker
DOCKER_CMD=""
if [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
    DOCKER_CMD="/Applications/Docker.app/Contents/Resources/bin/docker"
elif command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
else
    echo "❌ Error: Docker not found"
    exit 1
fi

echo "======================================================================"
echo "REBUILD AND REDEPLOY RASA ACTIONS SERVER"
echo "======================================================================"

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-941377143251}
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_NAME="pran-chatbot-rasa-actions"
IMAGE_TAG="latest"
FULL_IMAGE="${ECR_BASE}/${IMAGE_NAME}:${IMAGE_TAG}"

CLUSTER="pran-chatbot-cluster"
SERVICE="pran-chatbot-service"

echo ""
echo "📦 Configuration:"
echo "   Docker: $DOCKER_CMD"
echo "   AWS Account: $AWS_ACCOUNT_ID"
echo "   Region: $AWS_REGION"
echo "   Image: $FULL_IMAGE"
echo "   Cluster: $CLUSTER"
echo "   Service: $SERVICE"
echo ""

# Check AWS CLI
AWS_CMD=""
if command -v aws &> /dev/null; then
    AWS_CMD="aws"
elif [ -f "/usr/local/bin/aws" ]; then
    AWS_CMD="/usr/local/bin/aws"
else
    echo "❌ Error: AWS CLI is not installed or not in PATH"
    echo "   Please install AWS CLI or add it to PATH"
    exit 1
fi

# Step 1: Login to ECR
echo "======================================================================"
echo "Step 1: Logging in to ECR..."
echo "======================================================================"
$AWS_CMD ecr get-login-password --region $AWS_REGION | \
    $DOCKER_CMD login --username AWS --password-stdin $ECR_BASE

if [ $? -eq 0 ]; then
    echo "✅ Successfully logged in to ECR"
else
    echo "❌ Failed to login to ECR"
    exit 1
fi

echo ""

# Step 2: Build the image
echo "======================================================================"
echo "Step 2: Building Actions Server Docker image..."
echo "======================================================================"
echo "Dockerfile: ./backend/app/Dockerfile.actions"
echo "Context: ./backend/app"
echo "Platform: linux/amd64"
echo ""

$DOCKER_CMD build --platform linux/amd64 \
    --tag $FULL_IMAGE \
    --file ./backend/app/Dockerfile.actions \
    ./backend/app

if [ $? -eq 0 ]; then
    echo "✅ Successfully built image"
else
    echo "❌ Failed to build image"
    exit 1
fi

echo ""

# Step 3: Push to ECR
echo "======================================================================"
echo "Step 3: Pushing image to ECR..."
echo "======================================================================"
$DOCKER_CMD push $FULL_IMAGE

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed image to ECR"
else
    echo "❌ Failed to push image"
    exit 1
fi

echo ""

# Step 4: Force new deployment
echo "======================================================================"
echo "Step 4: Forcing new ECS deployment..."
echo "======================================================================"
$AWS_CMD ecs update-service \
    --cluster $CLUSTER \
    --service $SERVICE \
    --force-new-deployment \
    --region $AWS_REGION \
    --query 'service.{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount}' \
    --output table

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully triggered new deployment"
    echo ""
    echo "⏳ Waiting for deployment to stabilize..."
    echo "   This may take 2-5 minutes"
    echo ""
    
    # Wait for service to stabilize
    $AWS_CMD ecs wait services-stable \
        --cluster $CLUSTER \
        --services $SERVICE \
        --region $AWS_REGION
    
    if [ $? -eq 0 ]; then
        echo "✅ Deployment completed successfully!"
    else
        echo "⚠️  Deployment is in progress. Check ECS console for status."
    fi
else
    echo "❌ Failed to trigger deployment"
    exit 1
fi

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for containers to start"
echo "2. Run test script: ./test_actions_fix.sh"
echo "3. Check logs: $AWS_CMD logs tail /ecs/pran-chatbot-actions --follow"
echo ""
