"""
MAX Offline Voice-Based AI Assistant
Safe Local Command Execution with Strict Allowlist
"""

import os
import sys
import subprocess
import logging
import random
from datetime import datetime
from typing import Dict, Any, Callable
from backend.audio.player import audio_player
from backend.memory.database import memory_db

logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Executes safe local system actions and utility queries using a strict allowlist.
    Prevents arbitrary code execution and unauthorized shell commands.
    """

    ALLOWED_PROGRAMS = {
        "calculator": ["calc.exe"] if sys.platform == "win32" else ["gnome-calculator"],
        "notepad": ["notepad.exe"] if sys.platform == "win32" else ["gedit"],
        "explorer": ["explorer.exe"] if sys.platform == "win32" else ["nautilus"],
    }

    JOKES = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the Python programmer wear glasses? Because they couldn't C#!",
        "There are 10 types of people in the world: those who understand binary, and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
        "Why was the computer cold? It left its Windows open!",
    ]

    def __init__(self):
        # Register allowlisted actions
        self._handlers: Dict[str, Callable[[], Dict[str, Any]]] = {
            "get_time": self._handle_get_time,
            "get_date": self._handle_get_date,
            "open_calculator": self._handle_open_calculator,
            "open_notepad": self._handle_open_notepad,
            "open_explorer": self._handle_open_explorer,
            "clear_conversation": self._handle_clear_conversation,
            "stop_speaking": self._handle_stop_speaking,
            "tell_joke": self._handle_tell_joke,
        }

    def execute_command(self, action: str, conversation_id: str = "default") -> Dict[str, Any]:
        """
        Execute an action only if it exists in the explicit allowlist.
        """
        if action not in self._handlers:
            logger.warning(f"Rejected unapproved command action: '{action}'")
            return {
                "success": False,
                "action": action,
                "message": f"Action '{action}' is not in the allowed local command registry.",
                "should_speak": True,
            }

        try:
            if action == "clear_conversation":
                return self._handle_clear_conversation(conversation_id)
            return self._handlers[action]()
        except Exception as e:
            logger.error(f"Error executing command '{action}': {e}")
            return {
                "success": False,
                "action": action,
                "message": f"Could not complete {action}: {str(e)}",
                "should_speak": True,
            }

    def _handle_get_time(self) -> Dict[str, Any]:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        return {
            "success": True,
            "action": "get_time",
            "message": f"The current time is {time_str}.",
            "should_speak": True,
        }

    def _handle_get_date(self) -> Dict[str, Any]:
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return {
            "success": True,
            "action": "get_date",
            "message": f"Today is {date_str}.",
            "should_speak": True,
        }

    def _handle_open_calculator(self) -> Dict[str, Any]:
        cmd = self.ALLOWED_PROGRAMS["calculator"]
        subprocess.Popen(cmd, shell=False)
        return {
            "success": True,
            "action": "open_calculator",
            "message": "Opening Calculator.",
            "should_speak": True,
        }

    def _handle_open_notepad(self) -> Dict[str, Any]:
        cmd = self.ALLOWED_PROGRAMS["notepad"]
        subprocess.Popen(cmd, shell=False)
        return {
            "success": True,
            "action": "open_notepad",
            "message": "Opening Notepad.",
            "should_speak": True,
        }

    def _handle_open_explorer(self) -> Dict[str, Any]:
        cmd = self.ALLOWED_PROGRAMS["explorer"]
        subprocess.Popen(cmd, shell=False)
        return {
            "success": True,
            "action": "open_explorer",
            "message": "Opening File Explorer.",
            "should_speak": True,
        }

    def _handle_clear_conversation(self, conversation_id: str = "default") -> Dict[str, Any]:
        memory_db.clear_conversation(conversation_id)
        return {
            "success": True,
            "action": "clear_conversation",
            "message": "Conversation history has been cleared.",
            "should_speak": True,
        }

    def _handle_stop_speaking(self) -> Dict[str, Any]:
        audio_player.stop()
        return {
            "success": True,
            "action": "stop_speaking",
            "message": "Playback stopped.",
            "should_speak": False,
        }

    def _handle_tell_joke(self) -> Dict[str, Any]:
        joke = random.choice(self.JOKES)
        return {
            "success": True,
            "action": "tell_joke",
            "message": joke,
            "should_speak": True,
        }


command_handler = CommandHandler()
