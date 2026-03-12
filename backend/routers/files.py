"""
Files Router - File upload and management
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Optional
from services.file_manager import file_manager
from config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
):
    """Upload a file"""
    try:
        data = await file.read()
        if len(data) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        result = await file_manager.save_upload(
            file_data=data,
            filename=file.filename or "upload",
            conversation_id=conversation_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}")
async def get_file_info(file_id: str):
    """Get file information"""
    info = await file_manager.get_file(file_id)
    if not info:
        raise HTTPException(status_code=404, detail="File not found")
    return info


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a file"""
    await file_manager.delete_file(file_id)
    return {"status": "deleted"}