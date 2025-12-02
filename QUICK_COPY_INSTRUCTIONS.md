# Quick Copy Instructions

## 🚀 Fastest Way to Fix Your Amplify App

### Option 1: Use the Copy Script (Easiest)

```bash
# Run the copy script
./copy_to_amplify.sh /path/to/your/amplify/app

# Example:
./copy_to_amplify.sh ~/my-amplify-app
```

### Option 2: Manual Copy

Copy these files to your Amplify app:

```bash
# From the repository root, copy to your Amplify app:

# 1. Copy component files to src/
cp frontend/src/Chatbot.jsx /path/to/your/amplify/app/src/
cp frontend/src/Chatbot.css /path/to/your/amplify/app/src/
cp frontend/src/useChatbot.js /path/to/your/amplify/app/src/

# 2. Copy amplify.yml to root
cp amplify.yml /path/to/your/amplify/app/

# 3. Copy README for reference
cp FRONTEND_FIX_README.md /path/to/your/amplify/app/
```

### Option 3: Copy from GitHub

If your Amplify app is in a different location, you can:

1. **Clone or download from GitHub:**
   ```bash
   git clone https://github.com/PranDotAI1/Pran_bot_aws.git
   cd Pran_bot_aws
   ./copy_to_amplify.sh /path/to/your/amplify/app
   ```

2. **Or download individual files:**
   - Go to: https://github.com/PranDotAI1/Pran_bot_aws
   - Navigate to `frontend/src/`
   - Download: `Chatbot.jsx`, `Chatbot.css`, `useChatbot.js`
   - Download: `amplify.yml` from root

## 📋 Files to Copy

### Required Files:
- ✅ `frontend/src/Chatbot.jsx` → `your-app/src/Chatbot.jsx`
- ✅ `frontend/src/Chatbot.css` → `your-app/src/Chatbot.css`
- ✅ `amplify.yml` → `your-app/amplify.yml`

### Optional Files:
- 📖 `frontend/src/useChatbot.js` → `your-app/src/useChatbot.js` (if using hook)
- 📖 `FRONTEND_FIX_README.md` → `your-app/FRONTEND_FIX_README.md` (for reference)

## 🔧 After Copying

1. **Import in your app:**
   ```jsx
   import Chatbot from './Chatbot';
   import './Chatbot.css';
   
   function App() {
     return <Chatbot apiUrl="/api/chatbot" />;
   }
   ```

2. **Configure Amplify proxy** (fixes HTTPS/HTTP issue):
   - AWS Amplify Console → Your App → App Settings → Rewrites and redirects
   - Add rewrite:
     - Source: `/api/chatbot`
     - Target: `http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook`
     - Type: Rewrite (200)

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Add chatbot integration fix"
   git push
   ```

## ✅ That's It!

Your bot should now work without the "Sorry, I couldn't process" error!

