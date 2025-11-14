# Deployment Guide - New Pran Bot AWS

This guide provides step-by-step instructions for deploying the production-ready chatbot to AWS.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. Docker installed
4. Terraform (for infrastructure deployment)
5. Environment variables configured

## Pre-Deployment Checklist

- [ ] All environment variables configured in `.env`
- [ ] AWS credentials configured
- [ ] Database instances created and accessible
- [ ] MongoDB instance configured
- [ ] AWS Bedrock access granted
- [ ] Docker images built and tested locally

## Environment Configuration

1. Copy the environment template:
   ```bash
   cp deployment/config/.env.template .env
   ```

2. Fill in all required values:
   - AWS credentials
   - Database connection strings
   - MongoDB URI
   - API endpoints
   - Security keys

3. Verify configuration:
   ```bash
   # Test database connections
   python scripts/test_connections.py
   ```

## Local Testing

Before deploying to AWS, test locally:

```bash
# Start all services
docker-compose up -d

# Check health
curl http://localhost:5001/health

# Test MongoDB
curl http://localhost:5001/mongodb/test
```

## AWS Deployment

### Option 1: Using Terraform

```bash
cd deployment/terraform
terraform init
terraform plan
terraform apply
```

### Option 2: Using AWS CLI and ECS

```bash
# Build and push Docker images
./deployment/scripts/build_and_push.sh

# Deploy to ECS
./deployment/scripts/deploy_ecs.sh
```

### Option 3: Using Docker Compose on EC2

```bash
# SSH into EC2 instance
ssh user@your-ec2-instance

# Clone repository
git clone <repository-url>
cd New_Pran_bot_aws

# Configure environment
cp deployment/config/.env.template .env
# Edit .env with your values

# Start services
docker-compose up -d
```

## Post-Deployment Verification

1. Check health endpoints:
   ```bash
   curl https://your-domain.com/health
   ```

2. Verify MongoDB connection:
   ```bash
   curl https://your-domain.com/mongodb/test
   ```

3. Test chatbot:
   ```bash
   curl -X POST https://your-domain.com/rasa-webhook \
     -H "Content-Type: application/json" \
     -d '{"sender": "test", "message": "Hello"}'
   ```

4. Check CloudWatch logs for errors

## Monitoring

- CloudWatch Logs: Monitor application logs
- CloudWatch Metrics: Track performance
- Health Checks: Automated health monitoring
- Alarms: Set up alerts for critical issues

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check security groups
   - Verify credentials
   - Check network connectivity

2. **MongoDB Connection Failed**
   - Verify MongoDB URI format
   - Check firewall rules
   - Verify authentication

3. **AWS Bedrock Access Denied**
   - Verify IAM permissions
   - Check region configuration
   - Verify model access

4. **Rasa Not Responding**
   - Check Rasa service status
   - Verify webhook URL
   - Check logs for errors

## Rollback Procedure

If deployment fails:

```bash
# Stop services
docker-compose down

# Or for ECS
aws ecs update-service --cluster your-cluster --service your-service --desired-count 0

# Restore previous version
git checkout previous-stable-tag
# Redeploy
```

## Security Checklist

- [ ] All secrets in environment variables
- [ ] No hardcoded credentials
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Security groups configured
- [ ] IAM roles with least privilege
- [ ] Secrets Manager for sensitive data

## Maintenance

### Regular Tasks

1. Monitor logs weekly
2. Review CloudWatch metrics
3. Update dependencies monthly
4. Backup databases regularly
5. Review security configurations quarterly

### Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade
npm update

# Rebuild and redeploy
docker-compose build
docker-compose up -d
```

## Support

For deployment issues:
1. Check CloudWatch logs
2. Review this guide
3. Check GitHub issues
4. Contact DevOps team

