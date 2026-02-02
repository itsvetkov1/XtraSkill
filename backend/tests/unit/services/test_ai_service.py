"""Unit tests for ai_service AIService."""

import pytest
import json
from app.services.ai_service import AIService, stream_with_heartbeat
from app.models import Thread, Project, Document, Artifact, ArtifactType
from app.services.llm.base import StreamChunk
from tests.fixtures.llm_fixtures import MockLLMAdapter


class TestAIServiceExecuteTool:
    """Tests for AIService.execute_tool method."""

    @pytest.mark.asyncio
    async def test_save_artifact_creates_artifact(self, db_session, user):
        """save_artifact tool creates artifact in database."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(user_id=user.id, title="Test Thread")
        db_session.add(thread)
        await db_session.commit()

        service = AIService()

        result, event_data = await service.execute_tool(
            tool_name="save_artifact",
            tool_input={
                "artifact_type": "requirements_doc",
                "title": "Test BRD",
                "content_markdown": "# Business Requirements\n\nTest content."
            },
            project_id=None,
            thread_id=thread.id,
            db=db_session
        )

        # Verify artifact created
        assert "saved successfully" in result
        assert event_data is not None
        assert event_data["title"] == "Test BRD"
        assert event_data["artifact_type"] == "requirements_doc"

        # Verify persisted in DB
        from sqlalchemy import select
        stmt = select(Artifact).where(Artifact.thread_id == thread.id)
        db_result = await db_session.execute(stmt)
        artifact = db_result.scalar_one()
        assert artifact.title == "Test BRD"
        assert artifact.artifact_type == ArtifactType.REQUIREMENTS_DOC

    @pytest.mark.asyncio
    async def test_search_documents_returns_results(self, db_session, user):
        """search_documents tool returns formatted document results."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test Project")
        db_session.add(project)
        await db_session.commit()

        # Create and index a document
        doc = Document(
            project_id=project.id,
            filename="requirements.md",
            content_encrypted=b"encrypted"
        )
        db_session.add(doc)
        await db_session.commit()

        # Index document content
        from app.services.document_search import index_document
        await index_document(db_session, doc.id, doc.filename, "Login authentication requirements")
        await db_session.commit()

        service = AIService()

        result, event_data = await service.execute_tool(
            tool_name="search_documents",
            tool_input={"query": "authentication"},
            project_id=project.id,
            thread_id="thread-id",
            db=db_session
        )

        assert event_data is None  # No event for search
        assert "requirements.md" in result
        # Check for highlighted terms (** around matched words)
        assert "**" in result or "authentication" in result.lower()

    @pytest.mark.asyncio
    async def test_search_documents_empty_results(self, db_session, user):
        """search_documents returns message when no results."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Empty Project")
        db_session.add(project)
        await db_session.commit()

        service = AIService()

        result, event_data = await service.execute_tool(
            tool_name="search_documents",
            tool_input={"query": "nonexistent"},
            project_id=project.id,
            thread_id="thread-id",
            db=db_session
        )

        assert "No relevant documents" in result
        assert event_data is None

    @pytest.mark.asyncio
    async def test_search_documents_no_project(self, db_session):
        """search_documents returns empty for no project_id."""
        service = AIService()

        result, event_data = await service.execute_tool(
            tool_name="search_documents",
            tool_input={"query": "test"},
            project_id=None,
            thread_id="thread-id",
            db=db_session
        )

        assert "No relevant documents" in result
        assert event_data is None

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, db_session):
        """Unknown tool name returns error message."""
        service = AIService()

        result, event_data = await service.execute_tool(
            tool_name="unknown_tool",
            tool_input={},
            project_id=None,
            thread_id="thread-id",
            db=db_session
        )

        assert "Unknown tool" in result
        assert event_data is None


class TestAIServiceStreamChat:
    """Tests for AIService.stream_chat method."""

    @pytest.mark.asyncio
    async def test_yields_text_events(self, db_session, user, mock_llm_adapter):
        """Streaming yields text_delta events."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        # Create service with mock adapter
        adapter = mock_llm_adapter(responses=["Hello", " world", "!"])
        service = AIService.__new__(AIService)
        service.adapter = adapter
        service.tools = []

        events = []
        async for event in service.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id=None,
            thread_id=thread.id,
            db=db_session
        ):
            events.append(event)

        # Should have text_delta events
        text_events = [e for e in events if e.get("event") == "text_delta"]
        assert len(text_events) == 3

        # Parse data from events
        texts = [json.loads(e["data"])["text"] for e in text_events]
        assert texts == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_yields_message_complete(self, db_session, user, mock_llm_adapter):
        """Streaming ends with message_complete event."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        adapter = mock_llm_adapter(responses=["Response"])
        service = AIService.__new__(AIService)
        service.adapter = adapter
        service.tools = []

        events = []
        async for event in service.stream_chat(
            messages=[{"role": "user", "content": "Test"}],
            project_id=None,
            thread_id=thread.id,
            db=db_session
        ):
            events.append(event)

        # Last event should be message_complete
        assert events[-1]["event"] == "message_complete"
        data = json.loads(events[-1]["data"])
        assert "content" in data
        assert "usage" in data

    @pytest.mark.asyncio
    async def test_records_call_history(self, db_session, user, mock_llm_adapter):
        """MockLLMAdapter records call for verification."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        adapter = mock_llm_adapter(responses=["OK"])
        service = AIService.__new__(AIService)
        service.adapter = adapter
        service.tools = []

        messages = [{"role": "user", "content": "Test message"}]
        async for _ in service.stream_chat(messages, None, thread.id, db_session):
            pass

        # Verify call was recorded
        assert len(adapter.call_history) == 1
        assert adapter.call_history[0]["messages"] == messages

    @pytest.mark.asyncio
    async def test_handles_error_chunks(self, db_session, user, mock_llm_adapter):
        """Error chunks yield error events."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        adapter = mock_llm_adapter(raise_error="API rate limit exceeded")
        service = AIService.__new__(AIService)
        service.adapter = adapter
        service.tools = []

        events = []
        async for event in service.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id=None,
            thread_id=thread.id,
            db=db_session
        ):
            events.append(event)

        # Should have error event
        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) == 1
        data = json.loads(error_events[0]["data"])
        assert "rate limit" in data["message"]

    @pytest.mark.asyncio
    async def test_tool_execution_in_stream(self, db_session, user):
        """Tool calls are executed and results sent back."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        # First adapter call returns tool call, second returns text after tool result
        call_count = 0

        class ToolThenTextAdapter(MockLLMAdapter):
            async def stream_chat(self, messages, system_prompt, tools=None, max_tokens=4096):
                nonlocal call_count
                self.call_history.append({"messages": messages})
                call_count += 1

                if call_count == 1:
                    yield StreamChunk(chunk_type="tool_use", tool_call={
                        "id": "tool_1",
                        "name": "save_artifact",
                        "input": {
                            "artifact_type": "user_stories",
                            "title": "User Stories",
                            "content_markdown": "# Stories"
                        }
                    })
                    yield StreamChunk(chunk_type="complete", usage={"input_tokens": 10, "output_tokens": 5})
                else:
                    yield StreamChunk(chunk_type="text", content="Artifact saved!")
                    yield StreamChunk(chunk_type="complete", usage={"input_tokens": 15, "output_tokens": 10})

        adapter = ToolThenTextAdapter()
        service = AIService.__new__(AIService)
        service.adapter = adapter
        service.tools = []

        events = []
        async for event in service.stream_chat(
            messages=[{"role": "user", "content": "Create stories"}],
            project_id=None,
            thread_id=thread.id,
            db=db_session
        ):
            events.append(event)

        # Should have tool_executing and artifact_created events
        event_types = [e.get("event") for e in events]
        assert "tool_executing" in event_types
        assert "artifact_created" in event_types


class TestStreamWithHeartbeat:
    """Tests for stream_with_heartbeat function."""

    @pytest.mark.asyncio
    async def test_passes_through_data_events(self):
        """Data events are yielded unchanged."""
        async def data_gen():
            yield {"event": "text_delta", "data": '{"text": "hello"}'}
            yield {"event": "message_complete", "data": "{}"}

        events = []
        async for event in stream_with_heartbeat(data_gen(), initial_delay=10):
            events.append(event)
            if len(events) >= 2:
                break

        assert events[0]["event"] == "text_delta"
        assert events[1]["event"] == "message_complete"

    @pytest.mark.asyncio
    async def test_preserves_event_data_format(self):
        """Events pass through with correct data structure."""
        test_data = {"key": "value", "nested": {"a": 1}}

        async def data_gen():
            yield {"event": "custom", "data": json.dumps(test_data)}

        events = []
        async for event in stream_with_heartbeat(data_gen(), initial_delay=10):
            events.append(event)
            break  # Only need first event

        assert len(events) == 1
        assert events[0]["event"] == "custom"
        parsed = json.loads(events[0]["data"])
        assert parsed == test_data


class TestAIServiceInit:
    """Tests for AIService initialization."""

    def test_creates_with_default_provider(self):
        """Default provider is anthropic."""
        service = AIService()
        assert service.adapter is not None
        assert len(service.tools) == 2  # search_documents, save_artifact

    def test_has_document_search_tool(self):
        """Has document search tool configured."""
        service = AIService()
        tool_names = [t["name"] for t in service.tools]
        assert "search_documents" in tool_names

    def test_has_save_artifact_tool(self):
        """Has save artifact tool configured."""
        service = AIService()
        tool_names = [t["name"] for t in service.tools]
        assert "save_artifact" in tool_names
