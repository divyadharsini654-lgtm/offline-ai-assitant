"""
MAX Offline Voice-Based AI Assistant
Reasoning Engine Abstraction
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, Generator


class ReasoningEngine(ABC):
    """
    Abstract interface for local reasoning engines.
    Allows swappable LLM adapters (Ollama, llama.cpp, local offline engines).
    """

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a complete text response synchronously."""
        pass

    @abstractmethod
    def stream_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Stream response tokens sequentially."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend engine service is reachable and ready."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the reasoning engine."""
        pass

    @abstractmethod
    def clear_context(self) -> None:
        """Reset conversation context within the engine."""
        pass
