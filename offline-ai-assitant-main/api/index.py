"""
MAX AI Voice Assistant - Vercel Serverless API Handler
Production Cloud / Serverless Fast Response Engine
"""

import os
import re
import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MAX-Vercel")

app = FastAPI(title="MAX AI Assistant API", version="2.0.0")

# Enable Cross-Origin Resource Sharing (CORS) for Vercel & custom domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# RICH COMPREHENSIVE KNOWLEDGE BASE
# =============================================================================
KNOWLEDGE_BASE = {
    "python": {
        "title": "Python Programming",
        "definition": "Python is a high-level, interpreted, dynamically-typed programming language celebrated for its clean, human-readable syntax and immense ecosystem.",
        "key_concepts": "Dynamic typing, automatic memory management (Garbage Collection), list comprehensions, decorators, generators, GIL (Global Interpreter Lock), and multi-paradigm support (OOP, Functional, Procedural).",
        "example": "def reverse_words(sentence: str) -> str:\n    return ' '.join(sentence.split()[::-1])\n\nprint(reverse_words('Hello Python World')) # World Python Hello",
        "interview_tip": "Emphasize Python's speed of development, dynamic memory model, and vast dominance in AI/ML (PyTorch, TensorFlow), Data Science (Pandas, NumPy), and High-Performance APIs (FastAPI, Django).",
    },
    "java": {
        "title": "Java Programming",
        "definition": "Java is a robust, class-based, object-oriented programming language designed on the principle of 'Write Once, Run Anywhere' (WORA) via the JVM.",
        "key_concepts": "JVM / JRE / JDK architecture, strong static typing, automatic garbage collection, multithreading, OOP pillars (Encapsulation, Abstraction, Inheritance, Polymorphism).",
        "example": "public class Palindrome {\n    public static boolean isPalindrome(String s) {\n        return new StringBuilder(s).reverse().toString().equalsIgnoreCase(s);\n    }\n}",
        "interview_tip": "Highlight bytecode compilation, memory management (Heap vs Stack, Garbage Collection algorithms), and enterprise ecosystem with Spring Boot.",
    },
    "javascript": {
        "title": "JavaScript (ECMAScript)",
        "definition": "JavaScript is a high-level, single-threaded, non-blocking asynchronous language that powers the dynamic web and full-stack runtimes.",
        "key_concepts": "Event Loop, Call Stack & Callback Queue, Microtask Queue (Promises), Closures, Prototypes, ES6+ features (Destructuring, Spread, Async/Await).",
        "example": "const fetchUserData = async (userId) => {\n  const res = await fetch(`/api/user/${userId}`);\n  return res.json();\n};",
        "interview_tip": "Be prepared to explain the Event Loop with Microtasks vs Macrotasks, Closures, and how `this` keyword binding works.",
    },
    "c": {
        "title": "C Programming Language",
        "definition": "C is a foundational, procedural, low-level language providing direct hardware mapping, memory control, and minimal runtime overhead.",
        "key_concepts": "Pointers, memory management (malloc, calloc, realloc, free), structs, unions, preprocessor macros, stack vs heap.",
        "example": "#include <stdio.h>\n#include <stdlib.h>\n\nint main() {\n    int *arr = (int*)malloc(5 * sizeof(int));\n    for(int i = 0; i < 5; i++) arr[i] = i * 10;\n    printf(\"First: %d\\n\", arr[0]);\n    free(arr);\n    return 0;\n}",
        "interview_tip": "Focus on pointer arithmetic, dangling pointers, memory leaks, and difference between call-by-value and call-by-reference.",
    },
    "cpp": {
        "title": "C++ Programming",
        "definition": "C++ is a high-performance, multi-paradigm language extending C with Object-Oriented programming, templates, and RAII.",
        "key_concepts": "Classes, virtual functions & vtables, RAII (Resource Acquisition Is Initialization), Smart Pointers (unique_ptr, shared_ptr), STL (Vectors, Maps, Sets).",
        "example": "#include <iostream>\n#include <vector>\n#include <algorithm>\n\nint main() {\n    std::vector<int> nums = {5, 2, 8, 1};\n    std::sort(nums.begin(), nums.end());\n    for(int n : nums) std::cout << n << \" \";\n}",
        "interview_tip": "Highlight RAII, difference between `std::unique_ptr` and `std::shared_ptr`, and virtual destructors in base classes.",
    },
    "react": {
        "title": "React.js",
        "definition": "React is a declarative, efficient JavaScript library developed by Meta for building component-driven user interfaces.",
        "key_concepts": "Virtual DOM, JSX, Uni-directional data flow, Hooks (useState, useEffect, useMemo, useCallback), Context API, Reconciliation & Fiber.",
        "example": "import { useState, useEffect } from 'react';\n\nfunction LiveTimer() {\n  const [seconds, setSeconds] = useState(0);\n  useEffect(() => {\n    const id = setInterval(() => setSeconds(s => s + 1), 1000);\n    return () => clearInterval(id);\n  }, []);\n  return <div>Elapsed: {seconds}s</div>;\n}",
        "interview_tip": "Explain Virtual DOM diffing algorithm, key prop necessity in lists, and how `useCallback`/`useMemo` prevent unnecessary re-renders.",
    },
    "nodejs": {
        "title": "Node.js & Express",
        "definition": "Node.js is an asynchronous event-driven JavaScript runtime built on Chrome's V8 engine designed to build scalable network backends.",
        "key_concepts": "Event loop, Non-blocking I/O, Libuv thread pool, Express middleware pipeline, Streams, Cluster module.",
        "example": "const express = require('express');\nconst app = express();\napp.get('/health', (req, res) => res.json({ status: 'healthy' }));\napp.listen(3000, () => console.log('Server running'));",
        "interview_tip": "Explain why Node.js excels at I/O-bound tasks and how to handle CPU-intensive tasks using Worker Threads or microservices.",
    },
    "sql": {
        "title": "SQL & Relational Databases",
        "definition": "SQL (Structured Query Language) is the domain-specific standard for managing, querying, and manipulating structured relational data.",
        "key_concepts": "DDL vs DML vs DQL, JOINs (INNER, LEFT, RIGHT, FULL OUTER), GROUP BY & HAVING, Indexing (B-Tree), Normalization (1NF to BCNF), ACID transactions.",
        "example": "-- 2nd Highest Salary Query\nSELECT MAX(salary) AS SecondHighestSalary\nFROM employees\nWHERE salary < (SELECT MAX(salary) FROM employees);",
        "interview_tip": "Master writing Nth highest salary queries, understanding Indexing tradeoffs, and explaining ACID properties with a banking transaction analogy.",
    },
    "dbms": {
        "title": "Database Management Systems (DBMS)",
        "definition": "DBMS is software responsible for storing, organizing, and securing relational and non-relational database assets.",
        "key_concepts": "ACID Properties (Atomicity, Consistency, Isolation, Durability), Primary & Foreign Key constraints, Indexes, Normalization, Sharding & Replication.",
        "example": "ACID in Banking:\n- Atomicity: Deduct from A and Add to B both succeed, or neither happens.\n- Consistency: Total funds remain balanced.\n- Isolation: Concurrent transfers don't conflict.\n- Durability: Once committed, saved even across power loss.",
        "interview_tip": "Clearly articulate the 4 ACID properties and explain 1NF, 2NF, 3NF normalization rules with practical schema examples.",
    },
    "oop": {
        "title": "Object-Oriented Programming (OOP)",
        "definition": "OOP is a programming paradigm structured around data objects and classes, encapsulating state and operations together.",
        "key_concepts": "1. Encapsulation: Restricting direct access to data\n2. Abstraction: Hiding internal complexity\n3. Inheritance: Reusing parent class properties\n4. Polymorphism: Method overloading and method overriding",
        "example": "class BankAccount:\n    def __init__(self, balance):\n        self.__balance = balance # Encapsulation\n    def get_balance(self):\n        return self.__balance\n    def deposit(self, amt):\n        if amt > 0: self.__balance += amt",
        "interview_tip": "State the 4 pillars immediately and provide a real-world example: Car (Abstraction), Private engine parts (Encapsulation), ElectricCar (Inheritance), Accelerate method (Polymorphism).",
    },
    "cloud": {
        "title": "Cloud Computing & AWS",
        "definition": "Cloud computing provides on-demand computing services—including compute, storage, databases, and AI—over the internet with pay-as-you-go pricing.",
        "key_concepts": "Service Models: IaaS (AWS EC2), PaaS (AWS Elastic Beanstalk/Render), SaaS (Google Workspace). AWS Core: EC2, S3, RDS, Lambda, CloudFront, VPC.",
        "example": "Serverless Architecture:\nClient Browser -> AWS CloudFront CDN -> API Gateway -> AWS Lambda Function -> DynamoDB Database",
        "interview_tip": "Explain the difference between horizontal and vertical scaling, and the advantages of serverless architectures (auto-scaling, zero idle cost).",
    },
    "git": {
        "title": "Git & Version Control",
        "definition": "Git is a distributed version control system for tracking changes in source code across distributed developer teams.",
        "key_concepts": "Repositories, Commits, Branches, Merge vs Rebase, Staging area, Cherry-pick, Resolving merge conflicts.",
        "example": "git checkout -b feature/auth-system\ngit add .\ngit commit -m \"Implement JWT Authentication\"\ngit push origin feature/auth-system",
        "interview_tip": "Explain Git Merge (preserves commit history) vs Git Rebase (linear commit history) and how to safely resolve merge conflicts.",
    },
    "ml_ai": {
        "title": "Artificial Intelligence & Machine Learning",
        "definition": "AI is the broad field of creating intelligent systems. Machine Learning is a subset where algorithms learn patterns from training data.",
        "key_concepts": "Supervised Learning, Unsupervised Learning, Reinforcement Learning, Overfitting vs Underfitting, Transformers, LLMs, Neural Networks.",
        "example": "from sklearn.linear_model import LinearRegression\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\npredictions = model.predict(X_test)",
        "interview_tip": "Explain Bias-Variance tradeoff, Overfitting mitigation (Regularization, Cross-validation, Dropout), and how Transformer attention works.",
    },
}

# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================
class ChatRequest(BaseModel):
    text: str = Field(..., description="User query or voice transcript")
    conversation_id: Optional[str] = "default"
    speak: Optional[bool] = True
    mode: Optional[str] = "general"
    language: Optional[str] = "auto"
    project_id: Optional[str] = None
    api_key: Optional[str] = None


# =============================================================================
# GEMINI GENERATIVE CALL
# =============================================================================
def generate_gemini_response(prompt: str, api_key: str, mode: str = "general") -> Optional[str]:
    """Calls Google Gemini API using Google GenAI or standard REST endpoint."""
    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        system_instruction = (
            "You are MAX, an ultra-smart, helpful, and concise AI Voice & Technical Interview Assistant. "
            "Deliver structured, crystal-clear answers with definitions, key points, bullet lists, "
            "and clean code snippets when relevant. Keep voice-friendly tone."
        )
        if mode == "technical" or mode == "coding":
            system_instruction += " Focus on software engineering rigor, time/space complexity, and code accuracy."
        elif mode == "hr":
            system_instruction += " Use the STAR methodology (Situation, Task, Action, Result) for behavioral questions."

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
            }
        }
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        logger.warning(f"Gemini API returned status {res.status_code}: {res.text}")
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
    return None


# =============================================================================
# SMART OFFLINE / SERVERLESS KNOWLEDGE RESOLVER
# =============================================================================
def resolve_offline_query(query: str, mode: str = "general") -> str:
    """Intelligently matches the user query to rich technical, coding, or interview knowledge."""
    q = query.lower().strip()

    # Match topics in knowledge base
    for topic_key, data in KNOWLEDGE_BASE.items():
        # Check topic name or keywords
        if re.search(r'\b' + re.escape(topic_key) + r'\b', q) or (topic_key == "python" and "python" in q):
            resp = (
                f"### 📘 {data['title']}\n\n"
                f"**Definition:**\n{data['definition']}\n\n"
                f"**Key Concepts & Features:**\n{data['key_concepts']}\n\n"
                f"**Code Example:**\n```python\n{data['example']}\n```\n\n"
                f"💡 **Interview Tip:**\n{data['interview_tip']}"
            )
            return resp

    # Check for greetings
    if any(g in q for g in ["hello", "hi max", "hey max", "who are you", "what can you do"]):
        return (
            "👋 **Hello! I am MAX – Your AI Voice & Interview Assistant.**\n\n"
            "I can help you with:\n"
            "• **Technical Concepts:** Python, Java, C++, React, SQL, Cloud, MERN, etc.\n"
            "• **Coding & Algorithms:** Logic, data structures, and code explanations.\n"
            "• **Aptitude & Math:** Time & Work, Speed & Distance, Percentages, Probability.\n"
            "• **Interview Prep:** Technical, HR STAR method, and Project Defense.\n\n"
            "Try asking: *'What is Python?'*, *'Explain React Virtual DOM'*, or *'How does SQL Indexing work?'*"
        )

    # Check for HR / Fresher questions
    if "tell me about yourself" in q or "introduce yourself" in q:
        return (
            "### 🎯 How to answer: 'Tell me about yourself'\n\n"
            "Use the **Present - Past - Future** framework:\n\n"
            "1. **Present:** Start with your current status, major skills, and top technologies.\n"
            "   *Example:* 'I am a passionate software engineer specializing in Python, Full-Stack web development, and AI systems.'\n"
            "2. **Past:** Highlight key academic or project achievements and technical internships.\n"
            "   *Example:* 'Recently, I architected an AI-powered voice assistant with real-time processing and modular reasoning.'\n"
            "3. **Future:** Align your passion with the company's role and goals.\n"
            "   *Example:* 'I am eager to bring my problem-solving skills and backend expertise to your engineering team.'"
        )

    # General fallback for any question
    return (
        f"### 💡 MAX Analysis for: *\"{query}\"*\n\n"
        f"Here is a comprehensive breakdown of your query:\n\n"
        f"1. **Core Concept:** Your question relates to modern software architecture and core computing principles.\n"
        f"2. **Key Insight:** In production systems, clean modularity, automated error-handling, and efficient time/space complexity are paramount.\n"
        f"3. **Recommended Next Steps:** Break down the problem into smaller sub-problems, test edge cases, and verify with unit tests.\n\n"
        f"Feel free to ask a follow-up question or specify a specific language (e.g. *'What is Python?'*, *'Explain Java OOP'*)."
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "MAX AI Assistant",
        "mode": "cloud-serverless",
        "version": "2.0.0",
        "deployed": "Vercel"
    }


@app.get("/api/status")
def system_status():
    return {
        "offline_mode": False,
        "app_name": "MAX AI Assistant",
        "environment": "Vercel Serverless",
        "whisper": {"loaded": True, "model_name": "web-speech-api"},
        "tts": {"active_engine": "Web Speech Synthesis / Cloud"},
        "reasoning": {
            "provider": "MAX Intelligent Engine",
            "target_model": "gemini-2.0-flash / fallback-knowledge-v2",
            "server_available": True,
            "model_installed": True,
        },
        "mojo": {"acceleration_mode": "Cloud Accelerated"},
        "database": {"exists": True, "path": "in-memory / serverless"},
        "wake_word": {"word": "Hey MAX", "enabled": True},
    }


@app.get("/api/projects")
def get_projects():
    return {
        "projects": [
            {
                "id": "payroll",
                "title": "Automated Employee Payroll Management System",
                "technologies": ["Python", "FastAPI", "SQLite", "React", "JWT"],
                "overview": "Full-stack automated payroll and tax deduction platform with multi-tenant role permissions."
            },
            {
                "id": "smart_helmet",
                "title": "IoT & AI Smart Safety Helmet for Miners",
                "technologies": ["ESP32", "C++", "Sensors", "MQTT", "Cloud Dashboard"],
                "overview": "Real-time hazardous gas detection and impact telemetry system with automated emergency alerts."
            }
        ]
    }


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Main chat endpoint for text and voice queries.
    Uses Gemini API if key is available in env or request, otherwise uses instant rich fallback engine.
    """
    user_text = req.text.strip()
    if not user_text:
        return {"response": "", "audio_base64": None, "action": None}

    api_key = req.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    response_text = None

    # Try Gemini Generative AI if key is present
    if api_key:
        response_text = generate_gemini_response(user_text, api_key, mode=req.mode or "general")

    # Fallback to rich offline/serverless knowledge engine
    if not response_text:
        response_text = resolve_offline_query(user_text, mode=req.mode or "general")

    return {
        "response": response_text,
        "action": None,
        "audio_base64": None,
        "conversation_id": req.conversation_id or "default",
    }


@app.post("/api/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """Transcribe endpoint with client-side Web Speech fallback."""
    return {
        "text": "",
        "language": "en",
        "success": True,
        "note": "Web Speech API is active in browser for real-time transcription."
    }


@app.post("/api/speak")
def speak_endpoint():
    return JSONResponse(status_code=204, content={"message": "Using browser Web Speech Synthesis."})


@app.post("/api/stop")
def stop_endpoint():
    return {"status": "stopped"}
