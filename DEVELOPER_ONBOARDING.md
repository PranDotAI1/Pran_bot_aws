# Developer Onboarding Guide - PRAN Chatbot

**Quick Start Guide for Frontend/Backend Integration**

---

## 🚀 Quick Start (5 Minutes)

### 1. Clone the Repository
```bash
git clone https://github.com/PranDotAI1/pran_chatbot.git
cd pran_chatbot
git checkout new_pran_bot_aws
```

### 2. Setup Backend (One Command)
```bash
chmod +x setup_backend.sh
./setup_backend.sh
```

### 3. Start Services (2 Terminals)

**Terminal 1 - Rasa Server:**
```bash
source venv/bin/activate
cd backend/app
rasa run --enable-api --cors "*" --port 5005
```

**Terminal 2 - Flask API:**
```bash
source venv/bin/activate
cd backend
python wrapper_server.py
```

### 4. Test Connection
```bash
curl http://localhost:5001/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "flask_wrapper": "running",
  "rasa_status": "connected",
  "mongodb_status": "connected"
}
```

---

## 📍 Repository Information

- **Repository**: `https://github.com/PranDotAI1/pran_chatbot.git`
- **Branch**: `new_pran_bot_aws`
- **Backend Port**: `5001` (Flask API)
- **Rasa Port**: `5005` (Internal)
- **Frontend Port**: `3000` (Your React app)

---

## 🔌 API Endpoints for Frontend Integration

### Base URL
```
http://localhost:5001  (Local)
https://your-aws-endpoint.com  (Production)
```

### 1. Health Check
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

### 2. Send Message to Chatbot
```http
POST /rasa-webhook
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Hello, I need help with my health",
  "sender": "user123"
}
```

**Response:**
```json
{
  "response": [
    {
      "text": "Hello! I'm here to help with your health questions. What would you like to know?",
      "recipient_id": "user123"
    }
  ],
  "metadata": {
    "timestamp": "2024-11-19T12:00:00Z"
  }
}
```

### 3. Get Conversation History
```http
GET /conversations/{sender_id}
```

**Response:**
```json
{
  "conversations": [
    {
      "message": "Hello",
      "response": "Hi there! How can I help?",
      "timestamp": "2024-11-19T12:00:00Z"
    }
  ]
}
```

### 4. Save Conversation
```http
POST /conversations
Content-Type: application/json
```

**Request Body:**
```json
{
  "sender_id": "user123",
  "message": "User message",
  "response": "Bot response",
  "metadata": {}
}
```

---

## 💻 Frontend Integration Example (React/TypeScript)

### 1. Install Dependencies
```bash
npm install axios
```

### 2. Create API Client (`src/api/chatbot.ts`)
```typescript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatMessage {
  message: string;
  sender: string;
}

export interface ChatResponse {
  response: Array<{
    text: string;
    recipient_id: string;
  }>;
  metadata?: {
    timestamp: string;
  };
}

export const chatbotAPI = {
  // Send message to chatbot
  sendMessage: async (message: string, senderId: string): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/rasa-webhook', {
      message,
      sender: senderId,
    });
    return response.data;
  },

  // Get conversation history
  getConversations: async (senderId: string) => {
    const response = await apiClient.get(`/conversations/${senderId}`);
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};
```

### 3. Use in React Component (`src/components/Chat.tsx`)
```typescript
import React, { useState } from 'react';
import { chatbotAPI } from '../api/chatbot';

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Array<{text: string, sender: 'user' | 'bot'}>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const senderId = 'user123'; // Generate unique ID for each user

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message to UI
    setMessages(prev => [...prev, { text: input, sender: 'user' }]);
    setInput('');
    setLoading(true);

    try {
      // Call backend API
      const response = await chatbotAPI.sendMessage(input, senderId);
      
      // Add bot response to UI
      if (response.response && response.response.length > 0) {
        setMessages(prev => [...prev, { 
          text: response.response[0].text, 
          sender: 'bot' 
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        text: 'Sorry, I encountered an error. Please try again.', 
        sender: 'bot' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default Chat;
```

---

## 📁 Key Files to Read

### Backend Files
1. **`backend/wrapper_server.py`** - Flask API server (main integration point)
2. **`backend/app/actions/actions.py`** - Bot logic and database queries
3. **`backend/app/config.yml`** - Rasa configuration
4. **`backend/app/domain.yml`** - Bot intents and responses

### Configuration
1. **`backend/.env.template`** - Environment variables needed
2. **`backend/app/requirements.txt`** - Python dependencies

### Documentation
1. **`DEVELOPER_SETUP_GUIDE.md`** - Detailed setup instructions
2. **`README.md`** - Project overview

---

## ⚙️ Environment Variables

Create `.env` file in `backend/` directory:

```env
# Database
DB_HOST=your-database-host
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_PORT=5432

# MongoDB
MONGODB_URI=mongodb://user:pass@host:port/db

# Rasa
RASA_SERVER_URL=http://localhost:5005
RASA_WEBHOOK_URL=http://localhost:5005/webhooks/rest/webhook

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
```

**Note**: For local development, you can start without database connections for basic testing.

---

## 🧪 Testing the Integration

### 1. Test Health Endpoint
```bash
curl http://localhost:5001/health
```

### 2. Test Chat Message
```bash
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "sender": "test_user"
  }'
```

### 3. Test from Frontend
```typescript
// In your React app
import { chatbotAPI } from './api/chatbot';

// Test connection
chatbotAPI.healthCheck().then(console.log);

// Test message
chatbotAPI.sendMessage('Hello', 'user123').then(console.log);
```

---

## 🔗 Integration Checklist

- [ ] Clone repository and checkout `new_pran_bot_aws` branch
- [ ] Run `setup_backend.sh` to install dependencies
- [ ] Start Rasa server (port 5005)
- [ ] Start Flask API (port 5001)
- [ ] Test health endpoint
- [ ] Create API client in frontend
- [ ] Integrate chat component
- [ ] Test message sending
- [ ] Test conversation history (if needed)
- [ ] Configure production API URL

---

## 🐛 Troubleshooting

### Backend not starting?
```bash
# Check if ports are available
lsof -i :5001
lsof -i :5005

# Check Python version (needs 3.9+)
python3 --version

# Reinstall dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
pip install -r app/requirements.txt
```

### API not responding?
```bash
# Check if services are running
curl http://localhost:5001/health

# Check Rasa status
curl http://localhost:5005/status

# Check logs
# Terminal 1: Rasa logs
# Terminal 2: Flask logs
```

### CORS errors?
- Flask wrapper already has CORS enabled
- Make sure frontend URL is allowed (currently set to `*`)

---

## 📞 Support

- **Repository**: `https://github.com/PranDotAI1/pran_chatbot`
- **Branch**: `new_pran_bot_aws`
- **Documentation**: See `DEVELOPER_SETUP_GUIDE.md` for detailed setup

---

## ✅ Quick Reference

**Backend API Base URL:**
- Local: `http://localhost:5001`
- Production: (Get from AWS deployment)

**Main Endpoints:**
- `GET /health` - Health check
- `POST /rasa-webhook` - Send message
- `GET /conversations/{sender_id}` - Get history
- `POST /conversations` - Save conversation

**Key Files:**
- `backend/wrapper_server.py` - API server
- `backend/app/actions/actions.py` - Bot logic
- `setup_backend.sh` - Setup script

---

**You're all set! Start integrating! 🚀**

