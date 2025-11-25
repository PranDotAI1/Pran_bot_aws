# PRAN Chatbot AWS - Production Repository

[![Production Ready](https://img.shields.io/badge/status-production%20ready-green)](https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS)
[![AWS](https://img.shields.io/badge/AWS-ECS%20Fargate-orange)](https://aws.amazon.com/ecs/)
[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![Rasa](https://img.shields.io/badge/Rasa-3.6.15-red)](https://rasa.com/)

Production-ready healthcare chatbot deployed on AWS infrastructure with full AI integration using AWS Bedrock, Comprehend Medical, and other AWS services.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- AWS CLI configured
- AWS credentials with appropriate permissions

### 1. Clone the Repository

```bash
git clone https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS.git
cd PRAN_Chatbot_AWS
```

### 2. Configure Environment Variables

Copy the configuration template:

```bash
cp config.env.template config.env
```

Edit `config.env` with your AWS credentials and database endpoints. **Never commit `config.env` to git** - it's already in `.gitignore`.

### 3. Install Dependencies

#### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
pip install -r app/requirements.txt
```

#### Frontend (Node.js)

```bash
cd frontend
npm install
```

### 4. Run Locally with Docker Compose

```bash
docker-compose up -d
```

This will start:
- **Rasa Backend** on port 5005
- **Flask Wrapper** (API Gateway) on port 5001
- **Rasa Actions Server** on port 5055

### 5. Test the API

```bash
# Health check
curl http://localhost:5001/health

# Send a message
curl -X POST http://localhost:5001/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "user123", "message": "Hello"}'
```

## 📁 Repository Structure

```
PRAN_Chatbot_AWS/
├── backend/                    # Backend services
│   ├── app/                   # Rasa chatbot application
│   │   ├── actions/          # Custom Rasa actions
│   │   │   ├── actions.py    # Main action handlers
│   │   │   ├── aws_intelligence.py  # AWS Bedrock integration
│   │   │   └── rag_system.py # RAG system implementation
│   │   ├── data/             # Training data (NLU, stories, rules)
│   │   ├── config.yml        # Rasa configuration
│   │   ├── domain.yml        # Domain definition
│   │   ├── endpoints.yml     # Endpoint configuration
│   │   ├── credentials.yml   # Credentials
│   │   ├── Dockerfile        # Rasa backend container
│   │   └── requirements.txt  # Python dependencies
│   ├── wrapper_server.py    # Flask API gateway
│   ├── requirements.txt      # Flask wrapper dependencies
│   └── Dockerfile.backend    # Flask wrapper container
├── frontend/                  # React frontend (if applicable)
├── api_backend/              # Django API backend
├── deployment/                # Deployment configurations
│   └── config/               # Configuration templates
├── scripts/                   # Utility scripts
│   ├── get_secrets.py        # AWS Secrets Manager helper
│   └── update_task_definition.py  # ECS task definition updater
├── docker-compose.yml        # Local development setup
├── config.env.template       # Environment variable template
├── .gitignore                # Git ignore rules
└── README.md                # This file
```

## 🏗️ Architecture

### Services

- **Frontend**: React 18 with TypeScript (optional)
- **Backend**: Rasa NLP engine with AWS Bedrock integration
- **API Gateway**: Flask wrapper server
- **APIs**: Node.js and Django API services
- **Databases**: PostgreSQL (Aurora), MongoDB (DocumentDB), Redis (ElastiCache)

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

## 🔧 Configuration

### Environment Variables

Key environment variables (see `config.env.template`):

- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_ACCOUNT_ID`: Your AWS account ID
- `DB_PASSWORD`: PostgreSQL database password (from AWS Secrets Manager)
- `MONGODB_URI`: MongoDB connection string
- `RASA_WEBHOOK_URL`: Rasa webhook endpoint
- `FLASK_PORT`: Flask wrapper port (default: 5001)

### AWS Secrets Manager

The application uses AWS Secrets Manager for secure credential storage:

- `pran-chatbot/db-password`: Database password
- `pran-chatbot/mongodb-password`: MongoDB password

Use `scripts/get_secrets.py` to retrieve secrets programmatically.

## 📡 API Endpoints

### Health Check

```http
GET /health
```

Returns service health status.

### Rasa Webhook

```http
POST /rasa-webhook
Content-Type: application/json

{
  "sender": "user123",
  "message": "Hello, I need help"
}
```

### Rasa Status

```http
GET /rasa-status
```

Returns Rasa server status.

## 🚢 Deployment

### AWS ECS Deployment

The application is deployed on AWS ECS Fargate. See `DEPLOYMENT_GUIDE.md` for detailed instructions.

#### Quick Deploy Steps

1. Build and push Docker images to ECR
2. Update ECS task definition with `scripts/update_task_definition.py`
3. Deploy to ECS service

### Docker Images

- `pran-chatbot-flask-wrapper`: Flask API gateway
- `pran-chatbot-rasa-backend`: Rasa NLP engine
- `pran-chatbot-frontend`: React frontend (if applicable)
- `pran-chatbot-django-api`: Django API service
- `pran-chatbot-node-api`: Node.js API service

All images are built for `linux/amd64` platform for ECS Fargate compatibility.

## 🔒 Security

- ✅ No hardcoded credentials
- ✅ AWS Secrets Manager integration
- ✅ Environment variable configuration
- ✅ Secure VPC networking
- ✅ IAM role-based access control

## 📚 Documentation

- [API Endpoints Reference](API_ENDPOINTS_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Developer Setup Guide](DEVELOPER_SETUP_GUIDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## 🧪 Development

### Running Tests

```bash
cd backend/app
rasa test
```

### Training the Model

```bash
cd backend/app
rasa train
```

### Local Development

```bash
# Start Rasa backend
cd backend/app
rasa run --enable-api --cors "*"

# Start Flask wrapper (in another terminal)
cd backend
python wrapper_server.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is proprietary software. All rights reserved.

## 📞 Support

For issues and questions, please open an issue on GitHub.

## 🎯 Production Status

✅ **Fully Deployed and Operational**

- Service: Running on AWS ECS Fargate
- Health Checks: Passing
- API Endpoints: Operational
- Databases: Connected
- AWS Services: Integrated

**Last Updated**: November 2024

---

**Repository**: [https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS](https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS)
