"""
Research Router - Web research using Compound AI
"""
from fastapi import APIRouter, HTTPException
from models.schemas import ResearchRequest, ResearchResponse
from services.compound_service import compound_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["Research"])


@router.post("/", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Research a topic using web search and browser automation"""
    try:
        result = await compound_service.research(
            query=request.query,
            model=request.model,
            max_tokens=request.max_tokens,
        )
        return ResearchResponse(
            response=result["content"],
            citations=result.get("citations", []),
            model_used=result["model"],
            tools_used=result.get("tools_used", []),
            latency_ms=result["latency_ms"],
        )
    except Exception as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/website")
async def analyze_website(url: str, task: str = "Summarize the content"):
    """Visit and analyze a website"""
    try:
        result = await compound_service.visit_website(url=url, task=task)
        return {
            "response": result["content"],
            "citations": result.get("citations", []),
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Website analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent")
async def multi_step_agent(task: str, steps: list = None):
    """Execute a multi-step agentic task"""
    try:
        result = await compound_service.multi_step_agent(
            task=task,
            steps=steps,
        )
        return {
            "response": result["content"],
            "tools_used": result.get("tools_used", []),
            "citations": result.get("citations", []),
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))