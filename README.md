# MAX – Offline Voice-Based AI Assistant

> **Privacy-First Local Voice AI Assistant** powered by local Whisper speech recognition, modular local reasoning (Ollama / offline engine), Piper neural text-to-speech, SQLite memory, and SIMD-accelerated audio processing.

---

## 🚀 1. Project Overview

**MAX** is a production-grade, 100% offline conversational voice AI assistant designed to run completely on your local machine. 

### Why Offline?
- 🔒 **Absolute Privacy**: Your microphone audio, transcriptions, and conversations never leave your computer.
- ⚡ **Zero Cloud Latency & Subscriptions**: No OpenAI API keys, no Google Cloud Speech, no ElevenLabs, no monthly bills.
- 🛡️ **Air-Gapped & Resilient**: Works continuously even when your internet connection is down.

---

## 🏛️ 2. Pipeline & Architecture

```
                                  USER VOICE
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   Microphone Audio Stream │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │  Voice Activity Detection │ (VAD / Energy Gating)
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │  Whisper Offline STT      │ (Local speech-to-text)
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │  Command / Intent Engine  │ (Allowlist vs Conversational)
                        └──────┬─────────────┬──────┘
                               │             │
              [Command Action] │             │ [Conversational Query]
                               ▼             ▼
                 ┌──────────────────┐  ┌──────────────────────────┐
                 │  Safe OS Command │  │  Local Reasoning (Ollama │
                 │  Handler         │  │  or Built-in Engine)     │
                 └─────────────┬────┘  └─────────────┬────────────┘
                               │                     │
                               └──────────┬──────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │ SQLite Local Memory │ (Persistent multi-turn)
                               └──────────┬──────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │   Piper Offline TTS │ (ONNX neural synthesis)
                               └──────────┬──────────┘
                                          │
                                          ▼
                                     LOUDSPEAKER
```

---

## ✨ 3. Core Features

- **Local Speech Recognition**: Transcribes microphone speech via local Whisper models (`tiny`, `base`, `small`).
- **Modular Local Reasoning**: Seamless provider-independent reasoning layer:
  - **Ollama Adapter**: Connects locally to `llama3.2`, `mistral`, `phi3`, etc.
  - **Smart Built-in Offline Engine**: Zero-dependency offline intelligence with multi-turn pronoun tracking (e.g. *"What is Python?"* followed by *"Who created it?"*).
- **Offline Text-to-Speech**: Neural voice generation via Piper ONNX models, with automated local `pyttsx3` fallback.
- **Safe Command Allowlist**: Executes system utilities (`Calculator`, `Notepad`, `File Explorer`, `Time`, `Date`, `Jokes`) without allowing arbitrary shell injections.
- **SQLite Memory Database**: Chronological multi-turn history with clearing and thread management.
- **Futuristic Glassmorphic UI**:
  - Startup initialization checklist with animated progress.
  - Interactive glowing microphone button with circular animated waveform.
  - Seven real-time assistant states: `IDLE`, `LISTENING`, `RECORDING`, `TRANSCRIBING`, `THINKING`, `SPEAKING`, `ERROR`.
  - Push-to-talk (`Space`) and instant speech interruption (`Esc`).
- **Mojo Audio Module**: SIMD-vectorized audio processing module (`backend/mojo/audio_processing.mojo`) with transparent fallback bridge.

---

## 📁 4. Project Structure

```
MAX/
│
├── backend/
│   ├── main.py                     # FastAPI application & lifecycle manager
│   ├── config.py                   # Centralized configuration & environment loader
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── api/
│   │   ├── routes.py               # REST API endpoints
│   │   └── websocket.py            # Real-time WebSocket connection manager
│   │
│   ├── audio/
│   │   ├── microphone.py           # Device discovery & microphone health
│   │   ├── recorder.py             # Buffer manager & streaming capture
│   │   ├── vad.py                  # Adaptive Voice Activity Detection
│   │   └── player.py               # Local audio playback & interruption
│   │
│   ├── stt/
│   │   └── whisper_engine.py       # Offline Whisper engine wrapper
│   │
│   ├── reasoning/
│   │   ├── engine.py               # Abstract reasoning engine interface
│   │   ├── ollama_engine.py        # Ollama HTTP adapter
│   │   ├── fallback_engine.py      # Built-in offline knowledge & reasoning engine
│   │   ├── intent.py               # Intent classifier (commands vs queries)
│   │   └── context.py              # Multi-turn conversation context manager
│   │
│   ├── tts/
│   │   └── piper_engine.py         # Piper ONNX neural voice engine & fallback
│   │
│   ├── commands/
│   │   └── command_handler.py      # Safe local command execution with allowlist
│   │
│   ├── memory/
│   │   ├── database.py             # SQLite persistence & connection pooling
│   │   └── models.py               # Message & Conversation schema models
│   │
│   └── mojo/
│       ├── audio_processing.mojo   # Mojo SIMD audio acceleration module
│       └── bridge.py               # Python-Mojo transparent execution bridge
│
├── frontend/
│   ├── index.html                  # Startup checklist & futuristic assistant interface
│   ├── style.css                   # Cyberpunk glassmorphism design system
│   └── app.js                      # Web Audio API, WebSockets, canvas visualizer
│
├── models/
│   ├── whisper/                    # Local Whisper model weights cache
│   └── piper/                      # Local Piper ONNX voice models
│
├── data/
│   └── max.db                      # Local SQLite conversation database
│
├── tests/
│   ├── test_stt.py                 # Whisper engine tests
│   ├── test_tts.py                 # Piper TTS tests
│   ├── test_commands.py            # Allowlist security tests
│   ├── test_memory.py              # SQLite storage & context tests
│   └── test_api.py                 # FastAPI route & chat integration tests
│
├── .env.example                    # Environment configuration template
├── .gitignore                      # Git ignore rules
├── README.md                       # Documentation
└── run.py                          # All-in-one launcher script
```

---

## 🛠️ 5. System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Python 3.11 or higher (Python 3.13 recommended)
- **RAM**: 8 GB minimum (16 GB recommended when running larger local LLMs)
- **Audio Hardware**: Microphone and speakers/headphones

---

## ⚙️ 6. Quickstart & Installation

### Step 1: Clone or Navigate to the Repository
```bash
cd trustgrid
```

### Step 2: Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

---

## 🎙️ 7. Model Setup Guide

### A. Whisper Speech-to-Text Setup
Whisper models are automatically downloaded and cached locally into `models/whisper/` on their first initialization.
You can configure the model size in your `.env` or from the in-app Settings modal:
- `tiny`: ~75 MB (Ultra-fast, lowest latency)
- `base`: ~140 MB (Default recommended for general speech)
- `small`: ~460 MB (Higher accuracy)

### B. Piper Text-to-Speech Setup
1. Download a voice model and its JSON configuration from the [Piper Voice Library](https://github.com/rhasspy/piper/blob/master/VOICES.md) (e.g. `en_US-lessac-medium`):
   - `voice.onnx` -> save to `models/piper/voice.onnx`
   - `voice.onnx.json` -> save to `models/piper/voice.onnx.json`
2. **Built-in Fallback**: If the ONNX file is not present, MAX automatically activates the local `pyttsx3` offline speech engine so speech works immediately without crashing!

### C. Local LLM Reasoning (Ollama Setup)
1. Download and install [Ollama](https://ollama.com).
2. Pull your preferred local model:
   ```bash
   ollama pull llama3.2
   ```
3. Start Ollama:
   ```bash
   ollama serve
   ```
4. **Built-in Fallback**: If Ollama is not installed or turned off, MAX's built-in offline engine will answer queries, explain programming concepts, handle entity references, and execute safe commands seamlessly.

### D. Mojo Setup (Optional)
MAX includes a dedicated Mojo acceleration file at `backend/mojo/audio_processing.mojo`.
- To compile/run with Mojo on systems with Mojo installed:
  ```bash
  mojo backend/mojo/audio_processing.mojo
  ```
- If Mojo is not installed, MAX seamlessly uses its optimized NumPy vectorization bridge (`backend/mojo/bridge.py`), ensuring 100% functionality on all operating systems.

---

## 🚀 8. Running MAX

Simply launch using the automated runner:

```bash
python run.py
```

The runner will:
1. Validate your Python version.
2. Verify all dependencies.
3. Check and initialize the SQLite database (`data/max.db`).
4. Start the FastAPI backend server on `http://127.0.0.1:8000`.
5. Automatically open your default web browser to the MAX interface.

---

## 🧪 9. Running Tests

Execute the automated test suite with pytest:

```bash
python -m pytest tests/ -v
```

---

## 🛡️ 10. Security & Privacy Guardrails

1. **Command Allowlist**: Only explicit actions configured in `CommandHandler.ALLOWED_PROGRAMS` and allowlisted handlers can be executed. Shell commands from user voice or LLM hallucination are strictly rejected.
2. **Audio Ephemerality**: User microphone recordings are processed in-memory buffers for transcription and are never permanently stored to disk.
3. **Local Database**: All conversation memory is stored in the local SQLite database (`data/max.db`). No telemetry or analytics are gathered.

---

## ⌨️ 11. Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `Space` | Toggle Microphone (when text box is not focused) |
| `Escape` | Immediately Stop Assistant Speech Playback |
| `Enter` | Send typed message |

---

## 📄 License
MIT License. Built for offline privacy and local AI paired programming.
