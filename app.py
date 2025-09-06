import streamlit as st
import os
from modules.upload_interface import MortgageUploadInterface
from modules.dashboard import DashboardModule
from modules.database import DatabaseManager
from utils.helpers import initialize_session_state, render_assessor_login, assessor_logout

# Page configuration
st.set_page_config(
    page_title="Mortgage Document Automation",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize database
    db_manager = DatabaseManager()
    
    # Sidebar navigation
    st.sidebar.title("🏠 Mortgage Document Automation")
    
    # User role selection (Borrower remains, Assessor gated by login)
    user_role = st.sidebar.selectbox(
        "Select Your Role",
        ["Borrower", "Assessor"],
        key="user_role"
    )
    
    if user_role == "Borrower":
        st.sidebar.markdown("---")
        borrower_pages = st.sidebar.selectbox(
            "Navigation",
            ["Upload Documents", "My Applications"],
            key="borrower_nav"
        )
        
        if borrower_pages == "Upload Documents":
            upload_interface = MortgageUploadInterface(db_manager)
            upload_interface.render()
        else:
            dashboard_module = DashboardModule(db_manager, view_type="borrower")
            dashboard_module.render()
            
    else:  # Assessor
        st.sidebar.markdown("---")
        if st.session_state.get("assessor_authenticated"):
            st.sidebar.success(f"Signed in as: {st.session_state.get('assessor_username', 'Assessor')}")
            if st.sidebar.button("Logout"):
                assessor_logout()
                st.experimental_rerun()
            assessor_pages = st.sidebar.selectbox(
                "Navigation",
                ["Assessment Dashboard", "Document Review", "Analytics"],
                key="assessor_nav"
            )
            
            dashboard_module = DashboardModule(db_manager, view_type="assessor")
            
            if assessor_pages == "Assessment Dashboard":
                dashboard_module.render()
            elif assessor_pages == "Document Review":
                dashboard_module.render_document_review()
            else:
                dashboard_module.render_analytics()
        else:
            # Render login screen in main area
            render_assessor_login()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**System Status**")
    
    # Check GCP services availability
    try:
        from modules.gcp_services import GCPServices
        gcp_services = GCPServices()
        if gcp_services.check_services():
            st.sidebar.success("🟢 GCP Services Active")
        else:
            st.sidebar.warning("🟡 Fallback Mode Active")
    except Exception as e:
        st.sidebar.error("🔴 Service Check Failed")

if __name__ == "__main__":
    main()
