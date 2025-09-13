"""OCR processing API endpoints."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ...db.base import get_db
from ...db.models import Document, OCRResult, ProcessingJob, ProcessingStatus
from ...core.ocr.processor import OCRProcessor
from ...services.celery_app import process_document_ocr
from .auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])


@router.post("/process/{document_id}")
async def process_document_ocr_endpoint(
    document_id: int,
    background_tasks: BackgroundTasks,
    use_fallback: bool = Query(True, description="Use PyMuPDF fallback for text-based PDFs"),
    async_processing: bool = Query(True, description="Process asynchronously using Celery"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Start OCR processing for a document.

    Args:
        document_id: Document ID to process
        use_fallback: Use PyMuPDF for text-based PDFs
        async_processing: Process asynchronously
        db: Database session
        user_id: Current user ID

    Returns:
        Processing job information
    """
    # Get document
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if already processed
    existing_results = db.query(OCRResult).filter(
        OCRResult.document_id == document_id
    ).first()

    if existing_results:
        return {
            "message": "Document already processed",
            "document_id": document_id,
            "status": "completed"
        }

    # Update document status
    document.status = ProcessingStatus.OCR_PROCESSING
    db.commit()

    if async_processing:
        # Create processing job
        job = ProcessingJob(
            job_id=f"ocr_{document_id}_{user_id}",
            document_id=document_id,
            job_type="ocr",
            status="pending",
            current_step="Starting OCR processing",
            total_steps=document.page_count or 1
        )
        db.add(job)
        db.commit()

        # Queue Celery task
        task = process_document_ocr.delay(
            document_id=document_id,
            file_path=document.file_path,
            use_fallback=use_fallback
        )

        # Update job with Celery task ID
        job.job_id = task.id
        db.commit()

        return {
            "message": "OCR processing started",
            "document_id": document_id,
            "job_id": task.id,
            "status": "processing"
        }
    else:
        # Process synchronously (for small documents)
        background_tasks.add_task(
            process_ocr_sync,
            document_id=document_id,
            file_path=document.file_path,
            use_fallback=use_fallback,
            db=db
        )

        return {
            "message": "OCR processing started",
            "document_id": document_id,
            "status": "processing"
        }


@router.get("/results/{document_id}")
async def get_ocr_results(
    document_id: int,
    page: Optional[int] = Query(None, description="Get specific page result"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get OCR results for a document.

    Args:
        document_id: Document ID
        page: Specific page number (optional)
        db: Database session
        user_id: Current user ID

    Returns:
        OCR results
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Query OCR results
    query = db.query(OCRResult).filter(OCRResult.document_id == document_id)

    if page is not None:
        query = query.filter(OCRResult.page_number == page)

    results = query.order_by(OCRResult.page_number).all()

    if not results:
        raise HTTPException(status_code=404, detail="No OCR results found")

    return {
        "document_id": document_id,
        "total_pages": document.page_count,
        "results": [
            {
                "page_number": r.page_number,
                "text_content": r.text_content,
                "confidence_score": r.confidence_score,
                "ocr_engine": r.ocr_engine,
                "processing_time": r.processing_time,
                "language_detected": r.language_detected
            }
            for r in results
        ]
    }


@router.get("/status/{document_id}")
async def get_ocr_status(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get OCR processing status for a document.

    Args:
        document_id: Document ID
        db: Database session
        user_id: Current user ID

    Returns:
        Processing status information
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get processing job
    job = db.query(ProcessingJob).filter(
        and_(
            ProcessingJob.document_id == document_id,
            ProcessingJob.job_type == "ocr"
        )
    ).order_by(ProcessingJob.created_at.desc()).first()

    # Count processed pages
    processed_pages = db.query(OCRResult).filter(
        OCRResult.document_id == document_id
    ).count()

    return {
        "document_id": document_id,
        "status": document.status.value,
        "total_pages": document.page_count,
        "processed_pages": processed_pages,
        "progress_percentage": (processed_pages / document.page_count * 100) if document.page_count else 0,
        "job": {
            "id": job.job_id if job else None,
            "status": job.status if job else None,
            "current_step": job.current_step if job else None,
            "error_message": job.error_message if job else None
        } if job else None
    }


@router.delete("/results/{document_id}")
async def delete_ocr_results(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Delete OCR results for a document.

    Args:
        document_id: Document ID
        db: Database session
        user_id: Current user ID

    Returns:
        Deletion confirmation
    """
    # Verify document ownership
    document = db.query(Document).filter(
        and_(Document.id == document_id, Document.user_id == user_id)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete OCR results
    deleted_count = db.query(OCRResult).filter(
        OCRResult.document_id == document_id
    ).delete()

    # Reset document status
    document.status = ProcessingStatus.PENDING
    document.processing_completed_at = None

    db.commit()

    # Clear cache
    processor = OCRProcessor()
    processor.clear_cache(document_id)

    return {
        "message": "OCR results deleted",
        "document_id": document_id,
        "deleted_pages": deleted_count
    }


def process_ocr_sync(document_id: int, file_path: str, use_fallback: bool, db: Session):
    """
    Process OCR synchronously (for background tasks).

    Args:
        document_id: Document ID
        file_path: Path to PDF file
        use_fallback: Use PyMuPDF fallback
        db: Database session
    """
    try:
        processor = OCRProcessor()

        def progress_callback(progress, current_page, total_pages):
            # Update job progress
            job = db.query(ProcessingJob).filter(
                and_(
                    ProcessingJob.document_id == document_id,
                    ProcessingJob.job_type == "ocr"
                )
            ).first()

            if job:
                job.completed_steps = current_page
                job.progress_percentage = progress
                job.current_step = f"Processing page {current_page}/{total_pages}"
                db.commit()

        # Process document
        results = processor.process_document(
            pdf_path=file_path,
            document_id=document_id,
            use_fallback=use_fallback,
            progress_callback=progress_callback
        )

        # Save results to database
        for result in results:
            ocr_result = OCRResult(
                document_id=document_id,
                page_number=result["page_number"],
                text_content=result.get("text_content", ""),
                confidence_score=result.get("confidence_score", 0.0),
                processing_time=result.get("processing_time", 0.0),
                ocr_engine=result.get("ocr_engine", "unknown"),
                bbox_data=result.get("bbox_data"),
                language_detected=result.get("language_detected")
            )
            db.add(ocr_result)

        # Update document status
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = ProcessingStatus.COMPLETED
            document.word_count = sum(r.get("word_count", 0) for r in results)

            from datetime import datetime
            document.processing_completed_at = datetime.utcnow()

        # Update job status
        job = db.query(ProcessingJob).filter(
            and_(
                ProcessingJob.document_id == document_id,
                ProcessingJob.job_type == "ocr"
            )
        ).first()

        if job:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100.0

        db.commit()
        logger.info(f"OCR processing completed for document {document_id}")

    except Exception as e:
        logger.error(f"Error in OCR processing: {str(e)}")

        # Update status on error
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = ProcessingStatus.FAILED
            document.processing_error = str(e)

        job = db.query(ProcessingJob).filter(
            and_(
                ProcessingJob.document_id == document_id,
                ProcessingJob.job_type == "ocr"
            )
        ).first()

        if job:
            job.status = "failed"
            job.error_message = str(e)

        db.commit()
        raise