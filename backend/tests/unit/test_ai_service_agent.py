"""Unit tests for AIService agent provider routing.

Tests verify AIService correctly routes to _stream_agent_chat for agent providers
and that tool execution bypasses manual tool loop.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from typing import AsyncGenerator

from app.services.ai_service import AIService
from app.services.llm.base import StreamChunk


# ============================================================================
# Mock Helper Functions
# ============================================================================

async def async_gen(*chunks):
    """Create async generator that yields StreamChunk objects."""
    for chunk in chunks:
        yield chunk


# ============================================================================
# Test Classes
# ============================================================================

class TestAIServiceAgentRouting:
    """Tests for AIService agent provider routing."""

    @patch('app.services.ai_service.LLMFactory')
    def test_agent_provider_detected(self, mock_factory):
        """AIService.is_agent_provider is True for agent adapters."""
        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")

        assert svc.is_agent_provider is True

    @patch('app.services.ai_service.LLMFactory')
    def test_direct_api_provider_not_agent(self, mock_factory):
        """AIService.is_agent_provider is False for direct API adapters."""
        mock_adapter = MagicMock()
        # Direct API adapters don't have is_agent_provider attribute
        mock_adapter.is_agent_provider = False
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="anthropic")

        assert svc.is_agent_provider is False

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_streams_text_as_sse(self, mock_factory, mock_corr_id, mock_logging):
        """Agent adapter text StreamChunk yields text_delta SSE event."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        # Must return the async generator directly, not wrap in AsyncMock
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(chunk_type="text", content="hello"),
            StreamChunk(chunk_type="complete", usage={"input_tokens": 100, "output_tokens": 50})
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify text_delta event
        text_events = [e for e in events if e.get("event") == "text_delta"]
        assert len(text_events) == 1
        assert json.loads(text_events[0]["data"])["text"] == "hello"

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_tool_use_yields_tool_executing(self, mock_factory, mock_corr_id, mock_logging):
        """Agent tool_use StreamChunk yields tool_executing SSE event with status message."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(
                chunk_type="tool_use",
                tool_call={"name": "mcp__ba__search_documents", "input": {"query": "test"}}
            ),
            StreamChunk(chunk_type="complete", usage={"input_tokens": 100, "output_tokens": 50})
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify tool_executing event
        tool_events = [e for e in events if e.get("event") == "tool_executing"]
        assert len(tool_events) == 1
        assert json.loads(tool_events[0]["data"])["status"] == "Searching project documents..."

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_save_artifact_tool_status(self, mock_factory, mock_corr_id, mock_logging):
        """Agent save_artifact tool yields 'Generating artifact...' status."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(
                chunk_type="tool_use",
                tool_call={"name": "mcp__ba__save_artifact", "input": {"title": "Test"}}
            ),
            StreamChunk(chunk_type="complete", usage={"input_tokens": 100, "output_tokens": 50})
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify tool_executing event
        tool_events = [e for e in events if e.get("event") == "tool_executing"]
        assert len(tool_events) == 1
        assert json.loads(tool_events[0]["data"])["status"] == "Generating artifact..."

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_complete_with_documents_used(self, mock_factory, mock_corr_id, mock_logging):
        """Agent complete chunk with documents_used in metadata yields message_complete with source attribution."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(chunk_type="text", content="Based on the documents"),
            StreamChunk(
                chunk_type="complete",
                usage={"input_tokens": 100, "output_tokens": 50},
                metadata={"documents_used": [{"id": "doc-1", "filename": "test.pdf"}]}
            )
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify message_complete includes documents_used
        complete_events = [e for e in events if e.get("event") == "message_complete"]
        assert len(complete_events) == 1
        complete_data = json.loads(complete_events[0]["data"])
        assert "documents_used" in complete_data
        assert len(complete_data["documents_used"]) == 1
        assert complete_data["documents_used"][0]["id"] == "doc-1"

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_error_forwarded(self, mock_factory, mock_corr_id, mock_logging):
        """Agent error chunk yields error SSE event."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(chunk_type="error", error="SDK connection failed")
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify error event
        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) == 1
        assert "SDK connection failed" in json.loads(error_events[0]["data"])["message"]

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_artifact_created_event(self, mock_factory, mock_corr_id, mock_logging):
        """Agent chunk with artifact_created metadata yields artifact_created SSE event."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(
                chunk_type="tool_use",
                metadata={"artifact_created": {"id": "art-123", "title": "Test Artifact"}}
            ),
            StreamChunk(chunk_type="complete", usage={"input_tokens": 100, "output_tokens": 50})
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify artifact_created event
        artifact_events = [e for e in events if e.get("event") == "artifact_created"]
        assert len(artifact_events) == 1
        artifact_data = json.loads(artifact_events[0]["data"])
        assert artifact_data["id"] == "art-123"
        assert artifact_data["title"] == "Test Artifact"

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_no_manual_tool_execution(self, mock_factory, mock_corr_id, mock_logging):
        """Agent provider does not execute tools manually (SDK handles internally)."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(
                chunk_type="tool_use",
                tool_call={"name": "mcp__ba__search_documents", "input": {"query": "test"}}
            ),
            StreamChunk(chunk_type="complete", usage={"input_tokens": 100, "output_tokens": 50})
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        # Mock execute_tool to track if it's called
        svc.execute_tool = AsyncMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify execute_tool was NOT called
        svc.execute_tool.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.services.ai_service.get_logging_service')
    @patch('app.services.ai_service.get_correlation_id')
    @patch('app.services.ai_service.LLMFactory')
    async def test_agent_context_set_on_adapter(self, mock_factory, mock_corr_id, mock_logging):
        """AIService calls adapter.set_context before streaming."""
        mock_logging.return_value = MagicMock()
        mock_corr_id.return_value = "test-correlation-id"

        mock_adapter = MagicMock()
        mock_adapter.is_agent_provider = True
        mock_adapter.provider.value = "claude-code-sdk"
        mock_adapter.model = "claude-sonnet-4-5-20250514"
        mock_adapter.set_context = MagicMock()
        mock_adapter.stream_chat = MagicMock(return_value=async_gen(
            StreamChunk(chunk_type="complete", usage={"input_tokens": 100, "output_tokens": 50})
        ))
        mock_factory.create.return_value = mock_adapter

        svc = AIService(provider="claude-code-sdk")
        mock_db = MagicMock()

        events = []
        async for event in svc.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="proj-1",
            thread_id="thread-1",
            db=mock_db
        ):
            events.append(event)

        # Verify set_context was called with correct params
        mock_adapter.set_context.assert_called_once_with(mock_db, "proj-1", "thread-1")
