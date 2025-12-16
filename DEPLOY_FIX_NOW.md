# 🚨 DEPLOY THE FIX NOW

I've fixed the MongoDB bug in the code and pushed it to GitHub.  
Now we need to rebuild the Docker image and deploy it.

---

## ⚡ OPTION 1: Have AWS Admin Rebuild (EASIEST - 10 minutes)

**Send this to your AWS admin:**

```
Hi,

I've fixed the backend bug (MongoDB configuration error).  
The fix is in GitHub: commit 608616b2

Can you please rebuild and deploy the Docker images?

Commands needed:
1. cd pran_chatbot-main
2. git pull origin main
3. ./build_and_deploy_rasa_backend.sh

Or manually:
1. Build: docker build -t 941377143251.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-backend:latest -f backend/app/Dockerfile backend/app
2. Push: docker push 941377143251.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-backend:latest
3. Update ECS: Force new deployment on pran-chatbot-service

This will fix the 503 error.

Thanks!
```

---

## ⚡ OPTION 2: Install Docker & Deploy Yourself (20 minutes)

### Step 1: Install Docker

**macOS:**
```bash
# Download Docker Desktop from:
https://www.docker.com/products/docker-desktop/

# Or via Homebrew:
brew install --cask docker

# Start Docker Desktop application
# Wait for it to fully start (whale icon in menu bar)
```

### Step 2: Login to AWS ECR

```bash
cd /Users/viditagarwal/Downloads/pran_chatbot-main

# Get latest code
git pull origin main

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  941377143251.dkr.ecr.us-east-1.amazonaws.com
```

###Step 3: Build & Push Docker Image

```bash
# Build the image (takes 5-10 minutes)
docker build \
  --platform linux/amd64 \
  -t 941377143251.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-backend:latest \
  -f backend/app/Dockerfile \
  backend/app

# Push to ECR (takes 2-3 minutes)
docker push 941377143251.dkr.ecr.us-east-1.amazonaws.com/pran-chatbot-rasa-backend:latest
```

### Step 4: Update ECS Service

```bash
# Use the quick_deploy.py script
python3 quick_deploy.py

# Or use AWS CLI (if configured)
python3 -m awscli ecs update-service \
  --cluster pran-chatbot-cluster \
  --service pran-chatbot-service \
  --force-new-deployment \
  --region us-east-1
```

### Step 5: Wait & Test

Wait 5 minutes, then test:
```
https://main.d1fw711o7cx5w2.amplifyapp.com/
```

---

## ⚡ OPTION 3: Use AWS CodeBuild/Pipeline (If Set Up)

If there's a CI/CD pipeline:
1. Push is already done (commit 608616b2)
2. Pipeline should auto-build and deploy
3. Check AWS CodePipeline console

---

## 🎯 RECOMMENDED: Use Option 1

**Fastest:** Have AWS admin run the build script  
**Time:** 10 minutes  
**Requires:** AWS admin with Docker access  

---

## 📋 WHAT I'VE FIXED

**Bug:** MongoDB connection error  
**File:** `backend/wrapper_server.py`  
**Fix:** Made MongoDB optional + added default database name  
**Commit:** 608616b2  
**Status:** Code fixed and pushed to GitHub ✓  
**Remaining:** Need to rebuild Docker image and deploy  

---

## ⏰ NEXT STEPS

1. **Choose option above** (1, 2, or 3)
2. **Deploy the fix** (10-20 minutes)
3. **Test chatbot** (should work after deployment)
4. **Share with stakeholders**

---

**Fix Status:** Code fixed ✓  
**Deployment:** Pending  
**Action:** Deploy using one of the options above  
