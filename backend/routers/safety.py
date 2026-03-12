"""
Safety Router - Content moderation and safety checks
"""
from fastapi import APIRouter, HTTPException
from models.schemas import SafetyCheckRequest, SafetyCheckResponse
from services.safety_service import safety_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/safety", tags=["Safety"])


@router.post("/check", response_model=SafetyCheckResponse)
async def safety_check(request: SafetyCheckRequest):
    """Check content for safety"""
    try:
        if request.check_type == "full":
            result = await safety_service.full_safety_check(request.content)
            return SafetyCheckResponse(
                is_safe=result["is_safe"],
                categories=result.get("checks", {}),
                details="; ".join(result.get("details", [])),
                model_used="multi-model",
                latency_ms=sum(
                    c.get("latency_ms", 0)
                    for c in result.get("checks", {}).values()
                ),
            )
        elif request.check_type == "content_moderation":
            result = await safety_service.moderate_content(request.content)
            return SafetyCheckResponse(
                is_safe=result["is_safe"],
                details=result["details"],
                model_used=result["model"],
                latency_ms=result["latency_ms"],
            )
        elif request.check_type == "prompt_injection":
            result = await safety_service._check_prompt_injection(request.content)
            return SafetyCheckResponse(
                is_safe=result["is_safe"],
                details=result["details"],
                model_used="prompt_guard",
                latency_ms=result["latency_ms"],
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown check type: {request.check_type}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Safety check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def deep_safety_analysis(content: str):
    """Deep safety analysis with reasoning"""
    try:
        result = await safety_service.safeguard_reasoning(content)
        return {
            "is_safe": result["is_safe"],
            "analysis": result["details"],
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Safety analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))