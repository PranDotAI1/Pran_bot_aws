#!/bin/bash

# Rebuild and Deploy Rasa Server with New Model
# This script rebuilds the Rasa container with the updated config and model

set -e

echo "========================================================================"
echo "REBUILDING RASA SERVER WITH UPDATED CONFIG"
echo "========================================================================"
echo ""

# Configuration
export AWS_REGION="us-east-1"
export ECR_REGISTRY="941377143251.dkr.ecr.us-east-1.amazonaws.com"
export RASA_IMAGE="${ECR_REGISTRY}/pran-chatbot-rasa:latest"
export ECS_CLUSTER="pran-chatbot-cluster"
export ECS_SERVICE="pran-chatbot-service"
export DOCKER_PATH="/Applications/Docker.app/Contents/Resources/bin/docker"

echo "Configuration:"
echo "   Region: $AWS_REGION"
echo "   Rasa Image: $RASA_IMAGE"
echo "   Cluster: $ECS_CLUSTER"
echo "   Service: $ECS_SERVICE"
echo ""

# Step 1: Login to ECR
echo "========================================================================"
echo "Step 1: Logging in to ECR..."
echo "========================================================================"
aws ecr get-login-password --region $AWS_REGION | $DOCKER_PATH login --username AWS --password-stdin $ECR_REGISTRY
if [ $? -eq 0 ]; then
    echo "✅ Successfully logged in to ECR"
else
    echo "❌ Failed to login to ECR"
    exit 1
fi
echo ""

# Step 2: Build Rasa Docker image
echo "========================================================================"
echo "Step 2: Building Rasa Docker image..."
echo "========================================================================"
echo "Dockerfile: ./backend/app/Dockerfile"
echo "Context: ./backend/app"
echo "Platform: linux/amd64"
echo ""

$DOCKER_PATH build \
    --platform linux/amd64 \
    --tag $RASA_IMAGE \
    --file ./backend/app/Dockerfile \
    ./backend/app

if [ $? -eq 0 ]; then
    echo "✅ Successfully built image"
else
    echo "❌ Failed to build image"
    exit 1
fi
echo ""

# Step 3: Push image to ECR
echo "========================================================================"
echo "Step 3: Pushing image to ECR..."
echo "========================================================================"
$DOCKER_PATH push $RASA_IMAGE

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed image to ECR"
else
    echo "❌ Failed to push image to ECR"
    exit 1
fi
echo ""

# Step 4: Force new ECS deployment
echo "========================================================================"
echo "Step 4: Forcing new ECS deployment..."
echo "========================================================================"
aws ecs update-service \
    --cluster $ECS_CLUSTER \
    --service $ECS_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Successfully triggered new deployment"
else
    echo "❌ Failed to trigger deployment"
    exit 1
fi

# Wait for deployment
echo ""
echo "⏳ Waiting for deployment to stabilize..."
echo "   This may take 5-10 minutes"
echo ""

aws ecs wait services-stable \
    --cluster $ECS_CLUSTER \
    --services $ECS_SERVICE \
    --region $AWS_REGION

if [ $? -eq 0 ]; then
    echo "✅ Deployment completed successfully!"
else
    echo "⚠️  Deployment may still be in progress. Check ECS console."
fi

echo ""
echo "========================================================================"
echo "✅ RASA SERVER REBUILD COMPLETE"
echo "========================================================================"
echo ""
echo "The Rasa server has been rebuilt with:"
echo "  - affirm intent for 'yes' responses"
echo "  - FallbackClassifier to prevent multiple intent matches"
echo "  - Updated rules for proper handling"
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for containers to fully start"
echo "2. Test with: curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \\"
echo "      -H \"Content-Type: application/json\" \\"
echo "      -d '{\"sender\": \"test_user\", \"message\": \"yes\"}'"
echo ""

