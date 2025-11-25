# Developer Setup Guide - Step by Step

This guide will help your UI developer (or any developer) get the chatbot backend running quickly.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

## Step 1: Clone the Repository

```bash
git clone https://github.com/PranDotAI1/pran_chatbot.git
cd pran_chatbot
git checkout new_pran_bot_aws
```

## Step 2: Create Environment File

```bash
# Copy the template
cp .env.template .env

# Edit the .env file (you can use nano, vim, or any text editor)
nano .env
```

**Minimum required for basic testing:**
```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
RASA_WEBHOOK_URL=http://localhost:5005/webhooks/rest/webhook
RASA_STATUS_URL=http://localhost:5005/status
```

**Note:** You can leave AWS and database fields empty for basic testing. The app will work without them (some features won't be available).

## Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Flask wrapper dependencies
cd backend
pip install -r requirements.txt

# Install Rasa dependencies
pip install -r app/requirements.txt
```

## Step 4: Train Rasa Model (Required First Time)

```bash
cd backend/app

# Train the Rasa model
rasa train

# This will create a model in the models/ directory
```

**Expected output:** You should see "Your Rasa model is trained and saved" at the end.

## Step 5: Start the Services

You need **2 terminals** running:

### Terminal 1: Start Rasa Server

```bash
cd backend/app
rasa run --enable-api --cors "*" --port 5005
```

**Expected output:** You should see "Starting Rasa server on http://0.0.0.0:5005"

### Terminal 2: Start Flask Wrapper

```bash
cd backend
python wrapper_server.py
```

**Expected output:** You should see "Running on http://0.0.0.0:5001"

## Step 6: Test the API

Open a **third terminal** and test:

```bash
# Test health endpoint
curl http://localhost:5001/health

# Test chatbot
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_user", "message": "Hello"}'
```

## Common Issues & Solutions

### Issue 1: "Module not found" errors

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r backend/requirements.txt
pip install -r backend/app/requirements.txt
```

### Issue 2: "No model found" or Rasa errors

**Solution:**
```bash
cd backend/app
rasa train
```

### Issue 3: Port already in use

**Solution:**
```bash
# Find what's using the port
lsof -i :5001  # or :5005

# Kill the process or change ports in .env
```

### Issue 4: "Connection refused" when testing

**Solution:**
- Make sure both terminals are running (Rasa and Flask)
- Check that services started without errors
- Verify ports in .env match what you're using

### Issue 5: Import errors in actions

**Solution:**
```bash
# Make sure you're in the right directory
cd backend/app

# Install actions dependencies
pip install -r requirements.txt
```

## Quick Test Script

Save this as `test_backend.sh`:

```bash
#!/bin/bash
echo "Testing backend..."

# Test health
echo "1. Testing health endpoint..."
curl -s http://localhost:5001/health | python -m json.tool

# Test chat
echo -e "\n2. Testing chat endpoint..."
curl -s -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "Hello"}' | python -m json.tool
```

Run with: `chmod +x test_backend.sh && ./test_backend.sh`

## For UI Integration

Once the backend is running:

1. **API Endpoint:** `http://localhost:5001/rasa-webhook`
2. **Health Check:** `http://localhost:5001/health`
3. **CORS:** Already enabled, works from any frontend

See `UI_INTEGRATION_GUIDE.md` for complete integration examples.

## Need Help?

1. Check error messages in the terminal
2. Verify all steps were completed
3. Check that ports 5001 and 5005 are available
4. Review `SETUP.md` for more details

