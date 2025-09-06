import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .ai_processor import AIProcessor

class DashboardModule:
    def __init__(self, db_manager, view_type: str = "assessor"):
        self.db_manager = db_manager
        self.view_type = view_type
        self.ai_processor = AIProcessor()
    
    def render(self):
        """Render the main dashboard"""
        
        if self.view_type == "borrower":
            self._render_borrower_dashboard()
        else:
            self._render_assessor_dashboard()
    
    def _render_borrower_dashboard(self):
        """Render borrower-specific dashboard"""
        
        st.title("📊 My Applications")
        
        # Get borrower's applications (simplified - in real app, filter by user)
        applications = self.db_manager.get_all_applications()
        
        if not applications:
            st.info("No applications found. Upload documents to get started!")
            return
        
        # Application selector
        app_ids = list(set(app['application_id'] for app in applications))
        selected_app = st.selectbox("Select Application", app_ids)
        
        # Filter documents for selected application
        app_documents = [doc for doc in applications if doc['application_id'] == selected_app]
        
        # Display application status
        if selected_app:
            self._display_application_status(app_documents, selected_app)
        
        # Display document list
        self._display_document_list(app_documents, show_details=True)
    
    def _render_assessor_dashboard(self):
        """Render assessor-specific dashboard"""
        
        st.title("🏠 Assessment Dashboard")
        
        # Get all applications
        applications = self.db_manager.get_all_applications()
        
        if not applications:
            st.info("No applications to review.")
            return
        
        # Summary metrics
        self._display_summary_metrics(applications)
        
        # Applications overview
        st.subheader("📋 Applications Overview")
        
        # Group by application ID
        app_groups = {}
        for doc in applications:
            app_id = doc['application_id']
            if app_id not in app_groups:
                app_groups[app_id] = []
            app_groups[app_id].append(doc)
        
        # Display applications table
        self._display_applications_table(app_groups)
        
        # Detailed view
        if st.checkbox("Show Detailed View"):
            selected_app = st.selectbox(
                "Select Application for Details", 
                list(app_groups.keys())
            )
            
            if selected_app:
                st.subheader(f"📄 Application Details: {selected_app}")
                app_documents = app_groups[selected_app]
                self._display_application_analysis(app_documents, selected_app)
    
    def render_document_review(self):
        """Render document review interface for assessors"""
        
        st.title("📝 Document Review")
        
        applications = self.db_manager.get_all_applications()
        
        if not applications:
            st.info("No documents to review.")
            return
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            doc_type_filter = st.selectbox(
                "Filter by Document Type",
                ["All"] + list(set(doc.get('document_type', 'Unknown') for doc in applications))
            )
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Pending Review", "Approved", "Needs Attention"]
            )
        
        with col3:
            date_filter = st.selectbox(
                "Filter by Upload Date",
                ["All", "Today", "This Week", "This Month"]
            )
        
        # Apply filters
        filtered_docs = self._apply_filters(applications, doc_type_filter, status_filter, date_filter)
        
        # Display filtered documents
        for doc in filtered_docs:
            self._render_document_review_card(doc)
    
    def render_analytics(self):
        """Render analytics dashboard"""
        
        st.title("📈 Analytics Dashboard")
        
        applications = self.db_manager.get_all_applications()
        
        if not applications:
            st.info("No data available for analytics.")
            return
        
        # Create analytics visualizations
        self._render_processing_analytics(applications)
        self._render_document_type_analytics(applications)
        self._render_validation_analytics(applications)
        self._render_ai_insights_analytics(applications)
    
    def _display_summary_metrics(self, applications: List[Dict]):
        """Display summary metrics"""
        
        # Group by application
        app_groups = {}
        for doc in applications:
            app_id = doc['application_id']
            if app_id not in app_groups:
                app_groups[app_id] = []
            app_groups[app_id].append(doc)
        
        # Calculate metrics
        total_applications = len(app_groups)
        total_documents = len(applications)
        
        # Calculate completion rates
        complete_applications = 0
        pending_review = 0
        
        for app_id, docs in app_groups.items():
            # Simple completion check (can be enhanced)
            doc_types = set(doc.get('document_type') for doc in docs)
            if len(doc_types) >= 3:  # Assume 3+ doc types = complete
                complete_applications += 1
            else:
                pending_review += 1
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Applications", total_applications)
        
        with col2:
            st.metric("Total Documents", total_documents)
        
        with col3:
            st.metric("Complete Applications", complete_applications)
        
        with col4:
            st.metric("Pending Review", pending_review)
    
    def _display_application_status(self, app_documents: List[Dict], app_id: str):
        """Display application status overview"""
        
        st.subheader(f"Application Status: {app_id}")
        
        # Get borrower info from first document
        if app_documents:
            borrower_info = app_documents[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Borrower:** {borrower_info.get('borrower_name', 'N/A')}")
                st.write(f"**Email:** {borrower_info.get('borrower_email', 'N/A')}")
            
            with col2:
                st.write(f"**Phone:** {borrower_info.get('borrower_phone', 'N/A')}")
                st.write(f"**Loan Amount:** ${borrower_info.get('loan_amount', 0):,.2f}")
        
        # Document summary
        doc_types = [doc.get('document_type', 'Unknown') for doc in app_documents]
        doc_count_by_type = pd.Series(doc_types).value_counts()
        
        st.write("**Documents Uploaded:**")
        for doc_type, count in doc_count_by_type.items():
            display_name = str(doc_type).replace('_', ' ').title()
            st.write(f"- {display_name}: {count}")
        
        # Overall status
        validation_issues = 0
        for doc in app_documents:
            processing_result = doc.get('processing_result', {})
            validation_result = processing_result.get('validation_result', {})
            if not validation_result.get('is_valid', True):
                validation_issues += 1
        
        if validation_issues == 0:
            st.success("✅ All documents validated successfully")
        else:
            st.warning(f"⚠️ {validation_issues} document(s) need attention")
    
    def _display_document_list(self, documents: List[Dict], show_details: bool = False):
        """Display list of documents"""
        
        st.subheader("📄 Document Details")
        
        for i, doc in enumerate(documents):
            processing_result = doc.get('processing_result', {})
            
            # Document header
            with st.expander(f"📄 {doc.get('filename', 'Unknown')} - {doc.get('document_type', 'Unknown').replace('_', ' ').title()}"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Upload Date:** {doc.get('upload_timestamp', 'N/A')}")
                    st.write(f"**Document Type:** {doc.get('document_type', 'Unknown').replace('_', ' ').title()}")
                    st.write(f"**Processing Status:** {processing_result.get('status', 'Unknown').title()}")
                
                with col2:
                    # Validation status
                    validation_result = processing_result.get('validation_result', {})
                    if validation_result.get('is_valid'):
                        st.success("✅ Validation Passed")
                    else:
                        st.error("❌ Validation Issues")
                    
                    # Validation score
                    score = validation_result.get('validation_score', 0.0)
                    st.write(f"**Validation Score:** {score:.2f}")
                
                # Show validation issues
                if validation_result.get('issues'):
                    st.write("**Issues Found:**")
                    for issue in validation_result['issues']:
                        st.error(f"• {issue}")
                
                if validation_result.get('warnings'):
                    st.write("**Warnings:**")
                    for warning in validation_result['warnings']:
                        st.warning(f"• {warning}")
                
                # AI Analysis
                ai_analysis = processing_result.get('ai_analysis', {})
                if ai_analysis:
                    st.write("**AI Analysis:**")
                    
                    if ai_analysis.get('summary'):
                        st.write("*Document Summary:*")
                        st.write(ai_analysis['summary'])
                    
                    if ai_analysis.get('recommendations'):
                        st.write("*AI Recommendations:*")
                        for rec in ai_analysis['recommendations']:
                            st.info(f"💡 {rec}")
                
                # Show extracted data if details requested
                if show_details and processing_result.get('extraction_result'):
                    extraction = processing_result['extraction_result']
                    
                    if extraction.get('structured_data'):
                        st.write("**Extracted Data:**")
                        st.json(extraction['structured_data'])
    
    def _display_applications_table(self, app_groups: Dict[str, List[Dict]]):
        """Display applications in a table format"""
        
        # Prepare data for table
        table_data = []
        
        for app_id, docs in app_groups.items():
            # Get basic info from first document
            first_doc = docs[0]
            
            # Calculate summary stats
            total_docs = len(docs)
            valid_docs = sum(1 for doc in docs 
                           if doc.get('processing_result', {}).get('validation_result', {}).get('is_valid', False))
            
            # Get document types
            doc_types = list(set(doc.get('document_type', 'Unknown') for doc in docs))
            
            # Calculate completion percentage
            required_types = ['id_proof', 'payslip', 'bank_statement']
            completion = sum(1 for req_type in required_types if req_type in doc_types) / len(required_types)
            
            table_data.append({
                'Application ID': app_id,
                'Borrower': first_doc.get('borrower_name', 'N/A'),
                'Email': first_doc.get('borrower_email', 'N/A'),
                'Loan Amount': f"${first_doc.get('loan_amount', 0):,.2f}",
                'Documents': f"{total_docs} uploaded",
                'Valid Docs': f"{valid_docs}/{total_docs}",
                'Completion': f"{completion:.0%}",
                'Upload Date': str(first_doc.get('upload_timestamp', 'N/A'))[:10]
            })
        
        # Display table
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
    
    def _display_application_analysis(self, app_documents: List[Dict], app_id: str):
        """Display detailed analysis of an application"""
        
        # Generate AI-powered analysis
        analysis = self.ai_processor.analyze_application(app_documents)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Application Summary")
            
            if analysis.get('summary'):
                st.write(analysis['summary'])
            
            # Risk assessment
            if analysis.get('risk_assessment'):
                risk = analysis['risk_assessment']
                risk_level = risk.get('risk_level', 'unknown')
                
                if risk_level == 'low':
                    st.success(f"✅ Low Risk Application")
                elif risk_level == 'medium':
                    st.warning(f"⚠️ Medium Risk Application")
                else:
                    st.error(f"🚨 High Risk Application")
                
                if risk.get('reason'):
                    st.write(f"**Reason:** {risk['reason']}")
        
        with col2:
            st.subheader("💡 Recommendations")
            
            if analysis.get('recommendations'):
                for rec in analysis['recommendations']:
                    st.info(f"• {rec}")
            
            # Missing documents
            if analysis.get('missing_documents'):
                st.write("**Missing Documents:**")
                for missing in analysis['missing_documents']:
                    st.warning(f"• {missing.replace('_', ' ').title()}")
        
        # Document timeline
        self._display_document_timeline(app_documents)
    
    def _display_document_timeline(self, documents: List[Dict]):
        """Display document upload timeline"""
        
        st.subheader("📅 Document Timeline")
        
        # Prepare timeline data
        timeline_data = []
        for doc in documents:
            timeline_data.append({
                'date': doc.get('upload_timestamp'),
                'document': doc.get('filename', 'Unknown'),
                'type': doc.get('document_type', 'Unknown').replace('_', ' ').title(),
                'status': doc.get('processing_result', {}).get('status', 'Unknown')
            })
        
        # Sort by date
        timeline_data.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
        
        # Display timeline
        for item in timeline_data:
            date_str = str(item['date'])[:19] if item['date'] else 'Unknown'
            status_icon = "✅" if item['status'] == 'completed' else "⏳" if item['status'] == 'processing' else "❌"
            
            st.write(f"{status_icon} **{date_str}** - {item['document']} ({item['type']})")
    
    def _render_document_review_card(self, doc: Dict):
        """Render individual document review card"""
        
        processing_result = doc.get('processing_result', {})
        validation_result = processing_result.get('validation_result', {})
        
        # Determine card color based on validation
        if validation_result.get('is_valid'):
            card_type = "success"
            status_emoji = "✅"
        elif validation_result.get('issues'):
            card_type = "error"
            status_emoji = "❌"
        else:
            card_type = "warning"
            status_emoji = "⏳"
        
        with st.container():
            st.markdown(f"### {status_emoji} {doc.get('filename', 'Unknown')}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Application:** {doc.get('application_id', 'Unknown')}")
                st.write(f"**Type:** {doc.get('document_type', 'Unknown').replace('_', ' ').title()}")
            
            with col2:
                st.write(f"**Borrower:** {doc.get('borrower_name', 'N/A')}")
                st.write(f"**Upload Date:** {str(doc.get('upload_timestamp', 'N/A'))[:10]}")
            
            with col3:
                score = validation_result.get('validation_score', 0.0)
                st.metric("Validation Score", f"{score:.2f}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"Approve", key=f"approve_{doc.get('filename')}"):
                    st.success("Document approved!")
            
            with col2:
                if st.button(f"Request Changes", key=f"request_{doc.get('filename')}"):
                    st.warning("Change request sent to borrower")
            
            with col3:
                if st.button(f"Reject", key=f"reject_{doc.get('filename')}"):
                    st.error("Document rejected")
            
            st.markdown("---")
    
    def _apply_filters(self, documents: List[Dict], doc_type_filter: str, 
                      status_filter: str, date_filter: str) -> List[Dict]:
        """Apply filters to documents list"""
        
        filtered = documents
        
        # Document type filter
        if doc_type_filter != "All":
            filtered = [doc for doc in filtered if doc.get('document_type') == doc_type_filter]
        
        # Status filter
        if status_filter != "All":
            # This is simplified - in real app, implement proper status tracking
            filtered = documents  # Placeholder
        
        # Date filter
        if date_filter != "All":
            current_date = datetime.now()
            cutoff = None
            
            if date_filter == "Today":
                cutoff = current_date - timedelta(days=1)
            elif date_filter == "This Week":
                cutoff = current_date - timedelta(weeks=1)
            elif date_filter == "This Month":
                cutoff = current_date - timedelta(days=30)
            
            if cutoff:
                filtered = [doc for doc in filtered 
                           if doc.get('upload_timestamp') and doc['upload_timestamp'] >= cutoff]
        
        return filtered
    
    def _render_processing_analytics(self, applications: List[Dict]):
        """Render processing analytics charts"""
        
        st.subheader("📊 Processing Analytics")
        
        # Document processing status distribution
        statuses = [doc.get('processing_result', {}).get('status', 'Unknown') for doc in applications]
        status_counts = pd.Series(statuses).value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Document Processing Status"
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Validation score distribution
            scores = []
            for doc in applications:
                validation_result = doc.get('processing_result', {}).get('validation_result', {})
                score = validation_result.get('validation_score', 0.0)
                scores.append(score)
            
            fig_scores = px.histogram(
                x=scores,
                nbins=20,
                title="Validation Score Distribution"
            )
            st.plotly_chart(fig_scores, use_container_width=True)
    
    def _render_document_type_analytics(self, applications: List[Dict]):
        """Render document type analytics"""
        
        st.subheader("📄 Document Type Analytics")
        
        # Document type frequency
        doc_types = [doc.get('document_type', 'Unknown') for doc in applications]
        type_counts = pd.Series(doc_types).value_counts()
        
        fig_types = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            title="Document Types Uploaded"
        )
        fig_types.update_xaxes(title="Document Type")
        fig_types.update_yaxes(title="Count")
        
        st.plotly_chart(fig_types, use_container_width=True)
    
    def _render_validation_analytics(self, applications: List[Dict]):
        """Render validation analytics"""
        
        st.subheader("✅ Validation Analytics")
        
        # Validation issues by document type
        validation_data = []
        
        for doc in applications:
            processing_result = doc.get('processing_result', {})
            validation_result = processing_result.get('validation_result', {})
            
            validation_data.append({
                'document_type': doc.get('document_type', 'Unknown'),
                'is_valid': validation_result.get('is_valid', False),
                'issues_count': len(validation_result.get('issues', [])),
                'warnings_count': len(validation_result.get('warnings', []))
            })
        
        if validation_data:
            df = pd.DataFrame(validation_data)
            
            # Validation success rate by document type
            validation_rates = df.groupby('document_type')['is_valid'].agg(['count', 'sum']).reset_index()
            validation_rates['success_rate'] = validation_rates['sum'] / validation_rates['count']
            
            fig_validation = px.bar(
                x=validation_rates.index,
                y=validation_rates['success_rate'],
                title="Validation Success Rate by Document Type"
            )
            fig_validation.update_yaxes(title="Success Rate", range=[0, 1])
            
            st.plotly_chart(fig_validation, use_container_width=True)
    
    def _render_ai_insights_analytics(self, applications: List[Dict]):
        """Render AI insights analytics"""
        
        st.subheader("🤖 AI Insights Analytics")
        
        # Risk level distribution
        risk_levels = []
        
        for doc in applications:
            ai_analysis = doc.get('processing_result', {}).get('ai_analysis', {})
            risk_assessment = ai_analysis.get('risk_assessment', {})
            risk_level = risk_assessment.get('risk_level', 'unknown')
            risk_levels.append(risk_level)
        
        if risk_levels:
            risk_counts = pd.Series(risk_levels).value_counts()
            
            fig_risk = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title="Risk Level Distribution",
                color_discrete_map={
                    'low': 'green',
                    'medium': 'yellow',
                    'high': 'red',
                    'unknown': 'gray'
                }
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Common AI recommendations
        all_recommendations = []
        
        for doc in applications:
            ai_analysis = doc.get('processing_result', {}).get('ai_analysis', {})
            recommendations = ai_analysis.get('recommendations', [])
            all_recommendations.extend(recommendations)
        
        if all_recommendations:
            rec_counts = pd.Series(all_recommendations).value_counts().head(10)
            
            st.subheader("Most Common AI Recommendations")
            for rec, count in rec_counts.items():
                st.write(f"• {rec} ({count} times)")
