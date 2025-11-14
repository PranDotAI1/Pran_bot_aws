#!/bin/bash

# Complete Push Script - Handles authentication
cd "$(dirname "$0")"

echo "=========================================="
echo "Complete Push to GitHub - pran_chatbot"
echo "=========================================="
echo ""

# Check if repository exists on GitHub
echo "Checking if repository exists..."
if git ls-remote origin &> /dev/null; then
    echo "✅ Repository exists on GitHub"
    REPO_EXISTS=true
else
    echo "⚠️  Repository doesn't exist yet"
    REPO_EXISTS=false
fi

echo ""

if [ "$REPO_EXISTS" = false ]; then
    echo "STEP 1: Create GitHub Repository"
    echo "=================================="
    echo ""
    echo "Please create the repository first:"
    echo "1. Go to: https://github.com/new"
    echo "2. Repository name: pran_chatbot"
    echo "3. Description: Production-ready AWS-deployed Pran Healthcare Chatbot"
    echo "4. Visibility: Private or Public"
    echo "5. DO NOT initialize with README"
    echo "6. Click 'Create repository'"
    echo ""
    read -p "Press Enter after creating the repository..."
    echo ""
fi

echo "STEP 2: Authentication"
echo "=================================="
echo ""
echo "GitHub requires authentication to push."
echo ""
echo "You have two options:"
echo ""
echo "Option A: Personal Access Token (Recommended)"
echo "  1. Go to: https://github.com/settings/tokens"
echo "  2. Generate new token (classic)"
echo "  3. Select 'repo' scope"
echo "  4. Copy the token"
echo ""
echo "Option B: Use existing credentials (if stored)"
echo "  macOS Keychain may have your credentials"
echo ""
read -p "Do you have a Personal Access Token ready? (y/n): " has_token

if [ "$has_token" != "y" ]; then
    echo ""
    echo "Please create a token first:"
    echo "https://github.com/settings/tokens"
    echo ""
    read -p "Press Enter after creating the token..."
    echo ""
fi

echo ""
echo "STEP 3: Pushing to GitHub"
echo "=================================="
echo ""
echo "Pushing to: https://github.com/PranDotAI1/pran_chatbot.git"
echo ""

# Try to push
if git push -u origin main 2>&1; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Code pushed to GitHub!"
    echo "=========================================="
    echo ""
    echo "Repository URL: https://github.com/PranDotAI1/pran_chatbot"
    echo ""
    echo "Next steps:"
    echo "1. Share this URL with your UI developer"
    echo "2. Point them to: UI_INTEGRATION_GUIDE.md"
    echo "3. Grant access if repository is private"
    echo ""
    exit 0
else
    echo ""
    echo "=========================================="
    echo "❌ Push failed"
    echo "=========================================="
    echo ""
    echo "This usually means:"
    echo "1. Repository doesn't exist - create it first"
    echo "2. Authentication failed - check your token/credentials"
    echo "3. Network issue - check your connection"
    echo ""
    echo "Try manually:"
    echo "  git push -u origin main"
    echo ""
    echo "When prompted:"
    echo "  Username: PranDotAI1"
    echo "  Password: [Your Personal Access Token]"
    echo ""
    exit 1
fi

