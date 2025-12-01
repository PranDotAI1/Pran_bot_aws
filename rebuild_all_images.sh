#!/bin/bash
###############################################################################
# Rebuild All Container Images for linux/amd64 Platform
# This fixes the platform mismatch issue
###############################################################################

set -e

AWS_ACCOUNT_ID="941377143251"
AWS_REGION="us-east-1"
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=" * 70
echo "Rebuilding All Container Images for linux/amd64"
echo "=" * 70
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker buildx not found. Installing...${NC}"
    docker buildx install || echo "Note: buildx may need manual installation"
fi

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_BASE || {
    echo -e "${RED}❌ Failed to login to ECR${NC}"
    exit 1
}
echo -e "${GREEN}✅ Logged in to ECR${NC}"
echo ""

# Function to build and push image
build_and_push() {
    local container_name=$1
    local dockerfile_path=$2
    local build_context=$3
    local ecr_image="${ECR_BASE}/${container_name}:latest"
    
    echo "=" * 70
    echo "Building: $container_name"
    echo "=" * 70
    echo "Dockerfile: $dockerfile_path"
    echo "Context: $build_context"
    echo "ECR Image: $ecr_image"
    echo ""
    
    if [ ! -f "$dockerfile_path" ]; then
        echo -e "${YELLOW}⚠️  Dockerfile not found: $dockerfile_path${NC}"
        echo "   Skipping $container_name"
        return 1
    fi
    
    # Build with platform flag
    echo "Building image for linux/amd64..."
    docker buildx build \
        --platform linux/amd64 \
        --tag $ecr_image \
        --file "$dockerfile_path" \
        --push \
        "$build_context" || {
        echo -e "${YELLOW}⚠️  Buildx failed, trying regular build...${NC}"
        # Fallback to regular build
        docker build \
            --platform linux/amd64 \
            --tag $ecr_image \
            --file "$dockerfile_path" \
            "$build_context" || {
            echo -e "${RED}❌ Failed to build $container_name${NC}"
            return 1
        }
        docker push $ecr_image || {
            echo -e "${RED}❌ Failed to push $container_name${NC}"
            return 1
        }
    }
    
    echo -e "${GREEN}✅ Successfully built and pushed $container_name${NC}"
    echo ""
}

# Build each container
echo "Starting builds..."
echo ""

# 1. Flask Wrapper
build_and_push "pran-chatbot-flask-wrapper" \
    "./Dockerfile.backend" \
    "./backend"

# 2. Rasa Backend
build_and_push "pran-chatbot-rasa-backend" \
    "./backend/app/Dockerfile" \
    "./backend/app"

# 3. Frontend (check if Dockerfile exists)
if [ -f "./frontend/Dockerfile" ]; then
    build_and_push "pran-chatbot-frontend" \
        "./frontend/Dockerfile" \
        "./frontend"
elif [ -f "./AWS-Pran/frontend/Dockerfile" ]; then
    build_and_push "pran-chatbot-frontend" \
        "./AWS-Pran/frontend/Dockerfile" \
        "./AWS-Pran/frontend"
else
    echo -e "${YELLOW}⚠️  Frontend Dockerfile not found. Skipping frontend.${NC}"
fi

# 4. Django API
if [ -f "./AWS-Pran/api/django-api/Dockerfile" ]; then
    build_and_push "pran-chatbot-django-api" \
        "./AWS-Pran/api/django-api/Dockerfile" \
        "./AWS-Pran/api/django-api"
elif [ -f "./api_backend/Dockerfile" ]; then
    build_and_push "pran-chatbot-django-api" \
        "./api_backend/Dockerfile" \
        "./api_backend"
else
    echo -e "${YELLOW}⚠️  Django API Dockerfile not found. Skipping django-api.${NC}"
fi

# 5. Node API
if [ -f "./AWS-Pran/api/node-api/Dockerfile" ]; then
    build_and_push "pran-chatbot-node-api" \
        "./AWS-Pran/api/node-api/Dockerfile" \
        "./AWS-Pran/api/node-api"
elif [ -f "./dummy_api/Dockerfile" ]; then
    build_and_push "pran-chatbot-node-api" \
        "./dummy_api/Dockerfile" \
        "./dummy_api"
else
    echo -e "${YELLOW}⚠️  Node API Dockerfile not found. Skipping node-api.${NC}"
fi

echo "=" * 70
echo -e "${GREEN}✅ Build Process Complete!${NC}"
echo "=" * 70
echo ""
echo "Next steps:"
echo "1. Force new deployment:"
echo "   aws ecs update-service --cluster pran-chatbot-cluster --service pran-chatbot-service --force-new-deployment --region us-east-1"
echo ""
echo "2. Monitor deployment:"
echo "   aws ecs describe-services --cluster pran-chatbot-cluster --services pran-chatbot-service --region us-east-1"
echo ""

