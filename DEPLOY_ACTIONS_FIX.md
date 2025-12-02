# Deploy Actions Server Fix - Step by Step Guide

This guide walks you through rebuilding and redeploying the Rasa Actions Server with the fixes for duplicate responses.

## 🔧 What Was Fixed

1. **Indentation Errors**: Fixed all Python indentation issues in `actions.py`
2. **Duplicate Response Prevention**: Added error message detection to prevent duplicate AWS credential error messages
3. **Single Response Guarantee**: Ensured only one response is sent per action execution
4. **Proper Error Handling**: Improved fallback logic when AWS services fail

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Access to ECR (Elastic Container Registry)
- Access to ECS cluster: `pran-chatbot-cluster`
- ECS service: `pran-chatbot-service`

## 🚀 Deployment Steps

### Step 1: Verify AWS Configuration

```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify ECR access
aws ecr describe-repositories --region us-east-1 | grep pran-chatbot-rasa-actions
```

### Step 2: Run the Deployment Script

```bash
# Make script executable (if not already)
chmod +x rebuild_actions_server.sh

# Run the deployment
./rebuild_actions_server.sh
```

The script will:
1. ✅ Login to ECR
2. ✅ Build the Docker image for linux/amd64
3. ✅ Push image to ECR
4. ✅ Force new ECS deployment
5. ✅ Wait for deployment to stabilize

### Step 3: Monitor Deployment

```bash
# Watch ECS service status
aws ecs describe-services \
    --cluster pran-chatbot-cluster \
    --services pran-chatbot-service \
    --region us-east-1 \
    --query 'services[0].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount}' \
    --output table

# Check actions server logs
aws logs tail /ecs/pran-chatbot-actions --follow --region us-east-1
```

### Step 4: Test the Fix

```bash
# Run the test script
chmod +x test_actions_fix.sh
./test_actions_fix.sh
```

The test script will verify:
- ✅ Only one response per query
- ✅ No duplicate responses
- ✅ Proper error handling
- ✅ Fallback responses work correctly

## 🧪 Manual Testing

### Test 1: Simple Greeting

```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user_001",
    "message": "Hello"
  }'
```

**Expected**: Single response array with one message

### Test 2: Complex Query

```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user_002",
    "message": "I need help with diabetes"
  }'
```

**Expected**: Single response array with one message (no duplicates)

### Test 3: Verify No Duplicates

```bash
# Send a message and count responses
response=$(curl -s -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user_003",
    "message": "Hello"
  }')

# Count responses (should be 1)
echo "$response" | jq '. | length'
```

**Expected**: Output should be `1`

## 🔍 Troubleshooting

### Issue: Build fails

**Solution**: Check Docker is running and has enough resources
```bash
docker info
docker system df
```

### Issue: ECR push fails

**Solution**: Verify ECR repository exists and you have push permissions
```bash
aws ecr describe-repositories --repository-names pran-chatbot-rasa-actions --region us-east-1
```

### Issue: ECS deployment fails

**Solution**: Check ECS service logs and task definition
```bash
aws ecs describe-services \
    --cluster pran-chatbot-cluster \
    --services pran-chatbot-service \
    --region us-east-1
```

### Issue: Still getting duplicate responses

**Solution**: 
1. Verify the new image is being used
2. Check actions server logs for errors
3. Verify the code changes are in the image
4. Restart the ECS service

## 📊 Verification Checklist

- [ ] Docker image built successfully
- [ ] Image pushed to ECR
- [ ] ECS deployment triggered
- [ ] New tasks running with updated image
- [ ] Health checks passing
- [ ] Test script passes all tests
- [ ] Manual tests show single responses
- [ ] No duplicate error messages

## 🎯 Success Criteria

✅ **Deployment Successful When:**
- ECS service shows all tasks running
- Health checks return 200 OK
- Test script shows all tests passing
- Manual API calls return single responses
- No duplicate error messages in logs

## 📝 Notes

- Deployment typically takes 2-5 minutes
- Old tasks will be drained gracefully
- Zero-downtime deployment if service has multiple tasks
- Monitor CloudWatch logs for any errors

## 🆘 Support

If you encounter issues:
1. Check CloudWatch logs: `/ecs/pran-chatbot-actions`
2. Check ECS service events
3. Verify task definition is using the correct image
4. Check security groups and network configuration

---

**Last Updated**: 2024-12-02  
**Version**: 1.0.0

