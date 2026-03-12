"""
Conversation Manager - Handles multi-turn conversations with context
"""
import uuid
import time
from typing import Optional, List, Dict
from models.database import (
    save_conversation, save_message, get_conversation_messages,
    get_conversations, delete_conversation
)
from config import settings


class ConversationManager:
    """Manages conversation state and history"""

    def __init__(self):
        self._active_contexts: Dict[str, Dict] = {}

    def create_conversation(
        self,
        model: str = "general",
        system_prompt: str = "",
        title: str = "New Conversation"
    ) -> str:
        """Create a new conversation and return its ID"""
        conv_id = str(uuid.uuid4())
        self._active_contexts[conv_id] = {
            "model": model,
            "system_prompt": system_prompt,
            "title": title,
            "messages": [],
        }
        return conv_id

    async def ensure_conversation(
        self,
        conversation_id: Optional[str] = None,
        model: str = "general",
        system_prompt: str = "",
    ) -> str:
        """Ensure a conversation exists, creating one if needed"""
        if conversation_id and conversation_id in self._active_contexts:
            return conversation_id

        if conversation_id:
            # Try loading from DB
            messages = await get_conversation_messages(conversation_id)
            if messages:
                self._active_contexts[conversation_id] = {
                    "model": model,
                    "system_prompt": system_prompt,
                    "title": "Loaded Conversation",
                    "messages": [
                        {"role": m["role"], "content": m["content"]}
                        for m in messages
                    ],
                }
                return conversation_id

        # Create new
        conv_id = self.create_conversation(model, system_prompt)
        await save_conversation(conv_id, "New Conversation", model, system_prompt)
        return conv_id

    def get_messages_for_api(
        self,
        conversation_id: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict]:
        """Get messages formatted for the Groq API"""
        ctx = self._active_contexts.get(conversation_id, {})
        messages = []

        # System prompt
        sys_prompt = system_prompt or ctx.get("system_prompt", "")
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        # Conversation history (last N messages)
        history = ctx.get("messages", [])
        max_history = settings.MAX_CONVERSATION_HISTORY
        if len(history) > max_history:
            history = history[-max_history:]

        messages.extend(history)
        return messages

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        model_used: str = "",
        tokens_used: int = 0,
        latency_ms: float = 0,
        metadata: dict = None,
    ):
        """Add a message to conversation history"""
        if conversation_id not in self._active_contexts:
            self._active_contexts[conversation_id] = {
                "messages": [], "model": "", "system_prompt": "", "title": ""
            }

        self._active_contexts[conversation_id]["messages"].append({
            "role": role,
            "content": content,
        })

        # Persist to DB
        await save_message(
            conversation_id, role, content,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            metadata=metadata,
        )

        # Auto-title on first message
        if (role == "user" and
            len(self._active_contexts[conversation_id]["messages"]) == 1):
            title = content[:80] + ("..." if len(content) > 80 else "")
            self._active_contexts[conversation_id]["title"] = title
            await save_conversation(conversation_id, title)

    async def get_all_conversations(self) -> List[Dict]:
        """Get all conversations"""
        return await get_conversations()

    async def delete(self, conversation_id: str):
        """Delete a conversation"""
        if conversation_id in self._active_contexts:
            del self._active_contexts[conversation_id]
        await delete_conversation(conversation_id)


# Singleton
conversation_manager = ConversationManager()