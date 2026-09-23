"""
Unit Tests for MAX Safe Command Execution and Allowlist
"""

import pytest
from backend.commands.command_handler import CommandHandler
from backend.reasoning.intent import IntentDetector, IntentType


def test_intent_detection_commands():
    detector = IntentDetector()
    
    # Test time queries
    intent, action, _ = detector.detect_intent("What time is it?")
    assert intent == IntentType.COMMAND
    assert action == "get_time"

    # Test date queries
    intent, action, _ = detector.detect_intent("What is today's date?")
    assert intent == IntentType.COMMAND
    assert action == "get_date"

    # Test apps
    intent, action, _ = detector.detect_intent("Open calculator")
    assert intent == IntentType.COMMAND
    assert action == "open_calculator"

    intent, action, _ = detector.detect_intent("Open notepad")
    assert intent == IntentType.COMMAND
    assert action == "open_notepad"

    # Test joke
    intent, action, _ = detector.detect_intent("Tell me a joke")
    assert intent == IntentType.COMMAND
    assert action == "tell_joke"


def test_intent_detection_chat():
    detector = IntentDetector()
    intent, action, _ = detector.detect_intent("What is Python?")
    assert intent == IntentType.CHAT
    assert action is None

    intent, action, _ = detector.detect_intent("Who created it?")
    assert intent == IntentType.CHAT
    assert action is None


def test_command_handler_allowlist_enforcement():
    handler = CommandHandler()
    
    # Disallowed/malicious commands must be rejected
    res = handler.execute_command("rm -rf /")
    assert res["success"] is False
    assert "not in the allowed" in res["message"]

    res = handler.execute_command("powershell.exe -c dir")
    assert res["success"] is False

    res = handler.execute_command("drop_database")
    assert res["success"] is False


def test_command_handler_safe_utilities():
    handler = CommandHandler()

    time_res = handler.execute_command("get_time")
    assert time_res["success"] is True
    assert "current time is" in time_res["message"]

    date_res = handler.execute_command("get_date")
    assert date_res["success"] is True
    assert "Today is" in date_res["message"]

    joke_res = handler.execute_command("tell_joke")
    assert joke_res["success"] is True
    assert len(joke_res["message"]) > 5
