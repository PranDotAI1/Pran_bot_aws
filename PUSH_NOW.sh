#!/bin/bash

# Simple push script - Run this after getting your token
cd "$(dirname "$0")"

echo "=========================================="
echo "🚀 PUSH TO GITHUB"
echo "=========================================="
echo ""
echo "Repository: PRAN_Chatbot_AWS"
echo "URL: https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS.git"
echo ""
echo "📋 STEP 1: Get your GitHub token"
echo "   → https://github.com/settings/tokens"
echo "   → Generate new token (classic)"
echo "   → Select 'repo' scope"
echo "   → Copy the token"
echo ""
read -p "📋 STEP 2: Paste your token here: " TOKEN

if [ -z "$TOKEN" ]; then
    echo "❌ Token required. Exiting."
    exit 1
fi

echo ""
echo "🔄 Pushing to GitHub..."

# Set remote with token
git remote set-url origin https://${TOKEN}@github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS.git

# Push
if git push -u origin main; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Code pushed to GitHub!"
    echo "=========================================="
    echo ""
    echo "📍 Repository: https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS"
    echo ""
    
    # Remove token from remote for security
    git remote set-url origin https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS.git
    echo "✅ Token removed from remote URL"
    echo ""
    echo "🎉 Ready for UI integration!"
else
    echo ""
    echo "❌ Push failed. Check:"
    echo "   1. Token is valid and has 'repo' scope"
    echo "   2. Repository exists and you have access"
    echo "   3. Internet connection is working"
    exit 1
fi

