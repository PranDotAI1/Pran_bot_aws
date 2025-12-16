"""
Streamlit UI Demo for PRAN Chatbot
Professional chat interface to demonstrate the chatbot capabilities
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict

# Page configuration
st.set_page_config(
 page_title="PRAN Chatbot Demo",
 page_icon="",
 layout="wide",
 initial_sidebar_state="expanded"
)

# Production API endpoint
PRODUCTION_API_URL = "http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080"

# Custom CSS for better styling
st.markdown("""
 <style>
 .main-header {
 font-size: 2.5rem;
 font-weight: bold;
 color: #1f77b4;
 text-align: center;
 margin-bottom: 1rem;
 }
 .chat-message {
 padding: 1rem;
 border-radius: 0.5rem;
 margin-bottom: 1rem;
 display: flex;
 align-items: flex-start;
 }
 .user-message {
 background-color: #e3f2fd;
 margin-left: 20%;
 }
 .bot-message {
 background-color: #f5f5f5;
 margin-right: 20%;
 }
 .message-time {
 font-size: 0.75rem;
 color: #666;
 margin-top: 0.5rem;
 }
 .stButton>button {
 width: 100%;
 background-color: #1f77b4;
 color: white;
 font-weight: bold;
 }
 </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
 st.session_state.messages = []
if 'user_id' not in st.session_state:
 import uuid
 st.session_state.user_id = str(uuid.uuid4())
if 'api_status' not in st.session_state:
 st.session_state.api_status = None

def check_health():
 """Check if the API is healthy"""
 try:
 response = requests.get(f"{PRODUCTION_API_URL}/health", timeout=5)
 if response.status_code == 200:
 data = response.json()
 return {
 'status': 'healthy',
 'flask_wrapper': data.get('flask_wrapper', 'unknown'),
 'rasa_status': data.get('rasa_status', 'unknown'),
 'mongodb_status': data.get('mongodb_status', 'unknown')
 }
 else:
 return {'status': 'unhealthy', 'error': f'Status code: {response.status_code}'}
 except Exception as e:
 return {'status': 'error', 'error': str(e)}

def send_message(user_id: str, message: str) -> List[Dict]:
 """Send message to chatbot API"""
 try:
 response = requests.post(
 f"{PRODUCTION_API_URL}/rasa-webhook",
 json={
 "sender": user_id,
 "message": message
 },
 headers={"Content-Type": "application/json"},
 timeout=30
 )
 
 if response.status_code == 200:
 return response.json()
 else:
 return [{"text": f"Error: {response.status_code} - {response.text}", "recipient_id": user_id}]
 except requests.exceptions.Timeout:
 return [{"text": "Request timed out. Please try again.", "recipient_id": user_id}]
 except requests.exceptions.ConnectionError:
 return [{"text": "Cannot connect to the chatbot. Please check your connection.", "recipient_id": user_id}]
 except Exception as e:
 return [{"text": f"Error: {str(e)}", "recipient_id": user_id}]

# Header
st.markdown('<div class="main-header"> PRAN Healthcare Chatbot Demo</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
 st.header("⚙ Configuration")
 
 # API URL (editable)
 api_url = st.text_input(
 "API Base URL",
 value=PRODUCTION_API_URL,
 help="Base URL for the chatbot API"
 )
 
 # Health check
 st.subheader(" Health Check")
 if st.button("Check API Status"):
 with st.spinner("Checking API status..."):
 health = check_health()
 st.session_state.api_status = health
 
 if st.session_state.api_status:
 status = st.session_state.api_status
 if status['status'] == 'healthy':
 st.success(" API is Healthy")
 st.json(status)
 else:
 st.error(f" API Error: {status.get('error', 'Unknown error')}")
 
 st.divider()
 
 # User ID display
 st.subheader(" Session Info")
 st.text(f"User ID: {st.session_state.user_id[:8]}...")
 
 if st.button(" New Session"):
 st.session_state.messages = []
 import uuid
 st.session_state.user_id = str(uuid.uuid4())
 st.rerun()
 
 st.divider()
 
 # API Endpoints info
 st.subheader(" API Endpoints")
 st.text("Health: /health")
 st.text("Chat: /rasa-webhook")
 
 st.divider()
 
 # Instructions
 st.subheader(" Instructions")
 st.markdown("""
 1. Type your message in the input box
 2. Click Send or press Enter
 3. The bot will respond
 4. Check health status in sidebar
 """)

# Main chat area
st.subheader(" Chat")

# Example questions
if not st.session_state.messages:
 st.info(" Welcome! Start a conversation with the PRAN Healthcare Chatbot.")
 st.markdown("### Try asking:")
 example_questions = [
 "Hello, I need help",
 "What are the symptoms of diabetes?",
 "I want to book an appointment",
 "Tell me about hypertension",
 "How can I manage my blood pressure?"
 ]
 
 cols = st.columns(len(example_questions))
 for i, question in enumerate(example_questions):
 with cols[i]:
 if st.button(question, key=f"example_{i}"):
 # Simulate user input
 user_input = question
 user_message = {
 'role': 'user',
 'content': user_input,
 'timestamp': datetime.now().strftime("%H:%M:%S")
 }
 st.session_state.messages.append(user_message)
 
 # Get bot response
 with st.spinner(" Thinking..."):
 responses = send_message(st.session_state.user_id, user_input)
 
 # Display bot responses
 for response in responses:
 bot_text = response.get('text', 'No response')
 bot_message = {
 'role': 'assistant',
 'content': bot_text,
 'timestamp': datetime.now().strftime("%H:%M:%S")
 }
 st.session_state.messages.append(bot_message)
 
 st.rerun()

# Display chat messages
chat_container = st.container()
with chat_container:
 
 # Display all messages
 for message in st.session_state.messages:
 role = message['role']
 content = message['content']
 timestamp = message.get('timestamp', '')
 
 if role == 'user':
 with st.chat_message("user"):
 st.write(content)
 if timestamp:
 st.caption(timestamp)
 else:
 with st.chat_message("assistant"):
 st.write(content)
 if timestamp:
 st.caption(timestamp)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
 # Add user message to chat
 user_message = {
 'role': 'user',
 'content': user_input,
 'timestamp': datetime.now().strftime("%H:%M:%S")
 }
 st.session_state.messages.append(user_message)
 
 # Show user message immediately
 with st.chat_message("user"):
 st.write(user_input)
 st.caption(user_message['timestamp'])
 
 # Get bot response
 with st.spinner(" Thinking..."):
 responses = send_message(st.session_state.user_id, user_input)
 
 # Display bot responses
 for response in responses:
 bot_text = response.get('text', 'No response')
 bot_message = {
 'role': 'assistant',
 'content': bot_text,
 'timestamp': datetime.now().strftime("%H:%M:%S")
 }
 st.session_state.messages.append(bot_message)
 
 with st.chat_message("assistant"):
 st.write(bot_text)
 st.caption(bot_message['timestamp'])
 
 # Rerun to update the display
 st.rerun()

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
 st.markdown("**API Endpoint:**")
 st.text(f"{PRODUCTION_API_URL}/rasa-webhook")
with col2:
 st.markdown("**Status:**")
 if st.session_state.api_status and st.session_state.api_status.get('status') == 'healthy':
 st.success(" Online")
 else:
 st.warning(" Check Status")
with col3:
 st.markdown("**Messages:**")
 st.text(f"{len(st.session_state.messages)} messages")

