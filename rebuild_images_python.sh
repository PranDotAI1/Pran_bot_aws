#!/bin/bash
###############################################################################
# Rebuild Container Images for linux/amd64 Platform
# Uses Python/boto3 for ECR login (no AWS CLI required)
###############################################################################

set -e

export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

AWS_ACCOUNT_ID="941377143251"
AWS_REGION="us-east-1"
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "======================================================================"
echo "Rebuilding Container Images for linux/amd64"
echo "======================================================================"
echo ""

# Check Docker
if ! docker --version &> /dev/null; then
    echo "❌ Docker not found. Please ensure Docker Desktop is running."
    exit 1
fi
echo "✅ Docker found: $(docker --version)"

# Login to ECR using Python/boto3
echo ""
echo "Logging in to ECR..."
python3 << PYTHON_SCRIPT
import boto3
import subprocess
import sys

try:
    ecr = boto3.client('ecr', region_name='${AWS_REGION}')
    token = ecr.get_authorization_token()
    auth_data = token['authorizationData'][0]
    auth_token = auth_data['authorizationToken']
    
    # Decode base64 token
    import base64
    decoded = base64.b64decode(auth_token).decode('utf-8')
    username, password = decoded.split(':')
    
    # Login to docker
    login_cmd = [
        'docker', 'login',
        '--username', username,
        '--password-stdin',
        '${ECR_BASE}'
    ]
    
    process = subprocess.Popen(
        login_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate(input=password.encode())
    
    if process.returncode == 0:
        print("✅ Logged in to ECR")
        sys.exit(0)
    else:
        print(f"❌ Failed to login: {stderr.decode()}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ Failed to login to ECR"
    exit 1
fi

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
    
    if [ ! -d "$context" ]; then
        echo "⚠️  Context directory not found: $context"
        echo "   Skipping $name"
        return 1
    fi
    
    # Build with platform flag
    echo "Building for linux/amd64..."
    if ! docker build \
        --platform linux/amd64 \
        --tag "$image" \
        --file "$dockerfile" \
        "$context" 2>&1; then
        echo "❌ Failed to build $name"
        return 1
    fi
    
    # Push to ECR
    echo "Pushing to ECR..."
    if ! docker push "$image" 2>&1; then
        echo "❌ Failed to push $name"
        return 1
    fi
    
    echo "✅ Successfully built and pushed $name"
    echo ""
    return 0
}

# Build each container
echo "Starting builds..."
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

# 1. Flask Wrapper
if build_and_push "pran-chatbot-flask-wrapper" \
    "./Dockerfile.backend" \
    "./backend"; then
    ((SUCCESS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# 2. Rasa Backend
if build_and_push "pran-chatbot-rasa-backend" \
    "./backend/app/Dockerfile" \
    "./backend/app"; then
    ((SUCCESS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# 3. Frontend - check multiple locations
FRONTEND_BUILT=false
if [ -f "./AWS-Pran/frontend/Dockerfile" ]; then
    if build_and_push "pran-chatbot-frontend" \
        "./AWS-Pran/frontend/Dockerfile" \
        "./AWS-Pran/frontend"; then
        ((SUCCESS_COUNT++))
        FRONTEND_BUILT=true
    else
        ((FAIL_COUNT++))
    fi
elif [ -f "./frontend/Dockerfile" ]; then
    if build_and_push "pran-chatbot-frontend" \
        "./frontend/Dockerfile" \
        "./frontend"; then
        ((SUCCESS_COUNT++))
        FRONTEND_BUILT=true
    else
        ((FAIL_COUNT++))
    fi
fi

if [ "$FRONTEND_BUILT" = false ]; then
    echo "⚠️  Frontend Dockerfile not found. Skipping frontend."
    echo "   (This is OK if frontend is not needed)"
    echo ""
fi

# 4. Django API
DJANGO_BUILT=false
if [ -f "./AWS-Pran/api/django-api/Dockerfile" ]; then
    if build_and_push "pran-chatbot-django-api" \
        "./AWS-Pran/api/django-api/Dockerfile" \
        "./AWS-Pran/api/django-api"; then
        ((SUCCESS_COUNT++))
        DJANGO_BUILT=true
    else
        ((FAIL_COUNT++))
    fi
fi

if [ "$DJANGO_BUILT" = false ]; then
    echo "⚠️  Django API Dockerfile not found. Skipping django-api."
    echo "   (This is OK if django-api is not needed)"
    echo ""
fi

# 5. Node API
NODE_BUILT=false
if [ -f "./AWS-Pran/api/node-api/Dockerfile" ]; then
    if build_and_push "pran-chatbot-node-api" \
        "./AWS-Pran/api/node-api/Dockerfile" \
        "./AWS-Pran/api/node-api"; then
        ((SUCCESS_COUNT++))
        NODE_BUILT=true
    else
        ((FAIL_COUNT++))
    fi
fi

if [ "$NODE_BUILT" = false ]; then
    echo "⚠️  Node API Dockerfile not found. Skipping node-api."
    echo "   (This is OK if node-api is not needed)"
    echo ""
fi

echo "======================================================================"
echo "Build Summary"
echo "======================================================================"
echo "✅ Successfully built: $SUCCESS_COUNT"
echo "❌ Failed: $FAIL_COUNT"
echo ""

if [ $SUCCESS_COUNT -gt 0 ]; then
    echo "✅ At least some images were built successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Force new deployment:"
    echo "   python3 << 'EOF'"
    echo "   import boto3"
    echo "   ecs = boto3.client('ecs', region_name='us-east-1')"
    echo "   ecs.update_service("
    echo "       cluster='pran-chatbot-cluster',"
    echo "       service='pran-chatbot-service',"
    echo "       forceNewDeployment=True"
    echo "   )"
    echo "   print('✅ Deployment forced')"
    echo "   EOF"
    echo ""
    echo "2. Monitor deployment:"
    echo "   python3 << 'EOF'"
    echo "   import boto3"
    echo "   ecs = boto3.client('ecs', region_name='us-east-1')"
    echo "   response = ecs.describe_services("
    echo "       cluster='pran-chatbot-cluster',"
    echo "       services=['pran-chatbot-service']"
    echo "   )"
    echo "   service = response['services'][0]"
    echo "   print(f\"Running: {service['runningCount']}/{service['desiredCount']}\")"
    echo "   EOF"
    echo ""
else
    echo "❌ No images were built successfully."
    echo "   Please check the errors above."
fi

echo "======================================================================"

