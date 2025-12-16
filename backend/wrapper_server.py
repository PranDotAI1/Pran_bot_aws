"""
Minimal Flask Wrapper Server for Rasa Chatbot
No MongoDB - Just proxies requests to Rasa
"""

from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

RASA_URL = "http://localhost:5005"

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    try:
        response = requests.get(f"{RASA_URL}/status", timeout=2)
        if response.status_code == 200:
            return jsonify({"status": "healthy", "rasa": "connected"}), 200
    except Exception as e:
        logger.warning(f"Rasa not ready: {e}")
    
    return jsonify({"status": "starting", "rasa": "not ready"}), 200

@app.route("/rasa-webhook", methods=["POST"])
def rasa_webhook():
    """Forward requests to Rasa"""
    try:
        data = request.json
        logger.info(f"Request from {data.get('sender', 'unknown')}")
        
        response = requests.post(
            f"{RASA_URL}/webhooks/rest/webhook",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            logger.error(f"Rasa error: {response.status_code}")
            return jsonify([{"text": "Sorry, I'm having trouble connecting. Please try again."}]), 503
            
    except requests.exceptions.Timeout:
        logger.error("Rasa timeout")
        return jsonify([{"text": "Request timeout. Please try again."}]), 504
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify([{"text": "Sorry, something went wrong. Please try again."}]), 500

if __name__ == "__main__":
    logger.info("Starting minimal Flask wrapper (no MongoDB)")
    app.run(host="0.0.0.0", port=5000)
