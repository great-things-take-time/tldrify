"""File upload endpoints with improved dependency injection."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, Annotated
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from src.db.dependencies import DBSession
from src.db.models import Document, ProcessingStatus, DocumentType, ProcessingJob
from src.services.storage import storage_service
from src.db.redis_client import redis_client
from src.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """File upload response model."""
    success: bool
    document_id: int
    job_id: str
    filename: str
    file_size: int
    status: str = "pending"


class ChunkUploadStartResponse(BaseModel):
    """Chunked upload start response."""
    success: bool
    upload_id: str
    chunk_size: int
    total_chunks: int


class ChunkUploadResponse(BaseModel):
    """Single chunk upload response."""
    success: bool
    upload_id: str
    chunk_index: int
    chunks_received: int
    total_chunks: int


class ChunkUploadCompleteResponse(BaseModel):
    """Chunked upload completion response."""
    success: bool
    document_id: int
    job_id: str
    filename: str
    file_size: int
    status: str = "pending"


# Dependencies
UploadFileDep = Annotated[UploadFile, File(description="File to upload")]


def get_user_id() -> int:
    """Get current user ID from auth context."""
    # TODO: Implement actual auth extraction
    return 1


UserIdDep = Annotated[int, Depends(get_user_id)]


class FileValidator:
    """File validation dependency."""

    @staticmethod
    def validate_extension(filename: str) -> bool:
        """Validate file extension."""
        return storage_service.validate_file_extension(filename)

    @staticmethod
    def validate_size(size: int) -> bool:
        """Validate file size."""
        return storage_service.validate_file_size(size)

    async def __call__(self, file: UploadFileDep) -> UploadFile:
        """Validate uploaded file."""
        if not self.validate_extension(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )

        # For chunked uploads, size validation happens per chunk
        # For simple uploads, we'll validate after reading
        return file


FileValidatorDep = Annotated[UploadFile, Depends(FileValidator())]


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: FileValidatorDep,
    db: DBSession,
    user_id: UserIdDep,
):
    """
    Simple file upload endpoint (non-chunked).

    For files smaller than 10MB, use this endpoint for direct upload.
    """
    # Read file content
    content = await file.read()

    # Validate file size after reading
    if not storage_service.validate_file_size(len(content)):
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
        )

    # Save file
    file_info = await storage_service.save_file(content, file.filename)

    # Create database record
    document = Document(
        user_id=user_id,
        filename=file.filename,
        file_path=file_info["path"],
        file_size=file_info["size"],
        file_hash=file_info["hash"],
        mime_type=file.content_type or "application/pdf",
        document_type=DocumentType.PDF,
        status=ProcessingStatus.PENDING,
        title=file.filename.replace(".pdf", "")
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Create processing job
    job_id = str(uuid.uuid4())
    processing_job = ProcessingJob(
        job_id=job_id,
        document_id=document.id,
        job_type="ocr",
        status="pending",
        total_steps=1,
        completed_steps=0
    )
    db.add(processing_job)
    db.commit()

    return UploadResponse(
        success=True,
        document_id=document.id,
        job_id=job_id,
        filename=file.filename,
        file_size=file_info["size"],
        status="pending"
    )


@router.post("/chunk/start", response_model=ChunkUploadStartResponse)
async def start_chunked_upload(
    filename: Annotated[str, Form(description="Name of the file being uploaded")],
    file_size: Annotated[int, Form(description="Total size of the file in bytes")],
    chunk_size: Annotated[int, Form(description="Size of each chunk in bytes")],
    user_id: UserIdDep,
):
    """
    Start a chunked upload session.

    Use this for files larger than 10MB. Returns an upload_id to use for subsequent chunks.
    """
    # Validate file
    if not storage_service.validate_file_extension(filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )

    if not storage_service.validate_file_size(file_size):
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
        )

    # Generate upload ID
    upload_id = str(uuid.uuid4())

    # Calculate total chunks
    total_chunks = (file_size + chunk_size - 1) // chunk_size

    # Store upload metadata in Redis
    upload_metadata = {
        "upload_id": upload_id,
        "filename": filename,
        "file_size": file_size,
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
        "chunks_received": [],
        "user_id": user_id,
        "started_at": datetime.utcnow().isoformat()
    }

    redis_client.set(
        f"upload:{upload_id}",
        json.dumps(upload_metadata),
        ttl=3600  # 1 hour TTL
    )

    # Initialize upload in storage
    await storage_service.start_chunked_upload(upload_id, filename)

    return ChunkUploadStartResponse(
        success=True,
        upload_id=upload_id,
        chunk_size=chunk_size,
        total_chunks=total_chunks
    )


@router.post("/chunk/upload", response_model=ChunkUploadResponse)
async def upload_chunk(
    upload_id: Annotated[str, Form(description="Upload session ID")],
    chunk_index: Annotated[int, Form(description="Index of this chunk (0-based)")],
    chunk: UploadFileDep,
    user_id: UserIdDep,
):
    """
    Upload a single chunk of a file.

    Chunks must be uploaded sequentially or can be parallelized.
    """
    # Get upload metadata
    metadata_json = redis_client.get(f"upload:{upload_id}")
    if not metadata_json:
        raise HTTPException(status_code=404, detail="Upload session not found or expired")

    metadata = json.loads(metadata_json)

    # Verify user owns this upload
    if metadata["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Validate chunk index
    if chunk_index >= metadata["total_chunks"]:
        raise HTTPException(status_code=400, detail="Invalid chunk index")

    # Check if chunk already received
    if chunk_index in metadata["chunks_received"]:
        # Idempotent - return success if already received
        return ChunkUploadResponse(
            success=True,
            upload_id=upload_id,
            chunk_index=chunk_index,
            chunks_received=len(metadata["chunks_received"]),
            total_chunks=metadata["total_chunks"]
        )

    # Read and save chunk
    chunk_data = await chunk.read()
    await storage_service.save_chunk(upload_id, chunk_index, chunk_data)

    # Update metadata
    metadata["chunks_received"].append(chunk_index)
    redis_client.set(
        f"upload:{upload_id}",
        json.dumps(metadata),
        ttl=3600
    )

    return ChunkUploadResponse(
        success=True,
        upload_id=upload_id,
        chunk_index=chunk_index,
        chunks_received=len(metadata["chunks_received"]),
        total_chunks=metadata["total_chunks"]
    )


@router.post("/chunk/complete", response_model=ChunkUploadCompleteResponse)
async def complete_chunked_upload(
    upload_id: Annotated[str, Form(description="Upload session ID")],
    db: DBSession,
    user_id: UserIdDep,
):
    """
    Complete a chunked upload session.

    Assembles all chunks into final file and creates database record.
    """
    # Get upload metadata
    metadata_json = redis_client.get(f"upload:{upload_id}")
    if not metadata_json:
        raise HTTPException(status_code=404, detail="Upload session not found or expired")

    metadata = json.loads(metadata_json)

    # Verify user owns this upload
    if metadata["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Verify all chunks received
    if len(metadata["chunks_received"]) != metadata["total_chunks"]:
        missing_chunks = [
            i for i in range(metadata["total_chunks"])
            if i not in metadata["chunks_received"]
        ]
        raise HTTPException(
            status_code=400,
            detail=f"Missing chunks: {missing_chunks}"
        )

    # Assemble chunks
    file_info = await storage_service.assemble_chunks(
        upload_id,
        metadata["filename"],
        metadata["total_chunks"]
    )

    # Create database record
    document = Document(
        user_id=user_id,
        filename=metadata["filename"],
        file_path=file_info["path"],
        file_size=file_info["size"],
        file_hash=file_info["hash"],
        mime_type="application/pdf",
        document_type=DocumentType.PDF,
        status=ProcessingStatus.PENDING,
        title=metadata["filename"].replace(".pdf", "")
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Create processing job
    job_id = str(uuid.uuid4())
    processing_job = ProcessingJob(
        job_id=job_id,
        document_id=document.id,
        job_type="ocr",
        status="pending",
        total_steps=1,
        completed_steps=0
    )
    db.add(processing_job)
    db.commit()

    # Clean up Redis
    redis_client.delete(f"upload:{upload_id}")

    return ChunkUploadCompleteResponse(
        success=True,
        document_id=document.id,
        job_id=job_id,
        filename=metadata["filename"],
        file_size=file_info["size"],
        status="pending"
    )


@router.websocket("/ws/{upload_id}")
async def upload_progress_websocket(
    websocket: WebSocket,
    upload_id: str,
):
    """
    WebSocket endpoint for real-time upload progress updates.

    Connect to this endpoint to receive progress updates during chunked upload.
    """
    await websocket.accept()

    try:
        while True:
            # Get upload metadata
            metadata_json = redis_client.get(f"upload:{upload_id}")
            if not metadata_json:
                await websocket.send_json({
                    "type": "error",
                    "message": "Upload session not found or expired"
                })
                break

            metadata = json.loads(metadata_json)

            # Send progress update
            progress = len(metadata["chunks_received"]) / metadata["total_chunks"] * 100
            await websocket.send_json({
                "type": "progress",
                "upload_id": upload_id,
                "chunks_received": len(metadata["chunks_received"]),
                "total_chunks": metadata["total_chunks"],
                "progress_percentage": progress
            })

            # Check if complete
            if len(metadata["chunks_received"]) == metadata["total_chunks"]:
                await websocket.send_json({
                    "type": "complete",
                    "message": "Upload complete"
                })
                break

            # Wait for updates
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for upload {upload_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()