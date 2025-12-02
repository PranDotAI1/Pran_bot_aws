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

