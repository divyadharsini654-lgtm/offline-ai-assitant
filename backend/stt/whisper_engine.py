"""
MAX Offline Voice-Based AI Assistant
Whisper Offline Speech-to-Text Engine (faster-whisper backend)
"""

import io
import logging
import threading
from pathlib import Path
from typing import Optional, Union, Dict, Any
import numpy as np
from backend.config import settings

logger = logging.getLogger(__name__)


class WhisperEngine:
    """
    Local speech-to-text engine using faster-whisper (CTranslate2 / ONNX).
    No PyTorch required. Pre-loads model into memory once for fast inference.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        language: Optional[str] = None,
        device: Optional[str] = None,
        download_root: Optional[Path] = None,
    ):
        self.model_name = model_name or settings.WHISPER_MODEL
        self.language = language or settings.WHISPER_LANGUAGE
        self.device = device or settings.WHISPER_DEVICE
        self.download_root = download_root or settings.WHISPER_MODEL_DIR
        self._model = None
        self._load_lock = threading.Lock()
        self._is_loading = False
        self._load_error: Optional[str] = None

    def load_model(self) -> bool:
        """Load Whisper model once at startup or on first call."""
        if self._model is not None:
            return True

        with self._load_lock:
            if self._model is not None:
                return True
            try:
                self._is_loading = True
                self._load_error = None
                logger.info(
                    f"Loading faster-whisper model '{self.model_name}' on '{self.device}'..."
                )
                self.download_root.mkdir(parents=True, exist_ok=True)

                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type="int8",           # low-memory quantised inference
                    download_root=str(self.download_root),
                )
                logger.info(
                    f"faster-whisper model '{self.model_name}' loaded successfully."
                )
                return True
            except Exception as e:
                self._load_error = str(e)
                logger.error(f"Failed to load faster-whisper '{self.model_name}': {e}")
                return False
            finally:
                self._is_loading = False

    def is_loaded(self) -> bool:
        return self._model is not None

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "language": self.language,
            "device": self.device,
            "loaded": self.is_loaded(),
            "loading": self._is_loading,
            "error": self._load_error,
            "model_dir": str(self.download_root),
            "backend": "faster-whisper",
        }

    def transcribe(
        self,
        audio_input: Union[np.ndarray, bytes, str, Path],
        sample_rate: int = 16000,
    ) -> Dict[str, Any]:
        """
        Transcribe audio offline with faster-whisper.
        Supports: np.ndarray (float32), bytes (WAV), str/Path (file).
        """
        if not self.is_loaded():
            success = self.load_model()
            if not success:
                return {
                    "text": "",
                    "language": self.language,
                    "duration": 0.0,
                    "success": False,
                    "error": f"Whisper model unavailable: {self._load_error}",
                }

        try:
            import soundfile as sf

            # Normalise input to float32 mono numpy array
            audio_data: np.ndarray
            if isinstance(audio_input, (str, Path)):
                audio_data, sr = sf.read(str(audio_input), dtype="float32")
                if audio_data.ndim > 1:
                    audio_data = np.mean(audio_data, axis=1)
            elif isinstance(audio_input, bytes):
                buf = io.BytesIO(audio_input)
                audio_data, sr = sf.read(buf, dtype="float32")
                if audio_data.ndim > 1:
                    audio_data = np.mean(audio_data, axis=1)
            elif isinstance(audio_input, np.ndarray):
                audio_data = audio_input.astype(np.float32)
                if audio_data.ndim > 1:
                    audio_data = np.mean(audio_data, axis=1)
                sr = sample_rate
            else:
                return {
                    "text": "",
                    "language": self.language,
                    "duration": 0.0,
                    "success": False,
                    "error": "Unsupported audio input type",
                }

            if len(audio_data) == 0:
                return {
                    "text": "",
                    "language": self.language,
                    "duration": 0.0,
                    "success": True,
                    "error": None,
                }

            duration = len(audio_data) / float(sr)

            # Reject pure silence quickly
            rms = float(np.sqrt(np.mean(np.square(audio_data))))
            if rms < 0.002:
                return {
                    "text": "",
                    "language": self.language,
                    "duration": duration,
                    "success": True,
                    "error": None,
                }

            # faster-whisper transcribe returns (segments_generator, info)
            lang = self.language if (self.language and self.language != "auto") else None
            segments, info = self._model.transcribe(
                audio_data,
                language=lang,
                beam_size=5,
            )

            text_parts = [seg.text for seg in segments]
            full_text = " ".join(text_parts).strip()

            return {
                "text": full_text,
                "language": info.language if hasattr(info, "language") else self.language,
                "duration": duration,
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return {
                "text": "",
                "language": self.language,
                "duration": 0.0,
                "success": False,
                "error": str(e),
            }


# Singleton engine instance
whisper_engine = WhisperEngine()
