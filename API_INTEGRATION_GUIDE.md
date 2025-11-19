# API Integration Guide - PRAN Chatbot

**Complete API Reference for Frontend Integration**

---

## 🌐 Base URLs

- **Local Development**: `http://localhost:5001`
- **Production**: (Get from AWS deployment team)

---

## 📋 API Endpoints

### 1. Health Check
Check if the backend services are running.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "flask_wrapper": "running",
  "rasa_status": "connected",
  "mongodb_status": "connected"
}
```

**Status Codes:**
- `200` - All services healthy
- `503` - One or more services down

---

### 2. Send Message to Chatbot
Send a user message and get bot response.

```http
POST /rasa-webhook
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What are the symptoms of diabetes?",
  "sender": "user_unique_id_123"
}
```

**Response:**
```json
{
  "response": [
    {
      "text": "Common symptoms of diabetes include increased thirst, frequent urination, extreme fatigue, and blurred vision. Would you like more specific information?",
      "recipient_id": "user_unique_id_123"
    }
  ],
  "metadata": {
    "timestamp": "2024-11-19T12:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Message processed successfully
- `400` - Invalid request body
- `500` - Server error

**Notes:**
- `sender` should be a unique identifier for each user/session
- Multiple responses possible (array)
- Response includes metadata with timestamp

---

### 3. Get Conversation History
Retrieve all messages for a specific user.

```http
GET /conversations/{sender_id}
```

**Parameters:**
- `sender_id` (path) - Unique user identifier

**Response:**
```json
{
  "conversations": [
    {
      "message": "Hello",
      "response": "Hi! How can I help you today?",
      "timestamp": "2024-11-19T12:00:00Z",
      "metadata": {}
    },
    {
      "message": "What is diabetes?",
      "response": "Diabetes is a chronic condition...",
      "timestamp": "2024-11-19T12:01:00Z",
      "metadata": {}
    }
  ],
  "total": 2
}
```

**Status Codes:**
- `200` - Success
- `404` - User not found
- `500` - Server error

---

### 4. Save Conversation
Manually save a conversation (optional, usually auto-saved).

```http
POST /conversations
Content-Type: application/json
```

**Request Body:**
```json
{
  "sender_id": "user_unique_id_123",
  "message": "User message text",
  "response": "Bot response text",
  "metadata": {
    "intent": "ask_question",
    "confidence": 0.95
  }
}
```

**Response:**
```json
{
  "success": true,
  "conversation_id": "conv_123456",
  "message": "Conversation saved successfully"
}
```

**Status Codes:**
- `201` - Created successfully
- `400` - Invalid request
- `500` - Server error

---

### 5. MongoDB Test (Optional)
Test MongoDB connection (for debugging).

```http
GET /mongodb/test
```

**Response:**
```json
{
  "status": "connected",
  "database": "pran_chatbot",
  "collections": ["conversations", "users"]
}
```

---

## 💻 Code Examples

### JavaScript/TypeScript (Axios)

```typescript
import axios from 'axios';

const API_BASE = 'http://localhost:5001';

// Send message
const sendMessage = async (message: string, userId: string) => {
  try {
    const response = await axios.post(`${API_BASE}/rasa-webhook`, {
      message,
      sender: userId,
    });
    return response.data.response[0].text;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

// Get history
const getHistory = async (userId: string) => {
  try {
    const response = await axios.get(`${API_BASE}/conversations/${userId}`);
    return response.data.conversations;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

// Health check
const checkHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};
```

### React Hook Example

```typescript
import { useState, useCallback } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export const useChatbot = (userId: string) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_BASE}/rasa-webhook`, {
        message,
        sender: userId,
      });
      
      return response.data.response[0]?.text || 'No response';
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Failed to send message';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [userId]);

  return { sendMessage, loading, error };
};
```

### Fetch API (Vanilla JavaScript)

```javascript
const API_BASE = 'http://localhost:5001';

async function sendMessage(message, userId) {
  try {
    const response = await fetch(`${API_BASE}/rasa-webhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        sender: userId,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.response[0].text;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}
```

---

## 🔐 Authentication (If Required)

Currently, the API doesn't require authentication for local development. For production:

1. Add authentication headers if implemented
2. Include API keys if required
3. Handle CORS properly

**Example with Auth:**
```typescript
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`, // If implemented
  },
});
```

---

## 🎯 Best Practices

### 1. Error Handling
```typescript
try {
  const response = await sendMessage(message, userId);
  // Handle success
} catch (error) {
  if (error.response?.status === 500) {
    // Server error - show user-friendly message
    showError('Service temporarily unavailable. Please try again.');
  } else if (error.response?.status === 400) {
    // Bad request - check message format
    showError('Invalid message format.');
  } else {
    // Network error
    showError('Connection error. Please check your internet.');
  }
}
```

### 2. Loading States
```typescript
const [loading, setLoading] = useState(false);

const handleSend = async () => {
  setLoading(true);
  try {
    const response = await sendMessage(input, userId);
    // Update UI
  } finally {
    setLoading(false);
  }
};
```

### 3. User ID Management
```typescript
// Generate or retrieve unique user ID
const getUserId = () => {
  let userId = localStorage.getItem('chatbot_user_id');
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chatbot_user_id', userId);
  }
  return userId;
};
```

### 4. Message Formatting
```typescript
// Handle multiple responses
const handleResponse = (data: ChatResponse) => {
  if (data.response && data.response.length > 0) {
    // Display all responses
    data.response.forEach((resp) => {
      addMessage(resp.text, 'bot');
    });
  }
};
```

---

## 📊 Response Format

### Success Response Structure
```typescript
interface ChatResponse {
  response: Array<{
    text: string;
    recipient_id: string;
  }>;
  metadata?: {
    timestamp: string;
    intent?: string;
    confidence?: number;
  };
}
```

### Error Response Structure
```typescript
interface ErrorResponse {
  error: string;
  message: string;
  status_code: number;
}
```

---

## 🧪 Testing

### Using cURL
```bash
# Health check
curl http://localhost:5001/health

# Send message
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "sender": "test123"}'

# Get history
curl http://localhost:5001/conversations/test123
```

### Using Postman
1. Import collection (if available)
2. Set base URL: `http://localhost:5001`
3. Test each endpoint

---

## 🚀 Production Deployment

### Environment Variables
```env
REACT_APP_API_URL=https://your-production-api.com
```

### CORS Configuration
- Backend already configured for CORS
- Update allowed origins in production if needed

### Error Monitoring
- Implement error tracking (Sentry, etc.)
- Log API errors for debugging

---

## 📞 Support

- **Repository**: `https://github.com/PranDotAI1/pran_chatbot`
- **Branch**: `new_pran_bot_aws`
- **Documentation**: See `DEVELOPER_ONBOARDING.md`

---

**Ready to integrate! 🎉**

