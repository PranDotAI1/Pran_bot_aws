#!/usr/bin/env python3
"""
Simple script to fix the backend by restarting ECS service
Run this with: python3 fix_backend_simple.py
"""

import sys
import time
import json

# Try to import boto3
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("Installing boto3...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "boto3", "--quiet"])
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

print("=" * 70)
print("  PRAN CHATBOT - BACKEND FIX")
print("=" * 70)
print()

# Configuration
CLUSTER_NAME = "pran-chatbot-cluster"
SERVICE_NAME = "pran-chatbot-service"
REGION = "us-east-1"
BACKEND_URL = "http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"

def get_credentials():
    """Get AWS credentials from user"""
    print("I need your AWS credentials to fix the backend.")
    print()
    print("Please enter your AWS credentials:")
    print("(Get these from your AWS admin if you don't have them)")
    print()
    
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    
    if not access_key or not secret_key:
        print()
        print("❌ Credentials are required!")
        print()
        print("If you don't have credentials, ask your AWS admin to:")
        print("  1. Go to AWS Console > ECS > pran-chatbot-cluster")
        print("  2. Click pran-chatbot-service")
        print("  3. Click 'Update Service'")
        print("  4. Check 'Force new deployment'")
        print("  5. Set Desired tasks = 1")
        print("  6. Click 'Update'")
        print()
        sys.exit(1)
    
    return access_key, secret_key

def check_service_status(ecs_client):
    """Check current service status"""
    print("Step 1: Checking current service status...")
    try:
        response = ecs_client.describe_services(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME]
        )
        
        if response['services']:
            service = response['services'][0]
            print(f"  Service: {service['serviceName']}")
            print(f"  Status: {service['status']}")
            print(f"  Running tasks: {service['runningCount']}")
            print(f"  Desired tasks: {service['desiredCount']}")
            print()
            return True
        else:
            print("  ❌ Service not found!")
            return False
    except ClientError as e:
        print(f"  ❌ Error: {e}")
        return False

def restart_service(ecs_client):
    """Restart the ECS service"""
    print("Step 2: Restarting ECS service...")
    try:
        response = ecs_client.update_service(
            cluster=CLUSTER_NAME,
            service=SERVICE_NAME,
            forceNewDeployment=True,
            desiredCount=1
        )
        print("  ✓ Service restart initiated!")
        print()
        return True
    except ClientError as e:
        print(f"  ❌ Error: {e}")
        return False

def wait_for_tasks(ecs_client):
    """Wait for tasks to start"""
    print("Step 3: Waiting for tasks to start (2-3 minutes)...")
    print("Please be patient...")
    print()
    
    for i in range(36):  # 3 minutes max
        time.sleep(5)
        try:
            response = ecs_client.describe_services(
                cluster=CLUSTER_NAME,
                services=[SERVICE_NAME]
            )
            
            if response['services']:
                running = response['services'][0]['runningCount']
                print(".", end="", flush=True)
                
                if running >= 1:
                    print()
                    print()
                    print("  ✓ Tasks are running!")
                    print()
                    return True
        except:
            pass
    
    print()
    print("  ⚠ Tasks still starting... may need a few more minutes")
    print()
    return False

def test_backend():
    """Test if backend is responding"""
    print("Step 4: Testing backend...")
    print()
    
    import urllib.request
    import urllib.error
    
    # Wait a bit for health checks
    print("Waiting 30 seconds for health checks...")
    time.sleep(30)
    print()
    
    for i in range(10):
        print(f"Test attempt {i+1}/10...")
        try:
            data = json.dumps({"sender": "test", "message": "hello"}).encode('utf-8')
            req = urllib.request.Request(
                f"{BACKEND_URL}/rasa-webhook",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    print()
                    print("  ✓ Backend is responding!")
                    print()
                    if result and len(result) > 0:
                        print("Sample response:")
                        print(f"  {result[0].get('text', '')[:100]}...")
                    print()
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 503:
                if i < 9:
                    print("  Still starting... waiting 10 seconds")
                    time.sleep(10)
            else:
                print(f"  HTTP Error: {e.code}")
        except Exception as e:
            if i < 9:
                print(f"  Not ready yet... waiting 10 seconds")
                time.sleep(10)
    
    print()
    print("  ⚠ Backend not responding yet")
    print("  Try testing again in 3-5 minutes")
    print()
    return False

def main():
    # Get credentials
    try:
        access_key, secret_key = get_credentials()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    
    print()
    print("Connecting to AWS...")
    print()
    
    # Create ECS client
    try:
        ecs_client = boto3.client(
            'ecs',
            region_name=REGION,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Test credentials
        ecs_client.list_clusters(maxResults=1)
        print("  ✓ AWS credentials valid!")
        print()
    except NoCredentialsError:
        print("  ❌ Invalid credentials!")
        sys.exit(1)
    except ClientError as e:
        print(f"  ❌ Error: {e}")
        print()
        print("Make sure your credentials have ECS permissions")
        sys.exit(1)
    
    # Check service
    if not check_service_status(ecs_client):
        sys.exit(1)
    
    # Restart service
    if not restart_service(ecs_client):
        sys.exit(1)
    
    # Wait for tasks
    wait_for_tasks(ecs_client)
    
    # Test backend
    backend_ok = test_backend()
    
    # Summary
    print("=" * 70)
    if backend_ok:
        print("  ✓ BACKEND IS FIXED AND WORKING!")
    else:
        print("  ⚠ BACKEND IS RESTARTING (may need a few more minutes)")
    print("=" * 70)
    print()
    print("Your chatbot: https://main.d1fw711o7cx5w2.amplifyapp.com/")
    print()
    print("Test it now:")
    print("  1. Go to the URL above")
    print("  2. Type: 'hello'")
    print("  3. Expected: Bot responds with greeting")
    print()
    if not backend_ok:
        print("If bot still shows errors, wait 3-5 minutes and try again.")
        print()
    
    print("=" * 70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print()
        print("Please contact your AWS admin with this error message.")
        sys.exit(1)
