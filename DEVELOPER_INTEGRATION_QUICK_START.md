# 🚀 Developer Integration Quick Start

## ✅ Everything You Need is in the Repository!

This repository contains everything your developer needs to integrate the chatbot with any UI. **It will work!**

---

## 📡 Production API Endpoint

**Base URL**: `http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080`

### Main Endpoints:

1. **Health Check** (Test if backend is running):
   ```
   GET http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/health
   ```

2. **Chat Endpoint** (Send messages to chatbot):
   ```
   POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook
   ```

---

## 🔌 Quick Integration (Copy & Paste Ready)

### JavaScript/TypeScript Example

```typescript
// Configuration
const CHATBOT_API_URL = 'http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080';

// Send message function
async function sendMessage(userId: string, message: string) {
  try {
    const response = await fetch(`${CHATBOT_API_URL}/rasa-webhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender: userId,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data; // Returns array of message objects
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

// Usage
const messages = await sendMessage('user123', 'Hello, I need help');
messages.forEach(msg => {
  console.log('Bot:', msg.text);
});
```

### Request Format

```json
{
  "sender": "unique_user_id",
  "message": "Your message here"
}
```

### Response Format

```json
[
  {
    "recipient_id": "unique_user_id",
    "text": "Bot response message"
  }
]
```

---

## ✅ What's Included in Repository

### 1. Complete Backend ✅
- Flask API gateway with CORS enabled
- Rasa NLP engine
- AWS Bedrock integration
- All custom actions

### 2. API Documentation ✅
- `API_ENDPOINTS_REFERENCE.md` - Complete API reference
- `UI_INTEGRATION_GUIDE.md` - Detailed integration guide
- `UI_DEVELOPER_GUIDE.md` - Developer-focused guide

### 3. Configuration ✅
- `config.env.template` - Environment variable template
- `docker-compose.yml` - For local testing
- `README.md` - Complete setup instructions

### 4. CORS Enabled ✅
The backend has CORS enabled, so your UI can make requests from any domain:
```python
CORS(app)  # Already configured in wrapper_server.py
```

---

## 🧪 Test Before Integration

### 1. Test Health Endpoint

```bash
curl http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "flask_wrapper": "running",
  "rasa_status": "connected",
  "mongodb_status": "connected"
}
```

### 2. Test Chat Endpoint

```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_user", "message": "Hello"}'
```

Expected response:
```json
[
  {
    "recipient_id": "test_user",
    "text": "Hello! How can I help you today?"
  }
]
```

---

## 📚 Documentation Files in Repository

1. **`README.md`** - Main repository documentation
2. **`API_ENDPOINTS_REFERENCE.md`** - Complete API reference
3. **`UI_INTEGRATION_GUIDE.md`** - Step-by-step integration guide
4. **`UI_DEVELOPER_GUIDE.md`** - Developer-focused guide
5. **`DEVELOPER_SETUP_GUIDE.md`** - Backend setup (if needed)

---

## 🎯 Integration Checklist

- [x] Production endpoint is live and working
- [x] CORS is enabled (works from any domain)
- [x] Health check endpoint available
- [x] Chat endpoint documented
- [x] Request/response format documented
- [x] Example code provided
- [x] Error handling examples included
- [x] Complete documentation in repository

---

## ⚠️ Important Notes

1. **Production Endpoint**: The chatbot is deployed and running on AWS
2. **CORS**: Already enabled - no additional configuration needed
3. **Authentication**: No authentication required for these endpoints
4. **Rate Limiting**: Currently no rate limiting (can be added if needed)

---

## 🆘 Troubleshooting

If integration doesn't work:

1. **Check Health Endpoint**: Verify backend is running
2. **Check CORS**: Should work automatically, but verify browser console
3. **Check Network**: Ensure UI can reach the endpoint
4. **Check Request Format**: Must be JSON with `sender` and `message` fields

See `TROUBLESHOOTING.md` in the repository for more help.

---

## ✅ Summary

**YES, everything is there and it WILL work!**

- ✅ Production endpoint is live
- ✅ CORS is enabled
- ✅ Complete documentation
- ✅ Example code provided
- ✅ All necessary files in repository

Your developer can:
1. Clone the repository
2. Read the documentation
3. Use the production endpoint
4. Integrate immediately

**Repository**: https://github.com/PranDotAI1/Pran_bot_aws

