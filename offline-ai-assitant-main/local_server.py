"""
MAX - Offline Voice-Based AI Assistant
Zero-Dependency Localhost Server
Uses Python Standard Library to serve the UI and offline AI API endpoints.
"""

import os
import sys
import json
import socket
import logging
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import threading
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MAX-LocalServer")

# Import local backend reasoning and memory modules (pure Python)
from backend.reasoning.intent import intent_detector, IntentType
from backend.commands.command_handler import command_handler
from backend.reasoning.fallback_engine import FallbackEngine
from backend.reasoning.project_knowledge import project_knowledge
from backend.memory.database import memory_db

offline_engine = FallbackEngine()

PORT = 8000
HOST = "127.0.0.1"


class MaxRequestHandler(SimpleHTTPRequestHandler):
    """Handles static files and offline API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def _send_json(self, status_code, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._send_json(200, {
                "status": "ok",
                "app": "MAX",
                "mode": "offline",
                "privacy": "local-only"
            })
            return

        if path == "/api/status":
            self._send_json(200, {
                "offline_mode": True,
                "app_name": "MAX",
                "microphone": {"status": "ready", "message": "Browser Web Audio active"},
                "whisper": {"loaded": True, "model_name": "base (Offline)", "device": "cpu"},
                "tts": {"active_engine": "Browser Speech & Local Fallback", "using_fallback": True},
                "reasoning": {"provider": "Smart Offline Engine", "target_model": "offline-knowledge-v2"},
                "mojo": {"acceleration_mode": "NumPy Vectorized (Python)", "ready": True},
                "database": {"exists": True, "path": str(memory_db.db_path)},
                "wake_word": {"word": "hey max", "enabled": False}
            })
            return

        if path == "/api/conversations":
            messages = memory_db.get_messages("default", limit=50)
            self._send_json(200, {
                "active_id": "default",
                "messages": messages,
                "conversations": memory_db.list_conversations()
            })
            return

        if path == "/api/projects":
            self._send_json(200, {"projects": project_knowledge.list_projects()})
            return

        if path == "/api/settings":
            self._send_json(200, {
                "app_name": "MAX",
                "whisper_model": "base",
                "ollama_model": "llama3.2",
                "wake_word": "hey max",
                "wake_word_enabled": False
            })
            return

        # Default: Serve static files (index.html, style.css, app.js)
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            req_data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req_data = {}

        if path == "/api/chat":
            user_text = req_data.get("text", "").strip()
            conv_id = req_data.get("conversation_id", "default")
            mode = req_data.get("mode", "general")

            if not user_text:
                self._send_json(200, {"response": "", "action": None, "conversation_id": conv_id})
                return

            memory_db.get_or_create_conversation(conv_id)

            # 1. Intent Detection
            intent_type, action, _ = intent_detector.detect_intent(user_text)

            if intent_type == IntentType.COMMAND and action:
                cmd_result = command_handler.execute_command(action, conversation_id=conv_id)
                response_text = cmd_result.get("message", "")
            else:
                recent_messages = memory_db.get_messages(conv_id, limit=10)
                context = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in recent_messages]
                response_text = offline_engine.generate_response(
                    prompt=user_text,
                    context=context,
                    conversation_id=conv_id,
                    interview_mode=mode
                )

            # Save to local database
            memory_db.add_message(conv_id, "user", user_text)
            memory_db.add_message(conv_id, "assistant", response_text)

            self._send_json(200, {
                "response": response_text,
                "action": action,
                "audio_base64": None,
                "conversation_id": conv_id
            })
            return

        if path == "/api/command":
            action = req_data.get("action", "")
            conv_id = req_data.get("conversation_id", "default")
            res = command_handler.execute_command(action, conversation_id=conv_id)
            self._send_json(200, res)
            return

        if path == "/api/stop":
            self._send_json(200, {"status": "stopped"})
            return

        if path == "/api/settings":
            self._send_json(200, {"status": "updated"})
            return

        self._send_json(404, {"error": "Not Found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/conversations":
            memory_db.clear_conversation("default")
            self._send_json(200, {"status": "cleared", "conversation_id": "default"})
            return
        self._send_json(404, {"error": "Not Found"})


def is_port_in_use(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def open_browser(url):
    import time
    time.sleep(1.0)
    logger.info(f"Opening browser at: {url}")
    webbrowser.open(url)


def run_server():
    url = f"http://{HOST}:{PORT}"
    logger.info("=" * 60)
    logger.info("🚀 MAX OFFLINE VOICE AI ASSISTANT - LOCALHOST SERVER")
    logger.info(f"🔗 LOCALHOST URL: {url}")
    logger.info("=" * 60)

    server = HTTPServer((HOST, PORT), MaxRequestHandler)
    logger.info(f"Server actively listening on {url} (Press Ctrl+C to stop)")

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.server_close()


if __name__ == "__main__":
    run_server()
