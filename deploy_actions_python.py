#!/usr/bin/env python3
"""
Deploy Actions Server using Python (boto3 + Docker)
This script rebuilds and redeploys the Rasa Actions Server with fixes
"""

import subprocess
import sys
import os
import boto3
import time

# Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID', '941377143251')
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com"
IMAGE_NAME = "pran-chatbot-rasa-actions"
IMAGE_TAG = "latest"
FULL_IMAGE = f"{ECR_BASE}/{IMAGE_NAME}:{IMAGE_TAG}"

CLUSTER = "pran-chatbot-cluster"
SERVICE = "pran-chatbot-service"

# Find Docker
DOCKER_CMD = None
if os.path.exists("/Applications/Docker.app/Contents/Resources/bin/docker"):
    DOCKER_CMD = "/Applications/Docker.app/Contents/Resources/bin/docker"
elif subprocess.run(["which", "docker"], capture_output=True).returncode == 0:
    DOCKER_CMD = "docker"
else:
    print("❌ Error: Docker not found")
    sys.exit(1)

print("=" * 70)
print("REBUILD AND REDEPLOY RASA ACTIONS SERVER")
print("=" * 70)
print()
print("📦 Configuration:")
print(f"   Docker: {DOCKER_CMD}")
print(f"   AWS Account: {AWS_ACCOUNT_ID}")
print(f"   Region: {AWS_REGION}")
print(f"   Image: {FULL_IMAGE}")
print(f"   Cluster: {CLUSTER}")
print(f"   Service: {SERVICE}")
print()

def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(1)
    return result.returncode == 0

# Step 1: Login to ECR
print("=" * 70)
print("Step 1: Logging in to ECR...")
print("=" * 70)

ecr = boto3.client('ecr', region_name=AWS_REGION)
try:
    token_response = ecr.get_authorization_token()
    token = token_response['authorizationData'][0]['authorizationToken']
    endpoint = token_response['authorizationData'][0]['proxyEndpoint']
    
    # Decode token (base64 encoded username:password)
    import base64
    decoded = base64.b64decode(token).decode('utf-8')
    username, password = decoded.split(':')
    
    # Login to Docker
    login_cmd = [
        DOCKER_CMD, "login",
        "--username", username,
        "--password-stdin",
        endpoint
    ]
    
    result = subprocess.run(
        login_cmd,
        input=password,
        text=True,
        capture_output=True
    )
    
    if result.returncode == 0:
        print("✅ Successfully logged in to ECR")
    else:
        print(f"❌ Failed to login to ECR: {result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error logging in to ECR: {e}")
    sys.exit(1)

print()

# Step 2: Build the image
print("=" * 70)
print("Step 2: Building Actions Server Docker image...")
print("=" * 70)
print("Dockerfile: ./backend/app/Dockerfile.actions")
print("Context: ./backend/app")
print("Platform: linux/amd64")
print()

build_cmd = [
    DOCKER_CMD, "build",
    "--platform", "linux/amd64",
    "--tag", FULL_IMAGE,
    "--file", "./backend/app/Dockerfile.actions",
    "./backend/app"
]

if not run_command(build_cmd):
    print("❌ Failed to build image")
    sys.exit(1)

print("✅ Successfully built image")
print()

# Step 3: Push to ECR
print("=" * 70)
print("Step 3: Pushing image to ECR...")
print("=" * 70)

push_cmd = [DOCKER_CMD, "push", FULL_IMAGE]

if not run_command(push_cmd):
    print("❌ Failed to push image")
    sys.exit(1)

print("✅ Successfully pushed image to ECR")
print()

# Step 4: Force new deployment
print("=" * 70)
print("Step 4: Forcing new ECS deployment...")
print("=" * 70)

ecs = boto3.client('ecs', region_name=AWS_REGION)

try:
    response = ecs.update_service(
        cluster=CLUSTER,
        service=SERVICE,
        forceNewDeployment=True
    )
    
    service = response['service']
    print("✅ Successfully triggered new deployment")
    print()
    print(f"   Service: {service['serviceName']}")
    print(f"   Status: {service['status']}")
    print(f"   Desired Count: {service['desiredCount']}")
    print(f"   Running Count: {service['runningCount']}")
    print()
    print("⏳ Waiting for deployment to stabilize...")
    print("   This may take 2-5 minutes")
    print()
    
    # Wait for service to stabilize (with timeout)
    waiter = ecs.get_waiter('services_stable')
    try:
        waiter.wait(
            cluster=CLUSTER,
            services=[SERVICE],
            WaiterConfig={'MaxAttempts': 60, 'Delay': 10}
        )
        print("✅ Deployment completed successfully!")
    except Exception as e:
        print(f"⚠️  Deployment is in progress. Check ECS console for status.")
        print(f"   Error: {e}")
    
except Exception as e:
    print(f"❌ Failed to trigger deployment: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("✅ DEPLOYMENT COMPLETE")
print("=" * 70)
print()
print("Next steps:")
print("1. Wait 2-3 minutes for containers to start")
print("2. Run test script: ./test_actions_fix.sh")
print("3. Check logs: aws logs tail /ecs/pran-chatbot-actions --follow")
print()

