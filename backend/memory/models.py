"""
MAX Offline Voice-Based AI Assistant
Memory & Conversation Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json


@dataclass
class Message:
    id: Optional[int] = None
    conversation_id: str = "default"
    role: str = "user"  # "user", "assistant", "system"
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Message":
        # row: (id, conversation_id, role, content, timestamp, metadata_json)
        meta = {}
        if len(row) > 5 and row[5]:
            try:
                meta = json.loads(row[5])
            except Exception:
                meta = {}
        return cls(
            id=row[0],
            conversation_id=row[1],
            role=row[2],
            content=row[3],
            timestamp=row[4],
            metadata=meta,
        )


@dataclass
class Conversation:
    id: str
    title: str = "New Conversation"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
