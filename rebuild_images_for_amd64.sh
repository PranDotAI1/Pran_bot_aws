#!/bin/bash
###############################################################################
# Rebuild Container Images for linux/amd64 Platform
# Run this script when Docker is available
###############################################################################

set -e

AWS_ACCOUNT_ID="941377143251"
AWS_REGION="us-east-1"
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "======================================================================"
echo "Rebuilding Container Images for linux/amd64"
echo "======================================================================"
echo ""

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_BASE
echo "✅ Logged in to ECR"
echo ""

# Function to build and push
build_and_push() {
    local name=$1
    local dockerfile=$2
    local context=$3
    local image="${ECR_BASE}/${name}:latest"
    
    echo "======================================================================"
    echo "Building: $name"
    echo "======================================================================"
    echo "Dockerfile: $dockerfile"
    echo "Context: $context"
    echo "Image: $image"
    echo ""
    
    if [ ! -f "$dockerfile" ]; then
        echo "⚠️  Dockerfile not found: $dockerfile"
        echo "   Skipping $name"
        return 1
    fi
    
    # Build with platform flag
    echo "Building for linux/amd64..."
    docker build \
        --platform linux/amd64 \
        --tag "$image" \
        --file "$dockerfile" \
        "$context"
    
    # Push to ECR
    echo "Pushing to ECR..."
    docker push "$image"
    
    echo "✅ Successfully built and pushed $name"
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

# 3. Frontend - check multiple locations
if [ -f "./AWS-Pran/frontend/Dockerfile" ]; then
    build_and_push "pran-chatbot-frontend" \
        "./AWS-Pran/frontend/Dockerfile" \
        "./AWS-Pran/frontend"
elif [ -f "./frontend/Dockerfile" ]; then
    build_and_push "pran-chatbot-frontend" \
        "./frontend/Dockerfile" \
        "./frontend"
else
    echo "⚠️  Frontend Dockerfile not found. Creating simple one..."
    # Create a simple frontend Dockerfile if needed
    cat > /tmp/frontend.Dockerfile << 'DOCKERFILE'
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
DOCKERFILE
    
    if [ -d "./AWS-Pran/frontend" ]; then
        build_and_push "pran-chatbot-frontend" \
            "/tmp/frontend.Dockerfile" \
            "./AWS-Pran/frontend"
    elif [ -d "./frontend" ]; then
        build_and_push "pran-chatbot-frontend" \
            "/tmp/frontend.Dockerfile" \
            "./frontend"
    fi
fi

# 4. Django API
if [ -f "./AWS-Pran/api/django-api/Dockerfile" ]; then
    build_and_push "pran-chatbot-django-api" \
        "./AWS-Pran/api/django-api/Dockerfile" \
        "./AWS-Pran/api/django-api"
elif [ -d "./AWS-Pran/api/django-api" ]; then
    echo "⚠️  Django API Dockerfile not found. Creating one..."
    cat > /tmp/django.Dockerfile << 'DOCKERFILE'
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install django djangorestframework
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
DOCKERFILE
    build_and_push "pran-chatbot-django-api" \
        "/tmp/django.Dockerfile" \
        "./AWS-Pran/api/django-api"
fi

# 5. Node API
if [ -f "./AWS-Pran/api/node-api/Dockerfile" ]; then
    build_and_push "pran-chatbot-node-api" \
        "./AWS-Pran/api/node-api/Dockerfile" \
        "./AWS-Pran/api/node-api"
elif [ -d "./AWS-Pran/api/node-api" ]; then
    echo "⚠️  Node API Dockerfile not found. Creating one..."
    cat > /tmp/node.Dockerfile << 'DOCKERFILE'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "server.js"] || ["npm", "start"]
DOCKERFILE
    build_and_push "pran-chatbot-node-api" \
        "/tmp/node.Dockerfile" \
        "./AWS-Pran/api/node-api"
fi

echo "======================================================================"
echo "✅ Build Process Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Force new deployment:"
echo "   aws ecs update-service \\"
echo "     --cluster pran-chatbot-cluster \\"
echo "     --service pran-chatbot-service \\"
echo "     --force-new-deployment \\"
echo "     --region us-east-1"
echo ""
echo "2. Monitor deployment:"
echo "   aws ecs describe-services \\"
echo "     --cluster pran-chatbot-cluster \\"
echo "     --services pran-chatbot-service \\"
echo "     --region us-east-1"
echo ""

