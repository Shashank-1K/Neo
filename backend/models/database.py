"""
Database models and initialization
"""
import aiosqlite
import json
import time
from typing import Optional, List, Dict, Any
from config import settings
import os

DB_PATH = "nexus.db"


async def init_db():
    """Initialize the database with all required tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT 'New Conversation',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                model TEXT DEFAULT 'llama-3.3-70b-versatile',
                system_prompt TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT DEFAULT 'text',
                model_used TEXT,
                tokens_used INTEGER DEFAULT 0,
                latency_ms REAL DEFAULT 0,
                created_at REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );

            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                conversation_id TEXT,
                created_at REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS batch_jobs (
                id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'pending',
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                completed_at REAL,
                results TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_prefix TEXT NOT NULL,
                model TEXT NOT NULL,
                operation TEXT NOT NULL,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                latency_ms REAL DEFAULT 0,
                success INTEGER DEFAULT 1,
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created
                ON messages(created_at);
            CREATE INDEX IF NOT EXISTS idx_files_conversation
                ON files(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_usage_created
                ON usage_stats(created_at);
        """)
        await db.commit()


async def execute_query(query: str, params: tuple = ()) -> List[Dict]:
    """Execute a SELECT query and return results as dicts"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def execute_insert(query: str, params: tuple = ()) -> Optional[int]:
    """Execute an INSERT/UPDATE query"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor.lastrowid


async def save_conversation(conv_id: str, title: str = "New Conversation",
                            model: str = "", system_prompt: str = ""):
    """Create or update a conversation"""
    now = time.time()
    await execute_insert(
        """INSERT OR REPLACE INTO conversations
           (id, title, created_at, updated_at, model, system_prompt)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (conv_id, title, now, now, model, system_prompt)
    )


async def save_message(conversation_id: str, role: str, content: str,
                       content_type: str = "text", model_used: str = "",
                       tokens_used: int = 0, latency_ms: float = 0,
                       metadata: dict = None):
    """Save a message to a conversation"""
    now = time.time()
    await execute_insert(
        """INSERT INTO messages
           (conversation_id, role, content, content_type, model_used,
            tokens_used, latency_ms, created_at, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (conversation_id, role, content, content_type, model_used,
         tokens_used, latency_ms, now, json.dumps(metadata or {}))
    )
    # Update conversation timestamp
    await execute_insert(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id)
    )


async def get_conversation_messages(conversation_id: str,
                                     limit: int = 50) -> List[Dict]:
    """Get messages for a conversation"""
    return await execute_query(
        """SELECT * FROM messages
           WHERE conversation_id = ?
           ORDER BY created_at ASC
           LIMIT ?""",
        (conversation_id, limit)
    )


async def get_conversations(limit: int = 50) -> List[Dict]:
    """Get all conversations ordered by most recent"""
    return await execute_query(
        """SELECT * FROM conversations
           ORDER BY updated_at DESC
           LIMIT ?""",
        (limit,)
    )


async def delete_conversation(conversation_id: str):
    """Delete a conversation and its messages"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
        await db.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        await db.commit()


async def log_usage(api_key_prefix: str, model: str, operation: str,
                    tokens_input: int = 0, tokens_output: int = 0,
                    latency_ms: float = 0, success: bool = True):
    """Log API usage for analytics"""
    await execute_insert(
        """INSERT INTO usage_stats
           (api_key_prefix, model, operation, tokens_input, tokens_output,
            latency_ms, success, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (api_key_prefix, model, operation, tokens_input, tokens_output,
         latency_ms, 1 if success else 0, time.time())
    )