"""
LLM Router: Uses AWS Bedrock to intelligently route queries and generate responses
This reduces hardcoded logic in actions.py by leveraging LLM intelligence
"""

import boto3
import json
import logging
import os
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)

class LLMRouter:
 """Intelligent router using AWS Bedrock to handle all queries"""
 
 def __init__(self):
 self.bedrock_runtime = None
 self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
 
 try:
 self.bedrock_runtime = boto3.client(
 'bedrock-runtime',
 region_name=os.getenv('AWS_REGION', 'us-east-1')
 )
 logger.info("LLM Router initialized with Bedrock")
 except Exception as e:
 logger.warning(f"Bedrock not available for LLM Router: {e}")
 
 def route_query(
 self,
 user_message: str,
 conversation_history: List[Dict] = None,
 retrieved_context: Dict = None,
 available_data: Dict = None
 ) -> Dict[str, Any]:
 """
 Use LLM to intelligently route the query and determine what action to take
 
 Returns:
 {
 'action': 'show_doctors' | 'show_insurance' | 'book_appointment' | 'analyze_symptoms' | 'general_response',
 'parameters': {
 'specialty': 'gynecology',
 'urgency': 'routine',
 'query_type': 'doctor_search'
 },
 'response_template': '...',
 'needs_data': True/False,
 'data_type': 'doctors' | 'insurance' | 'appointments'
 }
 """
 if not self.bedrock_runtime:
 return self._fallback_routing(user_message)
 
 try:
 # Format context for LLM
 context_str = self._format_context(retrieved_context, available_data)
 history_str = self._format_history(conversation_history)
 
 prompt = f"""You are a SUPER INTELLIGENT healthcare assistant router. Analyze the user's query CAREFULLY and determine the EXACT intent.

USER QUERY: "{user_message}"

CONVERSATION HISTORY:
{history_str}

AVAILABLE DATA CONTEXT:
{context_str}

CRITICAL INSTRUCTIONS:
- If user asks about "insurance", "insurance plans", "plans" (in insurance context) → action MUST be "show_insurance"
- If user asks about "doctors", "physicians", "specialists" → action MUST be "show_doctors"
- If user mentions symptoms → action MUST be "analyze_symptoms"
- UNDERSTAND CONTEXT: "Show me insurance plans" means INSURANCE, not doctors
- "plans" alone after insurance context means INSURANCE PLANS
- Be VERY PRECISE - don't confuse insurance with doctors

AVAILABLE ACTIONS:
1. show_doctors - Show doctors from database (use when user wants doctors, physicians, specialists)
2. show_insurance - Show insurance plans (use when user wants insurance, plans, coverage, premiums)
3. book_appointment - Help book appointment
4. analyze_symptoms - Analyze symptoms and recommend doctors
5. general_response - General helpful response

DATABASE DATA AVAILABLE:
- doctors: {len(retrieved_context.get('doctors', [])) if retrieved_context else 0} doctors
- insurance_plans: {len(retrieved_context.get('insurance_plans', [])) if retrieved_context else 0} plans
- appointments: {len(retrieved_context.get('appointments', [])) if retrieved_context else 0} appointments

INSTRUCTIONS:
1. Read the user query CAREFULLY
2. Determine the EXACT intent (insurance vs doctors vs symptoms)
3. Select the CORRECT action (be precise!)
4. Extract parameters (specialty, urgency, etc.)
5. Set needs_data=true if you need to retrieve data
6. Set data_type to "doctors" or "insurance" or "appointments"

EXAMPLES:
- "Show me insurance plans" → action: "show_insurance", data_type: "insurance"
- "insurance" → action: "show_insurance", data_type: "insurance"
- "plans" (after insurance context) → action: "show_insurance", data_type: "insurance"
- "suggest me some doctors" → action: "show_doctors", data_type: "doctors"
- "I need a gynecologist" → action: "show_doctors", data_type: "doctors", specialty: "gynecology"

Respond in JSON format ONLY:
{{
 "action": "action_name",
 "parameters": {{
 "specialty": "specialty_name or null",
 "urgency": "routine|urgent|emergency or null",
 "query_type": "doctor_search|insurance_query|appointment|symptom_analysis",
 "symptoms": ["symptom1", "symptom2"] or null
 }},
 "needs_data": true/false,
 "data_type": "doctors|insurance|appointments|none",
 "response_template": "Template for response",
 "explanation": "Why this action was chosen"
}}

EXAMPLES:

User: "I need a gynecologist"
Response:
{{
 "action": "show_doctors",
 "parameters": {{"specialty": "gynecology", "query_type": "doctor_search"}},
 "needs_data": true,
 "data_type": "doctors",
 "response_template": " I found {{count}} gynecologist(s) for you:\\n\\n{{doctors}}\\n\\nWould you like to book an appointment?",
 "explanation": "User wants to find a gynecologist"
}}

User: "I am suffering from viral"
Response:
{{
 "action": "analyze_symptoms",
 "parameters": {{"symptoms": ["viral"], "specialty": "general_medicine", "urgency": "routine", "query_type": "symptom_analysis"}},
 "needs_data": true,
 "data_type": "doctors",
 "response_template": " Based on your symptoms, I recommend seeing a General Physician.\\n\\n I found {{count}} doctor(s):\\n\\n{{doctors}}\\n\\nWould you like to book an appointment?",
 "explanation": "User has symptoms, need to analyze and recommend doctors"
}}

User: "show me all insurance plans"
Response:
{{
 "action": "show_insurance",
 "parameters": {{"query_type": "insurance_query"}},
 "needs_data": true,
 "data_type": "insurance",
 "response_template": " Here are all available insurance plans:\\n\\n{{plans}}\\n\\nWould you like more details about any plan?",
 "explanation": "User wants to see insurance plans"
}}

Now analyze the user's query:"""

 body = {
 "anthropic_version": "bedrock-2023-05-31",
 "max_tokens": 2000,
 "system": "You are an intelligent healthcare assistant router. Always respond with valid JSON only.",
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
 
 # Extract JSON
 json_match = re.search(r'\{.*\}', content, re.DOTALL)
 if json_match:
 result = json.loads(json_match.group())
 logger.info(f"LLM Router: Action={result.get('action')}, DataType={result.get('data_type')}")
 return result
 
 return self._fallback_routing(user_message)
 
 except Exception as e:
 logger.error(f"LLM Router failed: {e}")
 import traceback
 logger.error(traceback.format_exc())
 return self._fallback_routing(user_message)
 
 def _format_context(self, retrieved_context: Dict, available_data: Dict) -> str:
 """Format retrieved context for LLM"""
 if not retrieved_context:
 return "No context available"
 
 parts = []
 if retrieved_context.get('doctors'):
 parts.append(f"DOCTORS ({len(retrieved_context['doctors'])}):")
 for doc in retrieved_context['doctors'][:3]:
 parts.append(f" - {doc.get('name')} ({doc.get('specialty')})")
 
 if retrieved_context.get('insurance_plans'):
 parts.append(f"INSURANCE PLANS ({len(retrieved_context['insurance_plans'])}):")
 for plan in retrieved_context['insurance_plans'][:3]:
 parts.append(f" - {plan.get('name')} (${plan.get('monthly_premium')})")
 
 return "\n".join(parts) if parts else "No context available"
 
 def _format_history(self, conversation_history: List[Dict]) -> str:
 """Format conversation history for LLM"""
 if not conversation_history:
 return "No previous conversation"
 
 parts = []
 for msg in conversation_history[-5:]: # Last 5 messages
 role = msg.get('role', 'user')
 content = msg.get('content', '')
 parts.append(f"{role.upper()}: {content}")
 
 return "\n".join(parts)
 
 def _fallback_routing(self, user_message: str) -> Dict[str, Any]:
 """Fallback rule-based routing"""
 msg_lower = user_message.lower()
 
 if any(word in msg_lower for word in ["doctor", "physician", "specialist", "gynecologist", "cardiologist"]):
 specialty = None
 if "gynecologist" in msg_lower or "gynec" in msg_lower:
 specialty = "gynecology"
 elif "cardiologist" in msg_lower:
 specialty = "cardiology"
 
 return {
 'action': 'show_doctors',
 'parameters': {'specialty': specialty, 'query_type': 'doctor_search'},
 'needs_data': True,
 'data_type': 'doctors',
 'response_template': ' I found {{count}} doctor(s):\n\n{{doctors}}\n\nWould you like to book an appointment?',
 'explanation': 'User wants to find doctors'
 }
 
 elif any(word in msg_lower for word in ["insurance", "plan", "coverage"]):
 return {
 'action': 'show_insurance',
 'parameters': {'query_type': 'insurance_query'},
 'needs_data': True,
 'data_type': 'insurance',
 'response_template': ' Here are all available insurance plans:\n\n{{plans}}\n\nWould you like more details?',
 'explanation': 'User wants to see insurance plans'
 }
 
 elif any(word in msg_lower for word in ["fever", "cold", "cough", "suffering", "symptom", "pain", "viral"]):
 return {
 'action': 'analyze_symptoms',
 'parameters': {'symptoms': ['mentioned'], 'specialty': 'general_medicine', 'urgency': 'routine'},
 'needs_data': True,
 'data_type': 'doctors',
 'response_template': 'Based on your symptoms, I recommend seeing a doctor.\n\n I found {{count}} doctor(s):\n\n{{doctors}}',
 'explanation': 'User has symptoms'
 }
 
 else:
 return {
 'action': 'general_response',
 'parameters': {},
 'needs_data': False,
 'data_type': 'none',
 'response_template': 'I\'m here to help with your healthcare needs. How can I assist you?',
 'explanation': 'General query'
 }
 
 def generate_response(
 self,
 action: str,
 data: Dict[str, Any],
 parameters: Dict[str, Any],
 template: str = None
 ) -> str:
 """
 Generate final response using LLM based on action and data
 
 Args:
 action: The action to perform
 data: Retrieved data (doctors, insurance plans, etc.)
 parameters: Action parameters
 template: Optional response template
 """
 if not self.bedrock_runtime:
 return self._generate_fallback_response(action, data, parameters)
 
 try:
 # Format data for LLM
 data_str = self._format_data_for_response(data, action)
 
 prompt = f"""Generate a helpful, empathetic healthcare assistant response.

ACTION: {action}
PARAMETERS: {json.dumps(parameters, indent=2)}
DATA AVAILABLE:
{data_str}

INSTRUCTIONS:
- Be empathetic and professional
- Use the data provided to give specific information
- Format doctors/plans nicely with emojis
- Ask follow-up questions when appropriate
- If urgency is "emergency", emphasize immediate care
- Keep response concise but informative

Generate the response:"""

 body = {
 "anthropic_version": "bedrock-2023-05-31",
 "max_tokens": 1500,
 "system": "You are Dr. AI, an empathetic healthcare assistant. Generate helpful, professional responses.",
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
 
 return content.strip()
 
 except Exception as e:
 logger.error(f"LLM response generation failed: {e}")
 return self._generate_fallback_response(action, data, parameters)
 
 def _format_data_for_response(self, data: Dict[str, Any], action: str) -> str:
 """Format data for LLM response generation"""
 if action == 'show_doctors' and data.get('doctors'):
 doctors = data['doctors']
 parts = [f"DOCTORS ({len(doctors)}):"]
 for i, doc in enumerate(doctors[:5], 1):
 parts.append(f"{i}. {doc.get('name')} - {doc.get('specialty')} - Phone: {doc.get('phone')}")
 return "\n".join(parts)
 
 elif action == 'show_insurance' and data.get('insurance_plans'):
 plans = data['insurance_plans']
 parts = [f"INSURANCE PLANS ({len(plans)}):"]
 for i, plan in enumerate(plans[:5], 1):
 parts.append(f"{i}. {plan.get('name')} - Premium: {plan.get('monthly_premium')} - Coverage: {plan.get('coverage')}")
 return "\n".join(parts)
 
 return "No specific data available"
 
 def _generate_fallback_response(self, action: str, data: Dict[str, Any], parameters: Dict[str, Any]) -> str:
 """Generate fallback response without LLM"""
 if action == 'show_doctors' and data.get('doctors'):
 doctors = data['doctors']
 response = f" **I found {len(doctors)} doctor(s):**\n\n"
 for i, doc in enumerate(doctors[:5], 1):
 response += f"**{i}. Dr. {doc.get('name', 'N/A')}**\n"
 response += f" Specialty: {doc.get('specialty', 'General Medicine')}\n"
 if doc.get('phone'):
 response += f" Phone: {doc.get('phone')}\n"
 response += "\n"
 response += " Would you like to book an appointment?"
 return response
 
 elif action == 'show_insurance' and data.get('insurance_plans'):
 plans = data['insurance_plans']
 response = f" **Here are all available insurance plans ({len(plans)}):**\n\n"
 for i, plan in enumerate(plans[:5], 1):
 response += f"**{i}. {plan.get('name')}**\n"
 response += f" Monthly Premium: {plan.get('monthly_premium')}\n"
 response += f" Coverage: {plan.get('coverage')}\n\n"
 return response
 
 return "I'm here to help with your healthcare needs. How can I assist you?"

