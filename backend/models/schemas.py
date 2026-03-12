"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ModelType(str, Enum):
    GENERAL = "general"
    FAST = "fast"
    CODING = "coding"
    REASONING = "reasoning"
    ARABIC = "arabic"
    VISION = "vision"
    COMPOUND = "compound"
    COMPOUND_MINI = "compound_mini"
    REASONING_LARGE = "reasoning_large"


# ── Chat ──
class ChatMessage(BaseModel):
    role: str = "user"
    content: str
    images: Optional[List[str]] = None  # base64 images


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: str = "general"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    images: Optional[List[str]] = None
    json_schema: Optional[Dict] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model_used: str
    tokens_used: int = 0
    latency_ms: float = 0
    citations: Optional[List[Dict]] = None


# ── Voice ──
class TTSRequest(BaseModel):
    text: str
    voice: str = "Fritz-PlayAI"
    model: str = "playai-tts"
    speed: float = 1.0
    response_format: str = "wav"


class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    latency_ms: float = 0


# ── Vision ──
class VisionRequest(BaseModel):
    prompt: str = "Describe this image in detail"
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    model: str = "vision_scout"
    max_tokens: int = 2048


class VisionResponse(BaseModel):
    analysis: str
    model_used: str
    latency_ms: float = 0


# ── Research ──
class ResearchRequest(BaseModel):
    query: str
    model: str = "compound"
    max_tokens: int = 8192
    include_citations: bool = True


class ResearchResponse(BaseModel):
    response: str
    citations: List[Dict] = []
    model_used: str
    tools_used: List[str] = []
    latency_ms: float = 0


# ── Code ──
class CodeRequest(BaseModel):
    prompt: str
    language: str = "python"
    model: str = "coding"
    execute: bool = False
    max_tokens: int = 4096


class CodeResponse(BaseModel):
    code: str
    explanation: str = ""
    execution_result: Optional[str] = None
    model_used: str
    latency_ms: float = 0


# ── Math ──
class MathRequest(BaseModel):
    query: str
    use_wolfram: bool = True
    model: str = "compound"


# ── Structured Data ──
class StructuredDataRequest(BaseModel):
    content: str
    schema_definition: Dict
    model: str = "general"
    images: Optional[List[str]] = None


class StructuredDataResponse(BaseModel):
    data: Dict
    model_used: str
    latency_ms: float = 0


# ── Safety ──
class SafetyCheckRequest(BaseModel):
    content: str
    check_type: str = "full"  # full, prompt_injection, content_moderation


class SafetyCheckResponse(BaseModel):
    is_safe: bool
    categories: Dict[str, bool] = {}
    details: str = ""
    model_used: str
    latency_ms: float = 0


# ── Batch ──
class BatchTask(BaseModel):
    type: str  # chat, transcribe, translate
    payload: Dict


class BatchRequest(BaseModel):
    tasks: List[BatchTask]
    priority: str = "normal"  # normal, high


class BatchResponse(BaseModel):
    job_id: str
    status: str
    total_tasks: int


# ── Workspace ──
class WorkspaceAction(BaseModel):
    action: str  # read_email, search_email, get_calendar, search_drive
    parameters: Dict = {}


# ── MCP ──
class MCPToolRequest(BaseModel):
    server_url: str
    tool_name: str
    arguments: Dict = {}
    model: str = "general"