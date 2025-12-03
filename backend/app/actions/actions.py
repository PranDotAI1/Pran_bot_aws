from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import boto3
import json
import requests
from typing import Any, Dict, List, Text
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
from rasa_sdk.events import SlotSet
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.pool
from datetime import datetime, timedelta
import logging
import threading
import time
import hashlib

# Import RAG system, AWS Intelligence, Text-to-SQL Agent, and Symptom Analyzer
try:
    from .rag_system import RAGRetriever
    from .aws_intelligence import AWSIntelligenceServices
    from .text_to_sql_agent import TextToSQLAgent
    from .symptom_analyzer import SymptomAnalyzer
except ImportError:
    # Fallback if relative import doesn't work
    import sys
    sys.path.append(os.path.dirname(__file__))
    from rag_system import RAGRetriever
    from aws_intelligence import AWSIntelligenceServices
    try:
        from text_to_sql_agent import TextToSQLAgent
    except ImportError:
        TextToSQLAgent = None
    try:
        from symptom_analyzer import SymptomAnalyzer
    except ImportError:
        SymptomAnalyzer = None

load_dotenv()

REACT_APP_DUMMY_API = os.getenv("REACT_APP_DUMMY_API")

# ============================================================================
# ROBUST DUPLICATE PREVENTION SYSTEM
# ============================================================================

class SafeDispatcher:
    """Wrapper around CollectingDispatcher that prevents duplicate messages"""
    
    # Thread-safe response tracking: {sender_id: {response_hash: timestamp}}
    _response_tracker = {}
    _lock = threading.Lock()
    
    def __init__(self, dispatcher: CollectingDispatcher, sender_id: str, message: str):
        self.dispatcher = dispatcher
        self.sender_id = sender_id
        self.message = message
        self.sent_messages = []  # Track messages sent in this action execution
        self.response_count = 0
        self.max_responses = 1  # Only allow ONE response per action execution
        
    def utter_message(self, text: str, **kwargs):
        """Send message only if not duplicate and within limit"""
        if not text or not text.strip():
            return
        
        # Create hash of the response
        response_hash = hashlib.md5(f"{self.sender_id}_{text}".encode()).hexdigest()
        current_time = time.time()
        
        with SafeDispatcher._lock:
            # Check if this exact response was sent recently (within 10 seconds)
            if self.sender_id in SafeDispatcher._response_tracker:
                if response_hash in SafeDispatcher._response_tracker[self.sender_id]:
                    last_time = SafeDispatcher._response_tracker[self.sender_id][response_hash]
                    if current_time - last_time < 10:  # 10 second window
                        logging.warning(f"Duplicate response prevented: '{text[:50]}...' for sender {self.sender_id}")
                        return
            
            # Check if we've already sent max responses in this execution
            if self.response_count >= self.max_responses:
                logging.warning(f"Max responses ({self.max_responses}) reached for sender {self.sender_id}, preventing: '{text[:50]}...'")
                return
            
            # Track this response
            if self.sender_id not in SafeDispatcher._response_tracker:
                SafeDispatcher._response_tracker[self.sender_id] = {}
            SafeDispatcher._response_tracker[self.sender_id][response_hash] = current_time
            
            # Clean up old entries (older than 60 seconds)
            for sid in list(SafeDispatcher._response_tracker.keys()):
                for rhash in list(SafeDispatcher._response_tracker[sid].keys()):
                    if current_time - SafeDispatcher._response_tracker[sid][rhash] > 60:
                        del SafeDispatcher._response_tracker[sid][rhash]
                if not SafeDispatcher._response_tracker[sid]:
                    del SafeDispatcher._response_tracker[sid]
        
        # Send the message
        try:
            # Increment response count BEFORE sending to prevent race conditions
            with SafeDispatcher._lock:
                self.response_count += 1
            
            self.dispatcher.utter_message(text=text, **kwargs)
            self.sent_messages.append(text)
            logging.info(f"SafeDispatcher: Sent response #{self.response_count} for sender {self.sender_id}: '{text[:50]}...'")
        except Exception as e:
            logging.error(f"Error sending message via SafeDispatcher: {e}")
            # Rollback response count on error
            with SafeDispatcher._lock:
                self.response_count -= 1
    
    def __getattr__(self, name):
        """Delegate all other attributes to the original dispatcher"""
        return getattr(self.dispatcher, name)

# Database configuration with fallback to known hospital database
DB_CONFIG = {
    'host': os.getenv('AURORA_ENDPOINT') or os.getenv('DB_HOST') or 'hospital.cv8wum284gev.us-east-1.rds.amazonaws.com',
    'database': os.getenv('DB_NAME', 'hospital'),  # Changed default from 'postgres' to 'hospital'
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD') or 'qMI8DUYcGnoTBpsyagh9',
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Legacy RDS configuration (points to same hospital database)
RDS_CONFIG = {
    'host': os.getenv('RDS_HOST') or 'hospital.cv8wum284gev.us-east-1.rds.amazonaws.com',
    'database': 'hospital',  # Changed from 'pran_chatbot' to 'hospital'
    'user': os.getenv('RDS_USER', 'postgres'),
    'password': os.getenv('RDS_PASSWORD') or os.getenv('DB_PASSWORD') or 'qMI8DUYcGnoTBpsyagh9',
    'port': 5432
}

# Create connection pool
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        **DB_CONFIG
    )
except Exception as e:
    logging.warning(f"Could not create database pool, will use direct connections: {e}")
    db_pool = None

class DatabaseHelper:
    """Helper class for database operations with intelligent conversation support"""
    
    @staticmethod
    def get_connection():
        """Get database connection from pool or create new with timeout"""
        try:
            if db_pool:
                conn = db_pool.getconn()
                # Set connection timeout
                conn.set_session(autocommit=False)
                return conn
            else:
                # Add connect_timeout to prevent hanging
                config = DB_CONFIG.copy()
                config['connect_timeout'] = 5
                return psycopg2.connect(**config)
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            try:
                # Fallback to RDS with timeout
                rds_config = RDS_CONFIG.copy()
                rds_config['connect_timeout'] = 5
                return psycopg2.connect(**rds_config)
            except Exception as e2:
                logging.error(f"RDS connection error: {e2}")
                return None
    
    @staticmethod
    def return_connection(conn):
        """Return connection to pool"""
        try:
            if db_pool and conn:
                db_pool.putconn(conn)
            elif conn:
                conn.close()
        except Exception as e:
            logging.error(f"Error returning connection: {e}")
    
    @staticmethod
    def get_insurance_plans():
        """Get insurance plans from database with timeout"""
        conn = DatabaseHelper.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            # Set statement timeout to prevent hanging
            cursor.execute("SET statement_timeout = '3s'")
            # Try to get from database, fallback to default if table doesn't exist
            try:
                cursor.execute("""
                    SELECT plan_id, plan_name, monthly_premium, deductible, coverage_percentage, features
                    FROM insurance_plans
                    WHERE is_active = true
                    ORDER BY monthly_premium
                    LIMIT 10
                """)
                plans = cursor.fetchall()
                if plans:
                    result = []
                    for p in plans:
                        features = p[5] if len(p) > 5 and p[5] else []
                        if isinstance(features, str):
                            # Handle PostgreSQL array format
                            features = features.strip('{}').split(',') if features else []
                        elif not isinstance(features, list):
                            features = []
                        
                        result.append({
                            'plan_id': p[0],
                            'name': p[1],
                            'monthly_premium': f"${float(p[2]):.2f}" if p[2] else "$0",
                            'deductible': f"${float(p[3]):.2f}" if p[3] else "$0",
                            'coverage': f"{int(p[4])}%" if p[4] else "0%",
                            'features': features
                        })
                    logging.info(f"Retrieved {len(result)} insurance plans from database")
                    return result
            except Exception as e:
                # Table doesn't exist or query failed, return None to use fallback
                logging.debug(f"Insurance plans query failed (using fallback): {e}")
                pass
            cursor.close()
            return None
        except Exception as e:
            logging.error(f"Error fetching insurance plans: {e}")
            return None
        finally:
            DatabaseHelper.return_connection(conn)
    
    @staticmethod
    def get_patient_info(patient_id=None, user_id=None):
        """Get patient information from database"""
        conn = DatabaseHelper.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            if patient_id:
                cursor.execute("""
                    SELECT patient_id, name, email, phone, date_of_birth, address, medical_history
                    FROM medical_patients
                    WHERE patient_id = %s
                """, (patient_id,))
            elif user_id:
                cursor.execute("""
                    SELECT patient_id, name, email, phone, date_of_birth, address, medical_history
                    FROM medical_patients
                    WHERE user_id = %s OR email = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id, user_id))
            else:
                return None
            
            patient = cursor.fetchone()
            if patient:
                return {
                    'patient_id': patient[0],
                    'name': patient[1],
                    'email': patient[2],
                    'phone': patient[3],
                    'date_of_birth': patient[4],
                    'address': patient[5],
                    'medical_history': json.loads(patient[6]) if patient[6] else {}
                }
            cursor.close()
            return None
        except Exception as e:
            logging.error(f"Error fetching patient info: {e}")
            return None
        finally:
            DatabaseHelper.return_connection(conn)
    
    @staticmethod
    def get_appointments(patient_id=None, user_id=None, upcoming=True):
        """Get appointments from database"""
        conn = DatabaseHelper.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            if patient_id:
                query = """
                    SELECT appointment_id, doctor_name, department, appointment_date, 
                           appointment_time, status, symptoms
                    FROM medical_appointments
                    WHERE patient_id = %s
                """
                params = (patient_id,)
            elif user_id:
                # First get patient_id from user_id
                patient = DatabaseHelper.get_patient_info(user_id=user_id)
                if not patient:
                    return None
                query = """
                    SELECT appointment_id, doctor_name, department, appointment_date, 
                           appointment_time, status, symptoms
                    FROM medical_appointments
                    WHERE patient_id = %s
                """
                params = (patient['patient_id'],)
            else:
                return None
            
            if upcoming:
                query += " AND appointment_date >= CURRENT_DATE AND status != 'cancelled'"
            query += " ORDER BY appointment_date, appointment_time"
            
            cursor.execute(query, params)
            appointments = cursor.fetchall()
            
            if appointments:
                return [{
                    'appointment_id': a[0],
                    'doctor_name': a[1],
                    'department': a[2],
                    'date': a[3].strftime('%Y-%m-%d') if a[3] else None,
                    'time': a[4].strftime('%H:%M') if a[4] else None,
                    'status': a[5],
                    'symptoms': a[6]
                } for a in appointments]
            cursor.close()
            return []
        except Exception as e:
            logging.error(f"Error fetching appointments: {e}")
            return None
        finally:
            DatabaseHelper.return_connection(conn)
    
    @staticmethod
    def get_availability_slots(doctor_id=None, date=None, specialty=None):
        """Get available appointment slots from database"""
        conn = DatabaseHelper.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout = '3s'")
            
            query = """
                SELECT s.slot_id, s.doctor_id, d.name as doctor_name, d.doc_type as specialty, d.department,
                       s.date, s.start_time, s.end_time, s.available
                FROM availability_slots s
                LEFT JOIN doctors d ON s.doctor_id = d.doctor_id
                WHERE s.available = true
            """
            params = []
            
            if doctor_id:
                query += " AND s.doctor_id = %s"
                params.append(doctor_id)
            
            if date:
                query += " AND s.date = %s"
                params.append(date)
            else:
                # Default to next 7 days
                query += " AND s.date >= CURRENT_DATE AND s.date <= CURRENT_DATE + INTERVAL '7 days'"
            
            if specialty:
                query += " AND (d.doc_type ILIKE %s OR d.specialty ILIKE %s OR d.department ILIKE %s)"
                specialty_term = f"%{specialty}%"
                params.extend([specialty_term, specialty_term, specialty_term])
            
            query += " ORDER BY s.date, s.start_time LIMIT 20"
            
            cursor.execute(query, params if params else None)
            slots = cursor.fetchall()
            
            if slots:
                result = []
                for slot in slots:
                    result.append({
                        'slot_id': slot[0],
                        'doctor_id': slot[1],
                        'doctor_name': slot[2] or 'Unknown',
                        'specialty': slot[3] or 'General',
                        'department': slot[4] or 'General',
                        'date': slot[5].isoformat() if isinstance(slot[5], datetime) else str(slot[5]),
                        'start_time': str(slot[6]) if slot[6] else None,
                        'end_time': str(slot[7]) if slot[7] else None,
                        'available': slot[8]
                    })
                logging.info(f"Retrieved {len(result)} available slots from database")
                return result
            
            cursor.close()
            return []
        except Exception as e:
            logging.debug(f"Error fetching availability slots: {e}")
            return None
        finally:
            DatabaseHelper.return_connection(conn)
    
    @staticmethod
    def get_doctors(specialty=None, department=None, limit=10):
        """Get doctors from database with timeout and fallback to sample data"""
        conn = DatabaseHelper.get_connection()
        if not conn:
            logging.warning("Database connection not available, using sample data")
            return DatabaseHelper._get_sample_doctors(specialty)
        
        try:
            cursor = conn.cursor()
            # Set timeout
            cursor.execute("SET statement_timeout = '3s'")
            
            # Try multiple table names (medical_doctors, doctors, physicians)
            table_found = False
            doctors = None
            
            for table_name in ['medical_doctors', 'doctors', 'physicians']:
                try:
                    # First, detect available columns
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}'
                    """)
                    available_columns = [row[0] for row in cursor.fetchall()]
                    
                    if not available_columns:
                        continue
                    
                    logging.info(f"Table {table_name} columns: {available_columns}")
                    
                    # Build SELECT clause based on available columns
                    select_cols = []
                    col_mapping = {}
                    
                    # doctor_id
                    if 'doctor_id' in available_columns:
                        select_cols.append('doctor_id')
                    elif 'id' in available_columns:
                        select_cols.append('id as doctor_id')
                    else:
                        select_cols.append('NULL as doctor_id')
                    
                    # name
                    if 'name' in available_columns:
                        select_cols.append('name')
                    elif 'doctor_name' in available_columns:
                        select_cols.append('doctor_name as name')
                    else:
                        select_cols.append("'Unknown' as name")
                    
                    # specialty (map from doc_type if needed)
                    if 'specialty' in available_columns:
                        select_cols.append('specialty')
                    elif 'doc_type' in available_columns:
                        select_cols.append('doc_type as specialty')
                        col_mapping['specialty_col'] = 'doc_type'
                    elif 'specialization' in available_columns:
                        select_cols.append('specialization as specialty')
                    else:
                        select_cols.append("'General Medicine' as specialty")
                    
                    # department
                    if 'department' in available_columns:
                        select_cols.append('department')
                    elif 'doc_type' in available_columns:
                        select_cols.append('doc_type as department')
                    else:
                        select_cols.append("'General Medicine' as department")
                    
                    # email
                    if 'email' in available_columns:
                        select_cols.append('email')
                    else:
                        select_cols.append("'info@hospital.com' as email")
                    
                    # phone
                    if 'phone' in available_columns:
                        select_cols.append('phone')
                    elif 'phone_number' in available_columns:
                        select_cols.append('phone_number as phone')
                    elif 'contact' in available_columns:
                        select_cols.append('contact as phone')
                    else:
                        select_cols.append("'(555) 123-4567' as phone")
                    
                    # experience_years
                    if 'experience_years' in available_columns:
                        select_cols.append('experience_years')
                    elif 'experience' in available_columns:
                        select_cols.append('experience as experience_years')
                    else:
                        select_cols.append('NULL as experience_years')
                    
                    # rating
                    if 'rating' in available_columns:
                        select_cols.append('rating')
                    else:
                        select_cols.append('NULL as rating')
                    
                    query = f"SELECT {', '.join(select_cols)} FROM {table_name}"
                    where_conditions = []
                    params = []
                    
                    # Check if is_active column exists
                    if 'is_active' in available_columns:
                        where_conditions.append("is_active = true")
                    
                    if specialty:
                        # Use actual column name for specialty filtering
                        specialty_col = col_mapping.get('specialty_col', 'specialty')
                        if specialty_col in available_columns:
                            # Handle general medicine with multiple search terms
                            if specialty.lower() == "general medicine":
                                where_conditions.append(f"({specialty_col} ILIKE %s OR {specialty_col} ILIKE %s OR {specialty_col} ILIKE %s OR {specialty_col} ILIKE %s)")
                                params.extend(["%general%", "%family%", "%primary%", "%gp%"])
                            else:
                                where_conditions.append(f"{specialty_col} ILIKE %s")
                                params.append(f"%{specialty}%")
                    
                    if department and 'department' in available_columns:
                        where_conditions.append("department ILIKE %s")
                        params.append(f"%{department}%")
                    
                    if where_conditions:
                        query += " WHERE " + " AND ".join(where_conditions)
                    
                    # Add ORDER BY if name column exists
                    if 'name' in available_columns or 'doctor_name' in available_columns:
                        query += f" ORDER BY name LIMIT {limit}"
                    else:
                        query += f" LIMIT {limit}"
                    
                    logging.info(f"Executing query: {query} with params: {params}")
                    cursor.execute(query, params if params else None)
                    doctors = cursor.fetchall()
                    table_found = True
                    logging.info(f"Successfully queried {table_name} table, found {len(doctors) if doctors else 0} doctors")
                    break
                except Exception as table_error:
                    logging.error(f"Table {table_name} query failed: {table_error}")
                    import traceback
                    logging.error(traceback.format_exc())
                    continue
            
            if not table_found:
                logging.warning("No doctor tables found in database, using sample data")
                cursor.close()
                return DatabaseHelper._get_sample_doctors(specialty)
            
            if doctors and len(doctors) > 0:
                result = [{
                    'doctor_id': d[0],
                    'name': d[1],
                    'specialty': d[2],
                    'department': d[3],
                    'email': d[4],
                    'phone': d[5],
                    'experience_years': d[6] if len(d) > 6 else None,
                    'rating': d[7] if len(d) > 7 else None
                } for d in doctors]
                cursor.close()
                logging.info(f"Returning {len(result)} doctors from database")
                return result
            else:
                logging.warning(f"No doctors found in database for specialty: {specialty}, using sample data")
                cursor.close()
                return DatabaseHelper._get_sample_doctors(specialty)
        except Exception as e:
            logging.error(f"Error fetching doctors: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return DatabaseHelper._get_sample_doctors(specialty)
        finally:
            DatabaseHelper.return_connection(conn)
    
    @staticmethod
    def _get_sample_doctors(specialty=None):
        """Return sample doctors data when database is empty or unavailable"""
        sample_doctors = [
            {
                'doctor_id': 'DR001',
                'name': 'Sarah Johnson',
                'specialty': 'General Medicine',
                'department': 'General Medicine',
                'email': 'sarah.johnson@hospital.com',
                'phone': '(555) 123-4567',
                'experience_years': 15,
                'rating': 4.8
            },
            {
                'doctor_id': 'DR002',
                'name': 'Emily Williams',
                'specialty': 'Gynecology',
                'department': 'Women\'s Health',
                'email': 'emily.williams@hospital.com',
                'phone': '(555) 123-4568',
                'experience_years': 12,
                'rating': 4.9
            },
            {
                'doctor_id': 'DR003',
                'name': 'Michael Chen',
                'specialty': 'Cardiology',
                'department': 'Cardiology',
                'email': 'michael.chen@hospital.com',
                'phone': '(555) 123-4569',
                'experience_years': 20,
                'rating': 4.7
            },
            {
                'doctor_id': 'DR004',
                'name': 'Lisa Anderson',
                'specialty': 'Pediatrics',
                'department': 'Pediatrics',
                'email': 'lisa.anderson@hospital.com',
                'phone': '(555) 123-4570',
                'experience_years': 10,
                'rating': 4.9
            },
            {
                'doctor_id': 'DR005',
                'name': 'David Martinez',
                'specialty': 'Neurology',
                'department': 'Neurology',
                'email': 'david.martinez@hospital.com',
                'phone': '(555) 123-4571',
                'experience_years': 18,
                'rating': 4.6
            },
            {
                'doctor_id': 'DR006',
                'name': 'Jessica Taylor',
                'specialty': 'Dermatology',
                'department': 'Dermatology',
                'email': 'jessica.taylor@hospital.com',
                'phone': '(555) 123-4572',
                'experience_years': 8,
                'rating': 4.8
            },
            {
                'doctor_id': 'DR007',
                'name': 'Robert Brown',
                'specialty': 'Orthopedics',
                'department': 'Orthopedics',
                'email': 'robert.brown@hospital.com',
                'phone': '(555) 123-4573',
                'experience_years': 22,
                'rating': 4.7
            },
            {
                'doctor_id': 'DR008',
                'name': 'Amanda Garcia',
                'specialty': 'Psychiatry',
                'department': 'Mental Health',
                'email': 'amanda.garcia@hospital.com',
                'phone': '(555) 123-4574',
                'experience_years': 14,
                'rating': 4.9
            }
        ]
        
        if specialty:
            # Filter by specialty
            filtered = [d for d in sample_doctors if specialty.lower() in d['specialty'].lower() or specialty.lower() in d['department'].lower()]
            if filtered:
                logging.info(f"Returning {len(filtered)} sample doctors for specialty: {specialty}")
                return filtered
        
        logging.info(f"Returning {len(sample_doctors)} sample doctors (all specialties)")
        return sample_doctors
    
    @staticmethod
    def save_conversation_history(sender_id, user_message, bot_response, intent=None, entities=None):
        """Save conversation history to database for context (non-blocking)"""
        # Don't block on saving history - do it asynchronously if possible
        try:
            conn = DatabaseHelper.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            # Set timeout
            cursor.execute("SET statement_timeout = '2s'")
            # Create table if it doesn't exist
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id SERIAL PRIMARY KEY,
                        sender_id VARCHAR(255),
                        user_message TEXT,
                        bot_response TEXT,
                        intent VARCHAR(100),
                        entities TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
            except Exception:
                pass  # Table might already exist
            
            cursor.execute("""
                INSERT INTO conversation_history (sender_id, user_message, bot_response, intent, entities)
                VALUES (%s, %s, %s, %s, %s)
            """, (sender_id, user_message, bot_response, intent, json.dumps(entities) if entities else None))
            
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            # Don't fail the request if history save fails
            logging.debug(f"Error saving conversation history (non-critical): {e}")
            return False
        finally:
            DatabaseHelper.return_connection(conn)
    
    @staticmethod
    def get_conversation_history(sender_id, limit=5):
        """Get recent conversation history for context with timeout"""
        conn = DatabaseHelper.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            # Set timeout to prevent hanging
            cursor.execute("SET statement_timeout = '2s'")
            cursor.execute("""
                SELECT user_message, bot_response, intent, entities, created_at
                FROM conversation_history
                WHERE sender_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (sender_id, limit))
            
            history = cursor.fetchall()
            cursor.close()
            
            # Return in reverse order (oldest first) for context
            return [{
                'user': h[0],
                'bot': h[1],
                'intent': h[2],
                'entities': json.loads(h[3]) if h[3] else None,
                'timestamp': h[4]
            } for h in reversed(history)]
        except Exception as e:
            # Don't fail if history fetch fails - just return empty
            logging.debug(f"Error fetching conversation history (non-critical): {e}")
            return []
        finally:
            DatabaseHelper.return_connection(conn)


class IntelligentFallback:
    """Fallback responses when Bedrock is not available"""
    
    @staticmethod
    def get_fallback_response(user_message: str, conversation_context: List[Dict] = None, retrieved_context: Dict = None) -> str:
        """Provide intelligent fallback responses for ANY query type with context"""
        msg_lower = user_message.lower()
        
            # Check conversation context for follow-up questions
        is_followup = False
        previous_topic = None
        if conversation_context:
            for msg in reversed(conversation_context[-5:]):  # Check last 5 messages for better context
                if msg.get("role") == "assistant":
                    prev_text = msg.get("content", "").lower()
                    if "appointment" in prev_text or "schedule" in prev_text or "book" in prev_text:
                        previous_topic = "appointment"
                    elif "insurance" in prev_text or "plan" in prev_text or "coverage" in prev_text:
                        previous_topic = "insurance"
                    elif "doctor" in prev_text or "specialist" in prev_text or "physician" in prev_text:
                        previous_topic = "doctor"
                    elif "symptom" in prev_text or "health" in prev_text or "medical" in prev_text:
                        previous_topic = "health"
                    elif "medication" in prev_text or "medicine" in prev_text or "drug" in prev_text:
                        previous_topic = "medication"
                    elif "lab" in prev_text or "test" in prev_text or "result" in prev_text:
                        previous_topic = "lab"
                    elif "bill" in prev_text or "payment" in prev_text or "cost" in prev_text:
                        previous_topic = "billing"
                    elif "wellness" in prev_text or "diet" in prev_text or "exercise" in prev_text:
                        previous_topic = "wellness"
                    break
        
        # Health/Symptom related
        if any(word in msg_lower for word in ["cold", "cough", "fever", "headache", "pain", "sick", "symptom"]):
            if "cold" in msg_lower or "cough" in msg_lower:
                return "I understand you're experiencing cold and cough symptoms. For immediate relief, rest, stay hydrated, and consider over-the-counter cold medications. Gargle with warm salt water for cough relief. If symptoms persist for more than 10 days, you have a high fever (over 101°F), difficulty breathing, or severe headache, please see a doctor. I can help you book an appointment with a doctor or find an ENT specialist. Would you like me to help you find a doctor or book an appointment?"
            
            elif "headache" in msg_lower:
                return "I understand you're experiencing a headache. Common causes include tension headaches, migraines, sinus issues, dehydration, or stress. If you have a sudden severe headache (worst of your life), headache with fever/stiff neck/confusion, headache after head injury, or vision changes, seek immediate care. I can help you book an appointment with a neurologist or general physician. Would you like me to find a doctor or schedule a consultation?"
            
            elif "fever" in msg_lower:
                return "I understand you have a fever. Normal body temperature is 98.6°F (37°C), fever is 100.4°F (38°C) or higher, and high fever is 103°F (39.4°C) or higher. Please see a doctor if your fever is over 103°F, lasts more than 3 days, or is accompanied by severe symptoms like rash, difficulty breathing, or confusion. For infants under 3 months, any fever requires immediate medical attention. I can help you book an appointment with a doctor or find available urgent care. Would you like me to help you schedule a consultation?"
            
            else:
                return "I understand you have health concerns. I can help you effectively! I can assist with booking appointments, finding the right specialist based on your symptoms, medication questions, locating nearby healthcare facilities, and symptom assessment. For your symptoms, I recommend describing them in detail, then I can help you find the right doctor and book an appointment for proper evaluation. Would you like me to help you find a doctor or book an appointment?"
        
        # Insurance related
        elif any(word in msg_lower for word in ["insurance", "coverage", "plan", "benefit"]):
            # Check if specifically asking for plans
            if any(word in msg_lower for word in ["plan", "plans", "available", "show", "list", "what", "options"]):
                return """Available Insurance Plans:

1. Basic Health Plan
   Monthly Premium: $150
   Deductible: $1000
   Coverage: 80%
   Features: Primary care, Emergency visits, Basic prescriptions

2. Premium Health Plan
   Monthly Premium: $300
   Deductible: $500
   Coverage: 90%
   Features: All basic features, Specialist visits, Mental health, Dental & Vision

3. Family Health Plan
   Monthly Premium: $450
   Deductible: $750
   Coverage: 85%
   Features: All premium features, Family coverage, Maternity care, Pediatric care

Would you like more details about any specific plan, or would you like personalized insurance recommendations based on your needs?"""
            elif previous_topic == "insurance" or any(word in msg_lower for word in ["yes", "sure", "ok", "please", "help"]):
                return "Great! I can verify your insurance coverage, show available insurance plans, provide personalized recommendations, check benefits and coverage details, and help you understand costs and copays. To get started, tell me your insurance provider name, ask about specific coverage questions, or request insurance plan comparisons. What would you like to know about insurance?"
            return "I can help you with insurance! I can verify your coverage, show available plans, provide personalized recommendations, check benefits, and explain costs and copays. To get started, tell me your insurance provider name or ask about specific coverage. What would you like to know about insurance?"
        
        # Doctor finding related - ALWAYS show doctors
        elif any(word in msg_lower for word in ["find", "doctor", "gynecologist", "gynacologist", "gynec", "gynaec", "obstetric", "specialist", "cardiologist", "neurologist", "dermatologist", "pediatrician", "is there any", "available doctor", "any doctor"]):
            # Try to get doctors from database or sample data
            specialty = None
            specialty_name = "doctor"
            
            if "gynecologist" in msg_lower or "gynacologist" in msg_lower or "gynec" in msg_lower or "gynaec" in msg_lower or "obstetric" in msg_lower:
                specialty = "gynecology"
                specialty_name = "gynecologist"
            elif "cardiologist" in msg_lower:
                specialty = "cardiology"
                specialty_name = "cardiologist"
            elif "neurologist" in msg_lower:
                specialty = "neurology"
                specialty_name = "neurologist"
            elif "dermatologist" in msg_lower:
                specialty = "dermatology"
                specialty_name = "dermatologist"
            elif "pediatrician" in msg_lower or "pediatric" in msg_lower:
                specialty = "pediatrics"
                specialty_name = "pediatrician"
            
            # Get doctors from database or sample
            try:
                from .actions import DatabaseHelper
                doctors = DatabaseHelper.get_doctors(specialty=specialty)
                if not doctors or len(doctors) == 0:
                    doctors = DatabaseHelper._get_sample_doctors(specialty)
            except:
                doctors = DatabaseHelper._get_sample_doctors(specialty) if 'DatabaseHelper' in dir() else []
            
            if doctors and len(doctors) > 0:
                response = f"✅ **I found {len(doctors)} {specialty_name}{'s' if len(doctors) > 1 else ''}:**\n\n"
                for i, doc in enumerate(doctors[:5], 1):
                    response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                    response += f"   📋 Specialty: {doc.get('specialty', doc.get('doc_type', specialty_name))}\n"
                    response += f"   🏥 Department: {doc.get('department', 'General Medicine')}\n"
                    if doc.get('phone'):
                        response += f"   📞 Phone: {doc.get('phone')}\n"
                    if doc.get('email'):
                        response += f"   ✉️ Email: {doc.get('email')}\n"
                    if doc.get('experience_years') or doc.get('experience'):
                        exp = doc.get('experience_years') or doc.get('experience')
                        response += f"   👨‍⚕️ Experience: {exp} years\n"
                    if doc.get('rating'):
                        response += f"   ⭐ Rating: {doc.get('rating')}/5\n"
                    response += "\n"
                response += "📅 **Would you like to book an appointment with any of these doctors?**\n"
                response += "Just tell me the doctor's name or number!"
                return response
            else:
                # Final fallback with sample doctors
                return f"✅ **I found these {specialty_name}s for you:**\n\n1. Dr. Emily Williams - Gynecology - (555) 201-0002\n2. Dr. Priya Reddy - Gynecology - (555) 201-0001\n3. Dr. Kavita Nair - Gynecology - (555) 201-0003\n\nWould you like to book an appointment with any of these doctors?"
        
        # Appointment related
        elif any(word in msg_lower for word in ["appointment", "book", "schedule", "visit"]):
            if previous_topic == "appointment" or any(word in msg_lower for word in ["yes", "sure", "ok", "please", "help"]):
                return "Perfect! To book an appointment, tell me your symptoms or preferred specialty, and I'll find the right doctor for you, show available time slots, and help you complete the booking. I can also help you reschedule or cancel existing appointments, and set up appointment reminders. What symptoms do you have or which specialty are you looking for?"
            return "I can help you book an appointment! I can schedule new appointments, find doctors by specialty or symptoms, check available time slots, reschedule or cancel appointments, and set up reminders. To get started, tell me your symptoms or preferred specialty, and I'll find the right doctor and show available times. Would you like to book an appointment now?"
        
        # Medication related
        elif any(word in msg_lower for word in ["medication", "medicine", "drug", "prescription", "pill", "tablet", "dose", "dosage", "side effect", "interaction"]):
            return "I can help with medication questions! I can check drug interactions, calculate proper dosages, create medication schedules, identify potential side effects, and help with medication management. Important: Always consult your doctor before changing medications, never stop medications without medical advice, and keep a list of all medications you're taking. What medication question can I help with?"
        
        # Lab results and medical records
        elif any(word in msg_lower for word in ["lab", "test", "result", "report", "blood test", "x-ray", "scan", "medical record", "report", "diagnosis"]):
            return "I can help you access and understand your lab results, medical reports, test results, and medical records! I can explain what your test results mean, help you understand your diagnosis, access your medical history, and guide you on next steps. Would you like me to help you access your lab results or medical records?"
        
        # Billing and payment
        elif any(word in msg_lower for word in ["bill", "billing", "payment", "cost", "price", "charge", "invoice", "statement", "pay", "fee"]):
            return "I can help with billing and payment questions! I can show you billing statements, explain charges, help with payment plans, verify insurance coverage for procedures, provide cost estimates, and assist with payment processing. What billing question can I help with?"
        
        # Emergency and urgent care
        elif any(word in msg_lower for word in ["emergency", "urgent", "immediate", "critical", "severe", "acute", "911", "ambulance"]):
            return "For medical emergencies, please call 911 or go to your nearest emergency room immediately. For urgent but non-emergency situations, I can help you find urgent care centers, assess the urgency of your symptoms, and guide you on when to seek immediate care. If this is a life-threatening emergency, please call 911 now. Otherwise, tell me about your symptoms and I'll help you determine the best course of action."
        
        # Mental health
        elif any(word in msg_lower for word in ["mental", "depression", "anxiety", "stress", "therapy", "counselor", "psychologist", "psychiatrist", "mental health", "emotional"]):
            return "I can help with mental health support! I can provide mental health assessments (GAD-7 for anxiety, PHQ-9 for depression), help you find mental health professionals, provide resources for stress management, and guide you to appropriate care. For mental health crises, please contact a crisis hotline or seek immediate professional help. How can I assist you with mental health support?"
        
        # Wellness and lifestyle
        elif any(word in msg_lower for word in ["wellness", "diet", "exercise", "fitness", "nutrition", "sleep", "weight", "lifestyle", "healthy", "wellbeing"]):
            return "I can help with wellness and lifestyle! I can provide personalized diet recommendations, exercise plans, sleep hygiene tips, weight management guidance, nutrition advice, and overall wellness strategies. I can also help you set health goals and track your progress. What aspect of wellness would you like help with?"
        
        # Hospital and location services
        elif any(word in msg_lower for word in ["hospital", "location", "clinic", "address", "where", "nearby", "near me", "facility"]):
            return "I can help you find hospitals, clinics, and healthcare facilities! I can show you locations, addresses, contact information, hours of operation, and services available at each location. I can also help you find the nearest facility based on your location. What type of facility are you looking for?"
        
        # Patient services and support
        elif any(word in msg_lower for word in ["patient", "service", "support", "help desk", "customer service", "assistance"]):
            return "I'm here to help with all patient services! I can assist with registration, medical records access, appointment scheduling, insurance verification, billing questions, medication management, and general healthcare guidance. What patient service can I help you with today?"
        
        # General greeting or help
        elif any(word in msg_lower for word in ["hi", "hello", "hey", "greetings", "help", "services", "what can you", "capabilities", "what do you do"]):
            return "Hello! I'm Dr. AI, your super intelligent healthcare assistant. I'm here to help with ALL your healthcare needs! I can assist with:\n\n• Medical Services: Symptom assessment, emergency evaluation, mental health screening\n• Appointments: Book, reschedule, find doctors by specialty\n• Insurance: Verify coverage, compare plans, explain benefits\n• Medications: Check interactions, dosages, schedules\n• Lab Results: Access and understand test results\n• Billing: View statements, payment plans, cost estimates\n• Wellness: Diet, exercise, sleep, lifestyle guidance\n• Patient Services: Records, registration, support\n• And much more!\n\nHow can I help you today? You can ask me anything about healthcare!"
        
        # Default helpful response - intelligent for ANY query
        else:
            # Check if we have context to enhance the response
            enhanced_info = ""
            if retrieved_context:
                if retrieved_context.get('doctors'):
                    enhanced_info += f" I found {len(retrieved_context['doctors'])} doctor(s) that might help."
                if retrieved_context.get('insurance_plans'):
                    enhanced_info += f" I have {len(retrieved_context['insurance_plans'])} insurance plan(s) available."
                if retrieved_context.get('appointments'):
                    enhanced_info += f" You have {len(retrieved_context['appointments'])} appointment(s)."
            
            return f"I'm here to help with all your healthcare needs! I can assist with booking appointments, insurance information and verification, finding doctors and specialists, medication questions, symptom assessment, patient services, wellness tips, and answer any healthcare-related questions.{enhanced_info} Try asking 'How do I book an appointment?', 'What services do you offer?', 'I need help with [your concern]', 'What insurance plans are available?', or ask me anything about healthcare. What can I help you with today?"


class AWSBedrockHelper:
    """A helper class for interacting with AWS Bedrock LLM service."""
    
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        # Use inference profile for on-demand access
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        # Try alternative model IDs if the default doesn't work
        self.fallback_models = [
            'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'anthropic.claude-3-5-sonnet-20240620-v1:0',
            'anthropic.claude-3-sonnet-20240229-v1:0'
        ]
    
    def get_response(self, prompt: Text, conversation_history: List[Dict] = None) -> Text:
        """Sends a prompt to AWS Bedrock and returns the response."""
        try:
            # Enhanced system prompt for RAG-powered intelligent healthcare assistant
            system_prompt = """You are Dr. AI, a super intelligent RAG-powered healthcare assistant. You use Retrieval-Augmented Generation (RAG) to provide accurate, context-aware responses.

RAG SYSTEM:
- You receive RETRIEVED CONTEXT from the database containing real-time information
- Use this context to provide accurate, specific answers
- Reference specific doctors, insurance plans, appointments, medications, and lab results from the context
- If context is provided, prioritize it over general knowledge
- Always cite specific information from the retrieved context when available

You have access to a complete healthcare platform with multiple services and APIs.

YOUR COMPLETE CAPABILITIES & SERVICES:

 MEDICAL SERVICES:
- Symptom Assessment: Analyze symptoms, provide guidance, recommend appropriate care
- Emergency Assessment: Evaluate emergency situations, calculate HEART scores, assess urgency
- Mental Health: GAD-7 and PHQ-9 assessments, crisis detection, counselor recommendations
- Medication Management: Drug interaction checking, dosage calculations, medication schedules
- Health Education: Provide information about conditions, treatments, and wellness

PATIENT MANAGEMENT:
- Patient Registration: Help register new patients with medical history and insurance
- Medical Records: Access and share medical records (HIPAA compliant)
- Patient History: View complete patient medical history
- Profile Management: Update patient profiles and information

APPOINTMENTS & SCHEDULING:
- Book Appointments: Schedule appointments with doctors
- Find Doctors: Match symptoms to appropriate medical specializations
- Reschedule/Cancel: Help manage existing appointments
- Appointment Reminders: Set up WhatsApp reminders
- Doctor Availability: Check doctor schedules and availability

INSURANCE & BILLING:
- Insurance Verification: Verify insurance coverage and benefits
- Insurance Plans: Show available insurance plans
- Insurance Suggestions: Recommend insurance based on needs
- Pre-authorization: Help with pre-authorization requests
- Cost Estimates: Provide service cost estimates
- Payment Plans: Explain payment plan options
- Billing Information: Access billing details and statements

WELLNESS & SUPPORT:
- Diet Recommendations: Personalized diet plans
- Exercise Plans: Fitness and exercise recommendations
- Sleep Hygiene: Sleep quality tips and advice
- Clinical Guidelines: Evidence-based clinical recommendations

 ANALYTICS & ADMINISTRATION:
- Disease Trends: Analyze health trends and patterns
- Feedback Collection: Gather patient feedback
- Health Predictions: Predictive health analytics
- Health Recommendations: Personalized health advice

 HOSPITAL SERVICES:
- Hospital Locations: Find nearby hospitals and clinics
- Hospital Policies: Explain hospital policies and procedures
- Country Services: Location-specific healthcare services

YOUR INTELLIGENCE GUIDELINES:
- Answer ANY question about ANY of these services intelligently and comprehensively
- Understand context from previous messages and maintain conversation flow
- When asked about appointments, provide detailed scheduling guidance, show available doctors, and help book
- When asked about insurance, explain coverage, plans, benefits, costs, and provide recommendations
- When asked about health/symptoms, provide medical guidance, recommend appropriate doctors, and suggest next steps
- When asked about medications, explain interactions, dosages, safety, and provide medication management help
- When asked about lab results, help interpret results, explain what they mean, and guide on next steps
- When asked about billing, explain charges, show statements, help with payment plans, and verify coverage
- When asked about emergencies, assess urgency, provide immediate guidance, and direct to appropriate care
- When asked about mental health, provide support, assessments, and help find mental health professionals
- When asked about wellness, provide personalized diet, exercise, sleep, and lifestyle recommendations
- When asked about locations, help find hospitals, clinics, and healthcare facilities nearby
- When asked about patient services, help with registration, records, support, and general assistance
- Always be empathetic, clear, helpful, and comprehensive
- Ask clarifying questions when needed to provide the best assistance
- Guide users to the right service or API when appropriate
- Provide detailed, actionable information for every query type
- Remember conversation context across multiple exchanges
- Handle follow-up questions intelligently based on previous conversation
- Never say "I don't know" - always provide helpful guidance or direct to appropriate resources

RESPONSE STYLE:
- Be conversational, warm, and professional
- Provide detailed, helpful answers
- Use examples when helpful
- Break down complex topics into understandable parts
- Always prioritize patient safety and well-being
- When appropriate, suggest using specific platform features

Remember: You are a complete healthcare companion that can help with EVERYTHING - from booking appointments to understanding insurance, from symptom analysis to medication management. You know about all available services and can guide users intelligently."""
            
            # Build conversation messages
            messages = []
            
            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history[-5:])  # Last 5 exchanges for context
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Prepare the request body for Claude (optimized for RAG responses)
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,  # Increased for detailed RAG responses
                "temperature": 0.7,  # Balanced creativity and accuracy
                "system": system_prompt,
                "messages": messages
            }
            
            # Try to invoke the model with timeout protection
            last_error = None
            for model_id in [self.model_id] + self.fallback_models:
                try:
                    # Use boto3's built-in timeout via config
                    from botocore.config import Config
                    config = Config(
                        connect_timeout=5,
                        read_timeout=10,
                        retries={'max_attempts': 1}
                    )
                    bedrock_client_fast = boto3.client('bedrock-runtime', 
                                                      region_name=os.getenv('AWS_REGION', 'us-east-1'),
                                                      config=config)
                    
                    response = bedrock_client_fast.invoke_model(
                        modelId=model_id,
                        body=json.dumps(request_body),
                        contentType='application/json'
                    )
                    
                    # Parse the response
                    response_body = json.loads(response['body'].read())
                    return response_body['content'][0]['text']
                except Exception as e:
                    last_error = e
                    # If it's not a model ID issue, break and return error
                    if "ValidationException" not in str(e) or "model ID" not in str(e):
                        break
                    continue
            
            # If all models failed, return helpful error
            error_msg = str(last_error) if last_error else "Unknown error"
            
            # Handle specific AWS Bedrock access issues - use intelligent fallback
            if "ResourceNotFoundException" in error_msg or "use case details" in error_msg.lower():
                # Use intelligent fallback with conversation context
                return IntelligentFallback.get_fallback_response(prompt, conversation_history, None)
            
            elif "credentials" in error_msg.lower() or "access" in error_msg.lower() or "AccessDenied" in error_msg:
                return "I'm having trouble connecting to my AI brain right now. Please ensure AWS credentials are configured for intelligent responses."
            elif "ValidationException" in error_msg or "model ID" in error_msg:
                return "I'm configured to use AWS Bedrock for intelligent responses, but there's a configuration issue. The bot will still work for structured queries (appointments, insurance, etc.), but general conversation features require AWS Bedrock setup. Please configure AWS Bedrock model access or use the specific feature commands."
            
            # Generic error - provide helpful fallback
            return """I encountered a technical issue, but I'm still here to help!

I can assist you with:
- Booking appointments
- Insurance information
- Patient management
-  Hospital services
-  And more!

Try asking: What services do you offer? or How do I book an appointment?"""
            
        except Exception as e:
            # More helpful error message
            error_msg = str(e)
            
            # Handle specific AWS Bedrock access issues - use intelligent fallback
            if "ResourceNotFoundException" in error_msg or "use case details" in error_msg.lower():
                # Use intelligent fallback with conversation context
                return IntelligentFallback.get_fallback_response(prompt, conversation_history, None)
            
            elif "credentials" in error_msg.lower() or "access" in error_msg.lower() or "AccessDenied" in error_msg:
                return "I'm having trouble connecting to my AI brain right now. Please ensure AWS credentials are configured for intelligent responses."
            
            elif "ValidationException" in error_msg or "model ID" in error_msg:
                return "I'm configured to use AWS Bedrock, but there's a model configuration issue. I can still help with structured queries (appointments, insurance, etc.)!"
            
            # Generic error - provide helpful fallback
            return """I encountered a technical issue, but I'm still here to help!

I can assist you with:
- Booking appointments
- Insurance information
- Patient management
-  Hospital services
-  And more!

Try asking: What services do you offer? or How do I book an appointment?"""

class AWSBedrockChat(Action):
    """Super intelligent RAG-powered chatbot with AWS services for conversational responses"""
    
    # Class-level guard to prevent multiple executions for same message
    _execution_tracker = {}
    _execution_lock = threading.Lock()
    
    def __init__(self):
        # Lazy initialization - only create services when needed
        # This allows simple queries to work even if AWS services fail
        self.bedrock_helper = None
        self.rag_retriever = None
        self.aws_intelligence = None
        self.text_to_sql_agent = None
        self.symptom_analyzer = None
    
    def _get_bedrock_helper(self):
        """Lazy initialization of Bedrock helper"""
        if self.bedrock_helper is None:
            try:
                self.bedrock_helper = AWSBedrockHelper()
            except Exception as e:
                logging.warning(f"Could not initialize Bedrock helper: {e}")
                self.bedrock_helper = None
        return self.bedrock_helper
    
    def _get_rag_retriever(self):
        """Lazy initialization of RAG retriever"""
        if self.rag_retriever is None:
            try:
                self.rag_retriever = RAGRetriever()
            except Exception as e:
                logging.warning(f"Could not initialize RAG retriever: {e}")
                self.rag_retriever = None
        return self.rag_retriever
    
    def _get_aws_intelligence(self):
        """Lazy initialization of AWS Intelligence"""
        if self.aws_intelligence is None:
            try:
                self.aws_intelligence = AWSIntelligenceServices()
            except Exception as e:
                logging.warning(f"Could not initialize AWS Intelligence: {e}")
                self.aws_intelligence = None
        return self.aws_intelligence
    
    def _get_text_to_sql_agent(self):
        """Lazy initialization of Text-to-SQL agent"""
        if self.text_to_sql_agent is None and TextToSQLAgent:
            try:
                self.text_to_sql_agent = TextToSQLAgent()
            except Exception as e:
                logging.warning(f"Could not initialize Text-to-SQL agent: {e}")
                self.text_to_sql_agent = None
        return self.text_to_sql_agent
    
    def _get_symptom_analyzer(self):
        """Lazy initialization of Symptom Analyzer"""
        if self.symptom_analyzer is None and SymptomAnalyzer:
            try:
                self.symptom_analyzer = SymptomAnalyzer()
            except Exception as e:
                logging.warning(f"Could not initialize Symptom Analyzer: {e}")
                self.symptom_analyzer = None
        return self.symptom_analyzer
    
    def name(self) -> Text:
        return "action_aws_bedrock_chat"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    
        # Wrap dispatcher with SafeDispatcher to prevent duplicates
        user_message = tracker.latest_message.get("text", "")
        sender_id = tracker.sender_id
        
        # Prevent multiple executions for the same message within 0.5 seconds (very short window)
        # This prevents rapid duplicates but allows legitimate follow-up messages
        message_hash = hashlib.md5(f"{sender_id}_{user_message}".encode()).hexdigest()
        current_time = time.time()
        
        with AWSBedrockChat._execution_lock:
            if message_hash in AWSBedrockChat._execution_tracker:
                last_time = AWSBedrockChat._execution_tracker[message_hash]
                if current_time - last_time < 0.5:  # 0.5 second window - very short to prevent rapid duplicates only
                    logging.warning(f"Preventing duplicate execution for message: '{user_message[:50]}...' from sender {sender_id}")
                    return []  # Return empty to prevent duplicate execution
            
            AWSBedrockChat._execution_tracker[message_hash] = current_time
            
            # Clean up old entries (older than 5 seconds)
            for mhash in list(AWSBedrockChat._execution_tracker.keys()):
                if current_time - AWSBedrockChat._execution_tracker[mhash] > 5:
                    del AWSBedrockChat._execution_tracker[mhash]
        
        safe_dispatcher = SafeDispatcher(dispatcher, sender_id, user_message)
        
        try:
            msg_lower = user_message.lower()
            logging.info(f"action_aws_bedrock_chat called with message: '{user_message}' from sender: {sender_id}")
            
            # Get conversation history for intelligent responses
            conversation_history = []
            for event in tracker.events[-10:]:  # Last 10 events for conversation context
                if event.get("event") == "user":
                    conversation_history.append({
                        "role": "user",
                        "content": event.get("text", "")
                    })
                elif event.get("event") == "bot":
                    conversation_history.append({
                        "role": "assistant",
                        "content": event.get("text", "")
                    })
            
            # PRIORITY 1: Handle "yes" responses FIRST (before AWS Intelligence)
            # This ensures "yes" is handled intelligently with database retrieval
            msg_lower = user_message.lower()
            if any(word in msg_lower for word in ["yes", "yeah", "yep", "sure", "ok", "okay"]) and len(msg_lower.strip()) < 10:
                # Check conversation context to understand what "yes" refers to
                context_lower = " ".join([msg.get("content", "").lower() for msg in conversation_history[-5:]])
                logging.info(f"Detected 'yes' response, context: {context_lower[:100]}")
                
                # Get RAG retriever for database access
                rag_retriever = self._get_rag_retriever()
                retrieved_context = {}
                
                # Retrieve context from database
                if rag_retriever:
                    try:
                        user_id = tracker.get_slot("user_id")
                        patient_id = None
                        if user_id:
                            try:
                                patient_info = DatabaseHelper.get_patient_info(user_id=user_id)
                                if patient_info:
                                    patient_id = patient_info.get('patient_id')
                            except:
                                pass
                        
                        retrieved_context = rag_retriever.retrieve_context(
                            query=user_message,
                            user_id=user_id,
                            patient_id=patient_id
                        )
                        logging.info(f"RAG retrieved context with {len(retrieved_context)} data types")
                    except Exception as e:
                        logging.debug(f"RAG retrieval for yes handling failed: {e}")
                
                doctors_from_rag = retrieved_context.get('doctors', []) if retrieved_context else []
                insurance_plans_from_rag = retrieved_context.get('insurance_plans', []) if retrieved_context else []
                
                # Handle "yes" for doctors - check if previous message mentioned doctors
                if "doctor" in context_lower or "specialist" in context_lower or "physician" in context_lower or "suggest" in context_lower or "search" in context_lower or "available" in context_lower:
                    logging.info("Handling 'yes' for doctors query")
                    specialty = None
                    if "viral" in context_lower or "symptom" in context_lower or "suffering" in context_lower:
                        specialty = "general medicine"
                    
                    doctors = doctors_from_rag
                    if not doctors and rag_retriever:
                        try:
                            doctors = rag_retriever.retrieve_doctors(user_message, specialty=specialty, limit=10)
                            logging.info(f"RAG retrieved {len(doctors) if doctors else 0} doctors")
                        except Exception as e:
                            logging.debug(f"RAG doctor retrieval failed: {e}")
                    
                    if not doctors:
                        try:
                            doctors = DatabaseHelper.get_doctors(specialty=specialty)
                            logging.info(f"DatabaseHelper retrieved {len(doctors) if doctors else 0} doctors")
                        except Exception as e:
                            logging.debug(f"Could not fetch doctors: {e}")
                    
                    if doctors and len(doctors) > 0:
                        response = f"I found {len(doctors)} doctor(s) available in our database:\n\n"
                        for i, doc in enumerate(doctors[:5], 1):
                            response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                            response += f"   Specialty: {doc.get('specialty', 'General Medicine')}\n"
                            if doc.get('department'):
                                response += f"   Department: {doc.get('department')}\n"
                            if doc.get('phone'):
                                response += f"   Phone: {doc.get('phone')}\n"
                            if doc.get('experience_years'):
                                response += f"   Experience: {doc.get('experience_years')} years\n"
                            if doc.get('rating'):
                                response += f"   Rating: {doc.get('rating')}/5\n"
                            response += "\n"
                        response += "Would you like to book an appointment with any of these doctors? I can help you schedule a visit!"
                        safe_dispatcher.utter_message(text=response)
                        logging.info(f"action_aws_bedrock_chat: Handled 'yes' for doctors, found {len(doctors)} doctors")
                        return []
                    else:
                        # ALWAYS use sample doctors if database fails
                        logging.warning("No doctors from database for 'yes' response, using sample data")
                        doctors = DatabaseHelper._get_sample_doctors(specialty="general medicine")
                        
                        if doctors and len(doctors) > 0:
                            response = f"✅ **I found {len(doctors)} doctor(s) for you:**\n\n"
                            for i, doc in enumerate(doctors[:5], 1):
                                response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                                response += f"   📋 Specialty: {doc.get('specialty', doc.get('doc_type', 'General Medicine'))}\n"
                                response += f"   🏥 Department: {doc.get('department', 'General Medicine')}\n"
                                if doc.get('phone'):
                                    response += f"   📞 Phone: {doc.get('phone')}\n"
                                if doc.get('email'):
                                    response += f"   ✉️ Email: {doc.get('email')}\n"
                                if doc.get('experience_years') or doc.get('experience'):
                                    exp = doc.get('experience_years') or doc.get('experience')
                                    response += f"   👨‍⚕️ Experience: {exp} years\n"
                                if doc.get('rating'):
                                    response += f"   ⭐ Rating: {doc.get('rating')}/5\n"
                                response += "\n"
                            response += "📅 **Would you like to book an appointment with any of these doctors?**\n"
                            response += "Just tell me the doctor's name or number!"
                        else:
                            # Final fallback
                            response = "✅ **I found these doctors for you:**\n\n"
                            response += "1. Dr. Sarah Johnson - General Medicine - (555) 123-4567\n"
                            response += "2. Dr. Emily Williams - Gynecology - (555) 201-0002\n"
                            response += "3. Dr. Michael Chen - Cardiology - (555) 202-0001\n\n"
                            response += "Would you like to book an appointment with any of these doctors?"
                        
                        safe_dispatcher.utter_message(text=response)
                        logging.info(f"action_aws_bedrock_chat: Handled 'yes' for doctors, showing {len(doctors) if doctors else 0} doctors")
                        return []
                
                # Handle "yes" for insurance
                elif "insurance" in context_lower or "plan" in context_lower or "coverage" in context_lower:
                    logging.info("Handling 'yes' for insurance query")
                    insurance_plans = insurance_plans_from_rag
                    if not insurance_plans:
                        try:
                            insurance_plans = DatabaseHelper.get_insurance_plans()
                        except Exception as e:
                            logging.debug(f"Could not fetch insurance plans: {e}")
                    
                    if insurance_plans and len(insurance_plans) > 0:
                        response = f"Here are all available insurance plans from our database ({len(insurance_plans)} plans):\n\n"
                        for i, plan in enumerate(insurance_plans[:5], 1):
                            response += f"**{i}. {plan.get('name', 'Insurance Plan')}**\n"
                            response += f"   Monthly Premium: {plan.get('monthly_premium', 'N/A')}\n"
                            response += f"   Deductible: {plan.get('deductible', 'N/A')}\n"
                            response += f"   Coverage: {plan.get('coverage', 'N/A')}\n"
                            features = plan.get('features', [])
                            if features:
                                if isinstance(features, list):
                                    response += f"   Features: {', '.join(features[:3])}\n"
                                else:
                                    response += f"   Features: {features}\n"
                            response += "\n"
                        response += "Would you like more details about any specific plan, or personalized recommendations based on your needs?"
                        safe_dispatcher.utter_message(text=response)
                        logging.info(f"action_aws_bedrock_chat: Handled 'yes' for insurance, found {len(insurance_plans)} plans")
                        return []
                    else:
                        # Fallback for insurance
                        response = "I can help you with insurance! I can show you available plans, explain coverage options, and help you choose the right plan. Would you like me to show you our insurance plans?"
                        safe_dispatcher.utter_message(text=response)
                        logging.info("action_aws_bedrock_chat: Handled 'yes' for insurance, but no plans found")
                        return []
                
                # Fallback for "yes" that doesn't match specific conditions
                else:
                    # Use intelligent fallback to provide helpful response
                    try:
                        response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                        if not response or len(response) < 20:
                            response = "I'm here to help! Could you please tell me more about what you need? For example:\n• 'I need to find a doctor'\n• 'I want to book an appointment'\n• 'I need help with insurance'\n• 'I have [symptoms]'\n\nWhat can I help you with?"
                        safe_dispatcher.utter_message(text=response)
                        logging.info("action_aws_bedrock_chat: Handled generic 'yes' with fallback")
                        return []
                    except Exception as e:
                        logging.error(f"Error in yes fallback: {e}")
                        # Ensure we still send a response
                        response = "I'm here to help! Could you please tell me more about what you need? For example:\n• 'I need to find a doctor'\n• 'I want to book an appointment'\n• 'I need help with insurance'\n• 'I have [symptoms]'\n\nWhat can I help you with?"
                        safe_dispatcher.utter_message(text=response)
                        logging.info("action_aws_bedrock_chat: Handled generic 'yes' with error fallback")
                        return []
            
            # Try to use AWS Bedrock for intelligent conversational responses
            # This enables super intelligent back-and-forth conversations
            aws_intelligence = self._get_aws_intelligence()
            bedrock_helper = self._get_bedrock_helper()
            
            # For ALL queries, try to use intelligent Bedrock response
            intelligent_response = None
            
            if aws_intelligence:
                try:
                    # Use AWS Intelligence for super intelligent conversational responses
                    # This works for ALL queries - greetings, questions, everything
                    intelligent_response = aws_intelligence.generate_conversational_response(
                        user_message=user_message,
                        context={},  # Will be populated below for complex queries
                        conversation_history=conversation_history,
                        medical_entities={},  # Will be populated below
                        sentiment=None  # Will be populated below
                    )
                    
                    # Check if response is an error message - if so, don't use it, use fallback instead
                    if intelligent_response and intelligent_response.strip():
                        error_indicators = [
                            "trouble connecting to my AI brain",
                            "AWS credentials are configured",
                            "configuration issue",
                            "encountered a technical issue"
                        ]
                        is_error_response = any(indicator in intelligent_response for indicator in error_indicators)
                        
                        if not is_error_response:
                            # We got a valid intelligent response! Use it.
                            safe_dispatcher.utter_message(text=intelligent_response)
                            logging.info(f"action_aws_bedrock_chat returning intelligent response: {intelligent_response[:100]}...")
                            return []
                        else:
                            # Error response from Bedrock - use fallback instead
                            logging.debug(f"Bedrock returned error message, using fallback instead")
                            intelligent_response = None
                except Exception as e:
                    logging.debug(f"AWS Intelligence conversational response failed: {e}")
            
            # Check if it's a simple query (greetings, etc.)
            is_simple_query = any(word in msg_lower for word in [
                "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
                "thanks", "thank you", "bye", "goodbye"
            ])
            
            if is_simple_query:
                # Simple response if Bedrock not available
                try:
                    if any(word in msg_lower for word in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
                        response = "Hello! I'm Dr. AI, your super intelligent healthcare assistant. I'm here to help with all your healthcare needs - appointments, insurance, finding doctors, symptom assessment, and more. How can I help you today?"
                    elif any(word in msg_lower for word in ["thanks", "thank you"]):
                        response = "You're welcome! I'm here whenever you need help with your healthcare needs. Is there anything else I can assist you with?"
                    elif any(word in msg_lower for word in ["bye", "goodbye"]):
                        response = "Goodbye! Take care of your health. Feel free to come back anytime you need assistance!"
                    else:
                        response = "Hello! How can I help you today?"
                    
                    safe_dispatcher.utter_message(text=response)
                    logging.info(f"action_aws_bedrock_chat returning simple response: {response[:100]}...")
                    return []
                except Exception as e:
                    logging.error(f"Error in simple query path: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
                    try:
                        safe_dispatcher.utter_message(text="Hello! I'm Dr. AI, your healthcare assistant. How can I help you today?")
                        return []
                    except Exception as e2:
                        logging.error(f"Error in fallback: {e2}")
                        return []
            
            # For complex queries (not simple greetings), continue with RAG and AWS Intelligence
                # RAG STEP 1: Retrieve relevant context from database
            user_id = tracker.get_slot("user_id")
            patient_id = None
            patient_info = None
            try:
                patient_info = DatabaseHelper.get_patient_info(user_id=user_id)
                if patient_info:
                    patient_id = patient_info.get('patient_id')
            except Exception as e:
                logging.debug(f"Could not get patient info for RAG: {e}")
            
            # AWS INTELLIGENCE STEP 1: Analyze query with AWS services (only for complex queries)
            aws_intelligence = self._get_aws_intelligence()
            query_analysis = None
            medical_entities = {}
            sentiment = None
            key_phrases = []
            
            if aws_intelligence:
                try:
                    query_analysis = aws_intelligence.analyze_query_intent(user_message)
                    medical_entities = aws_intelligence.extract_medical_entities(user_message)
                    sentiment = aws_intelligence.detect_sentiment(user_message)
                    key_phrases = aws_intelligence.detect_key_phrases(user_message)
                except Exception as e:
                    logging.debug(f"AWS Intelligence analysis failed: {e}")
        
            # RAG STEP 1: Retrieve relevant context from database (ALWAYS for intelligent responses)
            rag_retriever = self._get_rag_retriever()
            retrieved_context = {}
            context_string = ""
            
            # ENHANCED: Use Text-to-SQL Agent for intelligent database queries
            text_to_sql = self._get_text_to_sql_agent()
            
            # Always try to retrieve context from database for intelligent responses
            if rag_retriever:
                try:
                    # STEP 1: Use Text-to-SQL Agent to understand query and generate SQL
                    sql_result = None
                    if text_to_sql:
                        try:
                            # Understand query intent first
                            intent_result = text_to_sql.understand_query_intent(user_message)
                            logging.info(f"Text-to-SQL Intent: {intent_result.get('intent')}, Entities: {intent_result.get('entities')}")
                            
                            # Generate SQL if it's a database query
                            if intent_result.get('intent') in ['find_doctors', 'find_insurance', 'check_availability', 'book_appointment', 'get_medical_records']:
                                sql_result = text_to_sql.generate_sql(user_message, context=intent_result)
                                if sql_result:
                                    logging.info(f"Text-to-SQL generated SQL for table: {sql_result.get('table')}")
                                    
                                    # Execute SQL if we have a connection
                                    db_conn = DatabaseHelper.get_connection()
                                    if db_conn and sql_result.get('sql'):
                                        try:
                                            sql_data = text_to_sql.execute_sql_safely(
                                                sql_result['sql'],
                                                sql_result.get('parameters', {}),
                                                db_conn
                                            )
                                            
                                            # Map SQL results to retrieved_context
                                            table = sql_result.get('table', '')
                                            if table == 'doctors' and sql_data:
                                                retrieved_context['doctors'] = sql_data
                                                logging.info(f"Text-to-SQL: Retrieved {len(sql_data)} doctors")
                                            elif table == 'insurance_plans' and sql_data:
                                                retrieved_context['insurance_plans'] = sql_data
                                                logging.info(f"Text-to-SQL: Retrieved {len(sql_data)} insurance plans")
                                            elif table == 'availability_slots' and sql_data:
                                                retrieved_context['appointments'] = sql_data  # Map slots to appointments
                                                logging.info(f"Text-to-SQL: Retrieved {len(sql_data)} availability slots")
                                            
                                            DatabaseHelper.return_connection(db_conn)
                                        except Exception as e:
                                            logging.error(f"Error executing Text-to-SQL query: {e}")
                                            DatabaseHelper.return_connection(db_conn)
                        except Exception as e:
                            logging.error(f"Text-to-SQL agent failed: {e}")
                            import traceback
                            logging.error(traceback.format_exc())
                    
                    # STEP 2: Fallback to traditional RAG if Text-to-SQL didn't return data
                    if not any(retrieved_context.values()):
                        # Retrieve context using RAG system
                        retrieved_context = rag_retriever.retrieve_context(
                            query=user_message,
                            user_id=user_id,
                            patient_id=patient_id
                        )
                        
                        # Also retrieve specific data based on query type
                        msg_lower = user_message.lower()
                        
                        # If query mentions doctors, retrieve doctors from database
                        if any(word in msg_lower for word in ["doctor", "physician", "specialist", "suggest", "find", "list"]):
                            try:
                                doctors = rag_retriever.retrieve_doctors(user_message, limit=10)
                                if doctors:
                                    retrieved_context['doctors'] = doctors
                                    logging.info(f"RAG: Retrieved {len(doctors)} doctors from database")
                            except Exception as e:
                                logging.debug(f"RAG doctor retrieval failed: {e}")
                        
                        # If query mentions insurance, retrieve insurance plans from database
                        if any(word in msg_lower for word in ["insurance", "plan", "coverage", "benefit"]):
                            try:
                                insurance_plans = DatabaseHelper.get_insurance_plans()
                                if insurance_plans:
                                    retrieved_context['insurance_plans'] = insurance_plans
                                    logging.info(f"RAG: Retrieved {len(insurance_plans)} insurance plans from database")
                            except Exception as e:
                                logging.debug(f"RAG insurance retrieval failed: {e}")
                        
                        # If query mentions appointments, retrieve appointments from database
                        if any(word in msg_lower for word in ["appointment", "book", "schedule"]):
                            try:
                                if patient_id:
                                    appointments = rag_retriever.retrieve_appointments(patient_id=patient_id, limit=10)
                                    if appointments:
                                        retrieved_context['appointments'] = appointments
                                        logging.info(f"RAG: Retrieved {len(appointments)} appointments from database")
                            except Exception as e:
                                logging.debug(f"RAG appointment retrieval failed: {e}")
                    
                    # Format context for LLM
                    context_string = rag_retriever.format_context_for_llm(retrieved_context)
                    logging.info(f"RAG: Retrieved context with {len(retrieved_context)} data types")
                except Exception as e:
                    logging.error(f"RAG retrieval failed: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
                    # Continue without RAG context - bot will still work
            
            # Get detected intent and entities for context
            intent = tracker.latest_message.get("intent", {}).get("name", "")
            entities = tracker.latest_message.get("entities", [])
        
            # Get patient info if available for personalized responses (with timeout protection)
            patient_info = None
            appointments = None
            try:
                user_id = tracker.get_slot("user_id")
                if user_id:
                    # Quick timeout for patient info
                    import signal
                    def timeout_handler(signum, frame):
                        raise TimeoutError("Patient info query timed out")
                    
                    # Try to get patient info but don't block if it's slow
                    try:
                        patient_info = DatabaseHelper.get_patient_info(user_id=user_id)
                        if patient_info:
                            appointments = DatabaseHelper.get_appointments(patient_id=patient_info.get('patient_id'))
                    except Exception as e:
                        logging.debug(f"Could not fetch patient info (non-critical): {e}")
                        patient_info = None
                        appointments = None
            except Exception as e:
                logging.debug(f"Error getting patient context (non-critical): {e}")
                # Continue without patient info - don't block
            
            # RAG STEP 2: Build enhanced message with RAG-retrieved context
            # This is the core of RAG - augmenting the prompt with retrieved data
            enhanced_message = f"""User Query: {user_message}

RETRIEVED CONTEXT FROM DATABASE (RAG):
{context_string}

Please provide a comprehensive, intelligent response based on the retrieved context above. Use the specific information (doctors, insurance plans, appointments, patient info, medications, lab results) to give accurate, helpful answers. If the context contains relevant information, reference it specifically. If not, provide general helpful guidance."""
            
            # Add intent/entity info
            context_info = []
            if intent and intent != "nlu_fallback":
                context_info.append(f"Intent: {intent}")
            if entities:
                entity_info = ", ".join([f"{e.get('entity')}: {e.get('value')}" for e in entities])
                context_info.append(f"Entities: {entity_info}")
            
            if context_info:
                enhanced_message += f"\n\n[Detected: {', '.join(context_info)}]"
            
            # Get conversation history from tracker (for conversational context - back and forth)
            conversation_history = []
            for event in tracker.events[-10:]:  # Last 10 events for better conversation context
                if event.get("event") == "user":
                    conversation_history.append({
                        "role": "user",
                        "content": event.get("text", "")
                    })
                elif event.get("event") == "bot":
                    conversation_history.append({
                        "role": "assistant",
                        "content": event.get("text", "")
                    })
            
            # AWS INTELLIGENCE STEP 2: Generate super intelligent conversational response
            # (Simple queries already handled above, so this is only for complex queries)
            response = None
            
            # COMPLEX QUERIES: Use AWS Bedrock LLM with RAG context for super intelligent responses
            try:
                # PRIORITY 1: Use AWS Bedrock with RAG context for intelligent responses
                if bedrock_helper and context_string:
                    # Use Bedrock with RAG-retrieved context for intelligent, database-aware responses
                    enhanced_prompt = f"""User Query: {user_message}

RETRIEVED CONTEXT FROM DATABASE (RAG):
{context_string}

Please provide a comprehensive, intelligent response using the retrieved context above. 
- If doctors are in the context, reference them specifically by name and specialty
- If insurance plans are in the context, reference them specifically with details
- If appointments are in the context, reference them specifically
- Use the specific information from the database to give accurate, helpful answers
- If context is available, prioritize it over general knowledge
- Always cite specific information from the retrieved context when available

Conversation History:
{json.dumps(conversation_history[-5:], indent=2) if conversation_history else 'None'}

Provide a helpful, empathetic, and comprehensive response."""
                    
                    response = bedrock_helper.get_response(enhanced_prompt, conversation_history)
                    if response and response.strip():
                        # Check if response is an error message
                        error_indicators = [
                            "trouble connecting to my AI brain",
                            "AWS credentials are configured",
                            "configuration issue",
                            "encountered a technical issue"
                        ]
                        is_error_response = any(indicator in response for indicator in error_indicators)
                        if is_error_response:
                            response = None  # Will use fallback below
                        else:
                            logging.info(f"Bedrock with RAG: Generated intelligent response using database context")
                
                # PRIORITY 2: Use AWS Intelligence Services if Bedrock direct call didn't work
                if not response and aws_intelligence:
                    response = aws_intelligence.generate_conversational_response(
                        user_message=user_message,
                        context=retrieved_context,
                        conversation_history=conversation_history,
                        medical_entities=medical_entities,
                        sentiment=sentiment
                    )
                else:
                    response = None
                
                # Check if response is an error message - if so, don't use it
                if response and response.strip():
                    error_indicators = [
                        "trouble connecting to my AI brain",
                        "AWS credentials are configured",
                        "configuration issue",
                        "encountered a technical issue"
                    ]
                    is_error_response = any(indicator in response for indicator in error_indicators)
                    
                    if is_error_response:
                        # Error response from Bedrock - use fallback instead
                        logging.debug(f"Bedrock returned error message, using fallback instead")
                        response = None
                else:
                    response = None
                
            except Exception as e:
                logging.debug(f"AWS Intelligence failed, using intelligent fallback: {e}")
            # Fallback to intelligent response generation with database context
            if not response:
                msg_lower = user_message.lower()
                
                # Check for general physician requests first
                if any(word in msg_lower for word in ["general physician", "general practitioner", "GP", "family doctor", "primary care", "general doctor"]):
                    specialty = "general medicine"
                    doctors = None
                    try:
                        doctors = DatabaseHelper.get_doctors(specialty=specialty)
                    except Exception as e:
                        logging.debug(f"Could not fetch doctors: {e}")
                    
                    if doctors and len(doctors) > 0:
                        response = f"I found {len(doctors)} general physician(s) available:\n\n"
                        for i, doc in enumerate(doctors[:5], 1):
                            response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                            response += f"   Specialty: {doc.get('specialty', 'General Medicine')}\n"
                            response += f"   Department: {doc.get('department', 'General Medicine')}\n"
                            if doc.get('phone'):
                                response += f"   Phone: {doc.get('phone')}\n"
                            response += "\n"
                        response += "Would you like to book an appointment with any of these general physicians?"
                    else:
                        response = "I can help you find a general physician! I can search our database for available general practitioners, show you their contact information, and help you book an appointment. Would you like me to search for available general physicians now?"
                
                # Handle "suggest doctors" or "show doctors" queries
                elif any(word in msg_lower for word in ["suggest", "show", "find", "list"]) and any(word in msg_lower for word in ["doctor", "doctors", "specialist", "physician"]):
                    # User wants to see doctors - search for them using multiple methods
                    specialty = None
                    specialty_display_name = "doctor"
                    
                    # Check if viral/symptom was mentioned
                    if "viral" in msg_lower or "symptom" in msg_lower or "suffering" in msg_lower:
                        specialty = "general medicine"
                        specialty_display_name = "general physician"
                    
                    doctors = None
                    
                    # Attempt 1: Try RAG retriever first
                    if rag_retriever:
                        try:
                            doctors = rag_retriever.retrieve_doctors(user_message, specialty=specialty, limit=10)
                            if doctors:
                                logging.info(f"RAG: Retrieved {len(doctors)} doctors from database")
                        except Exception as e:
                            logging.debug(f"RAG retrieval failed: {e}")
                    
                    # Attempt 2: Try DatabaseHelper
                    if not doctors or len(doctors) == 0:
                        try:
                            doctors = DatabaseHelper.get_doctors(specialty=specialty)
                            if doctors:
                                logging.info(f"DatabaseHelper: Retrieved {len(doctors)} doctors from database")
                        except Exception as e:
                            logging.debug(f"DatabaseHelper failed: {e}")
                    
                    # Attempt 3: Try to get ALL doctors if specialty search failed
                    if not doctors or len(doctors) == 0:
                        try:
                            doctors = DatabaseHelper.get_doctors()  # No specialty filter
                            if doctors:
                                logging.info(f"DatabaseHelper: Retrieved {len(doctors)} doctors (all specialties)")
                        except Exception as e:
                            logging.error(f"Could not fetch any doctors: {e}")
                            import traceback
                            logging.error(traceback.format_exc())
                    
                    # ALWAYS use sample doctors if database fails (never show generic message)
                    if not doctors or len(doctors) == 0:
                        logging.warning(f"No doctors from database, using sample data for specialty: {specialty}")
                        doctors = DatabaseHelper._get_sample_doctors(specialty)
                        logging.info(f"Using {len(doctors) if doctors else 0} sample doctors")
                    
                    if doctors and len(doctors) > 0:
                        response = f"✅ **I found {len(doctors)} {specialty_display_name}{'s' if len(doctors) > 1 else ''}:**\n\n"
                        for i, doc in enumerate(doctors[:5], 1):
                            response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                            response += f"   📋 Specialty: {doc.get('specialty', doc.get('doc_type', 'General Medicine'))}\n"
                            response += f"   🏥 Department: {doc.get('department', 'General Medicine')}\n"
                            if doc.get('phone'):
                                response += f"   📞 Phone: {doc.get('phone')}\n"
                            if doc.get('email'):
                                response += f"   ✉️ Email: {doc.get('email')}\n"
                            if doc.get('experience_years') or doc.get('experience'):
                                exp = doc.get('experience_years') or doc.get('experience')
                                response += f"   👨‍⚕️ Experience: {exp} years\n"
                            if doc.get('rating'):
                                response += f"   ⭐ Rating: {doc.get('rating')}/5\n"
                            response += "\n"
                        response += "📅 **Would you like to book an appointment with any of these doctors?**\n"
                        response += "Just tell me the doctor's name or number and your preferred date/time!"
                        logging.info(f"Successfully displayed {len(doctors)} doctors to user")
                    else:
                        # Final fallback - should never reach here, but just in case
                        logging.error("CRITICAL: No doctors available even from sample data!")
                        response = f"I found these {specialty_display_name}s for you:\n\n"
                        response += "1. Dr. Sarah Johnson - General Medicine\n"
                        response += "2. Dr. Emily Williams - Gynecology\n"
                        response += "3. Dr. Michael Chen - Cardiology\n\n"
                        response += "Would you like to book an appointment with any of these doctors?"
                
                # Handle "yes" responses intelligently for ALL scenarios using RAG and database
                elif any(word in msg_lower for word in ["yes", "yeah", "yep", "sure", "ok", "okay"]) and len(msg_lower.strip()) < 10:
                    # Check conversation context to understand what "yes" refers to
                    context_lower = " ".join([msg.get("content", "").lower() for msg in conversation_history[-5:]])
                    
                    # Use RAG to retrieve relevant data from database
                    doctors_from_rag = retrieved_context.get('doctors', []) if retrieved_context else []
                    insurance_plans_from_rag = retrieved_context.get('insurance_plans', []) if retrieved_context else []
                    appointments_from_rag = retrieved_context.get('appointments', []) if retrieved_context else []
                    
                    if "insurance" in context_lower or "plan" in context_lower or "coverage" in context_lower:
                        # User said yes to insurance - use RAG to retrieve from database
                        insurance_plans = insurance_plans_from_rag
                        if not insurance_plans:
                            try:
                                insurance_plans = DatabaseHelper.get_insurance_plans()
                            except Exception as e:
                                logging.debug(f"Could not fetch insurance plans: {e}")
                        
                        # If still no plans, try RAG retriever
                        if not insurance_plans and rag_retriever:
                            try:
                                # RAG will retrieve insurance plans in retrieve_context
                                pass
                            except Exception as e:
                                logging.debug(f"RAG insurance retrieval failed: {e}")
                        
                        if insurance_plans and len(insurance_plans) > 0:
                            response = f"Here are all available insurance plans from our database ({len(insurance_plans)} plans):\n\n"
                            for i, plan in enumerate(insurance_plans[:5], 1):
                                response += f"**{i}. {plan.get('name', 'Insurance Plan')}**\n"
                                response += f"   Monthly Premium: {plan.get('monthly_premium', 'N/A')}\n"
                                response += f"   Deductible: {plan.get('deductible', 'N/A')}\n"
                                response += f"   Coverage: {plan.get('coverage', 'N/A')}\n"
                                features = plan.get('features', [])
                                if features:
                                    if isinstance(features, list):
                                        response += f"   Features: {', '.join(features[:3])}\n"
                                    else:
                                        response += f"   Features: {features}\n"
                                response += "\n"
                            response += "Would you like more details about any specific plan, or personalized recommendations based on your needs?"
                        else:
                            # Fallback to default plans
                            response = """Here are all available insurance plans:

**1. Basic Health Plan**
   Monthly Premium: $150
   Deductible: $1,000
   Coverage: 80%
   Features: Primary care visits, Emergency visits, Basic prescriptions
   Best for: Budget-conscious individuals

**2. Premium Health Plan**
   Monthly Premium: $300
   Deductible: $500
   Coverage: 90%
   Features: All basic features, Specialist visits, Mental health coverage, Dental & Vision
   Best for: Regular medical needs

**3. Family Health Plan**
   Monthly Premium: $450
   Deductible: $750
   Coverage: 85%
   Features: All premium features, Family coverage, Maternity care, Pediatric care
   Best for: Families with children

Would you like more details about any specific plan, or personalized recommendations?"""
                    
                    elif "doctor" in context_lower or "specialist" in context_lower or "physician" in context_lower or "suggest" in context_lower:
                        # User said yes to finding doctors - use RAG to retrieve from database intelligently
                        specialty = None
                        if "viral" in context_lower or "symptom" in context_lower or "suffering" in context_lower:
                            specialty = "general medicine"
                        elif "gynecologist" in context_lower or "gynacologist" in context_lower or "gynec" in context_lower or "gynaec" in context_lower:
                            specialty = "gynecology"
                        elif "cardiologist" in context_lower:
                            specialty = "cardiology"
                        elif "neurologist" in context_lower:
                            specialty = "neurology"
                        elif "dermatologist" in context_lower:
                            specialty = "dermatology"
                        elif "pediatrician" in context_lower:
                            specialty = "pediatrics"
                        
                        # PRIORITY: Use RAG-retrieved doctors from database
                        doctors = doctors_from_rag
                        if not doctors and rag_retriever:
                            try:
                                # Use RAG retriever to get doctors from database
                                doctors = rag_retriever.retrieve_doctors(user_message, specialty=specialty, limit=10)
                                logging.info(f"RAG: Retrieved {len(doctors) if doctors else 0} doctors directly from database")
                            except Exception as e:
                                logging.error(f"RAG doctor retrieval failed: {e}")
                                import traceback
                                logging.error(traceback.format_exc())
                        
                        # Fallback to DatabaseHelper if RAG didn't return doctors
                        if not doctors:
                            try:
                                doctors = DatabaseHelper.get_doctors(specialty=specialty)
                                logging.info(f"DatabaseHelper: Retrieved {len(doctors) if doctors else 0} doctors")
                            except Exception as e:
                                logging.error(f"DatabaseHelper failed: {e}")
                                import traceback
                                logging.error(traceback.format_exc())
                        
                        # ALWAYS use sample doctors if database fails (never show generic message)
                        if not doctors or len(doctors) == 0:
                            logging.warning(f"No doctors from database, using sample data for specialty: {specialty}")
                            doctors = DatabaseHelper._get_sample_doctors(specialty)
                            logging.info(f"Using {len(doctors) if doctors else 0} sample doctors")
                        
                        if doctors and len(doctors) > 0:
                            response = f"I found {len(doctors)} doctor(s) available in our database:\n\n"
                            for i, doc in enumerate(doctors[:5], 1):
                                response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                                response += f"   Specialty: {doc.get('specialty', 'General Medicine')}\n"
                                if doc.get('department'):
                                    response += f"   Department: {doc.get('department')}\n"
                                if doc.get('phone'):
                                    response += f"   Phone: {doc.get('phone')}\n"
                                if doc.get('experience_years'):
                                    response += f"   Experience: {doc.get('experience_years')} years\n"
                                if doc.get('rating'):
                                    response += f"   Rating: {doc.get('rating')}/5\n"
                                response += "\n"
                            response += "Would you like to book an appointment with any of these doctors? I can help you schedule a visit!"
                        else:
                            # ALWAYS use sample doctors if database fails
                            logging.warning("No doctors from database, using sample data")
                            doctors = DatabaseHelper._get_sample_doctors()
                            
                            if doctors and len(doctors) > 0:
                                response = f"✅ **I found {len(doctors)} doctor(s) for you:**\n\n"
                                for i, doc in enumerate(doctors[:5], 1):
                                    response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                                    response += f"   📋 Specialty: {doc.get('specialty', doc.get('doc_type', 'General Medicine'))}\n"
                                    response += f"   🏥 Department: {doc.get('department', 'General Medicine')}\n"
                                    if doc.get('phone'):
                                        response += f"   📞 Phone: {doc.get('phone')}\n"
                                    if doc.get('email'):
                                        response += f"   ✉️ Email: {doc.get('email')}\n"
                                    if doc.get('experience_years') or doc.get('experience'):
                                        exp = doc.get('experience_years') or doc.get('experience')
                                        response += f"   👨‍⚕️ Experience: {exp} years\n"
                                    if doc.get('rating'):
                                        response += f"   ⭐ Rating: {doc.get('rating')}/5\n"
                                    response += "\n"
                                response += "📅 **Would you like to book an appointment with any of these doctors?**\n"
                                response += "Just tell me the doctor's name or number!"
                            else:
                                # Final fallback
                                response = "✅ **I found these doctors for you:**\n\n"
                                response += "1. Dr. Sarah Johnson - General Medicine - (555) 123-4567\n"
                                response += "2. Dr. Emily Williams - Gynecology - (555) 201-0002\n"
                                response += "3. Dr. Michael Chen - Cardiology - (555) 202-0001\n\n"
                                response += "Would you like to book an appointment with any of these doctors?"
                    
                    elif "appointment" in context_lower or "book" in context_lower or "schedule" in context_lower:
                        # User said yes to booking - use RAG to get available doctors and slots
                        doctors = doctors_from_rag
                        if not doctors:
                            try:
                                doctors = DatabaseHelper.get_doctors(limit=5)
                            except Exception as e:
                                logging.debug(f"Could not fetch doctors: {e}")
                        
                        if doctors and len(doctors) > 0:
                            response = "Great! I can help you book an appointment. Here are available doctors:\n\n"
                            for i, doc in enumerate(doctors[:3], 1):
                                response += f"{i}. Dr. {doc.get('name', 'N/A')} - {doc.get('specialty', 'General Medicine')}\n"
                            response += "\nPlease tell me:\n• Which doctor you'd like to see\n• Your preferred date and time\n• Your symptoms or reason for visit\n\nI'll help you schedule the appointment!"
                        else:
                            response = "Great! To book an appointment, please tell me:\n• Your symptoms or preferred specialty\n• Preferred date and time (if any)\n• Any specific doctor preference\n\nI'll find the right doctor and show you available time slots."
                    
                    elif "lab" in context_lower or "test" in context_lower or "result" in context_lower:
                        # User said yes to lab results
                        response = "I can help you access and understand your lab results! I can:\n• Retrieve your test results from our system\n• Explain what your results mean\n• Help you understand your diagnosis\n• Guide you on next steps\n\nWould you like me to retrieve your recent lab results, or do you have specific test results you'd like me to explain?"
                    
                    elif "bill" in context_lower or "billing" in context_lower or "payment" in context_lower:
                        # User said yes to billing
                        response = "I can help with billing! I can:\n• Show you billing statements\n• Explain charges and fees\n• Help with payment plans\n• Verify insurance coverage for procedures\n• Provide cost estimates\n\nWhat billing question can I help with? You can ask about a specific bill, payment options, or cost estimates."
                    
                    elif "wellness" in context_lower or "diet" in context_lower or "exercise" in context_lower or "fitness" in context_lower:
                        # User said yes to wellness
                        response = "I can help with wellness! I can provide:\n• Personalized diet recommendations\n• Exercise and fitness plans\n• Sleep hygiene tips\n• Weight management guidance\n• Nutrition advice\n• Lifestyle recommendations\n\nWhat aspect of wellness would you like help with? For example, you can ask about diet plans, exercise routines, or sleep tips."
                    
                    elif "mental" in context_lower or "therapy" in context_lower or "counselor" in context_lower:
                        # User said yes to mental health
                        response = "I can help with mental health support! I can:\n• Provide mental health assessments (GAD-7 for anxiety, PHQ-9 for depression)\n• Help you find mental health professionals\n• Provide resources for stress management\n• Guide you to appropriate care\n\nFor mental health crises, please contact a crisis hotline or seek immediate professional help. How can I assist you with mental health support?"
                    
                    elif "location" in context_lower or "hospital" in context_lower or "clinic" in context_lower:
                        # User said yes to locations
                        response = "I can help you find healthcare facilities! I can:\n• Find hospitals and clinics near you\n• Show addresses and contact information\n• Check hours of operation\n• Show services available at each location\n\nWhat type of facility are you looking for? You can ask for hospitals, clinics, urgent care centers, or specific specialties."
                    
                    else:
                        # Generic yes - use intelligent fallback with RAG context
                        response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                        if not response or len(response) < 50:
                            response = "I'm here to help! Could you please tell me more about what you need? For example:\n• 'I need to find a doctor'\n• 'I want to book an appointment'\n• 'I need help with insurance'\n• 'I have [symptoms]'\n• 'I need lab results'\n• 'I have billing questions'\n\nWhat can I help you with?"
                
                # ENHANCED: Check for symptoms - use Symptom Analyzer for intelligent recommendations
                elif any(word in msg_lower for word in ["fever", "cold", "cough", "suffering", "symptom", "sick", "pain", "viral", "headache", "ache", "nausea", "vomiting", "diarrhea", "rash", "dizziness", "chest", "breathing", "shortness"]):
                    # Use Symptom Analyzer for intelligent analysis
                    symptom_analyzer = self._get_symptom_analyzer()
                    analysis_result = None
                    specialty = None
                    specialty_display_name = "General Physician"
                    urgency = "routine"
                    explanation = ""
                    
                    if symptom_analyzer:
                        try:
                            analysis_result = symptom_analyzer.analyze_symptoms(user_message)
                            specialty = analysis_result.get('recommended_specialty', 'general_medicine')
                            specialty_display_name = analysis_result.get('specialty_display_name', 'General Physician')
                            urgency = analysis_result.get('urgency', 'routine')
                            explanation = analysis_result.get('explanation', '')
                            
                            # Map specialty to database format
                            specialty_map = {
                                'general_medicine': 'general medicine',
                                'cardiology': 'cardiology',
                                'gynecology': 'gynecology',
                                'neurology': 'neurology',
                            'dermatology': 'dermatology',
                                'pediatrics': 'pediatrics',
                                'orthopedics': 'orthopedics',
                                'psychiatry': 'psychiatry',
                                'gastroenterology': 'gastroenterology',
                                'endocrinology': 'endocrinology',
                                'urology': 'urology',
                                'ent': 'ent',
                                'ophthalmology': 'ophthalmology',
                                'pulmonology': 'pulmonology'
                            }
                            specialty = specialty_map.get(specialty, 'general medicine')
                            
                            logging.info(f"Symptom Analyzer: {specialty_display_name} (urgency: {urgency})")
                        except Exception as e:
                            logging.error(f"Symptom Analyzer failed: {e}")
                            import traceback
                            logging.error(traceback.format_exc())
                    
                    # Fallback to rule-based if analyzer not available
                    if not analysis_result:
                        if "fever" in msg_lower or "cold" in msg_lower or "cough" in msg_lower or "viral" in msg_lower:
                            specialty = "general medicine"
                            specialty_display_name = "General Physician"
                        elif "blood pressure" in msg_lower or "high-blood" in msg_lower or "hypertension" in msg_lower or "chest pain" in msg_lower:
                            specialty = "cardiology"
                            specialty_display_name = "Cardiologist"
                        elif "sugar" in msg_lower or "diabetes" in msg_lower or "glucose" in msg_lower:
                            specialty = "endocrinology"
                            specialty_display_name = "Endocrinologist"
                        elif "headache" in msg_lower or "migraine" in msg_lower or "dizziness" in msg_lower:
                            specialty = "neurology"
                            specialty_display_name = "Neurologist"
                        elif "skin" in msg_lower or "rash" in msg_lower:
                            specialty = "dermatology"
                            specialty_display_name = "Dermatologist"
                        else:
                            specialty = "general medicine"
                            specialty_display_name = "General Physician"
                    
                    # Get doctors for the recommended specialty
                    doctors = None
                    try:
                        doctors = DatabaseHelper.get_doctors(specialty=specialty)
                    except Exception as e:
                        logging.error(f"Could not fetch doctors: {e}")
                    
                    # ALWAYS use sample doctors if database fails
                    if not doctors or len(doctors) == 0:
                        logging.warning(f"No doctors from database for specialty: {specialty}, using sample data")
                        doctors = DatabaseHelper._get_sample_doctors(specialty)
                    
                    if doctors and len(doctors) > 0:
                        # Build intelligent response with symptom analysis
                        if analysis_result and explanation:
                            response = f"🔍 **Symptom Analysis:**\n{explanation}\n\n"
                        else:
                            response = f"Based on your symptoms, I recommend seeing a **{specialty_display_name}**.\n\n"
                        
                        if urgency == 'emergency':
                            response += "⚠️ **URGENT:** This appears to be an emergency. Please seek immediate medical care or call 911.\n\n"
                        elif urgency == 'urgent':
                            response += "⚠️ **URGENT:** This should be addressed soon. I can help you find urgent care or schedule an appointment.\n\n"
                        
                        response += f"✅ **I found {len(doctors)} {specialty_display_name}{'s' if len(doctors) > 1 else ''} for you:**\n\n"
                        for i, doc in enumerate(doctors[:5], 1):
                            response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                            response += f"   📋 Specialty: {doc.get('specialty', doc.get('doc_type', specialty_display_name))}\n"
                            response += f"   🏥 Department: {doc.get('department', 'General Medicine')}\n"
                            if doc.get('phone'):
                                response += f"   📞 Phone: {doc.get('phone')}\n"
                            if doc.get('email'):
                                response += f"   ✉️ Email: {doc.get('email')}\n"
                            if doc.get('experience_years') or doc.get('experience'):
                                exp = doc.get('experience_years') or doc.get('experience')
                                response += f"   👨‍⚕️ Experience: {exp} years\n"
                            if doc.get('rating'):
                                response += f"   ⭐ Rating: {doc.get('rating')}/5\n"
                            response += "\n"
                        
                        response += "📅 **Would you like to book an appointment with any of these doctors?**\n"
                        if urgency == 'emergency':
                            response += "For emergencies, please call 911 or visit the nearest emergency room immediately."
                        else:
                            response += "Just tell me the doctor's name or number and your preferred date/time!"
                    else:
                        # Final fallback
                        response = f"Based on your symptoms, I recommend seeing a **{specialty_display_name}**.\n\n"
                        response += "✅ **I found these doctors for you:**\n\n"
                        response += "1. Dr. Sarah Johnson - General Medicine - (555) 123-4567\n"
                        response += "2. Dr. Emily Williams - Gynecology - (555) 201-0002\n"
                        response += "3. Dr. Michael Chen - Cardiology - (555) 202-0001\n\n"
                        response += "Would you like to book an appointment with any of these doctors?"
                
                # Lab results and medical records
                elif any(word in msg_lower for word in ["lab", "test", "result", "report", "blood test", "x-ray", "scan", "medical record", "diagnosis"]):
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                # Billing and payment
                elif any(word in msg_lower for word in ["bill", "billing", "payment", "cost", "price", "charge", "invoice", "statement", "pay", "fee"]):
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                # Emergency and urgent care
                elif any(word in msg_lower for word in ["emergency", "urgent", "immediate", "critical", "severe", "acute", "911", "ambulance"]):
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                # Mental health
                elif any(word in msg_lower for word in ["mental", "depression", "anxiety", "stress", "therapy", "counselor", "psychologist", "psychiatrist", "mental health", "emotional"]):
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                # Wellness and lifestyle
                elif any(word in msg_lower for word in ["wellness", "diet", "exercise", "fitness", "nutrition", "sleep", "weight", "lifestyle", "healthy", "wellbeing"]):
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                # Hospital and location services
                elif any(word in msg_lower for word in ["hospital", "location", "clinic", "address", "where", "nearby", "near me", "facility"]):
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                # Patient services
                elif any(word in msg_lower for word in ["patient", "service", "support", "help desk", "customer service", "assistance"]):
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                elif any(word in msg_lower for word in ["insurance", "plan", "coverage", "more about insurance"]):
                    # Handle insurance queries - check if asking for specific plan details
                    specific_plan = None
                    
                    # Check if asking for details on specific plan
                    if any(word in msg_lower for word in ["detail", "more about", "tell me about", "information about", "explain"]):
                        if "premium" in msg_lower or "2" in msg_lower:
                            specific_plan = "premium"
                        elif "basic" in msg_lower or "1" in msg_lower:
                            specific_plan = "basic"
                        elif "family" in msg_lower or "3" in msg_lower:
                            specific_plan = "family"
                    
                    if specific_plan:
                        # Show details for specific plan
                        if specific_plan == "premium":
                            response = """**Premium Health Plan - Detailed Information**

💰 **Cost:**
   • Monthly Premium: $300
   • Annual Cost: $3,600
   • Deductible: $500
   • Out-of-Pocket Maximum: $3,000

📋 **Coverage:**
   • Coverage Rate: 90% (You pay only 10%)
   • Covers most medical expenses after deductible

✨ **Features & Benefits:**
   ✅ All Basic Health Plan features
   ✅ Primary care visits (copay: $20)
   ✅ Emergency visits (copay: $100)
   ✅ Specialist visits (copay: $40)
   ✅ Mental health coverage (8 sessions/year)
   ✅ Dental & Vision included
   ✅ Prescription drug coverage (generic: $10, brand: $30)
   ✅ Preventive care (100% covered)
   ✅ Lab tests & diagnostics (90% covered)
   ✅ Wellness programs & gym membership discount
   ✅ Telehealth visits (unlimited, $0 copay)

👥 **Best For:**
   • Individuals with regular medical needs
   • Those who visit specialists frequently
   • Anyone wanting comprehensive coverage
   • People prioritizing mental health support

📞 **Network:**
   • Large network of doctors and hospitals
   • Over 10,000 providers in-network
   • Nationwide coverage

💡 **Why Choose Premium?**
   • Lower out-of-pocket costs when you need care
   • Comprehensive mental health support
   • Includes dental and vision
   • Great for regular doctor visits

Would you like to:
• Compare with other plans?
• Get personalized recommendations?
• Learn about enrollment process?
• See which doctors accept this plan?"""
                        elif specific_plan == "basic":
                            response = """**Basic Health Plan - Detailed Information**

💰 **Cost:**
   • Monthly Premium: $150
   • Annual Cost: $1,800
   • Deductible: $1,000
   • Out-of-Pocket Maximum: $6,000

📋 **Coverage:**
   • Coverage Rate: 80% (You pay 20%)
   • Essential medical coverage

✨ **Features & Benefits:**
   ✅ Primary care visits (copay: $30)
   ✅ Emergency visits (copay: $150)
   ✅ Basic prescriptions (generic: $15, brand: $50)
   ✅ Preventive care (100% covered)
   ✅ Lab tests (80% covered)
   ✅ Telehealth visits ($25 copay)

👥 **Best For:**
   • Budget-conscious individuals
   • Healthy individuals with minimal medical needs
   • Those wanting essential coverage only

Would you like to compare with Premium or Family plans?"""
                        elif specific_plan == "family":
                            response = """**Family Health Plan - Detailed Information**

💰 **Cost:**
   • Monthly Premium: $450
   • Annual Cost: $5,400
   • Deductible: $750
   • Out-of-Pocket Maximum: $5,000 (family)

📋 **Coverage:**
   • Coverage Rate: 85%
   • Family coverage (up to 4 members)

✨ **Features & Benefits:**
   ✅ All Premium Plan features
   ✅ Family coverage (4 members)
   ✅ Maternity care (prenatal, delivery, postnatal)
   ✅ Pediatric care (well-child visits, vaccinations)
   ✅ Family wellness programs
   ✅ Children's dental & vision
   ✅ NICU coverage
   ✅ Family therapy sessions

👥 **Best For:**
   • Families with children
   • Expecting parents
   • Multi-generational households

Would you like to see enrollment details or compare plans?"""
                    elif "more" in msg_lower or "all" in msg_lower or "available" in msg_lower:
                        # Show all insurance plans with details
                        response = """**All Available Insurance Plans:**

**1. Basic Health Plan**
   Monthly Premium: $150 | Deductible: $1,000 | Coverage: 80%
   Features: Primary care, Emergency visits, Basic prescriptions
   Best for: Budget-conscious individuals

**2. Premium Health Plan**
   Monthly Premium: $300 | Deductible: $500 | Coverage: 90%
   Features: All basic features, Specialist visits, Mental health, Dental & Vision
   Best for: Regular medical needs

**3. Family Health Plan**
   Monthly Premium: $450 | Deductible: $750 | Coverage: 85%
   Features: All premium features, Family coverage, Maternity care, Pediatric care
   Best for: Families with children

💡 **Want to learn more?** Ask:
• "Tell me more about the Premium Health Plan"
• "I want details on plan 2"
• "Compare Basic and Premium plans"

Would you like detailed information about any specific plan?"""
                    else:
                        # Use intelligent fallback with context
                        response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                elif any(word in msg_lower for word in ["appointment", "book", "schedule"]):
                    # Check if specialty is mentioned in appointment request
                    specialty = None
                    if "cardiologist" in msg_lower or "cardiac" in msg_lower:
                        specialty = "cardiology"
                    elif "gynecologist" in msg_lower or "gynacologist" in msg_lower or "gynec" in msg_lower or "gynaec" in msg_lower:
                        specialty = "gynecology"
                    elif "neurologist" in msg_lower:
                        specialty = "neurology"
                    elif "dermatologist" in msg_lower:
                        specialty = "dermatology"
                    elif "pediatrician" in msg_lower:
                        specialty = "pediatrics"
                    
                    if specialty:
                        # Get doctors for the requested specialty
                        doctors = None
                        try:
                            doctors = DatabaseHelper.get_doctors(specialty=specialty)
                        except Exception as e:
                            logging.debug(f"Could not fetch doctors: {e}")
                        
                        if doctors and len(doctors) > 0:
                            specialty_name = specialty.replace('_', ' ').title()
                            response = f"Great! I can help you book an appointment with a {specialty_name}. Here are available {specialty_name}s:\n\n"
                            for i, doc in enumerate(doctors[:3], 1):
                                response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                                response += f"   Specialty: {doc.get('specialty', 'General Medicine')}\n"
                                if doc.get('phone'):
                                    response += f"   Phone: {doc.get('phone')}\n"
                                response += "\n"
                            response += "Which doctor would you like to book an appointment with? Please provide the doctor's name or number, and I'll help you schedule."
                        else:
                            response = f"I can help you book an appointment with a {specialty.replace('_', ' ').title()}! Let me search for available doctors. Would you like me to find available {specialty.replace('_', ' ').title()}s for you?"
                    else:
                        # Use intelligent fallback with context
                        response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                elif any(word in msg_lower for word in ["show", "all", "list", "available"]) and "doctor" in msg_lower:
                    # User wants to see all doctors - get all doctors from database
                    doctors = None
                    try:
                        doctors = DatabaseHelper.get_doctors()  # No specialty filter = all doctors
                    except Exception as e:
                        logging.debug(f"Could not fetch doctors: {e}")
                    
                    # Fallback to API if database doesn't have doctors
                    if not doctors or len(doctors) == 0:
                        try:
                            response_api = requests.get(f"{REACT_APP_DUMMY_API}/doctors/all", timeout=5)
                            response_api.raise_for_status()
                            api_doctors = response_api.json()
                            if api_doctors:
                                doctors = [{
                                    'name': d.get('name', 'N/A'),
                                    'specialty': d.get('specialty', 'General Medicine'),
                                    'department': d.get('department', d.get('specialty', 'General Medicine')),
                                    'phone': d.get('phone', 'N/A'),
                                    'email': d.get('email', 'N/A')
                                } for d in api_doctors[:10]]
                        except requests.exceptions.RequestException as e:
                            logging.debug(f"API call failed: {e}")
                    
                    if doctors and len(doctors) > 0:
                        response = f" **All Available Doctors ({len(doctors)}):**\n\n"
                        for i, doc in enumerate(doctors[:10], 1):  # Show first 10
                            response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                            response += f"    Specialty: {doc.get('specialty', 'General Medicine')}\n"
                            response += f"    Department: {doc.get('department', 'N/A')}\n"
                            if doc.get('phone') and doc.get('phone') != 'N/A':
                                response += f"    Phone: {doc.get('phone')}\n"
                            response += "\n"
                        response += " **Next Steps:**\n"
                        response += "• Would you like to book an appointment with any of these doctors?\n"
                        response += "• I can help you find a specific specialist\n"
                        response += "• I can assist with scheduling\n\n"
                        response += "Which doctor would you like to book an appointment with?"
                    else:
                        # ALWAYS use sample doctors if database fails
                        logging.warning("No doctors from database, using sample data")
                        doctors = DatabaseHelper._get_sample_doctors()
                        
                        if doctors and len(doctors) > 0:
                            response = f"✅ **All Available Doctors ({len(doctors)}):**\n\n"
                            for i, doc in enumerate(doctors[:10], 1):
                                response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                                response += f"    Specialty: {doc.get('specialty', doc.get('doc_type', 'General Medicine'))}\n"
                                response += f"    Department: {doc.get('department', 'N/A')}\n"
                                if doc.get('phone') and doc.get('phone') != 'N/A':
                                    response += f"    Phone: {doc.get('phone')}\n"
                                response += "\n"
                            response += " **Next Steps:**\n"
                            response += "• Would you like to book an appointment with any of these doctors?\n"
                            response += "• I can help you find a specific specialist\n"
                            response += "• I can assist with scheduling\n\n"
                            response += "Which doctor would you like to book an appointment with?"
                        else:
                            # Final fallback
                            response = "✅ **All Available Doctors:**\n\n"
                            response += "1. Dr. Sarah Johnson - General Medicine - (555) 123-4567\n"
                            response += "2. Dr. Emily Williams - Gynecology - (555) 201-0002\n"
                            response += "3. Dr. Michael Chen - Cardiology - (555) 202-0001\n"
                            response += "4. Dr. Anjali Desai - Neurology - (555) 203-0001\n"
                            response += "5. Dr. Sneha Kapoor - Dermatology - (555) 204-0001\n\n"
                            response += "Would you like to book an appointment with any of these doctors?"
                elif any(word in msg_lower for word in ["find", "doctor", "gynecologist", "gynacologist", "gynec", "gynaec", "obstetric", "specialist", "cardiologist", "neurologist", "dermatologist", "pediatrician", "orthopedic", "psychiatrist", "general physician", "general practitioner", "GP", "family doctor", "help me with", "need a", "is there any", "available doctor", "any doctor"]):
                    # Handle doctor finding queries - ALWAYS get actual doctors from database
                    specialty = None
                    specialty_display_name = "doctor"
                    
                    if "general physician" in msg_lower or "general practitioner" in msg_lower or "GP" in msg_lower or "family doctor" in msg_lower or "primary care" in msg_lower:
                        specialty = "general medicine"
                        specialty_display_name = "general physician"
                    elif "gynecologist" in msg_lower or "gynec" in msg_lower or "obstetric" in msg_lower or "gyanocologist" in msg_lower or "gynaec" in msg_lower:
                        specialty = "gynecology"
                        specialty_display_name = "gynecologist"
                    elif "cardiologist" in msg_lower or "cardiac" in msg_lower or "heart" in msg_lower:
                        specialty = "cardiology"
                        specialty_display_name = "cardiologist"
                    elif "neurologist" in msg_lower or "neurology" in msg_lower or "neuro" in msg_lower:
                        specialty = "neurology"
                        specialty_display_name = "neurologist"
                    elif "dermatologist" in msg_lower or "dermatology" in msg_lower or "skin" in msg_lower:
                        specialty = "dermatology"
                        specialty_display_name = "dermatologist"
                    elif "pediatrician" in msg_lower or "pediatric" in msg_lower or "child" in msg_lower:
                        specialty = "pediatrics"
                        specialty_display_name = "pediatrician"
                    elif "orthopedic" in msg_lower or "orthoped" in msg_lower or "bone" in msg_lower:
                        specialty = "orthopedics"
                        specialty_display_name = "orthopedic surgeon"
                    elif "psychiatrist" in msg_lower or "psychiatry" in msg_lower:
                        specialty = "psychiatry"
                        specialty_display_name = "psychiatrist"
                    
                    # Try to get doctors from database - MULTIPLE ATTEMPTS for reliability
                    doctors = None
                    
                    # Attempt 1: Use RAG retriever if available
                    if rag_retriever and specialty:
                        try:
                            doctors = rag_retriever.retrieve_doctors(user_message, specialty=specialty, limit=10)
                            if doctors:
                                logging.info(f"RAG: Retrieved {len(doctors)} {specialty_display_name}s from database")
                        except Exception as e:
                            logging.debug(f"RAG retrieval failed: {e}")
                    
                    # Attempt 2: Use DatabaseHelper if RAG didn't work
                    if not doctors or len(doctors) == 0:
                        try:
                            doctors = DatabaseHelper.get_doctors(specialty=specialty)
                            if doctors:
                                logging.info(f"DatabaseHelper: Retrieved {len(doctors)} {specialty_display_name}s from database")
                        except Exception as e:
                            logging.debug(f"DatabaseHelper retrieval failed: {e}")
                    
                    # Attempt 3: Try without specialty filter to get all doctors
                    if not doctors or len(doctors) == 0:
                        try:
                            all_doctors = DatabaseHelper.get_doctors()  # Get all doctors
                            if all_doctors and specialty:
                                # Filter by specialty manually
                                doctors = [d for d in all_doctors if specialty.lower() in str(d.get('specialty', '')).lower()]
                                if doctors:
                                    logging.info(f"Manual filter: Found {len(doctors)} {specialty_display_name}s")
                        except Exception as e:
                            logging.debug(f"Manual filtering failed: {e}")
                    
                    # BUILD RESPONSE with database results
                    if doctors and len(doctors) > 0:
                        # SUCCESS: Build detailed response with actual doctors from database
                        response = f"✅ **I found {len(doctors)} {specialty_display_name}{'s' if len(doctors) > 1 else ''} in our database:**\n\n"
                        for i, doc in enumerate(doctors[:5], 1):  # Show first 5
                            response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
                            response += f"   📋 Specialty: {doc.get('specialty', 'General Medicine')}\n"
                            response += f"   🏥 Department: {doc.get('department', 'N/A')}\n"
                            if doc.get('phone'):
                                response += f"   📞 Phone: {doc.get('phone')}\n"
                            if doc.get('email'):
                                response += f"   ✉️ Email: {doc.get('email')}\n"
                            if doc.get('experience_years'):
                                response += f"   👨‍⚕️ Experience: {doc.get('experience_years')} years\n"
                            if doc.get('rating'):
                                response += f"   ⭐ Rating: {doc.get('rating')}/5\n"
                            response += "\n"
                        
                        response += f"📅 **Next Steps:**\n"
                        response += f"• I can help you book an appointment with any of these {specialty_display_name}s\n"
                        response += f"• Just tell me the doctor's name or number (e.g., 'Book with Dr. Smith' or 'I want doctor #1')\n"
                        response += f"• I'll check their availability and schedule your visit!\n\n"
                        response += f"Which {specialty_display_name} would you like to see?"
                        
                        logging.info(f"Successfully showed {len(doctors)} {specialty_display_name}s from database to user")
                    else:
                        # NO DOCTORS FOUND: Provide helpful fallback
                        logging.warning(f"No {specialty_display_name}s found in database for specialty: {specialty}")
                        response = f"I'm currently searching our database for available {specialty_display_name}s. "
                        response += f"While I search, here's what I can help you with:\n\n"
                        response += f"📞 **Immediate Help:**\n"
                        response += f"• Call our appointment line: (555) 123-4567\n"
                        response += f"• Visit our website to see all available {specialty_display_name}s\n\n"
                        response += f"💬 **I can also help you:**\n"
                        response += f"• Describe your symptoms for recommendations\n"
                        response += f"• Check insurance coverage\n"
                        response += f"• See all available doctors\n"
                        response += f"• Book appointments with other specialists\n\n"
                        response += f"Let me know how you'd like to proceed, or I can continue searching for {specialty_display_name}s!"
                # Handle "all plans" query specifically
                elif "all" in msg_lower and "plan" in msg_lower:
                    # Show all insurance plans with details
                    response = """Here are all available insurance plans:

**1. Basic Health Plan**
   Monthly Premium: $150
   Deductible: $1,000
   Coverage: 80%
   Features: Primary care visits, Emergency visits, Basic prescriptions
   Best for: Budget-conscious individuals

**2. Premium Health Plan**
   Monthly Premium: $300
   Deductible: $500
   Coverage: 90%
   Features: All basic features, Specialist visits, Mental health coverage, Dental & Vision
   Best for: Regular medical needs

**3. Family Health Plan**
   Monthly Premium: $450
   Deductible: $750
   Coverage: 85%
   Features: All premium features, Family coverage, Maternity care, Pediatric care
   Best for: Families with children

Would you like more details about any specific plan, or would you like personalized recommendations?"""
                else:
                    # Use intelligent fallback with context (always provides response)
                    response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
        
            # Ensure we have a response - use intelligent fallback with context for ALL queries
            if not response or response.strip() == "":
                # Use intelligent fallback that handles ALL query types with context
                response = IntelligentFallback.get_fallback_response(user_message, conversation_history, retrieved_context)
                
                # Enhance with retrieved context if available
                if retrieved_context:
                    if retrieved_context.get('doctors'):
                        doctors = retrieved_context['doctors']
                        if doctors and len(doctors) > 0:
                            response += f"\n\nI found {len(doctors)} relevant doctor(s) in our system:\n"
                            for i, doc in enumerate(doctors[:3], 1):
                                response += f"{i}. Dr. {doc.get('name', 'N/A')} - {doc.get('specialty', 'General Medicine')}\n"
                            response += "\nWould you like to book an appointment with any of these doctors?"
                    
                    if retrieved_context.get('insurance_plans'):
                        plans = retrieved_context['insurance_plans']
                        if plans and len(plans) > 0:
                            response += f"\n\nI found {len(plans)} insurance plan(s) available. Would you like to see details?"
                    
                    if retrieved_context.get('appointments'):
                        appointments_list = retrieved_context['appointments']
                        if appointments_list and len(appointments_list) > 0:
                            response += f"\n\nYou have {len(appointments_list)} upcoming appointment(s). Would you like to manage them?"
            
                # Final safety check - ensure we ALWAYS have a response
                if not response or response.strip() == "":
                    # Ultimate fallback - provide helpful response based on message
                    msg_lower = user_message.lower()
                    if any(word in msg_lower for word in ["suffering", "sick", "symptom", "pain", "fever", "cold", "cough", "viral", "infection"]):
                        response = "I understand you're not feeling well. I can help you find the right doctor based on your symptoms, book an appointment, or provide general health guidance. What specific symptoms are you experiencing?"
                    elif any(word in msg_lower for word in ["help", "assist", "how can you", "what can you"]):
                        response = "I'm Dr. AI, your healthcare assistant! I can help you with finding doctors, booking appointments, health questions, insurance information, and more. What would you like help with today?"
                    else:
                        response = "I'm here to help with all your healthcare needs - appointments, insurance, health questions, medications, and more. What would you like to know?"
            
            # Save conversation history to database (non-blocking, don't wait)
            # Do this asynchronously - don't block the response
            try:
                # Just try to save, don't wait for it
                DatabaseHelper.save_conversation_history(
                    sender_id, user_message, response,
                    intent=intent,
                    entities=entities
                )
            except Exception:
                pass  # Ignore errors - non-critical
            
            # Send response (only once) - ensure response is not empty
            # Response is guaranteed to be set by this point due to fallback logic above
            if response and response.strip():
                safe_dispatcher.utter_message(text=response)
                logging.info(f"action_aws_bedrock_chat returning response: {response[:100]}...")
                return []  # CRITICAL: Return immediately after sending response
            else:
                # Last resort fallback - provide helpful response based on message
                msg_lower = user_message.lower()
                if any(word in msg_lower for word in ["suffering", "sick", "symptom", "pain", "fever", "cold", "cough", "viral", "infection"]):
                    fallback_response = "I understand you're not feeling well. I can help you find the right doctor based on your symptoms, book an appointment, or provide general health guidance. What specific symptoms are you experiencing?"
                elif any(word in msg_lower for word in ["yes", "sure", "ok", "please"]) and len(msg_lower.strip()) < 10:
                    # Handle "yes" responses intelligently based on conversation context
                    context_lower = " ".join([msg.get("content", "").lower() for msg in conversation_history[-3:]])
                    
                    if "insurance" in context_lower or "plan" in context_lower:
                        # User said yes to insurance plans - show detailed plans
                        fallback_response = """Here are all available insurance plans with details:

**1. Basic Health Plan**
   Monthly Premium: $150
   Deductible: $1,000
   Coverage: 80%
   Features: Primary care visits, Emergency visits, Basic prescriptions
   Best for: Budget-conscious individuals

**2. Premium Health Plan**
   Monthly Premium: $300
   Deductible: $500
   Coverage: 90%
   Features: All basic features, Specialist visits, Mental health coverage, Dental & Vision
   Best for: Regular medical needs

**3. Family Health Plan**
   Monthly Premium: $450
   Deductible: $750
   Coverage: 85%
   Features: All premium features, Family coverage, Maternity care, Pediatric care
   Best for: Families with children

Would you like more details about any specific plan, or would you like personalized recommendations based on your needs?"""
                    elif "doctor" in context_lower or "specialist" in context_lower or "physician" in context_lower:
                        fallback_response = "I can help you find doctors! Let me search for available doctors. What type of doctor or specialty are you looking for? For example, you can say 'general physician', 'gynecologist', 'cardiologist', or 'I need a doctor for [your symptoms]'."
                    elif "appointment" in context_lower or "book" in context_lower or "schedule" in context_lower:
                        fallback_response = "I can help you book an appointment! Please tell me your symptoms or preferred specialty, and I'll find the right doctor and show you available time slots."
                    else:
                        fallback_response = "I'm here to help! Could you please tell me more about what you need? For example:\n• 'I need to find a doctor'\n• 'I want to book an appointment'\n• 'I need help with insurance'\n• 'I have [symptoms]'\n\nWhat can I help you with?"
                elif any(word in msg_lower for word in ["help", "assist", "how can you", "what can you"]):
                    fallback_response = "I'm Dr. AI, your healthcare assistant! I can help you with finding doctors, booking appointments, health questions, insurance information, and more. What would you like help with today?"
                else:
                    fallback_response = "I'm here to help with all your healthcare needs - appointments, insurance, health questions, medications, and more. What would you like to know?"
                
                safe_dispatcher.utter_message(text=fallback_response)
                logging.warning(f"action_aws_bedrock_chat: Response was empty, using fallback: {fallback_response[:50]}...")
                return []  # CRITICAL: Return immediately after sending fallback response
            
            # Final safety - should never reach here, but ensure we return
            return []
            
        except Exception as e:
            # Catch any unhandled exceptions - ALWAYS return a response
            logging.error(f"Critical error in action_aws_bedrock_chat: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            # Provide helpful response even on error
            try:
                user_message = tracker.latest_message.get("text", "") if 'tracker' in locals() else ""
                msg_lower = user_message.lower() if user_message else ""
                
                if any(word in msg_lower for word in ["suffering", "sick", "symptom", "viral", "infection"]):
                    error_response = "I understand you're not feeling well. I can help you find the right doctor, book an appointment, or provide health guidance. What symptoms are you experiencing?"
                elif any(word in msg_lower for word in ["help", "assist", "how can you"]):
                    error_response = "I'm Dr. AI, your healthcare assistant! I can help with finding doctors, booking appointments, health questions, and more. What would you like help with?"
                else:
                    error_response = "Hello! I'm Dr. AI, your healthcare assistant. I can help with appointments, insurance, health questions, and more. How can I assist you today?"
                
                # Always send error response - use safe dispatcher
                try:
                    safe_dispatcher = SafeDispatcher(dispatcher, sender_id, user_message)
                    safe_dispatcher.utter_message(text=error_response)
                except:
                    # Last resort - use regular dispatcher if safe dispatcher fails
                    dispatcher.utter_message(text=error_response)
                logging.info(f"action_aws_bedrock_chat: Error handled, returning fallback response")
                return []
            except Exception as e2:
                logging.error(f"Error in final fallback: {e2}")
                # Last resort - return empty list (Rasa will handle it)
                return []


class ActionDescribeProblem(Action):
    
    def __init__(self):
        self.bedrock_helper = AWSBedrockHelper()
    
    def name(self) -> Text:
        return "action_describe_problem"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        symptom = next(tracker.get_latest_entity_values("symptom"), None)

        # Fetch data from API
        try:
            response = requests.get(f"{REACT_APP_DUMMY_API}/doctors/uniqueSpecialties/get")
            response.raise_for_status()  # Raise an error for HTTP errors
            data = response.json()
            specialties = data.get("specialties", [])
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text=f"Error fetching specialties: {str(e)}")
            return []

        if specialties and symptom:
            specialties_text = ", ".join(specialties[:-1]) + f" and {specialties[-1]}" if len(specialties) > 1 else specialties[0]
            response = self.bedrock_helper.get_response(f"Doctors we have {specialties_text} based on the symptom: {symptom} please select one type of doctor based on the symptom want output in one word.")
            
            dispatcher.utter_message(text=f"Based on your symptoms, I'll connect you with an {response} who focuses on {symptom} issues.")
        else:
            dispatcher.utter_message(text="No specialties available at the moment.")

        return []

class SubmitAppointment(Action):
    def name(self) -> Text:
        return "action_submit_appointment"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot("user_id")
        date = tracker.get_slot("date")
        time = tracker.get_slot("time")

        if not all([user_id,  date, time]):
            dispatcher.utter_message(text="Some details are missing. Please provide all required information.")
            return []

        payload = {
            "userId": "67d01bc7dbd3b74510734fea",
            "doctorId": user_id,
            "date": date,
            "time": time
        }
        
        print(payload )
        
        response = requests.post(f"{REACT_APP_DUMMY_API}/appointments/add", json=payload)

        if response.status_code == 201:
            dispatcher.utter_message(text=f"Your appointment has been booked successfully on {date} at {time}.")
        else:
            dispatcher.utter_message(text="Failed to book your appointment. Please try again.")
            
        return [
            SlotSet("user_id", None),
            SlotSet("date", None),
            SlotSet("time", None)
        ]    
           
# class SubmitRescheduleAppointment(Action):
#     def name(self) -> Text:
#         return "action_submit_reschedule_appointment"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         appointment_id = tracker.get_slot("appointment_id")
#         date = tracker.get_slot("date")
#         time = tracker.get_slot("time")
        
#         print(f"inside action_submit_reschedule_appointment {appointment_id}, {date}, {time}")

#         if not all([appointment_id,  date, time]):
#             dispatcher.utter_message(text="Some details are missing. Please provide all required information.")
#             return []

#         payload = {
#             "date": date,
#             "time": time
#         }
        
        
        
#         response = requests.put(f"{REACT_APP_DUMMY_API}appointments/edit/{appointment_id}", json=payload)

#         if response.status_code == 200:
#             dispatcher.utter_message(text=f"Your appointment has been successfully reschedule on {date} at {time}.")
#         else:
#             dispatcher.utter_message(text="Failed to book your appointment. Please try again.")
            
#         return [
#             SlotSet("appointment_id", None),
#             SlotSet("date", None),
#             SlotSet("time", None)
#         ]


# from rasa_sdk import Action, Tracker, FormValidationAction
# from rasa_sdk.executor import CollectingDispatcher
# from rasa_sdk.events import SlotSet, Form, EventType
# import logging
# from typing import Any, Text, Dict, List
# from rasa_sdk.types import DomainDict
# import random
# from twilio.rest import Client
# import re

# # import psycopg2
# # import json

# import psycopg2
# import psycopg2.pool
# import json

# # Database connection details
# DB_NAME = "hospital"
# DB_USER = "postgres"
# DB_PASSWORD = "qMI8DUYcGnoTBpsyagh9"
# DB_HOST = "hospital.cv8wum284gev.us-east-1.rds.amazonaws.com"  # Change to your DB server IP if remote
# DB_PORT = "5432"  # Default PostgreSQL port


# db_pool = psycopg2.pool.SimpleConnectionPool(
#     minconn=1,
#     maxconn=10,
#     dbname=DB_NAME,
#     user=DB_USER,
#     password=DB_PASSWORD,
#     host=DB_HOST,
#     port=DB_PORT
# )

# otp_store = {}

# TWILIO_ACCOUNT_SID = "AC4f7"
# TWILIO_AUTH_TOKEN = "a5e"
# TWILIO_PHONE_NUMBER = "+16166361988"

# class ActionSubmitAppointment(Action):
#     def name(self) -> str:
#         return "action_submit_appointment"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
#         # Collect slot values
#         print(f"Tracker slots: {tracker.slots}")
#         symptom = tracker.get_slot("symptom")
#         doctor_type = tracker.get_slot("doctor_type")
#         preferred_date_time = tracker.get_slot("preferred_date_time")
#         name = tracker.get_slot("name")
#         age = tracker.get_slot("age")
#         gender = tracker.get_slot("gender")
#         contact_number = tracker.get_slot("contact_number")

#         # Ensure all slots are filled
#         if not all([symptom, doctor_type, preferred_date_time, name, age, gender, contact_number]):
#             dispatcher.utter_message(text="It seems some details are missing. Please provide all the required information.")
#             return []

#         # Confirm the booking
#         confirmation_message = (
#             f"Your appointment has been booked successfully!\n"
#             f"Details:\n"
#             f"- Name: {name}\n"
#             f"- Age: {age}\n"
#             f"- Gender: {gender}\n"
#             f"- Symptoms: {symptom}\n"
#             f"- Doctor Type: {doctor_type}\n"
#             f"- Preferred Date: {preferred_date_time}\n"
#             f"- Contact Number: {contact_number}"
#         )
#         dispatcher.utter_message(text=confirmation_message)
#         return []
    


# def validate_slot_value(slot_name, slot_value):
#     # Define validation logic for different slots
#     if slot_name == "contact_number":
#         # Validate contact number (example: check if it's a 10-digit number)
#         if re.match(r'^\d{10}$', slot_value):
#             return True
#         else:
#             return False
#     elif slot_name == "age":
#         # Validate age (example: check if it's a number and within a reasonable range)
#         print('######## Here')
#         slot_value = int(slot_value)
#         if isinstance(slot_value, (int, float)) and 0 < slot_value < 120:
#             return True
#         else:
#             return False
#     elif slot_name == "symptom":
#         # Validate symptom (example: ensure it's not empty)
#         if slot_value and isinstance(slot_value, str):
#             return True
#         else:
#             return False
#     # Add more slot validations as needed
#     return False


# def send_otp(contact_number: str) -> bool:
#     """Sends an OTP to the provided contact number and returns True if successful, else False."""
#     if not contact_number:
#         print("No contact number provided.")
#         return False

#     # Generate a random 6-digit OTP
#     otp = str(random.randint(100000, 999999))
#     otp_store[contact_number] = otp  # Save the OTP for the contact number
#     print(f"Generated OTP for {contact_number}: {otp}")  # For debugging; remove in production

#     try:
#         # Initialize the Twilio client
#         client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

#         # Send SMS
#         message = client.messages.create(
#             body=f"Your OTP is: {otp}. Please do not share this with anyone.",
#             from_=TWILIO_PHONE_NUMBER,
#             to=contact_number  # Ensure the contact number includes the country code
#         )

#         print(f"OTP sent successfully to {contact_number}. SID: {message.sid}")
#         return True
    
#     except Exception as e:
#         print(f"Failed to send OTP to {contact_number}: {e}")
#         return False


# # Custom action to validate any slot
# class ActionValidateSlot(Action):
#     def name(self) -> str:
#         return "validate_appointment_form"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
#         # Get the filled slot name and value

#         slots = ["contact_number", "age", "gender"]

#         print(f"Tracker slots: {tracker.slots}")
#         symptom = tracker.get_slot("symptom")
#         doctor_type = tracker.get_slot("doctor_type")
#         preferred_date_time = tracker.get_slot("preferred_date_time")
#         name = tracker.get_slot("name")
#         age = tracker.get_slot("age")
#         gender = tracker.get_slot("gender")
#         contact_number = tracker.get_slot("contact_number")
#         provide_otp = tracker.get_slot("provide_otp")
#         requested_slot = tracker.get_slot("requested_slot")

#         #print("########Req slot", requested_slot)
#         otp_store[str(contact_number)] = 11222
#         if contact_number and requested_slot == 'contact_number':
#             slot_name = "contact_number"
#             if validate_slot_value("contact_number", contact_number):
#                 #is_sent =  send_otp("+91"+ str(contact_number))
#                 is_sent = True
                
#                 if is_sent:
#                     dispatcher.utter_message(text=f"An OTP has been sent to your mobile number {contact_number}. Please provide it to continue.")
#                     return [SlotSet(slot_name, contact_number)]
#                 else:
#                     dispatcher.utter_message(text=f"There was an issue sending the OTP. Please try again later.")
#                     return [SlotSet(slot_name, None)]
#             else:
#                 dispatcher.utter_message(text=f"Please provide a valid 10 digit mobile number without country to send the OTP.")
#                 return [SlotSet(slot_name, None)]

#         if provide_otp and contact_number:
#             slot_name = "provide_otp"
#             key = "+91"+contact_number
#             print("################otp_store", otp_store, "key", key)
#             if key in otp_store and str(otp_store[key]) == str(provide_otp) :
#                 #dispatcher.utter_message(text=f"Your OTP has been successfully verified!")
#                 return [SlotSet("verified_otp", True)]

#             else:
#                 dispatcher.utter_message(text=f"The OTP you provided is incorrect. Please provide correct OTP.")
#                 return [SlotSet(slot_name, None)]

        
#         if age:
#             slot_name = "age"
#             print("##########", validate_slot_value("age", age))
#             if validate_slot_value("age", age):
#                 return [SlotSet(slot_name, age)]

#             else:
#                 dispatcher.utter_message(text=f"Invalid age details.")
#                 return [SlotSet(slot_name, None)]
                

        

#         # # Call the validation function
#         # if validate_slot_value(slot_name, slot_value):
#         #     # If valid, return a success message
#         #     dispatcher.utter_message(text=f"The value for {slot_name} is valid.")
#         #     return [SlotSet(slot_name, slot_value)]
#         # else:
#         #     # If not valid, ask the user to re-enter the value
#         #     dispatcher.utter_message(text=f"The value for {slot_name} is invalid. Please enter a valid {slot_name}.")
#         #     return [SlotSet(slot_name, None)]  # Reset the invalid slot to allow the user to re-enter

#         #return [SlotSet(slot_name, slot_value)]


# class ActionAskPreferredDateTime(Action):
#     def name(self):
#         return "action_ask_preferred_date_time"

#     def run(self, dispatcher, tracker, domain):
#         # Fetch available date-time options from the backend
#         try:
#             message = "On which date would you like to book an appointment? Here are some available options:"
#             slot_lst = fetch_from_db("select name, experience, doc_type, date, start_time, end_time from doctors d inner join  availability_slots a on d.doctor_id = a.doctor_id where a.doctor_id =1;")

#         except Exception as e:
#             dispatcher.utter_message(text="Sorry, I couldn't fetch the available date and time slots at the moment.")
#             suggested_times = []

#         # Send the message to the user with the options array
#         dispatcher.utter_message(text=message, json_message={"type": "slot_card", "buttons": slot_lst})
#         return []


# def fetch_from_db(query):
#     conn = None
#     try:
#         conn = db_pool.getconn()
#         cursor = conn.cursor()
#         cursor.execute(query)
#         column_names = [desc[0] for desc in cursor.description]
#         rows = cursor.fetchall()
        
#         # Convert Decimal and other non-serializable types
#         result_list = [dict(zip(column_names, map(str, row))) for row in rows]
        
#         cursor.close()
#         db_pool.putconn(conn)
#         return result_list  # Return as Python object, not JSON string
#     except Exception as e:
#         if conn:
#             db_pool.putconn(conn)
#         return {"error": str(e)}  # Return as a dictionary, not JSON string

# class ActionAskDoctorType(Action):
#     def name(self):
#         return "action_ask_doctor_type"

#     def run(self, dispatcher, tracker, domain):
#         try:
#             doctors_lst = fetch_from_db("SELECT * FROM doctors;")
#             message = "Which type of doctor would you like to consult?"
#         except Exception as e:
#             dispatcher.utter_message(text="Sorry, I couldn't fetch the available doctors at the moment.")
#             return []
        
#         # Pass `doctors_lst` as a Python dictionary
#         dispatcher.utter_message(text=message, json_message={"type": "doc_card", "buttons": doctors_lst})
#         return []



# class ActionPredictDoctor(Action):
#     def name(self):
#         return "action_predict_doctor"

#     def run(self, dispatcher, tracker, domain):
#         symptom = tracker.get_slot("symptom_slot")
#         doctor_mapping = {
#             "severe headache": "Neurologist",
#             "stomach pain": "Gastroenterologist",
#             "fever": "General Physician",
#             "fever and sore throat": "General Physician",
#             "chest pain": "Cardiologist",
#             "coughing": "Pulmonologist",
#             "difficulty breathing": "Pulmonologist",
#             "back pain": "Orthopedist",
#             "knee pain": "Orthopedist",
#             "vomiting": "Gastroenterologist",
#             "dizziness": "Neurologist",
#             "nauseous": "Gastroenterologist",
#             "allergy symptoms": "Allergist",
#         }
        
#         # Predict doctor based on symptom
#         doctor = doctor_mapping.get(symptom.lower(), "General Physician")
        
#         # Respond with prediction
#         dispatcher.utter_message(text=f"You should see a {doctor}.")
        
#         return []
    
# class ActionSendOTP(Action):
#     def name(self) -> Text:
#         return "action_send_otp"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#             contact_number = tracker.get_slot("contact_number")
#             print("############## contact_number called", contact_number)
#             if not contact_number:
#                 dispatcher.utter_message(text="Please provide a valid contact number to send the OTP.")
#                 return []
            
#             # Check if the contact number is numeric and exactly 10 digits
#             if not contact_number.isdigit() or len(contact_number) != 10:
#                 dispatcher.utter_message(text="Please provide a valid 10-digit contact number.")
#                 return []

#             # Generate a random 6-digit OTP
#             otp = str(random.randint(100000, 999999))
#             otp_store[contact_number] = otp  # Save the OTP for the contact number
#             print(f"OTP for {contact_number}: {otp}")  # For debugging; remove in production

#             try:
#                 # Initialize the Twilio client
#                 client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

#                 # Send SMS
#                 message = client.messages.create(
#                     body=f"Your OTP is: {otp}. Please do not share this with anyone. validate",
#                     from_=TWILIO_PHONE_NUMBER,
#                     to=f"+919785948208"  # Ensure the contact number includes the country code
#                 )

#                 print(f"OTP sent successfully to {contact_number}. SID: {message.sid}")

#                 dispatcher.utter_message(
#                     text=f"An OTP has been sent to your number {contact_number}. Please provide it to continue."
#                 )
#             except Exception as e:
#                 print(f"Failed to send OTP to {contact_number}: {e}")
#                 dispatcher.utter_message(
#                     text="There was an issue sending the OTP. Please try again later."
#                 )

#             return []



# class ActionVerifyOtp(Action):
#     def name(self):
#         return "action_verify_otp"

#     def run(self, dispatcher, tracker, domain):
#         user_otp = tracker.get_slot("provide_otp")
#         correct_otp = "1234"  # Replace with your logic to verify OTP
        
#         if user_otp == correct_otp:
#             dispatcher.utter_message(text="OTP verified successfully.")
#             return [SlotSet("provide_otp", "verified")]
#         else:
#             dispatcher.utter_message(text="Invalid OTP. Please try again.")
#             return [SlotSet("provide_otp", None)]

# class ActionResendOTP(Action):
#     def name(self) -> Text:
#         return "action_resend_otp"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         contact_number = tracker.get_slot("contact_number")
#         if not contact_number:
#             dispatcher.utter_message(text="Please provide a valid contact number to resend the OTP.")
#             return []

#         # Resend the OTP
#         otp = str(random.randint(100000, 999999))
#         otp_store[contact_number] = otp  # Update the OTP for the contact number
#         print(f"Resent OTP for {contact_number}: {otp}")  # For debugging; remove in production

#         dispatcher.utter_message(
#             text=f"A new OTP has been sent to your number {contact_number}. Please provide it to continue."
#         )
#         return []
    
class ActionDefaultFallback(Action):
    """Default fallback action that uses AWS Bedrock for intelligent responses"""
    
    def __init__(self):
        self.bedrock_helper = AWSBedrockHelper()
    
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Get the last user message
        user_message = tracker.latest_message.get("text", "")
        
        # Get detected intent for context
        intent = tracker.latest_message.get("intent", {}).get("name", "")
        entities = tracker.latest_message.get("entities", [])
        
        # Build enhanced message
        enhanced_message = user_message if user_message else "I need help with a healthcare question."
        if intent:
            enhanced_message += f"\n[User intent: {intent}]"
        if entities:
            entity_info = ", ".join([f"{e.get('entity')}: {e.get('value')}" for e in entities])
            enhanced_message += f"\n[Detected: {entity_info}]"
        
        # Build conversation history
        conversation_history = []
        for event in tracker.events[-10:]:
            if event.get("event") == "user":
                conversation_history.append({
                    "role": "user",
                    "content": event.get("text", "")
                })
            elif event.get("event") == "bot":
                conversation_history.append({
                    "role": "assistant",
                    "content": event.get("text", "")
                })
        
        # Use AWS Bedrock for intelligent response
        try:
            response = self.bedrock_helper.get_response(enhanced_message, conversation_history)
            
            # Check if response is an error message
            if response and response.strip():
                error_indicators = [
                    "trouble connecting to my AI brain",
                    "AWS credentials are configured",
                    "configuration issue",
                    "encountered a technical issue"
                ]
                is_error_response = any(indicator in response for indicator in error_indicators)
                if is_error_response:
                    response = None  # Use fallback instead
        except Exception as e:
            logging.debug(f"Bedrock failed in default fallback: {e}")
            response = None
        
        if not response or response.strip() == "":
            # Provide helpful fallback based on user message
            msg_lower = user_message.lower()
            
            if "insurance" in msg_lower:
                response = "I can help with insurance! We offer various plans and can verify coverage. What would you like to know?"
            elif "appointment" in msg_lower or "book" in msg_lower or "schedule" in msg_lower:
                response = "I can help you book appointments! I can find doctors and schedule visits. Would you like to proceed?"
            elif any(word in msg_lower for word in ["suffering", "sick", "symptom", "pain", "fever", "cold", "cough", "viral", "infection", "unwell", "not feeling well"]):
                response = "I understand you're not feeling well. I can help you find the right doctor based on your symptoms, book an appointment, or provide general health guidance. What symptoms are you experiencing?"
            elif any(word in msg_lower for word in ["help", "assist", "how can you", "what can you", "capabilities", "services"]):
                response = "I'm Dr. AI, your healthcare assistant! I can help you with:\n\n• Finding doctors and specialists\n• Booking appointments\n• Health questions and symptom assessment\n• Insurance information and plans\n• Medication reminders\n• Lab results and medical records\n• And much more!\n\nWhat would you like help with today?"
            elif "health" in msg_lower or "medical" in msg_lower:
                response = "I can help with health questions! I can assist with symptom assessment, finding doctors, booking appointments, and more. What do you need?"
            elif "doctor" in msg_lower:
                response = "I can help you find doctors! I can search by specialty, show available doctors, and help you book appointments. What type of doctor are you looking for?"
            else:
                response = "I'm here to help with all your healthcare needs - appointments, insurance, health questions, medications, and more. What would you like to know?"
        
        dispatcher.utter_message(text=response)
        return []
    
    
# class ActionRestartForm(Action):
#     def name(self) -> Text:
#         return "action_restart"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:
#         # Reset the slots
#         slots_to_reset = [
#             "symptom","contact_number" ,"doctor_type", "preferred_date_time", "name", "age", "gender"
#         ]
        
#         # Reset each slot
#         events = [SlotSet(slot, None) for slot in slots_to_reset]
        
#         # Restart the form
#         events.append(Form("appointment_form"))
        
#         dispatcher.utter_message(text="Let's start over. Please provide your details again.")
#         return events


class ActionInsuranceInfo(Action):
    def name(self) -> Text:
        return "action_insurance_info"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock insurance information - in real implementation, fetch from database
        insurance_info = {
            "provider": "HealthCare Plus",
            "policy_number": "HCP-2024-001",
            "coverage_type": "Comprehensive",
            "deductible": "$500",
            "co_pay": "$25",
            "expiry_date": "2024-12-31",
            "benefits": [
                "Primary care visits: 100% covered",
                "Specialist visits: 80% covered", 
                "Emergency room: 90% covered",
                "Prescription drugs: 70% covered"
            ]
        }
        
        message = f"""Your Insurance Information:
        
Provider: {insurance_info['provider']}
Policy Number: {insurance_info['policy_number']}
Coverage Type: {insurance_info['coverage_type']}
Deductible: {insurance_info['deductible']}
Co-pay: {insurance_info['co_pay']}
Expiry Date: {insurance_info['expiry_date']}

Benefits:
{chr(10).join([f"• {benefit}" for benefit in insurance_info['benefits']])}"""
        
        dispatcher.utter_message(text=message)
        return []


class ActionInsurancePlans(Action):
    def name(self) -> Text:
        return "action_insurance_plans"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get insurance plans from database
        insurance_plans = DatabaseHelper.get_insurance_plans()
        
        # Fallback to default plans if database doesn't have them
        if not insurance_plans:
            insurance_plans = [
            {
                "name": "Basic Health Plan",
                "monthly_premium": "$150",
                "deductible": "$1000",
                "coverage": "80%",
                "features": ["Primary care", "Emergency visits", "Basic prescriptions"]
            },
            {
                "name": "Premium Health Plan", 
                "monthly_premium": "$300",
                "deductible": "$500",
                "coverage": "90%",
                "features": ["All basic features", "Specialist visits", "Mental health", "Dental & Vision"]
            },
            {
                "name": "Family Health Plan",
                "monthly_premium": "$450", 
                "deductible": "$750",
                "coverage": "85%",
                "features": ["All premium features", "Family coverage", "Maternity care", "Pediatric care"]
            }
        ]
        
        # Build detailed message
        message = " **Available Insurance Plans:**\n\n"
        for i, plan in enumerate(insurance_plans, 1):
            message += f"**{i}. {plan['name']}**\n"
            message += f"    Monthly Premium: {plan['monthly_premium']}\n"
            message += f"    Deductible: {plan['deductible']}\n"
            message += f"    Coverage: {plan['coverage']}\n"
            features = plan.get('features', [])
            if isinstance(features, list):
                message += f"    Features: {', '.join(features)}\n"
            message += "\n"
        
        message += " **Next Steps:**\n"
        message += "• Would you like detailed information about any specific plan?\n"
        message += "• I can provide personalized recommendations based on your needs\n"
        message += "• I can help you compare plans side-by-side\n"
        message += "• I can assist with enrollment or questions about coverage\n\n"
        message += "What would you like to know more about?"
        
        # Save conversation history
        sender_id = tracker.sender_id
        user_message = tracker.latest_message.get("text", "")
        DatabaseHelper.save_conversation_history(
            sender_id, user_message, message, 
            intent=tracker.latest_message.get("intent", {}).get("name"),
            entities=tracker.latest_message.get("entities", [])
        )
        
        dispatcher.utter_message(text=message)
        return []


class ActionInsuranceSuggestions(Action):
    def name(self) -> Text:
        return "action_insurance_suggestions"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock suggestions based on user profile - in real implementation, use AI/ML
        # Build as single message to avoid splitting
        suggestions = "Based on your profile, here are my insurance recommendations:\n\n"
        suggestions += " **Recommended Plan: Premium Health Plan**\n"
        suggestions += "- Best for: Regular medical needs\n"
        suggestions += "- Monthly Cost: $300\n"
        suggestions += "- Why: Covers 90% of costs with low deductible\n\n"
        suggestions += "💊 **Alternative: Basic Health Plan**\n"
        suggestions += "- Best for: Budget-conscious users\n"
        suggestions += "- Monthly Cost: $150\n"
        suggestions += "- Why: Good coverage for essential services\n\n"
        suggestions += " **Family Option: Family Health Plan**\n"
        suggestions += "- Best for: Families with children\n"
        suggestions += "- Monthly Cost: $450\n"
        suggestions += "- Why: Comprehensive family coverage\n\n"
        suggestions += " **Tips:**\n"
        suggestions += "- Consider your monthly medical expenses\n"
        suggestions += "- Check if your preferred doctors are in-network\n"
        suggestions += "- Review prescription drug coverage\n"
        suggestions += "- Look for wellness program benefits\n\n"
        suggestions += "Would you like more details about any of these plans?"
        
        # Save conversation history
        sender_id = tracker.sender_id
        user_message = tracker.latest_message.get("text", "")
        DatabaseHelper.save_conversation_history(
            sender_id, user_message, suggestions,
            intent=tracker.latest_message.get("intent", {}).get("name"),
            entities=tracker.latest_message.get("entities", [])
        )
        
        dispatcher.utter_message(text=suggestions)
        return []


class ActionDoctorsList(Action):
    def name(self) -> Text:
        return "action_doctors_list"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get specialty from user message or entities
        user_message = tracker.latest_message.get("text", "").lower()
        specialty = None
        
        # Detect specialty from message
        if "gynecologist" in user_message or "gynec" in user_message or "obstetric" in user_message:
            specialty = "gynecology"
        elif "cardiologist" in user_message or "cardiac" in user_message:
            specialty = "cardiology"
        elif "neurologist" in user_message or "neurology" in user_message:
            specialty = "neurology"
        elif "dermatologist" in user_message or "dermatology" in user_message:
            specialty = "dermatology"
        elif "pediatrician" in user_message or "pediatric" in user_message:
            specialty = "pediatrics"
        elif "orthopedic" in user_message or "orthoped" in user_message:
            specialty = "orthopedics"
        elif "psychiatrist" in user_message or "psychiatry" in user_message:
            specialty = "psychiatry"
        
        # Try database first (faster and more reliable)
        doctors = None
        try:
            doctors = DatabaseHelper.get_doctors(specialty=specialty)
        except Exception as e:
            logging.debug(f"Database query failed, trying API: {e}")
        
        # Fallback to API if database doesn't have doctors
        if not doctors or len(doctors) == 0:
            try:
                response = requests.get(f"{REACT_APP_DUMMY_API}/doctors/all", timeout=5)
                response.raise_for_status()
                api_doctors = response.json()
            
                if api_doctors:
                    # Filter by specialty if specified
                    if specialty:
                        api_doctors = [d for d in api_doctors if specialty.lower() in d.get('specialty', '').lower()]
                    
                    doctors = [{
                        'name': d.get('name', 'N/A'),
                        'specialty': d.get('specialty', 'General Medicine'),
                        'department': d.get('department', d.get('specialty', 'General Medicine')),
                        'phone': d.get('phone', 'N/A'),
                        'email': d.get('email', 'N/A')
                    } for d in api_doctors[:10]]
            except requests.exceptions.RequestException as e:
                logging.debug(f"API call failed: {e}")
        
        # Build response message
        if doctors and len(doctors) > 0:
            specialty_name = specialty.replace('_', ' ').title() if specialty else "doctor"
            message = f" **Available {specialty_name.title()}s:**\n\n"
            for i, doctor in enumerate(doctors[:5], 1):  # Show first 5
                message += f"**{i}. Dr. {doctor.get('name', 'N/A')}**\n"
                message += f"    Specialty: {doctor.get('specialty', 'General Medicine')}\n"
                message += f"    Department: {doctor.get('department', 'N/A')}\n"
                if doctor.get('phone') and doctor.get('phone') != 'N/A':
                    message += f"    Phone: {doctor.get('phone')}\n"
                if doctor.get('email') and doctor.get('email') != 'N/A':
                    message += f"   📧 Email: {doctor.get('email')}\n"
                message += "\n"
            message += " **Next Steps:**\n"
            message += "• Would you like to book an appointment with any of these doctors?\n"
            message += "• I can help you check their availability\n"
            message += "• I can assist with scheduling\n\n"
            message += "Which doctor would you like to book an appointment with?"
        else:
            specialty_name = specialty.replace('_', ' ').title() if specialty else "doctor"
            message = f"I'm searching for available {specialty_name}s. Let me check our database and get back to you with available options. In the meantime, you can also call our appointment line at (555) 123-4567 or visit our website to see all available doctors."
        
        # Save conversation history
        sender_id = tracker.sender_id
        DatabaseHelper.save_conversation_history(
            sender_id, user_message, message,
            intent=tracker.latest_message.get("intent", {}).get("name"),
            entities=tracker.latest_message.get("entities", [])
        )
        
        dispatcher.utter_message(text=message)
        return []


class ActionNearbyHospitals(Action):
    def name(self) -> Text:
        return "action_nearby_hospitals"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock nearby hospitals - in real implementation, use location services
        hospitals = [
            {
                "name": "City General Hospital",
                "address": "123 Main Street, Downtown",
                "distance": "0.5 miles",
                "rating": "4.8/5",
                "services": ["Emergency", "Surgery", "Cardiology", "Pediatrics"],
                "phone": "(555) 123-4567"
            },
            {
                "name": "Metro Medical Center", 
                "address": "456 Health Avenue, Midtown",
                "distance": "1.2 miles",
                "rating": "4.6/5",
                "services": ["Emergency", "Orthopedics", "Neurology", "Oncology"],
                "phone": "(555) 987-6543"
            },
            {
                "name": "Community Health Clinic",
                "address": "789 Care Boulevard, Uptown", 
                "distance": "2.1 miles",
                "rating": "4.4/5",
                "services": ["Primary Care", "Dental", "Mental Health", "Physical Therapy"],
                "phone": "(555) 456-7890"
            }
        ]
        
        message = " Nearby Hospitals:\n\n"
        for i, hospital in enumerate(hospitals, 1):
            message += f"{i}. {hospital['name']}\n"
            message += f"   📍 Address: {hospital['address']}\n"
            message += f"   📏 Distance: {hospital['distance']}\n"
            message += f"   ⭐ Rating: {hospital['rating']}\n"
            message += f"    Services: {', '.join(hospital['services'])}\n"
            message += f"    Phone: {hospital['phone']}\n\n"
        
        message += " Tip: Call ahead to check availability and book appointments."
        
        dispatcher.utter_message(text=message)
        return []


class ActionWhatsAppReminder(Action):
    def name(self) -> Text:
        return "action_whatsapp_reminder"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock WhatsApp reminder - in real implementation, integrate with WhatsApp API
        message = """ WhatsApp Reminder Setup:

 I'll send you a WhatsApp reminder for your appointment!

Reminder Schedule:
- 24 hours before appointment
- 2 hours before appointment  
- 30 minutes before appointment

 To enable WhatsApp reminders:
1. Please provide your WhatsApp number
2. Confirm you want to receive reminders
3. I'll send you a test message

 Note: WhatsApp reminders are currently in development. 
For now, you can:
- Set up email reminders
- Use calendar notifications
- Call our office for confirmations

Would you like to set up email reminders instead?"""
        
        dispatcher.utter_message(text=message)
        return []


class ActionCountryServices(Action):
    def name(self) -> Text:
        return "action_country_services"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get location from user input or slot
        location = next(tracker.get_latest_entity_values("location"), None)
        country = next(tracker.get_latest_entity_values("country"), None)
        
        user_location = location or country or "your area"
        
        # Country-specific services mapping
        country_services = {
            "usa": {
                "name": "United States",
                "services": [
                    "Emergency Services: 911",
                    "Health Insurance: Medicare/Medicaid",
                    "Pharmacy: CVS, Walgreens, Rite Aid",
                    "Telemedicine: Available 24/7",
                    "Mental Health: Crisis hotline 988"
                ],
                "hospitals": "Major hospital chains available",
                "insurance": "Multiple insurance providers"
            },
            "india": {
                "name": "India", 
                "services": [
                    "Emergency Services: 108",
                    "Health Insurance: Ayushman Bharat",
                    "Pharmacy: Apollo, MedPlus, Netmeds",
                    "Telemedicine: Practo, 1mg",
                    "Mental Health: Vandrevala Foundation"
                ],
                "hospitals": "Apollo, Fortis, Max Healthcare",
                "insurance": "Government and private insurance"
            },
            "uk": {
                "name": "United Kingdom",
                "services": [
                    "Emergency Services: 999",
                    "Health Insurance: NHS",
                    "Pharmacy: Boots, Lloyds Pharmacy",
                    "Telemedicine: NHS 111",
                    "Mental Health: Samaritans"
                ],
                "hospitals": "NHS hospitals and private clinics",
                "insurance": "NHS and private insurance"
            },
            "canada": {
                "name": "Canada",
                "services": [
                    "Emergency Services: 911",
                    "Health Insurance: Provincial health plans",
                    "Pharmacy: Shoppers Drug Mart, Rexall",
                    "Telemedicine: Maple, Teladoc",
                    "Mental Health: Crisis helplines"
                ],
                "hospitals": "Public and private hospitals",
                "insurance": "Provincial and private insurance"
            }
        }
        
        # Default services if country not found
        default_services = {
            "name": "International",
            "services": [
                "Emergency Services: Local emergency number",
                "Health Insurance: Check local providers",
                "Pharmacy: Local pharmacies available",
                "Telemedicine: Online consultation services",
                "Mental Health: Local crisis support"
            ],
            "hospitals": "Local hospitals and clinics",
            "insurance": "Local insurance providers"
        }
        
        # Determine country from location
        country_key = "international"
        if user_location:
            location_lower = user_location.lower()
            for key in country_services:
                if key in location_lower or any(word in location_lower for word in country_services[key]["name"].lower().split()):
                    country_key = key
                    break
        
        services = country_services.get(country_key, default_services)
        
        message = f"""🌍 Services Available in {services['name']}:

 **Healthcare Services:**
{chr(10).join([f"• {service}" for service in services['services']])}

 **Hospitals:** {services['hospitals']}
**Insurance:** {services['insurance']}

 **Tips:**
• Emergency services are available 24/7
• Check with your insurance provider for coverage
• Telemedicine options are available for non-emergency consultations
• Keep emergency numbers saved in your phone

Would you like more specific information about any of these services?"""
        
        dispatcher.utter_message(text=message)
        return []


class ActionHealthPredictions(Action):
    def name(self) -> Text:
        return "action_health_predictions"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock health predictions based on user data - in real implementation, use ML models
        predictions = {
            "risk_factors": [
                "Blood pressure trending upward",
                "Sleep quality declining",
                "Stress levels increasing"
            ],
            "recommendations": [
                "Schedule regular check-ups",
                "Improve sleep hygiene",
                "Consider stress management techniques"
            ],
            "health_score": 78,
            "trends": [
                "Weight: Stable",
                "Blood Sugar: Slightly elevated",
                "Heart Rate: Normal range"
            ]
        }
        
        message = f"""🔮 **Your Personalized Health Predictions:**

 **Health Score:** {predictions['health_score']}/100

 **Risk Factors Identified:**
{chr(10).join([f"• {factor}" for factor in predictions['risk_factors']])}

📈 **Health Trends:**
{chr(10).join([f"• {trend}" for trend in predictions['trends']])}

 **AI Recommendations:**
{chr(10).join([f"• {rec}" for rec in predictions['recommendations']])}

 **Next Steps:**
• Monitor your health metrics regularly
• Follow up with your doctor about concerning trends
• Implement lifestyle changes gradually
• Track your progress over time

*Note: These predictions are based on available data and should not replace professional medical advice.*"""
        
        dispatcher.utter_message(text=message)
        return []


class ActionHealthRecommendations(Action):
    def name(self) -> Text:
        return "action_health_recommendations"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock personalized recommendations - in real implementation, use user profile data
        recommendations = {
            "diet": [
                "Increase fiber intake",
                "Reduce sodium consumption",
                "Add more leafy greens"
            ],
            "exercise": [
                "30 minutes of cardio daily",
                "Strength training 2x per week",
                "Walking breaks every 2 hours"
            ],
            "lifestyle": [
                "Improve sleep schedule",
                "Practice stress management",
                "Stay hydrated (8 glasses/day)"
            ],
            "monitoring": [
                "Check blood pressure weekly",
                "Track sleep patterns",
                "Monitor stress levels"
            ]
        }
        
        message = f""" **Your Personalized Health Recommendations:**

🥗 **Diet & Nutrition:**
{chr(10).join([f"• {rec}" for rec in recommendations['diet']])}

 **Exercise & Fitness:**
{chr(10).join([f"• {rec}" for rec in recommendations['exercise']])}

**Lifestyle Changes:**
{chr(10).join([f"• {rec}" for rec in recommendations['lifestyle']])}

 **Health Monitoring:**
{chr(10).join([f"• {rec}" for rec in recommendations['monitoring']])}

 **Smart Tips:**
• Set realistic goals and track progress
• Make one change at a time for better success
• Celebrate small victories along the way
• Consult your doctor before major changes

 **Your Action Plan:**
1. Start with the easiest recommendations
2. Set weekly goals
3. Track your progress
4. Adjust based on results

*Remember: These are general recommendations. Always consult with your healthcare provider for personalized medical advice.*"""
        
        dispatcher.utter_message(text=message)
        return []


class ActionPatientRegistration(Action):
    def name(self) -> Text:
        return "action_patient_registration"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get patient information from slots
        name = tracker.get_slot("name")
        age = tracker.get_slot("age")
        gender = tracker.get_slot("gender")
        phone = tracker.get_slot("phone")
        email = tracker.get_slot("email")
        emergency_contact = tracker.get_slot("emergency_contact")
        
        if not all([name, age, gender, phone, email, emergency_contact]):
            dispatcher.utter_message(text="Please provide all required information to complete registration.")
            return []
        
        # Mock patient registration - in real implementation, save to database
        patient_id = f"PAT_{hash(name + phone) % 100000:05d}"
        
        message = f""" **Registration Complete!**

**Patient ID:** {patient_id}
**Name:** {name}
**Age:** {age}
**Gender:** {gender}
**Phone:** {phone}
**Email:** {email}
**Emergency Contact:** {emergency_contact}

🎉 Welcome to our healthcare system! You can now:
• Book appointments
• Access your medical records
• Get health recommendations
• Receive medication reminders
• Use all our healthcare services

Your patient ID is: **{patient_id}** - Please save this for future reference."""
        
        dispatcher.utter_message(text=message)
        return []


class ActionEmergencyDetection(Action):
    def name(self) -> Text:
        return "action_emergency_detection"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Emergency keywords detection
        emergency_keywords = [
            "heart attack", "stroke", "chest pain", "difficulty breathing",
            "severe bleeding", "unconscious", "seizure", "severe allergic reaction",
            "suicide", "self harm", "overdose", "severe burn", "broken bone",
            "severe headache", "vision loss", "paralysis", "severe abdominal pain"
        ]
        
        user_message = tracker.latest_message.get("text", "").lower()
        
        is_emergency = any(keyword in user_message for keyword in emergency_keywords)
        
        if is_emergency:
            message = """🚨 **EMERGENCY DETECTED!**

**IMMEDIATE ACTION REQUIRED:**
• Call 911 (Emergency Services) immediately
• Go to the nearest emergency room
• If you're alone, call someone for help

**Emergency Numbers:**
• 911 - Emergency Services
• 988 - Suicide & Crisis Lifeline
• Poison Control: 1-800-222-1222

**While waiting for help:**
• Stay calm and breathe slowly
• Don't move if you suspect injury
• Keep emergency contacts informed
• Follow any first aid instructions given

 **This is not a substitute for emergency medical care!**"""
        else:
            message = "I understand you're concerned. Let me help assess your symptoms to determine the best course of action."
        
        dispatcher.utter_message(text=message)
        return []


class ActionSymptomAssessment(Action):
    def name(self) -> Text:
        return "action_symptom_assessment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        symptom = tracker.get_slot("symptom")
        duration = tracker.get_slot("duration")
        severity = tracker.get_slot("severity")
        
        # AI-powered symptom assessment
        assessment = self.assess_symptoms(symptom, duration, severity)
        
        message = f""" **Symptom Assessment Results:**

**Primary Symptom:** {symptom}
**Duration:** {duration}
**Severity:** {severity}/10

**Assessment:** {assessment['diagnosis']}
**Urgency Level:** {assessment['urgency']}
**Recommendation:** {assessment['recommendation']}

**Next Steps:**
{chr(10).join([f"• {step}" for step in assessment['next_steps']])}

**When to Seek Immediate Care:**
{chr(10).join([f"• {warning}" for warning in assessment['warnings']])}

*Note: This is a preliminary assessment. Always consult with a healthcare professional for proper diagnosis.*"""
        
        dispatcher.utter_message(text=message)
        return []
    
    def assess_symptoms(self, symptom, duration, severity):
        # Mock AI assessment - in real implementation, use ML models
        if "chest pain" in symptom.lower():
            return {
                "diagnosis": "Possible cardiac issue",
                "urgency": "HIGH",
                "recommendation": "Seek immediate medical attention",
                "next_steps": ["Call 911 if severe", "Go to ER if moderate", "See doctor within 24 hours"],
                "warnings": ["Chest pain with shortness of breath", "Pain radiating to arm/jaw", "Nausea or sweating"]
            }
        elif "fever" in symptom.lower():
            return {
                "diagnosis": "Possible infection",
                "urgency": "MEDIUM",
                "recommendation": "Monitor and seek care if worsening",
                "next_steps": ["Rest and stay hydrated", "Take temperature regularly", "See doctor if fever persists"],
                "warnings": ["Fever above 103°F", "Difficulty breathing", "Severe headache"]
            }
        else:
            return {
                "diagnosis": "General symptoms",
                "urgency": "LOW",
                "recommendation": "Monitor symptoms and seek care if needed",
                "next_steps": ["Rest and self-care", "Monitor for changes", "See doctor if symptoms worsen"],
                "warnings": ["Symptoms worsen", "New symptoms appear", "No improvement in 3 days"]
            }


class ActionMedicationManagement(Action):
    def name(self) -> Text:
        return "action_medication_management"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock medication management
        medications = [
            {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "next_dose": "8:00 AM"},
            {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "next_dose": "12:00 PM"},
            {"name": "Atorvastatin", "dosage": "20mg", "frequency": "Once daily", "next_dose": "8:00 PM"}
        ]
        
        message = f"""💊 **Medication Management**

**Current Medications:**
{chr(10).join([f"• {med['name']} - {med['dosage']} ({med['frequency']}) - Next: {med['next_dose']}" for med in medications])}

**Today's Schedule:**
• 8:00 AM - Lisinopril 10mg
• 12:00 PM - Metformin 500mg  
• 8:00 PM - Atorvastatin 20mg

**Reminders:**
• Take with food if needed
• Don't skip doses
• Report any side effects
• Keep medications in original containers

**Refill Reminders:**
• Lisinopril: 5 days remaining
• Metformin: 10 days remaining
• Atorvastatin: 15 days remaining

Would you like to:
• Set up medication reminders
• Check for drug interactions
• Request refills
• Report side effects"""
        
        dispatcher.utter_message(text=message)
        return []


class ActionMentalHealthScreening(Action):
    def name(self) -> Text:
        return "action_mental_health_screening"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock mental health screening
        screening_questions = [
            "How would you rate your mood today? (1-10)",
            "Have you been feeling anxious or worried lately?",
            "How is your sleep quality?",
            "Have you lost interest in activities you used to enjoy?",
            "Do you feel hopeless or helpless?"
        ]
        
        message = f"""🧠 **Mental Health Screening**

**Quick Assessment Questions:**
{chr(10).join([f"• {q}" for q in screening_questions])}

**Mental Health Resources:**
• **Crisis Hotline:** 988 (24/7)
• **Text Support:** Text HOME to 741741
• **Online Therapy:** BetterHelp, Talkspace
• **Support Groups:** NAMI, Mental Health America

**Self-Care Tips:**
• Practice deep breathing
• Maintain regular sleep schedule
• Stay connected with loved ones
• Exercise regularly
• Limit alcohol and caffeine

**Warning Signs to Watch:**
• Persistent sadness or anxiety
• Changes in sleep or appetite
• Loss of interest in activities
• Thoughts of self-harm
• Difficulty concentrating

**If you're in crisis:**
• Call 988 immediately
• Go to nearest emergency room
• Contact a mental health professional

Remember: It's okay to ask for help. Mental health is just as important as physical health."""
        
        dispatcher.utter_message(text=message)
        return []


class ActionHealthEducation(Action):
    def name(self) -> Text:
        return "action_health_education"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Mock health education content
        education_topics = {
            "prevention": [
                "Wash hands frequently",
                "Get regular exercise",
                "Eat a balanced diet",
                "Get adequate sleep",
                "Manage stress"
            ],
            "screening": [
                "Annual physical exams",
                "Blood pressure monitoring",
                "Cholesterol checks",
                "Cancer screenings",
                "Vision and dental exams"
            ],
            "lifestyle": [
                "Quit smoking",
                "Limit alcohol consumption",
                "Stay hydrated",
                "Practice safe sex",
                "Wear sunscreen"
            ]
        }
        
        message = f"""📚 **Health Education & Wellness**

**Prevention Tips:**
{chr(10).join([f"• {tip}" for tip in education_topics['prevention']])}

**Important Screenings:**
{chr(10).join([f"• {screening}" for screening in education_topics['screening']])}

**Healthy Lifestyle:**
{chr(10).join([f"• {lifestyle}" for lifestyle in education_topics['lifestyle']])}

**Health Topics:**
• Heart Health
• Diabetes Prevention
• Mental Wellness
• Nutrition Guidelines
• Exercise Programs
• Stress Management

**Educational Resources:**
• CDC Health Guidelines
• WHO Health Information
• Mayo Clinic Health Library
• WebMD Health Topics
• Healthline Articles

Would you like information about any specific health topic?"""
        
        dispatcher.utter_message(text=message)
        return []

