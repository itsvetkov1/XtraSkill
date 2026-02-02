"""Unit tests for conversation_service database functions."""

import pytest
from datetime import datetime, timedelta
from app.services.conversation_service import (
    save_message,
    build_conversation_context,
    get_message_count,
)
from app.models import Thread, Message, User, Project


class TestSaveMessage:
    """Tests for save_message function."""

    @pytest.mark.asyncio
    async def test_creates_message_with_correct_attributes(self, db_session, user):
        """Message is created with provided role and content."""
        # Create user and thread in DB
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-1", user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        message = await save_message(db_session, thread.id, "user", "Hello world")

        assert message.thread_id == thread.id
        assert message.role == "user"
        assert message.content == "Hello world"
        assert message.id is not None

    @pytest.mark.asyncio
    async def test_updates_thread_timestamp(self, db_session, user):
        """Saving message updates thread's updated_at timestamp."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-2", user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        original_updated_at = thread.updated_at

        # Small delay to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.1)

        await save_message(db_session, thread.id, "user", "New message")
        await db_session.refresh(thread)

        assert thread.updated_at >= original_updated_at

    @pytest.mark.asyncio
    async def test_assistant_role_saved(self, db_session, user):
        """Assistant messages are saved correctly."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-3", user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        message = await save_message(db_session, thread.id, "assistant", "Response")

        assert message.role == "assistant"


class TestBuildConversationContext:
    """Tests for build_conversation_context function."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_new_thread(self, db_session, user):
        """New thread with no messages returns empty list."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-4", user_id=user.id, title="Empty")
        db_session.add(thread)
        await db_session.commit()

        context = await build_conversation_context(db_session, thread.id)

        assert context == []

    @pytest.mark.asyncio
    async def test_returns_messages_in_chronological_order(self, db_session, user):
        """Messages are returned in chronological order."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-5", user_id=user.id, title="Ordered")
        db_session.add(thread)
        await db_session.commit()

        # Create messages with explicit ordering
        msg1 = Message(
            thread_id=thread.id,
            role="user",
            content="First",
            created_at=datetime.utcnow() - timedelta(minutes=2)
        )
        msg2 = Message(
            thread_id=thread.id,
            role="assistant",
            content="Second",
            created_at=datetime.utcnow() - timedelta(minutes=1)
        )
        msg3 = Message(
            thread_id=thread.id,
            role="user",
            content="Third",
            created_at=datetime.utcnow()
        )
        db_session.add_all([msg1, msg2, msg3])
        await db_session.commit()

        context = await build_conversation_context(db_session, thread.id)

        assert len(context) == 3
        assert context[0]["content"] == "First"
        assert context[1]["content"] == "Second"
        assert context[2]["content"] == "Third"

    @pytest.mark.asyncio
    async def test_returns_claude_message_format(self, db_session, user):
        """Messages are converted to Claude API format."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-6", user_id=user.id, title="Format")
        db_session.add(thread)
        await db_session.commit()

        msg = Message(thread_id=thread.id, role="user", content="Hello")
        db_session.add(msg)
        await db_session.commit()

        context = await build_conversation_context(db_session, thread.id)

        assert context[0] == {"role": "user", "content": "Hello"}


class TestGetMessageCount:
    """Tests for get_message_count function."""

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_thread(self, db_session, user):
        """Empty thread returns count of 0."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-7", user_id=user.id, title="Empty")
        db_session.add(thread)
        await db_session.commit()

        count = await get_message_count(db_session, thread.id)

        assert count == 0

    @pytest.mark.asyncio
    async def test_returns_correct_count(self, db_session, user):
        """Returns correct message count for thread."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(id="test-thread-8", user_id=user.id, title="Count")
        db_session.add(thread)
        await db_session.commit()

        for i in range(5):
            msg = Message(thread_id=thread.id, role="user", content=f"Msg {i}")
            db_session.add(msg)
        await db_session.commit()

        count = await get_message_count(db_session, thread.id)

        assert count == 5

    @pytest.mark.asyncio
    async def test_counts_only_thread_messages(self, db_session, user):
        """Only counts messages in specified thread."""
        db_session.add(user)
        await db_session.commit()

        thread1 = Thread(id="test-thread-9a", user_id=user.id, title="Thread 1")
        thread2 = Thread(id="test-thread-9b", user_id=user.id, title="Thread 2")
        db_session.add_all([thread1, thread2])
        await db_session.commit()

        # Add messages to both threads
        for _ in range(3):
            db_session.add(Message(thread_id=thread1.id, role="user", content="T1"))
        for _ in range(7):
            db_session.add(Message(thread_id=thread2.id, role="user", content="T2"))
        await db_session.commit()

        assert await get_message_count(db_session, thread1.id) == 3
        assert await get_message_count(db_session, thread2.id) == 7
