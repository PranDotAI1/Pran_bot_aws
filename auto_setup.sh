#!/bin/bash

# Auto-setup script that creates a ready-to-use integration package

set -e

echo "======================================================================"
echo "PRAN CHATBOT - AUTO SETUP"
echo "======================================================================"
echo ""

REPO_PATH="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$REPO_PATH/amplify-integration-package"

echo "📦 Creating integration package..."
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR/src"
mkdir -p "$OUTPUT_DIR"

# Copy all required files
echo "📋 Copying files..."
cp "$REPO_PATH/frontend/src/Chatbot.jsx" "$OUTPUT_DIR/src/" 2>/dev/null && echo "✅ Chatbot.jsx" || echo "⚠️  Chatbot.jsx not found"
cp "$REPO_PATH/frontend/src/Chatbot.css" "$OUTPUT_DIR/src/" 2>/dev/null && echo "✅ Chatbot.css" || echo "⚠️  Chatbot.css not found"
cp "$REPO_PATH/frontend/src/useChatbot.js" "$OUTPUT_DIR/src/" 2>/dev/null && echo "✅ useChatbot.js" || echo "⚠️  useChatbot.js not found"
cp "$REPO_PATH/amplify.yml" "$OUTPUT_DIR/" 2>/dev/null && echo "✅ amplify.yml" || echo "⚠️  amplify.yml not found"

# Create comprehensive setup instructions
cat > "$OUTPUT_DIR/README.md" << 'EOF'
# PRAN Chatbot Integration Package

## 📦 What's Included

- `src/Chatbot.jsx` - Complete React component
- `src/Chatbot.css` - Styling
- `src/useChatbot.js` - Custom hook (optional)
- `amplify.yml` - Amplify configuration

## 🚀 Quick Setup

### Step 1: Copy Files

Copy all files from this package to your Amplify app:

```bash
# Copy src files
cp src/* /path/to/your/amplify/app/src/

# Copy amplify.yml to root
cp amplify.yml /path/to/your/amplify/app/
```

### Step 2: Use the Component

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

### Step 3: Configure Amplify Proxy

**IMPORTANT:** This fixes the HTTPS/HTTP mixed content issue.

1. Go to AWS Amplify Console
2. Select your app
3. Go to **App Settings** → **Rewrites and redirects**
4. Click **Add rewrite rule**
5. Configure:
   - **Source address:** `/api/chatbot`
   - **Target address:** `http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook`
   - **Type:** Rewrite (200)
   - **Country code:** (leave empty)

### Step 4: Deploy

```bash
git add .
git commit -m "Add chatbot integration"
git push
```

## ✅ That's It!

Your bot should now work without errors!

## 🐛 Troubleshooting

See `FRONTEND_FIX_README.md` for detailed troubleshooting.
EOF

echo ""
echo "✅ Package created at: $OUTPUT_DIR"
echo ""
echo "📋 Package contents:"
ls -la "$OUTPUT_DIR"
echo ""
echo "======================================================================"
echo "✅ SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "📁 Integration package ready at:"
echo "   $OUTPUT_DIR"
echo ""
echo "📝 Next steps:"
echo "   1. Copy files from $OUTPUT_DIR to your Amplify app"
echo "   2. Follow instructions in $OUTPUT_DIR/README.md"
echo "   3. Configure Amplify proxy (see README.md)"
echo "   4. Deploy and test"
echo ""
echo "======================================================================"

