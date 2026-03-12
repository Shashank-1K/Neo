"""
NEXUS — Universal AI Workspace Assistant
Main FastAPI Application

The most comprehensive AI workspace product built on Groq's full stack:
- Ultra-fast chat with 6 model families
- Voice pipeline (Whisper STT → LLM → Orpheus TTS)
- Vision & OCR (Llama 4 Scout/Maverick)
- Agentic research (Compound with web search, code execution, Wolfram Alpha)
- Structured data extraction (JSON Schema enforcement)
- Content safety (Llama Guard 4, Prompt Guard, Safeguard)
- Batch processing (50% cost savings)
- MCP tool integration (connect to anything)
- Smart API key rotation across 6 keys
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import init_db

# Import all routers
from routers import (
    chat, voice, vision, research, code_execution,
    math_science, structured_data, safety, batch,
    mcp_tools, conversations, files, workspace,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("🚀 Starting NEXUS AI Workspace...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("frontend", exist_ok=True)
    logger.info("✅ File storage ready")

    logger.info(f"✅ {len(settings.GROQ_API_KEYS)} API keys loaded")
    logger.info(f"✅ {len(settings.MODELS)} models configured")
    logger.info("=" * 60)
    logger.info("  NEXUS AI Workspace is LIVE  ")
    logger.info(f"  Open http://localhost:{settings.PORT}")
    logger.info("=" * 60)

    yield

    logger.info("👋 Shutting down NEXUS...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Universal AI Workspace Assistant powered by Groq",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(vision.router)
app.include_router(research.router)
app.include_router(code_execution.router)
app.include_router(math_science.router)
app.include_router(structured_data.router)
app.include_router(safety.router)
app.include_router(batch.router)
app.include_router(mcp_tools.router)
app.include_router(conversations.router)
app.include_router(files.router)
app.include_router(workspace.router)

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend application"""
    return FileResponse("frontend/index.html")


@app.get("/api")
async def api_root():
    """API root - lists all endpoints"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "chat": "/api/chat/",
            "voice": "/api/voice/",
            "vision": "/api/vision/",
            "research": "/api/research/",
            "code": "/api/code/",
            "math": "/api/math/",
            "structured": "/api/structured/",
            "safety": "/api/safety/",
            "batch": "/api/batch/",
            "mcp": "/api/mcp/",
            "conversations": "/api/conversations/",
            "files": "/api/files/",
            "workspace": "/api/workspace/",
        },
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )