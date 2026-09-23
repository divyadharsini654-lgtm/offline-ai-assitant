"""
MAX Offline Voice-Based AI Assistant
Microphone Management & Device Enumeration
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    SD_AVAILABLE = True
except Exception as e:
    logger.warning(f"sounddevice import error: {e}")
    SD_AVAILABLE = False


class MicrophoneManager:
    """Manages audio input devices, safe query, and fallback states."""

    def __init__(self):
        self.is_available = SD_AVAILABLE

    def list_devices(self) -> List[Dict[str, Any]]:
        """List all available audio input devices."""
        if not self.is_available:
            return []
        try:
            devices = sd.query_devices()
            input_devs = []
            for idx, dev in enumerate(devices):
                if dev.get("max_input_channels", 0) > 0:
                    input_devs.append({
                        "index": idx,
                        "name": dev.get("name"),
                        "channels": dev.get("max_input_channels"),
                        "default_samplerate": dev.get("default_samplerate"),
                        "is_default": idx == sd.default.device[0],
                    })
            return input_devs
        except Exception as e:
            logger.error(f"Error querying audio devices: {e}")
            return []

    def get_default_device(self) -> Optional[Dict[str, Any]]:
        """Get the default input device details."""
        if not self.is_available:
            return None
        try:
            default_in_idx = sd.default.device[0]
            if default_in_idx is None or default_in_idx < 0:
                devs = self.list_devices()
                return devs[0] if devs else None
            dev_info = sd.query_devices(default_in_idx)
            return {
                "index": default_in_idx,
                "name": dev_info.get("name"),
                "channels": dev_info.get("max_input_channels"),
                "default_samplerate": dev_info.get("default_samplerate"),
            }
        except Exception as e:
            logger.warning(f"No default microphone detected: {e}")
            return None

    def check_health(self) -> Dict[str, Any]:
        """Check if a microphone is functional and available."""
        if not self.is_available:
            return {
                "status": "unavailable",
                "message": "Audio library not initialized or sounddevice unavailable",
                "device": None,
            }
        dev = self.get_default_device()
        if not dev:
            return {
                "status": "no_device",
                "message": "No microphone hardware detected",
                "device": None,
            }
        return {
            "status": "ready",
            "message": "Microphone ready",
            "device": dev,
        }


microphone_manager = MicrophoneManager()
