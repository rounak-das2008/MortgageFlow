# MortgageFlow System Architecture - Complete Mermaid Diagram

## High-Level System Architecture

```mermaid
graph TB
    %% User Interface Layer
    subgraph "User Interface Layer"
        UI[Streamlit Web App<br/>app.py]
        BORROWER[Borrower Interface<br/>Upload Documents<br/>My Applications]
        ASSESSOR[Assessor Interface<br/>Assessment Dashboard<br/>Document Review<br/>Analytics]
    end

    %% Core Application Layer
    subgraph "Core Application Layer"
        UPLOAD[Upload Interface<br/>upload_interface.py]
        BATCH[Batch Processor<br/>batch_processor.py]
        DASHBOARD[Dashboard Module<br/>dashboard.py]
        DB_MGR[Database Manager<br/>database.py]
    end

    %% Document Processing Pipeline
    subgraph "Document Processing Pipeline"
        EXTRACT[Document Extractor<br/>extract.py]
        VALIDATE[Document Validator<br/>validate.py]
        AI_PROC[AI Processor<br/>ai_processor.py]
        SIMPLE_AI[Simple AI Processor<br/>simple_ai_processor.py]
    end

    %% GCP Services Layer
    subgraph "GCP Services Layer"
        GCP[GCP Services<br/>gcp_services.py]
        DOC_AI[Document AI<br/>Form Parser<br/>Bank Statement<br/>ID Processor]
        VERTEX[Vertex AI<br/>Gemini Models]
        STORAGE[Cloud Storage<br/>Document Storage]
        FIRESTORE[Firestore<br/>NoSQL Database]
    end

    %% Data Storage Layer
    subgraph "Data Storage Layer"
        SQLITE[(SQLite Database<br/>Local Fallback)]
        FILES[File System<br/>Document Storage<br/>previous_uploads/]
    end

    %% Utilities and Configuration
    subgraph "Utilities & Configuration"
        DOC_TYPES[Document Types<br/>document_types.py]
        HELPERS[Helper Functions<br/>helpers.py]
        CONFIG[Configuration<br/>pyproject.toml<br/>Environment Variables]
    end

    %% User Flow Connections
    UI --> BORROWER
    UI --> ASSESSOR
    BORROWER --> UPLOAD
    ASSESSOR --> DASHBOARD

    %% Upload Flow
    UPLOAD --> BATCH
    BATCH --> EXTRACT
    BATCH --> VALIDATE
    BATCH --> AI_PROC
    BATCH --> SIMPLE_AI

    %% Processing Pipeline
    EXTRACT --> GCP
    EXTRACT --> DOC_AI
    VALIDATE --> DOC_TYPES
    AI_PROC --> VERTEX
    AI_PROC --> GCP
    SIMPLE_AI --> VERTEX

    %% Data Storage
    BATCH --> DB_MGR
    DB_MGR --> FIRESTORE
    DB_MGR --> SQLITE
    BATCH --> FILES
    GCP --> STORAGE
    GCP --> FIRESTORE

    %% Dashboard Data Flow
    DASHBOARD --> DB_MGR
    DASHBOARD --> AI_PROC

    %% Utility Dependencies
    UPLOAD --> DOC_TYPES
    UPLOAD --> HELPERS
    BATCH --> DOC_TYPES
    BATCH --> HELPERS
    VALIDATE --> DOC_TYPES

    %% Configuration
    GCP --> CONFIG
    AI_PROC --> CONFIG
    SIMPLE_AI --> CONFIG

    %% Styling
    classDef userInterface fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef coreApp fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef processing fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef gcp fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef utils fill:#f1f8e9,stroke:#33691e,stroke-width:2px

    class UI,BORROWER,ASSESSOR userInterface
    class UPLOAD,BATCH,DASHBOARD,DB_MGR coreApp
    class EXTRACT,VALIDATE,AI_PROC,SIMPLE_AI processing
    class GCP,DOC_AI,VERTEX,STORAGE,FIRESTORE gcp
    class SQLITE,FILES storage
    class DOC_TYPES,HELPERS,CONFIG utils
```

## Detailed Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User (Borrower/Assessor)
    participant UI as Streamlit UI
    participant UP as Upload Interface
    participant BP as Batch Processor
    participant EX as Document Extractor
    participant VA as Document Validator
    participant AI as AI Processor
    participant DB as Database Manager
    participant GCP as GCP Services
    participant FS as File System

    Note over U,FS: Document Upload and Processing Flow

    U->>UI: Access Application
    UI->>U: Show Role Selection (Borrower/Assessor)
    
    alt Borrower Role
        U->>UI: Select "Upload Documents"
        UI->>UP: Initialize Upload Interface
        UP->>U: Show Document Requirements
        U->>UP: Upload Multiple Documents
        UP->>UP: Validate File Types & Sizes
        UP->>UP: Classify Documents by Type
        U->>UP: Confirm Processing Options
        UP->>BP: Start Batch Processing
        
        BP->>FS: Save Uploaded Files
        BP->>EX: Extract Text & Data (Parallel)
        EX->>GCP: Use Document AI (if available)
        GCP-->>EX: Return Extracted Data
        EX-->>BP: Return Extraction Results
        
        BP->>VA: Validate Documents (Parallel)
        VA->>VA: Check Required Fields
        VA->>VA: Validate Document Recency
        VA->>VA: Check Data Formats
        VA-->>BP: Return Validation Results
        
        BP->>AI: Analyze Documents (Parallel)
        AI->>GCP: Use Vertex AI/Gemini
        GCP-->>AI: Return AI Analysis
        AI-->>BP: Return Analysis Results
        
        BP->>DB: Store All Results
        DB->>GCP: Store in Firestore (if available)
        DB->>DB: Store in SQLite (fallback)
        DB-->>BP: Confirm Storage
        
        BP-->>UP: Return Batch Results
        UP-->>U: Show Processing Results & Analysis
        
    else Assessor Role
        U->>UI: Login with Credentials
        UI->>U: Show Assessment Dashboard
        U->>UI: Select Application to Review
        UI->>DB: Fetch Application Data
        DB-->>UI: Return Documents & Analysis
        UI->>U: Display Application Details
        U->>UI: Review Documents & Make Decisions
    end
```

## System Components Overview

```mermaid
graph LR
    subgraph "Frontend Layer"
        A[Streamlit Web Interface]
    end
    
    subgraph "Business Logic Layer"
        B[Upload Management]
        C[Document Processing]
        D[AI Analysis]
        E[Dashboard & Analytics]
    end
    
    subgraph "Data Processing Layer"
        F[Text Extraction]
        G[Document Validation]
        H[AI Processing]
        I[Batch Operations]
    end
    
    subgraph "External Services"
        J[Google Cloud Platform]
        K[Document AI]
        L[Vertex AI/Gemini]
        M[Cloud Storage]
        N[Firestore]
    end
    
    subgraph "Data Storage"
        O[SQLite Database]
        P[File System]
    end
    
    A --> B
    A --> E
    B --> C
    C --> D
    C --> F
    C --> G
    C --> H
    C --> I
    F --> J
    F --> K
    H --> L
    D --> J
    I --> M
    I --> N
    I --> O
    I --> P
    E --> O
    E --> N
```

## Document Processing Pipeline Detail

```mermaid
flowchart TD
    START([Document Upload]) --> VALIDATE{File Validation}
    VALIDATE -->|Valid| CLASSIFY[Document Classification]
    VALIDATE -->|Invalid| ERROR1[Show Error Message]
    
    CLASSIFY --> EXTRACT[Text & Data Extraction]
    EXTRACT --> GCP_CHECK{GCP Available?}
    GCP_CHECK -->|Yes| DOC_AI[Document AI Processing]
    GCP_CHECK -->|No| TESSERACT[Tesseract OCR Fallback]
    
    DOC_AI --> PARSE[Parse Extracted Data]
    TESSERACT --> PARSE
    
    PARSE --> VALIDATE_DOC[Document Validation]
    VALIDATE_DOC --> AI_ANALYSIS[AI Analysis]
    
    AI_ANALYSIS --> GEMINI_CHECK{Gemini Available?}
    GEMINI_CHECK -->|Yes| GEMINI[Gemini AI Analysis]
    GEMINI_CHECK -->|No| BASIC[Basic Analysis]
    
    GEMINI --> STORE[Store Results]
    BASIC --> STORE
    
    STORE --> DB_CHECK{Database Available?}
    DB_CHECK -->|Firestore| FIRESTORE_DB[(Firestore)]
    DB_CHECK -->|SQLite| SQLITE_DB[(SQLite)]
    
    FIRESTORE_DB --> COMPLETE([Processing Complete])
    SQLITE_DB --> COMPLETE
    
    ERROR1 --> START
    
    classDef process fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef storage fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    
    class EXTRACT,CLASSIFY,PARSE,VALIDATE_DOC,AI_ANALYSIS,GEMINI,BASIC,STORE process
    class VALIDATE,GCP_CHECK,GEMINI_CHECK,DB_CHECK decision
    class FIRESTORE_DB,SQLITE_DB storage
    class ERROR1 error
```

## Key Features and Capabilities

### 1. **Multi-Role Interface**
- **Borrower Interface**: Document upload, application tracking
- **Assessor Interface**: Document review, analytics, decision making

### 2. **Document Processing Pipeline**
- **Batch Processing**: Handle multiple documents simultaneously
- **Parallel Processing**: Concurrent document analysis for speed
- **Fallback Systems**: Local processing when cloud services unavailable

### 3. **AI-Powered Analysis**
- **Document Summarization**: AI-generated document summaries
- **Fraud Detection**: Automated fraud indicator analysis
- **Risk Assessment**: Application risk evaluation
- **Smart Recommendations**: AI-driven improvement suggestions

### 4. **Robust Data Management**
- **Dual Database Support**: Firestore (cloud) + SQLite (local)
- **File Integrity**: SHA-256 hashing for document verification
- **Comprehensive Validation**: Document type, recency, format validation

### 5. **GCP Integration**
- **Document AI**: Advanced OCR and form parsing
- **Vertex AI**: Gemini models for intelligent analysis
- **Cloud Storage**: Scalable document storage
- **Firestore**: Real-time database for application data

### 6. **User Experience Features**
- **Progress Tracking**: Real-time processing status
- **Interactive Dashboards**: Rich analytics and visualizations
- **Smart Classification**: Automatic document type detection
- **Comprehensive Validation**: Pre-upload file validation

This system provides a complete end-to-end solution for mortgage document automation, combining modern web technologies with advanced AI capabilities and robust cloud infrastructure.
