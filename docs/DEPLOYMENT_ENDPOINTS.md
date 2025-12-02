# Deployment Endpoints Documentation

**PRAN Chatbot AWS - Complete API Endpoints Reference**

This document provides detailed information about all deployment endpoints, API URLs, and integration points for the PRAN Chatbot system deployed on AWS.

---

## 📋 Table of Contents

1. [Production Endpoints](#production-endpoints)
2. [Local Development Endpoints](#local-development-endpoints)
3. [Flask Wrapper API Gateway](#flask-wrapper-api-gateway)
4. [Rasa Backend Server](#rasa-backend-server)
5. [Rasa Actions Server](#rasa-actions-server)
6. [Service Architecture](#service-architecture)
7. [Environment Configuration](#environment-configuration)
8. [Testing & Verification](#testing--verification)
9. [Security & Authentication](#security--authentication)

---

## 🌐 Production Endpoints

### Production Base URL

**Application Load Balancer (ALB):**
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080
```

**Region:** `us-east-1`  
**Port:** `8080`  
**Protocol:** `HTTP` (HTTPS can be configured with SSL certificate)

---

### Production API Endpoints

#### 1. Health Check
**Endpoint:** `GET /health`

**Full URL:**
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/health
```

**Request:**
```bash
curl http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "flask_wrapper": "running",
  "rasa_status": "connected",
  "mongodb_status": "connected",
  "rasa_webhook_url": "http://localhost:5005/webhooks/rest/webhook"
}
```

**Status Codes:**
- `200` - All services healthy
- `503` - One or more services down

---

#### 2. Chatbot Webhook (Primary Endpoint)
**Endpoint:** `POST /rasa-webhook`

**Full URL:**
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook
```

**Request:**
```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "user_unique_id_123",
    "message": "Hello, I need help with diabetes",
    "metadata": {}
  }'
```

**Request Body:**
```json
{
  "sender": "user_unique_id_123",
  "message": "Hello, I need help with diabetes",
  "metadata": {}
}
```

**Response:**
```json
[
  {
    "text": "Hello! I'm here to help you with diabetes-related questions...",
    "recipient_id": "user_unique_id_123"
  }
]
```

**Status Codes:**
- `200` - Message processed successfully
- `400` - Invalid request body
- `500` - Server error
- `503` - Failed to connect to Rasa backend

**Notes:**
- This is the **primary endpoint** for frontend integration
- `sender` should be a unique identifier for each user/session
- Supports multi-turn conversations
- Returns array of responses (bot can send multiple messages)

---

#### 3. MongoDB Connection Test
**Endpoint:** `GET /mongodb/test`

**Full URL:**
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/mongodb/test
```

**Request:**
```bash
curl http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/mongodb/test
```

**Response:**
```json
{
  "status": "success",
  "message": "MongoDB connection successful",
  "databases": ["pran_chatbot", "admin", "config"],
  "address": "('documentdb-cluster.cluster-xxxxx.us-east-1.docdb.amazonaws.com', 27017)"
}
```

**Status Codes:**
- `200` - Connection successful
- `500` - Connection failed
- `503` - MongoDB not configured

---

#### 4. MongoDB Explore
**Endpoint:** `GET /mongodb/explore`

**Full URL:**
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/mongodb/explore
```

**Request:**
```bash
curl http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/mongodb/explore
```

**Response:**
```json
{
  "status": "success",
  "connection": {
    "address": "('documentdb-cluster.cluster-xxxxx.us-east-1.docdb.amazonaws.com', 27017)",
    "total_databases": 5,
    "user_databases": 2
  },
  "databases": [
    {
      "name": "pran_chatbot",
      "collections_count": 3,
      "collections": [
        {
          "name": "conversations",
          "document_count": 150,
          "fields": ["_id", "sender", "message", "response", "timestamp"],
          "sample_documents": [...]
        }
      ]
    }
  ]
}
```

**Status Codes:**
- `200` - Exploration successful
- `500` - Error exploring MongoDB
- `503` - MongoDB not configured

---

## 💻 Local Development Endpoints

### Local Base URLs

**Flask Wrapper (API Gateway):**
```
http://localhost:5001
```

**Rasa Backend Server:**
```
http://localhost:5005
```

**Rasa Actions Server:**
```
http://localhost:5055
```

---

### Local Development API Endpoints

#### Flask Wrapper Endpoints (Port 5001)

**1. Health Check**
```
GET http://localhost:5001/health
```

**2. Chatbot Webhook**
```
POST http://localhost:5001/rasa-webhook
```

**3. MongoDB Test**
```
GET http://localhost:5001/mongodb/test
```

**4. MongoDB Explore**
```
GET http://localhost:5001/mongodb/explore
```

---

#### Rasa Backend Endpoints (Port 5005)

**1. Chat Webhook (Direct)**
```
POST http://localhost:5005/webhooks/rest/webhook
```

**Request:**
```json
{
  "sender": "user_unique_id_123",
  "message": "Hello"
}
```

**2. Server Status**
```
GET http://localhost:5005/status
```

**3. Health Check**
```
GET http://localhost:5005/health
```

**4. Parse Message (Intent & Entity Extraction)**
```
POST http://localhost:5005/model/parse
```

**Request:**
```json
{
  "text": "I want to book an appointment with Dr. Smith"
}
```

**Response:**
```json
{
  "text": "I want to book an appointment with Dr. Smith",
  "intent": {
    "name": "book_appointment",
    "confidence": 0.95
  },
  "entities": [
    {
      "entity": "doctor_name",
      "value": "Dr. Smith",
      "start": 35,
      "end": 44,
      "confidence": 0.98
    }
  ]
}
```

**5. Get Conversation Tracker**
```
GET http://localhost:5005/conversations/{sender_id}/tracker
```

**6. Append Events to Tracker**
```
PUT http://localhost:5005/conversations/{sender_id}/tracker/events
```

**7. Get Version**
```
GET http://localhost:5005/version
```

---

#### Rasa Actions Server Endpoints (Port 5055)

**1. Action Webhook (Internal)**
```
POST http://localhost:5055/webhook
```

**Note:** This endpoint is called internally by Rasa, not directly by clients.

**2. Health Check**
```
GET http://localhost:5055/health
```

---

## 🔧 Flask Wrapper API Gateway

### Service Details

- **Service Name:** Flask Wrapper Server
- **Port:** `5001` (local), `8080` (production via ALB)
- **Protocol:** HTTP
- **Purpose:** API Gateway that forwards requests to Rasa backend

### Endpoint Specifications

#### POST /rasa-webhook

**Description:** Primary endpoint for chatbot interactions. Forwards user messages to Rasa backend and returns bot responses.

**Headers:**
```
Content-Type: application/json
```

**Request Body Schema:**
```json
{
  "sender": "string (required) - Unique user/session identifier",
  "message": "string (required) - User message text",
  "metadata": "object (optional) - Additional metadata"
}
```

**Response Schema:**
```json
[
  {
    "text": "string - Bot response message",
    "recipient_id": "string - User identifier"
  }
]
```

**Example Request:**
```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "user_12345",
    "message": "What are the symptoms of diabetes?",
    "metadata": {
      "source": "web",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }'
```

**Example Response:**
```json
[
  {
    "text": "Common symptoms of diabetes include increased thirst, frequent urination, extreme fatigue, blurred vision, and slow-healing sores. Would you like more information about any specific symptom?",
    "recipient_id": "user_12345"
  }
]
```

---

#### GET /health

**Description:** Comprehensive health check for all services (Flask, Rasa, MongoDB).

**Response Schema:**
```json
{
  "status": "healthy | unhealthy",
  "flask_wrapper": "running | stopped",
  "rasa_status": "connected | disconnected",
  "mongodb_status": "connected | disconnected | not_configured",
  "rasa_webhook_url": "string - Internal Rasa webhook URL"
}
```

---

#### GET /mongodb/test

**Description:** Test MongoDB connection and list available databases.

**Response Schema:**
```json
{
  "status": "success | error",
  "message": "string - Status message",
  "databases": ["string - Array of database names"],
  "address": "string - MongoDB connection address"
}
```

---

#### GET /mongodb/explore

**Description:** Explore MongoDB structure including databases, collections, document counts, and sample data.

**Response Schema:**
```json
{
  "status": "success | error",
  "connection": {
    "address": "string",
    "total_databases": "number",
    "user_databases": "number"
  },
  "databases": [
    {
      "name": "string",
      "collections_count": "number",
      "collections": [
        {
          "name": "string",
          "document_count": "number",
          "fields": ["string"],
          "sample_documents": ["object"]
        }
      ]
    }
  ]
}
```

---

## 🤖 Rasa Backend Server

### Service Details

- **Service Name:** Rasa Core Server
- **Port:** `5005`
- **Protocol:** HTTP
- **Purpose:** Chatbot core engine with NLU and dialogue management

### Key Endpoints

#### POST /webhooks/rest/webhook

**Description:** Main Rasa webhook for chat interactions. Called internally by Flask wrapper.

**Request Body:**
```json
{
  "sender": "string - User identifier",
  "message": "string - User message"
}
```

**Response:**
```json
[
  {
    "text": "string - Bot response",
    "recipient_id": "string - User identifier"
  }
]
```

---

#### POST /model/parse

**Description:** Parse user message to extract intent and entities without generating response.

**Request Body:**
```json
{
  "text": "string - User message"
}
```

**Response:**
```json
{
  "text": "string - Original message",
  "intent": {
    "name": "string - Intent name",
    "confidence": "number - Confidence score (0-1)"
  },
  "entities": [
    {
      "entity": "string - Entity type",
      "value": "string - Entity value",
      "start": "number - Start position",
      "end": "number - End position",
      "confidence": "number - Confidence score"
    }
  ],
  "intent_ranking": [
    {
      "name": "string",
      "confidence": "number"
    }
  ]
}
```

---

#### GET /conversations/{sender_id}/tracker

**Description:** Retrieve conversation tracker state for a specific user.

**Path Parameters:**
- `sender_id` (string, required) - Unique user identifier

**Response:**
```json
{
  "sender_id": "string",
  "slots": {
    "slot_name": "slot_value"
  },
  "latest_message": {
    "text": "string",
    "intent": {...},
    "entities": [...]
  },
  "events": [...],
  "latest_event_time": "number - Unix timestamp",
  "paused": "boolean",
  "followup_action": "string | null"
}
```

---

## ⚙️ Rasa Actions Server

### Service Details

- **Service Name:** Rasa Custom Actions Server
- **Port:** `5055`
- **Protocol:** HTTP
- **Purpose:** Execute custom actions (AWS Bedrock, database queries, etc.)

### Key Endpoints

#### POST /webhook

**Description:** Internal endpoint called by Rasa to execute custom actions. Not meant for direct client access.

**Request Body:**
```json
{
  "next_action": "string - Action name",
  "sender_id": "string - User identifier",
  "tracker": {
    "sender_id": "string",
    "slots": {...},
    "latest_message": {...},
    "events": [...]
  },
  "domain": {...},
  "version": "string - Rasa version"
}
```

**Response:**
```json
[
  {
    "text": "string - Action response",
    "recipient_id": "string - User identifier"
  }
]
```

**Available Custom Actions:**
- `action_aws_bedrock_chat` - Intelligent conversational responses using AWS Bedrock
- `action_get_doctor_info` - Retrieve doctor information
- `action_get_patient_info` - Retrieve patient information
- `action_get_appointments` - Get appointment details
- `action_get_insurance_plans` - Get insurance plan information
- `action_save_conversation_history` - Save conversation to database
- `action_get_conversation_history` - Retrieve conversation history

---

## 🏗️ Service Architecture

### Production Deployment (AWS ECS Fargate)

```
Internet
   │
   ▼
Application Load Balancer (ALB)
   │ Port: 8080
   │ http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080
   │
   ├──► Flask Wrapper Container (Port 5001)
   │       │
   │       ├──► /health
   │       ├──► /rasa-webhook (Primary)
   │       ├──► /mongodb/test
   │       └──► /mongodb/explore
   │
   └──► Rasa Backend Container (Port 5005)
           │
           ├──► /webhooks/rest/webhook
           ├──► /status
           ├──► /health
           ├──► /model/parse
           └──► /conversations/{sender_id}/tracker
           │
           └──► Rasa Actions Container (Port 5055)
                   │
                   └──► /webhook (Internal)
```

### Internal Service Communication

Within ECS Task (same task definition):
- Flask Wrapper → Rasa Backend: `http://localhost:5005/webhooks/rest/webhook`
- Rasa Backend → Actions Server: `http://localhost:5055/webhook`

### External Dependencies

- **AWS Bedrock:** `us-east-1` (Claude 3.5 Sonnet model)
- **AWS Comprehend Medical:** `us-east-1`
- **AWS Comprehend:** `us-east-1`
- **Aurora PostgreSQL:** Managed database endpoint
- **DocumentDB (MongoDB):** Managed database endpoint

---

## 🔐 Environment Configuration

### Flask Wrapper Environment Variables

```bash
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=False
RASA_WEBHOOK_URL=http://localhost:5005/webhooks/rest/webhook
RASA_STATUS_URL=http://localhost:5005/status
MONGODB_URI=mongodb://user:password@documentdb-endpoint:27017/pran_chatbot?ssl=true&replicaSet=rs0
```

### Rasa Backend Environment Variables

```bash
ACTION_SERVER_URL=http://localhost:5055/webhook
RASA_SERVER_URL=http://localhost:5005
```

### Rasa Actions Environment Variables

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AURORA_ENDPOINT=your-aurora-endpoint.region.rds.amazonaws.com
DB_NAME=pran_chatbot
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_PORT=5432
MONGODB_URI=mongodb://user:password@documentdb-endpoint:27017/pran_chatbot?ssl=true&replicaSet=rs0
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

---

## 🧪 Testing & Verification

### Production Endpoint Testing

#### 1. Health Check Test
```bash
curl -v http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/health
```

**Expected:** HTTP 200 with healthy status

#### 2. Chatbot Message Test
```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user_001",
    "message": "Hello"
  }'
```

**Expected:** HTTP 200 with bot response array

#### 3. MongoDB Connection Test
```bash
curl http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/mongodb/test
```

**Expected:** HTTP 200 with MongoDB connection status

---

### Local Development Testing

#### 1. Start Services
```bash
# Using Docker Compose
docker-compose up -d

# Or manually
# Terminal 1: Rasa Backend
cd backend/app
rasa run --enable-api --cors "*" --port 5005

# Terminal 2: Rasa Actions
cd backend/app
python -m rasa_sdk --actions actions --port 5055

# Terminal 3: Flask Wrapper
cd backend
python wrapper_server.py
```

#### 2. Test Health Endpoint
```bash
curl http://localhost:5001/health
```

#### 3. Test Chatbot
```bash
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "Hello"}'
```

#### 4. Test Rasa Directly
```bash
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "Hello"}'
```

---

## 🔒 Security & Authentication

### Current Status

- **Authentication:** Not implemented (public endpoints)
- **HTTPS:** Not configured (HTTP only)
- **CORS:** Enabled for all origins (`*`)

### Production Recommendations

1. **Enable HTTPS:**
   - Configure SSL certificate in ALB
   - Update base URL to use `https://`
   - Redirect HTTP to HTTPS

2. **Implement Authentication:**
   - API Key authentication
   - JWT token validation
   - OAuth 2.0 integration

3. **Configure CORS:**
   - Restrict allowed origins
   - Set appropriate headers
   - Handle preflight requests

4. **Rate Limiting:**
   - Implement per-IP rate limits
   - Implement per-user rate limits
   - Use AWS WAF for DDoS protection

5. **Network Security:**
   - Use VPC for internal communication
   - Configure security groups
   - Enable AWS Shield for DDoS protection

---

## 📊 Service Ports Summary

| Service | Local Port | Production Port | Protocol | Purpose |
|---------|-----------|-----------------|----------|---------|
| Flask Wrapper | 5001 | 8080 (via ALB) | HTTP | API Gateway |
| Rasa Backend | 5005 | 5005 (internal) | HTTP | Chatbot Core |
| Rasa Actions | 5055 | 5055 (internal) | HTTP | Custom Actions |
| MongoDB | 27017 | 27017 (internal) | TCP | Database |
| PostgreSQL | 5432 | 5432 (internal) | TCP | Database |

---

## 🔄 API Request/Response Flow

### Complete Request Flow

```
1. Client Request
   POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook
   {
     "sender": "user_123",
     "message": "I need help with diabetes"
   }

2. Application Load Balancer
   → Routes to Flask Wrapper Container (Port 5001)

3. Flask Wrapper (/rasa-webhook)
   → Forwards to Rasa Backend
   POST http://localhost:5005/webhooks/rest/webhook
   {
     "sender": "user_123",
     "message": "I need help with diabetes"
   }

4. Rasa Backend
   → Processes message (NLU, dialogue management)
   → Calls custom action if needed
   POST http://localhost:5055/webhook
   {
     "next_action": "action_aws_bedrock_chat",
     "sender_id": "user_123",
     "tracker": {...}
   }

5. Rasa Actions Server
   → Executes action_aws_bedrock_chat
   → Calls AWS Bedrock API
   → Returns response

6. Rasa Backend
   → Generates final response
   → Returns to Flask Wrapper

7. Flask Wrapper
   → Returns to client

8. Client Response
   [
     {
       "text": "I'd be happy to help you with diabetes-related questions...",
       "recipient_id": "user_123"
     }
   ]
```

---

## 📝 Integration Examples

### JavaScript/TypeScript (Frontend)

```javascript
const API_BASE_URL = 'http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080';

// Send message to chatbot
async function sendMessage(userId, message) {
  const response = await fetch(`${API_BASE_URL}/rasa-webhook`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sender: userId,
      message: message,
      metadata: {
        source: 'web',
        timestamp: new Date().toISOString()
      }
    })
  });
  
  const data = await response.json();
  return data; // Array of bot responses
}

// Health check
async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  const data = await response.json();
  return data;
}
```

### Python (Backend Integration)

```python
import requests

API_BASE_URL = 'http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080'

def send_message(user_id, message):
    """Send message to chatbot and get response"""
    response = requests.post(
        f'{API_BASE_URL}/rasa-webhook',
        json={
            'sender': user_id,
            'message': message,
            'metadata': {}
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json()  # Returns list of bot responses

def check_health():
    """Check service health"""
    response = requests.get(f'{API_BASE_URL}/health')
    response.raise_for_status()
    return response.json()
```

### cURL (Command Line)

```bash
# Health check
curl http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/health

# Send message
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "user_12345",
    "message": "What are the symptoms of diabetes?"
  }'

# MongoDB test
curl http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/mongodb/test
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Connection Timeout
**Symptom:** Request times out or connection refused

**Solutions:**
- Verify ALB is running and healthy
- Check security group rules allow traffic on port 8080
- Verify ECS tasks are running
- Check CloudWatch logs for errors

#### 2. 503 Service Unavailable
**Symptom:** Health check returns 503

**Solutions:**
- Check Rasa backend is running: `curl http://localhost:5005/status`
- Check Actions server is running: `curl http://localhost:5055/health`
- Verify MongoDB connection
- Check ECS task logs in CloudWatch

#### 3. Empty Response
**Symptom:** Request succeeds but returns empty array

**Solutions:**
- Check Rasa model is trained and loaded
- Verify custom actions are registered
- Check action server logs for errors
- Verify AWS Bedrock access and credentials

#### 4. CORS Errors (Frontend)
**Symptom:** CORS policy errors in browser

**Solutions:**
- Verify CORS is enabled in Flask wrapper
- Check allowed origins configuration
- Ensure proper headers are set

---

## 📚 Additional Resources

- **Repository:** https://github.com/PranDotAI1/Pran_bot_aws.git
- **API Reference:** `docs/API_ENDPOINTS_REFERENCE.md`
- **Developer Guide:** `docs/DEVELOPER_SETUP_GUIDE.md`
- **Deployment Guide:** `docs/DEPLOYMENT_GUIDE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

---

## 📅 Document Information

**Last Updated:** 2024-01-15  
**Version:** 1.0.0  
**Maintained By:** PRAN Chatbot Development Team

**Production Endpoint:**
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080
```

**For Support:**
- Check CloudWatch logs for detailed error messages
- Review ECS task definitions and service configurations
- Verify AWS service permissions and access

---

**Note:** This document reflects the current production deployment. Endpoints and URLs may change with infrastructure updates. Always verify endpoints before integration.

