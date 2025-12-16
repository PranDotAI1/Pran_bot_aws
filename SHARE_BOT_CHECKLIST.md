# Share Your Amplify Bot - Quick Checklist

Use this checklist to verify your bot is ready to share with others.

---

## ✅ **Pre-Share Checklist**

### 1. Backend Is Running
- [ ] ECS Service is ACTIVE and RUNNING
- [ ] Check at: AWS Console > ECS > Clusters > pran-chatbot-cluster > Services
- [ ] Running count: 1/1 or more
- [ ] Status: ACTIVE

### 2. Load Balancer Is Healthy
- [ ] ALB health checks passing
- [ ] Check at: AWS Console > EC2 > Load Balancers
- [ ] Target health: Healthy
- [ ] Test URL: `http://YOUR-ALB-DNS:8080/health` should return 200

### 3. Database Is Connected
- [ ] RDS instance is available
- [ ] Check at: AWS Console > RDS > Databases
- [ ] Status: Available
- [ ] Backend can connect (check ECS logs)

### 4. Amplify Is Deployed
- [ ] Latest code deployed successfully
- [ ] Check at: AWS Console > Amplify
- [ ] Build status: Succeed (green)
- [ ] No deployment errors

### 5. Frontend-Backend Connection
- [ ] `amplify.yml` proxy configured correctly
- [ ] Frontend uses `/api/chatbot` endpoint
- [ ] No Mixed Content errors in browser console

---

## 🚀 **Quick Test Before Sharing**

### Test 1: Visit Your Amplify URL
```
1. Open: https://YOUR-APP-ID.amplifyapp.com
2. Expected: Chatbot interface loads
3. Expected: No console errors
```

### Test 2: Send a Test Message
```
1. Type: "Hello"
2. Expected: Bot responds with greeting
3. Response time: < 5 seconds
```

### Test 3: Test Real Feature
```
1. Type: "show insurance plans"
2. Expected: Lists all 18 insurance plans
3. Expected: No errors or timeouts
```

---

## 📱 **Sharing Your Bot**

Once all checks pass, you can share:

### Share the Amplify URL:
```
https://YOUR-APP-ID.amplifyapp.com
```

### What Others Will See:
- ✅ Professional chatbot interface
- ✅ Real-time responses
- ✅ Access to all features:
  - Insurance plan information
  - Doctor search
  - Appointment booking
  - Medical information queries

### What Others DON'T Need:
- ❌ AWS account
- ❌ Installation or setup
- ❌ API keys or credentials
- ❌ Technical knowledge

**They just visit the link and start chatting!**

---

## 🔧 **Troubleshooting Before Sharing**

### Issue: "Bot doesn't respond"

**Check:**
1. Backend ECS tasks are running
2. Load balancer is healthy
3. Check CloudWatch logs: `/ecs/pran-chatbot-task`
4. Test backend directly:
   ```bash
   curl -X POST http://YOUR-ALB-DNS:8080/rasa-webhook \
     -H "Content-Type: application/json" \
     -d '{"sender":"test","message":"hello"}'
   ```

### Issue: "Mixed Content Error"

**Fix:**
- Ensure frontend uses `/api/chatbot` not direct HTTP URL
- Check `amplify.yml` has correct proxy configuration
- Frontend should NOT hardcode `http://` backend URL

### Issue: "CORS Error"

**Fix:**
- Use Amplify proxy (`/api/chatbot`) instead of direct backend calls
- This bypasses CORS by proxying through Amplify

### Issue: "Slow responses"

**Check:**
1. Database connection (might be timing out)
2. AWS Bedrock rate limits
3. ECS task CPU/memory usage
4. Increase ECS task size if needed

---

## 📊 **Monitoring After Sharing**

### Check Regularly:
1. **ECS Service Health**
   - Go to: ECS Console > pran-chatbot-service
   - Ensure tasks are running

2. **CloudWatch Logs**
   - Go to: CloudWatch > Log groups > `/ecs/pran-chatbot-task`
   - Look for errors

3. **Amplify Build Status**
   - Go to: Amplify Console > Your App
   - Ensure latest build succeeded

4. **Database Connections**
   - Go to: RDS Console > Performance Insights
   - Monitor connection count

---

## 🎯 **Current Deployment Info**

Update this section with your actual values:

### Amplify URL:
```
https://YOUR-APP-ID.amplifyapp.com
```

### Backend Load Balancer:
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080
```

### Database:
```
hospital.cv8wum284gev.us-east-1.rds.amazonaws.com
```

### Region:
```
us-east-1
```

---

## ✅ **Ready to Share Criteria**

Your bot is ready to share when:

- ✅ All pre-share checklist items checked
- ✅ All quick tests passing
- ✅ No errors in browser console
- ✅ Response time < 5 seconds
- ✅ Backend logs show no errors
- ✅ Database queries working

**Once ready, simply share your Amplify URL with anyone!**

---

## 📞 **Support**

If users report issues:
1. Check ECS logs first
2. Verify backend is running
3. Test the bot yourself
4. Check database connectivity
5. Review CloudWatch metrics

---

**Last Updated**: December 2025  
**Status**: Production Ready
