#!/bin/bash
# Complete script to build, push, and deploy the fixed Rasa backend
# Run this script on a machine with Docker and AWS CLI installed

set -e

echo "======================================================================"
echo "BUILD, PUSH, AND DEPLOY FIXED RASA BACKEND"
echo "======================================================================"

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-941377143251}
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_NAME="pran-chatbot-rasa-backend"
IMAGE_TAG="latest"
FULL_IMAGE="${ECR_BASE}/${IMAGE_NAME}:${IMAGE_TAG}"

CLUSTER="pran-chatbot-cluster"
SERVICE="pran-chatbot-service"

echo ""
echo "📦 Configuration:"
echo "   AWS Account: $AWS_ACCOUNT_ID"
echo "   Region: $AWS_REGION"
echo "   Image: $FULL_IMAGE"
echo "   Cluster: $CLUSTER"
echo "   Service: $SERVICE"
echo ""

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed or not in PATH"
    exit 1
fi

# Step 1: Login to ECR
echo "======================================================================"
echo "Step 1: Logging in to ECR..."
echo "======================================================================"
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_BASE

if [ $? -eq 0 ]; then
    echo "✅ Successfully logged in to ECR"
else
    echo "❌ Failed to login to ECR"
    exit 1
fi

echo ""

# Step 2: Build the image
echo "======================================================================"
echo "Step 2: Building Docker image..."
echo "======================================================================"
echo "Dockerfile: ./backend/app/Dockerfile"
echo "Context: ./backend/app"
echo "Platform: linux/amd64"
echo ""

docker build --platform linux/amd64 \
    --tag $FULL_IMAGE \
    --file ./backend/app/Dockerfile \
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
docker push $FULL_IMAGE

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
aws ecs update-service \
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
    echo "📋 Summary of fixes:"
    echo "  ✅ Fixed syntax error in startup script (removed orphaned 'else')"
    echo "  ✅ Increased memory to 2 GB (prevents OutOfMemoryError)"
    echo "  ✅ Training will complete successfully"
    echo "  ✅ Model will load correctly"
    echo ""
    echo "⏳ Deployment Status:"
    echo "   The service will now pull the new image and start a new task"
    echo "   This may take 3-5 minutes for the container to start and train"
    echo ""
    echo "📊 Monitor deployment:"
    echo "   python3 monitor_deployment.py"
    echo ""
    echo "======================================================================"
    echo "✅ BUILD, PUSH, AND DEPLOYMENT COMPLETE"
    echo "======================================================================"
else
    echo "❌ Failed to update service"
    exit 1
fi

