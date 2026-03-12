"""
Voice Router - Speech-to-text, text-to-speech, and full voice pipeline
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional
from models.schemas import TTSRequest, TranscriptionResponse
from services.voice_service import voice_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["Voice"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    fast: bool = Form(False),
):
    """Transcribe audio to text using Whisper"""
    try:
        audio_data = await file.read()
        result = await voice_service.transcribe_audio(
            audio_data=audio_data,
            filename=file.filename or "audio.wav",
            language=language,
            fast=fast,
        )
        return TranscriptionResponse(
            text=result["text"],
            latency_ms=result["latency_ms"],
        )
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate", response_model=TranscriptionResponse)
async def translate_audio(
    file: UploadFile = File(...),
):
    """Translate audio to English text"""
    try:
        audio_data = await file.read()
        result = await voice_service.translate_audio(
            audio_data=audio_data,
            filename=file.filename or "audio.wav",
        )
        return TranscriptionResponse(
            text=result["text"],
            latency_ms=result["latency_ms"],
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        audio_data, latency = await voice_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            model=request.model,
        )

        content_type = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "flac": "audio/flac",
        }.get(request.response_format, "audio/wav")

        return Response(
            content=audio_data,
            media_type=content_type,
            headers={
                "X-Latency-Ms": str(latency),
                "Content-Disposition": f'attachment; filename="speech.{request.response_format}"',
            },
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline")
async def voice_pipeline(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    model: str = Form("general"),
    voice: str = Form("Fritz-PlayAI"),
    system_prompt: str = Form(
        "You are a helpful voice assistant. Keep responses concise and conversational."
    ),
):
    """
    Full voice pipeline: Audio → STT → LLM → TTS → Audio
    Returns JSON with transcription, response text, and audio base64
    """
    try:
        audio_data = await file.read()
        result = await voice_service.full_voice_pipeline(
            audio_data=audio_data,
            filename=file.filename or "audio.wav",
            conversation_id=conversation_id,
            model=model,
            voice=voice,
            system_prompt=system_prompt,
        )
        return result
    except Exception as e:
        logger.error(f"Voice pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices():
    """List available TTS voices"""
    from config import settings
    return {
        "english": settings.TTS_VOICES["english"],
        "arabic": settings.TTS_VOICES["arabic"],
    }