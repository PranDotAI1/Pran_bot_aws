# UI Developer Guide - Complete Setup

This guide is specifically for **UI developers** who need to integrate with the PRAN Chatbot backend.

## What You Need to Know

As a UI developer, you **don't need to run the backend yourself** - you just need to:
1. Know the API endpoint
2. Understand the request/response format
3. Integrate it into your frontend

However, if you want to test locally, you can also run the backend.

## Option 1: Use Existing Backend (Recommended)

If the backend is already running (deployed or running locally by backend team):

### API Endpoint
```
POST http://localhost:5001/rasa-webhook
```
(Replace `localhost:5001` with the actual backend URL in production)

### Request Format
```json
{
  "sender": "unique_user_id",
  "message": "Hello, I need a doctor"
}
```

### Response Format
```json
[
  {
    "recipient_id": "unique_user_id",
    "text": "Hello! I'm your healthcare assistant. How can I help you today?"
  }
]
```

### Health Check
```
GET http://localhost:5001/health
```

## Option 2: Run Backend Locally (For Testing)

If you need to test the backend yourself:

### Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/PranDotAI1/pran_chatbot.git
cd pran_chatbot
git checkout new_pran_bot_aws

# 2. Run automated setup
./setup_backend.sh

# 3. Start backend (2 terminals needed)
# Terminal 1:
source venv/bin/activate
cd backend/app
rasa run --enable-api --cors "*" --port 5005

# Terminal 2:
source venv/bin/activate
cd backend
python wrapper_server.py
```

See `DEVELOPER_SETUP_GUIDE.md` for detailed setup instructions.

## Frontend Integration Examples

### React/TypeScript Example

```typescript
// ChatbotService.ts
const CHATBOT_API_URL = process.env.REACT_APP_CHATBOT_API_URL || 'http://localhost:5001';

export interface ChatMessage {
  text: string;
  sender: 'user' | 'bot';
}

export class ChatbotService {
  async sendMessage(userId: string, message: string): Promise<string[]> {
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
      // Response is an array of message objects
      return data.map((msg: any) => msg.text);
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${CHATBOT_API_URL}/health`);
      const data = await response.json();
      return data.status === 'healthy';
    } catch {
      return false;
    }
  }
}
```

### React Hook Example

```typescript
// useChatbot.ts
import { useState } from 'react';

interface Message {
  text: string;
  sender: 'user' | 'bot';
}

export function useChatbot(userId: string = 'user123') {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    setLoading(true);
    setError(null);

    // Add user message immediately
    setMessages(prev => [...prev, { text: message, sender: 'user' }]);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_CHATBOT_API_URL || 'http://localhost:5001'}/rasa-webhook`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sender: userId,
            message: message,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const botResponses = await response.json();

      // Add bot responses
      botResponses.forEach((msg: any) => {
        setMessages(prev => [...prev, { text: msg.text, sender: 'bot' }]);
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setMessages(prev => [...prev, { 
        text: 'Sorry, I encountered an error. Please try again.', 
        sender: 'bot' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, sendMessage, loading, error };
}
```

### React Component Example

```tsx
// Chatbot.tsx
import React, { useState } from 'react';
import { useChatbot } from './useChatbot';

export function Chatbot() {
  const [input, setInput] = useState('');
  const { messages, sendMessage, loading } = useChatbot('user123');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    
    const message = input;
    setInput('');
    await sendMessage(message);
  };

  return (
    <div className="chatbot-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {loading && <div className="loading">Bot is typing...</div>}
      </div>
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
```

### Vue.js Example

```vue
<template>
  <div class="chatbot">
    <div class="messages">
      <div 
        v-for="(msg, idx) in messages" 
        :key="idx" 
        :class="['message', msg.sender]"
      >
        {{ msg.text }}
      </div>
    </div>
    
    <form @submit.prevent="sendMessage">
      <input 
        v-model="input" 
        placeholder="Type your message..."
        :disabled="loading"
      />
      <button type="submit" :disabled="loading || !input.trim()">
        Send
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const messages = ref([]);
const input = ref('');
const loading = ref(false);
const userId = 'user123';
const API_URL = process.env.VUE_APP_CHATBOT_API_URL || 'http://localhost:5001';

const sendMessage = async () => {
  if (!input.value.trim() || loading.value) return;
  
  const userMessage = input.value;
  messages.value.push({ text: userMessage, sender: 'user' });
  input.value = '';
  loading.value = true;

  try {
    const response = await fetch(`${API_URL}/rasa-webhook`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: userId,
        message: userMessage,
      }),
    });

    const botResponses = await response.json();
    botResponses.forEach(msg => {
      messages.value.push({ text: msg.text, sender: 'bot' });
    });
  } catch (error) {
    messages.value.push({ 
      text: 'Sorry, an error occurred. Please try again.', 
      sender: 'bot' 
    });
  } finally {
    loading.value = false;
  }
};
</script>
```

### Vanilla JavaScript Example

```javascript
// chatbot.js
const CHATBOT_API_URL = 'http://localhost:5001';
const userId = 'user123';

async function sendMessage(message) {
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

    const data = await response.json();
    return data.map(msg => msg.text);
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Usage
sendMessage('Hello')
  .then(responses => {
    responses.forEach(text => {
      console.log('Bot:', text);
      // Display in UI
    });
  })
  .catch(error => {
    console.error('Failed to send message:', error);
  });
```

## Environment Configuration

### For React
Add to `.env`:
```env
REACT_APP_CHATBOT_API_URL=http://localhost:5001
```

### For Vue
Add to `.env`:
```env
VUE_APP_CHATBOT_API_URL=http://localhost:5001
```

### For Production
```env
REACT_APP_CHATBOT_API_URL=https://your-production-domain.com
```

## CORS Configuration

✅ **CORS is already enabled** on the backend - you can make requests from any frontend domain.

For production, you may want to restrict CORS to specific domains (backend team can configure this).

## Error Handling

The API returns standard HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Invalid request format
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Backend services unavailable

**Error Response Format:**
```json
{
  "error": "Error message description"
}
```

## Testing the Integration

### 1. Test Health Endpoint
```bash
curl http://localhost:5001/health
```

Expected:
```json
{
  "status": "healthy",
  "flask_wrapper": "running",
  "rasa_status": "connected"
}
```

### 2. Test Chat Endpoint
```bash
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_user", "message": "Hello"}'
```

Expected:
```json
[
  {
    "recipient_id": "test_user",
    "text": "Hello! How can I help you?"
  }
]
```

## Common Issues

### 1. CORS Errors
- ✅ CORS is enabled by default
- If you see CORS errors, check that backend is running
- Verify the API URL is correct

### 2. Connection Refused
- Backend is not running
- Wrong port (should be 5001 for Flask wrapper)
- Check backend health: `curl http://localhost:5001/health`

### 3. 503 Service Unavailable
- Rasa server is not running
- Backend needs both Flask wrapper AND Rasa server running

### 4. Empty Response
- Check response format - it's an array, not a single object
- Use `response[0].text` or map over the array

## Best Practices

1. **Always check health before sending messages**
   ```typescript
   const isHealthy = await chatbot.checkHealth();
   if (!isHealthy) {
     // Show error to user
   }
   ```

2. **Handle loading states**
   - Show loading indicator while waiting for response
   - Disable input during request

3. **Error handling**
   - Always wrap API calls in try-catch
   - Show user-friendly error messages

4. **User ID management**
   - Use consistent user IDs (session ID, user ID, etc.)
   - Store in localStorage or session storage

5. **Message history**
   - Maintain conversation context
   - Consider storing messages locally

## Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check backend status |
| `/rasa-webhook` | POST | Send chat message |

**Request:**
```json
{
  "sender": "user_id",
  "message": "user message"
}
```

**Response:**
```json
[
  {
    "recipient_id": "user_id",
    "text": "bot response"
  }
]
```

## Need Help?

1. Check `UI_INTEGRATION_GUIDE.md` for more examples
2. Check `TROUBLESHOOTING.md` for backend issues
3. Verify backend is running: `curl http://localhost:5001/health`
4. Check browser console for errors
5. Verify API URL in environment variables

## Summary

- **API Endpoint:** `POST /rasa-webhook`
- **Base URL:** `http://localhost:5001` (or production URL)
- **CORS:** ✅ Enabled
- **Response:** Array of message objects
- **Health Check:** `GET /health`

You're ready to integrate! 🚀

