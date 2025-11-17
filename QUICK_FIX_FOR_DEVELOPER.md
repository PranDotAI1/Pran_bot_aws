# Quick Fix for Developer - If Code Won't Run

## Immediate Steps

### 1. Run the Automated Setup Script

```bash
cd pran_chatbot  # or wherever you cloned it
git checkout new_pran_bot_aws
./setup_backend.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Train the Rasa model
- Create .env file

### 2. Create .env File (if script didn't work)

```bash
# Copy the example
cp .env.example .env

# Or copy from template
cp deployment/config/.env.template .env
```

**Minimum .env content for basic testing:**
```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
RASA_WEBHOOK_URL=http://localhost:5005/webhooks/rest/webhook
RASA_STATUS_URL=http://localhost:5005/status
```

### 3. Start Services

**Terminal 1:**
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
cd backend/app
rasa run --enable-api --cors "*" --port 5005
```

**Terminal 2:**
```bash
source venv/bin/activate
cd backend
python wrapper_server.py
```

### 4. Test

```bash
curl http://localhost:5001/health
```

## Common Quick Fixes

### "No module named 'rasa'"
```bash
source venv/bin/activate
pip install -r backend/app/requirements.txt
```

### "No model found"
```bash
cd backend/app
rasa train
```

### "Port already in use"
Change port in .env or kill the process using the port.

## Full Documentation

- `DEVELOPER_SETUP_GUIDE.md` - Complete step-by-step guide
- `TROUBLESHOOTING.md` - Detailed troubleshooting
- `SETUP.md` - Original setup instructions

