#!/bin/bash

# Complete Push Script - Automated
# This will help you push to GitHub with minimal steps

echo "=========================================="
echo "New Pran Bot AWS - Complete Push Setup"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Verify repository is ready
echo "1. Verifying repository..."
./verify_repository.sh 2>&1 | tail -3
echo ""

# Check git status
echo "2. Git status:"
git log --oneline -1
echo ""

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo "3. GitHub CLI detected!"
    echo ""
    read -p "Do you want to create repository using GitHub CLI? (y/n): " use_gh
    
    if [ "$use_gh" == "y" ]; then
        echo ""
        echo "Creating repository with GitHub CLI..."
        
        # Check if authenticated
        if gh auth status &> /dev/null; then
            echo "✅ GitHub CLI authenticated"
            
            read -p "Repository name [New_Pran_bot_aws]: " repo_name
            repo_name=${repo_name:-New_Pran_bot_aws}
            
            read -p "Description [Production-ready AWS-deployed Pran Healthcare Chatbot]: " repo_desc
            repo_desc=${repo_desc:-Production-ready AWS-deployed Pran Healthcare Chatbot}
            
            read -p "Visibility (public/private) [private]: " visibility
            visibility=${visibility:-private}
            
            echo ""
            echo "Creating repository: $repo_name"
            
            if gh repo create "$repo_name" --description "$repo_desc" --$visibility --source=. --remote=origin --push; then
                echo ""
                echo "=========================================="
                echo "✅ SUCCESS! Repository created and pushed!"
                echo "=========================================="
                echo ""
                gh repo view "$repo_name" --web 2>/dev/null || echo "Repository: https://github.com/$(gh api user --jq .login)/$repo_name"
                echo ""
                exit 0
            else
                echo "❌ Failed to create repository with GitHub CLI"
                echo "Falling back to manual method..."
            fi
        else
            echo "⚠️  GitHub CLI not authenticated"
            echo "Run: gh auth login"
            echo "Falling back to manual method..."
        fi
    fi
fi

# Manual method
echo ""
echo "3. Manual Push Method"
echo "=================================="
echo ""
echo "STEP 1: Create GitHub Repository"
echo "----------------------------------"
echo "1. Go to: https://github.com/new"
echo "2. Repository name: New_Pran_bot_aws"
echo "3. Description: Production-ready AWS-deployed Pran Healthcare Chatbot"
echo "4. Visibility: Private or Public"
echo "5. DO NOT initialize with README, .gitignore, or license"
echo "6. Click 'Create repository'"
echo ""
read -p "Press Enter after creating the repository..."

echo ""
echo "STEP 2: Enter Repository Details"
echo "----------------------------------"
read -p "Your GitHub username: " username

if [ -z "$username" ]; then
    echo "❌ Username is required"
    exit 1
fi

read -p "Repository name [New_Pran_bot_aws]: " repo_name
repo_name=${repo_name:-New_Pran_bot_aws}

remote_url="https://github.com/$username/$repo_name.git"

echo ""
echo "STEP 3: Adding Remote and Pushing"
echo "----------------------------------"

# Remove existing remote if any
git remote remove origin 2>/dev/null

# Add remote
echo "Adding remote: $remote_url"
git remote add origin "$remote_url"

# Push
echo "Pushing to GitHub..."
if git push -u origin main; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Code pushed to GitHub!"
    echo "=========================================="
    echo ""
    echo "Repository URL: $remote_url"
    echo ""
    echo "Next steps:"
    echo "1. Share this URL with your UI developer: $remote_url"
    echo "2. Point them to: UI_INTEGRATION_GUIDE.md"
    echo "3. Grant access if repository is private"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Push failed"
    echo "=========================================="
    echo ""
    echo "Common issues:"
    echo "1. Repository doesn't exist - make sure you created it"
    echo "2. Authentication required - GitHub will prompt for credentials"
    echo "3. Wrong repository name - check the name matches"
    echo ""
    echo "Try again or push manually:"
    echo "  git push -u origin main"
    echo ""
    exit 1
fi

