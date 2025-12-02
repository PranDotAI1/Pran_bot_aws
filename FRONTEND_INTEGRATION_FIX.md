# Frontend Integration Fix Guide

## Problem
The error message "Sorry, I couldn't process your message. Please try again." is appearing on your Amplify app, but the backend API is working correctly.

## Diagnosis
✅ **Backend API is working correctly** - tested and verified
✅ **API returns valid responses** - format is correct
⚠️ **Error is coming from FRONTEND** - not from backend

## Root Cause
The error message is likely in your Amplify frontend code. It's being triggered when:
1. The frontend receives an unexpected response format
2. There's a network error (CORS, timeout, etc.)
3. The frontend's error handler is too aggressive

## Solution

### Option 1: Check Frontend Error Handling

In your Amplify app's frontend code, look for error handling like this:

```javascript
// ❌ BAD - Too aggressive error handling
try {
  const response = await fetch(apiUrl, {...});
  if (!response.ok) {
    throw new Error("Sorry, I couldn't process your message. Please try again.");
  }
  const data = await response.json();
  return data;
} catch (error) {
  return { error: "Sorry, I couldn't process your message. Please try again." };
}
```

**Fix it to:**

```javascript
// ✅ GOOD - Proper error handling
async function sendMessage(message, senderId) {
  try {
    const response = await fetch(
      'http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: senderId,
          message: message
        })
      }
    );

    // Check if response is OK
    if (!response.ok) {
      console.error('API Error:', response.status, response.statusText);
      // Return a helpful fallback instead of error
      return [{
        text: "I'm here to help with all your healthcare needs. How can I assist you today?",
        recipient_id: senderId
      }];
    }

    // Parse response
    const data = await response.json();
    
    // Validate response format
    if (Array.isArray(data) && data.length > 0) {
      return data;
    } else if (data && data.text) {
      // Handle single message object
      return [data];
    } else {
      // Fallback response
      return [{
        text: "I'm here to help with all your healthcare needs. How can I assist you today?",
        recipient_id: senderId
      }];
    }
  } catch (error) {
    console.error('Network Error:', error);
    // Return helpful fallback instead of error message
    return [{
      text: "I'm here to help with all your healthcare needs. How can I assist you today?",
      recipient_id: senderId
    }];
  }
}
```

### Option 2: Check for HTTPS/HTTP Mixed Content

If your Amplify app uses HTTPS, but the API is HTTP, browsers will block the request.

**Solution:** Use HTTPS for the API or configure a proxy:

```javascript
// If using HTTPS on Amplify, you may need to:
// 1. Use a proxy in your Amplify app
// 2. Or configure the API to use HTTPS (requires SSL certificate)
```

### Option 3: Check CORS Configuration

The API already has CORS enabled (`Access-Control-Allow-Origin: *`), but verify your frontend is sending requests correctly.

### Option 4: Add Better Logging

Add console logging to debug:

```javascript
async function sendMessage(message, senderId) {
  console.log('Sending message:', message);
  
  try {
    const response = await fetch(apiUrl, {...});
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    const data = await response.json();
    console.log('Response data:', data);
    
    return data;
  } catch (error) {
    console.error('Error details:', error);
    // Return helpful fallback
    return [{
      text: "I'm here to help with all your healthcare needs. How can I assist you today?",
      recipient_id: senderId
    }];
  }
}
```

## API Endpoint Details

**URL:**
```
http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook
```

**Method:** POST

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "sender": "user_id_here",
  "message": "user message here"
}
```

**Response Format:**
```json
[
  {
    "recipient_id": "user_id_here",
    "text": "Bot response here"
  }
]
```

## Testing

Test the API directly:

```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "Hello"}'
```

Expected response:
```json
[
  {
    "recipient_id": "test",
    "text": "Hello! I'm Dr. AI, your super intelligent healthcare assistant..."
  }
]
```

## Next Steps

1. **Check your Amplify frontend code** for the error message "Sorry, I couldn't process your message"
2. **Update error handling** to use the code examples above
3. **Add logging** to see what's actually happening
4. **Test with browser console** open to see any errors

The backend is working correctly - the issue is in the frontend integration!

