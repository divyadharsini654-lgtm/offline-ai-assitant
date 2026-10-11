"""
MAX Offline Voice-Based AI Assistant
Voice Activity Detection (VAD) Engine
"""

import numpy as np
from typing import Tuple


class VoiceActivityDetector:
    """
    Robust, zero-dependency adaptive Voice Activity Detector.
    Uses dynamic energy estimation, spectral variance, and adaptive noise floors
    to detect voice onset and silence termination without requiring external C libraries.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        base_energy_threshold: float = 0.015,
        silence_timeout: float = 1.2,
        min_speech_duration: float = 0.3,
    ):
        self.sample_rate = sample_rate
        self.base_energy_threshold = base_energy_threshold
        self.silence_timeout = silence_timeout
        self.min_speech_duration = min_speech_duration

        # Dynamic noise floor estimation
        self.noise_floor = 0.005
        self.alpha_noise = 0.95  # Exponential smoothing for background noise

        # State tracking
        self.speech_detected = False
        self.speech_duration = 0.0
        self.silence_duration = 0.0

    def reset(self):
        """Reset state for a new recording session."""
        self.speech_detected = False
        self.speech_duration = 0.0
        self.silence_duration = 0.0

    def compute_rms(self, audio_chunk: np.ndarray) -> float:
        """Compute Root Mean Square (RMS) energy of an audio chunk."""
        if len(audio_chunk) == 0:
            return 0.0
        # Convert to float32 if needed
        if audio_chunk.dtype != np.float32 and audio_chunk.dtype != np.float64:
            audio_chunk = audio_chunk.astype(np.float32) / 32768.0
        return float(np.sqrt(np.mean(np.square(audio_chunk))))

    def compute_zero_crossing_rate(self, audio_chunk: np.ndarray) -> float:
        """Calculate zero crossing rate to distinguish unvoiced speech from noise."""
        if len(audio_chunk) < 2:
            return 0.0
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_chunk)))) / 2.0
        return float(zero_crossings / len(audio_chunk))

    def process_chunk(self, chunk: np.ndarray) -> Tuple[bool, bool]:
        """
        Process an incoming audio buffer chunk.
        Returns:
            (is_current_speech, should_stop_recording)
        """
        chunk_duration = len(chunk) / self.sample_rate
        rms = self.compute_rms(chunk)
        zcr = self.compute_zero_crossing_rate(chunk)

        # Dynamic threshold adapts to ambient room noise
        adaptive_threshold = max(self.base_energy_threshold, self.noise_floor * 2.5)
        is_speech = rms > adaptive_threshold

        if is_speech:
            self.speech_detected = True
            self.speech_duration += chunk_duration
            self.silence_duration = 0.0
        else:
            # Update background noise estimate during silence
            if not self.speech_detected:
                self.noise_floor = (self.alpha_noise * self.noise_floor) + ((1 - self.alpha_noise) * rms)
            else:
                self.silence_duration += chunk_duration

        # Determine if speech is finished (user spoke, and has stopped for silence_timeout)
        should_stop = False
        if self.speech_detected and self.speech_duration >= self.min_speech_duration:
            if self.silence_duration >= self.silence_timeout:
                should_stop = True

        return is_speech, should_stop
