"""
MAX Offline Voice-Based AI Assistant
Configuration Management
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    # General Application
    APP_NAME: str = os.getenv("APP_NAME", "MAX")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Project Directories
    ROOT_DIR: Path = PROJECT_ROOT
    BACKEND_DIR: Path = PROJECT_ROOT / "backend"
    FRONTEND_DIR: Path = PROJECT_ROOT / "frontend"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    DATA_DIR: Path = PROJECT_ROOT / "data"

    # Whisper Speech-to-Text
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_LANGUAGE: str = os.getenv("WHISPER_LANGUAGE", "en")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_MODEL_DIR: Path = field(
        default_factory=lambda: PROJECT_ROOT / "models" / "whisper"
    )

    # Piper Text-to-Speech
    PIPER_MODEL_PATH: Path = field(
        default_factory=lambda: PROJECT_ROOT / "models" / "piper" / "voice.onnx"
    )
    PIPER_CONFIG_PATH: Path = field(
        default_factory=lambda: PROJECT_ROOT / "models" / "piper" / "voice.onnx.json"
    )
    PIPER_VOICE_NAME: str = os.getenv("PIPER_VOICE_NAME", "en_US-lessac-medium")

    # Reasoning / Local LLM
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    REASONING_TEMPERATURE: float = float(os.getenv("REASONING_TEMPERATURE", "0.7"))
    CONTEXT_WINDOW_MESSAGES: int = int(os.getenv("CONTEXT_WINDOW_MESSAGES", "20"))

    # Audio Engine & VAD
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "1"))
    AUDIO_CHUNK_SIZE: int = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
    VAD_ENERGY_THRESHOLD: float = float(os.getenv("VAD_ENERGY_THRESHOLD", "0.015"))
    VAD_SILENCE_TIMEOUT: float = float(os.getenv("VAD_SILENCE_TIMEOUT", "1.2"))
    VAD_SPEECH_PADDING: float = float(os.getenv("VAD_SPEECH_PADDING", "0.3"))

    # Wake Word
    WAKE_WORD: str = os.getenv("WAKE_WORD", "hey max")
    WAKE_WORD_ENABLED: bool = os.getenv("WAKE_WORD_ENABLED", "false").lower() in ("true", "1", "yes")

    # Storage
    DATABASE_PATH: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / "max.db"
    )

    def __post_init__(self):
        # Ensure directories exist
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.WHISPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        (self.MODELS_DIR / "piper").mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
