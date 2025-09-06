# Smart Mortgage Document Analyzer

A comprehensive mortgage document processing and automation system built with Python, Streamlit, and Google Cloud Platform services.

## 🏠 Overview

This application automates the mortgage document processing workflow, allowing borrowers to upload multiple documents at once and providing intelligent analysis, validation, and insights for mortgage assessors.

### Key Features

- **Batch Document Upload**: Upload all mortgage documents at once for efficient processing
- **Intelligent Document Classification**: Automatically categorize documents using AI
- **Advanced Text Extraction**: Extract key information using GCP Document AI with OCR fallback
- **Smart Validation**: Automated document validation with recency checks and completeness verification  
- **AI-Powered Analysis**: Document summarization, fraud detection, and risk assessment using Vertex AI
- **Professional Interface**: Modern, bank-style UI optimized for mortgage workflows
- **Real-time Processing**: Live progress tracking and status updates
- **Comprehensive Dashboards**: Role-based views for borrowers and assessors

## 🛠 Technology Stack

### Primary (GCP Services)
- **Vertex AI**: Advanced document analysis and AI insights
- **Document AI**: OCR and structured data extraction
- **Cloud Storage**: Secure document storage
- **Firestore**: NoSQL database for metadata and results

### Fallback Solutions  
- **Gemini API**: Alternative AI processing when Vertex AI unavailable
- **Tesseract OCR**: Local text extraction fallback
- **SQLite**: Local database when Firestore unavailable
- **Local Filesystem**: Document storage fallback

### Framework & Libraries
- **Streamlit**: Web application framework
- **Python 3.11**: Core programming language
- **PyPDF2**: PDF text extraction
- **Pillow (PIL)**: Image processing
- **Pandas**: Data manipulation for analytics
- **Plotly**: Interactive visualizations

## 📋 Supported Documents

### Required Documents
- **ID Proof**: Passport, Driver License, National ID
- **Payslip**: Recent salary statements (last 3 months)
- **Bank Statement**: Account statements (last 3 months)  
- **Employment Letter**: Employment verification from employer

### Optional Documents
- **Tax Documents**: Tax returns, W2 forms, 1099 forms
- **Utility Bills**: Address verification documents
- **Property Documents**: Deeds, property valuations
- **Credit Reports**: Credit history and scores
- **Investment Statements**: Asset documentation

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Google Cloud Platform account with enabled services:
  - Vertex AI API
  - Document AI API
  - Cloud Storage API
  - Firestore API

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mortgage-document-automation
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure GCP Services**
   ```bash
   # Set your GCP project
   export GCP_PROJECT_ID="genai-hackathon-25"
   export GCP_LOCATION="us-central1"
   export GCS_BUCKET_NAME="your-bucket-name"
   ```

4. **Set up API keys**
   - Add your Gemini API key to environment variables:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py --server.port 5000
   ```

## 📖 Usage Guide

### For Borrowers

1. **Start Application**
   - Select "Borrower" role in the sidebar
   - Navigate to "Upload Documents"

2. **Provide Information**
   - Enter personal details (name, email, phone, loan amount)
   - Generate new application ID or use existing one

3. **Upload Documents**
   - Select all documents at once using the file picker
   - System automatically suggests document types
   - Verify and adjust document classifications

4. **Configure Processing**
   - Enable auto-validation for requirement checks
   - Turn on AI analysis for summaries and insights
   - Enable fraud detection for security

5. **Submit & Track**
   - Submit all documents for batch processing
   - Monitor real-time processing progress
   - Review results and recommendations

### For Assessors

1. **Access Dashboard**
   - Select "Assessor" role in the sidebar
   - View "Assessment Dashboard" for overview

2. **Review Applications**
   - See all submitted applications with status
   - Filter by document type, status, or date
   - View completion rates and metrics

3. **Document Analysis**
   - Access detailed document review interface
   - Review AI-generated insights and risk assessments
   - Approve, request changes, or reject documents

4. **Analytics & Reporting**
   - View processing analytics and trends
   - Monitor validation success rates
   - Access AI insights and fraud indicators

## 🏗 Architecture

### Document Processing Pipeline

1. **Capture**: Batch document upload with validation
2. **Classify**: AI-powered document type identification  
3. **Extract**: OCR and structured data extraction using Document AI
4. **Enrich**: AI analysis for summaries, insights, and risk assessment
5. **Validate**: Business rules validation and completeness checks
6. **Review**: Human assessor review and approval workflow

### Data Flow

```
Upload → Classification → Extraction → AI Analysis → Validation → Storage → Dashboard
```

### Security & Compliance

- Secure file storage with encryption
- PII detection and handling
- Audit trail for all document operations
- Role-based access control
- Data retention policies

## 🔧 Configuration

### Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID="genai-hackathon-25"
GCP_LOCATION="us-central1"
GCS_BUCKET_NAME="mortgage-documents-bucket"

# API Keys
GEMINI_API_KEY="your-gemini-api-key"

# Optional Settings
LOG_LEVEL="INFO"
MAX_FILE_SIZE_MB="10"
```

### Streamlit Configuration

The application uses `.streamlit/config.toml` for Streamlit-specific settings:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## 🐛 Troubleshooting

### Common Issues

1. **GCP Service Unavailable**
   - Check GCP credentials and project configuration
   - Verify API services are enabled
   - Application automatically falls back to local alternatives

2. **Document Processing Fails**
   - Ensure documents are in supported formats (PDF, JPG, PNG, TIFF)
   - Check file size limits (max 10MB per file)
   - Verify document quality and readability

3. **AI Analysis Not Working**
   - Confirm Vertex AI is properly configured
   - Check Gemini API key is valid
   - Review application logs for specific errors

### Logs and Debugging

- Application logs are written to console and can be viewed in the terminal
- Enable debug logging by setting `LOG_LEVEL=DEBUG`
- Check browser console for frontend errors
- Use Streamlit's built-in error handling and display

## 📈 Performance Optimization

- **Parallel Processing**: Documents are processed concurrently for faster throughput
- **Intelligent Caching**: Results are cached to avoid redundant processing
- **Progressive Loading**: UI updates in real-time during processing
- **Resource Management**: Automatic cleanup of temporary files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/new-feature`)
7. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Google Cloud Document AI](https://cloud.google.com/document-ai)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Gemini API Documentation](https://ai.google.dev/docs)

## 📞 Support

For questions, issues, or feature requests:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above

---

**Built with ❤️ for efficient mortgage processing**