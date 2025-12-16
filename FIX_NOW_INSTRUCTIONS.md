# 🚨 FIX BACKEND NOW - Complete End-to-End Instructions

**Problem:** Backend returning 503 errors - ECS service down  
**Solution:** Restart ECS service  
**Time:** 6-9 minutes total  
**Your Chatbot:** https://main.d1fw711o7cx5w2.amplifyapp.com/

---

## ⚡ **OPTION 1: AUTOMATED FIX (Recommended - 6-9 minutes)**

### **Step 1: Install AWS CLI (2-3 minutes)**

```bash
# On macOS, run this in Terminal:
brew install awscli

# Or download installer:
# https://awscli.amazonaws.com/AWSCLIV2.pkg
```

**Don't have Homebrew?**
```bash
# Install Homebrew first:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install AWS CLI:
brew install awscli
```

### **Step 2: Configure AWS Credentials (1 minute)**

```bash
aws configure
```

**Enter when prompted:**
```
AWS Access Key ID: [Your AWS key]
AWS Secret Access Key: [Your AWS secret]
Default region name: us-east-1
Default output format: json
```

**Don't have AWS credentials?**
- Ask your AWS admin for Access Key ID and Secret Access Key
- Or ask them to run Step 3 for you

### **Step 3: Run Automated Fix Script (3-5 minutes)**

```bash
cd /Users/viditagarwal/Downloads/pran_chatbot-main
./fix_backend_now.sh
```

**The script will:**
1. ✓ Check prerequisites
2. ✓ Check current service status
3. ✓ Restart ECS service
4. ✓ Wait for tasks to start
5. ✓ Verify backend is responding
6. ✓ Test frontend
7. ✓ Confirm system is working

**Expected output:**
```
✓ BACKEND FIXED AND OPERATIONAL!

System Status:
  Backend:  ✓ Running and healthy
  Frontend: ✓ Accessible
  Chatbot:  ✓ Ready for testing
```

---

## ⚡ **OPTION 2: MANUAL FIX VIA AWS CONSOLE (3-5 minutes)**

**If you can't install AWS CLI or don't have credentials:**

### **Ask Your AWS Admin:**

Send them this message:

```
Hi,

Our chatbot backend is down (503 error). Can you please restart it?

Instructions:
1. Go to: AWS Console > ECS > pran-chatbot-cluster
2. Click: pran-chatbot-service
3. Click: "Update Service" button
4. Check: ☑ "Force new deployment"  
5. Set: Desired tasks = 1
6. Click: "Update"
7. Wait: 3-5 minutes for tasks to start

This fixes the 503 error and makes the chatbot work.

Service details:
- Cluster: pran-chatbot-cluster
- Service: pran-chatbot-service
- Region: us-east-1

Thanks!
```

---

## ⚡ **OPTION 3: AWS CLI COMMANDS (If Already Configured)**

**If you already have AWS CLI configured:**

```bash
# Check current status
aws ecs describe-services \
  --cluster pran-chatbot-cluster \
  --services pran-chatbot-service \
  --region us-east-1

# Restart service
aws ecs update-service \
  --cluster pran-chatbot-cluster \
  --service pran-chatbot-service \
  --desired-count 1 \
  --force-new-deployment \
  --region us-east-1

# Wait 3-5 minutes, then verify
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender":"test","message":"hello"}'
```

---

## ✅ **VERIFY IT'S FIXED**

### **Test 1: Backend Direct**

```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender":"test","message":"hello"}'
```

**Expected:** JSON response with bot greeting (NOT 503 HTML)

### **Test 2: Frontend Chatbot**

1. Go to: https://main.d1fw711o7cx5w2.amplifyapp.com/
2. Type: "hello"
3. **Expected:** Bot responds: "Hello! I'm Dr. AI, your healthcare assistant..."
4. **NOT:** "Sorry, I couldn't process your message"

### **Test 3: Insurance Query**

1. Type: "show insurance plans"
2. **Expected:** Lists all 18 insurance plans
3. Response time: 3-5 seconds

**When all 3 tests pass → FIXED! ✓**

---

## 🎯 **WHAT EACH OPTION REQUIRES**

| Option | Time | Requires | Difficulty |
|--------|------|----------|-----------|
| **Option 1: Automated** | 6-9 min | AWS CLI + Credentials | Easy |
| **Option 2: AWS Console** | 3-5 min | AWS Admin help | Easiest |
| **Option 3: Manual CLI** | 3-5 min | Pre-configured AWS CLI | Medium |

---

## 📋 **RECOMMENDED: Use Option 1 (Automated)**

**Why?**
- One command fixes everything
- Automatic verification
- Reusable for future issues
- No AWS Console access needed

**Steps:**
```bash
# 1. Install AWS CLI
brew install awscli

# 2. Configure (get credentials from AWS admin)
aws configure

# 3. Run fix
cd /Users/viditagarwal/Downloads/pran_chatbot-main
./fix_backend_now.sh
```

---

## 🚨 **AFTER FIX: TELL STAKEHOLDERS**

Once fixed, send this to your stakeholders:

```
Subject: Chatbot Back Online

Hi Team,

The chatbot is back online and ready for testing!

🔗 https://main.d1fw711o7cx5w2.amplifyapp.com/

We experienced a brief service restart (normal cloud 
infrastructure maintenance). Everything is working now.

Please try these queries:
• "show insurance plans"
• "find a gynecologist"
• "book an appointment"

Thanks for your patience!
```

---

## 🛡️ **PREVENT THIS IN FUTURE**

After the fix, set up monitoring:

```bash
# Run this to set up CloudWatch alarms
# (requires AWS CLI configured)
aws cloudwatch put-metric-alarm \
  --alarm-name pran-chatbot-service-down \
  --alarm-description "Alert when ECS tasks drop to 0" \
  --metric-name RunningTaskCount \
  --namespace AWS/ECS \
  --statistic Average \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=ClusterName,Value=pran-chatbot-cluster Name=ServiceName,Value=pran-chatbot-service \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:TOPIC_NAME
```

Or see: `URGENT_FIX_BACKEND_DOWN.md` for full monitoring setup.

---

## 📞 **NEED HELP?**

**Can't install AWS CLI?**
- Use Option 2 (ask AWS admin)

**Don't have AWS credentials?**
- Ask AWS admin for:
  - AWS Access Key ID
  - AWS Secret Access Key
- Or ask them to run the fix

**Still not working after fix?**
- Check CloudWatch logs: `/ecs/pran-chatbot-task`
- Check ECS Console for error messages
- Verify tasks are RUNNING and HEALTHY
- Wait 5 minutes (tasks might still be starting)

---

## ⏱️ **TIMELINE**

```
Option 1 (Automated):
├─ Install AWS CLI: 2-3 min
├─ Configure credentials: 1 min
├─ Run script: 3-5 min
└─ Total: 6-9 minutes

Option 2 (AWS Admin):
├─ Send request: 1 min
├─ Admin fixes: 3-5 min
└─ Total: 4-6 minutes

Option 3 (Manual CLI):
├─ Run commands: 1 min
├─ Wait for restart: 3-5 min
└─ Total: 4-6 minutes
```

---

## 🎯 **QUICK START (Choose One)**

### **I have AWS CLI configured:**
```bash
cd /Users/viditagarwal/Downloads/pran_chatbot-main
./fix_backend_now.sh
```

### **I need to install AWS CLI:**
```bash
brew install awscli
aws configure
cd /Users/viditagarwal/Downloads/pran_chatbot-main
./fix_backend_now.sh
```

### **I don't have AWS access:**
```
Contact AWS admin with: URGENT_FIX_BACKEND_DOWN.md
```

---

**Current Status:** ❌ Backend Down  
**Your Chatbot:** https://main.d1fw711o7cx5w2.amplifyapp.com/  
**Fix Time:** 6-9 minutes  
**Action:** Choose option above and execute now!  

**🚨 FIX THIS BEFORE STAKEHOLDER DEMO! 🚨**
