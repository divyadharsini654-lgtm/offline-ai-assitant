"""
MAX Offline Voice-Based AI Assistant
Audio Playback Engine
"""

import io
import logging
import threading
from typing import Optional
import numpy as np
import soundfile as sf
from backend.audio.microphone import SD_AVAILABLE

logger = logging.getLogger(__name__)

if SD_AVAILABLE:
    import sounddevice as sd


class AudioPlayer:
    """Handles audio playback through system speakers with interruption control."""

    def __init__(self):
        self.is_playing = False
        self._current_stream = None
        self._stop_requested = threading.Event()

    def play_wav_bytes(self, wav_bytes: bytes, blocking: bool = False) -> bool:
        """Play WAV audio data through sounddevice."""
        if not SD_AVAILABLE:
            logger.warning("Audio playback unavailable: sounddevice not loaded.")
            return False

        try:
            self.stop()  # Stop any previous speech
            self._stop_requested.clear()
            self.is_playing = True

            buffer = io.BytesIO(wav_bytes)
            data, sample_rate = sf.read(buffer, dtype="float32")

            def _play_worker():
                try:
                    sd.play(data, samplerate=sample_rate)
                    sd.wait()
                except Exception as e:
                    logger.error(f"Playback error in worker: {e}")
                finally:
                    self.is_playing = False

            thread = threading.Thread(target=_play_worker, daemon=True)
            thread.start()

            if blocking:
                thread.join()

            return True
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            self.is_playing = False
            return False

    def play_numpy(self, audio_data: np.ndarray, sample_rate: int = 22050, blocking: bool = False) -> bool:
        """Play numpy float array directly."""
        if not SD_AVAILABLE:
            return False
        try:
            self.stop()
            self._stop_requested.clear()
            self.is_playing = True

            def _play_worker():
                try:
                    sd.play(audio_data, samplerate=sample_rate)
                    sd.wait()
                except Exception as e:
                    logger.error(f"Playback error: {e}")
                finally:
                    self.is_playing = False

            thread = threading.Thread(target=_play_worker, daemon=True)
            thread.start()
            if blocking:
                thread.join()
            return True
        except Exception as e:
            logger.error(f"Failed to play numpy audio: {e}")
            self.is_playing = False
            return False

    def stop(self):
        """Immediately abort speech playback."""
        if SD_AVAILABLE:
            try:
                sd.stop()
            except Exception as e:
                logger.debug(f"Error calling sd.stop: {e}")
        self.is_playing = False
        self._stop_requested.set()


audio_player = AudioPlayer()
