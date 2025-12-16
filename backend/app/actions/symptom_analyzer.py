"""
Symptom Analyzer: Analyzes symptoms and recommends appropriate doctors
Uses AWS Bedrock and Comprehend Medical for intelligent symptom understanding
"""

import boto3
import json
import logging
import os
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)

class SymptomAnalyzer:
 """Analyzes symptoms and recommends appropriate medical specialties and doctors"""
 
 def __init__(self):
 self.bedrock_runtime = None
 self.comprehend_medical = None
 self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
 
 try:
 self.bedrock_runtime = boto3.client(
 'bedrock-runtime',
 region_name=os.getenv('AWS_REGION', 'us-east-1')
 )
 logger.info("Symptom Analyzer initialized with Bedrock")
 except Exception as e:
 logger.warning(f"Bedrock not available for Symptom Analyzer: {e}")
 
 try:
 self.comprehend_medical = boto3.client(
 'comprehendmedical',
 region_name=os.getenv('AWS_REGION', 'us-east-1')
 )
 logger.info("Symptom Analyzer initialized with Comprehend Medical")
 except Exception as e:
 logger.warning(f"Comprehend Medical not available: {e}")
 
 def get_symptom_to_specialty_mapping(self) -> Dict[str, List[str]]:
 """Get mapping of symptoms to medical specialties"""
 return {
 # General Medicine / Primary Care
 'general_medicine': [
 'fever', 'cold', 'cough', 'flu', 'viral', 'infection', 'headache', 'body ache',
 'fatigue', 'weakness', 'nausea', 'vomiting', 'diarrhea', 'constipation',
 'common cold', 'sore throat', 'runny nose', 'congestion'
 ],
 
 # Cardiology
 'cardiology': [
 'chest pain', 'heart pain', 'palpitations', 'irregular heartbeat', 'shortness of breath',
 'high blood pressure', 'hypertension', 'low blood pressure', 'hypotension',
 'heart attack', 'cardiac', 'heart disease', 'chest discomfort', 'dizziness',
 'swollen ankles', 'heart murmur', 'arrhythmia'
 ],
 
 # Gynecology
 'gynecology': [
 'menstrual', 'period', 'pregnancy', 'pregnant', 'maternity', 'gynecological',
 'pelvic pain', 'vaginal', 'ovarian', 'uterine', 'menopause', 'fertility',
 'prenatal', 'postnatal', 'breast', 'pap smear', 'contraception'
 ],
 
 # Neurology
 'neurology': [
 'headache', 'migraine', 'severe headache', 'dizziness', 'vertigo', 'seizure',
 'epilepsy', 'tremor', 'parkinson', 'alzheimer', 'memory loss', 'confusion',
 'numbness', 'tingling', 'weakness in limbs', 'stroke', 'brain', 'neurological'
 ],
 
 # Dermatology
 'dermatology': [
 'rash', 'skin', 'acne', 'eczema', 'psoriasis', 'dermatitis', 'mole', 'wart',
 'itching', 'hives', 'allergy', 'skin infection', 'fungal', 'bacterial skin',
 'hair loss', 'alopecia', 'nail', 'dermatological'
 ],
 
 # Pediatrics
 'pediatrics': [
 'child', 'baby', 'infant', 'toddler', 'pediatric', 'children', 'kids',
 'childhood', 'vaccination', 'immunization', 'growth', 'development',
 'newborn', 'teenager', 'adolescent'
 ],
 
 # Orthopedics
 'orthopedics': [
 'bone', 'fracture', 'broken bone', 'joint pain', 'arthritis', 'back pain',
 'spine', 'knee pain', 'hip pain', 'shoulder pain', 'elbow pain', 'wrist pain',
 'sports injury', 'orthopedic', 'musculoskeletal', 'ligament', 'tendon'
 ],
 
 # Psychiatry / Mental Health
 'psychiatry': [
 'depression', 'anxiety', 'stress', 'mental health', 'psychiatric', 'therapy',
 'counseling', 'panic attack', 'phobia', 'bipolar', 'schizophrenia', 'suicidal',
 'emotional', 'mood', 'behavioral', 'addiction', 'substance abuse'
 ],
 
 # Gastroenterology
 'gastroenterology': [
 'stomach pain', 'abdominal pain', 'acid reflux', 'gerd', 'ulcer', 'indigestion',
 'bloating', 'gas', 'ibs', 'crohn', 'colitis', 'liver', 'gallbladder',
 'pancreas', 'digestive', 'gastrointestinal'
 ],
 
 # Endocrinology
 'endocrinology': [
 'diabetes', 'blood sugar', 'glucose', 'thyroid', 'hormone', 'metabolism',
 'weight gain', 'weight loss', 'insulin', 'diabetic', 'hypothyroidism',
 'hyperthyroidism', 'adrenal', 'pituitary'
 ],
 
 # Urology
 'urology': [
 'urinary', 'bladder', 'kidney', 'prostate', 'uti', 'urinary tract infection',
 'kidney stone', 'incontinence', 'erectile', 'urological'
 ],
 
 # ENT (Ear, Nose, Throat)
 'ent': [
 'ear pain', 'hearing loss', 'ear infection', 'sinus', 'sinusitis', 'nasal',
 'nose', 'throat', 'tonsil', 'laryngitis', 'hoarse voice', 'ear nose throat'
 ],
 
 # Ophthalmology
 'ophthalmology': [
 'eye', 'vision', 'blurred vision', 'eye pain', 'red eye', 'cataract',
 'glaucoma', 'retina', 'ophthalmic', 'ophthalmological'
 ],
 
 # Pulmonology
 'pulmonology': [
 'asthma', 'copd', 'breathing', 'lung', 'pneumonia', 'bronchitis', 'respiratory',
 'shortness of breath', 'wheezing', 'cough', 'pulmonary'
 ]
 }
 
 def analyze_symptoms(self, user_message: str) -> Dict[str, Any]:
 """
 Analyze symptoms from user message and recommend specialty
 
 Returns:
 {
 'symptoms': ['fever', 'cough'],
 'recommended_specialty': 'general_medicine',
 'specialty_display_name': 'General Physician',
 'urgency': 'routine' | 'urgent' | 'emergency',
 'confidence': 0.0-1.0,
 'explanation': 'Why this specialty was recommended'
 }
 """
 msg_lower = user_message.lower()
 
 # Use AWS Comprehend Medical if available
 medical_entities = {}
 if self.comprehend_medical:
 try:
 response = self.comprehend_medical.detect_entities(Text=user_message)
 entities = response.get('Entities', [])
 medical_entities = {
 'symptoms': [e['Text'] for e in entities if e['Type'] == 'SYMPTOM'],
 'conditions': [e['Text'] for e in entities if e['Type'] == 'MEDICAL_CONDITION'],
 'medications': [e['Text'] for e in entities if e['Type'] == 'MEDICATION']
 }
 logger.info(f"Comprehend Medical detected: {medical_entities}")
 except Exception as e:
 logger.debug(f"Comprehend Medical failed: {e}")
 
 # Use AWS Bedrock for intelligent analysis
 if self.bedrock_runtime:
 try:
 return self._analyze_with_bedrock(user_message, medical_entities)
 except Exception as e:
 logger.error(f"Bedrock analysis failed: {e}")
 
 # Fallback to rule-based analysis
 return self._rule_based_analysis(user_message, medical_entities)
 
 def _analyze_with_bedrock(self, user_message: str, medical_entities: Dict) -> Dict[str, Any]:
 """Use AWS Bedrock for intelligent symptom analysis"""
 
 symptom_mapping = self.get_symptom_to_specialty_mapping()
 mapping_str = json.dumps(symptom_mapping, indent=2)
 
 prompt = f"""Analyze these symptoms and recommend the appropriate medical specialty:

USER MESSAGE: {user_message}

MEDICAL ENTITIES DETECTED: {json.dumps(medical_entities, indent=2)}

SYMPTOM TO SPECIALTY MAPPING:
{mapping_str}

Analyze the symptoms and determine:
1. What symptoms are mentioned?
2. Which medical specialty is most appropriate?
3. What is the urgency level? (routine, urgent, emergency)
4. Why this specialty was recommended?

Respond in JSON format:
{{
 "symptoms": ["symptom1", "symptom2"],
 "recommended_specialty": "specialty_key",
 "specialty_display_name": "Display Name",
 "urgency": "routine|urgent|emergency",
 "confidence": 0.0-1.0,
 "explanation": "Brief explanation"
}}

SPECIALTY KEYS: general_medicine, cardiology, gynecology, neurology, dermatology, pediatrics, orthopedics, psychiatry, gastroenterology, endocrinology, urology, ent, ophthalmology, pulmonology

URGENCY GUIDELINES:
- emergency: chest pain, difficulty breathing, severe trauma, loss of consciousness, severe allergic reaction
- urgent: high fever (>103°F), severe pain, persistent vomiting, signs of infection
- routine: common cold, mild symptoms, checkups, non-urgent concerns

Now analyze the symptoms:"""

 body = {
 "anthropic_version": "bedrock-2023-05-31",
 "max_tokens": 1000,
 "system": "You are a medical AI assistant. Analyze symptoms and recommend appropriate medical specialties. Always respond with valid JSON only.",
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
 logger.info(f"Bedrock analysis: {result.get('recommended_specialty')} (confidence: {result.get('confidence')})")
 return result
 
 # Fallback if JSON parsing fails
 return self._rule_based_analysis(user_message, medical_entities)
 
 def _rule_based_analysis(self, user_message: str, medical_entities: Dict) -> Dict[str, Any]:
 """Rule-based symptom analysis (fallback)"""
 msg_lower = user_message.lower()
 
 symptom_mapping = self.get_symptom_to_specialty_mapping()
 
 # Count matches for each specialty
 specialty_scores = {}
 for specialty, symptoms in symptom_mapping.items():
 score = sum(1 for symptom in symptoms if symptom in msg_lower)
 if score > 0:
 specialty_scores[specialty] = score
 
 # Determine recommended specialty
 recommended_specialty = 'general_medicine' # Default
 specialty_display_name = 'General Physician'
 confidence = 0.5
 
 if specialty_scores:
 recommended_specialty = max(specialty_scores, key=specialty_scores.get)
 confidence = min(0.9, 0.5 + (specialty_scores[recommended_specialty] * 0.1))
 
 # Map to display name
 display_names = {
 'general_medicine': 'General Physician',
 'cardiology': 'Cardiologist',
 'gynecology': 'Gynecologist',
 'neurology': 'Neurologist',
 'dermatology': 'Dermatologist',
 'pediatrics': 'Pediatrician',
 'orthopedics': 'Orthopedic Surgeon',
 'psychiatry': 'Psychiatrist',
 'gastroenterology': 'Gastroenterologist',
 'endocrinology': 'Endocrinologist',
 'urology': 'Urologist',
 'ent': 'ENT Specialist',
 'ophthalmology': 'Ophthalmologist',
 'pulmonology': 'Pulmonologist'
 }
 specialty_display_name = display_names.get(recommended_specialty, 'General Physician')
 
 # Determine urgency
 urgency = 'routine'
 emergency_keywords = ['chest pain', 'difficulty breathing', 'severe', 'emergency', 'can\'t breathe', 'unconscious']
 urgent_keywords = ['high fever', 'persistent', 'severe pain', 'worsening']
 
 if any(keyword in msg_lower for keyword in emergency_keywords):
 urgency = 'emergency'
 elif any(keyword in msg_lower for keyword in urgent_keywords):
 urgency = 'urgent'
 
 # Extract symptoms
 symptoms = medical_entities.get('symptoms', [])
 if not symptoms:
 # Try to extract from message
 common_symptoms = ['fever', 'cough', 'headache', 'pain', 'nausea', 'vomiting', 'diarrhea']
 symptoms = [s for s in common_symptoms if s in msg_lower]
 
 explanation = f"Based on your symptoms, I recommend seeing a {specialty_display_name.lower()}. "
 if urgency == 'emergency':
 explanation += "This appears to be an emergency - please seek immediate medical care or call 911."
 elif urgency == 'urgent':
 explanation += "This should be addressed soon - I can help you find an urgent care facility or schedule an appointment."
 else:
 explanation += "I can help you find a doctor and book an appointment."
 
 return {
 'symptoms': symptoms if symptoms else ['symptoms mentioned'],
 'recommended_specialty': recommended_specialty,
 'specialty_display_name': specialty_display_name,
 'urgency': urgency,
 'confidence': confidence,
 'explanation': explanation
 }
 
 def get_recommended_doctors_query(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
 """
 Generate SQL query parameters for finding recommended doctors
 
 Returns:
 {
 'specialty': 'gynecology',
 'specialty_display_name': 'Gynecologist',
 'urgency': 'routine',
 'explanation': '...'
 }
 """
 return {
 'specialty': analysis_result.get('recommended_specialty'),
 'specialty_display_name': analysis_result.get('specialty_display_name'),
 'urgency': analysis_result.get('urgency'),
 'explanation': analysis_result.get('explanation'),
 'symptoms': analysis_result.get('symptoms', [])
 }

