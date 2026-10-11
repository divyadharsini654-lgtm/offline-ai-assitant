"""
MAX Offline Voice-Based AI Assistant
Command and Intent Detection
"""

import re
from enum import Enum
from typing import Tuple, Optional, Dict, Any


class IntentType(str, Enum):
    COMMAND = "command"
    CHAT = "chat"
    SYSTEM = "system"


class IntentDetector:
    """Classifies user speech into actionable commands or conversational queries."""

    # Patterns mapped to internal command actions
    COMMAND_PATTERNS = [
        (r"\b(what('s| is) the time|what time is it|current time|tell me the time)\b", "get_time"),
        (r"\b(what('s| is) (today's|the) date|what day is it|current date|today's date)\b", "get_date"),
        (r"\b(open|launch|start)\s+(calculator|calc)\b", "open_calculator"),
        (r"\b(open|launch|start)\s+(notepad|text editor)\b", "open_notepad"),
        (r"\b(open|launch|start)\s+(file explorer|explorer|files|my computer)\b", "open_explorer"),
        (r"\b(clear|reset)\s+(conversation|chat|history|messages)\b", "clear_conversation"),
        (r"\b(stop speaking|be quiet|shut up|silence|stop talking|cancel speech)\b", "stop_speaking"),
        (r"\b(tell me a joke|say something funny|joke)\b", "tell_joke"),
    ]

    def detect_intent(self, text: str) -> Tuple[IntentType, Optional[str], Dict[str, Any]]:
        """
        Analyze user text.
        Returns:
            (IntentType, action_name, metadata)
        """
        clean_text = text.strip().lower()

        for pattern, action in self.COMMAND_PATTERNS:
            if re.search(pattern, clean_text):
                return IntentType.COMMAND, action, {"matched_pattern": pattern, "query": text}

        return IntentType.CHAT, None, {"query": text}


intent_detector = IntentDetector()
