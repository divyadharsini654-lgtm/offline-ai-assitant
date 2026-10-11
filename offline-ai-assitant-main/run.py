"""
MAX - Offline Voice-Based AI Assistant
System Launcher & Environment Verifier
"""

import os
import sys
import time
import socket
import logging
import threading
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("MAX-Launcher")


def verify_python_version():
    """Verify that Python 3.11 or higher is being used."""
    logger.info("Checking Python environment...")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 11):
        logger.error(f"Python 3.11+ is required. Detected Python {major}.{minor}")
        sys.exit(1)
    logger.info(f"OK  Python {major}.{minor}.{sys.version_info.micro} (Supported)")


def verify_dependencies():
    """Verify essential Python packages - warnings only, never crash the launcher."""
    logger.info("Checking required packages...")
    packages = {
        "fastapi": "FastAPI Web Server",
        "uvicorn": "ASGI Server",
        "soundfile": "Audio file I/O",
        "sounddevice": "Audio hardware driver",
        "faster_whisper": "faster-whisper Offline STT",
        "requests": "HTTP Client for Ollama",
    }
    issues = []
    for pkg, desc in packages.items():
        try:
            __import__(pkg)
            logger.info(f"OK  {desc} ({pkg})")
        except Exception as e:
            issues.append(pkg)
            logger.warning(f"WARN  {desc} ({pkg}): {e}")

    if issues:
        logger.warning(
            "Some packages had issues - the app will still start with available components."
        )
        logger.info("To fix: pip install -r backend/requirements.txt")
    else:
        logger.info("All critical dependencies verified.")


def ensure_directories_and_database():
    """Create models, data dirs and initialise the SQLite database."""
    logger.info("Verifying workspace directories & storage...")
    (PROJECT_ROOT / "models" / "whisper").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "models" / "piper").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)

    try:
        from backend.memory.database import memory_db
        memory_db._init_db()
        logger.info(f"OK  SQLite database at {memory_db.db_path}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def open_browser(url: str, delay: float = 2.0):
    """Open web browser after server starts."""
    time.sleep(delay)
    logger.info(f"Opening browser at {url}...")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.debug(f"Could not open browser automatically: {e}")


def print_banner():
    banner = """
==================================================================
                 MAX - OFFLINE VOICE AI ASSISTANT
==================================================================
  * 100% Offline & Privacy-First Architecture
  * Speech Recognition : faster-whisper (CTranslate2)
  * Reasoning Engine   : Modular Adapter (Ollama / Local Engine)
  * Text-to-Speech     : Local Piper TTS / pyttsx3 Fallback
  * Memory & History   : Local SQLite Database
  * Audio Processing   : Mojo SIMD / Vectorized NumPy Engine
==================================================================
"""
    print(banner)


def main():
    print_banner()
    verify_python_version()
    verify_dependencies()
    ensure_directories_and_database()

    from backend.config import settings
    host = settings.HOST
    port = settings.PORT
    url = f"http://{host}:{port}"

    if is_port_in_use(port, host):
        logger.warning(f"Port {port} already in use. Server may already be running.")
        logger.info(f"Visit {url} in your browser.")
        return

    logger.info(f"Starting MAX server on {url}...")

    # Launch browser automatically after brief delay
    browser_thread = threading.Thread(target=open_browser, args=(url,), daemon=True)
    browser_thread.start()

    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
