#!/usr/bin/env python3
"""
Rebuild and Deploy Rasa Server with Updated Config
"""
import boto3
import subprocess
import time
import sys

# Configuration
AWS_REGION = "us-east-1"
ECR_REGISTRY = "941377143251.dkr.ecr.us-east-1.amazonaws.com"
RASA_IMAGE = f"{ECR_REGISTRY}/pran-chatbot-rasa-backend:latest"
ECS_CLUSTER = "pran-chatbot-cluster"
ECS_SERVICE = "pran-chatbot-service"
DOCKER_PATH = "/Applications/Docker.app/Contents/Resources/bin/docker"

print("=" * 70)
print("REBUILDING RASA SERVER WITH UPDATED CONFIG")
print("=" * 70)
print("")
print(f"Configuration:")
print(f"   Region: {AWS_REGION}")
print(f"   Rasa Image: {RASA_IMAGE}")
print(f"   Cluster: {ECS_CLUSTER}")
print(f"   Service: {ECS_SERVICE}")
print("")

# Initialize AWS clients
ecr = boto3.client('ecr', region_name=AWS_REGION)
ecs = boto3.client('ecs', region_name=AWS_REGION)

# Step 1: Login to ECR
print("=" * 70)
print("Step 1: Logging in to ECR...")
print("=" * 70)
try:
    response = ecr.get_authorization_token()
    auth_data = response['authorizationData'][0]
    token = auth_data['authorizationToken']
    endpoint = auth_data['proxyEndpoint']
    
    # Decode token and login
    import base64
    username, password = base64.b64decode(token).decode('utf-8').split(':')
    
    login_cmd = [DOCKER_PATH, 'login', '--username', username, '--password-stdin', endpoint]
    password_input = password if isinstance(password, bytes) else password.encode()
    result = subprocess.run(login_cmd, input=password_input, capture_output=True)
    
    if result.returncode == 0:
        print("✅ Successfully logged in to ECR")
    else:
        print(f"❌ Failed to login to ECR: {result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error during ECR login: {e}")
    sys.exit(1)

print("")

# Step 2: Build Rasa Docker image
print("=" * 70)
print("Step 2: Building Rasa Docker image...")
print("=" * 70)
print(f"Dockerfile: ./backend/app/Dockerfile")
print(f"Context: ./backend/app")
print(f"Platform: linux/amd64")
print("")

try:
    build_cmd = [
        DOCKER_PATH, 'build',
        '--platform', 'linux/amd64',
        '--tag', RASA_IMAGE,
        '--file', './backend/app/Dockerfile',
        './backend/app'
    ]
    
    result = subprocess.run(build_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Successfully built image")
    else:
        print(f"❌ Failed to build image: {result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error during image build: {e}")
    sys.exit(1)

print("")

# Step 3: Push image to ECR
print("=" * 70)
print("Step 3: Pushing image to ECR...")
print("=" * 70)

try:
    push_cmd = [DOCKER_PATH, 'push', RASA_IMAGE]
    result = subprocess.run(push_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Successfully pushed image to ECR")
    else:
        print(f"❌ Failed to push image to ECR: {result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error during image push: {e}")
    sys.exit(1)

print("")

# Step 4: Force new ECS deployment
print("=" * 70)
print("Step 4: Forcing new ECS deployment...")
print("=" * 70)

try:
    response = ecs.update_service(
        cluster=ECS_CLUSTER,
        service=ECS_SERVICE,
        forceNewDeployment=True
    )
    
    print("✅ Successfully triggered new deployment")
    print(f"   Service: {response['service']['serviceName']}")
    print(f"   Status: {response['service']['status']}")
    print(f"   Desired Count: {response['service']['desiredCount']}")
    print(f"   Running Count: {response['service']['runningCount']}")
except Exception as e:
    print(f"❌ Error triggering deployment: {e}")
    sys.exit(1)

print("")
print("⏳ Waiting for deployment to stabilize...")
print("   This may take 5-10 minutes")

try:
    waiter = ecs.get_waiter('services_stable')
    waiter.wait(
        cluster=ECS_CLUSTER,
        services=[ECS_SERVICE],
        WaiterConfig={
            'Delay': 15,
            'MaxAttempts': 40
        }
    )
    print("✅ Deployment completed successfully!")
except Exception as e:
    print(f"⚠️  Deployment may still be in progress: {e}")
    print("   Check ECS console for status")

print("")
print("=" * 70)
print("✅ RASA SERVER REBUILD COMPLETE")
print("=" * 70)
print("")
print("The Rasa server has been rebuilt with:")
print("  - affirm intent for 'yes' responses")
print("  - FallbackClassifier to prevent multiple intent matches")
print("  - Updated rules for proper handling")
print("")
print("Next steps:")
print("1. Wait 2-3 minutes for containers to fully start")
print("2. Test with:")
print("   curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \\")
print("     -H \"Content-Type: application/json\" \\")
print("     -d '{\"sender\": \"test_user\", \"message\": \"yes\"}'")
print("")
