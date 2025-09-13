"""Service for processing and storing text chunks in database."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..core.embeddings.chunker import SemanticChunker, ChunkConfig, TextChunk
from ..db.models import Document, OCRResult, TextChunk as DBTextChunk, ProcessingStatus
from ..db.base import get_db

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for managing text chunking and database storage."""

    def __init__(self, chunk_config: Optional[ChunkConfig] = None):
        """Initialize chunking service."""
        self.chunker = SemanticChunker(chunk_config)
        logger.info("Initialized ChunkingService")

    def process_document(self, document_id: int, db: Session) -> List[DBTextChunk]:
        """
        Process a document's OCR results into chunks.

        Args:
            document_id: Document ID to process
            db: Database session

        Returns:
            List of created database chunk objects
        """
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Get OCR results
        ocr_results = db.query(OCRResult).filter(
            OCRResult.document_id == document_id
        ).order_by(OCRResult.page_number).all()

        if not ocr_results:
            raise ValueError(f"No OCR results found for document {document_id}")

        logger.info(f"Processing {len(ocr_results)} pages for document {document_id}")

        # Combine text with page tracking
        full_text = []
        page_breaks = []
        current_pos = 0

        for ocr_result in ocr_results:
            text = ocr_result.text_content or ""
            full_text.append(text)
            current_pos += len(text)
            page_breaks.append(current_pos)

        combined_text = "\n\n".join(full_text)

        # Create chunks
        chunks = self.chunker.chunk_text(
            combined_text,
            document_id=document_id,
            page_breaks=page_breaks[:-1]  # Exclude last position
        )

        logger.info(f"Created {len(chunks)} chunks for document {document_id}")

        # Store chunks in database
        db_chunks = self._store_chunks(chunks, document_id, db)

        # Update document status
        document.status = ProcessingStatus.COMPLETED
        db.commit()

        return db_chunks

    def _store_chunks(self, chunks: List[TextChunk], document_id: int,
                     db: Session) -> List[DBTextChunk]:
        """Store chunks in database."""
        db_chunks = []

        # Delete existing chunks for document (if any)
        db.query(DBTextChunk).filter(
            DBTextChunk.document_id == document_id
        ).delete()

        # Create parent chunk mapping
        parent_map = {}

        # First pass: Create all chunks
        for chunk in chunks:
            db_chunk = DBTextChunk(
                document_id=document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                token_count=chunk.token_count,
                start_page=chunk.start_page,
                end_page=chunk.end_page,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                section_title=chunk.section_title,
                chunk_level=chunk.chunk_level,
                chunk_metadata=chunk.metadata
            )
            db.add(db_chunk)
            db.flush()  # Get ID

            db_chunks.append(db_chunk)

            # Track parent chunks
            if chunk.chunk_level == 0 and chunk.metadata and chunk.metadata.get('is_parent'):
                parent_map[chunk.chunk_index] = db_chunk.id

        # Second pass: Update parent relationships
        for chunk, db_chunk in zip(chunks, db_chunks):
            if chunk.parent_chunk_id is not None and chunk.parent_chunk_id in parent_map:
                db_chunk.parent_chunk_id = parent_map[chunk.parent_chunk_id]

        db.commit()
        logger.info(f"Stored {len(db_chunks)} chunks in database")

        return db_chunks

    def get_document_chunks(self, document_id: int, db: Session,
                          include_hierarchy: bool = False) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document ID
            db: Database session
            include_hierarchy: Include parent-child relationships

        Returns:
            List of chunk dictionaries
        """
        query = db.query(DBTextChunk).filter(
            DBTextChunk.document_id == document_id
        )

        if not include_hierarchy:
            # Only get main level chunks
            query = query.filter(DBTextChunk.chunk_level == 0)

        chunks = query.order_by(DBTextChunk.chunk_index).all()

        return [self._chunk_to_dict(chunk) for chunk in chunks]

    def _chunk_to_dict(self, chunk: DBTextChunk) -> Dict[str, Any]:
        """Convert database chunk to dictionary."""
        return {
            'id': chunk.id,
            'document_id': chunk.document_id,
            'chunk_index': chunk.chunk_index,
            'content': chunk.content,
            'token_count': chunk.token_count,
            'start_page': chunk.start_page,
            'end_page': chunk.end_page,
            'section_title': chunk.section_title,
            'chunk_level': chunk.chunk_level,
            'parent_chunk_id': chunk.parent_chunk_id,
            'metadata': chunk.chunk_metadata,
            'embedding_id': chunk.embedding_id,
            'created_at': chunk.created_at.isoformat() if chunk.created_at else None
        }

    def search_chunks(self, document_id: int, query: str, db: Session,
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search chunks by text content (simple text search).

        Args:
            document_id: Document ID
            query: Search query
            db: Database session
            limit: Maximum results

        Returns:
            List of matching chunks
        """
        # Simple text search (will be replaced with vector search later)
        chunks = db.query(DBTextChunk).filter(
            DBTextChunk.document_id == document_id,
            DBTextChunk.content.ilike(f'%{query}%')
        ).limit(limit).all()

        return [self._chunk_to_dict(chunk) for chunk in chunks]

    def get_chunk_statistics(self, document_id: int, db: Session) -> Dict[str, Any]:
        """Get statistics about document chunks."""
        chunks = db.query(DBTextChunk).filter(
            DBTextChunk.document_id == document_id
        ).all()

        if not chunks:
            return {
                'total_chunks': 0,
                'avg_token_count': 0,
                'min_token_count': 0,
                'max_token_count': 0,
                'total_tokens': 0,
                'hierarchy_levels': 0
            }

        token_counts = [c.token_count for c in chunks]
        hierarchy_levels = len(set(c.chunk_level for c in chunks))

        return {
            'total_chunks': len(chunks),
            'avg_token_count': sum(token_counts) / len(token_counts),
            'min_token_count': min(token_counts),
            'max_token_count': max(token_counts),
            'total_tokens': sum(token_counts),
            'hierarchy_levels': hierarchy_levels,
            'parent_chunks': sum(1 for c in chunks if c.chunk_level == 0 and c.chunk_metadata and c.chunk_metadata.get('is_parent')),
            'child_chunks': sum(1 for c in chunks if c.chunk_level > 0)
        }