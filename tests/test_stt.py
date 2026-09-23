"""
Unit Tests for MAX Speech-to-Text (WhisperEngine - faster-whisper backend)
"""

import numpy as np
import pytest
from backend.stt.whisper_engine import WhisperEngine


def test_whisper_engine_initialization():
    engine = WhisperEngine(model_name="tiny", language="en", device="cpu")
    status = engine.get_status()
    assert status["model_name"] == "tiny"
    assert status["language"] == "en"
    assert status["device"] == "cpu"
    assert status["loaded"] is False
    assert status["backend"] == "faster-whisper"


def test_whisper_empty_audio_handling():
    engine = WhisperEngine(model_name="tiny", language="en", device="cpu")
    empty_audio = np.array([], dtype=np.float32)

    class MockSegment:
        text = ""

    class MockInfo:
        language = "en"

    class MockModel:
        def transcribe(self, audio, **kwargs):
            return [], MockInfo()

    engine._model = MockModel()
    res = engine.transcribe(empty_audio)
    assert res["success"] is True
    assert res["text"] == ""


def test_whisper_silence_handling():
    engine = WhisperEngine(model_name="tiny", language="en", device="cpu")
    silence = np.zeros(16000, dtype=np.float32)

    class MockInfo:
        language = "en"

    class MockModel:
        def transcribe(self, audio, **kwargs):
            return [], MockInfo()

    engine._model = MockModel()
    res = engine.transcribe(silence)
    assert res["success"] is True
    assert res["text"] == ""


def test_whisper_mock_transcription():
    engine = WhisperEngine(model_name="tiny", language="en", device="cpu")
    # 1 second of sine wave (non-silent)
    sine_wave = np.sin(np.linspace(0, 100, 16000)).astype(np.float32)

    class MockSegment:
        text = "hello max"

    class MockInfo:
        language = "en"

    class MockModel:
        def transcribe(self, audio, **kwargs):
            return [MockSegment()], MockInfo()

    engine._model = MockModel()
    res = engine.transcribe(sine_wave)
    assert res["success"] is True
    assert res["text"] == "hello max"
    assert abs(res["duration"] - 1.0) < 0.01
