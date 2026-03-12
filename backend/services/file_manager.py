"""
File Manager - Handle uploads, storage, and processing
"""
import os
import uuid
import time
import base64
import aiofiles
from typing import Optional, Tuple
from config import settings
from models.database import execute_insert, execute_query
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """Handles file uploads and storage"""

    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    async def save_upload(
        self,
        file_data: bytes,
        filename: str,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """Save an uploaded file"""
        file_id = str(uuid.uuid4())
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        safe_filename = f"{file_id}.{ext}"
        filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(file_data)

        file_type = self._detect_type(ext)

        await execute_insert(
            """INSERT INTO files (id, filename, filepath, file_type, file_size,
               conversation_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (file_id, filename, filepath, file_type, len(file_data),
             conversation_id, time.time())
        )

        return {
            "id": file_id,
            "filename": filename,
            "filepath": filepath,
            "file_type": file_type,
            "file_size": len(file_data),
        }

    async def get_file(self, file_id: str) -> Optional[dict]:
        """Get file info"""
        rows = await execute_query(
            "SELECT * FROM files WHERE id = ?", (file_id,)
        )
        return rows[0] if rows else None

    async def read_file(self, file_id: str) -> Optional[bytes]:
        """Read file contents"""
        file_info = await self.get_file(file_id)
        if not file_info:
            return None

        async with aiofiles.open(file_info["filepath"], "rb") as f:
            return await f.read()

    async def get_file_as_base64(self, file_id: str) -> Optional[str]:
        """Get file as base64 string"""
        data = await self.read_file(file_id)
        return base64.b64encode(data).decode() if data else None

    async def delete_file(self, file_id: str):
        """Delete a file"""
        file_info = await self.get_file(file_id)
        if file_info and os.path.exists(file_info["filepath"]):
            os.remove(file_info["filepath"])
        await execute_insert("DELETE FROM files WHERE id = ?", (file_id,))

    def _detect_type(self, ext: str) -> str:
        """Detect file type from extension"""
        if ext in settings.ALLOWED_AUDIO_FORMATS:
            return "audio"
        elif ext in settings.ALLOWED_IMAGE_FORMATS:
            return "image"
        elif ext in ["pdf", "doc", "docx", "txt", "md", "csv", "json", "xml"]:
            return "document"
        elif ext in ["py", "js", "ts", "java", "cpp", "c", "go", "rs", "rb"]:
            return "code"
        return "other"


# Singleton
file_manager = FileManager()