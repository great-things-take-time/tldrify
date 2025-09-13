"""Document management endpoints with improved dependency injection."""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import List, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.db.dependencies import DBSession
from src.db.models import Document, ProcessingStatus, ProcessingJob

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    """Document response model."""
    id: int
    filename: str
    file_size: int
    status: str
    title: Optional[str] = None
    page_count: Optional[int] = None
    created_at: datetime
    processing_completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    """Document status response model."""
    document_id: int
    status: str
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None
    jobs: List[dict]


class PaginationParams:
    """Common pagination parameters as a dependency."""
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
        limit: Annotated[int, Query(ge=1, le=100, description="Number of items to return")] = 20,
    ):
        self.skip = skip
        self.limit = limit


# Using Annotated for cleaner dependency injection
PaginationDep = Annotated[PaginationParams, Depends(PaginationParams)]
DocumentIdDep = Annotated[int, Path(description="Document ID")]


def get_user_id() -> int:
    """Dependency to get current user ID from auth context."""
    # TODO: Implement actual auth extraction
    return 1


UserIdDep = Annotated[int, Depends(get_user_id)]


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    db: DBSession,
    pagination: PaginationDep,
    user_id: UserIdDep,
    status: Annotated[Optional[ProcessingStatus], Query(description="Filter by status")] = None,
):
    """
    List all documents for the current user.

    - **status**: Optional filter by processing status
    - **skip**: Number of items to skip for pagination
    - **limit**: Maximum number of items to return
    """
    query = db.query(Document).filter(Document.user_id == user_id)

    if status:
        query = query.filter(Document.status == status)

    documents = query.offset(pagination.skip).limit(pagination.limit).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: DocumentIdDep,
    db: DBSession,
    user_id: UserIdDep,
):
    """
    Get a specific document by ID.

    Returns 404 if document not found or doesn't belong to user.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: DocumentIdDep,
    db: DBSession,
    user_id: UserIdDep,
):
    """
    Delete a document and all associated data.

    This will:
    - Remove the document from database
    - Delete associated files from storage
    - Remove vectors from vector database
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # TODO: Implement cleanup in background task
    # - Delete file from storage
    # - Delete from vector DB
    # - Delete chunks and other related data

    db.delete(document)
    db.commit()

    return {"success": True, "message": "Document deleted successfully"}


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: DocumentIdDep,
    db: DBSession,
    user_id: UserIdDep,
):
    """
    Get detailed processing status for a document.

    Returns document status and all associated processing jobs.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get all processing jobs for this document
    jobs = db.query(ProcessingJob).filter(
        ProcessingJob.document_id == document_id
    ).order_by(ProcessingJob.created_at.desc()).all()

    return DocumentStatusResponse(
        document_id=document.id,
        status=document.status.value,
        processing_started=document.processing_started_at,
        processing_completed=document.processing_completed_at,
        jobs=[
            {
                "job_id": job.job_id,
                "type": job.job_type,
                "status": job.status,
                "progress": job.progress_percentage or 0,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "error_message": job.error_message,
            }
            for job in jobs
        ]
    )