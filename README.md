# New Pran Bot AWS - Production Repository

Production-ready healthcare chatbot deployed on AWS infrastructure with full AI integration.

## Overview

This repository contains the complete AWS-deployed healthcare chatbot system, fully operational on AWS cloud infrastructure with AWS-native services. The bot integrates with AWS Bedrock, Comprehend Medical, and other AWS services for intelligent healthcare conversations.

## Architecture

### Services
- **Frontend**: React 18 with TypeScript
- **Backend**: Rasa NLP engine with AWS Bedrock integration
- **API Gateway**: Flask wrapper server
- **APIs**: Node.js and Django API services
- **Databases**: PostgreSQL (Aurora), MongoDB, DocumentDB

### AWS Services
- **ECS Fargate**: Container orchestration
- **RDS PostgreSQL**: Primary database
- **DocumentDB/MongoDB**: NoSQL database
- **ElastiCache Redis**: Caching layer
- **Application Load Balancer**: Traffic distribution
- **S3**: Object storage
- **AWS Bedrock**: AI/ML capabilities (Claude 3.5 Sonnet)
- **AWS Comprehend Medical**: Medical entity recognition
- **CloudWatch**: Monitoring and logging
- **VPC**: Network isolation
- **Secrets Manager**: Credential management

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose
- AWS CLI configured
- AWS credentials with appropriate permissions

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd New_Pran_bot_aws
```

### 2. Configure Environment Variables

Copy the environment template and fill in your values:

```bash
cp deployment/config/.env.template .env
```

Edit `.env` with your configuration:
- AWS credentials
- Database connection strings
- MongoDB URI
- API endpoints

### 3. Install Dependencies

#### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend (Node.js)
```bash
cd frontend
npm install
```

### 4. Run Locally

#### Start Rasa Backend
```bash
cd backend/app
rasa run --enable-api --cors "*"
```

#### Start Flask Wrapper
```bash
cd backend
python wrapper_server.py
```

#### Start Frontend
```bash
cd frontend
npm run dev
```

## Configuration

### Environment Variables

All configuration is managed through environment variables. Key variables:

- `FLASK_HOST`: Flask server host (default: 0.0.0.0)
- `FLASK_PORT`: Flask server port (default: 5001)
- `RASA_WEBHOOK_URL`: Rasa webhook endpoint
- `MONGODB_URI`: MongoDB connection string
- `AWS_REGION`: AWS region for services
- `BEDROCK_MODEL_ID`: AWS Bedrock model identifier
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`: Database credentials

### Database Configuration

The application supports multiple database backends:
- PostgreSQL/Aurora (primary)
- MongoDB (document storage)
- Legacy RDS (fallback)

Configure database connections in `.env` file.

## Project Structure

```
New_Pran_bot_aws/
├── backend/                 # Backend services
│   ├── app/                # Rasa chatbot application
│   │   ├── actions/       # Custom actions
│   │   ├── data/          # Training data
│   │   └── models/        # Trained models
│   ├── wrapper_server.py  # Flask API gateway
│   └── requirements.txt   # Python dependencies
├── frontend/              # React frontend
│   ├── src/              # Source code
│   └── package.json      # Dependencies
├── api/                  # API services
│   ├── node-api/        # Node.js API
│   └── django-api/      # Django API
├── deployment/          # Deployment configurations
│   ├── scripts/        # Deployment scripts
│   ├── terraform/      # Infrastructure as Code
│   └── config/         # Configuration files
└── docs/               # Documentation
```

## API Endpoints

### Flask Wrapper Server

- `GET /health` - Health check endpoint
- `POST /rasa-webhook` - Forward requests to Rasa
- `GET /mongodb/test` - Test MongoDB connection
- `GET /mongodb/explore` - Explore MongoDB structure

### Rasa Backend

- `POST /webhooks/rest/webhook` - Chat webhook
- `GET /status` - Status endpoint

## Development

### Code Standards

- No emojis in code or logs
- All credentials in environment variables
- Proper error handling and logging
- Production-ready error messages
- Comprehensive documentation

### Logging

All services use structured logging:
- Python: `logging` module with INFO level
- Node.js: `winston` or similar
- Logs go to CloudWatch in production

### Testing

```bash
# Test Rasa model
cd backend/app
rasa test

# Test Flask wrapper
cd backend
python -m pytest tests/
```

## Deployment

### AWS Deployment

See `deployment/` directory for:
- Terraform configurations
- Deployment scripts
- Environment configurations

### Docker Deployment

```bash
# Build images
docker-compose build

# Run services
docker-compose up -d
```

## Security

- All credentials stored in environment variables
- Secrets managed through AWS Secrets Manager
- HTTPS/TLS for all external communications
- CORS properly configured
- Input validation on all endpoints

## Monitoring

- CloudWatch Logs for all services
- CloudWatch Metrics for performance
- Health check endpoints
- Error tracking and alerting

## Support

For issues and questions:
- Check documentation in `docs/`
- Review deployment logs
- Check CloudWatch metrics

## License

[Your License Here]

## Changelog

See `CHANGELOG.md` for version history and updates.

