"""
Structured Data Router - Extract and structure data using JSON Schema
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from models.schemas import StructuredDataRequest, StructuredDataResponse
from services.structured_output_service import structured_service
import base64
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/structured", tags=["Structured Data"])


@router.post("/extract", response_model=StructuredDataResponse)
async def extract_structured(request: StructuredDataRequest):
    """Extract structured data from text content"""
    try:
        result = await structured_service.extract(
            content=request.content,
            schema=request.schema_definition,
            model=request.model,
        )
        return StructuredDataResponse(
            data=result["data"],
            model_used=result["model"],
            latency_ms=result["latency_ms"],
        )
    except Exception as e:
        logger.error(f"Structured extract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-preset")
async def extract_with_preset(
    content: str,
    preset: str,
    model: str = "general",
):
    """Extract data using a pre-built schema preset"""
    try:
        result = await structured_service.extract_with_preset(
            content=content,
            preset=preset,
            model=model,
        )
        return {
            "data": result["data"],
            "preset": preset,
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Preset extract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-image")
async def extract_from_image(
    file: UploadFile = File(...),
    schema: str = Form(...),
    prompt: str = Form("Extract structured data from this image"),
):
    """Extract structured data from an image"""
    try:
        image_data = await file.read()
        image_b64 = base64.b64encode(image_data).decode()
        schema_dict = json.loads(schema)

        result = await structured_service.extract_from_image(
            image_base64=image_b64,
            schema=schema_dict,
            prompt=prompt,
        )
        return {
            "data": result["data"],
            "model_used": result["model"],
            "latency_ms": result["latency_ms"],
        }
    except Exception as e:
        logger.error(f"Image extract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets")
async def list_presets():
    """List available extraction presets"""
    return structured_service.get_available_presets()