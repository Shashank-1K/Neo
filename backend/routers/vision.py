"""
Vision Router - Image analysis, OCR, and document understanding
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from models.schemas import VisionRequest, VisionResponse
from services.vision_service import vision_service
import base64
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vision", tags=["Vision"])


@router.post("/analyze", response_model=VisionResponse)
async def analyze_image(request: VisionRequest):
    """Analyze an image with a text prompt"""
    try:
        result = await vision_service.analyze_image(
            prompt=request.prompt,
            image_base64=request.image_base64,
            image_url=request.image_url,
            model=request.model,
            max_tokens=request.max_tokens,
        )
        return VisionResponse(
            analysis=result["content"],
            model_used=result["model"],
            latency_ms=result["latency_ms"],
        )
    except Exception as e:
        logger.error(f"Vision analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-upload", response_model=VisionResponse)
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail"),
    model: str = Form("vision_scout"),
):
    """Analyze an uploaded image"""
    try:
        image_data = await file.read()
        image_b64 = base64.b64encode(image_data).decode()

        result = await vision_service.analyze_image(
            prompt=prompt,
            image_base64=image_b64,
            model=model,
        )
        return VisionResponse(
            analysis=result["content"],
            model_used=result["model"],
            latency_ms=result["latency_ms"],
        )
    except Exception as e:
        logger.error(f"Vision upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr")
async def extract_text(
    file: UploadFile = File(None),
    image_base64: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
):
    """Extract text from image (OCR)"""
    try:
        b64 = image_base64
        if file and not b64:
            image_data = await file.read()
            b64 = base64.b64encode(image_data).decode()

        result = await vision_service.extract_text_ocr(
            image_base64=b64,
            image_url=image_url,
        )
        return {
            "text": result["content"],
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document")
async def analyze_document(
    file: UploadFile = File(None),
    image_base64: Optional[str] = Form(None),
    analysis_type: str = Form("summary"),
):
    """Analyze a document image"""
    try:
        b64 = image_base64
        if file and not b64:
            image_data = await file.read()
            b64 = base64.b64encode(image_data).decode()

        result = await vision_service.analyze_document(
            image_base64=b64,
            analysis_type=analysis_type,
        )
        return {
            "analysis": result["content"],
            "analysis_type": analysis_type,
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Document analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))