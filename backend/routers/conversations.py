"""
Conversations Router - Manage conversation history
"""
from fastapi import APIRouter, HTTPException
from services.conversation_manager import conversation_manager
from models.database import get_conversation_messages
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("/")
async def list_conversations():
    """Get all conversations"""
    return await conversation_manager.get_all_conversations()


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation with messages"""
    messages = await get_conversation_messages(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": messages,
    }


@router.delete("/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    """Delete a conversation"""
    await conversation_manager.delete(conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/new")
async def create_conversation(
    model: str = "general",
    system_prompt: str = "",
    title: str = "New Conversation",
):
    """Create a new conversation"""
    from models.database import save_conversation
    conv_id = conversation_manager.create_conversation(model, system_prompt, title)
    await save_conversation(conv_id, title, model, system_prompt)
    return {"conversation_id": conv_id, "title": title}