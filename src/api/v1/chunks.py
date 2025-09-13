"""Text chunking API endpoints."""

import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from pathlib import Path

from ...db.base import get_db
from ...db.models import Document, OCRResult, TextChunk, ProcessingStatus
from ...services.chunking_service import ChunkingService
from ...core.embeddings.chunker import ChunkConfig
from .auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chunks", tags=["chunks"])


@router.post("/process/{document_id}")
async def process_document_chunks(
    document_id: int,
    min_tokens: int = Query(1000, description="Minimum tokens per chunk"),
    max_tokens: int = Query(2000, description="Maximum tokens per chunk"),
    overlap_tokens: int = Query(200, description="Overlap tokens between chunks"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Process document into semantic chunks.

    Args:
        document_id: Document ID to process
        min_tokens: Minimum tokens per chunk
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap tokens between chunks
        db: Database session
        user_id: Current user ID

    Returns:
        Chunking process result
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if OCR results exist
    ocr_results = db.query(OCRResult).filter(
        OCRResult.document_id == document_id
    ).first()

    if not ocr_results:
        raise HTTPException(
            status_code=400,
            detail="Document must be OCR processed first"
        )

    # Configure chunking
    config = ChunkConfig(
        min_tokens=min_tokens,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        detect_structure=True,
        enable_deduplication=True
    )

    # Process chunks
    chunking_service = ChunkingService(config)

    try:
        chunks = chunking_service.process_document(document_id, db)

        return {
            "success": True,
            "document_id": document_id,
            "total_chunks": len(chunks),
            "message": f"Created {len(chunks)} chunks successfully"
        }
    except Exception as e:
        logger.error(f"Error processing chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document_chunks(
    document_id: int,
    include_hierarchy: bool = Query(False, description="Include parent-child hierarchy"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get all chunks for a document.

    Args:
        document_id: Document ID
        include_hierarchy: Include hierarchical relationships
        db: Database session
        user_id: Current user ID

    Returns:
        List of document chunks
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks
    chunking_service = ChunkingService()
    chunks = chunking_service.get_document_chunks(
        document_id, db, include_hierarchy
    )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "total_chunks": len(chunks),
        "chunks": chunks
    }


@router.get("/{document_id}/statistics")
async def get_chunk_statistics(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get chunking statistics for a document.

    Args:
        document_id: Document ID
        db: Database session
        user_id: Current user ID

    Returns:
        Chunk statistics
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get statistics
    chunking_service = ChunkingService()
    stats = chunking_service.get_chunk_statistics(document_id, db)

    return {
        "document_id": document_id,
        "filename": document.filename,
        "statistics": stats
    }


@router.get("/{document_id}/export")
async def export_chunks_to_text(
    document_id: int,
    format: str = Query("detailed", description="Export format: simple, detailed, or debug"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Export chunks to a text file for review.

    Args:
        document_id: Document ID
        format: Export format (simple, detailed, debug)
        db: Database session
        user_id: Current user ID

    Returns:
        Text file with chunks
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks
    chunks = db.query(TextChunk).filter(
        TextChunk.document_id == document_id
    ).order_by(TextChunk.chunk_index).all()

    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found for document")

    # Create export content
    export_lines = []
    export_lines.append("=" * 80)
    export_lines.append(f"DOCUMENT CHUNKS EXPORT")
    export_lines.append(f"Document: {document.filename}")
    export_lines.append(f"Document ID: {document_id}")
    export_lines.append(f"Total Chunks: {len(chunks)}")
    export_lines.append(f"Export Time: {datetime.utcnow().isoformat()}")
    export_lines.append(f"Format: {format}")
    export_lines.append("=" * 80)
    export_lines.append("")

    # Add statistics
    total_tokens = sum(c.token_count for c in chunks)
    avg_tokens = total_tokens / len(chunks) if chunks else 0

    export_lines.append("STATISTICS:")
    export_lines.append(f"  Total Tokens: {total_tokens}")
    export_lines.append(f"  Average Tokens per Chunk: {avg_tokens:.1f}")
    export_lines.append(f"  Min Tokens: {min(c.token_count for c in chunks)}")
    export_lines.append(f"  Max Tokens: {max(c.token_count for c in chunks)}")
    export_lines.append("")
    export_lines.append("=" * 80)
    export_lines.append("")

    # Export chunks based on format
    for i, chunk in enumerate(chunks, 1):
        export_lines.append(f"### CHUNK {i}/{len(chunks)} ###")
        export_lines.append(f"Index: {chunk.chunk_index}")
        export_lines.append(f"Tokens: {chunk.token_count}")

        if format in ["detailed", "debug"]:
            export_lines.append(f"Section: {chunk.section_title or 'None'}")
            export_lines.append(f"Pages: {chunk.start_page or '?'} - {chunk.end_page or '?'}")
            export_lines.append(f"Level: {chunk.chunk_level}")

            if chunk.parent_chunk_id:
                export_lines.append(f"Parent Chunk ID: {chunk.parent_chunk_id}")

        if format == "debug":
            export_lines.append(f"Character Range: {chunk.start_char} - {chunk.end_char}")
            export_lines.append(f"Metadata: {chunk.chunk_metadata}")
            export_lines.append(f"Embedding ID: {chunk.embedding_id or 'Not generated'}")

        export_lines.append("-" * 40)
        export_lines.append(chunk.content)
        export_lines.append("")
        export_lines.append("=" * 80)
        export_lines.append("")

    # Save to file
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    filename = f"chunks_{document_id}_{document.filename.replace('.pdf', '')}_{format}.txt"
    filepath = export_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(export_lines))

    logger.info(f"Exported chunks to {filepath}")

    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/{document_id}/preview")
async def preview_chunks(
    document_id: int,
    limit: int = Query(5, description="Number of chunks to preview"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Preview first few chunks for quick review.

    Args:
        document_id: Document ID
        limit: Number of chunks to preview
        db: Database session
        user_id: Current user ID

    Returns:
        Preview of chunks
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get first few chunks
    chunks = db.query(TextChunk).filter(
        TextChunk.document_id == document_id
    ).order_by(TextChunk.chunk_index).limit(limit).all()

    preview = []
    for chunk in chunks:
        preview.append({
            "index": chunk.chunk_index,
            "tokens": chunk.token_count,
            "section": chunk.section_title,
            "preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
        })

    return {
        "document_id": document_id,
        "filename": document.filename,
        "preview_count": len(preview),
        "total_chunks": db.query(TextChunk).filter(
            TextChunk.document_id == document_id
        ).count(),
        "previews": preview
    }