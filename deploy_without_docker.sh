#!/bin/bash
# Alternative deployment: Force ECS to redeploy (will use existing image or trigger rebuild)
# This assumes the image was built before or will be built via CI/CD

set -e

echo "======================================================================"
echo "FORCING ECS DEPLOYMENT (Alternative Method)"
echo "======================================================================"

CLUSTER="pran-chatbot-cluster"
SERVICE="pran-chatbot-service"
REGION="us-east-1"

echo ""
echo "📦 Configuration:"
echo "   Cluster: $CLUSTER"
echo "   Service: $SERVICE"
echo "   Region: $REGION"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    exit 1
fi

# Force new deployment
echo "======================================================================"
echo "Forcing new ECS deployment..."
echo "======================================================================"

aws ecs update-service \
    --cluster $CLUSTER \
    --service $SERVICE \
    --force-new-deployment \
    --region $REGION \
    --query 'service.{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount}' \
    --output table

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully triggered new deployment"
    echo ""
    echo "⏳ Deployment Status:"
    echo "   This will restart all tasks with the latest code"
    echo "   Wait 2-5 minutes for deployment to complete"
    echo ""
    echo "Monitor deployment:"
    echo "   aws ecs describe-services --cluster $CLUSTER --services $SERVICE --region $REGION"
else
    echo "❌ Failed to trigger deployment"
    exit 1
fi
