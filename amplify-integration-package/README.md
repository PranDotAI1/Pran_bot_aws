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
