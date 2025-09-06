"""
Modern bank-style document upload interface for mortgage applications
"""

import streamlit as st
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from .batch_processor import BatchDocumentProcessor
from utils.document_types import DOCUMENT_TYPES, MANDATORY_DOCUMENTS
from utils.helpers import validate_file_upload, get_file_icon


class MortgageUploadInterface:
    """Modern, bank-style document upload interface"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.batch_processor = BatchDocumentProcessor(db_manager)
    
    def render(self):
        """Render the main upload interface"""
        
        st.title("🏠 Mortgage Application Document Upload")
        st.markdown("**Upload all your documents at once for faster processing**")
        
        # Progress indicator
        self._render_progress_steps()
        
        # Application information section
        with st.container():
            st.markdown("### 📋 Application Information")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                borrower_info = self._collect_borrower_information()
            
            with col2:
                application_id = self._handle_application_id()
        
        st.divider()
        
        # Document upload section
        with st.container():
            st.markdown("### 📎 Document Upload")
            
            # Document requirements info
            self._show_document_requirements()
            
            # Bulk file upload
            uploaded_files = self._render_file_upload()
            
            if uploaded_files:
                # Document classification and organization
                document_mapping = self._organize_uploaded_documents(uploaded_files)
                
                # Processing options
                processing_options = self._render_processing_options()
                
                # Final review and submit
                if st.button("🚀 Process All Documents", type="primary", use_container_width=True):
                    if self._validate_submission(borrower_info, document_mapping):
                        self._process_application_batch(
                            application_id, uploaded_files, document_mapping, 
                            borrower_info, processing_options
                        )
    
    def _render_progress_steps(self):
        """Render progress steps indicator"""
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**1. 📋 Information**")
            st.markdown("✅ Current Step")
        
        with col2:
            st.markdown("**2. 📎 Upload**")
            st.markdown("⏳ Next")
        
        with col3:
            st.markdown("**3. 🔍 Review**")
            st.markdown("⏳ Pending")
        
        with col4:
            st.markdown("**4. ✨ Processing**")
            st.markdown("⏳ Pending")
    
    def _collect_borrower_information(self) -> Dict[str, Any]:
        """Collect borrower information"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            borrower_name = st.text_input(
                "Full Name *", 
                placeholder="Enter your full legal name",
                key="borrower_name"
            )
            borrower_email = st.text_input(
                "Email Address *", 
                placeholder="your.email@example.com",
                key="borrower_email"
            )
        
        with col2:
            borrower_phone = st.text_input(
                "Phone Number *", 
                placeholder="+1 (555) 123-4567",
                key="borrower_phone"
            )
            loan_amount = st.number_input(
                "Loan Amount Requested *", 
                min_value=0, 
                step=1000,
                format="%d",
                key="loan_amount"
            )
        
        return {
            'borrower_name': borrower_name,
            'borrower_email': borrower_email,
            'borrower_phone': borrower_phone,
            'loan_amount': loan_amount
        }
    
    def _handle_application_id(self) -> str:
        """Handle application ID generation or input"""
        
        st.markdown("**Application ID**")
        
        # Option to use existing application ID
        use_existing = st.checkbox("I have an existing application ID")
        
        if use_existing:
            application_id = st.text_input(
                "Enter Application ID",
                placeholder="APP-1234-ABCD5678",
                key="existing_app_id"
            )
            if not application_id:
                st.warning("Please enter your existing application ID")
        else:
            # Generate new application ID
            if 'new_application_id' not in st.session_state:
                st.session_state.new_application_id = self._generate_application_id()
            
            application_id = st.session_state.new_application_id
            st.info(f"**New Application ID:** `{application_id}`")
            st.caption("Save this ID for future reference")
        
        return application_id or ""
    
    def _show_document_requirements(self):
        """Show document requirements and guidelines"""
        
        with st.expander("📋 Document Requirements & Guidelines", expanded=False):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Required Documents:**")
                for doc_type in MANDATORY_DOCUMENTS:
                    doc_info = DOCUMENT_TYPES[doc_type]
                    st.markdown(f"• **{doc_info['name']}** - {doc_info['description']}")
            
            with col2:
                st.markdown("**Upload Guidelines:**")
                st.markdown("""
                • **File formats:** PDF, JPG, PNG, TIFF
                • **File size:** Maximum 10 MB per file
                • **Quality:** Ensure documents are clear and readable
                • **Recency:** Bank statements and payslips should be from last 3 months
                • **Completeness:** Upload all pages of multi-page documents
                """)
    
    def _render_file_upload(self) -> Optional[List]:
        """Render the bulk file upload interface"""
        
        st.markdown("**Select all your documents at once:**")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png', 'tiff'],
            help="You can select multiple files at once. Hold Ctrl/Cmd to select multiple files.",
            key="bulk_upload"
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} files selected")
            
            # Show file summary
            with st.expander("📄 Uploaded Files Summary", expanded=True):
                for i, file in enumerate(uploaded_files, 1):
                    file_icon = get_file_icon(file.name.split('.')[-1])
                    file_size_mb = len(file.getbuffer()) / (1024 * 1024)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"{file_icon} **{file.name}**")
                    
                    with col2:
                        st.markdown(f"{file_size_mb:.1f} MB")
                    
                    with col3:
                        # Validation status
                        validation = validate_file_upload(file)
                        if validation['is_valid']:
                            st.success("✅ Valid")
                        else:
                            st.error("❌ Issues")
                            for error in validation['errors']:
                                st.caption(f"⚠️ {error}")
        
        return uploaded_files
    
    def _organize_uploaded_documents(self, uploaded_files: List) -> Dict[str, str]:
        """Organize and classify uploaded documents"""
        
        st.markdown("### 🏷️ Document Classification")
        st.markdown("Help us identify your documents for better processing:")
        
        document_mapping = {}
        
        # Create columns for better layout
        for i, uploaded_file in enumerate(uploaded_files):
            with st.container():
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    file_icon = get_file_icon(uploaded_file.name.split('.')[-1])
                    st.markdown(f"{file_icon} **{uploaded_file.name}**")
                
                with col2:
                    # Auto-suggest document type based on filename
                    suggested_type = self._suggest_document_type(uploaded_file.name)
                    
                    doc_type = st.selectbox(
                        "Document Type",
                        options=list(DOCUMENT_TYPES.keys()),
                        index=list(DOCUMENT_TYPES.keys()).index(suggested_type) if suggested_type in DOCUMENT_TYPES else 0,
                        key=f"doc_type_{i}",
                        format_func=lambda x: DOCUMENT_TYPES[x]['name']
                    )
                    
                    document_mapping[uploaded_file.name] = doc_type
        
        return document_mapping
    
    def _suggest_document_type(self, filename: str) -> str:
        """Suggest document type based on filename"""
        
        filename_lower = filename.lower()
        
        # Simple keyword matching
        if any(term in filename_lower for term in ['payslip', 'salary', 'pay_stub', 'wage']):
            return 'payslip'
        elif any(term in filename_lower for term in ['bank', 'statement', 'account']):
            return 'bank_statement'
        elif any(term in filename_lower for term in ['id', 'passport', 'license', 'identity']):
            return 'id_proof'
        elif any(term in filename_lower for term in ['tax', '1040', 'return', 'w2']):
            return 'tax_document'
        elif any(term in filename_lower for term in ['employment', 'job', 'work']):
            return 'employment_letter'
        elif any(term in filename_lower for term in ['utility', 'electric', 'gas', 'water']):
            return 'utility_bill'
        else:
            return 'payslip'  # Default
    
    def _render_processing_options(self) -> Dict[str, bool]:
        """Render processing options"""
        
        st.markdown("### ⚙️ Processing Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_validate = st.checkbox(
                "🔍 Auto-validate documents", 
                value=True,
                help="Automatically check document requirements and recency"
            )
            
            extract_entities = st.checkbox(
                "📊 Extract key information", 
                value=True,
                help="Extract important data like amounts, dates, and names"
            )
        
        with col2:
            generate_summary = st.checkbox(
                "📝 Generate AI summaries", 
                value=True,
                help="Create intelligent summaries of each document"
            )
            
            fraud_detection = st.checkbox(
                "🛡️ Fraud detection", 
                value=True,
                help="Analyze documents for potential fraud indicators"
            )
        
        return {
            'auto_validate': auto_validate,
            'extract_entities': extract_entities,
            'generate_summary': generate_summary,
            'fraud_detection': fraud_detection
        }
    
    def _validate_submission(self, borrower_info: Dict[str, Any], 
                           document_mapping: Dict[str, str]) -> bool:
        """Validate submission before processing"""
        
        errors = []
        
        # Validate borrower information
        required_fields = ['borrower_name', 'borrower_email', 'borrower_phone', 'loan_amount']
        for field in required_fields:
            if not borrower_info.get(field):
                field_name = field.replace('_', ' ').title()
                errors.append(f"{field_name} is required")
        
        # Validate email format
        if borrower_info.get('borrower_email'):
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, borrower_info['borrower_email']):
                errors.append("Please enter a valid email address")
        
        # Check for required documents
        uploaded_types = set(document_mapping.values())
        missing_required = set(MANDATORY_DOCUMENTS) - uploaded_types
        
        if missing_required:
            missing_names = [DOCUMENT_TYPES[doc_type]['name'] for doc_type in missing_required]
            errors.append(f"Missing required documents: {', '.join(missing_names)}")
        
        # Display errors
        if errors:
            st.error("Please fix the following issues before submitting:")
            for error in errors:
                st.error(f"• {error}")
            return False
        
        return True
    
    def _process_application_batch(self, application_id: str, uploaded_files: List,
                                 document_mapping: Dict[str, str], borrower_info: Dict[str, Any],
                                 processing_options: Dict[str, bool]):
        """Process the complete application batch"""
        
        # Show processing progress
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🚀 Processing Your Application")
            
            # Create progress elements
            overall_progress = st.progress(0)
            status_text = st.empty()
            results_container = st.empty()
            
            # Update progress
            status_text.text("Starting batch processing...")
            overall_progress.progress(10)
            
            try:
                # Process the batch
                batch_result = self.batch_processor.process_application_batch(
                    application_id=application_id,
                    uploaded_files=uploaded_files,
                    document_types=document_mapping,
                    borrower_info=borrower_info,
                    processing_options=processing_options
                )
                
                # Update progress
                overall_progress.progress(100)
                status_text.text("✅ Processing completed!")
                
                # Display results
                self._display_batch_results(batch_result, results_container)
                
            except Exception as e:
                st.error(f"Processing failed: {str(e)}")
                overall_progress.progress(0)
                status_text.text("❌ Processing failed")
    
    def _display_batch_results(self, batch_result: Dict[str, Any], container):
        """Display batch processing results"""
        
        with container:
            st.success("🎉 Your mortgage application has been processed successfully!")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Documents", batch_result['total_documents'])
            
            with col2:
                st.metric("Successfully Processed", batch_result['successful_documents'])
            
            with col3:
                st.metric("Processing Time", f"{batch_result['processing_time']:.1f}s")
            
            with col4:
                completion_rate = (batch_result['successful_documents'] / batch_result['total_documents']) * 100
                st.metric("Success Rate", f"{completion_rate:.0f}%")
            
            # Application analysis
            if batch_result.get('application_analysis'):
                analysis = batch_result['application_analysis']
                
                st.markdown("### 📊 Application Analysis")
                
                if analysis.get('summary'):
                    st.info(f"**Summary:** {analysis['summary']}")
                
                if analysis.get('risk_assessment'):
                    risk = analysis['risk_assessment']
                    risk_level = risk.get('risk_level', 'unknown')
                    
                    if risk_level == 'low':
                        st.success(f"✅ **Risk Assessment:** Low Risk - {risk.get('reason', '')}")
                    elif risk_level == 'medium':
                        st.warning(f"⚠️ **Risk Assessment:** Medium Risk - {risk.get('reason', '')}")
                    else:
                        st.error(f"🚨 **Risk Assessment:** High Risk - {risk.get('reason', '')}")
                
                if analysis.get('recommendations'):
                    st.markdown("**Recommendations:**")
                    for rec in analysis['recommendations']:
                        st.markdown(f"• {rec}")
            
            # Validation summary
            if batch_result.get('validation_summary'):
                validation = batch_result['validation_summary']
                
                st.markdown("### ✅ Application Completeness")
                
                if validation.get('is_complete'):
                    st.success("🎉 Your application is complete!")
                else:
                    st.warning("⚠️ Your application needs attention")
                
                if validation.get('missing_required'):
                    st.markdown("**Missing Required Documents:**")
                    for missing in validation['missing_required']:
                        doc_name = DOCUMENT_TYPES.get(missing, {}).get('name', missing)
                        st.error(f"• {doc_name}")
                
                if validation.get('recommendations'):
                    st.markdown("**Next Steps:**")
                    for rec in validation['recommendations']:
                        st.info(f"• {rec}")
            
            # Application ID reminder
            st.markdown("---")
            st.info(f"📝 **Your Application ID:** `{batch_result['application_id']}` - Save this for future reference!")
    
    def _generate_application_id(self) -> str:
        """Generate a unique application ID"""
        
        # Format: APP-MMDD-XXXXXXXX
        timestamp = datetime.now().strftime("%m%d")
        unique_part = str(uuid.uuid4())[:8].upper()
        
        return f"APP-{timestamp}-{unique_part}"