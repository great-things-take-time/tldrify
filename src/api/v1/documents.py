"""Document management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.db.base import get_db
from src.db.models import Document, ProcessingStatus
from pydantic import BaseModel

router = APIRouter()


class DocumentResponse(BaseModel):
    """Document response model."""
    id: int
    filename: str
    file_size: int
    status: str
    title: Optional[str]
    page_count: Optional[int]
    created_at: datetime
    processing_completed_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    status: Optional[ProcessingStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all documents."""
    query = db.query(Document)

    if status:
        query = query.filter(Document.status == status)

    # TODO: Add user filtering when auth is implemented
    query = query.filter(Document.user_id == 1)

    documents = query.offset(skip).limit(limit).all()

    return documents


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == 1  # TODO: Get from auth
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == 1  # TODO: Get from auth
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # TODO: Delete file from storage
    # TODO: Delete from vector DB

    db.delete(document)
    db.commit()

    return {"success": True, "message": "Document deleted successfully"}


@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get document processing status."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == 1  # TODO: Get from auth
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get processing jobs
    from src.db.models import ProcessingJob
    jobs = db.query(ProcessingJob).filter(
        ProcessingJob.document_id == document_id
    ).all()

    return {
        "document_id": document.id,
        "status": document.status.value,
        "processing_started": document.processing_started_at,
        "processing_completed": document.processing_completed_at,
        "jobs": [
            {
                "job_id": job.job_id,
                "type": job.job_type,
                "status": job.status,
                "progress": job.progress_percentage
            }
            for job in jobs
        ]
    }