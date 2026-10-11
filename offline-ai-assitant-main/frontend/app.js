/**
 * MAX – Offline Voice-Based AI Assistant
 * Frontend Application Logic, Futuristic Audio Visualizer, and State Manager
 */

/* ================= BACKEND CONFIGURATION =================
   Deployed Render backend
*/
const BACKEND_URL = "https://offline-ai-assitant-9.onrender.com";

function apiUrl(path) {
  return `${BACKEND_URL}${path}`;
}

function websocketUrl(path) {
  const url = new URL(BACKEND_URL);
  const protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${url.host}${path}`;
}

// Application State
const state = {
  assistantState: "IDLE",
  conversationId: "default",
  isRecording: false,
  isPlayingAudio: false,
  audioContext: null,
  analyser: null,
  micStream: null,
  mediaRecorder: null,
  audioChunks: [],
  currentAudioPlayer: null,
  ws: null,
  modelsStatus: {},
  currentAttachment: null,
};

// UI State labels and subtitle mapping
const STATE_LABELS = {
  IDLE: {
    text: "● Ready",
    subtitle: '"Click microphone or press Space to talk"',
  },
  LISTENING: {
    text: "🎙️ Listening...",
    subtitle: "Listening for your voice...",
  },
  RECORDING: {
    text: "🎙️ Listening...",
    subtitle: "Recording your query...",
  },
  TRANSCRIBING: {
    text: "◌ Understanding voice...",
    subtitle: "Transcribing audio with local Whisper...",
  },
  THINKING: {
    text: "◌ MAX is thinking...",
    subtitle: "Processing response with local reasoning...",
  },
  SPEAKING: {
    text: "🔊 MAX is speaking...",
    subtitle: "Speaking with local Piper TTS...",
  },
  ERROR: {
    text: "⚠️ Error",
    subtitle: "Something went wrong. Please try again.",
  },
};

// DOM Elements
const elements = {
  loadingScreen: document.getElementById("loading-screen"),
  loadingProgressBar: document.getElementById("loading-progress-bar"),
  loadingReadyMsg: document.getElementById("loading-ready-msg"),
  appContainer: document.getElementById("app-container"),

  statePill: document.getElementById("state-pill"),
  stateText: document.getElementById("state-text"),
  transcriptionBox: document.getElementById("live-transcription-box"),
  speakingWaveformIndicator: document.getElementById("speaking-waveform-indicator"),
  thinkingIndicator: document.getElementById("thinking-indicator"),
  inputStatusHint: document.getElementById("input-status-hint"),
  inputStatusText: document.getElementById("input-status-text"),

  micBtn: document.getElementById("mic-btn"),
  inputMicBtn: document.getElementById("input-mic-btn"),
  waveformCanvas: document.getElementById("waveform-canvas"),
  stopSpeakingBtn: document.getElementById("stop-speaking-btn"),

  chatMessages: document.getElementById("chat-messages"),
  chatForm: document.getElementById("text-input-form"),
  chatInput: document.getElementById("chat-input"),
  sendBtn: document.getElementById("send-btn"),
  clearChatBtn: document.getElementById("clear-chat-btn"),

  attachBtn: document.getElementById("chat-attach-btn"),
  attachmentInput: document.getElementById("chat-attachment-input"),
  attachmentPreview: document.getElementById("attachment-preview"),
  attachmentName: document.getElementById("attachment-name"),
  removeAttachmentBtn: document.getElementById("remove-attachment-btn"),

  modeSelect: document.getElementById("mode-select"),
  projectSelect: document.getElementById("project-select"),
  thinkToggleBtn: document.getElementById("think-toggle-btn"),

  settingsBtn: document.getElementById("settings-btn"),
  settingsModal: document.getElementById("settings-modal"),
  closeModalBtn: document.getElementById("close-modal-btn"),
  saveSettingsBtn: document.getElementById("save-settings-btn"),
  diagnosticsContent: document.getElementById("diagnostics-content"),

  sttBadge: document.getElementById("stt-badge"),
  reasoningBadge: document.getElementById("reasoning-badge"),
  ttsBadge: document.getElementById("tts-badge"),
  mojoSpec: document.getElementById("mojo-spec"),
};

// ================= INITIALIZATION & STARTUP CHECKLIST =================
async function initStartup() {
  const checkItems = [
    { id: "check-cfg", delay: 250 },
    { id: "check-mic", delay: 350 },
    { id: "check-whisper", delay: 450 },
    { id: "check-reasoning", delay: 400 },
    { id: "check-piper", delay: 350 },
    { id: "check-memory", delay: 250 },
    { id: "check-models", delay: 300 },
  ];

  let progress = 0;
  for (let i = 0; i < checkItems.length; i++) {
    const item = checkItems[i];
    await new Promise((r) => setTimeout(r, item.delay));
    const el = document.getElementById(item.id);
    if (el) {
      el.classList.add("done");
      const icon = el.querySelector(".check-icon");
      if (icon) icon.textContent = "✓";
    }
    progress = Math.round(((i + 1) / checkItems.length) * 100);
    if (elements.loadingProgressBar) {
      elements.loadingProgressBar.style.width = `${progress}%`;
    }
  }

  // Fetch initial system status from backend
  await fetchSystemStatus();

  // Show "MAX is ready"
  if (elements.loadingReadyMsg) {
    elements.loadingReadyMsg.classList.remove("hidden");
  }

  // Reveal main UI after a brief pause
  setTimeout(() => {
    if (elements.loadingScreen) {
      elements.loadingScreen.style.opacity = "0";
      setTimeout(() => {
        elements.loadingScreen.classList.add("hidden");
        elements.appContainer.classList.remove("hidden");
        initCanvasVisualizer();
        connectWebSocket();
        loadConversationHistory();
      }, 500);
    }
  }, 650);
}

// ================= SYSTEM STATUS & HEALTH =================
async function fetchSystemStatus() {
  try {
    const res = await fetch("https://offline-ai-assitant-9.onrender.com/api/status");
    if (res.ok) {
      const data = await res.json();
      state.modelsStatus = data;
      updateStatusUI(data);
    }
  } catch (err) {
    console.warn("Could not fetch status:", err);
  }
}

function updateStatusUI(status) {
  if (!status) return;

  // STT badge
  if (status.whisper && status.whisper.loaded) {
    elements.sttBadge.textContent = `Whisper (${status.whisper.model_name || "base"})`;
    elements.sttBadge.classList.add("active");
  } else {
    elements.sttBadge.textContent = `Whisper (Ready)`;
  }

  // Reasoning badge
  if (status.reasoning) {
    const isOllama = status.reasoning.provider === "Ollama";
    elements.reasoningBadge.textContent = isOllama
      ? `Ollama (${status.reasoning.target_model || "llama3.2"})`
      : "Local Reasoning";
    elements.reasoningBadge.classList.add("active");
  }

  // TTS badge
  if (status.tts) {
    elements.ttsBadge.textContent = status.tts.active_engine ? status.tts.active_engine : "Piper TTS";
    elements.ttsBadge.classList.add("active");
  }

  // Mojo status
  if (status.mojo && elements.mojoSpec) {
    elements.mojoSpec.textContent = status.mojo.acceleration_mode || "Mojo SIMD Enabled";
  }

  // Diagnostics modal content
  if (elements.diagnosticsContent) {
    elements.diagnosticsContent.textContent = JSON.stringify(status, null, 2);
  }
}

// ================= WEBSOCKET FOR REAL-TIME EVENTS =================
function connectWebSocket() {
  const wsUrl = "wss://offline-ai-assitant-9.onrender.com/ws";

  try {
    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
      console.log("WebSocket connected to MAX backend.");
    };

    state.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.type === "state_change") {
          setAssistantState(msg.state, msg.message);
        }
      } catch (e) {
        console.error("WS parse error:", e);
      }
    };

    state.ws.onclose = () => {
      setTimeout(connectWebSocket, 3000);
    };

    state.ws.onerror = (err) => {
      console.warn("WebSocket error:", err);
    };
  } catch (err) {
    console.error("Failed to connect WS:", err);
  }
}

// ================= ASSISTANT STATE MANAGEMENT =================
function setAssistantState(newState, customSubtitle) {
  state.assistantState = newState;
  const panel = document.querySelector(".voice-center-panel");
  const floatingInput = document.querySelector(".floating-ai-input");

  // Reset panels and container state classes
  if (panel) {
    panel.classList.remove("speaking", "listening", "thinking", "idle");
    panel.classList.add(newState.toLowerCase());
  }

  if (floatingInput) {
    floatingInput.classList.remove("speaking", "listening", "thinking", "idle");
    floatingInput.classList.add(newState.toLowerCase());
  }

  if (elements.appContainer) {
    elements.appContainer.classList.remove("state-speaking", "state-listening", "state-thinking", "state-idle");
    elements.appContainer.classList.add(`state-${newState.toLowerCase()}`);
  }

  // 1. Update State Pill
  if (elements.statePill) {
    elements.statePill.className = `state-pill ${newState.toLowerCase()}`;
  }

  const stateInfo = STATE_LABELS[newState] || { text: newState, subtitle: "" };
  if (elements.stateText) {
    elements.stateText.textContent = stateInfo.text;
  }

  // 2. Update Subtitle Box
  if (elements.transcriptionBox) {
    if (customSubtitle) {
      elements.transcriptionBox.textContent = `"${customSubtitle}"`;
    } else if (stateInfo.subtitle) {
      elements.transcriptionBox.textContent = stateInfo.subtitle;
    }
  }

  // 3. Update Specific State Visual Indicators
  if (newState === "SPEAKING") {
    if (elements.speakingWaveformIndicator) elements.speakingWaveformIndicator.classList.remove("hidden");
    if (elements.thinkingIndicator) elements.thinkingIndicator.classList.add("hidden");
    if (elements.inputStatusHint) elements.inputStatusHint.classList.add("hidden");
    if (elements.micBtn) elements.micBtn.classList.remove("active");
    if (elements.inputMicBtn) elements.inputMicBtn.classList.remove("active", "listening");
    if (elements.sendBtn) elements.sendBtn.classList.remove("listening");
  } else if (newState === "LISTENING" || newState === "RECORDING") {
    if (elements.speakingWaveformIndicator) elements.speakingWaveformIndicator.classList.add("hidden");
    if (elements.thinkingIndicator) elements.thinkingIndicator.classList.add("hidden");
    if (elements.inputStatusHint) {
      elements.inputStatusHint.classList.remove("hidden");
      if (elements.inputStatusText) elements.inputStatusText.textContent = "Listening...";
    }
    if (elements.micBtn) elements.micBtn.classList.add("active");
    if (elements.inputMicBtn) elements.inputMicBtn.classList.add("active", "listening");
    if (elements.sendBtn) elements.sendBtn.classList.add("listening");
  } else if (newState === "THINKING" || newState === "TRANSCRIBING") {
    if (elements.speakingWaveformIndicator) elements.speakingWaveformIndicator.classList.add("hidden");
    if (elements.thinkingIndicator) {
      elements.thinkingIndicator.classList.remove("hidden");
      const label = elements.thinkingIndicator.querySelector(".thinking-label");
      if (label) {
        label.textContent = newState === "TRANSCRIBING" ? "Transcribing voice" : "MAX is thinking";
      }
    }
    if (elements.inputStatusHint) {
      elements.inputStatusHint.classList.remove("hidden");
      if (elements.inputStatusText) {
        elements.inputStatusText.textContent = newState === "TRANSCRIBING" ? "Transcribing..." : "Thinking...";
      }
    }
    if (elements.micBtn) elements.micBtn.classList.remove("active");
    if (elements.inputMicBtn) elements.inputMicBtn.classList.remove("active", "listening");
    if (elements.sendBtn) elements.sendBtn.classList.remove("listening");
  } else {
    // IDLE or ERROR
    if (elements.speakingWaveformIndicator) elements.speakingWaveformIndicator.classList.add("hidden");
    if (elements.thinkingIndicator) elements.thinkingIndicator.classList.add("hidden");
    if (elements.inputStatusHint) elements.inputStatusHint.classList.add("hidden");
    if (elements.micBtn) elements.micBtn.classList.remove("active");
    if (elements.inputMicBtn) elements.inputMicBtn.classList.remove("active", "listening");
    if (elements.sendBtn) elements.sendBtn.classList.remove("listening");
  }
}

// ================= FUTURISTIC CANVAS VISUALIZER =================
let animFrameId = null;
let visualPhase = 0;
const orbitalParticles = [];

// Initialize orbital background particles
for (let p = 0; p < 24; p++) {
  orbitalParticles.push({
    angle: Math.random() * Math.PI * 2,
    radius: 75 + Math.random() * 85,
    speed: 0.005 + Math.random() * 0.012,
    size: 1.2 + Math.random() * 2,
    alpha: 0.2 + Math.random() * 0.6,
  });
}

function initCanvasVisualizer() {
  const canvas = elements.waveformCanvas;
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const size = 420;

  canvas.width = size * dpr;
  canvas.height = size * dpr;
  ctx.scale(dpr, dpr);

  const centerX = size / 2;
  const centerY = size / 2;
  const baseRadius = 66;

  function renderWaveform() {
    ctx.clearRect(0, 0, size, size);
    visualPhase += 0.035;

    let energy = 0.0;
    const freqData = new Uint8Array(64);

    if (state.analyser && (state.isRecording || state.isPlayingAudio)) {
      state.analyser.getByteFrequencyData(freqData);
      let sum = 0;
      for (let i = 0; i < freqData.length; i++) sum += freqData[i];
      energy = sum / (freqData.length * 255.0);
    } else if (state.assistantState === "RECORDING" || state.assistantState === "LISTENING") {
      energy = 0.32 + Math.sin(visualPhase * 2.5) * 0.15;
    } else if (state.assistantState === "SPEAKING") {
      energy = 0.45 + Math.sin(visualPhase * 3.2) * 0.22 + Math.cos(visualPhase * 1.5) * 0.1;
    } else if (state.assistantState === "THINKING" || state.assistantState === "TRANSCRIBING") {
      energy = 0.2 + Math.sin(visualPhase * 1.8) * 0.08;
    } else {
      // Gentle breathing idle pulse
      energy = 0.06 + Math.sin(visualPhase * 0.9) * 0.03;
    }

    // 1. Draw glowing ambient core backglow
    const coreGlow = ctx.createRadialGradient(centerX, centerY, 10, centerX, centerY, baseRadius + 30);
    if (state.assistantState === "RECORDING" || state.assistantState === "LISTENING") {
      coreGlow.addColorStop(0, "rgba(6, 182, 212, 0.35)");
      coreGlow.addColorStop(0.6, "rgba(14, 165, 233, 0.15)");
      coreGlow.addColorStop(1, "rgba(6, 182, 212, 0)");
    } else if (state.assistantState === "SPEAKING") {
      coreGlow.addColorStop(0, "rgba(16, 185, 129, 0.35)");
      coreGlow.addColorStop(0.6, "rgba(6, 182, 212, 0.18)");
      coreGlow.addColorStop(1, "rgba(16, 185, 129, 0)");
    } else if (state.assistantState === "THINKING" || state.assistantState === "TRANSCRIBING") {
      coreGlow.addColorStop(0, "rgba(245, 158, 11, 0.3)");
      coreGlow.addColorStop(0.6, "rgba(139, 92, 246, 0.15)");
      coreGlow.addColorStop(1, "rgba(245, 158, 11, 0)");
    } else {
      coreGlow.addColorStop(0, "rgba(99, 102, 241, 0.18)");
      coreGlow.addColorStop(0.7, "rgba(6, 182, 212, 0.06)");
      coreGlow.addColorStop(1, "rgba(99, 102, 241, 0)");
    }
    ctx.fillStyle = coreGlow;
    ctx.beginPath();
    ctx.arc(centerX, centerY, baseRadius + 30, 0, Math.PI * 2);
    ctx.fill();

    // 2. Draw Floating Quantum Sparkles
    for (let i = 0; i < orbitalParticles.length; i++) {
      const p = orbitalParticles[i];
      p.angle += p.speed * (state.assistantState === "SPEAKING" ? 2.2 : 1);
      const px = centerX + Math.cos(p.angle) * (p.radius + energy * 15);
      const py = centerY + Math.sin(p.angle) * (p.radius + energy * 15);

      ctx.beginPath();
      ctx.arc(px, py, p.size, 0, Math.PI * 2);
      ctx.fillStyle = state.assistantState === "SPEAKING"
        ? `rgba(52, 211, 153, ${p.alpha})`
        : state.assistantState === "LISTENING" || state.assistantState === "RECORDING"
          ? `rgba(56, 189, 248, ${p.alpha})`
          : `rgba(165, 180, 252, ${p.alpha * 0.8})`;
      ctx.fill();
    }

    // 3. Concentric Shockwave Rings
    const ringCount = 3;
    for (let r = 1; r <= ringCount; r++) {
      const ringRadius = baseRadius + r * 20 + energy * 28 * (r * 0.4);
      ctx.beginPath();
      ctx.arc(centerX, centerY, ringRadius, 0, Math.PI * 2);
      let ringColor;
      if (state.assistantState === "SPEAKING") {
        ringColor = `rgba(16, 185, 129, ${0.28 / r})`;
      } else if (state.assistantState === "LISTENING" || state.assistantState === "RECORDING") {
        ringColor = `rgba(6, 182, 212, ${0.32 / r})`;
      } else if (state.assistantState === "THINKING" || state.assistantState === "TRANSCRIBING") {
        ringColor = `rgba(245, 158, 11, ${0.24 / r})`;
      } else {
        ringColor = `rgba(99, 102, 241, ${0.12 / r})`;
      }
      ctx.strokeStyle = ringColor;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    // 4. Circular Equalizer Waveform Bars (48 segments)
    const numBars = 48;
    for (let i = 0; i < numBars; i++) {
      const angle = (i / numBars) * Math.PI * 2;
      const freqVal = freqData[i % freqData.length] / 255.0;

      // Height modulation according to state
      let dynamicHeight = 4;
      if (state.assistantState === "SPEAKING") {
        dynamicHeight = 8 + (freqVal * 42) + (energy * 32) * Math.abs(Math.sin(visualPhase * 2 + i * 0.25));
      } else if (state.assistantState === "LISTENING" || state.assistantState === "RECORDING") {
        dynamicHeight = 6 + (freqVal * 36) + (energy * 28) * Math.abs(Math.sin(visualPhase * 3 + i * 0.3));
      } else if (state.assistantState === "THINKING" || state.assistantState === "TRANSCRIBING") {
        dynamicHeight = 5 + Math.sin(visualPhase * 2.5 + i * 0.4) * 12 + energy * 10;
      } else {
        // Calm idle breathing wave
        dynamicHeight = 4 + Math.sin(visualPhase + i * 0.3) * 5;
      }

      const r1 = baseRadius + 8;
      const r2 = r1 + dynamicHeight;

      const x1 = centerX + Math.cos(angle) * r1;
      const y1 = centerY + Math.sin(angle) * r1;
      const x2 = centerX + Math.cos(angle) * r2;
      const y2 = centerY + Math.sin(angle) * r2;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);

      const grad = ctx.createLinearGradient(x1, y1, x2, y2);
      if (state.assistantState === "SPEAKING") {
        grad.addColorStop(0, "#10b981");
        grad.addColorStop(1, "#06b6d4");
      } else if (state.assistantState === "LISTENING" || state.assistantState === "RECORDING") {
        grad.addColorStop(0, "#0284c7");
        grad.addColorStop(1, "#38bdf8");
      } else if (state.assistantState === "THINKING" || state.assistantState === "TRANSCRIBING") {
        grad.addColorStop(0, "#f59e0b");
        grad.addColorStop(1, "#8b5cf6");
      } else {
        grad.addColorStop(0, "rgba(99, 102, 241, 0.4)");
        grad.addColorStop(1, "rgba(6, 182, 212, 0.5)");
      }

      ctx.strokeStyle = grad;
      ctx.lineWidth = 2.4;
      ctx.lineCap = "round";
      ctx.stroke();
    }

    // 5. Outer Sci-Fi Orbital Energy Sparks
    const sparkCount = 3;
    for (let s = 0; s < sparkCount; s++) {
      const sAngle = visualPhase * 1.6 + (s * Math.PI * 2) / sparkCount;
      const sRadius = baseRadius + 44 + Math.sin(visualPhase + s * 2) * 6;
      const sx = centerX + Math.cos(sAngle) * sRadius;
      const sy = centerY + Math.sin(sAngle) * sRadius;

      ctx.beginPath();
      ctx.arc(sx, sy, 3, 0, Math.PI * 2);
      const sparkColor = state.assistantState === "SPEAKING"
        ? "#34d399"
        : state.assistantState === "LISTENING" || state.assistantState === "RECORDING"
          ? "#38bdf8"
          : "#818cf8";
      ctx.fillStyle = sparkColor;
      ctx.shadowColor = sparkColor;
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    animFrameId = requestAnimationFrame(renderWaveform);
  }

  renderWaveform();
}

// ================= CLIENT-SIDE RICH KNOWLEDGE BASE =================
const CLIENT_KNOWLEDGE = {
  python: {
    title: "Python Programming",
    definition: "Python is a high-level, interpreted, dynamically-typed programming language celebrated for its clear, human-readable syntax and powerful ecosystem.",
    key_concepts: "Dynamic typing, automatic garbage collection, list comprehensions, decorators, generators, and multi-paradigm support (OOP, Functional, Procedural).",
    example: "def reverse_string(s: str) -> str:\n    return s[::-1]\n\nprint(reverse_string('MAX')) # Output: XAM",
    interview_tip: "Highlight Python's rapid development cycle, versatility in AI/ML (PyTorch, TensorFlow), Data Science, and modern high-speed backends (FastAPI).",
  },
  java: {
    title: "Java Programming",
    definition: "Java is a class-based, object-oriented programming language designed for portability across platforms via the Java Virtual Machine (JVM).",
    key_concepts: "Write Once Run Anywhere (WORA), static typing, JVM/JRE/JDK architecture, Garbage Collection, Multithreading, and OOP principles.",
    example: "public class Palindrome {\n    public static boolean isPalindrome(String s) {\n        return new StringBuilder(s).reverse().toString().equalsIgnoreCase(s);\n    }\n}",
    interview_tip: "Explain Bytecode, Heap vs Stack memory, Garbage Collection algorithms, and enterprise frameworks like Spring Boot.",
  },
  javascript: {
    title: "JavaScript (ECMAScript)",
    definition: "JavaScript is a high-level, single-threaded, non-blocking asynchronous language powering modern web applications.",
    key_concepts: "Event Loop, Call Stack, Microtask vs Macrotask Queue, Closures, Prototypal inheritance, Promises & Async/Await.",
    example: "const fetchUser = async (id) => {\n  const res = await fetch(`/api/user/${id}`);\n  return res.json();\n};",
    interview_tip: "Be ready to explain the Event Loop with Microtasks (Promises) vs Macrotasks (setTimeout) and Closures.",
  },
  react: {
    title: "React.js",
    definition: "React is a declarative, component-based JavaScript library developed by Meta for building dynamic user interfaces.",
    key_concepts: "Virtual DOM, JSX, Uni-directional data flow, Hooks (useState, useEffect, useMemo, useCallback), and Component Lifecycle.",
    example: "function Counter() {\n  const [count, setCount] = React.useState(0);\n  return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;\n}",
    interview_tip: "Explain Virtual DOM diffing reconciliation, key props in lists, and memoization using useMemo/useCallback.",
  },
  sql: {
    title: "SQL & Relational Databases",
    definition: "SQL (Structured Query Language) is the domain-specific language for storing, querying, and managing relational databases.",
    key_concepts: "DDL vs DML, JOINs (INNER, LEFT, RIGHT), GROUP BY & HAVING, Indexing (B-Trees), Normalization (1NF-3NF), ACID transactions.",
    example: "SELECT name, salary FROM employees\nWHERE salary = (SELECT MAX(salary) FROM employees WHERE salary < (SELECT MAX(salary) FROM employees));",
    interview_tip: "Master writing Nth highest salary queries, understanding Index performance tradeoffs, and explaining ACID properties.",
  },
  dbms: {
    title: "Database Management Systems (DBMS)",
    definition: "DBMS is software used to store, organize, retrieve, and secure database assets while ensuring data consistency.",
    key_concepts: "ACID Properties (Atomicity, Consistency, Isolation, Durability), Primary/Foreign Keys, Normalization (1NF to BCNF), and Indexing.",
    example: "ACID in Banking: Debit from Account A and Credit to Account B must both succeed together (Atomicity) without dirty reads (Isolation).",
    interview_tip: "Always illustrate ACID properties using a banking fund transfer example.",
  },
  oop: {
    title: "Object-Oriented Programming (OOP)",
    definition: "OOP is a programming paradigm structured around data objects and classes, encapsulating state and behavior.",
    key_concepts: "1. Encapsulation (data hiding)\n2. Abstraction (hiding implementation details)\n3. Inheritance (code reusability)\n4. Polymorphism (overloading & overriding)",
    example: "class Animal:\n    def speak(self):\n        pass\n\nclass Dog(Animal):\n    def speak(self):\n        return 'Woof!'",
    interview_tip: "Recite the 4 pillars immediately with real-world analogies (e.g. Car accelerator for Abstraction, Private balance for Encapsulation).",
  },
};

function resolveClientKnowledge(query, mode = "general") {
  const q = query.toLowerCase().trim();

  // Search topic dictionary
  for (const [key, data] of Object.entries(CLIENT_KNOWLEDGE)) {
    if (q.includes(key)) {
      return `### 📘 ${data.title}\n\n` +
        `**Definition:**\n${data.definition}\n\n` +
        `**Key Concepts:**\n${data.key_concepts}\n\n` +
        `**Code Example:**\n\`\`\`${key}\n${data.example}\n\`\`\`\n\n` +
        `💡 **Interview Tip:**\n${data.interview_tip}`;
    }
  }

  // Greetings
  if (/^(hi|hello|hey|who are you|what can you do)/i.test(q)) {
    return "👋 **Hello! I am MAX – Your AI Voice & Interview Assistant.**\n\n" +
      "I can help you with:\n" +
      "• **Technical Concepts:** Python, Java, JavaScript, React, SQL, OOP, DBMS, Cloud\n" +
      "• **Coding & Algorithms:** Logic explanations, debugging, and syntax\n" +
      "• **Interview Prep:** Technical Q&A, HR STAR method, and Project Defense\n\n" +
      "Try asking: *'What is Python?'*, *'Explain React Virtual DOM'*, or *'What is SQL?'*";
  }

  // HR / Self introduction
  if (q.includes("tell me about yourself") || q.includes("introduce yourself")) {
    return "### 🎯 How to answer: 'Tell me about yourself'\n\n" +
      "Use the **Present - Past - Future** framework:\n\n" +
      "1. **Present:** State your current role, primary programming skills, and core strengths.\n" +
      "2. **Past:** Highlight key academic achievements, certifications, or major technical projects.\n" +
      "3. **Future:** Express genuine enthusiasm for the role and explain how your skillset adds value.";
  }

  // General structured AI response
  return `### 💡 MAX Analysis for: *"${query}"*\n\n` +
    `1. **Core Concept:** In computer science and software engineering, understanding fundamental principles and system design is essential.\n` +
    `2. **Key Consideration:** Prioritize clean code architecture, optimal time & space complexity, and modular scalability.\n` +
    `3. **Interview Recommendation:** Clearly structure your thought process and write clean, testable code.\n\n` +
    `Feel free to ask a specific question like *'What is Python?'* or *'Explain Object Oriented Programming'*!`;
}

// ================= MICROPHONE CAPTURE & RECORDING =================
let speechRecognizer = null;

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  try {
    const recognizer = new SpeechRecognition();
    recognizer.continuous = false;
    recognizer.interimResults = true;
    recognizer.lang = "en-US";

    recognizer.onstart = () => {
      state.isRecording = true;
      setAssistantState("RECORDING", "Listening for your voice...");
    };

    recognizer.onresult = (event) => {
      let interim = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      if (interim && elements.transcriptionBox) {
        elements.transcriptionBox.textContent = `"${interim}"`;
      }

      if (finalTranscript.trim()) {
        const text = finalTranscript.trim();
        appendMessage("user", text);
        submitQuery(text);
      }
    };

    recognizer.onerror = (e) => {
      console.warn("Speech recognition notice:", e.error);
      if (e.error !== "no-speech") {
        setAssistantState("IDLE", "Ready");
      }
    };

    recognizer.onend = () => {
      state.isRecording = false;
      if (state.assistantState === "RECORDING" || state.assistantState === "LISTENING") {
        setAssistantState("IDLE", "Ready");
      }
    };

    return recognizer;
  } catch (e) {
    console.warn("Speech recognition init error:", e);
    return null;
  }
}

async function toggleMicrophone() {
  if (state.isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

async function startRecording() {
  stopSpeaking(); // Stop any active speech

  // Try Web Speech Recognition first for seamless browser voice input
  if (!speechRecognizer) {
    speechRecognizer = initSpeechRecognition();
  }

  if (speechRecognizer) {
    try {
      speechRecognizer.start();
      return;
    } catch (e) {
      console.log("SpeechRecognizer starting fallback media recorder...");
    }
  }

  // Fallback to MediaRecorder
  try {
    if (!state.audioContext) {
      state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (state.audioContext.state === "suspended") {
      await state.audioContext.resume();
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.micStream = stream;

    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 128;
    const source = state.audioContext.createMediaStreamSource(stream);
    source.connect(state.analyser);

    state.audioChunks = [];
    const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/wav";
    state.mediaRecorder = new MediaRecorder(stream, { mimeType });

    state.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        state.audioChunks.push(event.data);
      }
    };

    state.mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(state.audioChunks, { type: mimeType });
      await handleRecordedAudio(audioBlob);
    };

    state.mediaRecorder.start(250);
    state.isRecording = true;
    setAssistantState("RECORDING", "Listening for your voice...");
  } catch (err) {
    console.error("Microphone access error:", err);
    setAssistantState("ERROR", "Microphone access denied or unavailable.");
  }
}

function stopRecording() {
  if (speechRecognizer) {
    try {
      speechRecognizer.stop();
    } catch (e) { }
  }

  if (state.mediaRecorder && state.isRecording) {
    state.isRecording = false;
    state.mediaRecorder.stop();
    if (state.micStream) {
      state.micStream.getTracks().forEach((track) => track.stop());
      state.micStream = null;
    }
    setAssistantState("TRANSCRIBING", "Processing speech...");
  }
}

// Send audio blob to backend for Whisper offline STT
async function handleRecordedAudio(blob) {
  try {
    const formData = new FormData();
    formData.append("file", blob, "input_audio.webm");

    const transcribeRes = await fetch("https://offline-ai-assitant-9.onrender.com/api/transcribe", {
      method: "POST",
      body: formData,
    });

    if (transcribeRes.ok) {
      const transcribeData = await transcribeRes.json();
      const spokenText = transcribeData.text ? transcribeData.text.trim() : "";
      if (spokenText) {
        appendMessage("user", spokenText);
        await submitQuery(spokenText);
        return;
      }
    }
    setAssistantState("IDLE", "Please speak or type your question.");
  } catch (err) {
    console.error("Audio handling error:", err);
    setAssistantState("IDLE", "Ready");
  }
}

// ================= CHAT & REASONING PIPELINE =================
function showThinkingIndicator() {
  removeThinkingIndicator();
  const card = document.createElement("div");
  card.className = "message-card assistant-message thinking-card animate-fade";
  card.id = "assistant-thinking-indicator";

  const avatar = document.createElement("div");
  avatar.className = "avatar max-avatar";
  avatar.setAttribute("aria-hidden", "true");
  const avatarLetter = document.createElement("span");
  avatarLetter.className = "avatar-letter";
  avatarLetter.textContent = "M";
  avatar.appendChild(avatarLetter);

  const contentBox = document.createElement("div");
  contentBox.className = "message-content";

  const sender = document.createElement("div");
  sender.className = "message-sender";
  const senderName = document.createElement("span");
  senderName.className = "sender-name";
  senderName.textContent = "MAX";
  const senderTag = document.createElement("span");
  senderTag.className = "sender-tag";
  senderTag.textContent = "AI Voice Assistant";
  sender.appendChild(senderName);
  sender.appendChild(senderTag);

  const text = document.createElement("div");
  text.className = "message-text thinking-text";
  text.innerHTML = `
    <span class="thinking-label">MAX is thinking...</span>
    <span class="typing-indicator-dots" aria-label="Thinking">
      <span class="dot d1"></span>
      <span class="dot d2"></span>
      <span class="dot d3"></span>
    </span>
  `;

  contentBox.appendChild(sender);
  contentBox.appendChild(text);
  card.appendChild(avatar);
  card.appendChild(contentBox);

  elements.chatMessages.appendChild(card);
  elements.chatMessages.scrollTo({
    top: elements.chatMessages.scrollHeight,
    behavior: "smooth",
  });
}

function removeThinkingIndicator() {
  const existing = document.getElementById("assistant-thinking-indicator");
  if (existing) {
    existing.remove();
  }
}

async function submitQuery(text) {
  const queryText = text.trim();
  if (!queryText) return;

  setAssistantState("THINKING", "Processing your query...");
  showThinkingIndicator();

  const selectedMode = elements.modeSelect ? elements.modeSelect.value : "general";
  const selectedProject = elements.projectSelect ? elements.projectSelect.value : "payroll";
  const savedApiKey = localStorage.getItem("gemini_api_key") || "";

  let assistantReply = "";
  let audioBase64 = null;

  try {
    const res = await fetch("https://offline-ai-assitant-9.onrender.com/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: queryText,
        conversation_id: state.conversationId,
        speak: true,
        mode: selectedMode,
        project_id: selectedProject,
        api_key: savedApiKey,
      }),
    });

    if (res.ok) {
      const data = await res.json();
      assistantReply = data.response;
      audioBase64 = data.audio_base64;
    } else {
      // API fallback
      assistantReply = resolveClientKnowledge(queryText, selectedMode);
    }
  } catch (err) {
    console.warn("Backend API unreachable, using smart client fallback:", err);
    assistantReply = resolveClientKnowledge(queryText, selectedMode);
  }

  removeThinkingIndicator();

  if (!assistantReply) {
    assistantReply = resolveClientKnowledge(queryText, selectedMode);
  }

  // Append assistant card
  appendMessage("assistant", assistantReply);

  // Play synthesized audio
  if (audioBase64) {
    playBase64Audio(audioBase64);
  } else {
    // Speak using browser SpeechSynthesis
    fallbackBrowserSpeak(assistantReply.replace(/[*#`_]/g, "").slice(0, 300));
  }
}

// ================= AUDIO PLAYBACK & INTERRUPTION =================
function playBase64Audio(base64Data) {
  stopSpeaking(); // Cancel any existing playback

  try {
    const audioUrl = `data:audio/wav;base64,${base64Data}`;
    const audio = new Audio(audioUrl);
    state.currentAudioPlayer = audio;
    state.isPlayingAudio = true;

    // Connect Web Audio analyser for reactive visualizer
    if (state.audioContext) {
      try {
        const source = state.audioContext.createMediaElementSource(audio);
        if (!state.analyser) {
          state.analyser = state.audioContext.createAnalyser();
          state.analyser.fftSize = 128;
        }
        source.connect(state.analyser);
        state.analyser.connect(state.audioContext.destination);
      } catch (e) {
        // Fallback standard destination
      }
    }

    setAssistantState("SPEAKING", "MAX is speaking...");

    audio.onended = () => {
      state.isPlayingAudio = false;
      state.currentAudioPlayer = null;
      setAssistantState("IDLE", "Ready");
    };

    audio.onerror = (e) => {
      console.warn("Audio playback error:", e);
      state.isPlayingAudio = false;
      setAssistantState("IDLE", "Ready");
    };

    audio.play().catch((err) => {
      console.warn("Autoplay prevented:", err);
      state.isPlayingAudio = false;
      setAssistantState("IDLE", "Ready");
    });
  } catch (err) {
    console.error("Audio setup error:", err);
    setAssistantState("IDLE", "Ready");
  }
}

function stopSpeaking() {
  if (state.currentAudioPlayer) {
    try {
      state.currentAudioPlayer.pause();
      state.currentAudioPlayer.currentTime = 0;
    } catch (e) { }
    state.currentAudioPlayer = null;
  }
  state.isPlayingAudio = false;

  // Signal backend to abort sounddevice / audio buffer
  const res = await fetch("https://offline-ai-assitant-9.onrender.com/api/speak", { method: "POST" }).catch(() => { });

  if (state.assistantState === "SPEAKING") {
    setAssistantState("IDLE", "Playback stopped.");
  }
}

// ================= CONVERSATION HISTORY & MESSAGE CARDS =================

// Speak a message via /api/speak (backend TTS) or browser SpeechSynthesis fallback
async function speakMessageText(text, btn) {
  if (!text || !text.trim()) return;

  const resetButton = () => {
    btn.classList.remove("speaking-now");
    btn.innerHTML = '🔊 <span>Speak</span>';
    btn.disabled = false;
  };

  btn.classList.add("speaking-now");
  btn.innerHTML = '🔊 <span>Playing...</span><span class="speak-wave-indicator" aria-hidden="true"><span></span><span></span><span></span></span>';
  btn.disabled = true;

  try {
    const res = await fetch("https://offline-ai-assitant-9.onrender.com/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      state.currentAudioPlayer = audio;
      setAssistantState("SPEAKING", "MAX is speaking...");

      audio.onended = () => {
        URL.revokeObjectURL(url);
        state.currentAudioPlayer = null;
        setAssistantState("IDLE", "Ready");
        resetButton();
      };

      audio.onerror = () => {
        state.currentAudioPlayer = null;
        resetButton();
        setAssistantState("IDLE", "Ready");
      };

      audio.play().catch(() => {
        fallbackBrowserSpeak(text, btn, resetButton);
      });
    } else {
      // Fallback: browser Web Speech API
      fallbackBrowserSpeak(text, btn, resetButton);
    }
  } catch (e) {
    fallbackBrowserSpeak(text, btn, resetButton);
  }
}

function fallbackBrowserSpeak(text, btn, onFinish) {
  if (!window.speechSynthesis) {
    if (onFinish) onFinish();
    return;
  }
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 1.0;
  utter.pitch = 1.0;
  utter.onend = () => {
    if (onFinish) onFinish();
    setAssistantState("IDLE", "Ready");
  };
  utter.onerror = () => {
    if (onFinish) onFinish();
    setAssistantState("IDLE", "Ready");
  };
  setAssistantState("SPEAKING", "MAX is speaking...");
  window.speechSynthesis.speak(utter);
}

function appendMessage(role, content) {
  const card = document.createElement("div");
  card.className = `message-card ${role === "user" ? "user-message" : "assistant-message"}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${role === "user" ? "user-avatar" : "max-avatar"}`;
  avatar.setAttribute("aria-hidden", "true");
  const avatarLetter = document.createElement("span");
  avatarLetter.className = "avatar-letter";
  avatarLetter.textContent = role === "user" ? "U" : "M";
  avatar.appendChild(avatarLetter);

  const contentBox = document.createElement("div");
  contentBox.className = "message-content";

  const sender = document.createElement("div");
  sender.className = "message-sender";

  const senderName = document.createElement("span");
  senderName.className = "sender-name";
  senderName.textContent = role === "user" ? "You" : "MAX";
  sender.appendChild(senderName);

  if (role === "assistant") {
    const senderTag = document.createElement("span");
    senderTag.className = "sender-tag";
    senderTag.textContent = "AI Voice Assistant";
    sender.appendChild(senderTag);
  }

  // Timestamp
  const timeTag = document.createElement("span");
  timeTag.className = "msg-timestamp";
  const now = new Date();
  timeTag.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  sender.appendChild(timeTag);

  const text = document.createElement("div");
  text.className = "message-text";

  // 🔊 Speak button
  const speakBtn = document.createElement("button");
  speakBtn.className = "msg-speak-btn";
  speakBtn.innerHTML = '🔊 <span>Speak</span>';
  speakBtn.title = "Click to hear MAX read this message";
  speakBtn.setAttribute("aria-label", "Speak this message");
  speakBtn.addEventListener("click", () => speakMessageText(content, speakBtn));

  const meta = document.createElement("div");
  meta.className = "message-meta";
  if (role === "assistant") {
    meta.innerHTML = '<span class="meta-dot"></span> Offline Inference &bull; 100% Private';
  } else {
    meta.innerHTML = '<span class="meta-dot user-dot"></span> Local Speech / Input';
  }
  meta.appendChild(speakBtn);

  contentBox.appendChild(sender);
  contentBox.appendChild(text);
  contentBox.appendChild(meta);

  card.appendChild(avatar);
  card.appendChild(contentBox);

  elements.chatMessages.appendChild(card);

  // Typewriter effect for assistant messages, instant for user
  if (role === "assistant") {
    let i = 0;
    const speed = 15; // ms per character
    const cursor = document.createElement("span");
    cursor.className = "typing-cursor";
    cursor.textContent = "▋";
    text.appendChild(cursor);

    function typeChar() {
      if (i < content.length) {
        cursor.before(document.createTextNode(content[i]));
        i++;
        elements.chatMessages.scrollTo({ top: elements.chatMessages.scrollHeight, behavior: "smooth" });
        setTimeout(typeChar, speed);
      } else {
        cursor.remove();
      }
    }
    typeChar();
  } else {
    text.textContent = content;
  }

  // Auto-scroll smoothly to newest message
  elements.chatMessages.scrollTo({
    top: elements.chatMessages.scrollHeight,
    behavior: "smooth",
  });
}

async function loadConversationHistory() {
  try {
    const res = await fetch(`https://offline-ai-assitant-9.onrender.com/api/conversations?conversation_id=${state.conversationId}`);
    if (res.ok) {
      const data = await res.json();
      if (data.messages && data.messages.length > 0) {
        elements.chatMessages.innerHTML = "";
        data.messages.forEach((msg) => {
          appendMessage(msg.role, msg.content);
        });
      }
    }
  } catch (err) {
    console.warn("Could not load history:", err);
  }
}

async function clearConversation() {
  try {
    await fetch(`/api/conversations?conversation_id=${state.conversationId}`, {
      method: "DELETE",
    });
    elements.chatMessages.innerHTML = `
      <div class="message-card assistant-message animate-fade">
        <div class="avatar max-avatar" aria-hidden="true">
          <span class="avatar-letter">M</span>
        </div>
        <div class="message-content">
          <div class="message-sender">
            <span class="sender-name">MAX</span>
            <span class="sender-tag">AI Voice Assistant</span>
          </div>
          <div class="message-text">Conversation history cleared. Ready for your next query.</div>
          <div class="message-meta">
            <span class="meta-dot"></span> Offline Memory Reset
            <button class="msg-speak-btn" title="Click to hear MAX read this message" aria-label="Speak this message">
              🔊 <span>Speak</span>
            </button>
          </div>
        </div>
      </div>
    `;
    bindStaticSpeakButtons();
    setAssistantState("IDLE", "Conversation cleared.");
  } catch (err) {
    console.error("Clear conversation error:", err);
  }
}

// Bind click event to any static or dynamically inserted speak buttons
function bindStaticSpeakButtons() {
  document.querySelectorAll("#chat-messages .msg-speak-btn").forEach((btn) => {
    if (!btn.dataset.bound) {
      btn.dataset.bound = "true";
      btn.addEventListener("click", () => {
        const card = btn.closest(".message-card");
        const textEl = card ? card.querySelector(".message-text") : null;
        if (textEl) {
          speakMessageText(textEl.textContent.trim(), btn);
        }
      });
    }
  });
}

// ================= EVENT LISTENERS & SHORTCUTS =================
function setupEventListeners() {
  // Center mic button
  if (elements.micBtn) {
    elements.micBtn.addEventListener("click", toggleMicrophone);
  }

  // Floating input mic button
  if (elements.inputMicBtn) {
    elements.inputMicBtn.addEventListener("click", toggleMicrophone);
  }

  // Stop speaking button
  if (elements.stopSpeakingBtn) {
    elements.stopSpeakingBtn.addEventListener("click", stopSpeaking);
  }

  // Bind initial welcome card speak button
  bindStaticSpeakButtons();

  // 🧠 Think Mode Toggle Button
  if (elements.thinkToggleBtn) {
    elements.thinkToggleBtn.addEventListener("click", () => {
      state.isDeepThinking = !state.isDeepThinking;
      elements.thinkToggleBtn.classList.toggle("active", state.isDeepThinking);
      if (state.isDeepThinking) {
        if (elements.modeSelect && elements.modeSelect.value === "general") {
          elements.modeSelect.value = "technical";
        }
      }
    });
  }

  // Message input typing, auto-resize, Enter sending & mode switching
  if (elements.chatInput && elements.sendBtn) {
    const updateComposerMode = () => {
      elements.chatInput.style.height = "auto";
      const newHeight = Math.min(elements.chatInput.scrollHeight, 120);
      elements.chatInput.style.height = `${newHeight}px`;

      const hasText = elements.chatInput.value.trim().length > 0;
      const hasAttachment = !!state.currentAttachment;
      const shouldSend = hasText || hasAttachment;

      if (shouldSend) {
        elements.sendBtn.classList.remove("mode-voice");
        elements.sendBtn.classList.add("mode-send");
        elements.sendBtn.title = "Send message (Enter)";
        elements.sendBtn.setAttribute("aria-label", "Send message");
      } else {
        elements.sendBtn.classList.remove("mode-send");
        elements.sendBtn.classList.add("mode-voice");
        elements.sendBtn.title = "Voice Input";
        elements.sendBtn.setAttribute("aria-label", "Voice Input");
      }
    };

    elements.chatInput.addEventListener("input", updateComposerMode);

    // Enter sends message, Shift+Enter creates a new line
    elements.chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const hasText = elements.chatInput.value.trim().length > 0;
        const hasAttachment = !!state.currentAttachment;
        if ((hasText || hasAttachment) && elements.chatForm) {
          elements.chatForm.dispatchEvent(new Event("submit", { cancelable: true }));
        }
      }
    });

    elements.chatInput.addEventListener("focus", () => {
      elements.chatInput.placeholder = elements.chatInput.dataset.placeholderFocus || "Type a message...";
    });

    elements.chatInput.addEventListener("blur", () => {
      elements.chatInput.placeholder = elements.chatInput.dataset.placeholderDefault || "Type a message...";
    });

    // Circular Blue Voice/Send button click
    elements.sendBtn.addEventListener("click", (e) => {
      if (elements.sendBtn.classList.contains("mode-voice")) {
        e.preventDefault();
        toggleMicrophone();
      } else if (elements.sendBtn.classList.contains("mode-send") && elements.chatForm) {
        e.preventDefault();
        elements.chatForm.dispatchEvent(new Event("submit", { cancelable: true }));
      }
    });
  }

  // Attachment Button & Input Events
  if (elements.attachBtn && elements.attachmentInput) {
    elements.attachBtn.addEventListener("click", () => {
      elements.attachmentInput.click();
    });

    elements.attachmentInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) {
        state.currentAttachment = file;
        if (elements.attachmentName) elements.attachmentName.textContent = file.name;
        if (elements.attachmentPreview) elements.attachmentPreview.classList.remove("hidden");
        if (elements.sendBtn) {
          elements.sendBtn.classList.remove("mode-voice");
          elements.sendBtn.classList.add("mode-send");
          elements.sendBtn.title = "Send message (Enter)";
        }
      }
    });
  }

  // Remove attachment button
  if (elements.removeAttachmentBtn) {
    elements.removeAttachmentBtn.addEventListener("click", () => {
      state.currentAttachment = null;
      if (elements.attachmentInput) elements.attachmentInput.value = "";
      if (elements.attachmentPreview) elements.attachmentPreview.classList.add("hidden");
      const hasText = elements.chatInput && elements.chatInput.value.trim().length > 0;
      if (elements.sendBtn) {
        if (hasText) {
          elements.sendBtn.classList.remove("mode-voice");
          elements.sendBtn.classList.add("mode-send");
        } else {
          elements.sendBtn.classList.remove("mode-send");
          elements.sendBtn.classList.add("mode-voice");
        }
      }
    });
  }

  // Text input form submission
  if (elements.chatForm) {
    elements.chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = elements.chatInput.value.trim();
      const attached = state.currentAttachment;

      if (!text && !attached) return;

      let displayText = text;
      let queryText = text;

      if (attached) {
        displayText = text ? `📎 [Attached: ${attached.name}]\n${text}` : `📎 [Attached: ${attached.name}]`;
        queryText = text ? `[Attached File: ${attached.name}]\n${text}` : `Please analyze the attached file: ${attached.name}`;

        // If text-like file, read content excerpt
        if (
          attached.type.startsWith("text/") ||
          attached.name.endsWith(".txt") ||
          attached.name.endsWith(".py") ||
          attached.name.endsWith(".js") ||
          attached.name.endsWith(".json") ||
          attached.name.endsWith(".md")
        ) {
          try {
            const fileContent = await attached.text();
            if (fileContent) {
              queryText += `\n\n--- Content of ${attached.name} ---\n${fileContent.slice(0, 3000)}`;
            }
          } catch (err) { }
        }
      }

      // Add user's message as a new chat bubble in the conversation
      appendMessage("user", displayText);

      // Clear the input and reset height after sending
      elements.chatInput.value = "";
      elements.chatInput.style.height = "auto";
      elements.chatInput.placeholder = elements.chatInput.dataset.placeholderDefault || "Type a message...";

      // Reset send button back to voice mode
      elements.sendBtn.classList.remove("mode-send");
      elements.sendBtn.classList.add("mode-voice");
      elements.sendBtn.title = "Voice Input";

      // Reset attachment
      state.currentAttachment = null;
      if (elements.attachmentInput) elements.attachmentInput.value = "";
      if (elements.attachmentPreview) elements.attachmentPreview.classList.add("hidden");

      // Send to existing AI backend
      submitQuery(queryText);
    });
  }

  // Clear chat button
  if (elements.clearChatBtn) {
    elements.clearChatBtn.addEventListener("click", clearConversation);
  }

  // Quick Command Chips
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const cmd = chip.getAttribute("data-cmd");
      if (cmd) {
        appendMessage("user", cmd);
        submitQuery(cmd);
      }
    });
  });

  // Settings Modal Controls
  if (elements.settingsBtn) {
    elements.settingsBtn.addEventListener("click", () => {
      fetchSystemStatus();
      const geminiEl = document.getElementById("gemini-api-key-input");
      if (geminiEl) {
        geminiEl.value = localStorage.getItem("gemini_api_key") || "";
      }
      if (elements.settingsModal) elements.settingsModal.classList.remove("hidden");
    });
  }

  if (elements.closeModalBtn) {
    elements.closeModalBtn.addEventListener("click", () => {
      if (elements.settingsModal) elements.settingsModal.classList.add("hidden");
    });
  }

  if (elements.saveSettingsBtn) {
    elements.saveSettingsBtn.addEventListener("click", async () => {
      const whisperEl = document.getElementById("whisper-model-select");
      const ollamaEl = document.getElementById("ollama-model-input");
      const wakeEl = document.getElementById("wake-word-toggle");
      const geminiEl = document.getElementById("gemini-api-key-input");

      const whisperModel = whisperEl ? whisperEl.value : "base";
      const ollamaModel = ollamaEl ? ollamaEl.value : "llama3.2";
      const wakeWord = wakeEl ? wakeEl.checked : false;

      if (geminiEl) {
        localStorage.setItem("gemini_api_key", geminiEl.value.trim());
      }

      try {
        await fetch("https://offline-ai-assitant-9.onrender.com/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            whisper_model: whisperModel,
            ollama_model: ollamaModel,
            wake_word_enabled: wakeWord,
          }),
        });
      } catch (e) { }

      if (elements.settingsModal) elements.settingsModal.classList.add("hidden");
      fetchSystemStatus();
    });
  }

  // Keyboard Accessibility Shortcuts
  window.addEventListener("keydown", (e) => {
    // Spacebar toggles mic when not focused in an input or select
    const isTyping =
      document.activeElement === elements.chatInput ||
      document.activeElement?.tagName === "INPUT" ||
      document.activeElement?.tagName === "SELECT" ||
      document.activeElement?.tagName === "TEXTAREA";

    if (e.code === "Space" && !isTyping) {
      e.preventDefault();
      toggleMicrophone();
    }

    // Escape stops active audio playback
    if (e.code === "Escape") {
      stopSpeaking();
    }
  });
}

// Run startup sequence on page load
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  initStartup();
});
