# UI Integration Guide - New Pran Bot AWS

## Quick Start for UI Developers

This guide provides everything your UI developer needs to integrate with the chatbot backend.

## Repository Status

✅ **READY TO PUSH** - All checks passed (0 errors, 1 acceptable warning)

## API Endpoint for UI

### Primary Chat Endpoint

**URL**: `POST /rasa-webhook`

**Base URL Examples**:
- Local Development: `http://localhost:5001/rasa-webhook`
- Production: `https://your-domain.com/rasa-webhook`

**Request Format**:
```json
{
  "sender": "unique_user_id",
  "message": "Hello, I need a doctor",
  "metadata": {}  // Optional
}
```

**Response Format**:
```json
[
  {
    "recipient_id": "unique_user_id",
    "text": "Hello! I'm your healthcare assistant. How can I help you today?"
  }
]
```

**Note**: Response is an array of message objects. Each object contains:
- `recipient_id`: The sender ID you provided
- `text`: The bot's response message

## Example Integration Code

### JavaScript/TypeScript (React/Vue/Angular)

```typescript
// API Configuration
const CHATBOT_API_URL = process.env.REACT_APP_CHATBOT_API_URL || 'http://localhost:5001';

// Send message to chatbot
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
    return data; // Array of message objects
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

// Usage example
const messages = await sendMessage('user123', 'I need to book an appointment');
messages.forEach(msg => {
  console.log('Bot:', msg.text);
});
```

### React Hook Example

```typescript
import { useState } from 'react';

function useChatbot() {
  const [messages, setMessages] = useState<Array<{text: string, sender: string}>>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (userId: string, message: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_CHATBOT_API_URL}/rasa-webhook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender: userId, message }),
      });
      
      const botResponses = await response.json();
      
      // Add user message
      setMessages(prev => [...prev, { text: message, sender: 'user' }]);
      
      // Add bot responses
      botResponses.forEach((msg: any) => {
        setMessages(prev => [...prev, { text: msg.text, sender: 'bot' }]);
      });
    } catch (error) {
      console.error('Chatbot error:', error);
    } finally {
      setLoading(false);
    }
  };

  return { messages, sendMessage, loading };
}
```

## CORS Configuration

✅ **CORS is enabled** - The Flask wrapper has CORS enabled for all routes:
```python
from flask_cors import CORS
CORS(app)  # Allows all origins
```

For production, you can configure specific origins in the environment:
```python
CORS(app, origins=["https://your-frontend-domain.com"])
```

## Health Check Endpoint

**URL**: `GET /health`

Use this to verify the backend is running before making chat requests:

```typescript
async function checkBackendHealth() {
  const response = await fetch(`${CHATBOT_API_URL}/health`);
  const data = await response.json();
  return data.status === 'healthy';
}
```

**Response**:
```json
{
  "status": "healthy",
  "flask_wrapper": "running",
  "rasa_status": "connected",
  "mongodb_status": "connected",
  "rasa_webhook_url": "http://localhost:5005/webhooks/rest/webhook"
}
```

## Environment Variables for UI

Add to your UI's `.env` file:

```env
REACT_APP_CHATBOT_API_URL=http://localhost:5001
# Or for production:
# REACT_APP_CHATBOT_API_URL=https://your-production-domain.com
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request format
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Backend services unavailable

**Error Response Format**:
```json
{
  "error": "Error message description"
}
```

## Complete Integration Example

```typescript
// ChatbotService.ts
class ChatbotService {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.REACT_APP_CHATBOT_API_URL || 'http://localhost:5001') {
    this.baseUrl = baseUrl;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      const data = await response.json();
      return data.status === 'healthy';
    } catch {
      return false;
    }
  }

  async sendMessage(userId: string, message: string): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/rasa-webhook`, {
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
      const error = await response.json();
      throw new Error(error.error || 'Failed to send message');
    }

    const messages = await response.json();
    return messages.map((msg: any) => msg.text);
  }
}

// Usage
const chatbot = new ChatbotService();
const responses = await chatbot.sendMessage('user123', 'Hello');
responses.forEach(text => console.log('Bot:', text));
```

## Testing the Integration

### 1. Start the Backend

```bash
cd New_Pran_bot_aws/backend
python wrapper_server.py
```

The server will start on `http://localhost:5001`

### 2. Test with cURL

```bash
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user",
    "message": "Hello"
  }'
```

### 3. Test Health Endpoint

```bash
curl http://localhost:5001/health
```

## Common Use Cases

### 1. Simple Chat Interface

```typescript
const [input, setInput] = useState('');
const [chatHistory, setChatHistory] = useState<Array<{sender: string, text: string}>>([]);

const handleSend = async () => {
  if (!input.trim()) return;
  
  // Add user message to chat
  setChatHistory(prev => [...prev, { sender: 'user', text: input }]);
  
  // Send to backend
  const responses = await chatbot.sendMessage('user123', input);
  
  // Add bot responses
  responses.forEach(text => {
    setChatHistory(prev => [...prev, { sender: 'bot', text }]);
  });
  
  setInput('');
};
```

### 2. Loading States

```typescript
const [loading, setLoading] = useState(false);

const handleSend = async () => {
  setLoading(true);
  try {
    const responses = await chatbot.sendMessage(userId, message);
    // Handle responses
  } finally {
    setLoading(false);
  }
};
```

### 3. Error Handling

```typescript
try {
  const responses = await chatbot.sendMessage(userId, message);
  // Success
} catch (error) {
  // Show error message to user
  console.error('Chatbot error:', error);
  // Display: "Sorry, I'm having trouble connecting. Please try again."
}
```

## Production Deployment

### 1. Update API URL

Set the production API URL in your UI's environment:
```env
REACT_APP_CHATBOT_API_URL=https://api.yourdomain.com
```

### 2. Configure CORS

If needed, update CORS in `wrapper_server.py`:
```python
CORS(app, origins=["https://your-frontend-domain.com"])
```

### 3. SSL/HTTPS

Ensure both frontend and backend use HTTPS in production.

## Troubleshooting

### Issue: CORS Error
**Solution**: CORS is already enabled. If you still see errors, check:
- Backend is running
- Correct API URL
- Network connectivity

### Issue: 503 Service Unavailable
**Solution**: 
- Check if Rasa backend is running
- Verify health endpoint: `GET /health`
- Check backend logs

### Issue: Empty Response
**Solution**:
- Verify request format (sender and message required)
- Check backend logs for errors
- Ensure Rasa model is loaded

## Support

For integration issues:
1. Check backend health: `GET /health`
2. Review backend logs
3. Verify API endpoint URL
4. Check network connectivity

## Next Steps

1. ✅ Repository is ready to push
2. ✅ Backend API is ready (`/rasa-webhook`)
3. ✅ CORS is configured
4. ✅ Health check available
5. ⚠️ UI developer needs to:
   - Set `REACT_APP_CHATBOT_API_URL` environment variable
   - Implement the API calls as shown above
   - Handle responses (array of message objects)

---

**The backend is production-ready and fully compatible with UI integration!**

