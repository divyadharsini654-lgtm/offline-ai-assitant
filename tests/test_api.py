"""
Unit & Integration Tests for MAX FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == "offline"
    assert data["privacy"] == "local-only"


def test_api_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["offline_mode"] is True
    assert "whisper" in data
    assert "tts" in data
    assert "reasoning" in data
    assert "database" in data


def test_api_chat_flow(client):
    # Test conversational query
    payload = {
        "text": "What is Python?",
        "conversation_id": "test_api_thread",
        "speak": False,
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "python" in data["response"].lower()

    # Test followup with pronoun resolution ("Who created it?")
    followup_payload = {
        "text": "Who created it?",
        "conversation_id": "test_api_thread",
        "speak": False,
    }
    followup_res = client.post("/api/chat", json=followup_payload)
    assert followup_res.status_code == 200
    followup_data = followup_res.json()
    assert "guido" in followup_data["response"].lower()


def test_api_command_execution(client):
    payload = {
        "action": "get_time",
        "conversation_id": "test_api_thread",
    }
    response = client.post("/api/command", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "current time is" in data["message"]


def test_api_settings_update(client):
    res = client.get("/api/settings")
    assert res.status_code == 200
    current_settings = res.json()
    assert "whisper_model" in current_settings

    # Update settings
    update_payload = {
        "whisper_model": "tiny",
        "wake_word_enabled": True,
    }
    update_res = client.post("/api/settings", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["settings"]["whisper_model"] == "tiny"
    assert updated_data["settings"]["wake_word_enabled"] is True
