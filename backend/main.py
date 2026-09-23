"""
MAX – Offline Voice-Based AI Assistant
FastAPI Backend Application Entrypoint
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.api.routes import router as api_router
from backend.api.websocket import ws_manager
from backend.memory.database import memory_db
from backend.audio.microphone import microphone_manager
from backend.stt.whisper_engine import whisper_engine
from backend.tts.piper_engine import piper_engine

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("MAX")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("=" * 60)
    logger.info("  🚀 Starting MAX – Offline Voice-Based AI Assistant")
    logger.info("=" * 60)

    # 1. Initialize SQLite storage
    logger.info("✓ Initializing SQLite memory database...")
    memory_db._init_db()

    # 2. Check microphone
    mic_status = microphone_manager.check_health()
    logger.info(f"✓ Microphone status: {mic_status['status']} - {mic_status['message']}")

    # 3. Piper TTS setup
    logger.info("✓ Initializing Piper TTS Engine...")
    piper_engine.load_model()

    # 4. Background Whisper model verification
    logger.info(f"✓ Whisper model configured: '{settings.WHISPER_MODEL}' (device: {settings.WHISPER_DEVICE})")

    logger.info(f"✓ Serving UI at http://{settings.HOST}:{settings.PORT}")
    logger.info("=" * 60)
    logger.info("  ● OFFLINE MODE: ACTIVE. All operations local.")
    logger.info("=" * 60)

    yield

    logger.info("Stopping MAX assistant services...")
    piper_engine.stop()


app = FastAPI(
    title="MAX – Offline Voice-Based AI Assistant",
    description="Privacy-first, 100% offline voice assistant powered by Whisper, Piper, and local LLM reasoning.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach REST API router
app.include_router(api_router)


# Attach WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client heartbeats or messages
            pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# Mount frontend static files
frontend_path = settings.FRONTEND_DIR
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "MAX Frontend is building. index.html not yet found."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )
