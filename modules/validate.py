import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from utils.document_types import DOCUMENT_TYPES, VALIDATION_RULES

class DocumentValidator:
    def __init__(self):
        self.validation_rules = VALIDATION_RULES
    
    def validate_document(self, extraction_result: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Validate extracted document data"""
        
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'validation_score': 0.0,
            'missing_fields': [],
            'recommendations': []
        }
        
        try:
            # Get document-specific validation rules
            rules = self.validation_rules.get(document_type, {})
            
            # Validate required fields
            self._validate_required_fields(extraction_result, rules, validation_result)
            
            # Validate document recency
            self._validate_document_recency(extraction_result, document_type, validation_result)
            
            # Validate data formats
            self._validate_data_formats(extraction_result, document_type, validation_result)
            
            # Document-specific validations
            if document_type == 'payslip':
                self._validate_payslip(extraction_result, validation_result)
            elif document_type == 'bank_statement':
                self._validate_bank_statement(extraction_result, validation_result)
            elif document_type == 'id_proof':
                self._validate_id_proof(extraction_result, validation_result)
            elif document_type == 'tax_document':
                self._validate_tax_document(extraction_result, validation_result)
            
            # Calculate overall validation score
            validation_result['validation_score'] = self._calculate_validation_score(validation_result)
            
            # Set overall validity
            validation_result['is_valid'] = (
                len(validation_result['issues']) == 0 and
                validation_result['validation_score'] >= 0.7
            )
            
        except Exception as e:
            logging.error(f"Document validation failed: {str(e)}")
            validation_result['issues'].append(f"Validation error: {str(e)}")
            validation_result['is_valid'] = False
        
        return validation_result
    
    def _validate_required_fields(self, extraction_result: Dict[str, Any], 
                                rules: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate that required fields are present"""
        
        required_fields = rules.get('required_fields', [])
        structured_data = extraction_result.get('structured_data', {})
        
        for field in required_fields:
            if field not in structured_data or not structured_data[field]:
                validation_result['missing_fields'].append(field)
                validation_result['issues'].append(f"Missing required field: {field}")
    
    def _validate_document_recency(self, extraction_result: Dict[str, Any], 
                                 document_type: str, validation_result: Dict[str, Any]):
        """Validate document recency requirements"""
        
        recency_rules = {
            'payslip': 90,  # 3 months
            'bank_statement': 90,  # 3 months
            'utility_bill': 90,  # 3 months
            'employment_letter': 180,  # 6 months
            'tax_document': 365  # 1 year
        }
        
        max_age_days = recency_rules.get(document_type)
        if not max_age_days:
            return
        
        # Find dates in the document
        dates_found = self._extract_dates(extraction_result)
        
        if not dates_found:
            validation_result['warnings'].append(
                f"No date found in {document_type}. Manual verification required."
            )
            return
        
        # Check if any date is recent enough
        recent_enough = False
        current_date = datetime.now()
        cutoff_date = current_date - timedelta(days=max_age_days)
        
        for date_str in dates_found:
            try:
                doc_date = self._parse_date(date_str)
                if doc_date and doc_date >= cutoff_date:
                    recent_enough = True
                    break
            except:
                continue
        
        if not recent_enough:
            validation_result['issues'].append(
                f"{document_type.replace('_', ' ').title()} is older than {max_age_days} days. "
                f"Please provide a more recent document."
            )
            validation_result['recommendations'].append(
                f"Upload a {document_type.replace('_', ' ')} from the last {max_age_days // 30} month(s)"
            )
    
    def _validate_data_formats(self, extraction_result: Dict[str, Any], 
                             document_type: str, validation_result: Dict[str, Any]):
        """Validate data format consistency"""
        
        structured_data = extraction_result.get('structured_data', {})
        
        # Validate email format if present
        for field, value in structured_data.items():
            if 'email' in field.lower() and isinstance(value, (str, dict)):
                email_value = value.get('value', value) if isinstance(value, dict) else value
                if email_value and not self._is_valid_email(email_value):
                    validation_result['warnings'].append(f"Invalid email format: {email_value}")
            
            # Validate phone format if present
            elif 'phone' in field.lower() and isinstance(value, (str, dict)):
                phone_value = value.get('value', value) if isinstance(value, dict) else value
                if phone_value and not self._is_valid_phone(phone_value):
                    validation_result['warnings'].append(f"Invalid phone format: {phone_value}")
    
    def _validate_payslip(self, extraction_result: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate payslip-specific requirements"""
        
        structured_data = extraction_result.get('structured_data', {})
        
        # Check for salary information
        salary_fields = ['gross_salary', 'net_salary', 'basic_salary', 'gross_pay', 'net_pay']
        salary_found = any(field in structured_data for field in salary_fields)
        
        if not salary_found:
            validation_result['issues'].append("No salary information found in payslip")
        
        # Check for employer information
        employer_fields = ['employer_name', 'company', 'company_name']
        employer_found = any(field in structured_data for field in employer_fields)
        
        if not employer_found:
            validation_result['warnings'].append("Employer information not clearly identified")
        
        # Validate salary amounts are reasonable
        for field in salary_fields:
            if field in structured_data:
                salary_value = structured_data[field]
                if isinstance(salary_value, dict):
                    salary_value = salary_value.get('value', '')
                
                # Extract numeric value from salary
                numeric_salary = self._extract_numeric_value(str(salary_value))
                if numeric_salary:
                    if numeric_salary < 100:  # Unreasonably low
                        validation_result['warnings'].append(f"Salary amount seems unusually low: {salary_value}")
                    elif numeric_salary > 1000000:  # Unreasonably high
                        validation_result['warnings'].append(f"Salary amount seems unusually high: {salary_value}")
    
    def _validate_bank_statement(self, extraction_result: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate bank statement-specific requirements"""
        
        structured_data = extraction_result.get('structured_data', {})
        
        # Check for account information
        account_fields = ['account_number', 'account']
        account_found = any(field in structured_data for field in account_fields)
        
        if not account_found:
            validation_result['issues'].append("Account number not found in bank statement")
        
        # Check for balance information
        balance_fields = ['account_balance', 'balance', 'closing_balance']
        balance_found = any(field in structured_data for field in balance_fields)
        
        if not balance_found:
            validation_result['warnings'].append("Account balance information not clearly identified")
        
        # Check for bank name
        bank_fields = ['bank_name', 'bank', 'financial_institution']
        bank_found = any(field in structured_data for field in bank_fields)
        
        if not bank_found:
            validation_result['warnings'].append("Bank name not clearly identified")
    
    def _validate_id_proof(self, extraction_result: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate ID proof-specific requirements"""
        
        structured_data = extraction_result.get('structured_data', {})
        
        # Check for name
        name_fields = ['full_name', 'name', 'first_name', 'last_name']
        name_found = any(field in structured_data for field in name_fields)
        
        if not name_found:
            validation_result['issues'].append("Name not found in ID document")
        
        # Check for ID number
        id_fields = ['id_number', 'license_number', 'passport_number', 'ssn']
        id_found = any(field in structured_data for field in id_fields)
        
        if not id_found:
            validation_result['issues'].append("ID number not found in document")
        
        # Check for expiry date
        expiry_fields = ['expiry_date', 'expiration_date', 'valid_until']
        expiry_found = any(field in structured_data for field in expiry_fields)
        
        if expiry_found:
            # Validate that ID is not expired
            for field in expiry_fields:
                if field in structured_data:
                    expiry_value = structured_data[field]
                    if isinstance(expiry_value, dict):
                        expiry_value = expiry_value.get('value', '')
                    
                    try:
                        expiry_date = self._parse_date(str(expiry_value))
                        if expiry_date and expiry_date < datetime.now():
                            validation_result['issues'].append("ID document has expired")
                            break
                    except:
                        continue
    
    def _validate_tax_document(self, extraction_result: Dict[str, Any], validation_result: Dict[str, Any]):
        """Validate tax document-specific requirements"""
        
        structured_data = extraction_result.get('structured_data', {})
        
        # Check for tax year
        dates_found = self._extract_dates(extraction_result)
        current_year = datetime.now().year
        
        # Tax documents should be from recent years (within 3 years)
        valid_year_found = False
        for date_str in dates_found:
            try:
                date_obj = self._parse_date(date_str)
                if date_obj and date_obj.year >= current_year - 3:
                    valid_year_found = True
                    break
            except:
                continue
        
        if not valid_year_found:
            validation_result['warnings'].append("Tax document year could not be verified")
    
    def _extract_dates(self, extraction_result: Dict[str, Any]) -> List[str]:
        """Extract all dates found in the document"""
        
        dates = []
        
        # From structured data
        structured_data = extraction_result.get('structured_data', {})
        for field, value in structured_data.items():
            if 'date' in field.lower():
                date_value = value.get('value', value) if isinstance(value, dict) else value
                if date_value:
                    dates.append(str(date_value))
        
        # From dates_found field (pattern matching fallback)
        if 'dates_found' in structured_data:
            dates.extend(structured_data['dates_found'])
        
        return dates
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        
        date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
            '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y',
            '%d %b %Y', '%d %B %Y', '%b %d, %Y',
            '%B %d, %Y', '%d-%b-%Y', '%d-%B-%Y'
        ]
        
        # Clean the date string
        date_str = re.sub(r'[^\w\s/-]', '', date_str.strip())
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Phone should have 10-15 digits
        return 10 <= len(digits_only) <= 15
    
    def _extract_numeric_value(self, value_str: str) -> Optional[float]:
        """Extract numeric value from string"""
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[\$,€£¥]', '', value_str)
        
        # Find numeric value
        match = re.search(r'\d+(?:\.\d+)?', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return None
    
    def _calculate_validation_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        
        base_score = 1.0
        
        # Deduct for issues
        issue_penalty = len(validation_result['issues']) * 0.2
        warning_penalty = len(validation_result['warnings']) * 0.1
        missing_field_penalty = len(validation_result['missing_fields']) * 0.15
        
        total_penalty = issue_penalty + warning_penalty + missing_field_penalty
        final_score = max(0.0, base_score - total_penalty)
        
        return final_score

    def validate_application_completeness(self, application_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that all required documents for mortgage application are present"""
        
        required_doc_types = [
            'id_proof',
            'payslip',
            'bank_statement',
            'employment_letter'
        ]
        
        optional_doc_types = [
            'tax_document',
            'utility_bill',
            'property_document'
        ]
        
        completeness_result = {
            'is_complete': True,
            'missing_required': [],
            'missing_optional': [],
            'recommendations': [],
            'completeness_score': 0.0
        }
        
        # Get list of uploaded document types
        uploaded_types = [doc.get('document_type') for doc in application_documents]
        
        # Check required documents
        for req_type in required_doc_types:
            if req_type not in uploaded_types:
                completeness_result['missing_required'].append(req_type)
                completeness_result['is_complete'] = False
        
        # Check optional documents
        for opt_type in optional_doc_types:
            if opt_type not in uploaded_types:
                completeness_result['missing_optional'].append(opt_type)
        
        # Generate recommendations
        for missing in completeness_result['missing_required']:
            doc_name = missing.replace('_', ' ').title()
            completeness_result['recommendations'].append(
                f"Please upload your {doc_name} to complete your application"
            )
        
        # Calculate completeness score
        total_required = len(required_doc_types)
        uploaded_required = total_required - len(completeness_result['missing_required'])
        completeness_result['completeness_score'] = uploaded_required / total_required
        
        return completeness_result
