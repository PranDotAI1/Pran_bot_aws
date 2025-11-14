#!/bin/bash

# Automated Push Script for New Pran Bot AWS
# This script helps you push to a new GitHub repository

echo "=========================================="
echo "New Pran Bot AWS - Push to GitHub"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Error: Git not initialized. Run: git init"
    exit 1
fi

# Check if already has remote
if git remote get-url origin 2>/dev/null; then
    echo "Remote 'origin' already exists:"
    git remote get-url origin
    read -p "Do you want to change it? (y/n): " change_remote
    if [ "$change_remote" != "y" ]; then
        echo "Using existing remote..."
        REMOTE_URL=$(git remote get-url origin)
    else
        git remote remove origin
        REMOTE_URL=""
    fi
else
    REMOTE_URL=""
fi

if [ -z "$REMOTE_URL" ]; then
    echo ""
    echo "STEP 1: Create GitHub Repository"
    echo "=================================="
    echo ""
    echo "Please create a new repository on GitHub:"
    echo "1. Go to: https://github.com/new"
    echo "2. Repository name: New_Pran_bot_aws"
    echo "3. Description: Production-ready AWS-deployed Pran Healthcare Chatbot"
    echo "4. Set to Private or Public (your choice)"
    echo "5. DO NOT initialize with README, .gitignore, or license"
    echo "6. Click 'Create repository'"
    echo ""
    read -p "Press Enter after you've created the repository..."
    
    echo ""
    read -p "Enter your GitHub username: " GITHUB_USERNAME
    
    if [ -z "$GITHUB_USERNAME" ]; then
        echo "Error: GitHub username is required"
        exit 1
    fi
    
    read -p "Enter repository name [New_Pran_bot_aws]: " REPO_NAME
    REPO_NAME=${REPO_NAME:-New_Pran_bot_aws}
    
    REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    
    echo ""
    echo "Adding remote: $REMOTE_URL"
    git remote add origin "$REMOTE_URL"
fi

echo ""
echo "STEP 2: Verifying Repository"
echo "=================================="
./verify_repository.sh 2>&1 | tail -3
echo ""

echo "STEP 3: Checking Git Status"
echo "=================================="
git status --short | head -5
echo ""

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: There are uncommitted changes."
    read -p "Do you want to commit them? (y/n): " commit_changes
    if [ "$commit_changes" == "y" ]; then
        git add .
        git commit -m "Update: Additional changes"
    fi
fi

echo ""
echo "STEP 4: Pushing to GitHub"
echo "=================================="
echo "Pushing to: $REMOTE_URL"
echo "Branch: main"
echo ""

# Push to GitHub
if git push -u origin main; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Repository pushed to GitHub"
    echo "=========================================="
    echo ""
    echo "Repository URL: $REMOTE_URL"
    echo ""
    echo "Next steps:"
    echo "1. Share this URL with your UI developer"
    echo "2. Point them to UI_INTEGRATION_GUIDE.md"
    echo "3. Provide access if repository is private"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Push failed"
    echo "=========================================="
    echo ""
    echo "Possible issues:"
    echo "1. Repository doesn't exist on GitHub"
    echo "2. Authentication required (GitHub will prompt)"
    echo "3. Network connectivity issue"
    echo ""
    echo "Try manually:"
    echo "  git push -u origin main"
    echo ""
    exit 1
fi

