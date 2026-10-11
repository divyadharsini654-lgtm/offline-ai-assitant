"""
MAX Offline Voice-Based AI Assistant
Context & Conversation State Management
"""
import logging
from typing import List, Dict, Optional
from backend.config import settings
from backend.memory.database import memory_db
logger = logging.getLogger(__name__)
class ContextManager:
    """Maintains multi-turn context and prepares conversation state for reasoning engines."""

    def __init__(self, max_history: Optional[int] = None):
        self.max_history = max_history or settings.CONTEXT_WINDOW_MESSAGES

    def get_context(self, conversation_id: str = "default") -> List[Dict[str, str]]:
        """Retrieve recent conversation turns for reasoning context."""
        try:
            return memory_db.get_recent_context(conversation_id, max_messages=self.max_history)
        except Exception as e:
            logger.error(f"Error fetching context: {e}")
            return []

    def save_turn(self, conversation_id: str, user_text: str, assistant_text: str):
        """Persist a conversation turn into SQLite memory."""
        try:
            memory_db.add_message(conversation_id, "user", user_text)
            memory_db.add_message(conversation_id, "assistant", assistant_text)
        except Exception as e:
            logger.error(f"Error persisting turn to memory: {e}")

    def clear(self, conversation_id: str = "default"):
        """Clear context for a conversation."""
        try:
            memory_db.clear_conversation(conversation_id)
        except Exception as e:
            logger.error(f"Error clearing conversation context: {e}")


context_manager = ContextManager()
