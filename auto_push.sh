#!/bin/bash
# Automated push script

cd "$(dirname "$0")"

echo "Attempting to push to GitHub..."
echo "Repository: pran_chatbot"
echo ""

# Try to push
if git push -u origin main 2>&1; then
    echo ""
    echo "✅ SUCCESS! Code pushed to GitHub!"
    echo "Repository: https://github.com/PranDotAI1/pran_chatbot"
    exit 0
else
    echo ""
    echo "⚠️  Push requires authentication or repository doesn't exist"
    echo ""
    echo "Please:"
    echo "1. Create repository: https://github.com/new (name: pran_chatbot)"
    echo "2. Get token: https://github.com/settings/tokens"
    echo "3. Run: git push -u origin main"
    echo "   (Use token as password when prompted)"
    exit 1
fi
