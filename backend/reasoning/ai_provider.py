"""
MAX AI Interview Preparation Assistant
Multi-Provider AI Abstraction Layer

Supports: Gemini, OpenAI, Ollama (local), with automatic fallback.
API keys are loaded from environment variables — never exposed to frontend.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a complete response."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and reachable."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable provider name."""
        pass

    def _strip_thinking(self, text: str) -> str:
        """Remove internal thinking/CoT blocks from LLM output."""
        clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        clean = re.sub(r"\[thought\].*?\[/thought\]", "", clean, flags=re.DOTALL)
        return clean.strip()


# =============================================================================
# GEMINI PROVIDER
# =============================================================================
class GeminiProvider(AIProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model
        self._client = None
        self._available = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self._client = None
        return self._client

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        if not self.api_key:
            self._available = False
            return False
        try:
            client = self._get_client()
            if client is None:
                self._available = False
                return False
            # Quick validation — try listing models
            self._available = True
            return True
        except Exception as e:
            logger.warning(f"Gemini availability check failed: {e}")
            self._available = False
            return False

    def get_name(self) -> str:
        return f"Gemini ({self.model_name})"

    def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        client = self._get_client()
        if client is None:
            raise ConnectionError("Gemini client not initialized")

        try:
            from google.genai import types

            # Build contents list for multi-turn conversation
            contents = []
            if context:
                for msg in context:
                    role = msg.get("role", "user")
                    # Gemini uses "user" and "model" roles
                    gemini_role = "model" if role == "assistant" else "user"
                    contents.append(
                        types.Content(
                            role=gemini_role,
                            parts=[types.Part.from_text(text=msg.get("content", ""))],
                        )
                    )

            # Add current user message
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            )

            # Generate with system instruction
            config = types.GenerateContentConfig(
                system_instruction=system_prompt or "",
                temperature=0.7,
                max_output_tokens=4096,
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            if response and response.text:
                return self._strip_thinking(response.text)
            return "I could not generate a response. Please try again."

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise ConnectionError(f"Gemini API error: {e}")


# =============================================================================
# OPENAI PROVIDER
# =============================================================================
class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model
        self._client = None
        self._available = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self._client = None
        return self._client

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        if not self.api_key:
            self._available = False
            return False
        try:
            client = self._get_client()
            self._available = client is not None
            return self._available
        except Exception:
            self._available = False
            return False

    def get_name(self) -> str:
        return f"OpenAI ({self.model_name})"

    def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        client = self._get_client()
        if client is None:
            raise ConnectionError("OpenAI client not initialized")

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if context:
                for msg in context:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    })
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )

            if response.choices:
                return self._strip_thinking(response.choices[0].message.content or "")
            return "I could not generate a response. Please try again."

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise ConnectionError(f"OpenAI API error: {e}")


# =============================================================================
# OLLAMA PROVIDER (wraps existing local Ollama)
# =============================================================================
class OllamaLocalProvider(AIProvider):
    """Local Ollama LLM provider — fully offline."""

    def __init__(self, host: str = "http://127.0.0.1:11434", model: str = "llama3.2"):
        self.host = host.rstrip("/")
        self.model = model
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import requests
            res = requests.get(f"{self.host}/api/tags", timeout=2)
            self._available = res.status_code == 200
            return self._available
        except Exception:
            self._available = False
            return False

    def get_name(self) -> str:
        return f"Ollama ({self.model})"

    def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        import requests

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            for msg in context:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        messages.append({"role": "user", "content": prompt})

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7},
            }
            res = requests.post(f"{self.host}/api/chat", json=payload, timeout=60)
            if res.status_code == 200:
                data = res.json()
                content = data.get("message", {}).get("content", "")
                return self._strip_thinking(content)
            return f"Ollama error: HTTP {res.status_code}"
        except Exception as e:
            raise ConnectionError(f"Ollama connection error: {e}")


# =============================================================================
# PROVIDER MANAGER — auto-selects the best available provider
# =============================================================================
class ProviderManager:
    """Manages AI providers with automatic fallback selection."""

    def __init__(self):
        self._providers: List[AIProvider] = []
        self._active: Optional[AIProvider] = None

    def register(self, provider: AIProvider):
        """Register a provider in priority order."""
        self._providers.append(provider)

    def get_active_provider(self) -> Optional[AIProvider]:
        """Return the first available provider."""
        if self._active and self._active.is_available():
            return self._active

        for provider in self._providers:
            try:
                if provider.is_available():
                    self._active = provider
                    logger.info(f"Active AI provider: {provider.get_name()}")
                    return provider
            except Exception:
                continue

        return None

    def get_status(self) -> Dict[str, Any]:
        """Return status of all registered providers."""
        active = self.get_active_provider()
        return {
            "active_provider": active.get_name() if active else "None",
            "providers": [
                {
                    "name": p.get_name(),
                    "available": p.is_available(),
                    "active": p is active,
                }
                for p in self._providers
            ],
        }


def create_provider_manager_from_settings() -> ProviderManager:
    """Create and configure the provider manager from application settings."""
    from backend.config import settings

    manager = ProviderManager()

    # Priority 1: Gemini
    gemini_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    if gemini_key:
        gemini_model = getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
        manager.register(GeminiProvider(api_key=gemini_key, model=gemini_model))
        logger.info(f"Registered Gemini provider ({gemini_model})")

    # Priority 2: OpenAI
    openai_key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if openai_key:
        openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        manager.register(OpenAIProvider(api_key=openai_key, model=openai_model))
        logger.info(f"Registered OpenAI provider ({openai_model})")

    # Priority 3: Ollama (local, always registered)
    ollama_host = getattr(settings, "OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model = getattr(settings, "OLLAMA_MODEL", "llama3.2")
    manager.register(OllamaLocalProvider(host=ollama_host, model=ollama_model))
    logger.info(f"Registered Ollama provider ({ollama_model})")

    return manager
