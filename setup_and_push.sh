#!/bin/bash
# Setup remote and attempt push for pran_chatbot repository

cd "$(dirname "$0")"

REPO_NAME="pran_chatbot"
GITHUB_USER="PranDotAI1"  # Based on your existing repo URL

echo "=========================================="
echo "Setting up remote for: $REPO_NAME"
echo "=========================================="
echo ""

# Remove existing remote
git remote remove origin 2>/dev/null

# Add remote
REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
echo "Adding remote: $REMOTE_URL"
git remote add origin "$REMOTE_URL"

echo ""
echo "Remote configured:"
git remote -v

echo ""
echo "=========================================="
echo "Ready to push!"
echo "=========================================="
echo ""
echo "Repository URL: $REMOTE_URL"
echo ""
echo "To push, run:"
echo "  git push -u origin main"
echo ""
echo "OR if repository doesn't exist yet:"
echo "1. Create it at: https://github.com/new"
echo "   Name: $REPO_NAME"
echo "2. Then run: git push -u origin main"
echo ""
