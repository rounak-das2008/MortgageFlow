"""
Helper utilities for the mortgage document automation system
"""

import os
import hashlib
import logging
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
from PIL import Image
import tempfile

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    
    # User session variables
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'Borrower'
    
    # Authentication state for assessor
    if 'assessor_authenticated' not in st.session_state:
        st.session_state.assessor_authenticated = False
    if 'assessor_username' not in st.session_state:
        st.session_state.assessor_username = None
    
    if 'current_application_id' not in st.session_state:
        st.session_state.current_application_id = None
    
    # Upload session variables
    if 'uploaded_files_info' not in st.session_state:
        st.session_state.uploaded_files_info = []
    
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = {}
    
    # Navigation variables
    if 'borrower_nav' not in st.session_state:
        st.session_state.borrower_nav = 'Upload Documents'
    
    if 'assessor_nav' not in st.session_state:
        st.session_state.assessor_nav = 'Assessment Dashboard'
    
    # Application state variables
    if 'applications_cache' not in st.session_state:
        st.session_state.applications_cache = []
    
    if 'cache_timestamp' not in st.session_state:
        st.session_state.cache_timestamp = None
    
    # Document analysis state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    # Notification system
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    # Settings and preferences
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'auto_validate': True,
            'ai_analysis': True,
            'fraud_detection': True,
            'notification_level': 'normal'
        }

def _get_assessor_credentials() -> Dict[str, str]:
    """Fetch assessor credentials from env or Streamlit secrets."""
    username = None
    password = None
    try:
        # Prefer Streamlit secrets if available
        if hasattr(st, 'secrets') and st.secrets:
            username = st.secrets.get('ASSESSOR_USERNAME', None)
            password = st.secrets.get('ASSESSOR_PASSWORD', None)
    except Exception:
        pass
    # Fallback to environment variables
    if not username:
        username = os.getenv('ASSESSOR_USERNAME')
    if not password:
        password = os.getenv('ASSESSOR_PASSWORD')
    # Final fallback (development only)
    if not username:
        username = 'assessor'
    if not password:
        password = 'assessor123'
    return {'username': username, 'password': password}

def render_assessor_login() -> bool:
    """Render assessor login form and return authentication status."""
    st.title("🔐 Assessor Login")
    st.caption("Enter your credentials to access the assessor dashboard.")
    
    col1, col2 = st.columns(2)
    with col1:
        username_input = st.text_input("Username", key="assessor_login_username")
    with col2:
        password_input = st.text_input("Password", type="password", key="assessor_login_password")
    
    creds = _get_assessor_credentials()
    login_clicked = st.button("Sign In", type="primary")
    
    if login_clicked:
        if username_input == creds['username'] and password_input == creds['password']:
            st.session_state.assessor_authenticated = True
            st.session_state.assessor_username = username_input
            add_notification("Login successful.", "success")
            return True
        else:
            add_notification("Invalid username or password.", "error", auto_dismiss=False)
            return False
    
    return st.session_state.assessor_authenticated is True

def assessor_logout():
    """Log out the assessor user and clear auth state."""
    st.session_state.assessor_authenticated = False
    st.session_state.assessor_username = None

def save_uploaded_file(uploaded_file, application_id: str) -> str:
    """Save uploaded file to local storage and return file path"""
    
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join("uploads", application_id)
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = uploaded_file.name.split('.')[-1].lower()
        safe_filename = f"{timestamp}_{uploaded_file.name}"
        
        file_path = os.path.join(uploads_dir, safe_filename)
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        logging.info(f"File saved successfully: {file_path}")
        return file_path
        
    except Exception as e:
        logging.error(f"Failed to save uploaded file: {str(e)}")
        raise Exception(f"File save failed: {str(e)}")

def get_file_hash(file_path: str) -> str:
    """Generate SHA-256 hash of file for integrity checking"""
    
    try:
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
        
    except Exception as e:
        logging.error(f"Failed to generate file hash: {str(e)}")
        return "unknown"

def validate_file_upload(uploaded_file, allowed_types: Optional[list] = None, max_size_mb: int = 10) -> Dict[str, Any]:
    """Validate uploaded file for type, size, and basic integrity"""
    
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'file_info': {}
    }
    
    if allowed_types is None:
        allowed_types = ['pdf', 'jpg', 'jpeg', 'png', 'tiff']
    
    try:
        # Check file exists
        if uploaded_file is None:
            validation_result['is_valid'] = False
            validation_result['errors'].append("No file uploaded")
            return validation_result
        
        # Check file size
        file_size = len(uploaded_file.getbuffer())
        file_size_mb = file_size / (1024 * 1024)
        
        validation_result['file_info']['size_bytes'] = file_size
        validation_result['file_info']['size_mb'] = round(file_size_mb, 2)
        
        if file_size_mb > max_size_mb:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)")
        
        # Check file type
        file_extension = uploaded_file.name.split('.')[-1].lower()
        validation_result['file_info']['extension'] = file_extension
        validation_result['file_info']['filename'] = uploaded_file.name
        
        if file_extension not in allowed_types:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_types)}")
        
        # Additional validation for image files
        if file_extension in ['jpg', 'jpeg', 'png', 'tiff']:
            try:
                # Try to open the image to verify it's valid
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}")
                temp_file.write(uploaded_file.getbuffer())
                temp_file.close()
                
                with Image.open(temp_file.name) as img:
                    validation_result['file_info']['image_size'] = img.size
                    validation_result['file_info']['image_mode'] = img.mode
                    
                    # Check image quality
                    width, height = img.size
                    if width < 300 or height < 300:
                        validation_result['warnings'].append("Image resolution is low. This may affect text extraction quality.")
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
            except Exception as e:
                validation_result['warnings'].append(f"Could not validate image: {str(e)}")
        
        # Check filename for potential issues
        if len(uploaded_file.name) > 100:
            validation_result['warnings'].append("Filename is very long. Consider using a shorter name.")
        
        # Check for suspicious characters in filename
        suspicious_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in uploaded_file.name for char in suspicious_chars):
            validation_result['warnings'].append("Filename contains potentially problematic characters.")
        
    except Exception as e:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"File validation error: {str(e)}")
    
    return validation_result

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable file size"""
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """Clean filename to remove problematic characters"""
    
    import re
    
    # Remove or replace problematic characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra spaces and underscores
    cleaned = re.sub(r'[_\s]+', '_', cleaned)
    
    # Limit length
    if len(cleaned) > 100:
        name_part, ext_part = os.path.splitext(cleaned)
        cleaned = name_part[:95] + ext_part
    
    return cleaned

def add_notification(message: str, notification_type: str = "info", auto_dismiss: bool = True):
    """Add a notification to the session state"""
    
    notification = {
        'id': len(st.session_state.notifications),
        'message': message,
        'type': notification_type,  # info, success, warning, error
        'timestamp': datetime.now(),
        'auto_dismiss': auto_dismiss,
        'dismissed': False
    }
    
    st.session_state.notifications.append(notification)

def display_notifications():
    """Display all active notifications"""
    
    active_notifications = [n for n in st.session_state.notifications if not n['dismissed']]
    
    for notification in active_notifications:
        notification_type = notification['type']
        message = notification['message']
        
        if notification_type == "success":
            st.success(message)
        elif notification_type == "warning":
            st.warning(message)
        elif notification_type == "error":
            st.error(message)
        else:
            st.info(message)
        
        # Auto-dismiss after showing
        if notification['auto_dismiss']:
            notification['dismissed'] = True

def clear_notifications():
    """Clear all notifications"""
    st.session_state.notifications = []

def get_user_preference(key: str, default_value: Any = None) -> Any:
    """Get user preference value"""
    return st.session_state.user_preferences.get(key, default_value)

def set_user_preference(key: str, value: Any):
    """Set user preference value"""
    st.session_state.user_preferences[key] = value

def cache_applications(applications: list, ttl_minutes: int = 5):
    """Cache applications data with TTL"""
    
    st.session_state.applications_cache = applications
    st.session_state.cache_timestamp = datetime.now()

def get_cached_applications(ttl_minutes: int = 5) -> Optional[list]:
    """Get cached applications if not expired"""
    
    if not st.session_state.cache_timestamp:
        return None
    
    time_diff = datetime.now() - st.session_state.cache_timestamp
    if time_diff.total_seconds() > (ttl_minutes * 60):
        return None
    
    return st.session_state.applications_cache

def clear_cache():
    """Clear all cached data"""
    st.session_state.applications_cache = []
    st.session_state.cache_timestamp = None
    st.session_state.analysis_results = {}

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """Format datetime for display"""
    
    if include_time:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.strftime("%Y-%m-%d")

def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """Truncate text to specified length"""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    
    if add_ellipsis:
        truncated += "..."
    
    return truncated

def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent basic injection attacks"""
    
    if not isinstance(input_string, str):
        return str(input_string)
    
    # Remove potentially dangerous characters
    sanitized = input_string.replace('<', '&lt;').replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;').replace("'", '&#x27;')
    
    return sanitized.strip()

def validate_email(email: str) -> bool:
    """Basic email validation"""
    
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Basic phone number validation"""
    
    import re
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it has appropriate length
    return 10 <= len(digits_only) <= 15

def generate_application_id() -> str:
    """Generate a unique application ID"""
    
    import uuid
    
    # Generate a short, readable ID
    full_uuid = str(uuid.uuid4())
    short_id = full_uuid.split('-')[0].upper()
    
    # Add timestamp component for uniqueness
    timestamp_component = datetime.now().strftime("%m%d")
    
    return f"APP-{timestamp_component}-{short_id}"

def create_download_link(data: bytes, filename: str, mime_type: str = "application/octet-stream") -> str:
    """Create a download link for data"""
    
    import base64
    
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Download {filename}</a>'

def log_user_action(action: str, details: Optional[Dict[str, Any]] = None):
    """Log user actions for audit trail"""
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_role': st.session_state.get('user_role', 'Unknown'),
        'action': action,
        'details': details or {},
        'session_id': id(st.session_state)  # Simple session tracking
    }
    
    logging.info(f"User Action: {log_entry}")

def get_file_icon(file_extension: str) -> str:
    """Get appropriate icon for file type"""
    
    icon_mapping = {
        'pdf': '📄',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'tiff': '🖼️',
        'doc': '📝',
        'docx': '📝',
        'xls': '📊',
        'xlsx': '📊',
        'txt': '📃'
    }
    
    return icon_mapping.get(file_extension.lower(), '📁')

def extract_text_preview(text: str, max_words: int = 50) -> str:
    """Extract a preview of text content"""
    
    if not text:
        return "No text content available"
    
    words = text.split()
    
    if len(words) <= max_words:
        return text
    
    preview_words = words[:max_words]
    return ' '.join(preview_words) + '...'

def calculate_processing_time(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """Calculate and format processing time"""
    
    if end_time is None:
        end_time = datetime.now()
    
    time_diff = end_time - start_time
    
    if time_diff.total_seconds() < 60:
        return f"{time_diff.total_seconds():.1f} seconds"
    elif time_diff.total_seconds() < 3600:
        return f"{time_diff.total_seconds() / 60:.1f} minutes"
    else:
        return f"{time_diff.total_seconds() / 3600:.1f} hours"

def is_business_hours() -> bool:
    """Check if current time is within business hours (9 AM - 5 PM EST)"""
    
    from datetime import datetime
    import pytz
    
    try:
        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est)
        
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if current_time.weekday() >= 5:  # Weekend
            return False
        
        # Check if within business hours (9 AM - 5 PM)
        return 9 <= current_time.hour < 17
        
    except:
        # If timezone handling fails, assume business hours
        return True

def get_processing_status_color(status: str) -> str:
    """Get color code for processing status"""
    
    color_mapping = {
        'pending': '#FFA500',    # Orange
        'processing': '#1E90FF', # Blue
        'completed': '#32CD32',  # Green
        'error': '#FF4500',      # Red
        'warning': '#FFD700'     # Gold
    }
    
    return color_mapping.get(status.lower(), '#808080')  # Gray default

def estimate_processing_time(file_size_mb: float, document_type: str) -> str:
    """Estimate processing time based on file size and type"""
    
    # Base processing times in seconds
    base_times = {
        'id_proof': 30,
        'payslip': 45,
        'bank_statement': 60,
        'tax_document': 90,
        'employment_letter': 30,
        'utility_bill': 25,
        'property_document': 75,
        'credit_report': 40,
        'investment_statement': 50,
        'self_employment_proof': 65
    }
    
    base_time = base_times.get(document_type, 45)
    
    # Adjust for file size (larger files take longer)
    size_multiplier = 1 + (file_size_mb / 10)  # +10% per MB
    
    estimated_seconds = base_time * size_multiplier
    
    if estimated_seconds < 60:
        return f"{int(estimated_seconds)} seconds"
    else:
        return f"{int(estimated_seconds / 60)} minutes"

