# TLDRify Development Guide

## 🚀 Current Status
**Phase 1 Complete:** OCR-to-Embedding Pipeline Operational

### ✅ Completed Tasks (Tasks #17-21)
- [x] **Task #17**: Chunked Upload System with logical FK architecture
- [x] **Task #18**: Surya OCR Integration with PyMuPDF fallback
- [x] **Task #19**: Semantic Text Chunking System with export functionality
- [x] **Task #20**: Qdrant Vector Database Setup with Docker
- [x] **Task #21**: OpenAI Embedding Generation with Redis caching

### 🔄 Major Refactoring Completed
- FastAPI endpoints refactored with dependency injection best practices
- SQLAlchemy upgraded to 2.x patterns with async support
- Database architecture: **Logical FK only** (no physical constraints)

## 🏗️ Architecture Overview

### Core Pipeline
```
PDF Upload → OCR (Surya/PyMuPDF) → Chunking → Embeddings → Vector DB
```

### Technology Stack
- **Backend**: FastAPI + SQLAlchemy 2.x + Celery
- **Database**: PostgreSQL (logical FK only) + Redis
- **Vector DB**: Qdrant with HNSW indexing
- **OCR**: Surya OCR + PyMuPDF fallback
- **Embeddings**: OpenAI text-embedding-3-large
- **Frontend**: Next.js 14 + TypeScript + TailwindCSS

## 🔧 Development Setup

### Prerequisites
```bash
# Python 3.11+
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Add your API keys: OPENAI_API_KEY, DATABASE_URL, etc.
```

### Database Setup
```bash
# Start PostgreSQL + Qdrant + Redis
docker-compose up -d postgres qdrant redis

# Run migrations
alembic upgrade head
```

### Start Services
```bash
# Backend API (Terminal 1)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend && npm run dev

# Celery Worker (Terminal 3)
celery -A src.services.celery_app worker --loglevel=info
```

## 📊 API Endpoints

### Document Management
- `POST /api/v1/upload/` - File upload (chunked for >10MB)
- `GET /api/v1/documents/` - List documents with pagination
- `GET /api/v1/documents/{id}` - Get document details

### OCR Processing
- `POST /api/v1/documents/{id}/ocr` - Process OCR (background task)
- `GET /api/v1/documents/{id}/ocr-status` - Check OCR status

### Text Chunking
- `POST /api/v1/documents/{id}/chunks` - Generate chunks
- `GET /api/v1/documents/{id}/chunks/export` - Export chunks (simple/detailed/debug)

### Embeddings
- `POST /api/v1/documents/{id}/embeddings/generate` - Generate embeddings
- `GET /api/v1/documents/{id}/embeddings/status` - Check embedding status

## 🗄️ Database Schema

### Key Models (Logical FK Only)
```python
class Document(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)  # Logical FK only
    filename = Column(String(255), nullable=False)
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    # No ORM relationships - using logical FK only

class TextChunk(Base):
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, nullable=False, index=True)  # Logical FK only
    content = Column(Text, nullable=False)
    embedding_id = Column(String(100), index=True)
    # No ORM relationships - using logical FK only
```

### Critical Architecture Decision
**User Requirement**: "model을 작성할 때 **물리적 FK**는 만들지 말아줘. 오직 논리적으로만 FK 를 맺어줘"

- No physical foreign key constraints in database
- No SQLAlchemy `relationship()` declarations
- All relationships maintained through simple integer columns
- Prevents circular dependency issues and provides flexibility

## 🧪 Testing

### Full Pipeline Test
```bash
python -c "
import asyncio
from tests.test_pipeline import test_full_pipeline
asyncio.run(test_full_pipeline())
"
```

### Expected Output
```
✅ Upload: Document uploaded successfully (ID: X)
✅ OCR: OCR completed successfully
✅ Chunking: X chunks created successfully
✅ Embeddings: Embeddings generated successfully
✅ Export: Export completed successfully
```

## 🔍 FastAPI Dependency Injection Patterns

### Database Dependencies
```python
from src.db.dependencies import DBSession, AsyncDBSession

@router.get("/documents/")
async def list_documents(
    pagination: PaginationDep,
    db: DBSession,
):
    # Automatic session management with proper exception handling
```

### Custom Dependency Classes
```python
class PaginationParams:
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ):
        self.skip = skip
        self.limit = limit

PaginationDep = Annotated[PaginationParams, Depends(PaginationParams)]
```

### File Validation Dependencies
```python
class FileValidator:
    async def __call__(self, file: UploadFileDep) -> UploadFile:
        if not self.validate_extension(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type")
        return file

FileValidatorDep = Annotated[UploadFile, Depends(FileValidator())]
```

## 📈 Performance Metrics

### Current Performance
- **OCR Processing**: < 3 seconds per page
- **Chunking**: < 1 second for standard documents
- **Embedding Generation**: < 2 seconds per chunk
- **Total Pipeline**: < 10 seconds for test documents

### Optimization Features
- Redis caching for embeddings (24-hour TTL)
- Batch processing for OpenAI API calls
- Background task processing with Celery
- Connection pooling for database operations

## 🛠️ Debugging & Development

### Common Issues

1. **Module Import Errors**
   ```bash
   # Use uv for package installation
   uv pip install package-name
   ```

2. **SQLAlchemy Relationship Errors**
   ```bash
   # Clear Python cache
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -delete
   ```

3. **OCR Processing Issues**
   ```bash
   # Check background task logs
   celery -A src.services.celery_app events
   ```

### Export Functionality
```bash
# Test chunking with export
curl -X GET "http://localhost:8000/api/v1/documents/13/chunks/export?format=detailed"

# Export formats available: simple, detailed, debug
```

## 🔐 Security & Best Practices

### API Security
- JWT authentication (planned)
- File type validation
- Size limits (100MB max)
- Rate limiting on endpoints

### Code Quality
- Type hints with `Annotated` dependencies
- Pydantic models for validation
- Proper error handling and rollback
- Async patterns for I/O operations

## 📝 Next Development Phases

### Phase 2: Intelligence Layer (Tasks #22-24)
- [ ] **Task #22**: RAG Query System
- [ ] **Task #23**: AI Summarization
- [ ] **Task #24**: Question Generation

### Phase 3: UI Enhancement
- [ ] Real-time processing status
- [ ] Document management interface
- [ ] Q&A interaction system

---
*Last updated: 2025-09-14*