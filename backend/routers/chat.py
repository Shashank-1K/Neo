"""
Chat Router - Main conversational AI endpoint
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ChatResponse
from services.groq_client import groq_service
from services.conversation_manager import conversation_manager
from services.safety_service import safety_service
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with full conversation history,
    optional safety checks, and structured output support.
    """
    try:
        # Ensure conversation exists
        conv_id = await conversation_manager.ensure_conversation(
            request.conversation_id,
            request.model,
            request.system_prompt or "",
        )

        # Add user message
        await conversation_manager.add_message(conv_id, "user", request.message)

        # Build messages for API
        system_prompt = request.system_prompt or (
            "You are NEXUS, an advanced AI workspace assistant. You are helpful, "
            "knowledgeable, and capable. You can help with research, coding, "
            "analysis, writing, and much more. Be concise but thorough."
        )

        messages = conversation_manager.get_messages_for_api(conv_id, system_prompt)

        # Handle vision content
        if request.images:
            # Modify last message to include images
            last_msg = messages[-1]
            content = [{"type": "text", "text": last_msg["content"]}]
            for img in request.images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img}"}
                })
            messages[-1] = {"role": "user", "content": content}

            # Use vision model
            model = "vision_scout"
        else:
            model = request.model

        # Prepare response format
        response_format = None
        if request.json_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "schema": request.json_schema,
                    "strict": True,
                }
            }

        # Call Groq API
        result = await groq_service.chat_completion(
            messages=messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=response_format,
        )

        # Save assistant message
        await conversation_manager.add_message(
            conv_id, "assistant", result["content"],
            model_used=result["model"],
            tokens_used=result["tokens_used"],
            latency_ms=result["latency_ms"],
        )

        return ChatResponse(
            response=result["content"],
            conversation_id=conv_id,
            model_used=result["model"],
            tokens_used=result["tokens_used"],
            latency_ms=result["latency_ms"],
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint"""
    try:
        conv_id = await conversation_manager.ensure_conversation(
            request.conversation_id,
            request.model,
            request.system_prompt or "",
        )

        await conversation_manager.add_message(conv_id, "user", request.message)

        system_prompt = request.system_prompt or (
            "You are NEXUS, an advanced AI workspace assistant."
        )
        messages = conversation_manager.get_messages_for_api(conv_id, system_prompt)

        full_response = []

        async def generate():
            async for chunk in groq_service.chat_completion_stream(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                full_response.append(chunk)
                yield f"data: {json.dumps({'content': chunk, 'conversation_id': conv_id})}\n\n"

            # Save full response
            complete = "".join(full_response)
            await conversation_manager.add_message(
                conv_id, "assistant", complete,
                model_used=request.model,
            )
            yield f"data: {json.dumps({'done': True, 'conversation_id': conv_id})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/with-safety")
async def chat_with_safety(request: ChatRequest):
    """Chat with automatic safety checking"""
    try:
        # Check input safety
        safety_result = await safety_service.moderate_content(request.message)
        if not safety_result["is_safe"]:
            return ChatResponse(
                response="I cannot process this request as it was flagged by our safety system.",
                conversation_id=request.conversation_id or "",
                model_used="safety-filter",
                tokens_used=0,
                latency_ms=safety_result["latency_ms"],
            )

        # Process normally
        result = await chat(request)

        # Check output safety
        output_safety = await safety_service.moderate_content(result.response)
        if not output_safety["is_safe"]:
            return ChatResponse(
                response="The generated response was filtered by our safety system. Please rephrase your request.",
                conversation_id=result.conversation_id,
                model_used="safety-filter",
                tokens_used=0,
                latency_ms=result.latency_ms,
            )

        return result

    except Exception as e:
        logger.error(f"Safe chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))