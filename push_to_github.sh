#!/bin/bash

# Push New Pran Bot AWS to GitHub
# This script helps you push the repository

echo "=========================================="
echo "New Pran Bot AWS - GitHub Push Helper"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    echo "✅ Git initialized"
    echo ""
fi

# Check current status
echo "Current git status:"
git status --short | head -10
echo ""

# Ask user for option
echo "Choose an option:"
echo "1. Create new GitHub repository (recommended)"
echo "2. Push to existing repository as new branch"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
    echo ""
    echo "=== Option 1: New Repository ==="
    echo ""
    echo "1. First, create a new repository on GitHub:"
    echo "   - Go to: https://github.com/new"
    echo "   - Name: New_Pran_bot_aws"
    echo "   - DO NOT initialize with README"
    echo ""
    read -p "Press Enter after creating the repository..."
    
    read -p "Enter your GitHub username: " username
    read -p "Enter repository name [New_Pran_bot_aws]: " repo_name
    repo_name=${repo_name:-New_Pran_bot_aws}
    
    echo ""
    echo "Adding files..."
    git add .
    
    echo "Creating commit..."
    git commit -m "Initial commit: Production-ready AWS-deployed Pran Healthcare Chatbot

- Complete backend with Rasa NLP engine
- Flask API gateway with CORS enabled
- AWS Bedrock and Comprehend Medical integration
- MongoDB and PostgreSQL support
- Docker containerization
- Comprehensive documentation
- UI integration ready
- All code cleaned (no emojis, no hardcoded values)"
    
    echo "Adding remote..."
    git remote add origin https://github.com/$username/$repo_name.git 2>/dev/null || \
    git remote set-url origin https://github.com/$username/$repo_name.git
    
    echo "Pushing to main branch..."
    git branch -M main
    git push -u origin main
    
    echo ""
    echo "✅ Successfully pushed to: https://github.com/$username/$repo_name"
    
elif [ "$choice" == "2" ]; then
    echo ""
    echo "=== Option 2: New Branch ==="
    echo ""
    read -p "Enter existing repository URL: " repo_url
    read -p "Enter branch name [new_pran_bot_aws]: " branch_name
    branch_name=${branch_name:-new_pran_bot_aws}
    
    echo ""
    echo "Adding files..."
    git add .
    
    echo "Creating commit..."
    git commit -m "Add: Production-ready AWS-deployed bot ($branch_name branch)

- Complete AWS deployment codebase
- All code cleaned and production-ready
- Ready for UI integration"
    
    echo "Adding remote..."
    git remote add origin $repo_url 2>/dev/null || \
    git remote set-url origin $repo_url
    
    echo "Creating and pushing branch..."
    git checkout -b $branch_name
    git push -u origin $branch_name
    
    echo ""
    echo "✅ Successfully pushed to branch: $branch_name"
else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo ""
echo "=========================================="
echo "Push Complete!"
echo "=========================================="
