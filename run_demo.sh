#!/bin/bash

# Launch Streamlit Chatbot Demo

echo "=================================="
echo "PRAN Chatbot Demo - Streamlit UI"
echo "=================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing..."
    pip install streamlit requests
fi

# Check if requirements file exists
if [ -f "requirements_streamlit.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements_streamlit.txt
fi

echo ""
echo "🚀 Starting Streamlit demo..."
echo "📡 API Endpoint: http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"
echo ""
echo "The app will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run streamlit
streamlit run streamlit_demo.py

