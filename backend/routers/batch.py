"""
Batch Processing Router - Bulk operations at scale
"""
from fastapi import APIRouter, HTTPException
from models.schemas import BatchRequest, BatchResponse
from services.batch_service import batch_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/batch", tags=["Batch"])


@router.post("/create", response_model=BatchResponse)
async def create_batch(request: BatchRequest):
    """Create a new batch processing job"""
    try:
        tasks = [{"type": t.type, "payload": t.payload} for t in request.tasks]
        job_id = await batch_service.create_batch_job(tasks)
        return BatchResponse(
            job_id=job_id,
            status="processing",
            total_tasks=len(tasks),
        )
    except Exception as e:
        logger.error(f"Batch create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
async def get_batch_status(job_id: str):
    """Get batch job status"""
    result = await batch_service.get_job_status(job_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/jobs")
async def list_batch_jobs():
    """List all batch jobs"""
    return await batch_service.get_all_jobs()