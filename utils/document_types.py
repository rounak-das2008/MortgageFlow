"""
Document type definitions and validation rules for mortgage application processing
"""

from typing import Dict, List, Any

# Document type definitions with their requirements
DOCUMENT_TYPES = {
    'id_proof': {
        'name': 'ID Proof',
        'description': 'Government-issued identification document',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Passport', 'Driver License', 'National ID Card', 'State ID'],
        'required': True,
        'max_age_days': None,  # IDs don't expire for our purposes (we check expiry date)
        'category': 'identity'
    },
    'payslip': {
        'name': 'Payslip',
        'description': 'Recent salary statement from employer',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Monthly Pay Stub', 'Salary Statement', 'Wage Slip'],
        'required': True,
        'max_age_days': 90,  # 3 months
        'category': 'income'
    },
    'bank_statement': {
        'name': 'Bank Statement',
        'description': 'Recent bank account statement',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Monthly Bank Statement', 'Account Summary'],
        'required': True,
        'max_age_days': 90,  # 3 months
        'category': 'financial'
    },
    'employment_letter': {
        'name': 'Employment Letter',
        'description': 'Letter from employer confirming employment',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Employment Verification Letter', 'Job Confirmation Letter'],
        'required': True,
        'max_age_days': 180,  # 6 months
        'category': 'employment'
    },
    'tax_document': {
        'name': 'Tax Document',
        'description': 'Tax return or tax assessment document',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Tax Return', 'Tax Assessment', 'Form 1040', 'Tax Certificate'],
        'required': False,
        'max_age_days': 365,  # 1 year
        'category': 'financial'
    },
    'utility_bill': {
        'name': 'Utility Bill',
        'description': 'Recent utility bill for address verification',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Electricity Bill', 'Water Bill', 'Gas Bill', 'Internet Bill'],
        'required': False,
        'max_age_days': 90,  # 3 months
        'category': 'address_proof'
    },
    'property_document': {
        'name': 'Property Document',
        'description': 'Property-related documentation',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Property Deed', 'Sale Agreement', 'Property Valuation'],
        'required': False,
        'max_age_days': 365,  # 1 year
        'category': 'property'
    },
    'credit_report': {
        'name': 'Credit Report',
        'description': 'Credit history and score report',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Credit Bureau Report', 'FICO Score Report'],
        'required': False,
        'max_age_days': 30,  # 1 month
        'category': 'financial'
    },
    'investment_statement': {
        'name': 'Investment Statement',
        'description': 'Investment portfolio or asset statement',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Brokerage Statement', 'Mutual Fund Statement', '401k Statement'],
        'required': False,
        'max_age_days': 90,  # 3 months
        'category': 'financial'
    },
    'self_employment_proof': {
        'name': 'Self-Employment Proof',
        'description': 'Documentation proving self-employment income',
        'accepted_formats': ['pdf', 'jpg', 'jpeg', 'png'],
        'examples': ['Business License', 'Profit & Loss Statement', 'Business Tax Return'],
        'required': False,
        'max_age_days': 365,  # 1 year
        'category': 'income'
    }
}

# Validation rules for different document types
VALIDATION_RULES = {
    'id_proof': {
        'required_fields': ['full_name', 'id_number'],
        'optional_fields': ['date_of_birth', 'address', 'expiry_date'],
        'validation_checks': [
            'name_consistency',
            'expiry_date_check',
            'document_authenticity'
        ],
        'quality_requirements': {
            'min_confidence': 0.7,
            'min_resolution': 300,
            'required_elements': ['photo', 'signature', 'official_seal']
        }
    },
    'payslip': {
        'required_fields': ['employee_name', 'employer_name', 'pay_date', 'gross_salary'],
        'optional_fields': ['net_salary', 'deductions', 'employee_id', 'pay_period'],
        'validation_checks': [
            'date_recency',
            'salary_reasonableness',
            'employer_verification',
            'calculation_accuracy'
        ],
        'quality_requirements': {
            'min_confidence': 0.6,
            'required_elements': ['company_logo', 'pay_breakdown', 'totals']
        }
    },
    'bank_statement': {
        'required_fields': ['account_holder_name', 'account_number', 'statement_date'],
        'optional_fields': ['bank_name', 'account_balance', 'transactions', 'opening_balance', 'closing_balance'],
        'validation_checks': [
            'date_recency',
            'account_consistency',
            'balance_verification',
            'transaction_patterns'
        ],
        'quality_requirements': {
            'min_confidence': 0.6,
            'required_elements': ['bank_header', 'account_details', 'transaction_history']
        }
    },
    'employment_letter': {
        'required_fields': ['employee_name', 'employer_name', 'job_title', 'employment_date'],
        'optional_fields': ['salary_info', 'employment_type', 'supervisor_contact'],
        'validation_checks': [
            'employer_authenticity',
            'letterhead_verification',
            'contact_verification',
            'employment_consistency'
        ],
        'quality_requirements': {
            'min_confidence': 0.7,
            'required_elements': ['company_letterhead', 'official_signature', 'contact_info']
        }
    },
    'tax_document': {
        'required_fields': ['taxpayer_name', 'tax_year', 'total_income'],
        'optional_fields': ['filing_status', 'deductions', 'tax_owed', 'refund_amount'],
        'validation_checks': [
            'tax_year_validity',
            'income_consistency',
            'filing_status_check',
            'calculation_verification'
        ],
        'quality_requirements': {
            'min_confidence': 0.7,
            'required_elements': ['official_forms', 'signatures', 'tax_authority_marks']
        }
    },
    'utility_bill': {
        'required_fields': ['account_holder_name', 'service_address', 'bill_date'],
        'optional_fields': ['utility_company', 'account_number', 'amount_due', 'service_period'],
        'validation_checks': [
            'date_recency',
            'address_verification',
            'utility_company_verification'
        ],
        'quality_requirements': {
            'min_confidence': 0.6,
            'required_elements': ['company_logo', 'service_address', 'billing_details']
        }
    },
    'property_document': {
        'required_fields': ['property_address', 'owner_name', 'document_type'],
        'optional_fields': ['property_value', 'deed_number', 'registration_date'],
        'validation_checks': [
            'property_ownership',
            'document_authenticity',
            'legal_verification'
        ],
        'quality_requirements': {
            'min_confidence': 0.8,
            'required_elements': ['official_seals', 'legal_signatures', 'property_details']
        }
    },
    'credit_report': {
        'required_fields': ['report_holder_name', 'report_date', 'credit_score'],
        'optional_fields': ['credit_history', 'account_details', 'inquiry_history'],
        'validation_checks': [
            'report_recency',
            'bureau_authenticity',
            'score_validity'
        ],
        'quality_requirements': {
            'min_confidence': 0.7,
            'required_elements': ['bureau_header', 'score_details', 'account_summary']
        }
    },
    'investment_statement': {
        'required_fields': ['account_holder_name', 'statement_date', 'account_value'],
        'optional_fields': ['investment_details', 'gains_losses', 'account_number'],
        'validation_checks': [
            'statement_recency',
            'institution_verification',
            'value_consistency'
        ],
        'quality_requirements': {
            'min_confidence': 0.6,
            'required_elements': ['institution_header', 'account_summary', 'holdings_detail']
        }
    },
    'self_employment_proof': {
        'required_fields': ['business_name', 'owner_name', 'income_amount'],
        'optional_fields': ['business_address', 'license_number', 'business_type'],
        'validation_checks': [
            'business_verification',
            'income_documentation',
            'license_validity'
        ],
        'quality_requirements': {
            'min_confidence': 0.7,
            'required_elements': ['business_details', 'financial_summary', 'official_documentation']
        }
    }
}

# Document categories for organization
DOCUMENT_CATEGORIES = {
    'identity': {
        'name': 'Identity Verification',
        'description': 'Documents that verify the borrower\'s identity',
        'icon': '👤',
        'priority': 1
    },
    'income': {
        'name': 'Income Verification',
        'description': 'Documents that verify the borrower\'s income',
        'icon': '💰',
        'priority': 2
    },
    'employment': {
        'name': 'Employment Verification',
        'description': 'Documents that verify the borrower\'s employment status',
        'icon': '🏢',
        'priority': 3
    },
    'financial': {
        'name': 'Financial Documents',
        'description': 'Documents showing financial status and history',
        'icon': '📊',
        'priority': 4
    },
    'address_proof': {
        'name': 'Address Verification',
        'description': 'Documents that verify the borrower\'s address',
        'icon': '🏠',
        'priority': 5
    },
    'property': {
        'name': 'Property Documents',
        'description': 'Documents related to the property being financed',
        'icon': '🏘️',
        'priority': 6
    }
}

# Mandatory documents for mortgage application
MANDATORY_DOCUMENTS = [
    'id_proof',
    'payslip',
    'bank_statement',
    'employment_letter'
]

# Optional but recommended documents
RECOMMENDED_DOCUMENTS = [
    'tax_document',
    'utility_bill',
    'credit_report'
]

# Document processing priorities (higher number = higher priority)
PROCESSING_PRIORITIES = {
    'id_proof': 10,
    'payslip': 9,
    'employment_letter': 8,
    'bank_statement': 7,
    'tax_document': 6,
    'credit_report': 5,
    'utility_bill': 4,
    'property_document': 3,
    'investment_statement': 2,
    'self_employment_proof': 1
}

def get_document_category(document_type: str) -> str:
    """Get the category of a document type"""
    doc_info = DOCUMENT_TYPES.get(document_type, {})
    return doc_info.get('category', 'unknown')

def get_required_documents() -> List[str]:
    """Get list of required document types"""
    return [doc_type for doc_type, info in DOCUMENT_TYPES.items() if info.get('required', False)]

def get_optional_documents() -> List[str]:
    """Get list of optional document types"""
    return [doc_type for doc_type, info in DOCUMENT_TYPES.items() if not info.get('required', True)]

def get_documents_by_category(category: str) -> List[str]:
    """Get all document types in a specific category"""
    return [doc_type for doc_type, info in DOCUMENT_TYPES.items() 
            if info.get('category') == category]

def is_document_required(document_type: str) -> bool:
    """Check if a document type is required"""
    return DOCUMENT_TYPES.get(document_type, {}).get('required', False)

def get_document_max_age(document_type: str) -> int:
    """Get maximum age in days for a document type"""
    return DOCUMENT_TYPES.get(document_type, {}).get('max_age_days', 365)

def get_accepted_formats(document_type: str) -> List[str]:
    """Get accepted file formats for a document type"""
    return DOCUMENT_TYPES.get(document_type, {}).get('accepted_formats', ['pdf'])

def get_document_display_name(document_type: str) -> str:
    """Get the display name for a document type"""
    return DOCUMENT_TYPES.get(document_type, {}).get('name', document_type.replace('_', ' ').title())

def get_document_description(document_type: str) -> str:
    """Get the description for a document type"""
    return DOCUMENT_TYPES.get(document_type, {}).get('description', '')

def get_document_examples(document_type: str) -> List[str]:
    """Get examples for a document type"""
    return DOCUMENT_TYPES.get(document_type, {}).get('examples', [])

def validate_document_type(document_type: str) -> bool:
    """Validate if a document type is supported"""
    return document_type in DOCUMENT_TYPES

def get_category_info(category: str) -> Dict[str, Any]:
    """Get information about a document category"""
    return DOCUMENT_CATEGORIES.get(category, {})

def get_all_categories() -> Dict[str, Dict[str, Any]]:
    """Get all document categories"""
    return DOCUMENT_CATEGORIES

def get_processing_priority(document_type: str) -> int:
    """Get processing priority for a document type"""
    return PROCESSING_PRIORITIES.get(document_type, 0)

def sort_documents_by_priority(document_types: List[str]) -> List[str]:
    """Sort document types by processing priority"""
    return sorted(document_types, key=get_processing_priority, reverse=True)

def get_validation_requirements(document_type: str) -> Dict[str, Any]:
    """Get validation requirements for a document type"""
    return VALIDATION_RULES.get(document_type, {})

def get_required_fields(document_type: str) -> List[str]:
    """Get required fields for a document type"""
    return VALIDATION_RULES.get(document_type, {}).get('required_fields', [])

def get_optional_fields(document_type: str) -> List[str]:
    """Get optional fields for a document type"""
    return VALIDATION_RULES.get(document_type, {}).get('optional_fields', [])

def get_quality_requirements(document_type: str) -> Dict[str, Any]:
    """Get quality requirements for a document type"""
    return VALIDATION_RULES.get(document_type, {}).get('quality_requirements', {})

def get_validation_checks(document_type: str) -> List[str]:
    """Get validation checks for a document type"""
    return VALIDATION_RULES.get(document_type, {}).get('validation_checks', [])

def is_financial_document(document_type: str) -> bool:
    """Check if document is a financial document"""
    return get_document_category(document_type) == 'financial'

def is_identity_document(document_type: str) -> bool:
    """Check if document is an identity document"""
    return get_document_category(document_type) == 'identity'

def is_income_document(document_type: str) -> bool:
    """Check if document is an income document"""
    return get_document_category(document_type) == 'income'

def get_document_type_suggestions(uploaded_filename: str) -> List[str]:
    """Suggest document types based on filename"""
    filename_lower = uploaded_filename.lower()
    suggestions = []
    
    # Simple keyword matching for suggestions
    keyword_mapping = {
        'payslip': ['payslip', 'salary', 'pay_stub', 'wage'],
        'bank_statement': ['bank', 'statement', 'account'],
        'id_proof': ['id', 'passport', 'license', 'identity'],
        'tax_document': ['tax', '1040', 'return', 'w2'],
        'utility_bill': ['utility', 'electric', 'gas', 'water', 'bill'],
        'employment_letter': ['employment', 'job', 'work', 'employer'],
        'credit_report': ['credit', 'score', 'fico', 'bureau'],
        'property_document': ['property', 'deed', 'title', 'mortgage']
    }
    
    for doc_type, keywords in keyword_mapping.items():
        if any(keyword in filename_lower for keyword in keywords):
            suggestions.append(doc_type)
    
    return suggestions if suggestions else ['payslip']  # Default suggestion

