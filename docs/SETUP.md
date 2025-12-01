# Setup Instructions - New Pran Bot AWS

Complete setup guide for the production-ready chatbot repository.

## Initial Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd New_Pran_bot_aws
```

### 2. Configure Environment

```bash
# Copy environment template
cp deployment/config/.env.template .env

# Edit with your values
nano .env  # or use your preferred editor
```

Required environment variables:
- `MONGODB_URI`: MongoDB connection string
- `AWS_REGION`: AWS region
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`: Database credentials
- `RASA_WEBHOOK_URL`: Rasa webhook endpoint

### 3. Install Dependencies

#### Backend (Python)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r app/requirements.txt
```

#### Frontend (Node.js)

```bash
cd frontend
npm install
```

### 4. Configure Rasa

```bash
cd backend/app

# Train the model (if needed)
rasa train

# Verify configuration
rasa data validate
```

### 5. Start Services

#### Terminal 1: Rasa Backend
```bash
cd backend/app
rasa run --enable-api --cors "*" --port 5005
```

#### Terminal 2: Flask Wrapper
```bash
cd backend
python wrapper_server.py
```

#### Terminal 3: Frontend
```bash
cd frontend
npm run dev
```

## Docker Setup

### Build Images

```bash
# Build backend
docker build -f Dockerfile.backend -t pran-bot-backend .

# Build frontend (if Dockerfile exists)
docker build -t pran-bot-frontend ./frontend
```

### Run with Docker Compose

```bash
docker-compose up -d
```

## Verification

### 1. Health Check

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy",
  "flask_wrapper": "running",
  "rasa_status": "connected",
  "mongodb_status": "connected"
}
```

### 2. Test MongoDB

```bash
curl http://localhost:5001/mongodb/test
```

### 3. Test Chatbot

```bash
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user",
    "message": "Hello"
  }'
```

## Development Setup

### Code Structure

```
backend/
├── app/              # Rasa application
│   ├── actions/     # Custom actions
│   ├── data/        # Training data
│   └── models/      # Trained models
└── wrapper_server.py # Flask API gateway
```

### Running Tests

```bash
# Test Rasa model
cd backend/app
rasa test

# Test Python code
cd backend
pytest tests/
```

### Code Standards

- No emojis in code
- All credentials in environment variables
- Proper error handling
- Comprehensive logging
- Type hints where applicable

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Install all requirements
   - Check Python path

2. **Database Connection**
   - Verify credentials in `.env`
   - Check network connectivity
   - Verify database is running

3. **MongoDB Connection**
   - Verify MongoDB URI format
   - Check authentication
   - Verify network access

4. **Rasa Not Starting**
   - Check model exists: `ls backend/app/models/`
   - Train model if needed: `rasa train`
   - Check port availability

5. **AWS Services Not Working**
   - Verify AWS credentials
   - Check IAM permissions
   - Verify region configuration

## Next Steps

1. Review `README.md` for architecture details
2. Check `DEPLOYMENT_GUIDE.md` for AWS deployment
3. Review `CHANGELOG.md` for recent changes
4. Configure monitoring and logging
5. Set up CI/CD pipeline

## Support

For setup issues:
1. Check error messages carefully
2. Review logs
3. Verify environment variables
4. Check documentation
5. Open an issue on GitHub

