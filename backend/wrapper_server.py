"""
Flask Wrapper Server for Rasa Chatbot
Production-ready API gateway with MongoDB integration
"""

from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Load environment variables
load_dotenv()

# Configuration from environment variables
RASA_WEBHOOK_URL = os.getenv("RASA_WEBHOOK_URL", "http://localhost:5005/webhooks/rest/webhook")
RASA_STATUS_URL = os.getenv("RASA_STATUS_URL", "http://localhost:5005/status")
MONGODB_URI = os.getenv("MONGODB_URI")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# Initialize MongoDB client
mongodb_client = None
mongodb_db = None

def connect_mongodb():
    """Connect to MongoDB database"""
    global mongodb_client, mongodb_db
    
    if not MONGODB_URI:
        logger.warning("MONGODB_URI not configured. MongoDB features will be disabled.")
        return False
    
    try:
        mongodb_client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        # Test the connection
        mongodb_client.admin.command('ping')
        # Get the default database (or specify one)
        mongodb_db = mongodb_client.get_database()
        logger.info(f"Successfully connected to MongoDB at {mongodb_client.address}")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection error: {e}")
        mongodb_client = None
        mongodb_db = None
        return False

# Connect to MongoDB on startup if URI is provided
if MONGODB_URI:
    connect_mongodb()

def get_mongodb_db(db_name=None):
    """Get MongoDB database instance"""
    global mongodb_client, mongodb_db
    if mongodb_client is None:
        if not connect_mongodb():
            return None
    
    if db_name:
        return mongodb_client[db_name]
    return mongodb_db

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

@app.route("/mongodb/test", methods=["GET"])
def test_mongodb():
    """Test MongoDB connection and list databases"""
    if not MONGODB_URI:
        return jsonify({
            "status": "error",
            "message": "MongoDB not configured"
        }), 503
    
    try:
        if mongodb_client is None:
            if not connect_mongodb():
                return jsonify({
                    "status": "error",
                    "message": "Failed to connect to MongoDB"
                }), 500
        
        # Test connection
        mongodb_client.admin.command('ping')
        
        # List databases
        db_list = mongodb_client.list_database_names()
        
        return jsonify({
            "status": "success",
            "message": "MongoDB connection successful",
            "databases": db_list,
            "address": str(mongodb_client.address)
        }), 200
    except Exception as e:
        logger.error(f"MongoDB test error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/mongodb/explore", methods=["GET"])
def explore_mongodb():
    """Explore MongoDB structure: databases, collections, and sample data"""
    if not MONGODB_URI:
        return jsonify({
            "status": "error",
            "message": "MongoDB not configured"
        }), 503
    
    try:
        if mongodb_client is None:
            if not connect_mongodb():
                return jsonify({
                    "status": "error",
                    "message": "Failed to connect to MongoDB"
                }), 500
        
        # Test connection
        mongodb_client.admin.command('ping')
        
        # Get all databases (excluding system databases)
        all_databases = mongodb_client.list_database_names()
        system_dbs = ['admin', 'config', 'local']
        databases = [db for db in all_databases if db not in system_dbs]
        
        result = {
            "status": "success",
            "connection": {
                "address": str(mongodb_client.address),
                "total_databases": len(all_databases),
                "user_databases": len(databases)
            },
            "databases": []
        }
        
        # Explore each database
        for db_name in databases:
            try:
                db = mongodb_client[db_name]
                collections = db.list_collection_names()
                
                db_info = {
                    "name": db_name,
                    "collections_count": len(collections),
                    "collections": []
                }
                
                # Explore each collection
                for collection_name in collections:
                    try:
                        collection = db[collection_name]
                        doc_count = collection.count_documents({})
                        
                        # Get sample documents (max 3)
                        sample_docs = list(collection.find().limit(3))
                        
                        # Get field names from sample documents
                        field_names = set()
                        for doc in sample_docs:
                            field_names.update(doc.keys())
                        
                        collection_info = {
                            "name": collection_name,
                            "document_count": doc_count,
                            "fields": sorted(list(field_names)),
                            "sample_documents": []
                        }
                        
                        # Add sample documents (convert ObjectId to string)
                        for doc in sample_docs:
                            # Convert ObjectId and other non-serializable types
                            doc_str = json.dumps(doc, default=json_serial)
                            collection_info["sample_documents"].append(json.loads(doc_str))
                        
                        db_info["collections"].append(collection_info)
                    except Exception as e:
                        logger.error(f"Error reading collection {collection_name}: {e}")
                        db_info["collections"].append({
                            "name": collection_name,
                            "error": str(e)
                        })
                
                result["databases"].append(db_info)
            except Exception as e:
                logger.error(f"Error accessing database {db_name}: {e}")
                result["databases"].append({
                    "name": db_name,
                    "error": str(e)
                })
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"MongoDB explore error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    try:
        # Check if Rasa is responding
        rasa_check = requests.get(RASA_STATUS_URL, timeout=2)
        rasa_status = "connected" if rasa_check.status_code == 200 else "disconnected"
    except Exception as e:
        logger.warning(f"Rasa health check failed: {e}")
        rasa_status = "disconnected"
    
    # Check MongoDB connection
    mongodb_status = "not_configured"
    if MONGODB_URI:
        mongodb_status = "connected" if mongodb_client is not None else "disconnected"
        if mongodb_client:
            try:
                mongodb_client.admin.command('ping')
            except Exception as e:
                logger.warning(f"MongoDB ping failed: {e}")
                mongodb_status = "disconnected"
                connect_mongodb()  # Try to reconnect
    
    return jsonify({
        "status": "healthy",
        "flask_wrapper": "running",
        "rasa_status": rasa_status,
        "mongodb_status": mongodb_status,
        "rasa_webhook_url": RASA_WEBHOOK_URL
    }), 200

@app.route("/rasa-webhook", methods=["POST"])
def rasa_wrapper():
    """Forward requests to Rasa webhook"""
    logger.info("Request received at /rasa-webhook")
    try:
        data = request.json
        if not data:
            return jsonify([{"text": "I'm here to help! Please send me a message.", "recipient_id": "default"}]), 200
        
        # Ensure required fields exist
        sender_id = data.get("sender", "default")
        message = data.get("message", "")
        metadata = data.get("metadata", {})
        
        if not message or not message.strip():
            return jsonify([{"text": "I'm here to help! Please send me a message.", "recipient_id": sender_id}]), 200
        
        rasa_payload = {
            "sender": sender_id,
            "message": message,
        }
        
        if metadata:
            logger.debug(f"Metadata received: {metadata}")
        
        # Forward request to Rasa
        try:
        rasa_response = requests.post(RASA_WEBHOOK_URL, json=rasa_payload, timeout=30)
            rasa_response.raise_for_status()  # Raise exception for bad status codes
        rasa_response_data = rasa_response.json()
        
            # Ensure response is in correct format (array of messages)
            if not isinstance(rasa_response_data, list):
                # If response is not a list, wrap it
                if isinstance(rasa_response_data, dict):
                    if "text" in rasa_response_data:
                        rasa_response_data = [rasa_response_data]
                    else:
                        # Create a helpful response
                        rasa_response_data = [{"text": "I'm here to help with all your healthcare needs. How can I assist you today?", "recipient_id": sender_id}]
                else:
                    rasa_response_data = [{"text": "I'm here to help with all your healthcare needs. How can I assist you today?", "recipient_id": sender_id}]
            
            # Ensure all responses have recipient_id
            for resp in rasa_response_data:
                if isinstance(resp, dict) and "recipient_id" not in resp:
                    resp["recipient_id"] = sender_id
            
            # If response is empty, provide a helpful fallback
            if not rasa_response_data or len(rasa_response_data) == 0:
                rasa_response_data = [{"text": "I'm here to help with all your healthcare needs - appointments, insurance, health questions, and more. What would you like to know?", "recipient_id": sender_id}]
            
            return jsonify(rasa_response_data), 200
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Rasa HTTP error: {e}")
            # Return helpful response instead of error
            return jsonify([{"text": "I'm here to help with all your healthcare needs. How can I assist you today?", "recipient_id": sender_id}]), 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Rasa request error: {e}")
            # Return helpful response instead of error
            return jsonify([{"text": "I'm here to help with all your healthcare needs. How can I assist you today?", "recipient_id": sender_id}]), 200
    
    except Exception as e:
        logger.error(f"Unexpected error in rasa_wrapper: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Always return a helpful response, never an error
        sender_id = request.json.get("sender", "default") if request.json else "default"
        return jsonify([{"text": "I'm here to help with all your healthcare needs - appointments, insurance, health questions, and more. What would you like to know?", "recipient_id": sender_id}]), 200

if __name__ == "__main__":
    logger.info(f"Starting Flask wrapper server on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

