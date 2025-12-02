import React, { useState, useRef, useEffect } from 'react';
import './Chatbot.css';

/**
 * PRAN Chatbot Component
 * Production-ready React component for integrating with PRAN Chatbot API
 * 
 * Usage:
 * <Chatbot apiUrl="http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook" />
 */
const Chatbot = ({ 
  apiUrl = 'http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook',
  senderId = null,
  placeholder = "Type your message...",
  welcomeMessage = "Hi, how can I assist you today?",
  showWelcome = true
}) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Generate or use provided sender ID
  const [userId] = useState(() => {
    if (senderId) return senderId;
    // Generate a unique user ID
    return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  });

  // Initialize with welcome message
  useEffect(() => {
    if (showWelcome && messages.length === 0) {
      setMessages([{
        id: 'welcome',
        text: welcomeMessage,
        sender: 'bot',
        timestamp: new Date()
      }]);
    }
  }, [showWelcome, welcomeMessage, messages.length]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Send message to chatbot API
   * Handles errors gracefully and always returns a helpful response
   */
  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    // Add user message to chat
    const userMessage = {
      id: `user_${Date.now()}`,
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      // Make API request
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: userId,
          message: messageText
        }),
        // Increase timeout for slow connections
        signal: AbortSignal.timeout(30000) // 30 seconds
      });

      // Check if response is OK
      if (!response.ok) {
        console.error('API Error:', response.status, response.statusText);
        // Return helpful fallback instead of error
        throw new Error(`API returned status ${response.status}`);
      }

      // Parse response
      let data;
      try {
        data = await response.json();
      } catch (parseError) {
        console.error('JSON Parse Error:', parseError);
        throw new Error('Invalid response format from server');
      }

      // Validate and process response
      let botMessages = [];
      
      if (Array.isArray(data)) {
        // Response is an array (expected format)
        botMessages = data.filter(msg => msg && msg.text);
      } else if (data && typeof data === 'object') {
        // Response is a single object
        if (data.text) {
          botMessages = [data];
        } else if (data.error) {
          // Error object - use fallback
          throw new Error(data.error);
        }
      }

      // If no valid messages, use fallback
      if (botMessages.length === 0) {
        throw new Error('No response from server');
      }

      // Add bot messages to chat
      botMessages.forEach((msg, index) => {
        const botMessage = {
          id: `bot_${Date.now()}_${index}`,
          text: msg.text || 'I received your message, but I\'m having trouble processing it right now.',
          sender: 'bot',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botMessage]);
      });

    } catch (error) {
      console.error('Chatbot Error:', error);
      
      // Determine error type and provide helpful fallback
      let errorMessage = "I'm here to help with all your healthcare needs. How can I assist you today?";
      
      if (error.name === 'AbortError' || error.message.includes('timeout')) {
        errorMessage = "The request took too long. Please try again, or ask me about appointments, insurance, or finding a doctor.";
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage = "I'm having trouble connecting right now. Please check your internet connection and try again.";
      } else if (error.message.includes('CORS') || error.message.includes('Mixed Content')) {
        errorMessage = "There's a connection issue. Please contact support or try again later.";
      }

      // Add helpful error message as bot response
      const errorBotMessage = {
        id: `bot_error_${Date.now()}`,
        text: errorMessage,
        sender: 'bot',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorBotMessage]);
      setError(error.message);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!loading && input.trim()) {
      sendMessage(input.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-messages">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`chatbot-message ${message.sender} ${message.isError ? 'error' : ''}`}
          >
            <div className="message-content">
              {message.text}
            </div>
            <div className="message-timestamp">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chatbot-message bot loading">
            <div className="message-content">
              <span className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chatbot-input-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={loading}
          className="chatbot-input"
          autoFocus
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="chatbot-send-button"
          aria-label="Send message"
        >
          {loading ? (
            <span className="spinner"></span>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          )}
        </button>
      </form>

      {error && (
        <div className="chatbot-error-banner">
          <small>Connection issue detected. Showing fallback response.</small>
        </div>
      )}
    </div>
  );
};

export default Chatbot;

