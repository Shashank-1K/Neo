
### `backend/routers/math_science.py`

"""
Math & Science Router - Computation using Compound + Wolfram Alpha
"""
from fastapi import APIRouter, HTTPException
from models.schemas import MathRequest
from services.compound_service import compound_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/math", tags=["Math & Science"])


@router.post("/solve")
async def solve_math(request: MathRequest):
    """Solve math/science problems using Wolfram Alpha"""
    try:
        result = await compound_service.math_compute(
            query=request.query,
            show_steps=True,
        )
        return {
            "solution": result["content"],
            "tools_used": result.get("tools_used", []),
            "citations": result.get("citations", []),
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Math solve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compute")
async def compute(expression: str):
    """Quick computation"""
    try:
        result = await compound_service.math_compute(
            query=f"Compute: {expression}",
            show_steps=False,
        )
        return {
            "result": result["content"],
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Compute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))