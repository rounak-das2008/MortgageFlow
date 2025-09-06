# Mortgage Document Automation System

## Overview

This is a comprehensive mortgage document processing and automation web application built with Python and Streamlit. The system allows borrowers to upload mortgage-related documents (payslips, bank statements, ID proofs, tax documents) and provides automated document processing, validation, and assessment capabilities for mortgage assessors.

The application leverages Google Cloud Platform services for advanced document processing capabilities, with built-in fallback mechanisms to local processing when GCP services are unavailable. The system extracts text and structured data from documents, validates them against mortgage requirements, and provides intelligent insights through AI-powered analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework for rapid UI development
- **User Interface**: Role-based navigation with separate interfaces for borrowers and assessors
- **Session Management**: Streamlit session state for maintaining user context and application flow
- **Responsive Design**: Wide layout configuration with expandable sidebar navigation

### Backend Architecture
- **Modular Design**: Organized into distinct modules for upload, extraction, validation, dashboard, and AI processing
- **Database Abstraction**: DatabaseManager class provides abstraction layer supporting both GCP Firestore and SQLite
- **Processing Pipeline**: Sequential document processing through extraction → validation → AI analysis
- **Error Handling**: Comprehensive exception handling with graceful degradation

### Data Storage Solutions
- **Primary**: Google Cloud Firestore (NoSQL) for document metadata and processing results
- **Fallback**: SQLite database with structured tables for documents and applications
- **File Storage**: Google Cloud Storage for document files with local filesystem fallback
- **Caching**: In-memory session state caching for improved performance

### Document Processing Pipeline
- **Extraction Layer**: GCP Document AI for advanced OCR and structured data extraction, with Tesseract OCR fallback
- **Validation Engine**: Rule-based validation system with document-specific requirements
- **AI Analysis**: Google Gemini API integration for document summarization, risk assessment, and fraud detection
- **Quality Assessment**: Automated document quality scoring and recommendation generation

### Authentication and Authorization
- **Role-Based Access**: Simple role selection between Borrower and Assessor views
- **Application-Based Segmentation**: Document access controlled by application ID
- **GCP Integration**: Support for Google Cloud IAM when using GCP services

## External Dependencies

### Google Cloud Platform Services
- **Document AI**: Advanced OCR and structured document processing
- **Cloud Storage**: Secure document file storage and retrieval
- **Firestore**: NoSQL database for metadata and processing results storage
- **Gemini AI**: Natural language processing for document analysis and insights

### Python Libraries
- **Streamlit**: Web application framework for user interface
- **PIL (Pillow)**: Image processing and manipulation
- **PyPDF2**: PDF document parsing and text extraction
- **Pytesseract**: Fallback OCR processing engine
- **Pandas**: Data manipulation and analysis for dashboard features
- **Plotly**: Interactive visualization components for analytics

### Local Fallback Systems
- **SQLite**: Local database when Firestore is unavailable
- **Local Filesystem**: Document storage when Cloud Storage is unavailable
- **Tesseract OCR**: Local text extraction when Document AI is unavailable

### Development and Deployment
- **Environment Variables**: Configuration management for API keys and service credentials
- **Logging**: Comprehensive logging system for debugging and monitoring
- **Error Recovery**: Graceful fallback mechanisms for service unavailability