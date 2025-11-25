# API Endpoints Reference - PRAN Chatbot

Complete documentation of all API endpoints across all services in the PRAN Chatbot system.

---

## Table of Contents

1. [Flask Wrapper Server](#flask-wrapper-server)
2. [Rasa Backend Server](#rasa-backend-server)
3. [Rasa Actions Server](#rasa-actions-server)
4. [Custom REST Connector](#custom-rest-connector)
5. [Service Ports Summary](#service-ports-summary)
6. [Base URLs](#base-urls)

---

## Flask Wrapper Server

**Service**: Flask API Gateway  
**Port**: `5001`  
**Base URL (Local)**: `http://localhost:5001`  
**Base URL (Production)**: Configure based on deployment

### Endpoints

#### 1. Health Check
Check the health status of all services (Flask, Rasa, MongoDB).

```http
GET /health
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

#### 2. Send Message to Chatbot
Forward user messages to Rasa backend and return bot responses.

```http
POST /rasa-webhook
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What are the symptoms of diabetes?",
  "sender": "user_unique_id_123",
  "metadata": {}
}
```

**Response:**
```json
[
  {
    "text": "Common symptoms of diabetes include...",
    "recipient_id": "user_unique_id_123"
  }
]
```

**Status Codes:**
- `200` - Message processed successfully
- `400` - Invalid request body (no JSON data provided)
- `500` - Server error
- `503` - Failed to connect to Rasa

**Notes:**
- `sender` should be a unique identifier for each user/session
- Multiple responses possible (array)
- Forwards request to Rasa webhook endpoint

---

#### 3. MongoDB Connection Test
Test MongoDB connection and list available databases.

```http
GET /mongodb/test
```

**Response:**
```json
{
  "status": "success",
  "message": "MongoDB connection successful",
  "databases": ["pran_chatbot", "admin", "config"],
  "address": "('localhost', 27017)"
}
```

**Status Codes:**
- `200` - Connection successful
- `500` - Connection failed
- `503` - MongoDB not configured

---

#### 4. MongoDB Explore
Explore MongoDB structure: databases, collections, and sample data.

```http
GET /mongodb/explore
```

**Response:**
```json
{
  "status": "success",
  "connection": {
    "address": "('localhost', 27017)",
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

## Rasa Backend Server

**Service**: Rasa Core Server  
**Port**: `5005`  
**Base URL (Local)**: `http://localhost:5005`  
**Base URL (Production)**: Configure based on deployment

### Endpoints

#### 1. Chat Webhook
Main endpoint for sending messages to the chatbot and receiving responses.

```http
POST /webhooks/rest/webhook
Content-Type: application/json
```

**Request Body:**
```json
{
  "sender": "user_unique_id_123",
  "message": "Hello, how are you?"
}
```

**Response:**
```json
[
  {
    "text": "Hello! I'm doing well, thank you. How can I help you today?",
    "recipient_id": "user_unique_id_123"
  }
]
```

**Status Codes:**
- `200` - Message processed successfully
- `400` - Invalid request
- `500` - Server error

**Notes:**
- This is the primary chat interface endpoint
- Used internally by Flask wrapper server
- Supports multiple response messages

---

#### 2. Server Status
Check Rasa server status and health.

```http
GET /status
```

**Response:**
```json
{
  "version": "3.6.0",
  "status": "ok"
}
```

**Status Codes:**
- `200` - Server is running
- `503` - Server is down

---

#### 3. Health Check
Health check endpoint for container orchestration.

```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Unhealthy

---

#### 4. Parse Message
Parse user message to extract intent and entities (without generating response).

```http
POST /model/parse
Content-Type: application/json
```

**Request Body:**
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
  ],
  "text_tokens": [[0, 1], [2, 6], ...],
  "intent_ranking": [...]
}
```

**Status Codes:**
- `200` - Parse successful
- `400` - Invalid request
- `500` - Server error

**Notes:**
- Used for intent classification and entity extraction
- Does not generate bot response
- Useful for debugging and analytics

---

#### 5. Get Conversation Tracker
Retrieve conversation tracker state for a specific sender.

```http
GET /conversations/{sender_id}/tracker
```

**Parameters:**
- `sender_id` (path) - Unique user identifier

**Response:**
```json
{
  "sender_id": "user_unique_id_123",
  "slots": {
    "doctor_name": "Dr. Smith",
    "appointment_date": null
  },
  "latest_message": {
    "text": "I want to book an appointment",
    "intent": {...},
    "entities": [...]
  },
  "events": [...],
  "latest_event_time": 1234567890.0,
  "paused": false,
  "followup_action": null
}
```

**Status Codes:**
- `200` - Success
- `404` - Conversation not found
- `500` - Server error

---

#### 6. Append Events to Tracker
Add events to a conversation tracker.

```http
PUT /conversations/{sender_id}/tracker/events
Content-Type: application/json
```

**Request Body:**
```json
{
  "events": [
    {
      "event": "user",
      "text": "Hello",
      "timestamp": 1234567890.0
    }
  ]
}
```

**Status Codes:**
- `204` - Events added successfully
- `400` - Invalid events
- `500` - Server error

---

#### 7. Replace Tracker Events
Replace all events in a conversation tracker.

```http
PUT /conversations/{sender_id}/tracker/events
Content-Type: application/json
```

**Request Body:**
```json
{
  "events": [...],
  "execute_side_effects": true
}
```

**Status Codes:**
- `204` - Events replaced successfully
- `400` - Invalid events
- `500` - Server error

---

#### 8. Get Story
Retrieve a story by name.

```http
GET /story
```

**Query Parameters:**
- `story` - Story name

**Status Codes:**
- `200` - Success
- `404` - Story not found

---

#### 9. Get Version
Get Rasa server version information.

```http
GET /version
```

**Response:**
```json
{
  "version": "3.6.0",
  "minimum_compatible_version": "3.0.0"
}
```

---

## Rasa Actions Server

**Service**: Rasa Custom Actions Server  
**Port**: `5055`  
**Base URL (Local)**: `http://localhost:5055`  
**Base URL (Production)**: Configure based on deployment

### Endpoints

#### 1. Action Webhook
Endpoint for Rasa to call custom actions.

```http
POST /webhook
Content-Type: application/json
```

**Request Body:**
```json
{
  "next_action": "action_get_doctor_info",
  "sender_id": "user_unique_id_123",
  "tracker": {
    "sender_id": "user_unique_id_123",
    "slots": {...},
    "latest_message": {...},
    "events": [...]
  },
  "domain": {...},
  "version": "3.6.0"
}
```

**Response:**
```json
[
  {
    "text": "Here is the doctor information...",
    "recipient_id": "user_unique_id_123"
  }
]
```

**Status Codes:**
- `200` - Action executed successfully
- `400` - Invalid action request
- `500` - Action execution error

**Notes:**
- This endpoint is called internally by Rasa
- Custom actions are defined in `backend/app/actions/actions.py`
- Actions can return text responses, events, or dispatcher messages

---

#### 2. Health Check
Health check endpoint for actions server.

```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Unhealthy

---

## Custom REST Connector

**Service**: Custom Rasa Input Channel  
**Port**: `5005` (same as Rasa server)  
**Base URL**: `http://localhost:5005`

### Endpoints

#### 1. Custom Webhook
Custom REST webhook endpoint with enhanced response including intent and entity information.

```http
POST /webhook
Content-Type: application/json
```

**Request Body:**
```json
{
  "sender": "user_unique_id_123",
  "message": "I need help with diabetes"
}
```

**Response:**
```json
{
  "sender": "user_unique_id_123",
  "message": "I need help with diabetes",
  "intent": "ask_about_disease",
  "confidence": 0.92,
  "entities": [
    {
      "entity": "disease",
      "value": "diabetes",
      "start": 20,
      "end": 28
    }
  ],
  "bot_responses": [
    "Diabetes is a chronic condition that affects how your body processes blood sugar..."
  ]
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing sender or message
- `500` - Server error

**Notes:**
- Provides additional metadata (intent, confidence, entities) compared to standard webhook
- Uses custom REST input channel defined in `backend/app/custom_connectors/custom_rest.py`
- Internally calls `/model/parse` and `/webhooks/rest/webhook`

---

## Service Ports Summary

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Flask Wrapper | 5001 | HTTP | API Gateway |
| Rasa Backend | 5005 | HTTP | Chatbot Core |
| Rasa Actions | 5055 | HTTP | Custom Actions |
| MongoDB | 27017 | TCP | Database (if local) |

---

## Base URLs

### Local Development

```
Flask Wrapper:  http://localhost:5001
Rasa Backend:   http://localhost:5005
Rasa Actions:   http://localhost:5055
```

### Production

Production URLs should be configured based on your deployment:
- AWS ECS/EKS: Use load balancer URLs
- Docker Compose: Use service names (e.g., `http://flask-wrapper:5001`)
- Kubernetes: Use service names and ingress URLs

---

## Environment Variables

### Flask Wrapper Server
- `FLASK_HOST` - Host to bind (default: `0.0.0.0`)
- `FLASK_PORT` - Port to bind (default: `5001`)
- `FLASK_DEBUG` - Debug mode (default: `False`)
- `RASA_WEBHOOK_URL` - Rasa webhook URL (default: `http://localhost:5005/webhooks/rest/webhook`)
- `RASA_STATUS_URL` - Rasa status URL (default: `http://localhost:5005/status`)
- `MONGODB_URI` - MongoDB connection string

### Rasa Backend
- `ACTION_SERVER_URL` - Actions server URL (default: `http://localhost:5055/webhook`)
- `RASA_SERVER_URL` - Rasa server URL (default: `http://localhost:5005`)

### Rasa Actions
- `AWS_REGION` - AWS region for Bedrock
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AURORA_ENDPOINT` - Aurora database endpoint
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_PORT` - Database port
- `MONGODB_URI` - MongoDB connection string
- `BEDROCK_MODEL_ID` - Bedrock model ID
- `REACT_APP_DUMMY_API` - Dummy API URL

---

## Authentication

Currently, the API endpoints do not require authentication for local development. For production:

1. Implement API key authentication
2. Add JWT token validation
3. Configure CORS properly
4. Use HTTPS only

---

## Error Handling

All endpoints follow standard HTTP status codes:

- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

Error responses typically include:
```json
{
  "error": "Error message",
  "status_code": 500
}
```

---

## Rate Limiting

Rate limiting should be implemented in production:
- Flask endpoints: Use Flask-Limiter
- Rasa endpoints: Configure in Rasa settings
- Consider per-user and per-IP limits

---

## CORS Configuration

CORS is enabled for all Flask endpoints. For production:
- Configure allowed origins
- Set appropriate headers
- Handle preflight requests

---

## Testing Endpoints

### Using cURL

```bash
# Health check
curl http://localhost:5001/health

# Send message
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "sender": "test123"}'

# MongoDB test
curl http://localhost:5001/mongodb/test

# Rasa status
curl http://localhost:5005/status

# Parse message
curl -X POST http://localhost:5005/model/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello"}'
```

### Using Postman

1. Import collection (if available)
2. Set base URL: `http://localhost:5001` for Flask or `http://localhost:5005` for Rasa
3. Test each endpoint with appropriate request bodies

---

## Notes for Developers

1. **Primary Endpoint**: Use `/rasa-webhook` on Flask wrapper (port 5001) for frontend integration
2. **Direct Rasa Access**: Use `/webhooks/rest/webhook` on Rasa (port 5005) for direct integration
3. **Custom Connector**: Use `/webhook` on custom REST connector for enhanced responses with intent/entity info
4. **Health Monitoring**: Use `/health` endpoints for service monitoring
5. **MongoDB**: Use `/mongodb/test` and `/mongodb/explore` for database debugging

---

## Support

- **Repository**: Check project README.md
- **Documentation**: See `API_INTEGRATION_GUIDE.md` and `DEVELOPER_ONBOARDING.md`
- **Issues**: Report via project issue tracker

---

**Last Updated**: Generated automatically from codebase analysis  
**Version**: 1.0.0

