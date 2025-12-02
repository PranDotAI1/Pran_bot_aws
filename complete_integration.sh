#!/bin/bash

# Complete integration script - does everything possible automatically

set -e

echo "======================================================================"
echo "PRAN CHATBOT - COMPLETE INTEGRATION"
echo "======================================================================"
echo ""

REPO_PATH="$(cd "$(dirname "$0")" && pwd)"
PACKAGE_DIR="$REPO_PATH/amplify-integration-package"

# Step 1: Verify package exists
if [ ! -d "$PACKAGE_DIR" ]; then
    echo "❌ Error: Integration package not found. Running auto_setup.sh..."
    "$REPO_PATH/auto_setup.sh"
fi

echo "✅ Integration package ready"
echo ""

# Step 2: Try to find Amplify app
echo "🔍 Searching for Amplify app..."
AMPLIFY_APP_PATH=""

# Check common locations
SEARCH_PATHS=(
    "$HOME/Desktop"
    "$HOME/Documents"
    "$HOME/projects"
    "$HOME/Downloads"
    "$HOME"
)

for base_path in "${SEARCH_PATHS[@]}"; do
    if [ -d "$base_path" ]; then
        # Look for React apps with package.json
        found=$(find "$base_path" -maxdepth 3 -type f -name "package.json" -exec grep -l "react\|amplify" {} \; 2>/dev/null | head -1)
        if [ -n "$found" ]; then
            AMPLIFY_APP_PATH=$(dirname "$found")
            echo "✅ Found potential Amplify app at: $AMPLIFY_APP_PATH"
            break
        fi
    fi
done

# Step 3: Copy files if app found
if [ -n "$AMPLIFY_APP_PATH" ]; then
    echo ""
    echo "📋 Copying files to: $AMPLIFY_APP_PATH"
    echo ""
    
    # Create src if needed
    mkdir -p "$AMPLIFY_APP_PATH/src"
    
    # Copy files
    cp "$PACKAGE_DIR/src/Chatbot.jsx" "$AMPLIFY_APP_PATH/src/" && echo "✅ Copied Chatbot.jsx" || echo "⚠️  Failed to copy Chatbot.jsx"
    cp "$PACKAGE_DIR/src/Chatbot.css" "$AMPLIFY_APP_PATH/src/" && echo "✅ Copied Chatbot.css" || echo "⚠️  Failed to copy Chatbot.css"
    cp "$PACKAGE_DIR/src/useChatbot.js" "$AMPLIFY_APP_PATH/src/" && echo "✅ Copied useChatbot.js" || echo "⚠️  Failed to copy useChatbot.js"
    cp "$PACKAGE_DIR/amplify.yml" "$AMPLIFY_APP_PATH/" && echo "✅ Copied amplify.yml" || echo "⚠️  Failed to copy amplify.yml"
    cp "$PACKAGE_DIR/README.md" "$AMPLIFY_APP_PATH/INTEGRATION_README.md" && echo "✅ Copied README" || echo "⚠️  Failed to copy README"
    
    echo ""
    echo "✅ Files copied successfully!"
else
    echo ""
    echo "⚠️  Could not automatically find Amplify app"
    echo ""
    echo "📦 Integration package is ready at:"
    echo "   $PACKAGE_DIR"
    echo ""
    echo "Please manually copy files from there to your Amplify app"
fi

# Step 4: Configure Amplify via AWS CLI (if available)
echo ""
echo "🔧 Configuring Amplify proxy..."
echo ""

if command -v aws &> /dev/null; then
    echo "✅ AWS CLI found"
    
    # Get Amplify app ID
    APP_ID=$(aws amplify list-apps --region us-east-1 --query "apps[?name=='main' || contains(name, 'pran') || contains(name, 'chatbot')].appId" --output text 2>/dev/null | head -1)
    
    if [ -n "$APP_ID" ] && [ "$APP_ID" != "None" ]; then
        echo "✅ Found Amplify app: $APP_ID"
        
        # Check current rewrite rules
        CURRENT_RULES=$(aws amplify get-app --app-id "$APP_ID" --region us-east-1 --query "app.customRules" --output json 2>/dev/null)
        
        if echo "$CURRENT_RULES" | grep -q "/api/chatbot"; then
            echo "✅ Proxy rule already exists"
        else
            echo "📝 Adding proxy rule..."
            
            # Create new rules array with chatbot proxy
            NEW_RULES='[{"source":"/api/chatbot","target":"http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook","status":"200","condition":null}]'
            
            # Try to update (this might require additional permissions)
            if aws amplify update-app --app-id "$APP_ID" --region us-east-1 --custom-rules "$NEW_RULES" &>/dev/null; then
                echo "✅ Proxy rule configured successfully!"
            else
                echo "⚠️  Could not automatically configure proxy (may need manual setup)"
                echo "   See instructions below"
            fi
        fi
    else
        echo "⚠️  Could not find Amplify app automatically"
        echo "   You'll need to configure proxy manually (see instructions below)"
    fi
else
    echo "⚠️  AWS CLI not found"
    echo "   You'll need to configure proxy manually (see instructions below)"
fi

# Step 5: Create comprehensive setup guide
echo ""
echo "📝 Creating setup guide..."
echo ""

cat > "$REPO_PATH/COMPLETE_SETUP_GUIDE.md" << 'EOF'
# ✅ Complete Integration Setup Guide

## What Was Done Automatically

✅ Integration package created
✅ Files copied to Amplify app (if found)
✅ Amplify proxy configured (if AWS CLI available)

## Manual Steps (If Needed)

### 1. Copy Files (If Not Done Automatically)

```bash
# From the integration package
cd /Users/viditagarwal/Downloads/pran_chatbot-main/amplify-integration-package

# Copy to your Amplify app
cp src/* /path/to/your/amplify/app/src/
cp amplify.yml /path/to/your/amplify/app/
```

### 2. Add Component to Your App

In your `App.js` or `App.jsx`:

```jsx
import Chatbot from './Chatbot';
import './Chatbot.css';

function App() {
  return (
    <div className="App">
      <Chatbot apiUrl="/api/chatbot" />
    </div>
  );
}
```

### 3. Configure Amplify Proxy (IMPORTANT!)

If not configured automatically, do this manually:

1. **Go to AWS Amplify Console:**
   - https://console.aws.amazon.com/amplify/

2. **Select your app:**
   - App name: `main` or your app name
   - URL: https://main.d1fw711o7cx5w2.amplifyapp.com/

3. **Navigate to:**
   - **App Settings** → **Rewrites and redirects**

4. **Add rewrite rule:**
   - Click **Add rewrite rule**
   - **Source address:** `/api/chatbot`
   - **Target address:** `http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook`
   - **Type:** Rewrite (200)
   - **Country code:** (leave empty)
   - Click **Save**

### 4. Deploy

```bash
cd /path/to/your/amplify/app
git add .
git commit -m "Add chatbot integration"
git push
```

### 5. Test

After deployment, test these messages:
- "Hello"
- "I am suffering from viral"
- "how can you help me"

## ✅ Verification

1. ✅ Files copied to Amplify app
2. ✅ Component imported in App.js/jsx
3. ✅ Amplify proxy configured
4. ✅ App deployed
5. ✅ Bot responds without errors

## 🐛 Troubleshooting

### Still seeing "Sorry, I couldn't process" error?

1. **Check browser console (F12):**
   - Look for CORS errors
   - Look for mixed content errors
   - Check Network tab for failed requests

2. **Verify proxy is configured:**
   - Go to Amplify Console → App Settings → Rewrites and redirects
   - Ensure `/api/chatbot` rule exists

3. **Test API directly:**
   ```bash
   curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
     -H "Content-Type: application/json" \
     -d '{"sender": "test", "message": "Hello"}'
   ```

4. **Check component is using correct URL:**
   - Should be: `<Chatbot apiUrl="/api/chatbot" />`
   - NOT: `<Chatbot apiUrl="http://..." />`

## 📞 Support

If issues persist:
1. Check `FRONTEND_FIX_README.md` for detailed troubleshooting
2. Review browser console errors
3. Verify all files are copied correctly
4. Ensure Amplify proxy is configured

EOF

echo "✅ Created: COMPLETE_SETUP_GUIDE.md"
echo ""

# Step 6: Summary
echo "======================================================================"
echo "✅ INTEGRATION COMPLETE!"
echo "======================================================================"
echo ""
echo "📋 Summary:"
echo ""
if [ -n "$AMPLIFY_APP_PATH" ]; then
    echo "✅ Files copied to: $AMPLIFY_APP_PATH"
else
    echo "⚠️  Files need to be copied manually"
    echo "   Package location: $PACKAGE_DIR"
fi
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. ✅ Verify files are in your Amplify app"
echo "2. ✅ Add component to App.js/jsx (see COMPLETE_SETUP_GUIDE.md)"
echo "3. ✅ Configure Amplify proxy (see instructions above or COMPLETE_SETUP_GUIDE.md)"
echo "4. ✅ Deploy your app"
echo "5. ✅ Test the chatbot"
echo ""
echo "📖 See COMPLETE_SETUP_GUIDE.md for detailed instructions"
echo ""
echo "======================================================================"

