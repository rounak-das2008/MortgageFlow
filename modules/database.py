import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .gcp_services import GCPServices

class DatabaseManager:
    def __init__(self, use_gcp: bool = True):
        self.use_gcp = use_gcp
        self.gcp_services = None
        self.sqlite_db_path = "mortgage_documents.db"
        
        if use_gcp:
            self.gcp_services = GCPServices()
            self.use_gcp = self.gcp_services.firestore_available
        
        if not self.use_gcp:
            self._initialize_sqlite()
            logging.info("Using SQLite database as fallback")
        else:
            logging.info("Using Firestore database")
    
    def _initialize_sqlite(self):
        """Initialize SQLite database with required tables"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Create documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    borrower_name TEXT,
                    borrower_email TEXT,
                    borrower_phone TEXT,
                    loan_amount REAL,
                    processing_result TEXT,  -- JSON string
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id TEXT UNIQUE NOT NULL,
                    borrower_name TEXT,
                    borrower_email TEXT,
                    borrower_phone TEXT,
                    loan_amount REAL,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create analysis table for AI insights
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,  -- 'document', 'application', 'fraud'
                    analysis_data TEXT,  -- JSON string
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logging.info("SQLite database initialized successfully")
            
        except Exception as e:
            logging.error(f"SQLite initialization failed: {str(e)}")
            raise
    
    def store_document(self, document_data: Dict[str, Any]) -> bool:
        """Store document information"""
        
        if self.use_gcp:
            return self._store_document_firestore(document_data)
        else:
            return self._store_document_sqlite(document_data)
    
    def _store_document_firestore(self, document_data: Dict[str, Any]) -> bool:
        """Store document in Firestore"""
        
        try:
            # Prepare data for Firestore
            firestore_data = document_data.copy()

            def serialize(value):
                if isinstance(value, datetime):
                    return value.isoformat()
                if isinstance(value, dict):
                    return {k: serialize(v) for k, v in value.items()}
                if isinstance(value, list):
                    return [serialize(v) for v in value]
                return value
            
            # Convert datetime objects to strings for Firestore
            if 'upload_timestamp' in firestore_data:
                firestore_data['upload_timestamp'] = serialize(firestore_data['upload_timestamp'])
            
            # Convert processing result to JSON string if it's a dict
            if isinstance(firestore_data.get('processing_result'), dict):
                firestore_data['processing_result'] = json.dumps(serialize(firestore_data['processing_result']))
            
            # Generate document ID
            doc_id = f"{document_data['application_id']}_{document_data.get('file_hash', 'unknown')}"
            
            # Store in Firestore
            success = self.gcp_services.store_in_firestore('documents', doc_id, serialize(firestore_data))
            
            if success:
                # Also store/update application info
                self._store_application_info_firestore(document_data)
            
            return success
            
        except Exception as e:
            logging.error(f"Firestore document storage failed: {str(e)}")
            return False
    
    def _store_document_sqlite(self, document_data: Dict[str, Any]) -> bool:
        """Store document in SQLite"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Convert processing result to JSON string
            processing_result_json = json.dumps(document_data.get('processing_result', {}))
            
            cursor.execute('''
                INSERT INTO documents (
                    application_id, document_type, filename, file_path, file_hash,
                    upload_timestamp, borrower_name, borrower_email, borrower_phone,
                    loan_amount, processing_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_data.get('application_id'),
                document_data.get('document_type'),
                document_data.get('filename'),
                document_data.get('file_path'),
                document_data.get('file_hash'),
                document_data.get('upload_timestamp'),
                document_data.get('borrower_name'),
                document_data.get('borrower_email'),
                document_data.get('borrower_phone'),
                document_data.get('loan_amount'),
                processing_result_json
            ))
            
            conn.commit()
            conn.close()
            
            # Store/update application info
            self._store_application_info_sqlite(document_data)
            
            return True
            
        except Exception as e:
            logging.error(f"SQLite document storage failed: {str(e)}")
            return False
    
    def _store_application_info_firestore(self, document_data: Dict[str, Any]):
        """Store/update application info in Firestore"""
        
        try:
            app_data = {
                'application_id': document_data['application_id'],
                'borrower_name': document_data.get('borrower_name'),
                'borrower_email': document_data.get('borrower_email'),
                'borrower_phone': document_data.get('borrower_phone'),
                'loan_amount': document_data.get('loan_amount'),
                'status': 'active',
                'updated_at': datetime.now().isoformat()
            }
            
            self.gcp_services.store_in_firestore('applications', document_data['application_id'], app_data)
            
        except Exception as e:
            logging.error(f"Application info storage failed: {str(e)}")
    
    def _store_application_info_sqlite(self, document_data: Dict[str, Any]):
        """Store/update application info in SQLite"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Insert or update application
            cursor.execute('''
                INSERT OR REPLACE INTO applications (
                    application_id, borrower_name, borrower_email, borrower_phone,
                    loan_amount, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_data['application_id'],
                document_data.get('borrower_name'),
                document_data.get('borrower_email'),
                document_data.get('borrower_phone'),
                document_data.get('loan_amount'),
                'active',
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"SQLite application info storage failed: {str(e)}")
    
    def get_application_documents(self, application_id: str) -> List[Dict[str, Any]]:
        """Get all documents for an application"""
        
        if self.use_gcp:
            return self._get_application_documents_firestore(application_id)
        else:
            return self._get_application_documents_sqlite(application_id)
    
    def _get_application_documents_firestore(self, application_id: str) -> List[Dict[str, Any]]:
        """Get application documents from Firestore"""
        
        try:
            documents = self.gcp_services.query_firestore(
                'documents',
                [('application_id', '==', application_id)]
            )
            
            # Parse processing results from JSON
            for doc in documents:
                if doc.get('processing_result'):
                    try:
                        doc['processing_result'] = json.loads(doc['processing_result'])
                    except json.JSONDecodeError:
                        pass
            
            return documents
            
        except Exception as e:
            logging.error(f"Firestore document retrieval failed: {str(e)}")
            return []
    
    def _get_application_documents_sqlite(self, application_id: str) -> List[Dict[str, Any]]:
        """Get application documents from SQLite"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM documents WHERE application_id = ?
            ''', (application_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            documents = []
            for row in rows:
                doc = dict(row)
                
                # Parse processing result from JSON
                if doc.get('processing_result'):
                    try:
                        doc['processing_result'] = json.loads(doc['processing_result'])
                    except json.JSONDecodeError:
                        doc['processing_result'] = {}
                
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logging.error(f"SQLite document retrieval failed: {str(e)}")
            return []
    
    def get_all_applications(self) -> List[Dict[str, Any]]:
        """Get all applications with their documents"""
        
        if self.use_gcp:
            return self._get_all_applications_firestore()
        else:
            return self._get_all_applications_sqlite()
    
    def _get_all_applications_firestore(self) -> List[Dict[str, Any]]:
        """Get all applications from Firestore"""
        
        try:
            documents = self.gcp_services.query_firestore('documents')
            
            # Parse processing results from JSON
            for doc in documents:
                if doc.get('processing_result'):
                    try:
                        doc['processing_result'] = json.loads(doc['processing_result'])
                    except json.JSONDecodeError:
                        pass
            
            return documents
            
        except Exception as e:
            logging.error(f"Firestore applications retrieval failed: {str(e)}")
            return []
    
    def _get_all_applications_sqlite(self) -> List[Dict[str, Any]]:
        """Get all applications from SQLite"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM documents ORDER BY upload_timestamp DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            documents = []
            for row in rows:
                doc = dict(row)
                
                # Parse processing result from JSON
                if doc.get('processing_result'):
                    try:
                        doc['processing_result'] = json.loads(doc['processing_result'])
                    except json.JSONDecodeError:
                        doc['processing_result'] = {}
                
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logging.error(f"SQLite applications retrieval failed: {str(e)}")
            return []
    
    def store_analysis_result(self, application_id: str, analysis_type: str, analysis_data: Dict[str, Any]) -> bool:
        """Store AI analysis results"""
        
        if self.use_gcp:
            return self._store_analysis_firestore(application_id, analysis_type, analysis_data)
        else:
            return self._store_analysis_sqlite(application_id, analysis_type, analysis_data)
    
    def _store_analysis_firestore(self, application_id: str, analysis_type: str, analysis_data: Dict[str, Any]) -> bool:
        """Store analysis in Firestore"""
        
        try:
            doc_id = f"{application_id}_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            firestore_data = {
                'application_id': application_id,
                'analysis_type': analysis_type,
                'analysis_data': json.dumps(analysis_data),
                'created_at': datetime.now().isoformat()
            }
            
            return self.gcp_services.store_in_firestore('analysis_results', doc_id, firestore_data)
            
        except Exception as e:
            logging.error(f"Firestore analysis storage failed: {str(e)}")
            return False
    
    def _store_analysis_sqlite(self, application_id: str, analysis_type: str, analysis_data: Dict[str, Any]) -> bool:
        """Store analysis in SQLite"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_results (application_id, analysis_type, analysis_data)
                VALUES (?, ?, ?)
            ''', (application_id, analysis_type, json.dumps(analysis_data)))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"SQLite analysis storage failed: {str(e)}")
            return False
    
    def get_analysis_results(self, application_id: str, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get analysis results for an application"""
        
        if self.use_gcp:
            return self._get_analysis_firestore(application_id, analysis_type)
        else:
            return self._get_analysis_sqlite(application_id, analysis_type)
    
    def _get_analysis_firestore(self, application_id: str, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get analysis from Firestore"""
        
        try:
            filters = [('application_id', '==', application_id)]
            if analysis_type:
                filters.append(('analysis_type', '==', analysis_type))
            
            results = self.gcp_services.query_firestore('analysis_results', filters)
            
            # Parse analysis data from JSON
            for result in results:
                if result.get('analysis_data'):
                    try:
                        result['analysis_data'] = json.loads(result['analysis_data'])
                    except json.JSONDecodeError:
                        pass
            
            return results
            
        except Exception as e:
            logging.error(f"Firestore analysis retrieval failed: {str(e)}")
            return []
    
    def _get_analysis_sqlite(self, application_id: str, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get analysis from SQLite"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if analysis_type:
                cursor.execute('''
                    SELECT * FROM analysis_results 
                    WHERE application_id = ? AND analysis_type = ?
                    ORDER BY created_at DESC
                ''', (application_id, analysis_type))
            else:
                cursor.execute('''
                    SELECT * FROM analysis_results 
                    WHERE application_id = ?
                    ORDER BY created_at DESC
                ''', (application_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                result = dict(row)
                
                # Parse analysis data from JSON
                if result.get('analysis_data'):
                    try:
                        result['analysis_data'] = json.loads(result['analysis_data'])
                    except json.JSONDecodeError:
                        result['analysis_data'] = {}
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logging.error(f"SQLite analysis retrieval failed: {str(e)}")
            return []
    
    def update_document_status(self, application_id: str, filename: str, status: str) -> bool:
        """Update document processing status"""
        
        if self.use_gcp:
            return self._update_document_status_firestore(application_id, filename, status)
        else:
            return self._update_document_status_sqlite(application_id, filename, status)
    
    def _update_document_status_firestore(self, application_id: str, filename: str, status: str) -> bool:
        """Update document status in Firestore"""
        
        try:
            # This would require querying and updating the specific document
            # For now, return True as a placeholder
            return True
            
        except Exception as e:
            logging.error(f"Firestore status update failed: {str(e)}")
            return False
    
    def _update_document_status_sqlite(self, application_id: str, filename: str, status: str) -> bool:
        """Update document status in SQLite"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE documents 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE application_id = ? AND filename = ?
            ''', (application_id, filename))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"SQLite status update failed: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        if self.use_gcp:
            return self._get_firestore_stats()
        else:
            return self._get_sqlite_stats()
    
    def _get_firestore_stats(self) -> Dict[str, Any]:
        """Get Firestore statistics"""
        
        try:
            documents = self.gcp_services.query_firestore('documents')
            applications = self.gcp_services.query_firestore('applications')
            
            return {
                'total_documents': len(documents),
                'total_applications': len(applications),
                'database_type': 'Firestore',
                'connection_status': 'Connected' if self.use_gcp else 'Disconnected'
            }
            
        except Exception as e:
            logging.error(f"Firestore stats failed: {str(e)}")
            return {'error': str(e), 'database_type': 'Firestore'}
    
    def _get_sqlite_stats(self) -> Dict[str, Any]:
        """Get SQLite statistics"""
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM documents')
            doc_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT application_id) FROM documents')
            app_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_documents': doc_count,
                'total_applications': app_count,
                'database_type': 'SQLite',
                'database_path': self.sqlite_db_path,
                'connection_status': 'Connected'
            }
            
        except Exception as e:
            logging.error(f"SQLite stats failed: {str(e)}")
            return {'error': str(e), 'database_type': 'SQLite'}
