#!/bin/bash

# Script to copy frontend fix files to Amplify app
# Usage: ./copy_to_amplify.sh /path/to/your/amplify/app

set -e

echo "======================================================================"
echo "COPYING FRONTEND FIX FILES TO AMPLIFY APP"
echo "======================================================================"
echo ""

# Check if destination path is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide the path to your Amplify app"
    echo ""
    echo "Usage: ./copy_to_amplify.sh /path/to/your/amplify/app"
    echo ""
    echo "Example: ./copy_to_amplify.sh ~/my-amplify-app"
    exit 1
fi

AMPLIFY_APP_PATH="$1"

# Check if path exists
if [ ! -d "$AMPLIFY_APP_PATH" ]; then
    echo "❌ Error: Directory does not exist: $AMPLIFY_APP_PATH"
    exit 1
fi

echo "📁 Source: $(pwd)"
echo "📁 Destination: $AMPLIFY_APP_PATH"
echo ""

# Create src directory if it doesn't exist
if [ ! -d "$AMPLIFY_APP_PATH/src" ]; then
    echo "📂 Creating src directory..."
    mkdir -p "$AMPLIFY_APP_PATH/src"
fi

# Copy files
echo "📋 Copying files..."
echo ""

# Copy Chatbot component
if [ -f "frontend/src/Chatbot.jsx" ]; then
    cp "frontend/src/Chatbot.jsx" "$AMPLIFY_APP_PATH/src/"
    echo "✅ Copied: Chatbot.jsx"
else
    echo "⚠️  Warning: Chatbot.jsx not found"
fi

# Copy CSS
if [ -f "frontend/src/Chatbot.css" ]; then
    cp "frontend/src/Chatbot.css" "$AMPLIFY_APP_PATH/src/"
    echo "✅ Copied: Chatbot.css"
else
    echo "⚠️  Warning: Chatbot.css not found"
fi

# Copy hook
if [ -f "frontend/src/useChatbot.js" ]; then
    cp "frontend/src/useChatbot.js" "$AMPLIFY_APP_PATH/src/"
    echo "✅ Copied: useChatbot.js"
else
    echo "⚠️  Warning: useChatbot.js not found"
fi

# Copy amplify.yml to root
if [ -f "amplify.yml" ]; then
    cp "amplify.yml" "$AMPLIFY_APP_PATH/"
    echo "✅ Copied: amplify.yml (to app root)"
else
    echo "⚠️  Warning: amplify.yml not found"
fi

# Copy README
if [ -f "FRONTEND_FIX_README.md" ]; then
    cp "FRONTEND_FIX_README.md" "$AMPLIFY_APP_PATH/"
    echo "✅ Copied: FRONTEND_FIX_README.md"
else
    echo "⚠️  Warning: FRONTEND_FIX_README.md not found"
fi

echo ""
echo "======================================================================"
echo "✅ FILES COPIED SUCCESSFULLY"
echo "======================================================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Open your Amplify app: $AMPLIFY_APP_PATH"
echo ""
echo "2. Import and use the component in your app:"
echo "   import Chatbot from './Chatbot';"
echo "   import './Chatbot.css';"
echo ""
echo "3. Configure Amplify rewrite rule:"
echo "   - Go to AWS Amplify Console"
echo "   - App Settings > Rewrites and redirects"
echo "   - Add: /api/chatbot -> http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook"
echo ""
echo "4. Deploy your app"
echo ""
echo "📖 See FRONTEND_FIX_README.md for detailed instructions"
echo ""

