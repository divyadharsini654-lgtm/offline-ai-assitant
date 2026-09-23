"""
MAX Offline Voice-Based AI Assistant
REST API Routes
"""

import base64
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from pydantic import BaseModel, Field

from backend.config import settings
from backend.audio.microphone import microphone_manager
from backend.audio.player import audio_player
from backend.stt.whisper_engine import whisper_engine
from backend.tts.piper_engine import piper_engine
from backend.reasoning.intent import intent_detector, IntentType
from backend.commands.command_handler import command_handler
from backend.reasoning.interview_engine import interview_engine
from backend.reasoning.project_knowledge import project_knowledge
from backend.reasoning.context import context_manager
from backend.memory.database import memory_db
from backend.mojo.bridge import mojo_bridge
from backend.api.websocket import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def get_active_reasoning_engine():
    """Returns the unified AI Interview reasoning engine."""
    return interview_engine


# Pydantic Request Models
class ChatRequest(BaseModel):
    text: str = Field(..., description="User voice transcription or text message")
    conversation_id: Optional[str] = Field("default", description="Conversation thread ID")
    speak: Optional[bool] = Field(True, description="Whether to synthesize speech for the response")
    mode: Optional[str] = Field("general", description="Interview mode: general, technical, coding, sql, hr, project, mock, aptitude")
    language: Optional[str] = Field("auto", description="Language preference: auto, english, tamil, tanglish")
    project_id: Optional[str] = Field(None, description="Active project profile ID")


class CommandRequest(BaseModel):
    action: str = Field(..., description="Action name to execute from allowlist")
    conversation_id: Optional[str] = Field("default")


class SpeakRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")


class SettingsUpdateRequest(BaseModel):
    whisper_model: Optional[str] = None
    whisper_language: Optional[str] = None
    ollama_model: Optional[str] = None
    wake_word_enabled: Optional[bool] = None


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "mode": "offline",
        "privacy": "local-only",
    }


@router.get("/status")
def system_status():
    """Comprehensive diagnostic status of all assistant sub-systems."""
    active_engine = get_active_reasoning_engine()
    return {
        "offline_mode": True,
        "app_name": settings.APP_NAME,
        "microphone": microphone_manager.check_health(),
        "whisper": whisper_engine.get_status(),
        "tts": piper_engine.get_status(),
        "reasoning": active_engine.get_status(),
        "mojo": mojo_bridge.get_status(),
        "database": {
            "path": str(settings.DATABASE_PATH),
            "exists": settings.DATABASE_PATH.exists(),
        },
        "wake_word": {
            "word": settings.WAKE_WORD,
            "enabled": settings.WAKE_WORD_ENABLED,
        },
    }


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accept an uploaded audio recording (WAV/WebM/PCM) and transcribe it offline with Whisper.
    """
    try:
        await ws_manager.broadcast_state("TRANSCRIBING", "Understanding your voice...")
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio payload received")

        result = whisper_engine.transcribe(audio_bytes)
        await ws_manager.broadcast_state("IDLE", "Ready")
        return result
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        await ws_manager.broadcast_state("ERROR", "Transcription failed")
        return {
            "text": "",
            "language": settings.WHISPER_LANGUAGE,
            "duration": 0.0,
            "success": False,
            "error": str(e),
        }


@router.post("/chat")
async def process_chat(req: ChatRequest):
    """
    Core conversational and voice processing pipeline:
    1. Detect intent (command vs chat query)
    2. Route to command handler or reasoning engine
    3. Persist multi-turn context in SQLite
    4. Synthesize voice response offline with Piper
    """
    user_text = req.text.strip()
    if not user_text:
        return {"response": "", "audio_base64": None, "action": None}

    conv_id = req.conversation_id or "default"
    memory_db.get_or_create_conversation(conv_id)

    # 1. Intent Detection
    intent_type, action, _ = intent_detector.detect_intent(user_text)

    response_text = ""
    audio_base64 = None

    if intent_type == IntentType.COMMAND and action:
        # Execute safe allowlisted local command
        await ws_manager.broadcast_state("THINKING", "Executing command...")
        cmd_result = command_handler.execute_command(action, conversation_id=conv_id)
        response_text = cmd_result.get("message", "")
        should_speak = cmd_result.get("should_speak", True)
    else:
        # Conversational reasoning via Interview Engine
        await ws_manager.broadcast_state("THINKING", "Thinking...")
        recent_context = context_manager.get_context(conv_id)
        response_text = interview_engine.generate_response(
            user_text,
            context=recent_context,
            interview_mode=req.mode or "general",
            language=req.language or "auto",
            conversation_id=conv_id,
            project_id=req.project_id,
        )
        should_speak = True

    # 2. Persist turn in memory
    context_manager.save_turn(conv_id, user_text, response_text)

    # 3. Text-to-Speech Synthesis
    if req.speak and should_speak and response_text:
        await ws_manager.broadcast_state("SPEAKING", "MAX is speaking...")
        wav_bytes = piper_engine.synthesize_wav_bytes(response_text)
        if wav_bytes:
            audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

    await ws_manager.broadcast_state("IDLE", "Ready")

    return {
        "response": response_text,
        "action": action,
        "audio_base64": audio_base64,
        "conversation_id": conv_id,
    }


@router.get("/projects")
def get_projects():
    """Return available project profiles for interview preparation."""
    return {"projects": project_knowledge.list_projects()}


@router.post("/speak")
def synthesize_speech(req: SpeakRequest):
    """Generate offline audio/wav binary stream for direct browser or client playback."""
    wav_bytes = piper_engine.synthesize_wav_bytes(req.text)
    if not wav_bytes:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")
    return Response(content=wav_bytes, media_type="audio/wav")


@router.post("/command")
def execute_command_api(req: CommandRequest):
    """Directly trigger an allowlisted command."""
    return command_handler.execute_command(req.action, conversation_id=req.conversation_id or "default")


@router.get("/conversations")
def get_conversations(conversation_id: Optional[str] = "default"):
    """Retrieve message history for a conversation or list all threads."""
    messages = memory_db.get_messages(conversation_id, limit=100)
    all_conversations = memory_db.list_conversations()
    return {
        "active_id": conversation_id,
        "messages": messages,
        "conversations": all_conversations,
    }


@router.delete("/conversations")
def clear_conversations(conversation_id: Optional[str] = "default"):
    """Clear conversation history."""
    if conversation_id:
        memory_db.clear_conversation(conversation_id)
        return {"status": "cleared", "conversation_id": conversation_id}
    else:
        memory_db.delete_all_conversations()
        return {"status": "cleared_all"}


@router.post("/stop")
def stop_speaking():
    """Stop active audio playback immediately."""
    piper_engine.stop()
    audio_player.stop()
    return {"status": "stopped"}


@router.get("/settings")
def get_settings():
    """Return runtime configuration."""
    return {
        "app_name": settings.APP_NAME,
        "whisper_model": settings.WHISPER_MODEL,
        "whisper_language": settings.WHISPER_LANGUAGE,
        "ollama_host": settings.OLLAMA_HOST,
        "ollama_model": settings.OLLAMA_MODEL,
        "piper_model_path": str(settings.PIPER_MODEL_PATH),
        "wake_word": settings.WAKE_WORD,
        "wake_word_enabled": settings.WAKE_WORD_ENABLED,
    }


@router.post("/settings")
def update_settings(req: SettingsUpdateRequest):
    """Update runtime configuration without restarting server."""
    if req.whisper_model:
        settings.WHISPER_MODEL = req.whisper_model
        whisper_engine.model_name = req.whisper_model
    if req.whisper_language:
        settings.WHISPER_LANGUAGE = req.whisper_language
        whisper_engine.language = req.whisper_language
    if req.ollama_model:
        settings.OLLAMA_MODEL = req.ollama_model
        ollama_engine.model = req.ollama_model
    if req.wake_word_enabled is not None:
        settings.WAKE_WORD_ENABLED = req.wake_word_enabled

    return {"status": "updated", "settings": get_settings()}
