/**
 * Custom React Hook for Chatbot Integration
 * Handles API communication with proper error handling
 */

import { useState, useCallback, useRef } from 'react';

/**
 * Custom hook for chatbot functionality
 * @param {string} apiUrl - API endpoint URL
 * @param {string} senderId - User ID (optional, auto-generated if not provided)
 * @returns {Object} Chatbot state and functions
 */
export const useChatbot = (apiUrl, senderId = null) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Generate or use provided sender ID
  const userIdRef = useRef(senderId || `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  /**
   * Send message to chatbot API
   * Always returns a helpful response, never throws errors to user
   */
  const sendMessage = useCallback(async (messageText) => {
    if (!messageText || !messageText.trim()) {
      return;
    }

    // Add user message
    const userMessage = {
      id: `user_${Date.now()}`,
      text: messageText.trim(),
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      // Determine API URL - use proxy if available, otherwise direct
      const apiEndpoint = apiUrl || '/api/chatbot';
      
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: userIdRef.current,
          message: messageText.trim()
        }),
        signal: AbortSignal.timeout(30000) // 30 second timeout
      });

      // Handle non-OK responses gracefully
      if (!response.ok) {
        console.error('API Error:', response.status, response.statusText);
        // Return helpful fallback instead of error
        throw new Error(`Server returned status ${response.status}`);
      }

      // Parse response
      let data;
      try {
        data = await response.json();
      } catch (parseError) {
        console.error('JSON Parse Error:', parseError);
        throw new Error('Invalid response format');
      }

      // Process response - handle different formats
      let botMessages = [];
      
      if (Array.isArray(data)) {
        // Expected format: array of messages
        botMessages = data
          .filter(msg => msg && (msg.text || msg.message))
          .map(msg => ({
            text: msg.text || msg.message,
            recipient_id: msg.recipient_id || userIdRef.current
          }));
      } else if (data && typeof data === 'object') {
        // Single message object
        if (data.text || data.message) {
          botMessages = [{
            text: data.text || data.message,
            recipient_id: data.recipient_id || userIdRef.current
          }];
        } else if (data.error) {
          // Error object - use fallback
          throw new Error(data.error);
        }
      }

      // If no valid messages, provide helpful fallback
      if (botMessages.length === 0) {
        throw new Error('No response received');
      }

      // Add bot messages to chat
      botMessages.forEach((msg, index) => {
        const botMessage = {
          id: `bot_${Date.now()}_${index}`,
          text: msg.text || 'I received your message. How can I help you?',
          sender: 'bot',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botMessage]);
      });

      return botMessages;

    } catch (error) {
      console.error('Chatbot Error:', error);
      
      // Determine helpful fallback based on error type
      let fallbackMessage = "I'm here to help with all your healthcare needs. How can I assist you today?";
      
      if (error.name === 'AbortError' || error.message.includes('timeout')) {
        fallbackMessage = "The request took too long. Please try again, or ask me about appointments, insurance, or finding a doctor.";
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        fallbackMessage = "I'm having trouble connecting right now. Please check your internet connection and try again.";
      } else if (error.message.includes('CORS') || error.message.includes('Mixed Content')) {
        fallbackMessage = "There's a connection configuration issue. Please try again or contact support.";
      } else if (error.message.includes('status 5')) {
        fallbackMessage = "The server is temporarily unavailable. Please try again in a moment.";
      }

      // Add helpful fallback message
      const errorBotMessage = {
        id: `bot_error_${Date.now()}`,
        text: fallbackMessage,
        sender: 'bot',
        timestamp: new Date(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorBotMessage]);
      setError(error.message);
      
      return [errorBotMessage];
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  /**
   * Clear chat history
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  /**
   * Add a welcome message
   */
  const addWelcomeMessage = useCallback((message = "Hi, how can I assist you today?") => {
    const welcomeMessage = {
      id: 'welcome',
      text: message,
      sender: 'bot',
      timestamp: new Date()
    };
    setMessages(prev => [welcomeMessage, ...prev]);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
    addWelcomeMessage,
    userId: userIdRef.current
  };
};

export default useChatbot;

