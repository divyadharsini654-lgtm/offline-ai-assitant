"""
MAX Offline Voice-Based AI Assistant
Project Knowledge Base & Local Document Manager
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECTS_DIR = PROJECT_ROOT / "data" / "projects"

# Pre-packaged Default Project Profiles
DEFAULT_PROJECT_PROFILES = {
    "payroll": {
        "id": "payroll",
        "title": "MERN Stack Payroll Management System",
        "short_name": "Payroll Management System",
        "category": "Full Stack / MERN",
        "overview": "A web-based payroll management system built using the MERN stack (MongoDB, Express.js, React.js, Node.js) to automate employee salary calculation, tax deductions, bonuses, and payslip generation.",
        "problem_solved": "Eliminates manual errors in payroll processing, automates tax and deduction calculations, provides role-based access control (Admin vs Employee), and generates downloadable digital payslips.",
        "technologies": [
            "MongoDB (NoSQL Database)",
            "Express.js (Backend Framework)",
            "React.js (Frontend UI)",
            "Node.js (Runtime Environment)",
            "JWT (JSON Web Tokens for Auth)",
            "Tailwind CSS / Glassmorphism UI",
            "PDFKit / HTML2PDF for Payslip Generation"
        ],
        "key_features": [
            "Secure User & Employee Authentication (JWT + BCrypt)",
            "Employee Profile & Salary Tier Management",
            "Automated Monthly Salary Calculation with Tax/PF Deductions",
            "Bonus & Overtime Calculation Engine",
            "Instant PDF Payslip Generation & Download",
            "Interactive Dashboard for Admin with Salary Analytics Charts"
        ],
        "role": "Full Stack Developer. Responsible for designing database schemas in MongoDB, developing RESTful APIs in Node.js/Express, creating React dashboard components, and implementing JWT security.",
        "challenges": [
            "Handling complex tax tier logic accurately across different employee levels.",
            "Ensuring transactional consistency during bulk salary processing.",
            "Optimizing MongoDB queries for fast report generation."
        ],
        "advantages": "Fully automated, reduces payroll processing time by 80%, secure role-based access, transparent payslip access for employees.",
        "limitations": "Currently supports single-currency (INR/USD) and requires internet connectivity for cloud MongoDB deployment unless run locally.",
        "future_scope": "Adding multi-currency support, automated email payslip delivery, direct bank API integration, and AI-driven attendance tracking."
    },
    "smart_helmet": {
        "id": "smart_helmet",
        "title": "AI Smart Helmet for Rider Safety",
        "short_name": "AI Smart Helmet",
        "category": "IoT / Embedded AI",
        "overview": "An intelligent IoT and AI-enabled smart helmet designed to prevent motorcycle accidents by ensuring the rider wears a helmet, detecting alcohol consumption, detecting crashes in real-time, and sending automated emergency GPS location alerts.",
        "problem_solved": "Reduces motorcycle fatalities by preventing riding without a helmet or while intoxicated, and ensures immediate emergency response during accidents.",
        "technologies": [
            "Arduino / ESP32 Microcontroller",
            "MQ-3 Alcohol Sensor",
            "IR / Pressure Sensors for Helmet Detection",
            "MPU6050 Accelerometer & Gyroscope for Impact Detection",
            "Neo-6M GPS Module for Real-time Location",
            "SIM800L GSM Module for Emergency SMS Alerts",
            "Python / Edge AI Model for Fall/Crash Verification"
        ],
        "key_features": [
            "Engine Ignition Lock: Bike engine starts ONLY if helmet is worn and rider is sober.",
            "Alcohol Sensing: MQ-3 sensor cuts ignition if alcohol concentration exceeds threshold.",
            "Real-time Crash Detection: Accelerometer detects severe impacts and sudden falls.",
            "Emergency SOS Alerts: Automatically sends SMS with exact Google Maps location to emergency contacts.",
            "Solar Auxiliary Charging: Solar panel mounted on helmet for extended battery backup."
        ],
        "role": "Embedded Systems & Hardware Integration Developer. Assembled hardware modules, wrote micro-controller firmware in C++, integrated GPS/GSM protocols, and developed fall detection threshold algorithm.",
        "challenges": [
            "Calibrating accelerometer thresholds to distinguish between accidental helmet drops and actual crashes.",
            "Minimizing battery consumption while maintaining active GPS signal."
        ],
        "advantages": "Automated life-saving intervention, zero rider effort required, real-time emergency notifications.",
        "limitations": "Requires GSM network coverage to send SMS alerts during accidents in remote areas.",
        "future_scope": "Integrating HUD (Heads-Up Display) for navigation, Bluetooth intercom for hands-free calls, and camera-based obstacle warning."
    }
}


class ProjectKnowledgeManager:
    """Manages project documentation and candidate project profiles for interview preparation."""

    def __init__(self):
        self.projects_dir = PROJECTS_DIR
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.profiles = dict(DEFAULT_PROJECT_PROFILES)
        self._load_local_project_files()

    def _load_local_project_files(self):
        """Load JSON/Markdown project files from data/projects directory."""
        try:
            for file_path in self.projects_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "id" in data:
                            self.profiles[data["id"]] = data
                except Exception as e:
                    logger.warning(f"Could not load project file {file_path}: {e}")

            for file_path in self.projects_dir.glob("*.md"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        proj_id = file_path.stem.lower().replace(" ", "_")
                        self.profiles[proj_id] = {
                            "id": proj_id,
                            "title": file_path.stem.replace("_", " ").title(),
                            "short_name": file_path.stem,
                            "overview": content[:500],
                            "full_text": content,
                        }
                except Exception as e:
                    logger.warning(f"Could not load markdown project file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading projects directory: {e}")

    def list_projects(self) -> List[Dict[str, str]]:
        """Return list of available projects for UI selection."""
        return [
            {
                "id": pid,
                "title": p.get("title", pid),
                "category": p.get("category", "General"),
            }
            for pid, p in self.profiles.items()
        ]

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve profile by ID or search term."""
        pid_lower = project_id.lower()
        for pid, profile in self.profiles.items():
            if pid_lower in pid.lower() or pid_lower in profile.get("title", "").lower() or pid_lower in profile.get("short_name", "").lower():
                return profile
        # Default to first profile if not found
        return list(self.profiles.values())[0] if self.profiles else None

    def match_project_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Determine if a query is asking about a specific project profile."""
        q_lower = query.lower()
        if "smart helmet" in q_lower or "helmet" in q_lower:
            return self.profiles.get("smart_helmet")
        if "payroll" in q_lower or "mern" in q_lower or "salary management" in q_lower:
            return self.profiles.get("payroll")
        
        for pid, profile in self.profiles.items():
            if pid in q_lower or profile.get("title", "").lower() in q_lower:
                return profile
        return None

    def format_project_answer(self, query: str, project_id: Optional[str] = None) -> str:
        """Generate a natural interview answer for a project query."""
        project = self.get_project(project_id or "") if project_id else self.match_project_query(query)
        if not project:
            project = self.profiles.get("payroll")

        q_lower = query.lower()
        title = project.get("title", "My Project")

        # Specific Question Handling
        if any(k in q_lower for k in ["problem", "solve", "why built", "purpose"]):
            return (
                f"### Problem Solved by {title}\n\n"
                f"**Problem:** {project.get('problem_solved', 'Automating manual workflows and increasing efficiency.')}\n\n"
                f"**Key Advantage:** {project.get('advantages', 'Provides real-time automation and accuracy.')}"
            )

        if any(k in q_lower for k in ["technology", "technologies", "tech stack", "tools"]):
            techs = project.get("technologies", [])
            tech_list = "\n".join([f"- {t}" for t in techs]) if isinstance(techs, list) else str(techs)
            return (
                f"### Tech Stack for {title}\n\n"
                f"{tech_list}\n\n"
                f"**Reason for choice:** Chosen for scalability, modularity, and rapid development."
            )

        if any(k in q_lower for k in ["role", "contribution", "your role", "what did you do"]):
            return (
                f"### My Role in {title}\n\n"
                f"{project.get('role', 'Developed core modules and integrated key features.')}"
            )

        if any(k in q_lower for k in ["challenge", "difficult", "obstacle", "problem faced"]):
            challenges = project.get("challenges", [])
            ch_list = "\n".join([f"- {c}" for c in challenges]) if isinstance(challenges, list) else str(challenges)
            return (
                f"### Key Challenges & Solutions in {title}\n\n"
                f"{ch_list}"
            )

        if any(k in q_lower for k in ["limitation", "drawback", "disadvantage"]):
            return (
                f"### Limitations of {title}\n\n"
                f"{project.get('limitations', 'Currently requires local configuration and specific network connectivity.')}\n\n"
                f"**Future Scope:** {project.get('future_scope', 'Expanding system integration and adding cloud features.')}"
            )

        if any(k in q_lower for k in ["future", "scope", "improvement"]):
            return (
                f"### Future Scope for {title}\n\n"
                f"{project.get('future_scope', 'Adding automated analytics and cloud synchronization.')}"
            )

        # General Project Overview (Interview Pitch)
        features = project.get("key_features", [])
        feat_list = "\n".join([f"- {f}" for f in features]) if isinstance(features, list) else str(features)
        techs = project.get("technologies", [])
        tech_str = ", ".join(techs) if isinstance(techs, list) else str(techs)

        return (
            f"### Project Interview Pitch: {title}\n\n"
            f"**Overview:**\n{project.get('overview', '')}\n\n"
            f"**Tech Stack:** {tech_str}\n\n"
            f"**Key Features:**\n{feat_list}\n\n"
            f"**My Role:**\n{project.get('role', '')}\n\n"
            f"**Interview Tip:** When explaining this in an interview, start with the 30-second elevator pitch (Overview + Tech Stack), then highlight your specific contribution."
        )


project_knowledge = ProjectKnowledgeManager()
