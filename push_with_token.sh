#!/bin/bash

# Push script using Personal Access Token
cd "$(dirname "$0")"

echo "=========================================="
echo "Push to PRAN_Chatbot_AWS"
echo "=========================================="
echo ""

read -p "Enter your GitHub Personal Access Token: " TOKEN

if [ -z "$TOKEN" ]; then
    echo "❌ Token is required"
    echo ""
    echo "Get token from: https://github.com/settings/tokens"
    exit 1
fi

echo ""
echo "Setting remote with token..."
git remote set-url origin https://${TOKEN}@github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS.git

echo ""
echo "Pushing to GitHub..."
if git push -u origin main; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Code pushed to GitHub!"
    echo "=========================================="
    echo ""
    echo "Repository: https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS"
    echo ""
    echo "Next: Share this URL with your UI developer!"
    echo ""
    
    # Remove token from remote for security
    git remote set-url origin https://github.com/viditagarwal286-ship-it/PRAN_Chatbot_AWS.git
    echo "✅ Token removed from remote URL for security"
else
    echo ""
    echo "❌ Push failed"
    echo "Check:"
    echo "1. Token is valid"
    echo "2. Repository exists"
    echo "3. You have write access"
    exit 1
fi

