# Quick Start for UI Developer

## 1. Clone Repository
```bash
git clone <repository-url>
cd New_Pran_bot_aws
```

## 2. Set Up Environment
```bash
cp .env.template .env
# Edit .env with your configuration
```

## 3. Start Backend (Option 1: Direct)
```bash
# Terminal 1: Start Rasa
cd backend/app
rasa run --enable-api --cors "*"

# Terminal 2: Start Flask Wrapper
cd backend
python wrapper_server.py
```

## 4. Start Backend (Option 2: Docker)
```bash
docker-compose up
```

## 5. Test API
```bash
# Health check
curl http://localhost:5001/health

# Send message
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "Hello"}'
```

## 6. Integrate in UI
```typescript
const response = await fetch('http://localhost:5001/rasa-webhook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sender: 'user_id',
    message: 'Hello'
  })
});
const messages = await response.json();
```

See `UI_INTEGRATION_GUIDE.md` for complete examples.
