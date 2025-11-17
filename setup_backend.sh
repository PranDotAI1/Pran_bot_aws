#!/bin/bash

# Automated setup script for PRAN Chatbot Backend
# This script helps developers set up the backend quickly

set -e  # Exit on error

echo "=========================================="
echo "PRAN Chatbot Backend Setup"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing Flask wrapper dependencies..."
cd backend
pip install -r requirements.txt

echo ""
echo "📦 Installing Rasa dependencies..."
pip install -r app/requirements.txt

# Create .env if it doesn't exist
cd ..
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Train Rasa model
echo ""
echo "🤖 Training Rasa model (this may take a few minutes)..."
cd backend/app
rasa train

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration (optional for basic testing)"
echo "2. Start Rasa server:"
echo "   cd backend/app"
echo "   rasa run --enable-api --cors '*' --port 5005"
echo ""
echo "3. In another terminal, start Flask wrapper:"
echo "   cd backend"
echo "   python wrapper_server.py"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:5001/health"
echo ""
echo "See DEVELOPER_SETUP_GUIDE.md for detailed instructions"
echo "=========================================="

