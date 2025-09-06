"""
Batch document processing module for mortgage applications
Handles multiple document upload and processing workflow
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import concurrent.futures
from .extract import DocumentExtractor
from .validate import DocumentValidator
from .simple_ai_processor import SimpleAIProcessor
from .database import DatabaseManager
from utils.document_types import DOCUMENT_TYPES, get_document_category
from utils.helpers import save_uploaded_file, get_file_hash


class BatchDocumentProcessor:
    """Handles batch processing of mortgage documents"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.extractor = DocumentExtractor()
        self.validator = DocumentValidator()
        self.ai_processor = SimpleAIProcessor()
        
    def process_application_batch(self, application_id: str, uploaded_files: List,
                                document_types: Dict[str, str], borrower_info: Dict[str, Any],
                                processing_options: Dict[str, bool]) -> Dict[str, Any]:
        """Process all documents in a mortgage application batch"""
        
        batch_result = {
            'application_id': application_id,
            'total_documents': len(uploaded_files),
            'processed_documents': 0,
            'successful_documents': 0,
            'failed_documents': 0,
            'document_results': [],
            'application_analysis': None,
            'validation_summary': None,
            'processing_time': None,
            'status': 'processing'
        }
        
        start_time = datetime.now()
        
        try:
            # Phase 1: Document Storage and Classification
            logging.info(f"Starting batch processing for application {application_id}")
            stored_files = self._store_documents(uploaded_files, document_types, application_id)
            
            # Phase 2: Parallel Document Processing
            document_results = self._process_documents_parallel(
                stored_files, application_id, borrower_info, processing_options
            )
            
            batch_result['document_results'] = document_results
            batch_result['processed_documents'] = len(document_results)
            batch_result['successful_documents'] = len([r for r in document_results if r['status'] == 'completed'])
            batch_result['failed_documents'] = len([r for r in document_results if r['status'] == 'error'])
            
            # Phase 3: Application-Level Analysis
            if processing_options.get('generate_summary', True):
                batch_result['application_analysis'] = self._analyze_complete_application(
                    document_results, application_id
                )
            
            # Phase 4: Cross-Document Validation
            batch_result['validation_summary'] = self._validate_application_completeness(
                document_results, application_id
            )
            
            # Phase 5: Final Processing
            end_time = datetime.now()
            batch_result['processing_time'] = (end_time - start_time).total_seconds()
            batch_result['status'] = 'completed'
            
            # Store application-level results
            self._store_batch_results(batch_result)
            
            logging.info(f"Batch processing completed for application {application_id}")
            
        except Exception as e:
            logging.error(f"Batch processing failed: {str(e)}")
            batch_result['status'] = 'error'
            batch_result['error'] = str(e)
            batch_result['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        return batch_result
    
    def _store_documents(self, uploaded_files: List, document_types: Dict[str, str], 
                        application_id: str) -> List[Dict[str, Any]]:
        """Store uploaded documents and prepare for processing"""
        
        stored_files = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Determine document type
                doc_type = document_types.get(uploaded_file.name, 'unknown')
                
                # Save file
                file_path = save_uploaded_file(uploaded_file, application_id)
                file_hash = get_file_hash(file_path)
                
                stored_file = {
                    'filename': uploaded_file.name,
                    'file_path': file_path,
                    'file_hash': file_hash,
                    'document_type': doc_type,
                    'file_size': len(uploaded_file.getbuffer()),
                    'upload_timestamp': datetime.now(),
                    'processing_order': i + 1
                }
                
                stored_files.append(stored_file)
                logging.info(f"Stored document: {uploaded_file.name}")
                
            except Exception as e:
                logging.error(f"Failed to store document {uploaded_file.name}: {str(e)}")
                # Continue with other files
                continue
        
        return stored_files
    
    def _process_documents_parallel(self, stored_files: List[Dict[str, Any]], 
                                  application_id: str, borrower_info: Dict[str, Any],
                                  processing_options: Dict[str, bool]) -> List[Dict[str, Any]]:
        """Process documents in parallel for faster throughput"""
        
        results = []
        
        # Use ThreadPoolExecutor for I/O bound operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_file = {
                executor.submit(
                    self._process_single_document,
                    file_info,
                    application_id,
                    borrower_info,
                    processing_options
                ): file_info for file_info in stored_files
            }
            
            for future in concurrent.futures.as_completed(future_to_file):
                file_info = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logging.error(f"Document processing failed for {file_info['filename']}: {str(e)}")
                    error_result = {
                        'filename': file_info['filename'],
                        'document_type': file_info['document_type'],
                        'status': 'error',
                        'error': str(e),
                        'processing_order': file_info['processing_order']
                    }
                    results.append(error_result)
        
        # Sort results by processing order
        results.sort(key=lambda x: x.get('processing_order', 0))
        return results
    
    def _process_single_document(self, file_info: Dict[str, Any], application_id: str,
                               borrower_info: Dict[str, Any], 
                               processing_options: Dict[str, bool]) -> Dict[str, Any]:
        """Process a single document through the complete pipeline"""
        
        result = {
            'filename': file_info['filename'],
            'document_type': file_info['document_type'],
            'file_path': file_info['file_path'],
            'file_hash': file_info['file_hash'],
            'processing_order': file_info['processing_order'],
            'status': 'processing',
            'extraction_result': None,
            'validation_result': None,
            'ai_analysis': None,
            'errors': [],
            'processing_timestamp': datetime.now()
        }
        
        try:
            # Step 1: Document Classification (if needed)
            if file_info['document_type'] == 'unknown':
                classified_type = self._classify_document(file_info['file_path'])
                result['document_type'] = classified_type
                file_info['document_type'] = classified_type
            
            # Step 2: Text and Data Extraction
            if processing_options.get('extract_entities', True):
                extraction_result = self.extractor.extract_document_data(
                    file_info['file_path'], 
                    file_info['document_type']
                )
                result['extraction_result'] = extraction_result
                
                if extraction_result.get('error'):
                    result['errors'].append(f"Extraction error: {extraction_result['error']}")
            
            # Step 3: Document Validation
            if processing_options.get('auto_validate', True) and result['extraction_result']:
                validation_result = self.validator.validate_document(
                    result['extraction_result'], 
                    file_info['document_type']
                )
                result['validation_result'] = validation_result
            
            # Step 4: AI Analysis and Enrichment
            if processing_options.get('generate_summary', True) or processing_options.get('fraud_detection', True):
                ai_analysis = self.ai_processor.analyze_document(
                    file_info['file_path'],
                    file_info['document_type'],
                    result.get('extraction_result'),
                    processing_options.get('generate_summary', True),
                    processing_options.get('fraud_detection', True)
                )
                result['ai_analysis'] = ai_analysis
            
            result['status'] = 'completed'
            
            # Store individual document result
            self._store_document_result(result, application_id, borrower_info)
            
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Processing error: {str(e)}")
            logging.error(f"Document processing failed for {file_info['filename']}: {str(e)}")
        
        return result
    
    def _classify_document(self, file_path: str) -> str:
        """Classify document type using GCP Document AI or AI analysis"""
        
        try:
            # First try to extract text for classification
            text_content = ""
            
            if file_path.lower().endswith('.pdf'):
                # Use simple PDF text extraction for classification
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
            
            # Use AI to classify based on content
            if text_content and self.ai_processor.use_vertex:
                classification_prompt = f"""
                Analyze this document text and classify it as one of these mortgage document types:
                - payslip (salary statement, pay stub)
                - bank_statement (bank account statement)
                - id_proof (passport, driver license, ID card)
                - tax_document (tax return, W2, 1099)
                - employment_letter (employment verification)
                - utility_bill (electricity, gas, water bill)
                - property_document (deed, property papers)
                
                Text sample: {text_content[:1000]}
                
                Return only the document type from the list above.
                """
                
                try:
                    if self.ai_processor.vertex_model:
                        response = self.ai_processor.vertex_model.generate_content(classification_prompt)
                        classified_type = response.text.strip().lower()
                        
                        # Validate against known types
                        if classified_type in DOCUMENT_TYPES:
                            return classified_type
                except Exception as e:
                    logging.warning(f"AI classification failed: {str(e)}")
            
            # Fallback to filename-based classification
            filename_lower = os.path.basename(file_path).lower()
            
            if any(term in filename_lower for term in ['payslip', 'salary', 'pay']):
                return 'payslip'
            elif any(term in filename_lower for term in ['bank', 'statement']):
                return 'bank_statement'
            elif any(term in filename_lower for term in ['id', 'passport', 'license']):
                return 'id_proof'
            elif any(term in filename_lower for term in ['tax', 'w2', '1099']):
                return 'tax_document'
            elif any(term in filename_lower for term in ['employment', 'job']):
                return 'employment_letter'
            elif any(term in filename_lower for term in ['utility', 'bill', 'electric']):
                return 'utility_bill'
            else:
                return 'unknown'
                
        except Exception as e:
            logging.error(f"Document classification failed: {str(e)}")
            return 'unknown'
    
    def _analyze_complete_application(self, document_results: List[Dict[str, Any]], 
                                    application_id: str) -> Dict[str, Any]:
        """Perform application-level analysis using AI"""
        
        try:
            return self.ai_processor.analyze_application(document_results)
        except Exception as e:
            logging.error(f"Application analysis failed: {str(e)}")
            return {
                'summary': 'Application analysis could not be completed',
                'error': str(e)
            }
    
    def _validate_application_completeness(self, document_results: List[Dict[str, Any]], 
                                         application_id: str) -> Dict[str, Any]:
        """Validate completeness of the mortgage application"""
        
        try:
            return self.validator.validate_application_completeness(document_results)
        except Exception as e:
            logging.error(f"Application validation failed: {str(e)}")
            return {
                'is_complete': False,
                'error': str(e),
                'missing_required': [],
                'recommendations': ['Please review all documents and re-submit']
            }
    
    def _store_document_result(self, result: Dict[str, Any], application_id: str, 
                             borrower_info: Dict[str, Any]):
        """Store individual document processing result"""
        
        try:
            document_data = {
                'application_id': application_id,
                'document_type': result['document_type'],
                'filename': result['filename'],
                'file_path': result['file_path'],
                'file_hash': result['file_hash'],
                'upload_timestamp': result.get('processing_timestamp', datetime.now()),
                'processing_result': result,
                **borrower_info
            }
            
            self.db_manager.store_document(document_data)
            
        except Exception as e:
            logging.error(f"Failed to store document result: {str(e)}")
    
    def _store_batch_results(self, batch_result: Dict[str, Any]):
        """Store batch processing results"""
        
        try:
            self.db_manager.store_analysis_result(
                batch_result['application_id'],
                'batch_processing',
                batch_result
            )
        except Exception as e:
            logging.error(f"Failed to store batch results: {str(e)}")
    
    def get_processing_status(self, application_id: str) -> Dict[str, Any]:
        """Get processing status for an application"""
        
        try:
            documents = self.db_manager.get_application_documents(application_id)
            
            total_docs = len(documents)
            completed_docs = len([d for d in documents if d.get('processing_result', {}).get('status') == 'completed'])
            
            return {
                'application_id': application_id,
                'total_documents': total_docs,
                'completed_documents': completed_docs,
                'progress_percentage': (completed_docs / total_docs * 100) if total_docs > 0 else 0,
                'status': 'completed' if completed_docs == total_docs else 'processing'
            }
            
        except Exception as e:
            logging.error(f"Failed to get processing status: {str(e)}")
            return {
                'application_id': application_id,
                'status': 'error',
                'error': str(e)
            }