"""
Voice Service - Complete voice pipeline (STT → LLM → TTS)
"""
import io
import base64
from typing import Optional, Tuple
from services.groq_client import groq_service
from services.conversation_manager import conversation_manager
import logging

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Full voice interaction pipeline:
    1. Whisper STT (audio → text)
    2. LLM processing (text → response)
    3. Orpheus TTS (response → audio)
    """

    async def transcribe_audio(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None,
        fast: bool = False,
    ) -> dict:
        """Transcribe audio to text"""
        model = "stt_fast" if fast else "stt"
        audio_file = (filename, audio_data)

        result = await groq_service.transcribe(
            audio_file=audio_file,
            model=model,
            language=language,
        )
        return result

    async def translate_audio(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
    ) -> dict:
        """Translate audio to English"""
        audio_file = (filename, audio_data)
        result = await groq_service.translate_audio(audio_file=audio_file)
        return result

    async def text_to_speech(
        self,
        text: str,
        voice: str = "Fritz-PlayAI",
        model: str = "playai-tts",
    ) -> Tuple[bytes, float]:
        """Convert text to speech"""
        audio_data, latency = await groq_service.text_to_speech(
            text=text,
            voice=voice,
            model=model,
        )
        return audio_data, latency

    async def full_voice_pipeline(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
        conversation_id: Optional[str] = None,
        model: str = "general",
        voice: str = "Fritz-PlayAI",
        system_prompt: str = "You are a helpful voice assistant. Keep responses concise and conversational.",
    ) -> dict:
        """
        Complete voice pipeline:
        Audio In → STT → LLM → TTS → Audio Out
        """
        # Step 1: Transcribe
        stt_result = await self.transcribe_audio(audio_data, filename)
        user_text = stt_result["text"]
        stt_latency = stt_result["latency_ms"]

        # Step 2: Process with LLM
        conv_id = await conversation_manager.ensure_conversation(
            conversation_id, model, system_prompt
        )
        await conversation_manager.add_message(conv_id, "user", user_text)

        messages = conversation_manager.get_messages_for_api(conv_id, system_prompt)

        llm_result = await groq_service.chat_completion(
            messages=messages,
            model=model,
            max_tokens=1024,
            temperature=0.7,
        )
        response_text = llm_result["content"]
        llm_latency = llm_result["latency_ms"]

        await conversation_manager.add_message(
            conv_id, "assistant", response_text,
            model_used=llm_result["model"],
            tokens_used=llm_result["tokens_used"],
            latency_ms=llm_latency,
        )

        # Step 3: Text to Speech
        tts_audio, tts_latency = await self.text_to_speech(
            text=response_text,
            voice=voice,
        )

        total_latency = stt_latency + llm_latency + tts_latency

        return {
            "user_text": user_text,
            "response_text": response_text,
            "audio_base64": base64.b64encode(tts_audio).decode(),
            "conversation_id": conv_id,
            "latency": {
                "stt_ms": stt_latency,
                "llm_ms": llm_latency,
                "tts_ms": tts_latency,
                "total_ms": total_latency,
            },
            "model_used": llm_result["model"],
        }


# Singleton
voice_service = VoiceService()