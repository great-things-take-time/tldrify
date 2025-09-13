"""Celery application configuration and tasks."""

import os
import logging
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "tldrify",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


@celery_app.task(bind=True, name="process_document_ocr")
def process_document_ocr(self, document_id: int, file_path: str, use_fallback: bool = True):
    """
    Process document with OCR asynchronously.

    Args:
        document_id: Document ID
        file_path: Path to PDF file
        use_fallback: Use PyMuPDF fallback for text-based PDFs

    Returns:
        Processing result
    """
    from ..db.base import SessionLocal
    from ..db.models import Document, OCRResult, ProcessingJob, ProcessingStatus
    from ..core.ocr.processor import OCRProcessor
    from sqlalchemy import and_

    db = SessionLocal()

    try:
        # Update task status
        self.update_state(
            state="PROCESSING",
            meta={"current": 0, "total": 100, "status": "Starting OCR processing..."}
        )

        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Update processing job
        job = db.query(ProcessingJob).filter(
            and_(
                ProcessingJob.document_id == document_id,
                ProcessingJob.job_type == "ocr"
            )
        ).first()

        if job:
            job.status = "processing"
            job.started_at = datetime.utcnow()
            job.job_id = self.request.id
            db.commit()

        # Initialize OCR processor
        processor = OCRProcessor()

        # Process document with progress tracking
        def progress_callback(progress, current_page, total_pages):
            # Update Celery task state
            self.update_state(
                state="PROCESSING",
                meta={
                    "current": current_page,
                    "total": total_pages,
                    "progress": progress,
                    "status": f"Processing page {current_page}/{total_pages}"
                }
            )

            # Update database job
            if job:
                job.completed_steps = current_page
                job.progress_percentage = progress
                job.current_step = f"Processing page {current_page}/{total_pages}"
                db.commit()

        # Run OCR processing
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

        # Update document
        document.status = ProcessingStatus.EMBEDDING  # Next step
        document.word_count = sum(r.get("word_count", 0) for r in results)
        document.processing_completed_at = datetime.utcnow()

        # Update job
        if job:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100.0
            job.current_step = "OCR processing completed"

        db.commit()

        logger.info(f"OCR processing completed for document {document_id}")

        return {
            "status": "success",
            "document_id": document_id,
            "pages_processed": len(results),
            "average_confidence": sum(r.get("confidence_score", 0) for r in results) / len(results) if results else 0
        }

    except Exception as e:
        logger.error(f"Error in OCR task for document {document_id}: {str(e)}")

        # Update document status
        if 'document' in locals():
            document.status = ProcessingStatus.FAILED
            document.processing_error = str(e)

        # Update job status
        if 'job' in locals() and job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

        db.commit()

        # Re-raise for Celery error handling
        raise

    finally:
        db.close()


@celery_app.task(bind=True, name="process_document_embedding")
def process_document_embedding(self, document_id: int):
    """
    Generate embeddings for document chunks.

    Args:
        document_id: Document ID

    Returns:
        Processing result
    """
    # To be implemented in Task #19-21
    logger.info(f"Embedding generation for document {document_id} - Not yet implemented")
    return {"status": "pending", "message": "Embedding generation not yet implemented"}


@celery_app.task(bind=True, name="generate_document_summary")
def generate_document_summary(self, document_id: int):
    """
    Generate AI-powered summary for document.

    Args:
        document_id: Document ID

    Returns:
        Summary result
    """
    # To be implemented in later tasks
    logger.info(f"Summary generation for document {document_id} - Not yet implemented")
    return {"status": "pending", "message": "Summary generation not yet implemented"}


# Signal handlers for logging
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log task start."""
    logger.info(f"Task {task.name} [{task_id}] started")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, result=None, **kwargs):
    """Log task completion."""
    logger.info(f"Task {task.name} [{task_id}] completed with result: {result}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failure."""
    logger.error(f"Task [{task_id}] failed with exception: {exception}")