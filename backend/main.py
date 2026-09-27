"""
MAX – Offline Voice-Based AI Assistant
Render / Cloud Compatible FastAPI Backend
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes import router as api_router
from backend.api.websocket import ws_manager
from backend.memory.database import memory_db

# Audio / AI engines
from backend.audio.microphone import microphone_manager
from backend.stt.whisper_engine import whisper_engine
from backend.tts.piper_engine import piper_engine


# ============================================================
# WINDOWS UTF-8 SUPPORT
# ============================================================

if sys.platform == "win32":

    try:
        sys.stdout.reconfigure(
            encoding="utf-8",
            errors="replace"
        )

        sys.stderr.reconfigure(
            encoding="utf-8",
            errors="replace"
        )

    except Exception:
        pass


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
)

logger = logging.getLogger("MAX")


# ============================================================
# ENVIRONMENT
# ============================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "production"
)

HOST = os.getenv(
    "HOST",
    "0.0.0.0"
)

PORT = int(
    os.getenv(
        "PORT",
        "8000"
    )
)


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("=" * 60)
    logger.info("🚀 Starting MAX – Offline Voice-Based AI Assistant")
    logger.info("=" * 60)

    logger.info(
        f"Environment: {ENVIRONMENT}"
    )

    logger.info(
        f"Host: {HOST}"
    )

    logger.info(
        f"Port: {PORT}"
    )

    # ========================================================
    # SQLITE DATABASE
    # ========================================================

    try:

        logger.info(
            "Initializing SQLite memory database..."
        )

        memory_db._init_db()

        logger.info(
            "✓ SQLite memory database ready"
        )

    except Exception as e:

        logger.warning(
            f"⚠ SQLite initialization warning: {e}"
        )


    # ========================================================
    # MICROPHONE
    # ========================================================

    try:

        mic_status = microphone_manager.check_health()

        logger.info(
            "Microphone status: "
            f"{mic_status.get('status', 'unknown')} - "
            f"{mic_status.get('message', '')}"
        )

    except Exception as e:

        logger.warning(
            "⚠ Microphone unavailable in cloud environment: "
            f"{e}"
        )

        logger.info(
            "✓ Server will continue without server-side microphone."
        )


    # ========================================================
    # PIPER TTS
    # ========================================================

    try:

        logger.info(
            "Initializing Piper TTS Engine..."
        )

        piper_engine.load_model()

        logger.info(
            "✓ Piper TTS initialization completed"
        )

    except Exception as e:

        logger.warning(
            f"⚠ Piper TTS unavailable: {e}"
        )

        logger.info(
            "✓ Server will continue without Piper TTS."
        )


    # ========================================================
    # WHISPER
    # ========================================================

    try:

        whisper_model = getattr(
            settings,
            "WHISPER_MODEL",
            "base"
        )

        whisper_device = getattr(
            settings,
            "WHISPER_DEVICE",
            "cpu"
        )

        logger.info(
            "Whisper model configured: "
            f"'{whisper_model}' "
            f"(device: {whisper_device})"
        )

    except Exception as e:

        logger.warning(
            f"⚠ Whisper configuration warning: {e}"
        )


    # ========================================================
    # CLOUD MODE
    # ========================================================

    logger.info("=" * 60)
    logger.info("☁ CLOUD MODE: ACTIVE")
    logger.info("🎤 Server-side microphone: optional")
    logger.info("🔊 Piper TTS: optional")
    logger.info("🧠 Whisper: configured")
    logger.info("🔌 WebSocket: enabled")
    logger.info("🌐 CORS: enabled")
    logger.info("=" * 60)


    # Application running
    yield


    # ========================================================
    # SHUTDOWN
    # ========================================================

    logger.info(
        "Stopping MAX assistant services..."
    )

    try:

        piper_engine.stop()

        logger.info(
            "✓ Piper TTS stopped"
        )

    except Exception as e:

        logger.warning(
            f"⚠ Piper shutdown warning: {e}"
        )

    logger.info(
        "MAX backend shutdown completed."
    )


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="MAX – Offline Voice-Based AI Assistant",

    description=(
        "Privacy-first voice assistant backend "
        "powered by Whisper, Piper and local AI."
    ),

    version="1.0.0",

    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "*"
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():

    return {
        "status": "ok",
        "service": "MAX AI Assistant",
        "environment": ENVIRONMENT,
        "websocket": "/ws",
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "message": "MAX AI Assistant Backend is running",
        "status": "online",
        "environment": ENVIRONMENT,
        "health": "/health",
        "websocket": "/ws",
    }


# ============================================================
# REST API
# ============================================================

app.include_router(
    api_router
)


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await ws_manager.connect(
        websocket
    )

    logger.info(
        "WebSocket client connected."
    )

    try:

        while True:

            data = await websocket.receive_text()

            logger.debug(
                f"WebSocket message received: {data}"
            )

    except WebSocketDisconnect:

        logger.info(
            "WebSocket client disconnected."
        )

        ws_manager.disconnect(
            websocket
        )

    except Exception as e:

        logger.warning(
            f"WebSocket error: {e}"
        )

        try:

            ws_manager.disconnect(
                websocket
            )

        except Exception:
            pass


# ============================================================
# SERVER START
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "backend.main:app",

        host=HOST,

        port=PORT,

        reload=False,
    )