"""
AWS Intelligence Services Integration
Uses AWS Comprehend Medical, Bedrock, and other services for intelligent responses
"""

import boto3
import json
import os
import logging
from typing import Dict, List, Any, Optional, Text
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSIntelligenceServices:
    """Integration with AWS services for intelligent healthcare responses"""
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Initialize AWS clients
        try:
            self.comprehend_medical = boto3.client('comprehendmedical', region_name=self.region)
            logger.info("AWS Comprehend Medical initialized")
        except Exception as e:
            logger.warning(f"Comprehend Medical not available: {e}")
            self.comprehend_medical = None
        
        try:
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.region)
            logger.info("AWS Bedrock Runtime initialized")
        except Exception as e:
            logger.warning(f"Bedrock Runtime not available: {e}")
            self.bedrock_runtime = None
        
        try:
            self.comprehend = boto3.client('comprehend', region_name=self.region)
            logger.info("AWS Comprehend initialized")
        except Exception as e:
            logger.warning(f"Comprehend not available: {e}")
            self.comprehend = None
    
    def extract_medical_entities(self, text: str) -> Dict[str, Any]:
        """Extract medical entities using AWS Comprehend Medical"""
        if not self.comprehend_medical:
            return {}
        
        try:
            response = self.comprehend_medical.detect_entities_v2(Text=text)
            entities = response.get('Entities', [])
            
            result = {
                'medications': [],
                'conditions': [],
                'anatomy': [],
                'procedures': [],
                'test_results': []
            }
            
            for entity in entities:
                entity_type = entity.get('Type', '')
                entity_text = entity.get('Text', '')
                category = entity.get('Category', '')
                
                if category == 'MEDICATION':
                    result['medications'].append({
                        'name': entity_text,
                        'type': entity_type
                    })
                elif category == 'MEDICAL_CONDITION':
                    result['conditions'].append({
                        'name': entity_text,
                        'type': entity_type
                    })
                elif category == 'ANATOMY':
                    result['anatomy'].append(entity_text)
                elif category == 'PROTECTED_HEALTH_INFORMATION':
                    # Skip PHI for privacy
                    pass
            
            return result
        except Exception as e:
            logger.error(f"Error extracting medical entities: {e}")
            return {}
    
    def detect_icd10_codes(self, text: str) -> List[Dict[str, Any]]:
        """Detect ICD-10 codes using AWS Comprehend Medical"""
        if not self.comprehend_medical:
            return []
        
        try:
            response = self.comprehend_medical.infer_icd10_cm(Text=text)
            codes = response.get('Entities', [])
            
            result = []
            for code_info in codes:
                result.append({
                    'code': code_info.get('ICD10CMConcepts', [{}])[0].get('Code', ''),
                    'description': code_info.get('ICD10CMConcepts', [{}])[0].get('Description', ''),
                    'text': code_info.get('Text', ''),
                    'score': code_info.get('Score', 0)
                })
            
            return result
        except Exception as e:
            logger.error(f"Error detecting ICD-10 codes: {e}")
            return []
    
    def detect_rxnorm_codes(self, text: str) -> List[Dict[str, Any]]:
        """Detect RxNorm codes for medications"""
        if not self.comprehend_medical:
            return []
        
        try:
            response = self.comprehend_medical.infer_rx_norm(Text=text)
            codes = response.get('Entities', [])
            
            result = []
            for code_info in codes:
                result.append({
                    'code': code_info.get('RxNormConcepts', [{}])[0].get('Code', ''),
                    'description': code_info.get('RxNormConcepts', [{}])[0].get('Description', ''),
                    'text': code_info.get('Text', ''),
                    'score': code_info.get('Score', 0)
                })
            
            return result
        except Exception as e:
            logger.error(f"Error detecting RxNorm codes: {e}")
            return []
    
    def generate_intelligent_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Text]]] = None
    ) -> str:
        """Generate intelligent response using AWS Bedrock Claude"""
        if not self.bedrock_runtime:
            return "I'm sorry, but the AI service is currently unavailable."
        
        try:
            # Extract medical entities for context
            medical_entities = self.extract_medical_entities(user_message)
            
            # Build system prompt
            system_prompt = """You are a professional healthcare assistant powered by AWS Bedrock. 
You provide accurate, empathetic, and helpful medical guidance while always emphasizing that 
you are not a substitute for professional medical care. You have access to medical entity recognition 
and can understand medical terminology, medications, conditions, and procedures."""
            
            # Build user prompt with context
            prompt = f"User question: {user_message}\n\n"
            
            if medical_entities:
                prompt += f"Detected medical information: {json.dumps(medical_entities, indent=2)}\n\n"
            
            if context:
                prompt += f"Additional context: {json.dumps(context, indent=2)}\n\n"
            
            prompt += "Please provide a helpful, accurate, and empathetic response."
            
            # Prepare messages
            messages = []
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Prepare request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": messages,
                "system": system_prompt
            }
            
            # Call Bedrock
            model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                return content[0].get('text', 'I apologize, but I could not generate a response.')
            else:
                return "I apologize, but I could not generate a response."
        
        except Exception as e:
            logger.error(f"Error generating intelligent response: {e}")
            return "I'm sorry, but I encountered an error while processing your request."
    
    def generate_conversational_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Text]]] = None,
        medical_entities: Optional[Dict[str, Any]] = None,
        sentiment: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate super intelligent conversational response using AWS Bedrock Claude with full context"""
        if not self.bedrock_runtime:
            logger.warning("Bedrock Runtime not available, using fallback")
            return None
        
        try:
            # Enhanced system prompt for super intelligent conversational bot
            system_prompt = """You are Dr. AI, a super intelligent, empathetic healthcare assistant powered by AWS Bedrock Claude. 
You engage in natural, flowing conversations and provide intelligent, context-aware responses.

YOUR INTELLIGENCE:
- You understand context from previous messages in the conversation
- You remember what was discussed earlier
- You ask follow-up questions when needed
- You provide detailed, helpful, and empathetic responses
- You can discuss any healthcare topic intelligently
- You use retrieved context from the database to provide accurate, specific answers
- You reference specific information when available (doctors, appointments, insurance, etc.)

CONVERSATION STYLE:
- Be warm, conversational, and natural
- Engage in back-and-forth dialogue
- Show understanding of the user's situation
- Provide comprehensive answers
- Ask clarifying questions when helpful
- Remember previous parts of the conversation
- Build on previous exchanges naturally

MEDICAL GUIDANCE:
- Provide helpful medical information and guidance
- Always emphasize you're not a substitute for professional medical care
- Recommend seeing doctors when appropriate
- Use medical entity recognition to understand conditions, medications, symptoms
- Consider sentiment to respond appropriately (empathetic for concerns, encouraging for positive)

You are a complete healthcare companion that can intelligently discuss appointments, insurance, symptoms, medications, wellness, and any healthcare topic."""
            
            # Build enhanced prompt with all context
            prompt_parts = [f"User: {user_message}"]
            
            # Add medical entities if available
            if medical_entities:
                entities_text = json.dumps(medical_entities, indent=2)
                prompt_parts.append(f"\nDetected Medical Information:\n{entities_text}")
            
            # Add sentiment if available
            if sentiment:
                sentiment_text = sentiment.get('sentiment', 'NEUTRAL')
                prompt_parts.append(f"\nSentiment: {sentiment_text}")
            
            # Add retrieved context from database (RAG)
            if context:
                context_text = json.dumps(context, indent=2, default=str)
                prompt_parts.append(f"\nRetrieved Context from Database:\n{context_text}")
            
            user_prompt = "\n".join(prompt_parts)
            user_prompt += "\n\nPlease provide an intelligent, conversational, and helpful response. Remember the conversation history and respond naturally."
            
            # Prepare conversation messages with history
            messages = []
            
            # Add conversation history (last 10 exchanges for context)
            if conversation_history:
                # Convert to Claude message format
                for msg in conversation_history[-10:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role in ['user', 'assistant'] and content:
                        messages.append({
                            "role": role,
                            "content": content
                        })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            # Prepare request body for Claude 3.5 Sonnet
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,  # Allow longer, more detailed responses
                "messages": messages,
                "system": system_prompt,
                "temperature": 0.7  # Slightly creative for natural conversation
            }
            
            # Call Bedrock with Claude 3.5 Sonnet
            model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
            
            logger.info(f"Calling Bedrock model {model_id} for conversational response")
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                intelligent_response = content[0].get('text', '')
                logger.info(f"Generated intelligent response: {intelligent_response[:100]}...")
                return intelligent_response
            else:
                logger.warning("Bedrock returned empty content")
                return None
        
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def detect_sentiment(self, text: str) -> Dict[str, Any]:
        """Detect sentiment using AWS Comprehend"""
        if not self.comprehend:
            return {'sentiment': 'NEUTRAL', 'score': 0.5}
        
        try:
            response = self.comprehend.detect_sentiment(Text=text, LanguageCode='en')
            return {
                'sentiment': response.get('Sentiment', 'NEUTRAL'),
                'scores': response.get('SentimentScore', {})
            }
        except Exception as e:
            logger.error(f"Error detecting sentiment: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0.5}
    
    def detect_language(self, text: str) -> str:
        """Detect language using AWS Comprehend"""
        if not self.comprehend:
            return 'en'
        
        try:
            response = self.comprehend.detect_dominant_language(Text=text)
            languages = response.get('Languages', [])
            if languages:
                return languages[0].get('LanguageCode', 'en')
            return 'en'
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return 'en'

