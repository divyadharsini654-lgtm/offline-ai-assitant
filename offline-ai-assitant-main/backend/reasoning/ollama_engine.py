"""
MAX Offline Voice-Based AI Assistant
Ollama Modular Reasoning Engine
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional, Generator
import requests
from backend.config import settings
from backend.reasoning.engine import ReasoningEngine

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are MAX, a helpful, friendly, and intelligent offline AI voice assistant.
Respond concisely and naturally, ideal for spoken output.
Keep answers direct, informative, and avoid unnecessary preamble.
Do not output markdown code blocks or raw JSON unless explicitly requested by the user.
Never output hidden chain of thought or internal reasoning tags."""


class OllamaEngine(ReasoningEngine):
    """
    Adapter for local Ollama server running offline on the user's machine.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self.host = (host or settings.OLLAMA_HOST).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.temperature = temperature if temperature is not None else settings.REASONING_TEMPERATURE
        self.session = requests.Session()

    def is_available(self) -> bool:
        """Check if local Ollama daemon is active."""
        try:
            res = self.session.get(f"{self.host}/api/tags", timeout=1.5)
            return res.status_code == 200
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Check model availability and server status."""
        available = False
        models = []
        model_installed = False

        try:
            res = self.session.get(f"{self.host}/api/tags", timeout=1.5)
            if res.status_code == 200:
                available = True
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]
                model_installed = any(self.model in m for m in models)
        except Exception:
            pass

        return {
            "provider": "Ollama",
            "host": self.host,
            "target_model": self.model,
            "server_available": available,
            "model_installed": model_installed,
            "available_models": models,
        }

    def _strip_chain_of_thought(self, text: str) -> str:
        """Strip internal thinking/chain-of-thought blocks like <think>...</think>."""
        clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        clean = re.sub(r"\[thought\].*?\[/thought\]", "", clean, flags=re.DOTALL)
        return clean.strip()

    def generate_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate response via Ollama /api/chat."""
        messages = [{"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT}]

        if context:
            for msg in context:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        messages.append({"role": "user", "content": prompt})

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                },
            }
            res = self.session.post(f"{self.host}/api/chat", json=payload, timeout=30.0)
            if res.status_code == 200:
                data = res.json()
                content = data.get("message", {}).get("content", "")
                return self._strip_chain_of_thought(content)
            else:
                logger.warning(f"Ollama returned HTTP {res.status_code}: {res.text}")
                return f"Error from local Ollama: HTTP {res.status_code}"
        except Exception as e:
            logger.warning(f"Ollama connection error: {e}")
            raise ConnectionError(f"Cannot reach Ollama at {self.host}: {e}")

    def stream_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Stream tokens sequentially from Ollama."""
        messages = [{"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT}]
        if context:
            for msg in context:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": self.temperature},
        }

        try:
            with self.session.post(f"{self.host}/api/chat", json=payload, stream=True, timeout=30.0) as resp:
                if resp.status_code != 200:
                    yield f"Error from Ollama: HTTP {resp.status_code}"
                    return
                for line in resp.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
        except Exception as e:
            logger.error(f"Streaming error from Ollama: {e}")
            yield f"\n[Ollama connection lost: {e}]"

    def clear_context(self) -> None:
        """Stateless on client side (context managed via database/memory)."""
        pass
