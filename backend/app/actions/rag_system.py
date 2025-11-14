"""
RAG (Retrieval-Augmented Generation) System for Intelligent Healthcare Bot
Retrieves relevant context from database and APIs to generate intelligent responses
"""

import logging
import psycopg2
from typing import List, Dict, Text, Any, Optional
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('AURORA_ENDPOINT') or os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

class RAGRetriever:
    """Retrieval component of RAG system - fetches relevant context from database"""
    
    @staticmethod
    def get_connection():
        """Get database connection"""
        if not DB_CONFIG.get('host') or not DB_CONFIG.get('password'):
            logger.warning("Database configuration incomplete")
            return None
        
        try:
            config = DB_CONFIG.copy()
            config['connect_timeout'] = 5
            return psycopg2.connect(**config)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    @staticmethod
    def retrieve_doctors(query: str, specialty: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """Retrieve relevant doctors based on query"""
        conn = RAGRetriever.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout = '3s'")
            
            if specialty:
                query_sql = """
                    SELECT doctor_id, name, specialty, department, email, phone, experience_years, rating
                    FROM doctors
                    WHERE LOWER(specialty) LIKE LOWER(%s) OR LOWER(department) LIKE LOWER(%s)
                    LIMIT %s
                """
                cursor.execute(query_sql, (f'%{specialty}%', f'%{specialty}%', limit))
            else:
                query_sql = """
                    SELECT doctor_id, name, specialty, department, email, phone, experience_years, rating
                    FROM doctors
                    WHERE LOWER(name) LIKE LOWER(%s) OR LOWER(specialty) LIKE LOWER(%s) OR LOWER(department) LIKE LOWER(%s)
                    LIMIT %s
                """
                search_term = f'%{query}%'
                cursor.execute(query_sql, (search_term, search_term, search_term, limit))
            
            results = cursor.fetchall()
            doctors = []
            for row in results:
                doctors.append({
                    'doctor_id': row[0],
                    'name': row[1],
                    'specialty': row[2],
                    'department': row[3],
                    'email': row[4],
                    'phone': row[5],
                    'experience_years': row[6],
                    'rating': row[7] if len(row) > 7 else None
                })
            
            cursor.close()
            conn.close()
            return doctors
        except Exception as e:
            logger.error(f"Error retrieving doctors: {e}")
            try:
                conn.close()
            except:
                pass
            return []
    
    @staticmethod
    def retrieve_patients(query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant patient records based on query"""
        conn = RAGRetriever.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout = '3s'")
            
            query_sql = """
                SELECT patient_id, name, age, gender, medical_history
                FROM patients
                WHERE LOWER(name) LIKE LOWER(%s)
                LIMIT %s
            """
            search_term = f'%{query}%'
            cursor.execute(query_sql, (search_term, limit))
            
            results = cursor.fetchall()
            patients = []
            for row in results:
                patients.append({
                    'patient_id': row[0],
                    'name': row[1],
                    'age': row[2],
                    'gender': row[3],
                    'medical_history': row[4] if len(row) > 4 else None
                })
            
            cursor.close()
            conn.close()
            return patients
        except Exception as e:
            logger.error(f"Error retrieving patients: {e}")
            try:
                conn.close()
            except:
                pass
            return []
    
    @staticmethod
    def retrieve_appointments(patient_id: Optional[str] = None, doctor_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Retrieve appointment records"""
        conn = RAGRetriever.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout = '3s'")
            
            conditions = []
            params = []
            
            if patient_id:
                conditions.append("patient_id = %s")
                params.append(patient_id)
            
            if doctor_id:
                conditions.append("doctor_id = %s")
                params.append(doctor_id)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.append(limit)
            
            query_sql = f"""
                SELECT appointment_id, patient_id, doctor_id, appointment_date, status, notes
                FROM appointments
                WHERE {where_clause}
                ORDER BY appointment_date DESC
                LIMIT %s
            """
            
            cursor.execute(query_sql, params)
            results = cursor.fetchall()
            
            appointments = []
            for row in results:
                appointments.append({
                    'appointment_id': row[0],
                    'patient_id': row[1],
                    'doctor_id': row[2],
                    'appointment_date': row[3].isoformat() if isinstance(row[3], datetime) else str(row[3]),
                    'status': row[4],
                    'notes': row[5] if len(row) > 5 else None
                })
            
            cursor.close()
            conn.close()
            return appointments
        except Exception as e:
            logger.error(f"Error retrieving appointments: {e}")
            try:
                conn.close()
            except:
                pass
            return []
    
    @staticmethod
    def retrieve_medical_records(patient_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve medical records for a patient"""
        conn = RAGRetriever.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout = '3s'")
            
            query_sql = """
                SELECT record_id, patient_id, record_type, record_date, diagnosis, treatment, notes
                FROM medical_records
                WHERE patient_id = %s
                ORDER BY record_date DESC
                LIMIT %s
            """
            
            cursor.execute(query_sql, (patient_id, limit))
            results = cursor.fetchall()
            
            records = []
            for row in results:
                records.append({
                    'record_id': row[0],
                    'patient_id': row[1],
                    'record_type': row[2],
                    'record_date': row[3].isoformat() if isinstance(row[3], datetime) else str(row[3]),
                    'diagnosis': row[4],
                    'treatment': row[5],
                    'notes': row[6] if len(row) > 6 else None
                })
            
            cursor.close()
            conn.close()
            return records
        except Exception as e:
            logger.error(f"Error retrieving medical records: {e}")
            try:
                conn.close()
            except:
                pass
            return []
    
    @staticmethod
    def retrieve_context_for_query(query: str, max_results: int = 5) -> Dict[str, Any]:
        """Retrieve relevant context from multiple sources for a query"""
        context = {
            'doctors': [],
            'patients': [],
            'appointments': [],
            'medical_records': []
        }
        
        query_lower = query.lower()
        
        # Determine what to retrieve based on query
        if any(word in query_lower for word in ['doctor', 'physician', 'specialist', 'appointment']):
            # Extract specialty if mentioned
            specialty = None
            specialties = ['cardiologist', 'neurologist', 'dermatologist', 'pediatrician', 
                          'orthopedic', 'psychiatrist', 'gynecologist', 'general']
            for spec in specialties:
                if spec in query_lower:
                    specialty = spec
                    break
            
            context['doctors'] = RAGRetriever.retrieve_doctors(query, specialty, max_results)
        
        if any(word in query_lower for word in ['patient', 'medical history', 'record']):
            context['patients'] = RAGRetriever.retrieve_patients(query, max_results)
        
        if 'appointment' in query_lower:
            context['appointments'] = RAGRetriever.retrieve_appointments(limit=max_results)
        
        if any(word in query_lower for word in ['diagnosis', 'treatment', 'prescription', 'test']):
            # Try to extract patient_id from query or context
            # In real implementation, this would come from user session
            context['medical_records'] = RAGRetriever.retrieve_medical_records('', max_results)
        
        return context

