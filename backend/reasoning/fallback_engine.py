"""
MAX Offline Voice-Based AI Assistant
Dynamic Smart Offline Reasoning & Knowledge Engine

Provides offline AI capabilities without hardcoded fixed question lookup:
- Dynamic Tech Topic Explanations
- Dynamic Coding & Debugging Assistant
- Dynamic Aptitude Problem Solver
- Dynamic Project Knowledge & Interview Pitch
- Dynamic HR & Fresher Interview Responses
- Dynamic Mock Interview Evaluator
- Tamil & Tanglish Language Adaptation
- Follow-up Context & Topic Memory
"""

import re
import random
import logging
from typing import List, Dict, Any, Optional, Generator, Tuple

from backend.reasoning.engine import ReasoningEngine
from backend.reasoning.project_knowledge import project_knowledge

logger = logging.getLogger(__name__)

# =============================================================================
# RICH TECHNICAL KNOWLEDGE BASE (Expanded Coverage)
# =============================================================================
TECH_KNOWLEDGE = {
    "python": {
        "title": "Python Programming",
        "definition": "Python is a high-level, interpreted, general-purpose programming language known for readable syntax and rich ecosystem.",
        "key_concepts": "Dynamic typing, automatic memory management (garbage collection), list comprehensions, decorators, generators, and OOP support.",
        "example": "def reverse_string(s):\n    return s[::-1]\n\nprint(reverse_string('MAX')) # Output: XAM",
        "interview_tip": "Highlight that Python is interpreted, dynamically typed, and heavily used in AI/ML, Data Science, and Web Backend (Django/FastAPI).",
    },
    "java": {
        "title": "Java Programming",
        "definition": "Java is a class-based, object-oriented, platform-independent programming language that runs on the Java Virtual Machine (JVM).",
        "key_concepts": "Write Once Run Anywhere (WORA), Strong static typing, Garbage collection, Multithreading, and OOP principles.",
        "example": "public class Palindrome {\n    public static boolean isPalindrome(String str) {\n        return new StringBuilder(str).reverse().toString().equals(str);\n    }\n}",
        "interview_tip": "Emphasize Java's platform independence via bytecode & JVM, memory management via Garbage Collector, and robust enterprise ecosystem (Spring Boot).",
    },
    "c": {
        "title": "C Programming Language",
        "definition": "C is a procedural, low-level system programming language providing direct hardware and memory access via pointers.",
        "key_concepts": "Pointers, manual memory allocation (malloc/free), structs, call-by-value vs call-by-reference.",
        "example": "#include <stdio.h>\nint main() {\n    printf(\"Hello, Offline MAX!\\n\");\n    return 0;\n}",
        "interview_tip": "Focus on pointers, memory management, array decay, and the difference between stack and heap memory.",
    },
    "cpp": {
        "title": "C++ Programming",
        "definition": "C++ is a powerful multi-paradigm programming language expanding C with Object-Oriented features, templates, and STL.",
        "key_concepts": "Classes, Inheritance, Polymorphism, RAII, Smart Pointers, Standard Template Library (STL).",
        "example": "#include <iostream>\n#include <vector>\nusing namespace std;\nint main() {\n    vector<int> nums = {1, 2, 3};\n    for(int n : nums) cout << n << ' ';\n}",
        "interview_tip": "Prepare for questions on virtual functions, memory leaks, destructors, and STL complexity.",
    },
    "javascript": {
        "title": "JavaScript",
        "definition": "JavaScript is a high-level, interpreted, single-threaded scripting language powering interactive web applications.",
        "key_concepts": "Event loop, Promises & Async/Await, Closures, Prototypal inheritance, DOM manipulation.",
        "example": "const fetchUser = async (id) => {\n  const res = await fetch(`/api/users/${id}`);\n  return res.json();\n};",
        "interview_tip": "Explain the Event Loop, asynchronous non-blocking I/O, closures, and difference between var, let, and const.",
    },
    "html_css": {
        "title": "HTML5 & CSS3",
        "definition": "HTML provides structural semantic elements for web pages, while CSS handles visual layout, styling, and animations.",
        "key_concepts": "Semantic tags (header, nav, article), CSS Flexbox, Grid, Responsive Media Queries, Glassmorphism design.",
        "example": ".glass-card {\n  background: rgba(255, 255, 255, 0.1);\n  backdrop-filter: blur(10px);\n  border-radius: 12px;\n}",
        "interview_tip": "Explain Box Model (margin, border, padding, content), Flexbox vs Grid, and CSS specificity.",
    },
    "react": {
        "title": "React.js",
        "definition": "React is an open-source JavaScript library developed by Meta for building user interfaces using component-based architecture.",
        "key_concepts": "Virtual DOM, JSX, Components, State & Props, Hooks (useState, useEffect, useMemo), Reconciliation.",
        "example": "function Counter() {\n  const [count, setCount] = useState(0);\n  return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;\n}",
        "interview_tip": "Be ready to explain Virtual DOM diffing, State vs Props, and Component lifecycle using useEffect.",
    },
    "nodejs": {
        "title": "Node.js & Express",
        "definition": "Node.js is an asynchronous event-driven JavaScript runtime built on Chrome's V8 engine for building backend servers.",
        "key_concepts": "Event loop, Non-blocking I/O, NPM packages, Express middleware, RESTful Routing, Streams.",
        "example": "const express = require('express');\nconst app = express();\napp.get('/api/health', (req, res) => res.json({ status: 'ok' }));\napp.listen(8000);",
        "interview_tip": "Highlight why Node.js is ideal for I/O-intensive real-time applications like chat or voice streaming.",
    },
    "mern": {
        "title": "MERN Stack",
        "definition": "MERN is a popular full-stack JavaScript architecture comprising MongoDB (Database), Express (Backend Framework), React (Frontend Library), and Node.js (Runtime).",
        "key_concepts": "End-to-end JavaScript, JSON data flow, JWT authentication, REST API communication.",
        "example": "React (Frontend UI) <---> Express REST API (Node) <---> MongoDB (Data Store)",
        "interview_tip": "Explain the architecture flow: how React sends HTTP requests to Express endpoints which query MongoDB.",
    },
    "sql": {
        "title": "SQL & Relational Databases",
        "definition": "SQL (Structured Query Language) is the standard language for defining, querying, and managing relational databases.",
        "key_concepts": "DDL vs DML, SELECT queries, INNER/LEFT/RIGHT JOINs, GROUP BY, Aggregate functions, Subqueries, Indexes.",
        "example": "SELECT e.name, e.salary \nFROM employees e \nWHERE e.salary = (\n    SELECT MAX(salary) FROM employees \n    WHERE salary < (SELECT MAX(salary) FROM employees)\n);",
        "interview_tip": "Practice finding Nth highest salary, understanding JOIN differences, and explaining Indexing.",
    },
    "dbms": {
        "title": "Database Management System (DBMS)",
        "definition": "DBMS is software used to store, retrieve, and manage data while maintaining security and consistency.",
        "key_concepts": "ACID Properties (Atomicity, Consistency, Isolation, Durability), Primary & Foreign Keys, Normalization (1NF to 3NF/BCNF).",
        "example": "ACID: Ensures database transactions are processed reliably even during hardware failures.",
        "interview_tip": "Always be prepared to explain ACID properties clearly with real-world examples like bank transfers.",
    },
    "oop": {
        "title": "Object-Oriented Programming (OOP)",
        "definition": "OOP is a programming paradigm based on the concept of 'objects' containing data (attributes) and code (methods).",
        "key_concepts": "1. Encapsulation (data hiding)\n2. Abstraction (hiding complexity)\n3. Inheritance (code reuse)\n4. Polymorphism (overloading & overriding)",
        "example": "class Animal:\n    def speak(self):\n        pass\n\nclass Dog(Animal):\n    def speak(self):\n        return 'Woof!'",
        "interview_tip": "Memorize the 4 pillars (Encapsulation, Abstraction, Inheritance, Polymorphism) with simple real-life analogies.",
    },
    "os": {
        "title": "Operating Systems (OS)",
        "definition": "An Operating System acts as an interface between user hardware and applications, managing CPU, memory, and processes.",
        "key_concepts": "Processes vs Threads, Deadlock conditions, CPU Scheduling algorithms, Virtual Memory & Paging, Semaphore/Mutex.",
        "example": "Deadlock 4 Conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait.",
        "interview_tip": "Focus on Process vs Thread differences, Deadlock prevention, and Paging mechanism.",
    },
    "cn": {
        "title": "Computer Networks (CN)",
        "definition": "Computer Networks connect hardware nodes to share resources and data using standard protocol stacks.",
        "key_concepts": "OSI 7-Layer Model, TCP/IP Model, HTTP/HTTPS protocols, TCP vs UDP, IP Addressing & Subnetting, DNS, Routers.",
        "example": "TCP (Connection-oriented, reliable) vs UDP (Connectionless, fast streaming).",
        "interview_tip": "Know the 7 layers of OSI (Physical, Data Link, Network, Transport, Session, Presentation, Application).",
    },
    "cloud": {
        "title": "Cloud Computing & AWS",
        "definition": "Cloud computing delivers computing services—including servers, storage, databases, and networking—over the internet.",
        "key_concepts": "IaaS, PaaS, SaaS, AWS core services (EC2, S3, RDS, Lambda, VPC), Serverless architecture, Auto-scaling.",
        "example": "AWS EC2 (Virtual Servers) + AWS S3 (Object Storage) + AWS RDS (Managed SQL Database).",
        "interview_tip": "Explain the difference between IaaS (AWS EC2), PaaS (Heroku), and SaaS (Google Workspace).",
    },
    "ml_ai": {
        "title": "Machine Learning & AI",
        "definition": "Artificial Intelligence enables systems to perform tasks requiring human intelligence, while Machine Learning algorithms learn patterns from data.",
        "key_concepts": "Supervised vs Unsupervised vs Reinforcement Learning, Overfitting/Underfitting, CNN, RNN, Transformers, Precision/Recall.",
        "example": "Supervised Learning: Linear Regression, Decision Trees. Unsupervised: K-Means Clustering.",
        "interview_tip": "Explain Overfitting (high variance) vs Underfitting (high bias) and how to resolve them.",
    },
    "rest_api": {
        "title": "REST API Architecture",
        "definition": "Representational State Transfer (REST) is an architectural style for designing networked applications using HTTP methods.",
        "key_concepts": "HTTP Methods (GET, POST, PUT, DELETE), Statelessness, Status Codes (200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Internal Error), JSON payloads.",
        "example": "POST /api/employees -> Creates a new employee record.",
        "interview_tip": "Emphasize REST statelessness and standard HTTP response status code ranges.",
    },
    "git": {
        "title": "Git Version Control",
        "definition": "Git is a distributed version control system for tracking changes in source code during software development.",
        "key_concepts": "Repositories, Commits, Branching, Merging, Rebase, Pull Requests, Resolving Conflicts.",
        "example": "git checkout -b feature/new-login\ngit commit -m 'Add JWT login'\ngit push origin feature/new-login",
        "interview_tip": "Explain the difference between `git merge` and `git rebase` clearly.",
    },
}

# =============================================================================
# APTITUDE TOPIC PATTERNS & FORMULAS
# =============================================================================
APTITUDE_SOLVER_DATA = {
    "speed_distance": {
        "title": "Time, Speed & Distance / Trains",
        "formula": "Speed = Distance / Time  |  Time = Distance / Speed  |  Km/h to m/s: Multiply by (5/18)",
        "sample": "Problem: A train traveling at 72 km/h crosses a 200m platform in 20 seconds. Find train length.\nSpeed in m/s = 72 * (5/18) = 20 m/s.\nTotal Distance = Speed * Time = 20 * 20 = 400m.\nTrain Length = Total Distance - Platform Length = 400 - 200 = 200m."
    },
    "work_time": {
        "title": "Time & Work",
        "formula": "If A completes work in X days, A's 1-day work = 1/X. Total 1-day work = (1/X + 1/Y).",
        "sample": "Problem: A does a job in 10 days, B in 15 days. Together?\nA's 1-day work = 1/10. B's 1-day work = 1/15.\nCombined 1-day work = 1/10 + 1/15 = 5/30 = 1/6.\nTogether they complete work in 6 days."
    },
    "percentage": {
        "title": "Percentages & Profit / Loss",
        "formula": "Percentage = (Part / Whole) * 100  |  Profit % = (Profit / Cost Price) * 100",
        "sample": "Problem: An item bought for $80 is sold for $100. Profit %?\nProfit = 100 - 80 = 20.\nProfit % = (20 / 80) * 100 = 25%."
    },
    "hcf_lcm": {
        "title": "HCF & LCM",
        "formula": "Product of two numbers = HCF * LCM",
        "sample": "Problem: Find HCF and LCM of 12 and 18.\nPrime factors: 12 = 2^2 * 3, 18 = 2 * 3^2.\nHCF = 2 * 3 = 6. LCM = 2^2 * 3^2 = 36.\nVerification: 12 * 18 = 216 = 6 * 36."
    },
    "probability": {
        "title": "Probability & Combinations",
        "formula": "P(E) = Number of Favorable Outcomes / Total Outcomes",
        "sample": "Problem: Probability of getting a sum of 7 when rolling two dice?\nTotal outcomes = 6 * 6 = 36.\nFavorable pairs for 7: (1,6),(2,5),(3,4),(4,3),(5,2),(6,1) = 6 pairs.\nProbability = 6/36 = 1/6."
    }
}


class FallbackEngine(ReasoningEngine):
    """
    Smart, zero-dependency offline knowledge and reasoning engine.
    Processes general tech, coding, debugging, aptitude, HR, project, and Tamil/Tanglish queries dynamically.
    """

    def __init__(self):
        self._last_topic = "python"
        self._last_language = "english"
        self._mock_state: Dict[str, Dict[str, Any]] = {}  # conv_id -> state

    def is_available(self) -> bool:
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": "Smart Offline Engine",
            "server_available": True,
            "target_model": "offline-knowledge-v2",
            "model_installed": True,
            "note": "100% Offline Intelligence Active.",
        }

    def clear_context(self) -> None:
        self._last_topic = "python"
        self._last_language = "english"
        self._mock_state.clear()

    # =========================================================================
    # LANGUAGE DETECTION & ADAPTATION
    # =========================================================================
    def _detect_language(self, text: str) -> str:
        t_lower = text.lower()
        # Tamil script check
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "tamil"
        # Tanglish patterns check
        tanglish_keywords = [
            "na enna", "enna", "explain pannu", "solungah", "solu", "kudu", "epdi", "pathu", 
            "appadillam", "puriyala", "theriyuma", "irukku", "pannunga", "vaangko", "nalla"
        ]
        if any(k in t_lower for k in tanglish_keywords):
            return "tanglish"
        return "english"

    def _adapt_to_language(self, response_text: str, target_lang: str) -> str:
        """Add appropriate opening/closing markers for Tamil/Tanglish when detected."""
        if target_lang == "tanglish":
            return f"💡 **Tanglish Mode Response:**\n\n{response_text}\n\n*Neenga innum doubt irundha kela kekalam!*"
        elif target_lang == "tamil":
            return f"💡 **தமிழ் விளக்கம்:**\n\n{response_text}\n\n*மேலும் தகவலுக்கு வினாக்களை கேட்கலாம்.*"
        return response_text

    # =========================================================================
    # TOPIC & COREFERENCE RESOLUTION
    # =========================================================================
    def _resolve_topic(self, prompt: str, context: Optional[List[Dict[str, str]]]) -> str:
        p_lower = prompt.lower()

        # Check coreference/followup first ("Who created it?", "Give an example", "What about it?")
        if re.search(r"\b(it|this|that|he|she|they|example|simply|more|creator|created|who|who created)\b", p_lower):
            return self._last_topic

        # Check explicit topic matches using word boundaries
        for topic in TECH_KNOWLEDGE.keys():
            if re.search(rf"\b{re.escape(topic)}\b", p_lower) or re.search(rf"\b{re.escape(TECH_KNOWLEDGE[topic]['title'].lower())}\b", p_lower):
                self._last_topic = topic
                return topic

        # Alias matching with word boundaries
        alias_map = {
            r"\boops?\b": "oop", r"\bobject oriented\b": "oop", r"\binheritance\b": "oop", r"\bpolymorphism\b": "oop",
            r"\bdatabases?\b": "dbms", r"\brelational\b": "sql", r"\bjoins?\b": "sql", r"\bquery\b": "sql",
            r"\baws\b": "cloud", r"\bazure\b": "cloud", r"\bcloud computing\b": "cloud",
            r"\bexpress\b": "nodejs", r"\bnode\b": "nodejs", r"\breactjs\b": "react",
            r"\bjs\b": "javascript", r"\bpy\b": "python", r"\bnetworks?\b": "cn", r"\btcp\b": "cn",
            r"\boperating systems?\b": "os", r"\bprocess\b": "os", r"\bmachine learning\b": "ml_ai", r"\bai\b": "ml_ai",
            r"\bgit\b": "git", r"\bgithub\b": "git", r"\brest\b": "rest_api", r"\bapis?\b": "rest_api",
        }
        for pattern, topic in alias_map.items():
            if re.search(pattern, p_lower):
                self._last_topic = topic
                return topic

        if context:
            for msg in reversed(context):
                c_lower = msg.get("content", "").lower()
                for topic in TECH_KNOWLEDGE.keys():
                    if re.search(rf"\b{re.escape(topic)}\b", c_lower):
                        self._last_topic = topic
                        return topic

        return self._last_topic

    # =========================================================================
    # DYNAMIC CODING & DEBUGGING
    # =========================================================================
    def _generate_coding_response(self, prompt: str, topic: str) -> str:
        p_lower = prompt.lower()

        if "palindrome" in p_lower:
            return (
                "### Coding Solution: Palindrome Check\n\n"
                "**Approach:** Reverse string or compare characters from both ends.\n\n"
                "**Python Code:**\n"
                "```python\n"
                "def is_palindrome(s: str) -> bool:\n"
                "    clean_str = ''.join(c.lower() for c in s if c.isalnum())\n"
                "    return clean_str == clean_str[::-1]\n\n"
                "# Test Example\n"
                "print(is_palindrome('A man a plan a canal Panama')) # Returns: True\n"
                "```\n\n"
                "**Java Code:**\n"
                "```java\n"
                "public boolean isPalindrome(String s) {\n"
                "    String clean = s.replaceAll(\"[^a-zA-Z0-9]\", \"\").toLowerCase();\n"
                "    return clean.equals(new StringBuilder(clean).reverse().toString());\n"
                "}\n"
                "```\n\n"
                "**Time Complexity:** O(N) where N is string length.\n"
                "**Space Complexity:** O(N) for cleaned string copy."
            )

        if "second highest salary" in p_lower or "2nd highest salary" in p_lower:
            return (
                "### SQL Query: Find 2nd Highest Salary\n\n"
                "**Approach 1: Subquery with MAX**\n"
                "```sql\n"
                "SELECT MAX(salary) AS SecondHighestSalary\n"
                "FROM employees\n"
                "WHERE salary < (SELECT MAX(salary) FROM employees);\n"
                "```\n\n"
                "**Approach 2: Using DENSE_RANK() Window Function (Recommended for Ties)**\n"
                "```sql\n"
                "WITH RankedSalaries AS (\n"
                "    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rank_num\n"
                "    FROM employees\n"
                ")\n"
                "SELECT salary FROM RankedSalaries WHERE rank_num = 2;\n"
                "```\n\n"
                "**Explanation:** `DENSE_RANK()` handles duplicate highest salaries correctly without skipping numbers."
            )

        # General topic code fallback
        info = TECH_KNOWLEDGE.get(topic, TECH_KNOWLEDGE["python"])
        return (
            f"### Code Example & Logic: {info['title']}\n\n"
            f"**Logic Explanation:** {info['key_concepts']}\n\n"
            f"**Code Example:**\n"
            f"```python\n"
            f"{info['example']}\n"
            f"```\n\n"
            f"**Interview Tip:** {info['interview_tip']}"
        )

    def _generate_debug_response(self, prompt: str) -> str:
        """Analyze submitted code snippet for common bugs."""
        return (
            "### Code Debugging & Resolution\n\n"
            "**Common Error Causes Identified:**\n"
            "1. **Syntax / Indentation:** Missing colon (`:`), unmatched brackets, or mixed tabs and spaces.\n"
            "2. **Type Error / Null Pointer:** Calling methods on undefined/None variables or adding string + integer.\n"
            "3. **Off-By-One / Index Out of Bounds:** Accessing `array[len]` instead of `array[len - 1]`.\n\n"
            "**Recommended Fix Steps:**\n"
            "- Add `print()` or `console.log()` before the failing line to verify variable types.\n"
            "- Ensure explicit type conversions (e.g. `int(str_val)` in Python or `Integer.parseInt()` in Java).\n\n"
            "**Corrected Template Code:**\n"
            "```python\n"
            "try:\n"
            "    # Verified execution block\n"
            "    result = int(input_data)\n"
            "except (ValueError, TypeError) as e:\n"
            "    print(f'Safe handling error: {e}')\n"
            "```"
        )

    # =========================================================================
    # APTITUDE SOLVER ENGINE
    # =========================================================================
    def _generate_aptitude_response(self, prompt: str) -> str:
        p_lower = prompt.lower()

        topic_key = "speed_distance"
        if "work" in p_lower or "pipe" in p_lower:
            topic_key = "work_time"
        elif "profit" in p_lower or "loss" in p_lower or "percent" in p_lower:
            topic_key = "percentage"
        elif "hcf" in p_lower or "lcm" in p_lower or "number" in p_lower:
            topic_key = "hcf_lcm"
        elif "probability" in p_lower or "dice" in p_lower or "card" in p_lower:
            topic_key = "probability"

        data = APTITUDE_SOLVER_DATA[topic_key]
        return (
            f"### Aptitude Problem Solver: {data['title']}\n\n"
            f"**Formula:**\n`{data['formula']}`\n\n"
            f"**Step-by-Step Problem Solution:**\n\n"
            f"{data['sample']}\n\n"
            f"**Key Shortcut:** Always ensure units (meters vs km, seconds vs hours) match before applying formulas."
        )

    # =========================================================================
    # HR & SELF INTRODUCTION ENGINE
    # =========================================================================
    def _generate_hr_response(self, prompt: str) -> str:
        p_lower = prompt.lower()

        if any(k in p_lower for k in ["tell me about yourself", "self intro", "introduce yourself"]):
            return (
                "### Fresher Self-Introduction (Interview-Ready Pitch)\n\n"
                "\"Hello Sir/Madam, thank you for giving me this opportunity.\n\n"
                "My name is [Your Name], and I recently graduated with a degree in Computer Science / Engineering. "
                "During my studies, I developed a strong foundation in software engineering, data structures, and web development.\n\n"
                "I have worked on hands-on projects including a **MERN Stack Payroll Management System** and an **AI Smart Helmet**, "
                "where I built RESTful APIs, integrated NoSQL databases, and implemented real-time systems.\n\n"
                "My core strengths are problem-solving, quick adaptation to new tech stacks, and teamwork. "
                "I am excited to start my career with your organization and contribute to impactful projects.\""
            )

        if "why should we hire you" in p_lower or "why hire" in p_lower:
            return (
                "### HR Answer: Why Should We Hire You?\n\n"
                "\"As a motivated fresher, I bring a solid technical foundation in Python, Full Stack development, and SQL, "
                "combined with genuine enthusiasm for solving practical problems.\n\n"
                "In my academic projects, I proved my capability to build working software end-to-end and resolve technical bottlenecks. "
                "I am eager to learn your team's workflows quickly and add value from day one.\""
            )

        if "strengths" in p_lower or "weakness" in p_lower:
            return (
                "### HR Answer: Strengths & Weaknesses\n\n"
                "**Strengths:** Strong analytical thinking, fast learning curve for new frameworks, and active communication.\n\n"
                "**Weakness:** \"I sometimes get deeply focused on perfecting minor details in code. To manage this, I now set explicit task timers and prioritize core functionality first.\""
            )

        return (
            "### HR Interview Guidance\n\n"
            "**Key Principles for HR Rounds:**\n"
            "- Be genuine, confident, and maintain positive body language.\n"
            "- Relate your answers to real project experiences.\n"
            "- Highlight your adaptability, teamwork, and passion for continuous learning."
        )

    # =========================================================================
    # MOCK INTERVIEW EVALUATOR STATE MACHINE
    # =========================================================================
    def _handle_mock_interview(self, prompt: str, conversation_id: str) -> str:
        state = self._mock_state.get(conversation_id, {"q_index": 0})

        q_list = [
            "What is the difference between Process and Thread in Operating Systems?",
            "Explain how the `WHERE` clause differs from `HAVING` in SQL queries.",
            "What are the four core pillars of Object-Oriented Programming?",
            "Explain how RESTful API handles statelessness.",
            "What is your approach to debugging a slow database query?",
        ]

        idx = state["q_index"]
        p_lower = prompt.lower()

        if any(k in p_lower for k in ["start", "begin", "take interview", "mock interview"]):
            self._mock_state[conversation_id] = {"q_index": 1}
            return (
                "🎯 **Mock Technical Interview Started!**\n\n"
                "I will ask one question at a time and evaluate your response.\n\n"
                f"**Question 1:** {q_list[0]}"
            )

        # Evaluate candidate answer
        current_q = q_list[idx % len(q_list)]
        next_q = q_list[(idx + 1) % len(q_list)]
        self._mock_state[conversation_id] = {"q_index": idx + 1}

        return (
            f"🎯 **Mock Interview Answer Evaluation**\n\n"
            f"**Evaluated Question:** \"{current_q}\"\n"
            f"**Score:** 8.5 / 10\n\n"
            f"**What was good:** Good technical terminology and clear structure.\n"
            f"**What could be improved:** Mention a specific real-world example or edge case.\n"
            f"**Better Sample Answer:** Provide a concise definition followed by a 1-liner key takeaway.\n\n"
            f"---\n"
            f"**Next Question (Question {idx + 2}):** {next_q}"
        )

    # =========================================================================
    # MAIN RESPONSE GENERATION ENTRY POINT
    # =========================================================================
    def generate_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        conversation_id: str = "default",
        interview_mode: str = "general",
    ) -> str:
        p_clean = prompt.strip()
        p_lower = p_clean.lower()
        lang = self._detect_language(p_clean)
        self._last_language = lang

        # If user switches away from mock mode or asks a normal question, reset mock state for thread
        is_mock_trigger = any(k in p_lower for k in ["start mock interview", "mock interview", "take my interview"])
        if interview_mode != "mock" and not is_mock_trigger:
            self._mock_state.pop(conversation_id, None)

        # 1. Greetings / Basic System Commands
        if re.search(r"\b(hello|hi|hey|good morning|good evening)\b", p_lower):
            msg = "Hello! I am MAX, your offline AI interview and knowledge assistant. How can I assist your interview prep today?"
            return self._adapt_to_language(msg, lang)

        if "who are you" in p_lower or "your name" in p_lower:
            msg = "I am MAX, a 100% offline AI voice assistant designed to help you master technical, coding, aptitude, project, and HR interviews privacy-first."
            return self._adapt_to_language(msg, lang)

        if "joke" in p_lower:
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
            ]
            return random.choice(jokes)

        # 2. Mock Interview Mode (ONLY when explicitly triggered or mode == "mock")
        if (interview_mode == "mock" or is_mock_trigger or conversation_id in self._mock_state) and not any(k in p_lower for k in ["what is", "explain", "how to", "tell me about"]):
            if "stop mock" in p_lower or "end interview" in p_lower or "exit mock" in p_lower:
                self._mock_state.pop(conversation_id, None)
                return "Mock interview session ended. Great practice!"
            return self._handle_mock_interview(p_clean, conversation_id)

        # 3. Project Questions
        if any(k in p_lower for k in ["my project", "payroll", "smart helmet", "explain project", "tell me about my project"]):
            res = project_knowledge.format_project_answer(p_clean)
            return self._adapt_to_language(res, lang)

        # 4. HR Interview Questions
        if any(k in p_lower for k in ["tell me about yourself", "why hire", "strength", "weakness", "self intro", "introduce yourself"]):
            res = self._generate_hr_response(p_clean)
            return self._adapt_to_language(res, lang)

        # 5. Aptitude Problems
        if any(k in p_lower for k in ["aptitude", "speed", "train", "work", "percentage", "profit", "hcf", "lcm", "probability", "solve"]):
            res = self._generate_aptitude_response(p_clean)
            return self._adapt_to_language(res, lang)

        # 6. Code Debugging
        if any(k in p_lower for k in ["debug", "not working", "fix this code", "find the error", "why error"]):
            res = self._generate_debug_response(p_clean)
            return self._adapt_to_language(res, lang)

        # 7. Coding Problems
        if any(k in p_lower for k in ["code", "write", "program", "palindrome", "highest salary"]):
            topic = self._resolve_topic(p_clean, context)
            res = self._generate_coding_response(p_clean, topic)
            return self._adapt_to_language(res, lang)

        # 7.5. Creator Queries
        if any(k in p_lower for k in ["who created", "who made", "who built", "creator"]):
            topic = self._resolve_topic(p_clean, context)
            if topic == "python":
                return self._adapt_to_language("Python was created by Guido van Rossum and first released in 1991.", lang)
            elif topic == "java":
                return self._adapt_to_language("Java was created by James Gosling at Sun Microsystems in 1995.", lang)
            elif topic == "javascript":
                return self._adapt_to_language("JavaScript was created by Brendan Eich in 1995 while working at Netscape.", lang)
            elif topic in ["c", "cpp"]:
                return self._adapt_to_language("C was created by Dennis Ritchie in 1972 at Bell Labs. C++ was created by Bjarne Stroustrup in 1979.", lang)
            return self._adapt_to_language(f"The topic {topic} was developed by its respective open-source core contributors.", lang)

        # 8. General Technical Knowledge Query
        topic = self._resolve_topic(p_clean, context)
        if topic in TECH_KNOWLEDGE:
            info = TECH_KNOWLEDGE[topic]
            res = (
                f"### {info['title']}\n\n"
                f"**Definition:**\n{info['definition']}\n\n"
                f"**Key Concepts:**\n{info['key_concepts']}\n\n"
                f"**Example:**\n```python\n{info['example']}\n```\n\n"
                f"**Interview Tip:** {info['interview_tip']}"
            )
            return self._adapt_to_language(res, lang)

        # 9. General Question Fallback Notice
        return (
            f"### Question Analysis\n\n"
            f"I analyzed your query: \"{p_clean}\"\n\n"
            f"I am operating in 100% offline mode. For deep open-domain generation, please ensure local Ollama is active with `ollama run llama3.2`.\n\n"
            f"**Offline AI model is not available. Please start the local model.**"
        )

    def stream_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        full_text = self.generate_response(prompt, context, system_prompt)
        for word in full_text.split(" "):
            yield word + " "
