"""SQLAlchemy models for TLDRify."""

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Float, Boolean,
    JSON, Index, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .base import Base


class ProcessingStatus(enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    OCR_PROCESSING = "ocr_processing"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(enum.Enum):
    """Supported document types."""
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Note: No ORM relationships - using logical FK only


class Document(Base):
    """Document model for storing PDF/file metadata."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Logical FK only

    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    file_hash = Column(String(64), index=True)  # SHA-256 hash for deduplication
    mime_type = Column(String(100))
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.PDF)

    # Processing information
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)

    # Document metadata
    title = Column(String(500))
    language = Column(String(10))  # ISO 639-1 code
    page_count = Column(Integer)
    word_count = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Note: No ORM relationships - using logical FK only

    # Indexes
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_created_at', 'created_at'),
    )


class OCRResult(Base):
    """OCR processing results for each page."""
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False, index=True)  # Logical FK only

    page_number = Column(Integer, nullable=False)
    text_content = Column(Text)
    confidence_score = Column(Float)  # 0.0 to 1.0
    processing_time = Column(Float)  # in seconds
    ocr_engine = Column(String(50))  # 'surya', 'pymupdf', etc.

    # Metadata
    bbox_data = Column(JSON)  # Bounding box information
    language_detected = Column(String(10))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: No ORM relationships - using logical FK only

    # Indexes
    __table_args__ = (
        Index('idx_document_page', 'document_id', 'page_number'),
        UniqueConstraint('document_id', 'page_number', name='uq_document_page'),
    )


class TextChunk(Base):
    """Text chunks for embedding and retrieval."""
    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False, index=True)  # Logical FK only

    # Chunk information
    chunk_index = Column(Integer, nullable=False)  # Order within document
    content = Column(Text, nullable=False)
    token_count = Column(Integer)

    # Position information
    start_page = Column(Integer)
    end_page = Column(Integer)
    start_char = Column(Integer)
    end_char = Column(Integer)

    # Hierarchy
    parent_chunk_id = Column(Integer, index=True)  # Logical self-reference
    chunk_level = Column(Integer, default=0)  # 0=main, 1=sub-chunk, etc.

    # Metadata
    section_title = Column(String(500))
    chunk_metadata = Column(JSON)  # Additional metadata like headers, formatting

    # Embedding information
    embedding_id = Column(String(100), index=True)  # Reference to vector DB
    embedding_model = Column(String(100))
    embedding_dimension = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: No ORM relationships - using logical FK only

    # Indexes
    __table_args__ = (
        Index('idx_document_chunk', 'document_id', 'chunk_index'),
        Index('idx_embedding_id', 'embedding_id'),
    )


class Summary(Base):
    """Document and chunk summaries."""
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False, index=True)  # Logical FK only
    chunk_id = Column(Integer, index=True)  # Optional logical FK

    summary_type = Column(String(50))  # 'document', 'chapter', 'section'
    summary_level = Column(String(50))  # 'brief', 'detailed', 'comprehensive'
    content = Column(Text, nullable=False)

    # Generation metadata
    model_used = Column(String(100))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    generation_time = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: No ORM relationships - using logical FK only

    # Indexes
    __table_args__ = (
        Index('idx_document_summary_type', 'document_id', 'summary_type'),
    )


class Query(Base):
    """User queries and RAG interactions."""
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Logical FK only
    document_id = Column(Integer, index=True)  # Optional logical FK

    # Query information
    query_text = Column(Text, nullable=False)
    query_embedding_id = Column(String(100))

    # Response information
    response_text = Column(Text)
    retrieved_chunks = Column(JSON)  # List of chunk IDs and scores
    citations = Column(JSON)  # Source references

    # Performance metrics
    retrieval_time = Column(Float)
    generation_time = Column(Float)
    total_time = Column(Float)

    # Model information
    retrieval_model = Column(String(100))
    generation_model = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: No ORM relationships - using logical FK only

    # Indexes
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )


class ProcessingJob(Base):
    """Async job tracking for Celery tasks."""
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)  # Celery task ID
    document_id = Column(Integer, index=True)  # Optional logical FK

    job_type = Column(String(50), nullable=False)  # 'ocr', 'embedding', 'summary'
    status = Column(String(50), default="pending")  # 'pending', 'processing', 'completed', 'failed'

    # Progress tracking
    current_step = Column(String(100))
    total_steps = Column(Integer)
    completed_steps = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    # Error handling
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Indexes
    __table_args__ = (
        Index('idx_job_status', 'job_id', 'status'),
        Index('idx_document_job', 'document_id', 'job_type'),
    )