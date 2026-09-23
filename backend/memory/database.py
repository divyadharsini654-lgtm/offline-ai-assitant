"""
MAX Offline Voice-Based AI Assistant
SQLite Memory Database
"""

import sqlite3
import json
import uuid
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from backend.config import settings
from backend.memory.models import Message, Conversation


class MemoryDatabase:
    """Thread-safe SQLite storage for conversation persistence."""

    def __init__(self, db_path: Optional[Union[Path, str]] = None):
        if str(db_path) == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = Path(db_path or settings.DATABASE_PATH)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Create schema with proper constraints and indexes."""
        with self._lock:
            cursor = self._conn.cursor()
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)

            # Indexes for low-latency retrieval
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conv_time 
                ON messages (conversation_id, id ASC)
            """)
            self._conn.commit()

        # Ensure default conversation
        self.get_or_create_conversation("default", "Primary Conversation")

    def get_or_create_conversation(self, conv_id: Optional[str] = None, title: str = "Voice Chat") -> str:
        with self._lock:
            cursor = self._conn.cursor()
            if conv_id:
                cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
                row = cursor.fetchone()
                if row:
                    return row["id"]

            new_id = conv_id or str(uuid.uuid4())[:8]
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT OR IGNORE INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (new_id, title, now, now))
            self._conn.commit()
            return new_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to the conversation."""
        now = datetime.now(timezone.utc).isoformat()
        meta_str = json.dumps(metadata or {})

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                UPDATE conversations SET updated_at = ? WHERE id = ?
            """, (now, conversation_id))

            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content, timestamp, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, role, content, now, meta_str))
            msg_id = cursor.lastrowid
            self._conn.commit()

            return Message(
                id=msg_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                timestamp=now,
                metadata=metadata or {},
            )

    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch chronological message history for a conversation."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT id, conversation_id, role, content, timestamp, metadata_json
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id ASC
                LIMIT ?
            """, (conversation_id, limit))
            rows = cursor.fetchall()

            messages = []
            for r in rows:
                meta = {}
                if r["metadata_json"]:
                    try:
                        meta = json.loads(r["metadata_json"])
                    except Exception:
                        pass
                messages.append({
                    "id": r["id"],
                    "conversation_id": r["conversation_id"],
                    "role": r["role"],
                    "content": r["content"],
                    "timestamp": r["timestamp"],
                    "metadata": meta,
                })
            return messages

    def get_recent_context(self, conversation_id: str, max_messages: int = 6) -> List[Dict[str, str]]:
        """Return the last N messages formatted as [role, content] pairs for LLM context."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (conversation_id, max_messages))
            rows = cursor.fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations ordered by recent update."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT c.id, c.title, c.created_at, c.updated_at,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def clear_conversation(self, conversation_id: str):
        """Delete all messages inside a specific conversation."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            self._conn.commit()

    def delete_conversation(self, conversation_id: str):
        """Delete an entire conversation and all its messages."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            self._conn.commit()

    def delete_all_conversations(self):
        """Clear everything."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM conversations")
            self._conn.commit()

    def close(self):
        """Close connection cleanly."""
        with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass


# Singleton instance
memory_db = MemoryDatabase()
