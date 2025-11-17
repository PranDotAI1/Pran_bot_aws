# UI Developer - Quick Start (5 Minutes)

## For UI Developers Who Just Need the API

### 1. API Endpoint
```
POST http://localhost:5001/rasa-webhook
```

### 2. Request
```javascript
fetch('http://localhost:5001/rasa-webhook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sender: 'user123',
    message: 'Hello'
  })
})
```

### 3. Response
```javascript
// Response is an array
[
  {
    "recipient_id": "user123",
    "text": "Hello! How can I help you?"
  }
]

// Extract text:
const response = await fetch(...);
const messages = await response.json();
const botMessage = messages[0].text; // "Hello! How can I help you?"
```

### 4. Health Check
```javascript
fetch('http://localhost:5001/health')
  .then(r => r.json())
  .then(data => console.log(data.status)); // "healthy"
```

## That's It!

- ✅ CORS enabled (works from any frontend)
- ✅ No authentication needed for local testing
- ✅ Standard REST API

## Full Examples

See `UI_DEVELOPER_GUIDE.md` for:
- React/TypeScript examples
- Vue.js examples
- Error handling
- Loading states
- Complete integration patterns

## If Backend Isn't Running

Ask backend team, or see `DEVELOPER_SETUP_GUIDE.md` to run it yourself.

