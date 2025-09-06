import streamlit as st
import os
from datetime import datetime
import uuid
from typing import List, Dict, Any
from .extract import DocumentExtractor
from .validate import DocumentValidator
from .ai_processor import AIProcessor
from utils.document_types import DOCUMENT_TYPES, get_document_category
from utils.helpers import save_uploaded_file, get_file_hash

class UploadModule:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.extractor = DocumentExtractor()
        self.validator = DocumentValidator()
        self.ai_processor = AIProcessor()
    
    def render(self):
        """Render the document upload interface"""
        st.title("📄 Document Upload")
        st.markdown("Upload your mortgage-related documents for automated processing and validation.")
        
        # Application ID input
        col1, col2 = st.columns([2, 1])
        with col1:
            application_id = st.text_input(
                "Application ID (Optional)",
                placeholder="Enter existing application ID or leave blank for new application",
                help="If you have an existing application, enter its ID to add documents"
            )
        
        with col2:
            if st.button("Generate New ID"):
                new_id = str(uuid.uuid4())[:8].upper()
                st.session_state.generated_app_id = new_id
                st.success(f"New Application ID: {new_id}")
        
        if not application_id and 'generated_app_id' in st.session_state:
            application_id = st.session_state.generated_app_id
            st.info(f"Using generated Application ID: {application_id}")
        
        # Borrower details
        st.subheader("👤 Borrower Information")
        col1, col2 = st.columns(2)
        
        with col1:
            borrower_name = st.text_input("Full Name*", key="borrower_name")
            borrower_email = st.text_input("Email Address*", key="borrower_email")
        
        with col2:
            borrower_phone = st.text_input("Phone Number*", key="borrower_phone")
            loan_amount = st.number_input("Requested Loan Amount*", min_value=0, key="loan_amount")
        
        # Document upload section
        st.subheader("📎 Document Upload")
        
        # Document type selection
        doc_type = st.selectbox(
            "Document Type",
            options=list(DOCUMENT_TYPES.keys()),
            help="Select the type of document you're uploading"
        )
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png', 'tiff'],
            help="Supported formats: PDF, JPG, PNG, TIFF"
        )
        
        # Processing options
        st.subheader("⚙️ Processing Options")
        col1, col2 = st.columns(2)
        
        with col1:
            auto_validate = st.checkbox("Auto-validate documents", value=True)
            generate_summary = st.checkbox("Generate AI summary", value=True)
        
        with col2:
            extract_entities = st.checkbox("Extract key information", value=True)
            fraud_detection = st.checkbox("Enable fraud detection", value=True)
        
        # Process documents
        if st.button("Process Documents", type="primary"):
            if not all([borrower_name, borrower_email, borrower_phone, loan_amount]):
                st.error("Please fill in all required borrower information fields.")
                return
            
            if not uploaded_files:
                st.error("Please upload at least one document.")
                return
            
            if not application_id:
                application_id = str(uuid.uuid4())[:8].upper()
            
            # Process each uploaded file
            with st.spinner("Processing documents..."):
                results = []
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    
                    # Save uploaded file
                    file_path = save_uploaded_file(uploaded_file, application_id)
                    file_hash = get_file_hash(file_path)
                    
                    # Process document
                    result = self._process_document(
                        file_path, uploaded_file.name, doc_type, application_id,
                        auto_validate, generate_summary, extract_entities, fraud_detection
                    )
                    
                    # Store in database
                    document_data = {
                        'application_id': application_id,
                        'document_type': doc_type,
                        'filename': uploaded_file.name,
                        'file_path': file_path,
                        'file_hash': file_hash,
                        'upload_timestamp': datetime.now(),
                        'borrower_name': borrower_name,
                        'borrower_email': borrower_email,
                        'borrower_phone': borrower_phone,
                        'loan_amount': loan_amount,
                        'processing_result': result
                    }
                    
                    self.db_manager.store_document(document_data)
                    results.append(result)
                
                progress_bar.progress(1.0)
                st.success(f"Successfully processed {len(uploaded_files)} document(s)!")
                
                # Display results
                self._display_results(results, application_id)
    
    def _process_document(self, file_path: str, filename: str, doc_type: str, 
                         application_id: str, auto_validate: bool, generate_summary: bool,
                         extract_entities: bool, fraud_detection: bool) -> Dict[str, Any]:
        """Process a single document through the pipeline"""
        
        result = {
            'filename': filename,
            'document_type': doc_type,
            'status': 'processing',
            'extraction_result': None,
            'validation_result': None,
            'ai_analysis': None,
            'errors': []
        }
        
        try:
            # Extract text and data
            if extract_entities:
                extraction_result = self.extractor.extract_document_data(file_path, doc_type)
                result['extraction_result'] = extraction_result
                
                if extraction_result.get('error'):
                    result['errors'].append(f"Extraction error: {extraction_result['error']}")
            
            # Validate document
            if auto_validate and result['extraction_result']:
                validation_result = self.validator.validate_document(
                    result['extraction_result'], doc_type
                )
                result['validation_result'] = validation_result
            
            # AI analysis
            if generate_summary or fraud_detection:
                ai_analysis = self.ai_processor.analyze_document(
                    file_path, doc_type, result.get('extraction_result'),
                    generate_summary, fraud_detection
                )
                result['ai_analysis'] = ai_analysis
            
            result['status'] = 'completed'
            
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Processing error: {str(e)}")
        
        return result
    
    def _display_results(self, results: List[Dict[str, Any]], application_id: str):
        """Display processing results"""
        
        st.subheader("📊 Processing Results")
        st.info(f"Application ID: **{application_id}**")
        
        # Summary metrics
        total_docs = len(results)
        successful_docs = len([r for r in results if r['status'] == 'completed'])
        error_docs = total_docs - successful_docs
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", total_docs)
        with col2:
            st.metric("Successfully Processed", successful_docs)
        with col3:
            st.metric("Errors", error_docs)
        
        # Detailed results
        for i, result in enumerate(results):
            with st.expander(f"📄 {result['filename']} - {result['status'].title()}"):
                
                # Status indicator
                if result['status'] == 'completed':
                    st.success("✅ Processing completed successfully")
                else:
                    st.error("❌ Processing failed")
                    for error in result['errors']:
                        st.error(error)
                
                # Extraction results
                if result.get('extraction_result'):
                    st.subheader("🔍 Extracted Information")
                    extraction = result['extraction_result']
                    
                    if extraction.get('text_content'):
                        st.text_area("Extracted Text (Preview)", 
                                   extraction['text_content'][:500] + "...", 
                                   height=100)
                    
                    if extraction.get('structured_data'):
                        st.json(extraction['structured_data'])
                
                # Validation results
                if result.get('validation_result'):
                    st.subheader("✅ Validation Results")
                    validation = result['validation_result']
                    
                    if validation.get('is_valid'):
                        st.success("Document validation passed")
                    else:
                        st.warning("Document validation issues found")
                    
                    if validation.get('issues'):
                        for issue in validation['issues']:
                            st.warning(f"⚠️ {issue}")
                
                # AI analysis
                if result.get('ai_analysis'):
                    st.subheader("🤖 AI Analysis")
                    ai_analysis = result['ai_analysis']
                    
                    if ai_analysis.get('summary'):
                        st.markdown("**Document Summary:**")
                        st.write(ai_analysis['summary'])
                    
                    if ai_analysis.get('risk_assessment'):
                        risk = ai_analysis['risk_assessment']
                        if risk.get('risk_level') == 'high':
                            st.error(f"🚨 High Risk: {risk.get('reason', 'Unknown')}")
                        elif risk.get('risk_level') == 'medium':
                            st.warning(f"⚠️ Medium Risk: {risk.get('reason', 'Unknown')}")
                        else:
                            st.success("✅ Low Risk Document")
                    
                    if ai_analysis.get('recommendations'):
                        st.markdown("**AI Recommendations:**")
                        for rec in ai_analysis['recommendations']:
                            st.info(f"💡 {rec}")
