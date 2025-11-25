# Troubleshooting Guide

## Common Issues When Running the Backend

### 1. "ModuleNotFoundError" or Import Errors

**Problem:** Python can't find installed packages.

**Solutions:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Reinstall all dependencies
pip install -r backend/requirements.txt
pip install -r backend/app/requirements.txt
```

### 2. "No model found" or Rasa Model Errors

**Problem:** Rasa model hasn't been trained yet.

**Solution:**
```bash
cd backend/app
rasa train
```

**Expected:** You should see "Your Rasa model is trained and saved" message.

### 3. Port Already in Use

**Problem:** Port 5001 or 5005 is already being used.

**Solutions:**

**Option A: Find and kill the process**
```bash
# Find process using port 5001
lsof -i :5001  # macOS/Linux
# or
netstat -ano | findstr :5001  # Windows

# Kill the process (replace PID with actual process ID)
kill -9 PID  # macOS/Linux
# or
taskkill /PID PID /F  # Windows
```

**Option B: Change ports in .env**
```env
FLASK_PORT=5002
RASA_WEBHOOK_URL=http://localhost:5006/webhooks/rest/webhook
```

### 4. "Connection refused" When Testing API

**Problem:** Services aren't running or wrong ports.

**Checklist:**
- [ ] Is Rasa server running? (Terminal 1)
- [ ] Is Flask wrapper running? (Terminal 2)
- [ ] Are you using the correct port? (default: 5001)
- [ ] Check for error messages in both terminals

**Test:**
```bash
# Check if services are running
curl http://localhost:5001/health
curl http://localhost:5005/status
```

### 5. "Rasa server not responding"

**Problem:** Rasa server isn't starting or crashed.

**Solutions:**
```bash
cd backend/app

# Check if model exists
ls models/

# If no model, train it
rasa train

# Try starting with verbose output
rasa run --enable-api --cors "*" --port 5005 --debug
```

### 6. Environment Variables Not Loading

**Problem:** .env file not found or not being read.

**Solutions:**
```bash
# Make sure .env exists
ls -la .env

# If missing, create from template
cp .env.template .env

# Verify Flask is reading it
# Check wrapper_server.py uses: load_dotenv()
```

### 7. MongoDB Connection Errors

**Problem:** MongoDB connection failing (if configured).

**Solutions:**
- MongoDB is optional - you can leave `MONGODB_URI` empty in .env
- If using MongoDB, verify:
  - Connection string format is correct
  - MongoDB server is accessible
  - Credentials are correct

### 8. AWS Errors (if using AWS features)

**Problem:** AWS credentials or permissions issues.

**Solutions:**
- AWS features are optional for basic testing
- Leave AWS credentials empty if not needed
- If using AWS, verify:
  - Credentials are correct in .env
  - IAM permissions are set up
  - Region is correct

### 9. Python Version Issues

**Problem:** Wrong Python version.

**Check:**
```bash
python3 --version  # Should be 3.9 or higher
```

**Solution:**
- Install Python 3.9+ if needed
- Use `python3` instead of `python` if both are installed

### 10. Virtual Environment Issues

**Problem:** Virtual environment not working.

**Solutions:**
```bash
# Delete and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install -r backend/app/requirements.txt
```

## Quick Diagnostic Commands

```bash
# Check Python version
python3 --version

# Check if virtual environment is active
which python  # Should show venv path

# Check installed packages
pip list

# Check if ports are in use
lsof -i :5001
lsof -i :5005

# Test Rasa model
cd backend/app
rasa test

# Validate Rasa configuration
rasa data validate
```

## Getting Help

1. **Check the logs:**
   - Look at terminal output for error messages
   - Check for stack traces

2. **Verify setup:**
   - Run `./setup_backend.sh` again
   - Follow `DEVELOPER_SETUP_GUIDE.md` step by step

3. **Test components individually:**
   ```bash
   # Test Rasa
   cd backend/app
   rasa run --enable-api --cors "*"
   
   # Test Flask (in another terminal)
   cd backend
   python wrapper_server.py
   ```

4. **Check documentation:**
   - `DEVELOPER_SETUP_GUIDE.md` - Step by step setup
   - `SETUP.md` - Detailed setup instructions
   - `README.md` - Overview and architecture

## Still Having Issues?

1. Share the exact error message
2. Share output of `python3 --version`
3. Share output of `pip list`
4. Share terminal output from both services
5. Check if all prerequisites are installed

