#!/usr/bin/env python3
"""
Deploy chatbot fixes to AWS ECS
"""
import subprocess
import sys
import os

AWS_REGION = "us-east-1"
ECR_REPO_PREFIX = "pran-chatbot"
CLUSTER_NAME = "pran-chatbot-cluster"
SERVICE_NAME = "pran-chatbot-service"

def run_cmd(cmd, cwd=None):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"Running: {cmd}")
    print(f"{'='*70}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=False)
    return result.returncode == 0

def main():
    print("="*70)
    print("DEPLOYING CHATBOT FIXES")
    print("="*70)
    print("\nFixes included:")
    print("1. Department specialist filtering - shows only requested department")
    print("2. Booking accepts manual typing of doctor names")
    print("3. Improved context awareness")
    print("4. Step-by-step question flow instead of paragraphs")
    print("5. Numbered lists instead of bullet points")
    print("\n" + "="*70)
    
    # Get AWS account ID
    print("\nGetting AWS account ID...")
    result = subprocess.run(
        "aws sts get-caller-identity --query Account --output text",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("ERROR: Failed to get AWS account ID. Make sure AWS CLI is configured.")
        sys.exit(1)
    
    account_id = result.stdout.strip()
    ecr_base = f"{account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com"
    
    # Login to ECR
    print("\n" + "="*70)
    print("AUTHENTICATING WITH ECR")
    print("="*70)
    if not run_cmd(f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {ecr_base}"):
        print("ERROR: Failed to authenticate with ECR")
        sys.exit(1)
    
    print("\n[OK] ECR authentication successful!")
    
    # Build and push Rasa Actions image
    print("\n" + "="*70)
    print("BUILDING AND PUSHING RASA ACTIONS IMAGE")
    print("="*70)
    
    os.chdir("backend/app")
    
    # Build
    image_name = f"{ecr_base}/{ECR_REPO_PREFIX}-rasa-actions:latest"
    if not run_cmd(f"docker build -f Dockerfile.actions -t {image_name} ."):
        print("ERROR: Failed to build Rasa Actions image")
        sys.exit(1)
    
    # Push
    if not run_cmd(f"docker push {image_name}"):
        print("ERROR: Failed to push Rasa Actions image")
        sys.exit(1)
    
    print("\n[OK] Rasa Actions image built and pushed successfully!")
    
    # Update ECS service
    print("\n" + "="*70)
    print("UPDATING ECS SERVICE")
    print("="*70)
    
    os.chdir("../../")
    
    if not run_cmd(
        f"aws ecs update-service --cluster {CLUSTER_NAME} --service {SERVICE_NAME} "
        f"--force-new-deployment --region {AWS_REGION}"
    ):
        print("ERROR: Failed to update ECS service")
        sys.exit(1)
    
    print("\n[OK] ECS service update triggered!")
    print("\n" + "="*70)
    print("DEPLOYMENT INITIATED")
    print("="*70)
    print("\nThe deployment will take 3-5 minutes to complete.")
    print("You can monitor the deployment with:")
    print(f"  aws ecs describe-services --cluster {CLUSTER_NAME} --services {SERVICE_NAME} --query 'services[0].deployments'")
    print("\nYour chatbot will be available at:")
    print("  https://main.d1fw711o7cx5w2.amplifyapp.com")
    print("="*70)

if __name__ == "__main__":
    main()

