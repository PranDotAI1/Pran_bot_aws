"""
Text-to-SQL Agent: Converts natural language queries to SQL using AWS Bedrock
This makes the bot super intelligent by understanding queries and generating accurate SQL
"""

import boto3
import json
import logging
import os
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)

class TextToSQLAgent:
    """Intelligent Text-to-SQL agent using AWS Bedrock Claude"""
    
    def __init__(self):
        self.bedrock_runtime = None
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        
        try:
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            logger.info("Text-to-SQL Agent initialized with Bedrock")
        except Exception as e:
            logger.warning(f"Bedrock not available for Text-to-SQL: {e}")
    
    def get_database_schema(self) -> str:
        """Get database schema information for SQL generation"""
        schema = """
DATABASE SCHEMA (PostgreSQL):

1. doctors table:
   - doctor_id (integer, PRIMARY KEY)
   - name (varchar) - Doctor's full name
   - rating (numeric) - Doctor rating (0-5)
   - experience (integer) - Years of experience
   - doc_type (varchar) - Type: physician, gynecologist, cardiologist, neurologist, dermatologist, pediatrician, orthopedic, psychiatrist, general physician
   - specialty (varchar) - Medical specialty
   - department (varchar) - Department name
   - email (varchar) - Email address
   - phone (varchar) - Phone number

2. insurance_plans table:
   - plan_id (integer, PRIMARY KEY)
   - plan_name (varchar) - Plan name
   - monthly_premium (decimal) - Monthly premium cost
   - deductible (decimal) - Deductible amount
   - coverage_percentage (integer) - Coverage percentage (0-100)
   - features (text[]) - Array of features
   - is_active (boolean) - Whether plan is active

3. appointments table:
   - appointment_id (integer, PRIMARY KEY)
   - patient_id (integer) - Patient ID
   - doctor_id (integer) - Doctor ID (FOREIGN KEY to doctors)
   - appointment_date (date) - Appointment date
   - appointment_time (time) - Appointment time
   - status (varchar) - Status: scheduled, completed, cancelled
   - symptoms (text) - Patient symptoms
   - notes (text) - Additional notes

4. availability_slots table:
   - slot_id (integer, PRIMARY KEY)
   - doctor_id (integer) - Doctor ID (FOREIGN KEY to doctors)
   - date (date) - Slot date
   - start_time (time) - Start time
   - end_time (time) - End time
   - available (boolean) - Whether slot is available
   - patient_id (integer) - Patient ID if booked

5. medical_records table:
   - record_id (integer, PRIMARY KEY)
   - patient_id (integer) - Patient ID
   - doctor_id (integer) - Doctor ID
   - record_type (varchar) - Type: Lab Test, Diagnosis, Treatment
   - record_date (date) - Record date
   - diagnosis (text) - Diagnosis
   - treatment (text) - Treatment
   - notes (text) - Additional notes

6. patients table:
   - patient_id (integer, PRIMARY KEY)
   - first_name (varchar)
   - last_name (varchar)
   - date_of_birth (date)
   - gender (varchar)
   - contact_number (varchar)
   - email (varchar)
   - address (text)

IMPORTANT NOTES:
- Use ILIKE for case-insensitive text matching
- Use % for pattern matching in WHERE clauses
- Always use parameterized queries to prevent SQL injection
- Join doctors table when querying appointments or availability_slots
- Filter by is_active = true for insurance_plans
- Filter by available = true for availability_slots
"""
        return schema
    
    def generate_sql(self, user_query: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Convert natural language query to SQL using AWS Bedrock
        
        Returns:
            {
                'sql': 'SELECT ...',
                'table': 'doctors',
                'intent': 'find_doctors',
                'parameters': {...}
            }
        """
        if not self.bedrock_runtime:
            return None
        
        try:
            schema = self.get_database_schema()
            
            # Build enhanced prompt
            prompt = f"""You are an expert SQL query generator for a healthcare database. Convert the user's natural language query into a precise PostgreSQL SQL query.

DATABASE SCHEMA:
{schema}

USER QUERY: {user_query}

CONTEXT (if available):
{json.dumps(context, indent=2) if context else 'None'}

INSTRUCTIONS:
1. Generate a valid PostgreSQL SQL query that answers the user's question
2. Use proper JOINs when querying related tables
3. Use ILIKE for case-insensitive text matching
4. Use parameterized queries with %s placeholders
5. Always include relevant filters (is_active=true, available=true, etc.)
6. Limit results to reasonable numbers (10-20 rows)
7. Order results appropriately (by name, date, rating, etc.)

RESPOND IN JSON FORMAT:
{{
    "sql": "SELECT ... FROM ... WHERE ...",
    "table": "primary_table_name",
    "intent": "intent_description",
    "parameters": {{"param1": "value1"}},
    "explanation": "Brief explanation of the query"
}}

EXAMPLES:

User: "find gynecologists"
Response:
{{
    "sql": "SELECT doctor_id, name, specialty, department, email, phone, rating, experience FROM doctors WHERE (doc_type ILIKE %s OR specialty ILIKE %s OR department ILIKE %s) AND name IS NOT NULL ORDER BY rating DESC, name LIMIT 10",
    "table": "doctors",
    "intent": "find_doctors_by_specialty",
    "parameters": {{"specialty": "gynecologist"}},
    "explanation": "Find all gynecologists ordered by rating"
}}

User: "show me all insurance plans"
Response:
{{
    "sql": "SELECT plan_id, plan_name, monthly_premium, deductible, coverage_percentage, features FROM insurance_plans WHERE is_active = true ORDER BY monthly_premium LIMIT 10",
    "table": "insurance_plans",
    "intent": "list_insurance_plans",
    "parameters": {{}},
    "explanation": "Get all active insurance plans ordered by premium"
}}

User: "available appointment slots for cardiologist next week"
Response:
{{
    "sql": "SELECT s.slot_id, s.doctor_id, d.name as doctor_name, d.specialty, s.date, s.start_time, s.end_time FROM availability_slots s JOIN doctors d ON s.doctor_id = d.doctor_id WHERE s.available = true AND (d.doc_type ILIKE %s OR d.specialty ILIKE %s) AND s.date >= CURRENT_DATE AND s.date <= CURRENT_DATE + INTERVAL '7 days' ORDER BY s.date, s.start_time LIMIT 20",
    "table": "availability_slots",
    "intent": "find_available_slots",
    "parameters": {{"specialty": "cardiologist", "timeframe": "next_week"}},
    "explanation": "Find available slots for cardiologists in the next 7 days"
}}

Now generate the SQL query for the user's query above:"""

            # Call Bedrock
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "system": "You are an expert SQL query generator. Always respond with valid JSON only.",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info(f"Generated SQL: {result.get('sql', 'N/A')[:100]}...")
                return result
            else:
                logger.warning(f"Could not parse SQL from Bedrock response: {content[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def understand_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Understand the intent and extract entities from the query
        Returns structured information about what the user wants
        """
        if not self.bedrock_runtime:
            # Fallback to rule-based
            return self._rule_based_intent(user_query)
        
        try:
            prompt = f"""Analyze this healthcare query and extract intent and entities:

QUERY: {user_query}

Extract:
1. Intent (what the user wants): find_doctors, find_insurance, book_appointment, check_availability, get_medical_records, etc.
2. Entities:
   - specialty: gynecologist, cardiologist, etc.
   - date: specific date or relative (today, tomorrow, next week)
   - doctor_name: specific doctor name if mentioned
   - insurance_plan: specific plan name
   - symptoms: any symptoms mentioned
   - urgency: urgent, emergency, routine

Respond in JSON:
{{
    "intent": "intent_name",
    "entities": {{
        "specialty": "...",
        "date": "...",
        "doctor_name": "...",
        "symptoms": "...",
        "urgency": "..."
    }},
    "confidence": 0.0-1.0
}}"""

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": "You are an expert NLU system for healthcare queries. Respond with JSON only.",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info(f"Intent: {result.get('intent')}, Entities: {result.get('entities')}")
                return result
            else:
                return self._rule_based_intent(user_query)
                
        except Exception as e:
            logger.error(f"Error understanding intent: {e}")
            return self._rule_based_intent(user_query)
    
    def _rule_based_intent(self, user_query: str) -> Dict[str, Any]:
        """Fallback rule-based intent detection"""
        query_lower = user_query.lower()
        
        intent = "general_query"
        entities = {}
        
        # Detect intent
        if any(word in query_lower for word in ["doctor", "physician", "specialist", "find", "suggest", "show"]):
            intent = "find_doctors"
        elif any(word in query_lower for word in ["insurance", "plan", "coverage"]):
            intent = "find_insurance"
        elif any(word in query_lower for word in ["appointment", "book", "schedule"]):
            intent = "book_appointment"
        elif any(word in query_lower for word in ["available", "slot", "time"]):
            intent = "check_availability"
        elif any(word in query_lower for word in ["record", "lab", "test", "result"]):
            intent = "get_medical_records"
        
        # Extract entities
        specialties = ["gynecologist", "cardiologist", "neurologist", "dermatologist", 
                      "pediatrician", "orthopedic", "psychiatrist", "general physician"]
        for spec in specialties:
            if spec in query_lower:
                entities["specialty"] = spec
                break
        
        if "today" in query_lower:
            entities["date"] = "today"
        elif "tomorrow" in query_lower:
            entities["date"] = "tomorrow"
        elif "next week" in query_lower or "next week" in query_lower:
            entities["date"] = "next_week"
        
        return {
            "intent": intent,
            "entities": entities,
            "confidence": 0.7
        }
    
    def execute_sql_safely(self, sql: str, parameters: Dict[str, Any], connection) -> List[Dict]:
        """
        Execute SQL query safely with parameters
        Returns list of dictionaries (rows)
        """
        if not connection:
            return []
        
        try:
            cursor = connection.cursor()
            cursor.execute("SET statement_timeout = '5s'")
            
            # Convert parameters dict to tuple for SQL placeholders
            param_values = []
            if parameters:
                # Replace %s placeholders with actual values
                for key, value in parameters.items():
                    if key in sql:
                        sql = sql.replace(f"%{key}%", f"%{value}%")
                    param_values.append(f"%{value}%")
            
            # Execute query
            if param_values:
                cursor.execute(sql, tuple(param_values))
            else:
                cursor.execute(sql)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            logger.info(f"SQL executed successfully, returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

