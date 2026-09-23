"""
MAX AI Interview Preparation Assistant
Interview Engine Orchestrator
"""

import logging
from typing import List, Dict, Any, Optional

from backend.reasoning.engine import ReasoningEngine
from backend.reasoning.prompts import (
    build_system_prompt,
    build_mock_start_prompt,
    build_mock_eval_prompt,
)
from backend.reasoning.ai_provider import create_provider_manager_from_settings
from backend.reasoning.fallback_engine import FallbackEngine
from backend.reasoning.project_knowledge import project_knowledge

logger = logging.getLogger(__name__)


class InterviewEngine(ReasoningEngine):
    """
    Central orchestrator for the MAX AI Interview Assistant.
    Builds context-aware prompts and routes to the active AI provider or Smart Fallback Engine.
    """

    def __init__(self):
        self.provider_manager = create_provider_manager_from_settings()
        self.fallback = FallbackEngine()
        self._mock_active: Dict[str, bool] = {}

    def is_available(self) -> bool:
        provider = self.provider_manager.get_active_provider()
        return provider is not None or self.fallback.is_available()

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the reasoning engine and all providers."""
        status = self.provider_manager.get_status()
        active = status.get("active_provider", "None")
        is_llm = active != "None"

        return {
            "provider": "MAX AI Reasoning Engine",
            "server_available": True,
            "target_model": active if is_llm else "Smart Offline Engine",
            "model_installed": True,
            "providers_status": status,
            "note": "Ready for dynamic AI interview generation." if is_llm else "Smart Offline Reasoning Engine Active (100% Offline Privacy).",
        }

    def clear_context(self) -> None:
        self._mock_active.clear()
        self.fallback.clear_context()

    def generate_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        interview_mode: str = "general",
        language: str = "auto",
        is_mock_start: bool = False,
        conversation_id: str = "default",
        project_id: Optional[str] = None,
    ) -> str:
        """
        Generate response dynamically via active AI providers or Smart Fallback.
        """
        p_clean = prompt.strip().lower()

        # Check for project context integration
        project_context_str = ""
        if any(k in p_clean for k in ["project", "payroll", "smart helmet"]):
            proj_data = project_knowledge.get_project(project_id or "") or project_knowledge.match_project_query(prompt)
            if proj_data:
                project_context_str = f"\n\nCandidate Project Profile Context:\nTitle: {proj_data.get('title')}\nOverview: {proj_data.get('overview')}\nTechnologies: {proj_data.get('technologies')}\nFeatures: {proj_data.get('key_features')}\nRole: {proj_data.get('role')}\n"

        # Reset mock active if mode is not mock and user is not explicitly asking to start a mock session
        is_mock_trigger = any(k in p_clean for k in ["start mock interview", "mock interview", "take my interview"])
        if interview_mode != "mock" and not is_mock_trigger:
            self._mock_active[conversation_id] = False

        provider = self.provider_manager.get_active_provider()

        # Fallback to local offline engine if no external/Ollama provider is ready
        if not provider:
            logger.info("Using Smart Offline Reasoning Engine for response generation.")
            return self.fallback.generate_response(
                prompt=prompt,
                context=context,
                system_prompt=system_prompt,
                conversation_id=conversation_id,
                interview_mode=interview_mode,
            )

        # 1. Start a Mock Interview Session
        if is_mock_start or is_mock_trigger:
            self._mock_active[conversation_id] = True
            mock_sys_prompt = build_system_prompt(mode="mock", language=language) + project_context_str
            mock_start_msg = build_mock_start_prompt(mode=interview_mode)

            try:
                response = provider.generate(
                    prompt=mock_start_msg,
                    context=[],
                    system_prompt=mock_sys_prompt,
                )
                return response
            except Exception as e:
                logger.error(f"Mock start failed on provider: {e}")
                return self.fallback.generate_response(prompt, context, conversation_id=conversation_id, interview_mode=interview_mode)

        # 2. Continue Mock Interview Evaluation
        if (interview_mode == "mock" or self._mock_active.get(conversation_id, False)) and not any(k in p_clean for k in ["what is", "explain", "how to", "tell me about"]):
            if p_clean in ["stop mock", "end interview", "stop interview", "exit mock"]:
                self._mock_active[conversation_id] = False
                return "Mock interview session ended. Excellent practice! Feel free to ask any other questions."

            mock_sys_prompt = build_system_prompt(mode="mock", language=language) + project_context_str
            eval_prompt = f"User's answer:\n\n{prompt}\n\n{build_mock_eval_prompt()}"

            try:
                response = provider.generate(
                    prompt=eval_prompt,
                    context=context,
                    system_prompt=mock_sys_prompt,
                )
                return response
            except Exception as e:
                logger.error(f"Mock evaluation failed on provider: {e}")
                return self.fallback.generate_response(prompt, context, conversation_id=conversation_id, interview_mode=interview_mode)

        # 3. Standard Dynamic Q&A Generation
        sys_prompt = (system_prompt or build_system_prompt(mode=interview_mode, language=language)) + project_context_str

        try:
            response = provider.generate(
                prompt=prompt,
                context=context,
                system_prompt=sys_prompt,
            )
            return response
        except Exception as e:
            logger.error(f"Provider generation failed: {e}. Falling back to smart offline engine.")
            return self.fallback.generate_response(prompt, context, conversation_id=conversation_id)

    def stream_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ):
        yield self.generate_response(prompt, context, system_prompt)


interview_engine = InterviewEngine()
