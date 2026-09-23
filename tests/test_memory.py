"""
Unit Tests for MAX SQLite Conversation Memory
"""

import pytest
from backend.memory.database import MemoryDatabase


@pytest.fixture
def temp_db():
    db = MemoryDatabase(db_path=":memory:")
    yield db
    db.close()


def test_conversation_creation_and_messages(temp_db):
    conv_id = temp_db.get_or_create_conversation("test_thread", "Test Conversation")
    assert conv_id == "test_thread"

    # Add user message
    msg1 = temp_db.add_message(conv_id, "user", "What is Python?")
    assert msg1.id is not None
    assert msg1.role == "user"
    assert msg1.content == "What is Python?"

    # Add assistant response
    msg2 = temp_db.add_message(conv_id, "assistant", "Python is a programming language.")
    assert msg2.id is not None
    assert msg2.role == "assistant"

    # Fetch messages
    messages = temp_db.get_messages(conv_id)
    assert len(messages) == 2
    assert messages[0]["content"] == "What is Python?"
    assert messages[1]["content"] == "Python is a programming language."


def test_recent_context_extraction(temp_db):
    conv_id = "context_test"
    temp_db.get_or_create_conversation(conv_id)

    # Insert 4 turns (8 messages)
    for i in range(4):
        temp_db.add_message(conv_id, "user", f"Question {i}")
        temp_db.add_message(conv_id, "assistant", f"Answer {i}")

    # Extract recent context limit 4
    context = temp_db.get_recent_context(conv_id, max_messages=4)
    assert len(context) == 4
    assert context[0]["content"] == "Question 2"
    assert context[-1]["content"] == "Answer 3"


def test_clear_conversation(temp_db):
    conv_id = "clear_test"
    temp_db.get_or_create_conversation(conv_id)
    temp_db.add_message(conv_id, "user", "Hello")
    assert len(temp_db.get_messages(conv_id)) == 1

    temp_db.clear_conversation(conv_id)
    assert len(temp_db.get_messages(conv_id)) == 0
