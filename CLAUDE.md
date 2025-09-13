# TLDRify - AI-Powered PDF Learning Platform

## 🎯 Project Overview
TLDRify는 PDF 문서를 AI 기반 학습 자료로 변환하는 플랫폼입니다. OCR, 임베딩, RAG를 통해 문서의 내용을 이해하고 요약, 질문 생성, Q&A를 제공합니다.

## 🏗️ Architecture Overview

### Core Flow
```
PDF Upload → OCR (Surya) → Text Extraction → Chunking → Embedding → Vector DB → RAG → AI Processing
```

### Technology Stack
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **Backend**: FastAPI (Python 3.11+)
- **ORM** : SQLAlchemy 2.x
- **OCR**: Surya OCR (Open-source, multilingual support)
- **Vector DB**: Qdrant
- **LLM**: OpenAI GPT-4 / Claude
- **Database**: PostgreSQL + Redis
- **Queue**: Celery + Redis
- **Container**: Docker

## 📁 Project Structure

```
tldrify/
├── frontend/                    # Next.js Frontend Application
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   │   ├── _components/    # Shared components
│   │   │   ├── _home/         # Home page components
│   │   │   └── api.ts         # API client
│   │   ├── hook/              # Custom React hooks
│   │   │   └── file/          # File handling hooks
│   │   ├── types/             # TypeScript definitions
│   │   └── util/              # Utility functions
│   └── package.json
│
├── src/                        # FastAPI Backend (To be implemented)
│   ├── api/                   # REST API endpoints
│   │   ├── v1/
│   │   │   ├── documents.py  # Document upload/management
│   │   │   ├── ocr.py        # OCR processing endpoints
│   │   │   ├── embeddings.py # Embedding generation
│   │   │   ├── rag.py        # RAG queries
│   │   │   └── summaries.py  # AI summarization
│   ├── core/                  # Core business logic
│   │   ├── ocr/              # OCR processing
│   │   │   ├── surya.py      # Surya OCR integration
│   │   │   └── processor.py  # Text extraction pipeline
│   │   ├── embeddings/       # Embedding generation
│   │   │   ├── chunker.py    # Semantic chunking
│   │   │   └── encoder.py    # Text to embeddings
│   │   ├── rag/              # RAG implementation
│   │   │   ├── retriever.py  # Vector search
│   │   │   └── generator.py  # Response generation
│   │   └── ai/               # AI services
│   │       ├── summarizer.py # Document summarization
│   │       └── qa.py         # Question generation
│   ├── db/                   # Database layer
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── vector.py         # Qdrant integration
│   │   └── redis.py          # Redis caching
│   ├── services/             # External services
│   │   ├── storage.py        # File storage (S3/local)
│   │   └── celery_app.py     # Async task queue
│   └── main.py               # FastAPI application
│
├── ocr-poc/                   # OCR Proof of Concept
│   ├── surya_test.py         # Surya OCR testing
│   └── benchmarks/           # Performance benchmarks
│
├── docker/                    # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── tests/                     # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── docs/                      # Documentation
    ├── api/                   # API documentation
    ├── architecture/          # System design docs
    └── deployment/           # Deployment guides
```

## 🔄 OCR-POC Implementation Flow

### Phase 1: Core Pipeline
1. **PDF Upload Service**
   - Chunked upload for large files (up to 100MB)
   - File validation and storage
   - Job queue initialization

2. **OCR Processing**
   - Surya OCR integration
   - Page-by-page processing
   - Text extraction with confidence scores
   - Fallback mechanisms for low-quality scans

3. **Text Processing**
   - Semantic chunking (1000-2000 tokens)
   - Metadata extraction (chapters, sections)
   - Language detection

### Phase 2: Intelligence Layer
4. **Embedding Generation**
   - OpenAI text-embedding-3-large
   - Batch processing for efficiency
   - Dimension reduction options

5. **Vector Storage**
   - Qdrant vector database setup
   - Collection management
   - Hybrid search (vector + BM25)

6. **RAG Implementation**
   - Context retrieval
   - Query expansion
   - Response generation with citations

### Phase 3: AI Features
7. **Summarization**
   - Multi-level summaries (document, chapter, section)
   - Key points extraction
   - Custom prompt engineering

8. **Question Generation**
   - Multiple choice questions
   - Short answer questions
   - Difficulty calibration

## 🔧 Development Guidelines

### Code Style
- Python: Black formatter, Ruff linter, type hints
- TypeScript: ESLint, Prettier
- Commit convention: Conventional Commits

### API Design
- RESTful principles
- Versioned endpoints (/api/v1/)
- OpenAPI documentation
- Consistent error responses

### Testing Strategy
- Unit tests: 80% coverage minimum
- Integration tests for critical paths
- E2E tests for user workflows

### Security
- JWT authentication
- Rate limiting
- Input validation
- File size restrictions
- Content type verification

## 🚀 Quick Start Commands

```bash
# Backend development
cd tldrify
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend development
cd frontend
npm install
npm run dev

# Docker development
docker-compose up -d

# Run tests
pytest tests/ -v
npm test

# Database migrations
alembic upgrade head

# Celery worker
celery -A src.services.celery_app worker --loglevel=info
```

## 📊 Performance Targets
- OCR Processing: < 5 seconds per page
- Embedding Generation: < 2 seconds per chunk
- RAG Query: < 3 seconds response time
- Summary Generation: < 10 seconds per document
- Concurrent users: 100+
- Storage: 10GB per user quota

## 🔍 Monitoring & Observability
- Application: Sentry for error tracking
- Infrastructure: CloudWatch/Prometheus
- Logs: Structured JSON logging
- Metrics: Response times, queue lengths, error rates

## 📝 Environment Variables

```env
# API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Database
DATABASE_URL=postgresql://user:pass@localhost/tldrify
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333

# Storage
STORAGE_TYPE=local  # or 's3'
UPLOAD_PATH=/data/uploads
MAX_FILE_SIZE=104857600  # 100MB

# Security
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# OCR
SURYA_MODEL_PATH=/models/surya
OCR_CONFIDENCE_THRESHOLD=0.8
```

## 🎯 Current Focus
The immediate priority is implementing the OCR-POC pipeline:
1. Surya OCR integration with FastAPI
2. Text extraction and chunking
3. Embedding generation and vector storage
4. Basic RAG query system
5. Simple summarization endpoint

## 📈 Success Metrics
- OCR accuracy: > 95% for standard PDFs
- Processing speed: 50 pages/minute
- Retrieval accuracy: > 85% relevant chunks
- Summary quality: > 4.0/5.0 user rating
- System uptime: > 99.9%

---
*Building intelligent document processing, one PDF at a time* 🚀