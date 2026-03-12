"""
NEXUS Configuration - Central configuration for all services
"""
import os
from typing import List, Dict
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()  # <-- this reads backend/.env

class Settings(BaseModel):
    APP_NAME: str = "NEXUS AI Workspace"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Groq API Keys - Round Robin Pool
    # GROQ_API_KEYS: List[str] = os.getenv("GROQ_API_KEYS", "").split(",")
    # GROQ_API_KEYS: List[str] = [key.strip() for key in os.getenv("GROQ_API_KEYS", "").split(",") if key.strip()]
    GROQ_API_KEYS: List[str] = [key.strip() for key in os.getenv("GROQ_API_KEYS", "").split(",") if key.strip()]


    # Model Configurations — ADDED Dict[str, str] annotation
    MODELS: Dict[str, str] = {
        # Chat Models
        "general": "llama-3.3-70b-versatile",
        "fast": "llama-3.1-8b-instant",
        "coding": "moonshotai/kimi-k2-instruct",
        "reasoning": "qwen/qwen3-32b",
        "arabic": "allam-2-7b",

        # Vision Models
        "vision_maverick": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "vision_scout": "meta-llama/llama-4-scout-17b-16e-instruct",

        # Compound (Agentic)
        "compound": "groq/compound",
        "compound_mini": "groq/compound-mini",

        # Speech
        "stt": "whisper-large-v3",
        "stt_fast": "whisper-large-v3-turbo",
        "tts_english": "playai-tts",
        "tts_arabic": "playai-tts-arabic",

        # Safety
        "guard": "meta-llama/llama-guard-4-12b",
        "prompt_guard": "meta-llama/llama-prompt-guard-2-86m",
        "safeguard": "openai/gpt-oss-safeguard-20b",

        # Reasoning
        "reasoning_large": "openai/gpt-oss-120b",
        "reasoning_small": "openai/gpt-oss-20b",
    }

    # TTS Voices — ADDED Dict[str, List[str]] annotation
    TTS_VOICES: Dict[str, List[str]] = {
        "english": [
            "Fritz-PlayAI", "Arista-PlayAI", "Atlas-PlayAI",
            "Basil-PlayAI", "Briggs-PlayAI", "Calista-PlayAI",
            "Celeste-PlayAI", "Cheyenne-PlayAI", "Chip-PlayAI",
            "Cillian-PlayAI", "Deedee-PlayAI", "Eleanor-PlayAI",
            "Gail-PlayAI", "Indigo-PlayAI", "Mamaw-PlayAI",
            "Mason-PlayAI", "Mikail-PlayAI", "Mitch-PlayAI",
            "Nia-PlayAI", "Quinn-PlayAI", "Thunder-PlayAI",
        ],
        "arabic": [
            "Ahmad-PlayAI", "Amira-PlayAI", "Khalid-PlayAI", "Noura-PlayAI",
        ],
    }

    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 25 * 1024 * 1024  # 25MB
    ALLOWED_AUDIO_FORMATS: List[str] = [
        "flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "wav", "webm"
    ]
    ALLOWED_IMAGE_FORMATS: List[str] = ["png", "jpg", "jpeg", "gif", "webp"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///nexus.db"

    # Conversation
    MAX_CONVERSATION_HISTORY: int = 50
    DEFAULT_MAX_TOKENS: int = 4096
    DEFAULT_TEMPERATURE: float = 0.7


settings = Settings()