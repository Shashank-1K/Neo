"""
Workspace Router - Unified workspace actions
"""
from fastapi import APIRouter, HTTPException
from services.compound_service import compound_service
from services.mcp_service import mcp_service
from api_key_manager import key_manager
from models.database import execute_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/workspace", tags=["Workspace"])


@router.get("/models")
async def list_models():
    """List all available models"""
    from config import settings
    return settings.MODELS


@router.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "api_keys": key_manager.get_stats(),
    }


@router.get("/usage")
async def get_usage_stats():
    """Get API usage statistics"""
    stats = await execute_query(
        """SELECT
            model,
            operation,
            COUNT(*) as total_calls,
            SUM(tokens_input) as total_input_tokens,
            SUM(tokens_output) as total_output_tokens,
            AVG(latency_ms) as avg_latency_ms,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures
        FROM usage_stats
        GROUP BY model, operation
        ORDER BY total_calls DESC"""
    )
    return {"usage": stats}


@router.get("/capabilities")
async def list_capabilities():
    """List all NEXUS capabilities"""
    return {
        "capabilities": [
            {
                "name": "Chat",
                "description": "Multi-model conversational AI",
                "endpoint": "/api/chat/",
                "models": ["llama-3.3-70b", "llama-3.1-8b", "kimi-k2", "qwen3-32b"],
            },
            {
                "name": "Voice",
                "description": "Speech-to-text and text-to-speech",
                "endpoint": "/api/voice/",
                "features": ["transcribe", "translate", "speak", "full pipeline"],
            },
            {
                "name": "Vision",
                "description": "Image analysis, OCR, and document understanding",
                "endpoint": "/api/vision/",
                "models": ["llama-4-scout", "llama-4-maverick"],
            },
            {
                "name": "Research",
                "description": "Web search, browser automation, and deep research",
                "endpoint": "/api/research/",
                "features": ["web search", "website analysis", "multi-step agents"],
            },
            {
                "name": "Code",
                "description": "Code generation, execution, and debugging",
                "endpoint": "/api/code/",
                "features": ["generate", "execute", "debug", "explain"],
            },
            {
                "name": "Math & Science",
                "description": "Computation using Wolfram Alpha",
                "endpoint": "/api/math/",
                "features": ["solve", "compute"],
            },
            {
                "name": "Structured Data",
                "description": "Extract structured data using JSON Schema",
                "endpoint": "/api/structured/",
                "presets": ["contact", "invoice", "meeting_notes", "sentiment", "todo_list"],
            },
            {
                "name": "Safety",
                "description": "Content moderation and safety checks",
                "endpoint": "/api/safety/",
                "models": ["llama-guard-4", "prompt-guard", "safeguard"],
            },
            {
                "name": "Batch",
                "description": "Bulk processing at 50% cost",
                "endpoint": "/api/batch/",
                "features": ["create", "status", "list jobs"],
            },
            {
                "name": "MCP Tools",
                "description": "Connect to external tools via MCP",
                "endpoint": "/api/mcp/",
                "features": ["custom servers", "Google Workspace"],
            },
        ]
    }