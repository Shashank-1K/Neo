"""
Core Groq Client Service - Central interface for all Groq API calls
"""
import time
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from groq import Groq, AsyncGroq
from config import settings
from api_key_manager import key_manager
from models.database import log_usage
import logging
import httpx

logger = logging.getLogger(__name__)


class GroqClientService:
    """
    Unified Groq client that handles:
    - Automatic key rotation
    - Retry with fallback keys
    - Usage tracking
    - All API endpoints
    """

    def _get_model_id(self, model_alias: str) -> str:
        """Resolve model alias to actual model ID"""
        return settings.MODELS.get(model_alias, model_alias)

    async def _get_client(self, workload: str = "chat") -> tuple:
        """Get an AsyncGroq client with an appropriate key"""
        api_key = await key_manager.get_key(workload)
        client = AsyncGroq(api_key=api_key)
        return client, api_key

    async def _call_with_retry(self, func, workload: str = "chat",
                                max_retries: int = 3, **kwargs):
        """Execute an API call with automatic retry on different keys"""
        last_error = None

        for attempt in range(max_retries):
            client, api_key = await self._get_client(workload)
            start_time = time.time()

            try:
                result = await func(client, **kwargs)
                latency = (time.time() - start_time) * 1000
                await key_manager.report_success(api_key)
                return result, latency, api_key

            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = "rate_limit" in error_str or "429" in error_str

                await key_manager.report_failure(api_key, is_rate_limit)
                last_error = e

                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed on key "
                    f"{api_key[:20]}...: {e}"
                )

                if not is_rate_limit and "invalid" not in error_str:
                    raise

                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))

        raise last_error

    # ─── CHAT COMPLETIONS ───

    async def chat_completion(
        self,
        messages: List[Dict],
        model: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[Dict] = None,
        stream: bool = False,
    ) -> Dict:
        """Standard chat completion"""
        model_id = self._get_model_id(model)

        async def _call(client, **kw):
            params = {
                "model": model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
            if response_format:
                params["response_format"] = response_format
            if stream:
                params["stream"] = True

            if stream:
                return await client.chat.completions.create(**params)
            else:
                return await client.chat.completions.create(**params)

        result, latency, api_key = await self._call_with_retry(
            _call, workload="chat"
        )

        if stream:
            return {"stream": result, "latency_ms": latency, "model": model_id}

        # Extract response
        choice = result.choices[0]
        usage = result.usage

        await log_usage(
            api_key[:20], model_id, "chat",
            tokens_input=usage.prompt_tokens if usage else 0,
            tokens_output=usage.completion_tokens if usage else 0,
            latency_ms=latency
        )

        return {
            "content": choice.message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in (choice.message.tool_calls or [])
            ],
            "tokens_used": (usage.total_tokens if usage else 0),
            "latency_ms": latency,
            "model": model_id,
            "finish_reason": choice.finish_reason,
        }

    async def chat_completion_stream(
        self,
        messages: List[Dict],
        model: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion"""
        model_id = self._get_model_id(model)
        api_key = await key_manager.get_key("chat")
        client = AsyncGroq(api_key=api_key)

        try:
            stream = await client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            await key_manager.report_success(api_key)

        except Exception as e:
            await key_manager.report_failure(api_key, "429" in str(e))
            raise

    # ─── COMPOUND (AGENTIC) ───

    async def compound_query(
        self,
        messages: List[Dict],
        model: str = "compound",
        max_tokens: int = 8192,
    ) -> Dict:
        """
        Compound AI system with built-in tools:
        web search, code execution, browser, Wolfram Alpha
        """
        model_id = self._get_model_id(model)

        async def _call(client, **kw):
            return await client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=max_tokens,
            )

        result, latency, api_key = await self._call_with_retry(
            _call, workload="compound"
        )

        choice = result.choices[0]
        usage = result.usage

        # Extract executed tools from response metadata
        executed_tools = []
        if hasattr(choice.message, 'executed_tools'):
            executed_tools = choice.message.executed_tools or []

        citations = []
        if hasattr(result, 'citations'):
            citations = result.citations or []

        await log_usage(
            api_key[:20], model_id, "compound",
            tokens_input=usage.prompt_tokens if usage else 0,
            tokens_output=usage.completion_tokens if usage else 0,
            latency_ms=latency
        )

        return {
            "content": choice.message.content or "",
            "tools_used": executed_tools,
            "citations": citations,
            "tokens_used": usage.total_tokens if usage else 0,
            "latency_ms": latency,
            "model": model_id,
        }

    # ─── VISION ───

    async def vision_analysis(
        self,
        prompt: str,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        model: str = "vision_scout",
        max_tokens: int = 2048,
    ) -> Dict:
        """Analyze images with vision models"""
        model_id = self._get_model_id(model)

        content = []
        content.append({"type": "text", "text": prompt})

        if image_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            })
        elif image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        messages = [{"role": "user", "content": content}]

        async def _call(client, **kw):
            return await client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=max_tokens,
            )

        result, latency, api_key = await self._call_with_retry(
            _call, workload="vision"
        )

        choice = result.choices[0]
        usage = result.usage

        await log_usage(
            api_key[:20], model_id, "vision",
            tokens_input=usage.prompt_tokens if usage else 0,
            tokens_output=usage.completion_tokens if usage else 0,
            latency_ms=latency
        )

        return {
            "content": choice.message.content or "",
            "tokens_used": usage.total_tokens if usage else 0,
            "latency_ms": latency,
            "model": model_id,
        }

    # ─── SPEECH TO TEXT ───

    async def transcribe(
        self,
        audio_file,
        model: str = "stt",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> Dict:
        """Transcribe audio to text"""
        model_id = self._get_model_id(model)

        async def _call(client, **kw):
            params = {
                "model": model_id,
                "file": audio_file,
            }
            if language:
                params["language"] = language
            if prompt:
                params["prompt"] = prompt
            return await client.audio.transcriptions.create(**params)

        result, latency, api_key = await self._call_with_retry(
            _call, workload="voice"
        )

        await log_usage(api_key[:20], model_id, "transcribe", latency_ms=latency)

        return {
            "text": result.text,
            "latency_ms": latency,
            "model": model_id,
        }

    async def translate_audio(
        self,
        audio_file,
        model: str = "stt",
    ) -> Dict:
        """Translate audio to English text"""
        model_id = self._get_model_id(model)

        async def _call(client, **kw):
            return await client.audio.translations.create(
                model=model_id,
                file=audio_file,
            )

        result, latency, api_key = await self._call_with_retry(
            _call, workload="voice"
        )

        await log_usage(api_key[:20], model_id, "translate", latency_ms=latency)

        return {
            "text": result.text,
            "latency_ms": latency,
            "model": model_id,
        }

    # ─── TEXT TO SPEECH ───

    async def text_to_speech(
        self,
        text: str,
        voice: str = "Fritz-PlayAI",
        model: str = "playai-tts",
        response_format: str = "wav",
    ) -> tuple:
        """Convert text to speech audio"""
        api_key = await key_manager.get_key("voice")
        start_time = time.time()

        try:
            # Use httpx directly for TTS since the SDK may not support it yet
            async with httpx.AsyncClient(timeout=60.0) as http_client:
                response = await http_client.post(
                    "https://api.groq.com/openai/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "input": text,
                        "voice": voice,
                        "response_format": response_format,
                    },
                )
                response.raise_for_status()
                audio_data = response.content

            latency = (time.time() - start_time) * 1000
            await key_manager.report_success(api_key)
            await log_usage(api_key[:20], model, "tts", latency_ms=latency)

            return audio_data, latency

        except Exception as e:
            await key_manager.report_failure(api_key, "429" in str(e))
            raise

    # ─── SAFETY ───

    async def check_safety(
        self,
        content: str,
        model: str = "guard",
    ) -> Dict:
        """Check content safety with guard models"""
        model_id = self._get_model_id(model)

        messages = [{"role": "user", "content": content}]

        async def _call(client, **kw):
            return await client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=512,
            )

        result, latency, api_key = await self._call_with_retry(
            _call, workload="safety"
        )

        response_text = result.choices[0].message.content or ""
        is_safe = "safe" in response_text.lower() and "unsafe" not in response_text.lower()

        await log_usage(api_key[:20], model_id, "safety", latency_ms=latency)

        return {
            "is_safe": is_safe,
            "details": response_text,
            "latency_ms": latency,
            "model": model_id,
        }

    # ─── STRUCTURED OUTPUTS ───

    async def structured_completion(
        self,
        messages: List[Dict],
        json_schema: Dict,
        model: str = "general",
        temperature: float = 0.3,
    ) -> Dict:
        """Get structured JSON output conforming to a schema"""
        model_id = self._get_model_id(model)

        async def _call(client, **kw):
            return await client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=4096,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_output",
                        "schema": json_schema,
                        "strict": True,
                    }
                },
            )

        result, latency, api_key = await self._call_with_retry(
            _call, workload="chat"
        )

        content = result.choices[0].message.content or "{}"
        parsed = json.loads(content)

        await log_usage(api_key[:20], model_id, "structured", latency_ms=latency)

        return {
            "data": parsed,
            "latency_ms": latency,
            "model": model_id,
        }

    # ─── TOOL CALLING ───

    async def function_call(
        self,
        messages: List[Dict],
        tools: List[Dict],
        model: str = "general",
        tool_choice: str = "auto",
    ) -> Dict:
        """Execute function/tool calling"""
        return await self.chat_completion(
            messages=messages,
            model=model,
            tools=tools,
            tool_choice=tool_choice,
        )


# Singleton
groq_service = GroqClientService()