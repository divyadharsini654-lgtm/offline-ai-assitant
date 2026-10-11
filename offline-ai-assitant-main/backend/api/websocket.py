"""
MAX Offline Voice-Based AI Assistant
WebSocket Manager for Real-Time Status & Audio Streaming
"""

import json
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSockets for UI state synchronization and audio streaming."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.current_state: str = "IDLE"

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")
        # Send current initial state
        await self.send_personal_message(
            {"type": "state_change", "state": self.current_state, "message": "Ready"},
            websocket
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.debug(f"Failed to send personal message: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.add(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)

    async def broadcast_state(self, state: str, message: str = ""):
        """Broadcast assistant lifecycle state."""
        self.current_state = state
        await self.broadcast({
            "type": "state_change",
            "state": state,
            "message": message,
        })

    async def broadcast_audio_level(self, level: float, is_speech: bool = False):
        """Broadcast live microphone audio amplitude for dynamic waveform rendering."""
        await self.broadcast({
            "type": "audio_level",
            "level": round(level, 4),
            "is_speech": is_speech,
        })


ws_manager = ConnectionManager()
