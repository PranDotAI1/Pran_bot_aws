# AWS Amplify Deployment Guide

Complete step-by-step guide to deploy the Hospital Chatbot on AWS Amplify from this repository.

---

## Overview

This chatbot system consists of:
- **Frontend**: React app deployed on AWS Amplify
- **Backend**: Rasa chatbot running on AWS ECS
- **Database**: PostgreSQL on AWS RDS
- **AI**: AWS Bedrock for LLM responses

---

## Prerequisites

Before starting, ensure you have:

- [ ] AWS Account with admin access
- [ ] GitHub account (for Amplify connection)
- [ ] AWS CLI installed and configured
- [ ] Docker installed locally
- [ ] Node.js 14+ and Python 3.10+ installed

---

## Part 1: Backend Infrastructure Setup (Required First)

### Step 1: Create RDS PostgreSQL Database

1. Go to AWS RDS Console
2. Click "Create database"
3. Choose:
   - Engine: PostgreSQL
   - Version: 13 or higher
   - Template: Free tier (for testing) or Production
   - DB instance identifier: `pran-chatbot-db`
   - Master username: `postgres`
   - Master password: (create a strong password)
   - DB name: `hospital`
   - VPC: Default or your custom VPC
   - Public access: Yes (for initial setup)
4. Create database and note the endpoint

### Step 2: Populate Database

```bash
# Clone the repository
git clone https://github.com/PranDotAI1/Pran_bot_aws.git
cd Pran_bot_aws

# Install Python dependencies
pip install psycopg2-binary

# Set environment variables
export DB_HOST=your-rds-endpoint.rds.amazonaws.com
export DB_NAME=hospital
export DB_USER=postgres
export DB_PASSWORD=your-password
export DB_PORT=5432

# Run database population script (you'll need to create one or use pgAdmin)
# Import the schema and data from your local database
```

### Step 3: Create ECR Repositories

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repositories
aws ecr create-repository --repository-name pran-chatbot-rasa-backend --region us-east-1
aws ecr create-repository --repository-name pran-chatbot-rasa-actions --region us-east-1
```

### Step 4: Build and Push Docker Images

```bash
# Navigate to backend
cd backend/app

# Build backend image
docker build -t pran-chatbot-rasa-backend:latest -f Dockerfile .

# Build actions image
docker build -t pran-chatbot-rasa-actions:latest -f Dockerfile.actions .

# Tag images
docker tag pran-chatbot-rasa-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-backend:latest
docker tag pran-chatbot-rasa-actions:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-actions:latest

# Push images
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-backend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-actions:latest
```

### Step 5: Create ECS Cluster and Task Definition

1. Go to AWS ECS Console
2. Create a new cluster:
   - Name: `pran-chatbot-cluster`
   - Infrastructure: AWS Fargate
3. Create task definition with both containers:
   - Container 1: rasa-backend (port 5005)
   - Container 2: rasa-actions (port 5055)
4. Set environment variables in task definition:
   - `DB_HOST`: Your RDS endpoint
   - `DB_NAME`: hospital
   - `DB_USER`: postgres
   - `DB_PASSWORD`: Your password
   - `AWS_REGION`: us-east-1

### Step 6: Create Application Load Balancer

1. Go to EC2 > Load Balancers
2. Create Application Load Balancer:
   - Name: `pran-chatbot-alb`
   - Scheme: Internet-facing
   - Listeners: HTTP on port 8080
   - Target group: Create new, target type IP
3. Note the Load Balancer DNS name

### Step 7: Create ECS Service

1. In ECS cluster, create service:
   - Launch type: Fargate
   - Task definition: Your created definition
   - Service name: `pran-chatbot-service`
   - Desired tasks: 1
   - Load balancer: Attach the ALB created above
2. Wait for service to become healthy

---

## Part 2: Frontend Deployment on AWS Amplify

### Step 1: Fork or Connect Repository

1. Go to AWS Amplify Console
2. Click "New app" > "Host web app"
3. Choose "GitHub"
4. Authorize AWS Amplify to access your GitHub
5. Select repository: `Pran_bot_aws`
6. Branch: `main`

### Step 2: Configure Build Settings

Amplify will detect the `amplify.yml` file automatically. Verify it contains:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: build
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

### Step 3: Update amplify.yml with Your Backend URL

Edit `amplify.yml` in your repository:

```yaml
rewrites:
  - source: /api/chatbot
    target: http://YOUR-LOAD-BALANCER-DNS:8080/rasa-webhook
    status: 200
    headers:
      Content-Type: application/json
```

Replace `YOUR-LOAD-BALANCER-DNS` with your actual ALB DNS from Step 6 above.

### Step 4: Configure Environment Variables (if needed)

In Amplify Console:
1. Go to App settings > Environment variables
2. Add any frontend-specific variables (usually none needed)

### Step 5: Update Frontend API Endpoint

Edit `frontend/src/useChatbot.js` to ensure it points to the correct endpoint:

```javascript
const API_URL = '/api/chatbot'; // This uses the Amplify proxy
```

Commit and push this change to GitHub.

### Step 6: Deploy

1. In Amplify Console, click "Save and deploy"
2. Amplify will:
   - Pull code from GitHub
   - Install dependencies
   - Build the React app
   - Deploy to CDN
3. Wait for build to complete (5-10 minutes)

### Step 7: Get Your App URL

After deployment completes:
1. Amplify will provide a URL like: `https://main.d1234567890.amplifyapp.com`
2. Visit this URL to test your chatbot

---

## Part 3: Testing

### Test 1: Frontend Loads
```
Visit your Amplify URL
Expected: Chatbot interface appears
```

### Test 2: Chat Functionality
```
Type: "Hello"
Expected: Bot responds with greeting
```

### Test 3: Insurance Plans
```
Type: "show insurance plans"
Expected: Lists all 18 insurance plans
```

### Test 4: Doctor Search
```
Type: "find a gynecologist"
Expected: Lists available gynecologists
```

---

## Part 4: Continuous Deployment

Once set up, Amplify automatically deploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Update chatbot feature"
git push origin main

# Amplify automatically detects and deploys
```

---

## Environment Variables Reference

### Backend (ECS Task Definition)
```env
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_NAME=hospital
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_PORT=5432
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
```

### Frontend (Amplify - Optional)
```env
REACT_APP_API_URL=/api/chatbot
```

---

## Cost Estimation (AWS)

Monthly costs for running this application:

- **RDS PostgreSQL** (db.t3.micro): ~$15
- **ECS Fargate** (1 task, 0.5 vCPU, 1GB RAM): ~$15
- **Application Load Balancer**: ~$20
- **Amplify Hosting**: Free tier / ~$0.15 per GB
- **AWS Bedrock**: Pay per API call (varies)

**Total**: Approximately $50-70/month

---

## Troubleshooting

### Issue: Amplify build fails

**Solution:**
```bash
# Check that frontend/package.json exists
# Verify amplify.yml is in root directory
# Check build logs in Amplify Console
```

### Issue: Chatbot doesn't respond

**Solution:**
1. Verify ECS tasks are running (ECS Console)
2. Check Load Balancer health checks (EC2 Console)
3. Test backend directly:
   ```bash
   curl -X POST http://YOUR-ALB-DNS:8080/rasa-webhook \
     -H "Content-Type: application/json" \
     -d '{"sender":"test","message":"hello"}'
   ```

### Issue: Database connection failed

**Solution:**
1. Check RDS security group allows inbound from ECS tasks
2. Verify environment variables in ECS task definition
3. Check RDS publicly accessible setting

### Issue: CORS errors in browser

**Solution:**
- Ensure `amplify.yml` proxy rewrite is configured correctly
- Check backend CORS settings in `wrapper_server.py`

---

## Quick Start Commands

For someone cloning the repository:

```bash
# 1. Clone repository
git clone https://github.com/PranDotAI1/Pran_bot_aws.git
cd Pran_bot_aws

# 2. Set up AWS infrastructure (follow Part 1 above)

# 3. Update amplify.yml with your Load Balancer URL

# 4. Connect to Amplify (follow Part 2 above)

# 5. Test deployment
curl https://your-amplify-url.amplifyapp.com
```

---

## Security Best Practices

1. **Never commit credentials** - Use AWS Secrets Manager
2. **Enable HTTPS** - Use AWS Certificate Manager with ALB
3. **Restrict security groups** - Only allow necessary traffic
4. **Use IAM roles** - Don't hardcode AWS credentials
5. **Enable CloudWatch logs** - Monitor for security issues

---

## Architecture Diagram

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  AWS Amplify        │  (Frontend - React)
│  CloudFront CDN     │
└──────┬──────────────┘
       │ /api/chatbot
       ▼
┌─────────────────────┐
│  Application LB     │  (Port 8080)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  ECS Fargate        │
│  ├─ Rasa Backend    │  (Port 5005)
│  └─ Rasa Actions    │  (Port 5055)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐     ┌──────────────┐
│  RDS PostgreSQL     │     │ AWS Bedrock  │
│  (Hospital DB)      │     │ (LLM)        │
└─────────────────────┘     └──────────────┘
```

---

## Support

For deployment issues:
1. Check CloudWatch logs in ECS
2. Review Amplify build logs
3. Test backend endpoint directly
4. Check GitHub issues: https://github.com/PranDotAI1/Pran_bot_aws/issues

---

## Additional Resources

- [AWS Amplify Documentation](https://docs.aws.amazon.com/amplify/)
- [Rasa Documentation](https://rasa.com/docs/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [PostgreSQL on RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)

---

**Last Updated**: December 2025  
**Status**: Production Ready  
**Maintainer**: PranDotAI Team
