"""
Unit Tests for MAX Text-to-Speech (PiperEngine)
"""

import wave
import io
import pytest
from backend.tts.piper_engine import PiperEngine


def test_piper_engine_initialization():
    engine = PiperEngine()
    status = engine.get_status()
    assert "model_path" in status
    assert "model_installed" in status
    assert "using_fallback" in status


def test_piper_fallback_synthesis():
    engine = PiperEngine()
    # Force fallback mode
    engine._fallback_active = True

    wav_bytes = engine.synthesize_wav_bytes("Hello from MAX assistant.")
    assert wav_bytes is not None
    assert len(wav_bytes) > 44  # Valid WAV header + data

    # Verify WAV header structure
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getnchannels() in (1, 2)
        assert wf.getsampwidth() == 2  # 16-bit PCM
        assert wf.getframerate() in (16000, 22050, 24000, 44100)


def test_piper_empty_text():
    engine = PiperEngine()
    result = engine.synthesize_wav_bytes("")
    assert result is None


def test_piper_stop_execution():
    engine = PiperEngine()
    # Test that calling stop does not throw an exception
    engine.stop()
