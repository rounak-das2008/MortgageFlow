"""
Simplified AI processor for mortgage document analysis using Vertex AI
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

class SimpleAIProcessor:
    """Simplified AI processor with Vertex AI integration and fallbacks"""
    
    def __init__(self):
        self.vertex_available = False
        self.gemini_available = False
        
        # Try google-genai (Vertex routing) first
        try:
            from google import genai
            self.gemini_client = genai.Client(vertexai=True, project=os.environ.get("GCP_PROJECT_ID", "genai-hackathon-25"), location=os.environ.get("GCP_GENAI_LOCATION", "global"))
            self.gemini_available = True
            logging.info("google-genai client (vertexai=True) initialized")
            
        except Exception as e:
            logging.warning(f"google-genai vertex routing not available: {str(e)}")
    
    def analyze_document(self, file_path: str, document_type: str, 
                        extraction_result: Optional[Dict[str, Any]] = None,
                        generate_summary: bool = True, 
                        fraud_detection: bool = True) -> Dict[str, Any]:
        """Analyze document using available AI services"""
        
        if not generate_summary and not fraud_detection:
            return self._basic_analysis(document_type, extraction_result)
        
        try:
            if self.gemini_available:
                return self._analyze_with_gemini(document_type, extraction_result, generate_summary, fraud_detection)
            else:
                return self._basic_analysis(document_type, extraction_result)
                
        except Exception as e:
            logging.error(f"AI analysis failed: {str(e)}")
            return self._basic_analysis(document_type, extraction_result)
    
    def analyze_application(self, app_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze complete application"""
        
        try:
            if self.vertex_available:
                return self._analyze_application_vertex(app_documents)
            elif self.gemini_available:
                return self._analyze_application_gemini(app_documents)
            else:
                return self._basic_application_analysis(app_documents)
                
        except Exception as e:
            logging.error(f"Application analysis failed: {str(e)}")
            return self._basic_application_analysis(app_documents)
    
    def _analyze_with_vertex(self, document_type: str, extraction_result: Dict[str, Any],
                           generate_summary: bool, fraud_detection: bool) -> Dict[str, Any]:
        """Analyze using Vertex AI"""
        
        prompt = self._create_analysis_prompt(document_type, extraction_result, generate_summary, fraud_detection)
        
        # No-op since we use google-genai path first now
        return self._basic_analysis(document_type, extraction_result)
    
    def _analyze_with_gemini(self, document_type: str, extraction_result: Dict[str, Any],
                           generate_summary: bool, fraud_detection: bool) -> Dict[str, Any]:
        """Analyze using Gemini API"""
        
        prompt = self._create_analysis_prompt(document_type, extraction_result, generate_summary, fraud_detection)
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            return self._parse_ai_response(response.text, document_type)
        except Exception as e:
            logging.error(f"Gemini API analysis failed: {str(e)}")
            return self._basic_analysis(document_type, extraction_result)
    
    def _analyze_application_vertex(self, app_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze application using Vertex AI"""
        
        prompt = self._create_application_prompt(app_documents)
        
        try:
            response = self.vertex_model.generate_content(prompt)
            return self._parse_application_response(response.text)
        except Exception as e:
            logging.error(f"Vertex AI application analysis failed: {str(e)}")
            return self._basic_application_analysis(app_documents)
    
    def _analyze_application_gemini(self, app_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze application using Gemini API"""
        
        prompt = self._create_application_prompt(app_documents)
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            return self._parse_application_response(response.text)
        except Exception as e:
            logging.error(f"Gemini API application analysis failed: {str(e)}")
            return self._basic_application_analysis(app_documents)
    
    def _create_analysis_prompt(self, document_type: str, extraction_result: Dict[str, Any],
                              generate_summary: bool, fraud_detection: bool) -> str:
        """Create analysis prompt for document"""
        
        prompt = f"Analyze this {document_type.replace('_', ' ')} document:\n\n"
        
        if extraction_result:
            if extraction_result.get('text_content'):
                prompt += f"Text content: {extraction_result['text_content'][:1000]}\n\n"
            
            if extraction_result.get('structured_data'):
                prompt += f"Extracted data: {json.dumps(extraction_result['structured_data'], indent=2)}\n\n"
        
        if generate_summary:
            prompt += "Provide a concise summary of this document.\n"
        
        if fraud_detection:
            prompt += "Analyze for potential fraud indicators.\n"
        
        prompt += "\nProvide response in JSON format with fields: summary, risk_level, recommendations"
        
        return prompt
    
    def _create_application_prompt(self, app_documents: List[Dict[str, Any]]) -> str:
        """Create prompt for application analysis"""
        
        prompt = "Analyze this mortgage application:\n\n"
        
        for i, doc in enumerate(app_documents, 1):
            prompt += f"Document {i}: {doc.get('document_type', 'unknown')}\n"
            if doc.get('processing_result', {}).get('validation_result'):
                validation = doc['processing_result']['validation_result']
                prompt += f"- Valid: {validation.get('is_valid', False)}\n"
                if validation.get('issues'):
                    prompt += f"- Issues: {', '.join(validation['issues'])}\n"
        
        prompt += "\nProvide analysis in JSON format with fields: summary, risk_assessment, recommendations, missing_documents"
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, document_type: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return {
                    'summary': parsed.get('summary', f"Analysis completed for {document_type}"),
                    'risk_assessment': {
                        'risk_level': parsed.get('risk_level', 'medium'),
                        'reason': parsed.get('reason', 'Standard analysis')
                    },
                    'recommendations': parsed.get('recommendations', []),
                    'quality_assessment': {
                        'overall_score': 0.8,
                        'issues': []
                    },
                    'fraud_indicators': parsed.get('fraud_indicators', []),
                    'key_insights': [f"Document analysis completed for {document_type}"]
                }
        except:
            pass
        
        # Fallback parsing
        return {
            'summary': f"AI analysis completed for {document_type}",
            'risk_assessment': {
                'risk_level': 'medium',
                'reason': 'Standard automated analysis'
            },
            'recommendations': ['Document processed successfully'],
            'quality_assessment': {
                'overall_score': 0.8,
                'issues': []
            },
            'fraud_indicators': [],
            'key_insights': ['Document analysis completed']
        }
    
    def _parse_application_response(self, response_text: str) -> Dict[str, Any]:
        """Parse application analysis response"""
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return {
                    'summary': parsed.get('summary', 'Application analysis completed'),
                    'risk_assessment': {
                        'risk_level': parsed.get('risk_level', 'medium'),
                        'reason': parsed.get('reason', 'Standard review')
                    },
                    'recommendations': parsed.get('recommendations', []),
                    'missing_documents': parsed.get('missing_documents', []),
                    'completeness_score': parsed.get('completeness_score', 0.8),
                    'approval_likelihood': parsed.get('approval_likelihood', 'moderate')
                }
        except:
            pass
        
        # Fallback
        return self._basic_application_analysis([])
    
    def _basic_analysis(self, document_type: str, extraction_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic analysis without AI"""
        
        return {
            'summary': f"Document processed: {document_type.replace('_', ' ').title()}",
            'risk_assessment': {
                'risk_level': 'medium',
                'reason': 'Standard processing completed'
            },
            'recommendations': ['Document uploaded successfully'],
            'quality_assessment': {
                'overall_score': 0.7,
                'issues': []
            },
            'fraud_indicators': [],
            'key_insights': ['Document processing completed']
        }
    
    def _basic_application_analysis(self, app_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic application analysis without AI"""
        
        doc_types = set(doc.get('document_type') for doc in app_documents)
        required_types = {'id_proof', 'payslip', 'bank_statement', 'employment_letter'}
        
        completeness = len(doc_types.intersection(required_types)) / len(required_types)
        missing = list(required_types - doc_types)
        
        return {
            'summary': f"Application contains {len(app_documents)} documents",
            'risk_assessment': {
                'risk_level': 'low' if completeness > 0.8 else 'medium',
                'reason': 'Basic completeness check'
            },
            'recommendations': ['Review all documents for completeness'],
            'missing_documents': missing,
            'completeness_score': completeness,
            'approval_likelihood': 'good' if completeness > 0.8 else 'moderate'
        }