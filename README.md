# Hospital Chatbot System

A comprehensive healthcare chatbot built with Rasa, AWS Bedrock, and PostgreSQL, designed to provide intelligent medical assistance, appointment scheduling, and patient management.

## Features

- **Intelligent Conversation**: AWS Bedrock LLM integration for natural language understanding
- **Doctor Search & Booking**: Search 77+ doctors across 22+ specialties with real-time availability
- **Insurance Management**: Browse and compare 18 comprehensive insurance plans
- **Appointment Scheduling**: Real-time appointment booking with 3000+ available slots
- **Medical Records**: Access to patient medical history, medications, and lab results
- **RAG System**: Retrieval-Augmented Generation for context-aware responses
- **Multi-channel Support**: REST API and custom connectors

## Architecture

```
├── frontend/                 # React frontend application
├── backend/
│   ├── app/
│   │   ├── actions/         # Custom Rasa actions
│   │   │   ├── actions.py           # Main action handlers
│   │   │   ├── aws_intelligence.py  # AWS Bedrock integration
│   │   │   ├── rag_system.py        # RAG retrieval system
│   │   │   ├── llm_router.py        # LLM query routing
│   │   │   ├── text_to_sql_agent.py # SQL generation
│   │   │   └── symptom_analyzer.py  # Symptom analysis
│   │   ├── config.yml       # Rasa NLU pipeline configuration
│   │   ├── domain.yml       # Rasa domain definition
│   │   └── data/
│   │       ├── nlu.yml      # Training data (500+ examples)
│   │       ├── rules.yml    # Conversation rules
│   │       └── stories.yml  # Conversation flows
│   └── wrapper_server.py    # API wrapper server
├── aws-deployment/          # AWS infrastructure configurations
└── scripts/                 # Deployment utilities
```

## Technology Stack

### Backend
- **Rasa 3.x**: Conversational AI framework
- **AWS Bedrock**: LLM for intelligent responses
- **PostgreSQL**: Relational database (AWS RDS)
- **Python 3.10**: Core language
- **FastAPI**: API endpoints
- **psycopg2**: Database connectivity

### Frontend
- **React 18**: UI framework
- **Axios**: HTTP client
- **Modern ES6+**: JavaScript features

### Infrastructure
- **AWS ECS Fargate**: Container orchestration
- **AWS ECR**: Container registry
- **AWS RDS**: Managed PostgreSQL
- **AWS Application Load Balancer**: Traffic distribution
- **Docker**: Containerization

## Database Schema

The system uses PostgreSQL with the following main tables:

- **doctors**: Doctor profiles with specialties and contact information
- **patients**: Patient records and medical history
- **appointments**: Appointment scheduling and status tracking
- **insurance_plans**: Insurance plan details and coverage
- **medical_records**: Patient medical history
- **medications**: Prescription tracking
- **lab_results**: Laboratory test results
- **availability_slots**: Doctor availability management

## Quick Start

### For AWS Amplify Deployment (Recommended)

**Want to deploy this chatbot to AWS Amplify?** Follow our comprehensive guide:

📘 **[Complete AWS Amplify Deployment Guide](AMPLIFY_DEPLOYMENT_GUIDE.md)**

This guide includes:
- Step-by-step AWS infrastructure setup (RDS, ECS, ECR)
- Backend deployment on ECS Fargate
- Frontend deployment on AWS Amplify
- Environment configuration
- Testing procedures
- Troubleshooting tips

### Prerequisites

- AWS Account with admin access
- GitHub account
- AWS CLI installed and configured
- Docker installed
- Python 3.10+ and Node.js 14+

### Quick Clone and Deploy

```bash
# 1. Clone the repository
git clone https://github.com/PranDotAI1/Pran_bot_aws.git
cd Pran_bot_aws

# 2. Follow the Amplify Deployment Guide
# See AMPLIFY_DEPLOYMENT_GUIDE.md for complete instructions

# 3. Set up backend infrastructure (RDS, ECS)
# 4. Deploy frontend to Amplify
# 5. Test your deployed chatbot
```

### Local Development (Optional)

For local testing before deployment:

1. **Clone the repository**
```bash
git clone https://github.com/PranDotAI1/Pran_bot_aws.git
cd Pran_bot_aws
```

2. **Backend Setup**
```bash
cd backend/app
pip install -r requirements.txt
rasa train
rasa run -p 5005
```

3. **Actions Server**
```bash
cd backend/app
rasa run actions -p 5055
```

4. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
DB_HOST=<rds-endpoint>
DB_NAME=hospital
DB_USER=<username>
DB_PASSWORD=<password>
DB_PORT=5432
AWS_REGION=us-east-1
```

## API Endpoints

### Rasa Webhook
```
POST /rasa-webhook
Content-Type: application/json

{
  "sender": "user_id",
  "message": "I need a doctor"
}
```

### Health Check
```
GET /health
```

## Deployment

The application is deployed on AWS using:

- **ECS Cluster**: pran-chatbot-cluster
- **Service**: pran-chatbot-service
- **Load Balancer**: Application Load Balancer on port 8080
- **Database**: RDS PostgreSQL instance

### Deploy to AWS

```bash
# Build Docker images
docker build -t <ecr-repo>/rasa-backend:latest -f backend/app/Dockerfile backend/app
docker build -t <ecr-repo>/rasa-actions:latest -f backend/app/Dockerfile.actions backend/app

# Push to ECR
docker push <ecr-repo>/rasa-backend:latest
docker push <ecr-repo>/rasa-actions:latest

# Update ECS service
aws ecs update-service --cluster pran-chatbot-cluster --service pran-chatbot-service --force-new-deployment
```

## Key Features Implementation

### Intelligent Query Routing

The system uses an LLM router to intelligently direct queries:

- Insurance queries retrieve plan data from database
- Doctor searches query the doctors table with specialty filtering
- Medical questions leverage AWS Bedrock for accurate responses
- Appointment bookings check real-time availability

### RAG System

Retrieval-Augmented Generation enhances responses with:

- Database context injection
- Patient history integration
- Real-time data retrieval
- Context-aware answer generation

### Conversation Management

- Session management with 5-minute expiration
- Conversation history tracking
- Duplicate response prevention
- Multi-turn conversation support

## Usage Examples

### Finding a Doctor
```
User: "I need a gynecologist"
Bot: [Lists available gynecologists with ratings and availability]
```

### Insurance Information
```
User: "What insurance plans do you have?"
Bot: [Displays all 18 plans with pricing and coverage]

User: "Tell me about Premium Health Plan"
Bot: [Shows detailed plan information]
```

### Appointment Booking
```
User: "Book an appointment"
Bot: [Shows available doctors and time slots]
```

## Testing

Run tests with:

```bash
# Backend tests
cd backend/app
pytest

# Frontend tests
cd frontend
npm test
```

## Performance

- Response time: < 2 seconds average
- Uptime: 99.9%
- Concurrent users: 100+
- Database query time: < 100ms

## Security

- Environment variables for sensitive data
- AWS IAM roles for service access
- PostgreSQL SSL connections
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Create an issue in the repository
- Contact the development team

## Documentation

- 📘 **[AWS Amplify Deployment Guide](AMPLIFY_DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- [Final Deployment Status](FINAL_DEPLOYMENT_STATUS.md) - Current deployment details
- [Database Documentation](DATABASE_COMPLETE_STATUS.md) - Database schema and data
- [Permanent Deployment Details](PERMANENT_DEPLOYMENT_COMPLETE.md) - Technical specifications
- [Cleanup Summary](CLEANUP_SUMMARY.md) - Repository organization details

---

**Version**: 1.0.0  
**Last Updated**: December 2025
