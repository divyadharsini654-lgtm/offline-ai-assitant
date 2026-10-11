"""
MAX Offline Voice-Based AI Assistant
Piper Local Offline Text-to-Speech Engine
"""

import io
import os
import wave
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
from backend.config import settings
from backend.audio.player import audio_player

logger = logging.getLogger(__name__)


class PiperEngine:
    """
    Offline Text-to-Speech engine supporting Piper ONNX neural voices
    with automated local pyttsx3 fallback.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ):
        self.model_path = Path(model_path or settings.PIPER_MODEL_PATH)
        self.config_path = Path(config_path or settings.PIPER_CONFIG_PATH)
        self._piper_voice = None
        self._load_lock = threading.Lock()
        self._pyttsx3_engine = None
        self._fallback_active = False

    def is_model_installed(self) -> bool:
        """Check if Piper ONNX model file exists on disk."""
        return self.model_path.exists() and self.model_path.stat().st_size > 1000

    def load_model(self) -> bool:
        """Load Piper ONNX voice model into memory."""
        if not self.is_model_installed():
            logger.info(f"Piper ONNX model not found at {self.model_path}. Using offline pyttsx3 fallback.")
            self._fallback_active = True
            return False

        with self._load_lock:
            try:
                # Try loading via piper-tts
                from piper import PiperVoice
                self._piper_voice = PiperVoice.load(
                    str(self.model_path),
                    config_path=str(self.config_path) if self.config_path.exists() else None,
                )
                self._fallback_active = False
                logger.info(f"Piper TTS voice successfully loaded from {self.model_path}")
                return True
            except Exception as e:
                logger.warning(f"Could not load Piper voice: {e}. Activating fallback.")
                self._fallback_active = True
                return False

    def _init_pyttsx3(self):
        """Initialize local pyttsx3 engine for fallback synthesis."""
        if self._pyttsx3_engine is None:
            try:
                import pyttsx3
                self._pyttsx3_engine = pyttsx3.init()
                self._pyttsx3_engine.setProperty("rate", 165)
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
                self._pyttsx3_engine = None

    def synthesize_wav_bytes(self, text: str) -> Optional[bytes]:
        """
        Synthesize text into offline WAV audio bytes.
        Prioritizes Piper ONNX neural synthesis; falls back to pyttsx3.
        """
        clean_text = text.strip()
        if not clean_text:
            return None

        # 1. Try Piper ONNX synthesis
        if not self._fallback_active and self._piper_voice is not None:
            try:
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, "wb") as wav_file:
                    self._piper_voice.synthesize(clean_text, wav_file)
                return wav_buffer.getvalue()
            except Exception as e:
                logger.warning(f"Piper synthesis error: {e}. Trying fallback.")

        # 2. Local Fallback via pyttsx3
        return self._synthesize_pyttsx3(clean_text)

    def _synthesize_pyttsx3(self, text: str) -> Optional[bytes]:
        """Synthesize WAV audio using local pyttsx3 engine."""
        import tempfile
        try:
            import pyttsx3
            # In multi-threaded environments, creating a fresh engine instance avoids COM threading deadlocks on Windows
            engine = pyttsx3.init()
            engine.setProperty("rate", 170)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                temp_wav_path = tf.name

            engine.save_to_file(text, temp_wav_path)
            engine.runAndWait()

            with open(temp_wav_path, "rb") as f:
                wav_bytes = f.read()

            try:
                os.remove(temp_wav_path)
            except Exception:
                pass

            return wav_bytes
        except Exception as e:
            logger.error(f"Fallback pyttsx3 synthesis error: {e}")
            return self._generate_tone_speech_fallback()

    def _generate_tone_speech_fallback(self) -> bytes:
        """Ultimate safety fallback: generate a brief notification chime WAV."""
        sample_rate = 16000
        duration = 0.4
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        # Soft chime frequencies: 523Hz (C5) and 659Hz (E5)
        tone = (0.3 * np.sin(2 * np.pi * 523.25 * t) + 0.3 * np.sin(2 * np.pi * 659.25 * t))
        audio = (tone * 32767).astype(np.int16)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())
        return buffer.getvalue()

    def speak(self, text: str, blocking: bool = False) -> bool:
        """Synthesize text and play immediately through system audio."""
        wav_bytes = self.synthesize_wav_bytes(text)
        if wav_bytes:
            return audio_player.play_wav_bytes(wav_bytes, blocking=blocking)
        return False

    def stop(self):
        """Immediately stop speaking."""
        audio_player.stop()

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_path": str(self.model_path),
            "model_installed": self.is_model_installed(),
            "using_fallback": self._fallback_active or not self.is_model_installed(),
            "active_engine": "Piper ONNX" if (self._piper_voice and not self._fallback_active) else "pyttsx3 Local Fallback",
        }


piper_engine = PiperEngine()
