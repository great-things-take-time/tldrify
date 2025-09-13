"""File upload endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.db.models import Document, ProcessingStatus, DocumentType, ProcessingJob
from src.services.storage import storage_service
from src.db.redis_client import redis_client
from src.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Simple file upload endpoint (non-chunked)."""
    # Validate file extension
    if not storage_service.validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if not storage_service.validate_file_size(len(content)):
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
        )

    # Save file
    file_info = await storage_service.save_file(content, file.filename)

    # Create database record
    document = Document(
        user_id=1,  # TODO: Get from auth
        filename=file.filename,
        file_path=file_info["path"],
        file_size=file_info["size"],
        file_hash=file_info["hash"],
        mime_type=file.content_type,
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
        status="pending"
    )
    db.add(processing_job)
    db.commit()

    return JSONResponse(content={
        "success": True,
        "document_id": document.id,
        "job_id": job_id,
        "filename": file.filename,
        "size": file_info["size"],
        "message": "File uploaded successfully"
    })


@router.post("/upload/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    chunk: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file chunk."""
    # Validate file extension
    if not storage_service.validate_file_extension(filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )

    # Read chunk data
    chunk_data = await chunk.read()

    # Save chunk and get progress
    progress = await storage_service.save_chunk(
        upload_id=upload_id,
        chunk_index=chunk_index,
        chunk_data=chunk_data,
        total_chunks=total_chunks
    )

    # Check if all chunks are uploaded
    if progress["completed_chunks"] == total_chunks:
        # Assemble file
        try:
            file_info = await storage_service.assemble_chunks(
                upload_id=upload_id,
                filename=filename,
                total_chunks=total_chunks
            )

            # Create database record
            document = Document(
                user_id=1,  # TODO: Get from auth
                filename=filename,
                file_path=file_info["path"],
                file_size=file_info["size"],
                file_hash=file_info["hash"],
                mime_type="application/pdf",
                document_type=DocumentType.PDF,
                status=ProcessingStatus.PENDING,
                title=filename.replace(".pdf", "")
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
                status="pending"
            )
            db.add(processing_job)
            db.commit()

            return JSONResponse(content={
                "success": True,
                "complete": True,
                "document_id": document.id,
                "job_id": job_id,
                "filename": filename,
                "size": file_info["size"],
                "message": "File upload completed"
            })

        except Exception as e:
            logger.error(f"Error assembling chunks: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={
        "success": True,
        "complete": False,
        "progress": progress,
        "message": f"Chunk {chunk_index + 1}/{total_chunks} uploaded"
    })


@router.get("/upload/progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    """Get upload progress."""
    progress = storage_service.get_upload_progress(upload_id)

    if not progress:
        raise HTTPException(status_code=404, detail="Upload not found")

    return JSONResponse(content={
        "success": True,
        "progress": progress
    })


@router.websocket("/ws/upload/{upload_id}")
async def websocket_upload_progress(websocket: WebSocket, upload_id: str):
    """WebSocket endpoint for real-time upload progress."""
    await websocket.accept()

    try:
        while True:
            # Get progress from Redis
            progress = storage_service.get_upload_progress(upload_id)

            if progress:
                await websocket.send_json({
                    "type": "progress",
                    "data": progress
                })

                # If upload is complete, close connection
                if progress.get("percentage", 0) >= 100:
                    await websocket.send_json({
                        "type": "complete",
                        "message": "Upload completed"
                    })
                    break

            # Wait before next update
            await websocket.receive_text()  # This will block until client sends a message

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for upload {upload_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()