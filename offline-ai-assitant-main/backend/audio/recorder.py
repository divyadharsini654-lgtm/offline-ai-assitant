"""
MAX Offline Voice-Based AI Assistant
Audio Recorder with VAD Integration
"""

import io
import time
import logging
import threading
from typing import Optional, Callable, Tuple
import numpy as np
import soundfile as sf
from backend.config import settings
from backend.audio.vad import VoiceActivityDetector
from backend.audio.microphone import SD_AVAILABLE

logger = logging.getLogger(__name__)

if SD_AVAILABLE:
    import sounddevice as sd


class AudioRecorder:
    """Captures microphone audio, applies VAD, and buffers speech data."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.vad = VoiceActivityDetector(
            sample_rate=sample_rate,
            base_energy_threshold=settings.VAD_ENERGY_THRESHOLD,
            silence_timeout=settings.VAD_SILENCE_TIMEOUT,
        )
        self.is_recording = False
        self._stop_event = threading.Event()

    def record_speech_segment(
        self,
        max_duration: float = 15.0,
        on_chunk: Optional[Callable[[float, bool], None]] = None,
    ) -> Optional[np.ndarray]:
        """
        Record audio from the local microphone until silence is detected by VAD
        or max_duration is reached.
        Returns:
            np.ndarray of shape (N,) float32 audio samples, or None on failure/empty speech.
        """
        if not SD_AVAILABLE:
            logger.warning("Audio input unavailable: sounddevice not loaded.")
            return None

        self.vad.reset()
        self._stop_event.clear()
        self.is_recording = True
        audio_buffer = []

        chunk_size = settings.AUDIO_CHUNK_SIZE

        def callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"Audio input status: {status}")
            chunk = indata[:, 0].copy()  # Mono channel
            audio_buffer.append(chunk)

            is_speech, should_stop = self.vad.process_chunk(chunk)
            rms = self.vad.compute_rms(chunk)
            if on_chunk:
                on_chunk(rms, is_speech)

            if should_stop:
                self._stop_event.set()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=chunk_size,
                callback=callback,
            ):
                start_time = time.time()
                while not self._stop_event.is_set():
                    time.sleep(0.05)
                    if (time.time() - start_time) > max_duration:
                        logger.info("Max recording duration reached.")
                        break
        except Exception as e:
            logger.error(f"Recording error: {e}")
            return None
        finally:
            self.is_recording = False

        if not audio_buffer or not self.vad.speech_detected:
            logger.info("No speech detected during recording session.")
            return None

        recorded_audio = np.concatenate(audio_buffer, axis=0)
        return recorded_audio

    def stop(self):
        """Immediately stop recording."""
        self._stop_event.set()
        self.is_recording = False

    @staticmethod
    def audio_to_wav_bytes(audio_array: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Encode float32 numpy array into standard 16-bit PCM WAV bytes."""
        buffer = io.BytesIO()
        sf.write(buffer, audio_array, sample_rate, format="WAV", subtype="PCM_16")
        return buffer.getvalue()

    @staticmethod
    def wav_bytes_to_audio(wav_bytes: bytes) -> Tuple[np.ndarray, int]:
        """Decode WAV bytes into float32 numpy array and sample rate."""
        buffer = io.BytesIO(wav_bytes)
        data, sr = sf.read(buffer, dtype="float32")
        if data.ndim > 1:
            data = np.mean(data, axis=1)  # Convert to mono
        return data, sr
