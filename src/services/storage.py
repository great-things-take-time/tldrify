"""File storage service."""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any
import aiofiles
import json
from datetime import datetime
import uuid

from src.core.config import settings
from src.db.redis_client import redis_client


class StorageService:
    """Handles file storage operations."""

    def __init__(self):
        self.upload_path = settings.UPLOAD_PATH
        self.temp_path = settings.TEMP_PATH
        self.chunk_size = settings.CHUNK_SIZE

    async def save_chunk(
        self,
        upload_id: str,
        chunk_index: int,
        chunk_data: bytes,
        total_chunks: int
    ) -> Dict[str, Any]:
        """Save a file chunk."""
        # Create upload directory
        chunk_dir = self.temp_path / upload_id
        chunk_dir.mkdir(parents=True, exist_ok=True)

        # Save chunk
        chunk_path = chunk_dir / f"chunk_{chunk_index}"
        async with aiofiles.open(chunk_path, 'wb') as f:
            await f.write(chunk_data)

        # Update progress in Redis
        progress_key = f"upload:progress:{upload_id}"
        progress_data = {
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "completed_chunks": len(list(chunk_dir.glob("chunk_*"))),
            "percentage": (len(list(chunk_dir.glob("chunk_*"))) / total_chunks) * 100,
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.set_json(progress_key, progress_data, expire=3600)

        return progress_data

    async def assemble_chunks(
        self,
        upload_id: str,
        filename: str,
        total_chunks: int
    ) -> Dict[str, Any]:
        """Assemble chunks into final file."""
        chunk_dir = self.temp_path / upload_id

        # Verify all chunks exist
        for i in range(total_chunks):
            chunk_path = chunk_dir / f"chunk_{i}"
            if not chunk_path.exists():
                raise ValueError(f"Missing chunk {i}")

        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        final_path = self.upload_path / unique_filename

        # Assemble file
        async with aiofiles.open(final_path, 'wb') as final_file:
            for i in range(total_chunks):
                chunk_path = chunk_dir / f"chunk_{i}"
                async with aiofiles.open(chunk_path, 'rb') as chunk_file:
                    chunk_data = await chunk_file.read()
                    await final_file.write(chunk_data)

        # Calculate file hash
        file_hash = await self.calculate_file_hash(final_path)

        # Clean up chunks
        shutil.rmtree(chunk_dir)

        # Clear progress from Redis
        redis_client.delete(f"upload:progress:{upload_id}")

        return {
            "filename": unique_filename,
            "original_filename": filename,
            "path": str(final_path),
            "size": final_path.stat().st_size,
            "hash": file_hash
        }

    async def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    async def save_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Save a complete file (non-chunked upload)."""
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_path / unique_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)

        # Calculate hash
        file_hash = await self.calculate_file_hash(file_path)

        return {
            "filename": unique_filename,
            "original_filename": filename,
            "path": str(file_path),
            "size": len(file_data),
            "hash": file_hash
        }

    def get_upload_progress(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get upload progress from Redis."""
        return redis_client.get_json(f"upload:progress:{upload_id}")

    def validate_file_extension(self, filename: str) -> bool:
        """Validate file extension."""
        file_extension = Path(filename).suffix.lower()
        return file_extension in settings.ALLOWED_EXTENSIONS

    def validate_file_size(self, size: int) -> bool:
        """Validate file size."""
        return size <= settings.MAX_FILE_SIZE


storage_service = StorageService()