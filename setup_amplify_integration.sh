#!/bin/bash

# Complete setup script for Amplify integration
# This script will help you set up the chatbot integration

set -e

echo "======================================================================"
echo "PRAN CHATBOT - AMPLIFY INTEGRATION SETUP"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Find Amplify app
echo "🔍 Step 1: Finding your Amplify app..."
echo ""

AMPLIFY_APP_PATH=""

# Check common locations
COMMON_PATHS=(
    "$HOME/amplify-app"
    "$HOME/my-amplify-app"
    "$HOME/Documents/amplify-app"
    "$HOME/Desktop/amplify-app"
    "$HOME/Downloads/amplify-app"
    "$HOME/projects/amplify-app"
    "$HOME/projects/pran-amplify"
    "$HOME/projects/chatbot-amplify"
)

for path in "${COMMON_PATHS[@]}"; do
    if [ -d "$path" ] && [ -f "$path/package.json" ]; then
        AMPLIFY_APP_PATH="$path"
        echo -e "${GREEN}✅ Found Amplify app at: $path${NC}"
        break
    fi
done

# If not found, ask user
if [ -z "$AMPLIFY_APP_PATH" ]; then
    echo -e "${YELLOW}⚠️  Could not automatically find your Amplify app${NC}"
    echo ""
    echo "Please provide the path to your Amplify app:"
    read -p "Path: " AMPLIFY_APP_PATH
    
    if [ ! -d "$AMPLIFY_APP_PATH" ]; then
        echo -e "${RED}❌ Error: Directory does not exist: $AMPLIFY_APP_PATH${NC}"
        exit 1
    fi
    
    if [ ! -f "$AMPLIFY_APP_PATH/package.json" ]; then
        echo -e "${YELLOW}⚠️  Warning: package.json not found. Is this a React/Node.js app?${NC}"
        read -p "Continue anyway? (y/n): " CONTINUE
        if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
            exit 1
        fi
    fi
fi

echo ""
echo "📁 Amplify app path: $AMPLIFY_APP_PATH"
echo ""

# Step 2: Create src directory if needed
echo "🔧 Step 2: Setting up directory structure..."
if [ ! -d "$AMPLIFY_APP_PATH/src" ]; then
    mkdir -p "$AMPLIFY_APP_PATH/src"
    echo "✅ Created src directory"
else
    echo "✅ src directory exists"
fi
echo ""

# Step 3: Copy files
echo "📋 Step 3: Copying files..."
echo ""

REPO_PATH="$(cd "$(dirname "$0")" && pwd)"

# Copy Chatbot.jsx
if [ -f "$REPO_PATH/frontend/src/Chatbot.jsx" ]; then
    cp "$REPO_PATH/frontend/src/Chatbot.jsx" "$AMPLIFY_APP_PATH/src/"
    echo "✅ Copied: Chatbot.jsx"
else
    echo -e "${RED}❌ Error: Chatbot.jsx not found${NC}"
    exit 1
fi

# Copy Chatbot.css
if [ -f "$REPO_PATH/frontend/src/Chatbot.css" ]; then
    cp "$REPO_PATH/frontend/src/Chatbot.css" "$AMPLIFY_APP_PATH/src/"
    echo "✅ Copied: Chatbot.css"
else
    echo -e "${RED}❌ Error: Chatbot.css not found${NC}"
    exit 1
fi

# Copy useChatbot.js
if [ -f "$REPO_PATH/frontend/src/useChatbot.js" ]; then
    cp "$REPO_PATH/frontend/src/useChatbot.js" "$AMPLIFY_APP_PATH/src/"
    echo "✅ Copied: useChatbot.js"
else
    echo -e "${YELLOW}⚠️  Warning: useChatbot.js not found (optional)${NC}"
fi

# Copy amplify.yml
if [ -f "$REPO_PATH/amplify.yml" ]; then
    cp "$REPO_PATH/amplify.yml" "$AMPLIFY_APP_PATH/"
    echo "✅ Copied: amplify.yml"
else
    echo -e "${YELLOW}⚠️  Warning: amplify.yml not found${NC}"
fi

# Copy README
if [ -f "$REPO_PATH/FRONTEND_FIX_README.md" ]; then
    cp "$REPO_PATH/FRONTEND_FIX_README.md" "$AMPLIFY_APP_PATH/"
    echo "✅ Copied: FRONTEND_FIX_README.md"
fi

echo ""

# Step 4: Check if App.js or App.jsx exists and offer to update
echo "🔍 Step 4: Checking for App.js/App.jsx..."
echo ""

APP_FILE=""
if [ -f "$AMPLIFY_APP_PATH/src/App.js" ]; then
    APP_FILE="$AMPLIFY_APP_PATH/src/App.js"
elif [ -f "$AMPLIFY_APP_PATH/src/App.jsx" ]; then
    APP_FILE="$AMPLIFY_APP_PATH/src/App.jsx"
fi

if [ -n "$APP_FILE" ]; then
    echo "✅ Found: $APP_FILE"
    
    # Check if Chatbot is already imported
    if grep -q "Chatbot" "$APP_FILE"; then
        echo -e "${YELLOW}⚠️  Chatbot already imported in $APP_FILE${NC}"
    else
        echo ""
        echo "Would you like me to add the Chatbot component to $APP_FILE? (y/n)"
        read -p "Add component: " ADD_COMPONENT
        
        if [ "$ADD_COMPONENT" = "y" ] || [ "$ADD_COMPONENT" = "Y" ]; then
            # Backup original file
            cp "$APP_FILE" "$APP_FILE.backup"
            echo "✅ Created backup: $APP_FILE.backup"
            
            # Add import if not present
            if ! grep -q "import.*Chatbot" "$APP_FILE"; then
                # Find the last import statement
                LAST_IMPORT_LINE=$(grep -n "^import" "$APP_FILE" | tail -1 | cut -d: -f1)
                if [ -n "$LAST_IMPORT_LINE" ]; then
                    sed -i.bak "${LAST_IMPORT_LINE}a\\
import Chatbot from './Chatbot';\\
import './Chatbot.css';
" "$APP_FILE"
                    rm -f "$APP_FILE.bak"
                    echo "✅ Added imports"
                fi
            fi
            
            # Add component to JSX (simple approach - add before closing div)
            if grep -q "</div>" "$APP_FILE"; then
                # Add Chatbot component before the last </div>
                sed -i.bak 's|</div>|      <Chatbot apiUrl="/api/chatbot" />\n    </div>|' "$APP_FILE"
                rm -f "$APP_FILE.bak"
                echo "✅ Added Chatbot component"
            else
                echo -e "${YELLOW}⚠️  Could not automatically add component. Please add manually:${NC}"
                echo "   <Chatbot apiUrl=\"/api/chatbot\" />"
            fi
        fi
    fi
else
    echo -e "${YELLOW}⚠️  App.js/App.jsx not found. You'll need to import manually:${NC}"
    echo "   import Chatbot from './Chatbot';"
    echo "   import './Chatbot.css';"
    echo "   <Chatbot apiUrl=\"/api/chatbot\" />"
fi

echo ""

# Step 5: Create integration guide
echo "📝 Step 5: Creating integration summary..."
echo ""

INTEGRATION_GUIDE="$AMPLIFY_APP_PATH/INTEGRATION_COMPLETE.md"

cat > "$INTEGRATION_GUIDE" << EOF
# ✅ Integration Complete!

## Files Added:
- ✅ src/Chatbot.jsx
- ✅ src/Chatbot.css
- ✅ src/useChatbot.js (optional hook)
- ✅ amplify.yml

## Next Steps:

### 1. Configure Amplify Proxy (IMPORTANT!)

Go to AWS Amplify Console:
1. Select your app: https://main.d1fw711o7cx5w2.amplifyapp.com/
2. Go to **App Settings** → **Rewrites and redirects**
3. Click **Add rewrite rule**
4. Configure:
   - **Source address:** \`/api/chatbot\`
   - **Target address:** \`http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook\`
   - **Type:** Rewrite (200)
   - **Country code:** (leave empty)

### 2. Use the Component

If not already added, import in your App.js/App.jsx:

\`\`\`jsx
import Chatbot from './Chatbot';
import './Chatbot.css';

function App() {
  return (
    <div>
      <Chatbot apiUrl="/api/chatbot" />
    </div>
  );
}
\`\`\`

### 3. Deploy

\`\`\`bash
git add .
git commit -m "Add chatbot integration"
git push
\`\`\`

### 4. Test

After deployment, test these messages:
- "Hello"
- "I am suffering from viral"
- "how can you help me"

## ✅ That's It!

The bot should now work without the "Sorry, I couldn't process" error!

## 🐛 Troubleshooting

If you still see errors:
1. Check browser console (F12) for errors
2. Verify Amplify rewrite rule is configured
3. Check Network tab to see if requests are being made
4. See FRONTEND_FIX_README.md for detailed troubleshooting

EOF

echo "✅ Created: INTEGRATION_COMPLETE.md"
echo ""

# Step 6: Summary
echo "======================================================================"
echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
echo "======================================================================"
echo ""
echo "📁 Files copied to: $AMPLIFY_APP_PATH"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure Amplify proxy (see INTEGRATION_COMPLETE.md)"
echo "2. Deploy your app"
echo "3. Test the chatbot"
echo ""
echo "📖 See INTEGRATION_COMPLETE.md for detailed instructions"
echo ""
echo "======================================================================"

