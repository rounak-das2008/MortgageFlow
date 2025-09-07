Create a high-level system architecture diagram for a mortgage document automation platform with the following components and flow:

**User Interface Layer:**
- Streamlit Web App (main entry point)
- Borrower Interface (document upload, application tracking)
- Assessor Interface (document review, analytics, decision making)

**Core Processing Layer:**
- Document Upload Interface (handles file validation and classification)
- Batch Document Processor (parallel processing of multiple documents)
- Dashboard Module (analytics and application management)

**Document Processing Pipeline:**
- Document Extractor (text and data extraction using OCR)
- Document Validator (validates document types, recency, completeness)
- AI Processor (document analysis, fraud detection, risk assessment)

**Google Cloud Services:**
- Document AI (advanced OCR and form parsing)
- Vertex AI/Gemini (AI analysis and document summarization)
- Cloud Storage (document file storage)
- Firestore (application data database)

**Data Storage:**
- SQLite Database (local fallback)
- File System (document storage)

**Key Flow:**
1. User uploads documents through Streamlit interface
2. Documents are validated and classified by type
3. Batch processor handles multiple documents in parallel
4. Document extractor uses GCP Document AI or local OCR
5. Validator checks document requirements and recency
6. AI processor analyzes documents for fraud and risk
7. Results stored in Firestore (cloud) or SQLite (fallback)
8. Dashboard displays analytics and processing results

**Key Features:**
- Dual-role interface (borrower/assessor)
- Parallel document processing
- AI-powered analysis and fraud detection
- Cloud-first with local fallbacks
- Real-time progress tracking
- Comprehensive validation and error handling

Show the data flow with arrows, use different colors for different layers, and keep it clean and professional. Focus on the main services, data flow, and key decision points.