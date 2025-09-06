import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytesseract
from PIL import Image
import PyPDF2
from .gcp_services import GCPServices

class DocumentExtractor:
    def __init__(self):
        self.gcp_services = GCPServices()
        self.use_gcp = self.gcp_services.check_services()
        
        if not self.use_gcp:
            logging.info("Using fallback OCR (Tesseract)")
    
    def extract_document_data(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract text and structured data from document"""
        
        try:
            if self.use_gcp:
                return self._extract_with_document_ai(file_path, document_type)
            else:
                return self._extract_with_tesseract(file_path, document_type)
                
        except Exception as e:
            logging.error(f"Document extraction failed: {str(e)}")
            return {
                'error': str(e),
                'text_content': None,
                'structured_data': None,
                'confidence': 0.0
            }
    
    def _extract_with_document_ai(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract using GCP Document AI"""
        
        try:
            # Determine processor type based on document type
            processor_type = self._get_processor_type(document_type)
            
            # Process document
            result = self.gcp_services.process_document(file_path, processor_type)
            
            if not result:
                raise Exception("Document AI processing failed")
            
            # Parse Document AI response
            extracted_data = {
                'text_content': result.get('text', ''),
                'structured_data': {},
                'confidence': result.get('confidence', 0.0),
                'processor_type': processor_type
            }
            
            # Extract entities based on document type
            if result.get('entities'):
                extracted_data['structured_data'] = self._parse_entities(
                    result['entities'], document_type
                )
            
            return extracted_data
            
        except Exception as e:
            logging.error(f"Document AI extraction failed: {str(e)}")
            # Fallback to Tesseract
            return self._extract_with_tesseract(file_path, document_type)
    
    def _extract_with_tesseract(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Fallback extraction using Tesseract OCR"""
        
        try:
            text_content = ""
            
            # Handle PDF files
            if file_path.lower().endswith('.pdf'):
                text_content = self._extract_pdf_text(file_path)
                
                # If PDF text extraction fails, convert to image and OCR
                if not text_content.strip():
                    text_content = self._ocr_pdf_as_images(file_path)
            
            # Handle image files
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                text_content = self._ocr_image(file_path)
            
            else:
                raise Exception(f"Unsupported file format: {file_path}")
            
            # Extract structured data using pattern matching
            structured_data = self._extract_structured_data_patterns(
                text_content, document_type
            )
            
            return {
                'text_content': text_content,
                'structured_data': structured_data,
                'confidence': 0.7,  # Lower confidence for Tesseract
                'extraction_method': 'tesseract'
            }
            
        except Exception as e:
            logging.error(f"Tesseract extraction failed: {str(e)}")
            return {
                'error': str(e),
                'text_content': '',
                'structured_data': {},
                'confidence': 0.0
            }
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        
        text_content = ""
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
                    
        except Exception as e:
            logging.error(f"PDF text extraction failed: {str(e)}")
            
        return text_content
    
    def _ocr_image(self, file_path: str) -> str:
        """Perform OCR on image file"""
        
        try:
            image = Image.open(file_path)
            text_content = pytesseract.image_to_string(image)
            return text_content
            
        except Exception as e:
            logging.error(f"Image OCR failed: {str(e)}")
            return ""
    
    def _ocr_pdf_as_images(self, file_path: str) -> str:
        """Convert PDF pages to images and perform OCR"""
        
        # This would require pdf2image library
        # For now, return empty string as fallback
        logging.warning("PDF to image conversion not implemented")
        return ""
    
    def _get_processor_type(self, document_type: str) -> str:
        """Map document type to Document AI processor type"""
        
        processor_mapping = {
            'payslip': 'FORM_PARSER_PROCESSOR',
            'bank_statement': 'BANK_STATEMENT_PROCESSOR',
            'id_proof': 'ID_PROCESSOR',
            'tax_document': 'FORM_PARSER_PROCESSOR',
            'invoice': 'INVOICE_PROCESSOR',
            'ocr': 'OCR_PROCESSOR',
            'employment_letter': 'FORM_PARSER_PROCESSOR',
            'utility_bill': 'FORM_PARSER_PROCESSOR'
        }
        
        return processor_mapping.get(document_type, 'FORM_PARSER_PROCESSOR')
    
    def _parse_entities(self, entities: list, document_type: str) -> Dict[str, Any]:
        """Parse Document AI entities into structured data"""
        
        structured_data = {}
        
        for entity in entities:
            entity_type = entity.get('type', '')
            entity_text = entity.get('mentionText', '')
            confidence = entity.get('confidence', 0.0)
            
            if confidence > 0.5:  # Only include high confidence entities
                structured_data[entity_type] = {
                    'value': entity_text,
                    'confidence': confidence
                }
        
        # Document-specific parsing
        if document_type == 'payslip':
            structured_data.update(self._parse_payslip_entities(entities))
        elif document_type == 'bank_statement':
            structured_data.update(self._parse_bank_statement_entities(entities))
        elif document_type == 'id_proof':
            structured_data.update(self._parse_id_entities(entities))
        
        return structured_data
    
    def _parse_payslip_entities(self, entities: list) -> Dict[str, Any]:
        """Parse payslip-specific entities"""
        
        payslip_data = {}
        
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            entity_text = entity.get('mentionText', '')
            
            if 'salary' in entity_type or 'gross_pay' in entity_type:
                payslip_data['gross_salary'] = entity_text
            elif 'net_pay' in entity_type:
                payslip_data['net_salary'] = entity_text
            elif 'date' in entity_type:
                payslip_data['pay_date'] = entity_text
            elif 'employee' in entity_type or 'name' in entity_type:
                payslip_data['employee_name'] = entity_text
            elif 'employer' in entity_type or 'company' in entity_type:
                payslip_data['employer_name'] = entity_text
        
        return payslip_data
    
    def _parse_bank_statement_entities(self, entities: list) -> Dict[str, Any]:
        """Parse bank statement-specific entities"""
        
        bank_data = {}
        
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            entity_text = entity.get('mentionText', '')
            
            if 'account' in entity_type and 'number' in entity_type:
                bank_data['account_number'] = entity_text
            elif 'balance' in entity_type:
                bank_data['account_balance'] = entity_text
            elif 'bank' in entity_type and 'name' in entity_type:
                bank_data['bank_name'] = entity_text
            elif 'statement_date' in entity_type:
                bank_data['statement_date'] = entity_text
        
        return bank_data
    
    def _parse_id_entities(self, entities: list) -> Dict[str, Any]:
        """Parse ID document-specific entities"""
        
        id_data = {}
        
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            entity_text = entity.get('mentionText', '')
            
            if 'name' in entity_type:
                id_data['full_name'] = entity_text
            elif 'id_number' in entity_type or 'license_number' in entity_type:
                id_data['id_number'] = entity_text
            elif 'date_of_birth' in entity_type:
                id_data['date_of_birth'] = entity_text
            elif 'expiry' in entity_type or 'expiration' in entity_type:
                id_data['expiry_date'] = entity_text
            elif 'address' in entity_type:
                id_data['address'] = entity_text
        
        return id_data
    
    def _extract_structured_data_patterns(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract structured data using pattern matching (fallback method)"""
        
        import re
        
        structured_data = {}
        text_lower = text.lower()
        
        # Common patterns
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\d{2,4}[-/]\d{1,2}[-/]\d{1,2}',
            r'\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4}\b'
        ]
        
        amount_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$'
        ]
        
        # Extract dates
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        if dates:
            structured_data['dates_found'] = dates
        
        # Extract amounts
        amounts = []
        for pattern in amount_patterns:
            amounts.extend(re.findall(pattern, text))
        
        if amounts:
            structured_data['amounts_found'] = amounts
        
        # Document-specific patterns
        if document_type == 'payslip':
            # Look for salary-related keywords
            salary_keywords = ['gross pay', 'net pay', 'basic salary', 'total earnings']
            for keyword in salary_keywords:
                if keyword in text_lower:
                    # Try to find amount near keyword
                    keyword_pos = text_lower.find(keyword)
                    nearby_text = text[max(0, keyword_pos-50):keyword_pos+100]
                    amounts_nearby = []
                    for pattern in amount_patterns:
                        amounts_nearby.extend(re.findall(pattern, nearby_text))
                    if amounts_nearby:
                        structured_data[keyword.replace(' ', '_')] = amounts_nearby[0]
        
        elif document_type == 'bank_statement':
            # Look for account number patterns
            account_patterns = [
                r'\b\d{8,12}\b',  # Simple account number pattern
                r'account.*?(\d{8,12})',
                r'a/c.*?(\d{8,12})'
            ]
            
            for pattern in account_patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    structured_data['account_number'] = matches[0]
                    break
        
        return structured_data
