#!/bin/bash

# Push script for new_pran_bot_aws branch to old repository
cd "$(dirname "$0")"

echo "=========================================="
echo "🚀 PUSH BRANCH: new_pran_bot_aws"
echo "=========================================="
echo ""
echo "Repository: https://github.com/PranDotAI1/pran_chatbot.git"
echo "Branch: new_pran_bot_aws"
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
echo "🔄 Pushing branch to GitHub..."

# Set remote with token
git remote set-url origin https://${TOKEN}@github.com/PranDotAI1/pran_chatbot.git

# Push branch
if git push -u origin new_pran_bot_aws; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Branch pushed to GitHub!"
    echo "=========================================="
    echo ""
    echo "📍 Branch URL: https://github.com/PranDotAI1/pran_chatbot/tree/new_pran_bot_aws"
    echo ""
    echo "For UI developer:"
    echo "  git clone https://github.com/PranDotAI1/pran_chatbot.git"
    echo "  cd pran_chatbot"
    echo "  git checkout new_pran_bot_aws"
    echo ""
    
    # Remove token from remote for security
    git remote set-url origin https://github.com/PranDotAI1/pran_chatbot.git
    echo "✅ Token removed from remote URL for security"
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

