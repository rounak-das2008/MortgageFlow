import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from google.cloud import documentai
from google.cloud import storage
from google.cloud import firestore
from google.cloud import aiplatform
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

class GCPServices:
    def __init__(self):
        self.project_id = os.environ.get("GCP_PROJECT_ID", "genai-hackathon-25")
        # Use a dedicated project for Document AI if provided (project NUMBER works best here)
        self.document_ai_project_id = os.environ.get("GCP_DOCUMENT_AI_PROJECT_ID", "976956559592")
        # Document AI uses 'us' region, Vertex AI uses 'us-central1'
        self.document_ai_location = os.environ.get("GCP_DOCUMENT_AI_LOCATION", "us")
        self.vertex_ai_location = os.environ.get("GCP_VERTEX_AI_LOCATION", "us-central1")
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME", "mortgage-documents-bucket")
        
        # Initialize Vertex AI
        try:
            vertexai.init(project=self.project_id, location=self.vertex_ai_location)
            self.vertex_model = GenerativeModel("gemini-2.5-pro")
            self.vertex_available = True
            logging.info("Vertex AI initialized successfully")
        except Exception as e:
            logging.warning(f"Vertex AI initialization failed: {str(e)}")
            self.vertex_model = None
            self.vertex_available = False
        
        # Service clients
        self.document_ai_client = None
        self.storage_client = None
        self.firestore_client = None
        
        # Service availability flags
        self.document_ai_available = False
        self.storage_available = False
        self.firestore_available = False
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize GCP services with error handling"""
        
        try:
            # Try to initialize Document AI
            self.document_ai_client = documentai.DocumentProcessorServiceClient()
            self.document_ai_available = True
            logging.info("Document AI client initialized successfully")
        except Exception as e:
            logging.warning(f"Document AI initialization failed: {str(e)}")
        
        try:
            # Try to initialize Cloud Storage
            self.storage_client = storage.Client(project=self.project_id)
            self.storage_available = True
            logging.info("Cloud Storage client initialized successfully")
        except Exception as e:
            logging.warning(f"Cloud Storage initialization failed: {str(e)}")
        
        try:
            # Try to initialize Firestore
            self.firestore_client = firestore.Client(project=self.project_id)
            self.firestore_available = True
            logging.info("Firestore client initialized successfully")
        except Exception as e:
            logging.warning(f"Firestore initialization failed: {str(e)}")
    
    def check_services(self) -> bool:
        """Check if GCP services are available"""
        return any([
            self.document_ai_available,
            self.storage_available,
            self.firestore_available
        ])
    
    def process_document(self, file_path: str, processor_type: str = "FORM_PARSER_PROCESSOR") -> Optional[Dict[str, Any]]:
        """Process document using Document AI"""
        
        if not self.document_ai_available:
            return None
        
        try:
            # Read document file
            with open(file_path, "rb") as file:
                file_content = file.read()
            
            # Configure document
            document = documentai.RawDocument(
                content=file_content,
                mime_type=self._get_mime_type(file_path)
            )
            
            # Get processor name
            processor_name = self._get_processor_name(processor_type)
            
            # Process document
            request = documentai.ProcessRequest(
                name=processor_name,
                raw_document=document
            )
            
            result = self.document_ai_client.process_document(request=request)
            
            # Extract data from result
            document_response = result.document
            
            processed_data = {
                'text': document_response.text,
                'entities': [],
                'confidence': 0.0
            }
            
            # Extract entities
            for entity in document_response.entities:
                entity_data = {
                    'type': entity.type_,
                    'mentionText': entity.mention_text,
                    'confidence': entity.confidence,
                    'normalizedValue': getattr(entity.normalized_value, 'text', '') if entity.normalized_value else ''
                }
                processed_data['entities'].append(entity_data)
            
            # Calculate overall confidence
            if processed_data['entities']:
                total_confidence = sum(e['confidence'] for e in processed_data['entities'])
                processed_data['confidence'] = total_confidence / len(processed_data['entities'])
            
            return processed_data
            
        except Exception as e:
            logging.error(f"Document AI processing failed: {str(e)}")
            return None
    
    def upload_to_storage(self, file_path: str, destination_blob_name: str) -> Optional[str]:
        """Upload file to Cloud Storage"""
        
        if not self.storage_available:
            return None
        
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(destination_blob_name)
            
            blob.upload_from_filename(file_path)
            
            # Return public URL (if bucket allows public access)
            return f"gs://{self.bucket_name}/{destination_blob_name}"
            
        except Exception as e:
            logging.error(f"Cloud Storage upload failed: {str(e)}")
            return None
    
    def store_in_firestore(self, collection_name: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Store document data in Firestore"""
        
        if not self.firestore_available:
            return False
        
        try:
            # Serialize datetime objects to strings
            serialized_data = self._serialize_datetime_objects(data)
            doc_ref = self.firestore_client.collection(collection_name).document(document_id)
            doc_ref.set(serialized_data)
            return True
            
        except Exception as e:
            logging.error(f"Firestore storage failed: {str(e)}")
            return False
    
    def get_from_firestore(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document data from Firestore"""
        
        if not self.firestore_available:
            return None
        
        try:
            doc_ref = self.firestore_client.collection(collection_name).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
                
        except Exception as e:
            logging.error(f"Firestore retrieval failed: {str(e)}")
            return None
    
    def query_firestore(self, collection_name: str, filters: List[tuple] = None) -> List[Dict[str, Any]]:
        """Query documents from Firestore"""
        
        if not self.firestore_available:
            return []
        
        try:
            query = self.firestore_client.collection(collection_name)
            
            # Apply filters if provided
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            docs = query.stream()
            
            results = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                results.append(doc_data)
            
            return results
            
        except Exception as e:
            logging.error(f"Firestore query failed: {str(e)}")
            return []
    
    def create_storage_bucket(self) -> bool:
        """Create storage bucket if it doesn't exist"""
        
        if not self.storage_available:
            return False
        
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(
                    self.bucket_name,
                    location=self.document_ai_location
                )
                logging.info(f"Created bucket: {self.bucket_name}")
            
            return True
            
        except Exception as e:
            logging.error(f"Bucket creation failed: {str(e)}")
            return False
    
    def _get_processor_name(self, processor_type: str) -> str:
        """Get full processor name for Document AI"""
        
        # Map logical processor types to your actual processor IDs
        # Region: us, Project: self.document_ai_project_id
        processor_mapping = {
            'FORM_PARSER_PROCESSOR': 'projects/{}/locations/{}/processors/{}'.format(
                self.document_ai_project_id, self.document_ai_location, '814a06f8fb3f18de'
            ),
            'BANK_STATEMENT_PROCESSOR': 'projects/{}/locations/{}/processors/{}'.format(
                self.document_ai_project_id, self.document_ai_location, 'a635c2b09536d6f9'
            ),
            'ID_PROCESSOR': 'projects/{}/locations/{}/processors/{}'.format(
                self.document_ai_project_id, self.document_ai_location, 'e3cdb96b44b8f751'
            ),
            'INVOICE_PROCESSOR': 'projects/{}/locations/{}/processors/{}'.format(
                self.document_ai_project_id, self.document_ai_location, '8556cebf6c444142'
            ),
            'OCR_PROCESSOR': 'projects/{}/locations/{}/processors/{}'.format(
                self.document_ai_project_id, self.document_ai_location, 'e7f2725bcd2d6b4c'
            ),
        }
        
        return processor_mapping.get(processor_type, processor_mapping['FORM_PARSER_PROCESSOR'])
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type based on file extension"""
        
        file_extension = file_path.lower().split('.')[-1]
        
        mime_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'tiff': 'image/tiff',
            'tif': 'image/tiff'
        }
        
        return mime_types.get(file_extension, 'application/pdf')
    
    def _serialize_datetime_objects(self, data: Any) -> Any:
        """Recursively serialize datetime objects to ISO format strings"""
        
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self._serialize_datetime_objects(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetime_objects(item) for item in data]
        else:
            return data
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all GCP services"""
        
        return {
            'document_ai': self.document_ai_available,
            'cloud_storage': self.storage_available,
            'firestore': self.firestore_available,
            'overall': self.check_services()
        }
    
    def test_connections(self) -> Dict[str, str]:
        """Test connections to all GCP services"""
        
        status = {}
        
        # Test Document AI
        if self.document_ai_available:
            try:
                # Try to list processors (simple connectivity test)
                parent = f"projects/{self.project_id}/locations/{self.document_ai_location}"
                processors = self.document_ai_client.list_processors(parent=parent)
                status['document_ai'] = "Connected"
            except Exception as e:
                status['document_ai'] = f"Error: {str(e)}"
        else:
            status['document_ai'] = "Not available"
        
        # Test Cloud Storage
        if self.storage_available:
            try:
                # Try to list buckets
                buckets = list(self.storage_client.list_buckets())
                status['cloud_storage'] = "Connected"
            except Exception as e:
                status['cloud_storage'] = f"Error: {str(e)}"
        else:
            status['cloud_storage'] = "Not available"
        
        # Test Firestore
        if self.firestore_available:
            try:
                # Try to access a collection
                collections = self.firestore_client.collections()
                status['firestore'] = "Connected"
            except Exception as e:
                status['firestore'] = f"Error: {str(e)}"
        else:
            status['firestore'] = "Not available"
        
        return status
