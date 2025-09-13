"""Embedding generation API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from ...db.base import get_db
from ...db.models import Document, TextChunk, ProcessingStatus, ProcessingJob
from ...db.vector import vector_db
from ...core.embeddings.encoder import embedding_service
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/{document_id}/generate")
async def generate_embeddings(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    batch_size: int = Query(100, description="Batch size for processing"),
    use_cache: bool = Query(True, description="Use cached embeddings if available"),
):
    """
    Generate embeddings for all chunks of a document.

    This endpoint triggers the embedding generation process for a document
    that has already been OCR'd and chunked.
    """
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if document is ready for embedding
    if document.status not in [ProcessingStatus.COMPLETED, ProcessingStatus.EMBEDDING]:
        raise HTTPException(
            status_code=400,
            detail=f"Document must be processed before generating embeddings. Current status: {document.status.value}"
        )

    # Get chunks
    chunks = db.query(TextChunk).filter(
        TextChunk.document_id == document_id
    ).all()

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No chunks found for document. Please run chunking first."
        )

    # Create processing job
    import uuid
    job = ProcessingJob(
        job_id=str(uuid.uuid4()),
        document_id=document_id,
        job_type="embedding_generation",
        status="pending",
        total_steps=len(chunks),
        completed_steps=0
    )
    db.add(job)
    db.commit()

    # Start background task
    background_tasks.add_task(
        process_embeddings_task,
        document_id=document_id,
        job_id=job.id,
        batch_size=batch_size,
        use_cache=use_cache
    )

    return {
        "message": f"Embedding generation started for {len(chunks)} chunks",
        "job_id": job.id,
        "document_id": document_id,
        "total_chunks": len(chunks)
    }


async def process_embeddings_task(
    document_id: int,
    job_id: int,
    batch_size: int = 100,
    use_cache: bool = True
):
    """Background task to generate and store embeddings."""
    from ...db.base import SessionLocal
    db = SessionLocal()

    try:
        # Update job status
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()

        # Update document status
        document = db.query(Document).filter(Document.id == document_id).first()
        document.status = ProcessingStatus.EMBEDDING
        db.commit()

        # Get all chunks
        chunks = db.query(TextChunk).filter(
            TextChunk.document_id == document_id
        ).order_by(TextChunk.chunk_index).all()

        logger.info(f"Processing {len(chunks)} chunks for document {document_id}")

        # Create collection in Qdrant if not exists
        collection_name = f"document_{document_id}"
        await vector_db.create_collection(
            collection_name=collection_name,
            vector_size=1536,  # text-embedding-3-large
            on_disk=False
        )

        # Process chunks in batches
        processed_count = 0
        total_cost = 0.0

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]

            # Prepare chunk data for embedding service
            chunk_data = []
            for chunk in batch_chunks:
                chunk_data.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,  # Fixed: use 'content' not 'text'
                    "metadata": chunk.chunk_metadata or {}
                })

            # Generate embeddings
            chunks_with_embeddings = await embedding_service.embed_document_chunks(
                chunks=chunk_data,
                use_fallback=False
            )

            # Prepare vectors and payloads for Qdrant
            vectors = []
            payloads = []

            for chunk_with_emb in chunks_with_embeddings:
                if "embedding" in chunk_with_emb:
                    vectors.append(chunk_with_emb["embedding"])
                    payloads.append({
                        "chunk_id": chunk_with_emb["chunk_id"],
                        "document_id": chunk_with_emb["document_id"],
                        "chunk_index": chunk_with_emb["chunk_index"],
                        "text": chunk_with_emb["content"][:1000],  # Store first 1000 chars
                        "metadata": chunk_with_emb.get("metadata", {}),
                        "embedding_model": chunk_with_emb.get("embedding_model", "unknown"),
                        "embedding_dimensions": chunk_with_emb.get("embedding_dimensions", 0)
                    })

                    # Update chunk in database
                    chunk_record = next(
                        (c for c in batch_chunks if c.id == chunk_with_emb["chunk_id"]),
                        None
                    )
                    if chunk_record:
                        # Create new metadata dict if needed
                        metadata = chunk_record.chunk_metadata or {}
                        metadata["embedding_generated"] = True
                        metadata["embedding_model"] = chunk_with_emb.get("embedding_model")
                        metadata["embedding_dimensions"] = chunk_with_emb.get("embedding_dimensions")
                        chunk_record.chunk_metadata = metadata

            # Store in Qdrant
            if vectors:
                ids = await vector_db.insert_vectors(
                    collection_name=collection_name,
                    vectors=vectors,
                    payloads=payloads
                )
                logger.info(f"Stored {len(ids)} vectors in Qdrant for document {document_id}")

            # Update progress
            processed_count += len(batch_chunks)
            job.completed_steps = processed_count
            job.progress_percentage = (processed_count / len(chunks)) * 100
            db.commit()

            logger.info(f"Processed {processed_count}/{len(chunks)} chunks")

        # Get embedding statistics
        if embedding_service.primary_encoder:
            stats = embedding_service.primary_encoder.get_statistics()
            total_cost = stats.get("total_cost", 0)

        # Update job as completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.completed_steps = len(chunks)
        db.commit()

        # Update document status
        document.status = ProcessingStatus.COMPLETED
        db.commit()

        logger.info(f"Embedding generation completed for document {document_id}. Cost: ${total_cost:.6f}")

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")

        # Update job as failed
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        # Update document status
        if document:
            document.status = ProcessingStatus.FAILED
            document.processing_error = f"Embedding generation failed: {str(e)}"
            db.commit()

        raise

    finally:
        db.close()


@router.get("/{document_id}/status")
async def get_embedding_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get the status of embedding generation for a document."""

    # Get latest embedding job
    job = db.query(ProcessingJob).filter(
        ProcessingJob.document_id == document_id,
        ProcessingJob.job_type == "embedding_generation"
    ).order_by(ProcessingJob.created_at.desc()).first()

    if not job:
        return {
            "status": "not_started",
            "message": "No embedding generation job found for this document"
        }

    # Get collection info from Qdrant
    collection_name = f"document_{document_id}"
    collection_info = await vector_db.get_collection_info(collection_name)

    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_chunks": job.total_steps,
        "processed_chunks": job.completed_steps,
        "progress_percentage": job.progress_percentage or 0,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message,
        "embedding_model": "text-embedding-3-large",
        "total_cost": 0,  # TODO: track cost
        "vector_database": {
            "collection_name": collection_name,
            "vectors_count": collection_info.get("vectors_count", 0) if collection_info else 0,
            "status": collection_info.get("status") if collection_info else "not_found"
        }
    }


@router.post("/{document_id}/search")
async def search_similar_chunks(
    document_id: int,
    query: str,
    limit: int = Query(5, description="Number of results to return"),
    score_threshold: float = Query(0.7, description="Minimum similarity score"),
    db: Session = Depends(get_db)
):
    """
    Search for similar chunks in a document using semantic search.
    """
    # Check if document exists
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if embeddings exist
    collection_name = f"document_{document_id}"
    collection_info = await vector_db.get_collection_info(collection_name)

    if not collection_info or collection_info.get("vectors_count", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="No embeddings found for this document. Please generate embeddings first."
        )

    # Generate query embedding
    if not embedding_service.primary_encoder:
        raise HTTPException(
            status_code=500,
            detail="Embedding service not available"
        )

    query_embedding, _ = await embedding_service.primary_encoder.embed_text(query)

    if not query_embedding:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate query embedding"
        )

    # Search in Qdrant
    results = await vector_db.search_vectors(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=limit,
        score_threshold=score_threshold
    )

    # Format results
    formatted_results = []
    for vector_id, score, payload in results:
        formatted_results.append({
            "chunk_id": payload.get("chunk_id"),
            "chunk_index": payload.get("chunk_index"),
            "text": payload.get("text"),
            "score": score,
            "metadata": payload.get("metadata", {})
        })

    return {
        "query": query,
        "document_id": document_id,
        "results": formatted_results,
        "total_results": len(formatted_results)
    }


@router.get("/statistics")
async def get_embedding_statistics():
    """Get global embedding service statistics."""

    stats = embedding_service.get_encoder_statistics()

    return {
        "service_status": "operational" if embedding_service.primary_encoder else "unavailable",
        "encoders": stats,
        "supported_models": [
            "text-embedding-3-large",
            "text-embedding-3-small",
            "text-embedding-ada-002"
        ]
    }