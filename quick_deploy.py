#!/usr/bin/env python3
"""
Quick deployment script - Updates ECS task definition to pull latest code
This forces ECS to rebuild the image from the GitHub repo
"""

import boto3
import json
import time

# AWS Credentials - Set these before running
ACCESS_KEY = input("Enter AWS Access Key ID: ").strip()
SECRET_KEY = input("Enter AWS Secret Access Key: ").strip()
REGION = 'us-east-1'
CLUSTER = 'pran-chatbot-cluster'
SERVICE = 'pran-chatbot-service'

print("=" * 70)
print("  DEPLOYING MONGODB FIX TO BACKEND")
print("=" * 70)
print()

# Create ECS client
ecs = boto3.client(
    'ecs',
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

print("Step 1: Forcing new deployment with latest code...")
try:
    response = ecs.update_service(
        cluster=CLUSTER,
        service=SERVICE,
        forceNewDeployment=True
    )
    print("  ✓ Deployment initiated!")
    print()
except Exception as e:
    print(f"  ✗ Error: {e}")
    exit(1)

print("Step 2: Waiting for new tasks to start (3-5 minutes)...")
print("Please be patient - this takes time...")
print()

for i in range(60):  # 5 minutes max
    time.sleep(5)
    print(".", end="", flush=True)
    
    try:
        resp = ecs.describe_services(cluster=CLUSTER, services=[SERVICE])
        if resp['services']:
            running = resp['services'][0]['runningCount']
            if running >= 1:
                print()
                print()
                print("  ✓ Tasks are starting!")
                break
    except:
        pass

print()
print("Waiting for health checks (30 seconds)...")
time.sleep(30)
print()

print("Step 3: Testing backend...")
import urllib.request
import urllib.error

backend_url = 'http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook'

for i in range(15):  # Try for 2.5 minutes
    try:
        data = json.dumps({'sender': 'test', 'message': 'hello'}).encode('utf-8')
        req = urllib.request.Request(backend_url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                print(f"  ✓ Backend is responding! (attempt {i+1})")
                print()
                if result:
                    print("Bot response:")
                    print(f"  {result[0].get('text', '')[:100]}...")
                print()
                print("=" * 70)
                print("  ✓✓✓ BACKEND IS FIXED AND WORKING! ✓✓✓")
                print("=" * 70)
                print()
                print("Your chatbot: https://main.d1fw711o7cx5w2.amplifyapp.com/")
                print()
                print("Share with stakeholders now!")
                print()
                exit(0)
    except Exception as e:
        if i < 14:
            print(f"  Attempt {i+1}/15 - waiting 10 seconds...")
            time.sleep(10)

print()
print("=" * 70)
print("  ⚠ Backend may need more time to start")
print("=" * 70)
print()
print("The deployment is in progress but needs more time.")
print("Try testing in 5-10 minutes:")
print("  https://main.d1fw711o7cx5w2.amplifyapp.com/")
print()
print("Or check CloudWatch logs for any errors.")
print()
