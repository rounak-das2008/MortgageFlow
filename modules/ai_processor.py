import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from google import genai
from google.genai import types
from .gcp_services import GCPServices
from dotenv import load_dotenv
load_dotenv()

class AIProcessor:
    def __init__(self):
        self.gcp_services = GCPServices()
        # Prefer google-genai with Vertex routing (no API key needed) to avoid Vertex SDK model path issues
        self.use_gemini = False
        try:
            project = os.environ.get("GCP_PROJECT_ID", "genai-hackathon-25")
            location = os.environ.get("GCP_GENAI_LOCATION", "global")
            self.client = genai.Client(vertexai=True, project=project, location=location)
            self.use_gemini = True
            logging.info("google-genai client initialized (vertexai=True, global)")
        except Exception as e:
            logging.warning(f"google-genai init failed: {str(e)}")
            self.client = None
            self.use_gemini = False
    
    def analyze_document(self, file_path: str, document_type: str, 
                        extraction_result: Optional[Dict[str, Any]] = None,
                        generate_summary: bool = True, 
                        fraud_detection: bool = True) -> Dict[str, Any]:
        """Analyze document using AI"""
        
        analysis_result = {
            'summary': None,
            'risk_assessment': None,
            'recommendations': [],
            'quality_assessment': None,
            'fraud_indicators': [],
            'key_insights': []
        }
        
        try:
            if not self.use_gemini:
                return self._fallback_analysis(extraction_result, document_type)
            
            # Generate document summary
            if generate_summary:
                analysis_result['summary'] = self._generate_document_summary(
                    file_path, document_type, extraction_result
                )
            
            # Perform fraud detection
            if fraud_detection:
                fraud_analysis = self._detect_fraud_indicators(
                    file_path, document_type, extraction_result
                )
                analysis_result['risk_assessment'] = fraud_analysis.get('risk_assessment')
                analysis_result['fraud_indicators'] = fraud_analysis.get('fraud_indicators', [])
            
            # Generate recommendations
            analysis_result['recommendations'] = self._generate_recommendations(
                document_type, extraction_result, analysis_result
            )
            
            # Quality assessment
            analysis_result['quality_assessment'] = self._assess_document_quality(
                extraction_result, document_type
            )
            
            # Key insights
            analysis_result['key_insights'] = self._extract_key_insights(
                extraction_result, document_type
            )
            
        except Exception as e:
            logging.error(f"AI analysis failed: {str(e)}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    def analyze_application(self, app_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze complete application using AI"""
        
        application_analysis = {
            'summary': None,
            'risk_assessment': None,
            'recommendations': [],
            'missing_documents': [],
            'completeness_score': 0.0,
            'approval_likelihood': None
        }
        
        try:
            if not self.use_gemini:
                return self._fallback_application_analysis(app_documents)
            
            # Prepare application data for analysis
            app_summary = self._prepare_application_summary(app_documents)
            
            # Generate comprehensive application analysis
            prompt = self._create_application_analysis_prompt(app_summary)
            
            if not self.client:
                return self._fallback_application_analysis(app_documents)
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2048
                )
            )
            
            if response.text:
                # Parse AI response
                application_analysis = self._parse_application_analysis(response.text)
            
        except Exception as e:
            logging.error(f"Application analysis failed: {str(e)}")
            application_analysis['error'] = str(e)
        
        return application_analysis
    
    def generate_smart_suggestions(self, validation_results: List[Dict[str, Any]], 
                                 document_types: List[str]) -> List[str]:
        """Generate smart suggestions based on validation results"""
        
        suggestions = []
        
        try:
            if not self.use_gemini:
                return self._fallback_suggestions(validation_results, document_types)
            
            # Prepare validation summary
            validation_summary = self._prepare_validation_summary(validation_results, document_types)
            
            prompt = f"""
            As a mortgage document expert, analyze these validation results and provide actionable suggestions:
            
            {validation_summary}
            
            Provide specific, actionable suggestions to help the borrower improve their application.
            Focus on:
            1. Missing or problematic documents
            2. Document quality issues
            3. Compliance requirements
            4. Timeline recommendations
            
            Format as a numbered list of clear, actionable items.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            
            if response.text:
                # Extract suggestions from response
                suggestions = self._extract_suggestions_from_response(response.text)
            
        except Exception as e:
            logging.error(f"Smart suggestions generation failed: {str(e)}")
            suggestions = ["Please review document requirements and re-upload if necessary"]
        
        return suggestions
    
    def _generate_document_summary(self, file_path: str, document_type: str, 
                                 extraction_result: Optional[Dict[str, Any]]) -> str:
        """Generate AI-powered document summary"""
        
        try:
            # Prepare context for analysis
            context = f"Document Type: {document_type.replace('_', ' ').title()}\n"
            
            if extraction_result and extraction_result.get('text_content'):
                text_content = extraction_result['text_content'][:2000]  # Limit text length
                context += f"Extracted Text: {text_content}\n"
            
            if extraction_result and extraction_result.get('structured_data'):
                structured_data = json.dumps(extraction_result['structured_data'], indent=2)
                context += f"Structured Data: {structured_data}\n"
            
            prompt = f"""
            Analyze this {document_type.replace('_', ' ')} document and provide a concise summary:
            
            {context}
            
            Provide a summary that includes:
            1. Document type and purpose
            2. Key information extracted
            3. Date and recency
            4. Any notable observations
            
            Keep the summary under 150 words and focus on mortgage application relevance.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt
            )
            
            return response.text if response.text else "Summary generation failed"
            
        except Exception as e:
            logging.error(f"Document summary generation failed: {str(e)}")
            return f"Unable to generate summary for {document_type.replace('_', ' ')}"
    
    def _detect_fraud_indicators(self, file_path: str, document_type: str,
                               extraction_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect potential fraud indicators using AI"""
        
        fraud_analysis = {
            'risk_assessment': {'risk_level': 'low', 'reason': ''},
            'fraud_indicators': [],
            'confidence': 0.0
        }
        
        try:
            # Prepare document data for fraud analysis
            analysis_data = {
                'document_type': document_type,
                'extraction_result': extraction_result
            }
            
            prompt = f"""
            As a fraud detection expert, analyze this mortgage document for potential fraud indicators:
            
            Document Type: {document_type.replace('_', ' ').title()}
            
            Extracted Data: {json.dumps(extraction_result, indent=2) if extraction_result else 'None'}
            
            Look for common fraud patterns in mortgage documents:
            1. Inconsistent formatting or fonts
            2. Unrealistic salary amounts
            3. Suspicious dates or date patterns
            4. Missing required information
            5. Data inconsistencies
            
            Provide:
            1. Risk level (low/medium/high)
            2. Specific fraud indicators found
            3. Reasoning for risk assessment
            4. Confidence level (0.0-1.0)
            
            Format response as JSON with fields: risk_level, fraud_indicators, reason, confidence
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                try:
                    fraud_analysis = json.loads(response.text)
                except json.JSONDecodeError:
                    # Fallback parsing
                    fraud_analysis['risk_assessment'] = {'risk_level': 'medium', 'reason': 'Analysis incomplete'}
            
        except Exception as e:
            logging.error(f"Fraud detection failed: {str(e)}")
            fraud_analysis['fraud_indicators'].append("Fraud detection analysis failed")
        
        return fraud_analysis
    
    def _generate_recommendations(self, document_type: str, extraction_result: Optional[Dict[str, Any]],
                                analysis_result: Dict[str, Any]) -> List[str]:
        """Generate AI-powered recommendations"""
        
        recommendations = []
        
        try:
            # Context for recommendations
            context = {
                'document_type': document_type,
                'has_extraction': bool(extraction_result),
                'risk_level': analysis_result.get('risk_assessment', {}).get('risk_level', 'unknown'),
                'fraud_indicators': analysis_result.get('fraud_indicators', [])
            }
            
            if extraction_result:
                context['structured_data'] = extraction_result.get('structured_data', {})
            
            prompt = f"""
            Based on this mortgage document analysis, provide specific recommendations:
            
            Context: {json.dumps(context, indent=2)}
            
            Provide actionable recommendations for:
            1. Document improvements
            2. Missing information
            3. Compliance requirements
            4. Next steps for the borrower
            
            Focus on practical, specific advice that will help with mortgage approval.
            Return as a JSON array of recommendation strings.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                try:
                    recommendations = json.loads(response.text)
                    if not isinstance(recommendations, list):
                        recommendations = ["Review document for completeness"]
                except json.JSONDecodeError:
                    recommendations = ["Review document quality and completeness"]
            
        except Exception as e:
            logging.error(f"Recommendations generation failed: {str(e)}")
            recommendations = ["Please ensure all required information is clearly visible"]
        
        return recommendations
    
    def _assess_document_quality(self, extraction_result: Optional[Dict[str, Any]], 
                               document_type: str) -> Dict[str, Any]:
        """Assess document quality using AI"""
        
        quality_assessment = {
            'overall_score': 0.0,
            'readability': 0.0,
            'completeness': 0.0,
            'clarity': 0.0,
            'issues': []
        }
        
        try:
            if not extraction_result:
                quality_assessment['issues'].append("No extraction data available")
                return quality_assessment
            
            confidence = extraction_result.get('confidence', 0.0)
            text_content = extraction_result.get('text_content', '')
            structured_data = extraction_result.get('structured_data', {})
            
            # Simple quality metrics
            quality_assessment['readability'] = min(confidence, 1.0)
            quality_assessment['completeness'] = min(len(structured_data) / 5.0, 1.0)  # Assume 5 fields = complete
            quality_assessment['clarity'] = 1.0 if len(text_content) > 100 else 0.5
            
            # Overall score
            quality_assessment['overall_score'] = (
                quality_assessment['readability'] * 0.4 +
                quality_assessment['completeness'] * 0.4 +
                quality_assessment['clarity'] * 0.2
            )
            
            # Generate issues
            if quality_assessment['readability'] < 0.7:
                quality_assessment['issues'].append("Document may be difficult to read")
            if quality_assessment['completeness'] < 0.6:
                quality_assessment['issues'].append("Some required information may be missing")
            
        except Exception as e:
            logging.error(f"Quality assessment failed: {str(e)}")
            quality_assessment['issues'].append("Quality assessment failed")
        
        return quality_assessment
    
    def _extract_key_insights(self, extraction_result: Optional[Dict[str, Any]], 
                            document_type: str) -> List[str]:
        """Extract key insights from document"""
        
        insights = []
        
        try:
            if not extraction_result or not extraction_result.get('structured_data'):
                return insights
            
            structured_data = extraction_result['structured_data']
            
            # Document-specific insights
            if document_type == 'payslip':
                if 'gross_salary' in structured_data:
                    insights.append(f"Gross salary information identified")
                if 'employer_name' in structured_data:
                    insights.append(f"Employment details available")
            
            elif document_type == 'bank_statement':
                if 'account_balance' in structured_data:
                    insights.append(f"Account balance information available")
                if 'account_number' in structured_data:
                    insights.append(f"Account verification possible")
            
            elif document_type == 'id_proof':
                if 'full_name' in structured_data:
                    insights.append(f"Identity verification information available")
                if 'expiry_date' in structured_data:
                    insights.append(f"Document validity period identified")
            
            # General insights
            confidence = extraction_result.get('confidence', 0.0)
            if confidence > 0.8:
                insights.append("High-quality document with clear information")
            elif confidence < 0.5:
                insights.append("Document quality may need improvement")
            
        except Exception as e:
            logging.error(f"Key insights extraction failed: {str(e)}")
        
        return insights
    
    def _fallback_analysis(self, extraction_result: Optional[Dict[str, Any]], 
                         document_type: str) -> Dict[str, Any]:
        """Fallback analysis when Gemini API is not available"""
        
        return {
            'summary': f"Basic analysis of {document_type.replace('_', ' ')} completed",
            'risk_assessment': {'risk_level': 'medium', 'reason': 'Unable to perform AI analysis'},
            'recommendations': ['Please ensure document is clear and complete'],
            'quality_assessment': {
                'overall_score': 0.5,
                'readability': 0.5,
                'completeness': 0.5,
                'clarity': 0.5,
                'issues': ['AI analysis not available']
            },
            'fraud_indicators': [],
            'key_insights': ['Basic document processing completed']
        }
    
    def _fallback_application_analysis(self, app_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback application analysis"""
        
        doc_types = set(doc.get('document_type') for doc in app_documents)
        required_types = {'id_proof', 'payslip', 'bank_statement'}
        
        completeness = len(doc_types.intersection(required_types)) / len(required_types)
        
        return {
            'summary': f"Application contains {len(app_documents)} documents",
            'risk_assessment': {'risk_level': 'medium', 'reason': 'Limited analysis available'},
            'recommendations': ['Upload all required documents'],
            'missing_documents': list(required_types - doc_types),
            'completeness_score': completeness,
            'approval_likelihood': 'moderate' if completeness > 0.6 else 'low'
        }
    
    def _fallback_suggestions(self, validation_results: List[Dict[str, Any]], 
                            document_types: List[str]) -> List[str]:
        """Fallback suggestions generation"""
        
        suggestions = []
        
        # Basic suggestions based on validation results
        for result in validation_results:
            if result.get('issues'):
                suggestions.append("Please address validation issues identified")
            if result.get('missing_fields'):
                suggestions.append("Ensure all required information is visible in documents")
        
        # Required document types check
        required_types = {'id_proof', 'payslip', 'bank_statement'}
        missing_types = required_types - set(document_types)
        
        for missing in missing_types:
            suggestions.append(f"Upload {missing.replace('_', ' ')} document")
        
        if not suggestions:
            suggestions.append("Review all documents for completeness")
        
        return suggestions
    
    def _prepare_application_summary(self, app_documents: List[Dict[str, Any]]) -> str:
        """Prepare application summary for AI analysis"""
        
        summary = f"Mortgage Application Analysis\n"
        summary += f"Total Documents: {len(app_documents)}\n\n"
        
        for i, doc in enumerate(app_documents, 1):
            summary += f"Document {i}:\n"
            summary += f"- Type: {doc.get('document_type', 'Unknown')}\n"
            summary += f"- Filename: {doc.get('filename', 'Unknown')}\n"
            
            processing_result = doc.get('processing_result', {})
            if processing_result:
                summary += f"- Processing Status: {processing_result.get('status', 'Unknown')}\n"
                
                validation = processing_result.get('validation_result', {})
                if validation:
                    summary += f"- Validation Score: {validation.get('validation_score', 0.0)}\n"
                    summary += f"- Valid: {validation.get('is_valid', False)}\n"
                    if validation.get('issues'):
                        summary += f"- Issues: {', '.join(validation['issues'])}\n"
            
            summary += "\n"
        
        return summary
    
    def _create_application_analysis_prompt(self, app_summary: str) -> str:
        """Create prompt for application analysis"""
        
        return f"""
        As a mortgage underwriting expert, analyze this complete mortgage application:
        
        {app_summary}
        
        Provide a comprehensive analysis including:
        1. Overall application summary
        2. Risk assessment (low/medium/high) with reasoning
        3. Specific recommendations for improvement
        4. Missing documents or information
        5. Completeness score (0.0-1.0)
        6. Approval likelihood assessment
        
        Focus on mortgage lending standards and regulatory requirements.
        Provide actionable insights for both the borrower and assessor.
        
        Format the response as a structured analysis with clear sections.
        """
    
    def _parse_application_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI application analysis response"""
        
        # This is a simplified parser - in production, would use more sophisticated parsing
        analysis = {
            'summary': '',
            'risk_assessment': {'risk_level': 'medium', 'reason': ''},
            'recommendations': [],
            'missing_documents': [],
            'completeness_score': 0.5,
            'approval_likelihood': 'moderate'
        }
        
        try:
            # Extract key sections from AI response
            lines = ai_response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify sections
                if 'summary' in line.lower():
                    current_section = 'summary'
                elif 'risk' in line.lower():
                    current_section = 'risk'
                elif 'recommendation' in line.lower():
                    current_section = 'recommendations'
                elif 'missing' in line.lower():
                    current_section = 'missing'
                elif current_section:
                    # Add content to current section
                    if current_section == 'summary':
                        analysis['summary'] += line + ' '
                    elif current_section == 'recommendations' and line.startswith('-'):
                        analysis['recommendations'].append(line[1:].strip())
                    elif current_section == 'missing' and line.startswith('-'):
                        analysis['missing_documents'].append(line[1:].strip())
            
            # Extract risk level
            response_lower = ai_response.lower()
            if 'high risk' in response_lower:
                analysis['risk_assessment']['risk_level'] = 'high'
            elif 'low risk' in response_lower:
                analysis['risk_assessment']['risk_level'] = 'low'
            
        except Exception as e:
            logging.error(f"Failed to parse AI analysis: {str(e)}")
        
        return analysis
    
    def _prepare_validation_summary(self, validation_results: List[Dict[str, Any]], 
                                  document_types: List[str]) -> str:
        """Prepare validation summary for suggestions"""
        
        summary = "Validation Results Summary:\n\n"
        
        for i, result in enumerate(validation_results):
            summary += f"Document {i+1} ({document_types[i] if i < len(document_types) else 'Unknown'}):\n"
            summary += f"- Valid: {result.get('is_valid', False)}\n"
            summary += f"- Score: {result.get('validation_score', 0.0)}\n"
            
            if result.get('issues'):
                summary += f"- Issues: {', '.join(result['issues'])}\n"
            
            if result.get('warnings'):
                summary += f"- Warnings: {', '.join(result['warnings'])}\n"
            
            if result.get('missing_fields'):
                summary += f"- Missing Fields: {', '.join(result['missing_fields'])}\n"
            
            summary += "\n"
        
        return summary
    
    def _extract_suggestions_from_response(self, ai_response: str) -> List[str]:
        """Extract suggestions from AI response"""
        
        suggestions = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered or bulleted lists
            if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('•'):
                suggestion = re.sub(r'^\d+\.\s*', '', line)
                suggestion = suggestion.lstrip('-•').strip()
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions if suggestions else ["Please review document requirements"]
