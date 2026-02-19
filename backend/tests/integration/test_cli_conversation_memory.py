"""Integration test for CLI adapter conversation memory across turns.

This test spawns a REAL Claude CLI subprocess and verifies that the
adapter correctly preserves conversation context across multiple turns.

IMPORTANT: This test incurs real API token costs. It is marked with
@pytest.mark.integration to allow exclusion from regular CI runs.

To run this test explicitly:
    cd backend && ./venv/bin/python -m pytest tests/integration/test_cli_conversation_memory.py -v -m integration

To skip in regular test runs:
    cd backend && ./venv/bin/python -m pytest -m "not integration"
"""
import shutil
import pytest
from unittest.mock import MagicMock


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    shutil.which("claude") is None,
    reason="Claude CLI not installed — integration test requires claude CLI in PATH"
)
async def test_assistant_remembers_fact_across_turns():
    """
    Verify CLI adapter preserves conversation context across 3+ turns.

    Strategy:
    - Turn 1: Casually mention a tech stack fact (natural phrasing, not "remember this")
    - Turn 2: Ask a general follow-up question to build realistic context
    - Turn 3: Ask about the fact from turn 1 WITHOUT repeating it

    This tests REAL conversation memory, not Claude Code memory.md injection.
    The key: do NOT use phrases like "remember this" or "please remember X".
    Claude Code intercepts those and stores them in memory.md — the test
    would pass for the wrong reason.

    The assertion checks that turn 3's response contains "FastAPI" because the
    CLI received the full conversation history (turns 1+2+3) via stdin, so the
    model can reference the tech stack mentioned in turn 1.
    """
    from app.services.llm.claude_cli_adapter import ClaudeCLIAdapter
    from app.services.llm.base import StreamChunk

    # Create adapter — CLI uses its own auth (subscription/OAuth), not api_key
    adapter = ClaudeCLIAdapter(api_key="not-needed")

    # Provide mock context (no real DB operations needed for this test)
    mock_db = MagicMock()
    adapter.set_context(mock_db, project_id="test-proj", thread_id="test-thread")

    system_prompt = "You are a helpful assistant."

    # --- Turn 1: Casual fact mention ---
    turn1_messages = [
        {
            "role": "user",
            "content": (
                "I'm building a project management tool using FastAPI for the backend "
                "and React for the frontend."
            )
        }
    ]

    # Verify format before sending (unit-level check, no API cost)
    turn1_prompt = adapter._convert_messages_to_prompt(turn1_messages)
    assert "Human:" in turn1_prompt
    assert "FastAPI" in turn1_prompt

    # Stream turn 1 and collect response
    turn1_response = ""
    async for chunk in adapter.stream_chat(
        messages=turn1_messages,
        system_prompt=system_prompt,
    ):
        if isinstance(chunk, StreamChunk) and chunk.chunk_type == "text":
            turn1_response += chunk.content

    assert turn1_response, "Turn 1 produced no response"

    # --- Turn 2: Build context naturally ---
    turn2_messages = turn1_messages + [
        {"role": "assistant", "content": turn1_response},
        {
            "role": "user",
            "content": "What are some good database options I should consider for this?"
        }
    ]

    # Verify all messages are in the formatted prompt
    turn2_prompt = adapter._convert_messages_to_prompt(turn2_messages)
    assert "Human:" in turn2_prompt
    assert "Assistant:" in turn2_prompt
    assert "---" in turn2_prompt  # Separator between turns

    # Stream turn 2 and collect response
    turn2_response = ""
    async for chunk in adapter.stream_chat(
        messages=turn2_messages,
        system_prompt=system_prompt,
    ):
        if isinstance(chunk, StreamChunk) and chunk.chunk_type == "text":
            turn2_response += chunk.content

    assert turn2_response, "Turn 2 produced no response"

    # --- Turn 3: Ask about turn 1 fact WITHOUT repeating it ---
    turn3_messages = turn2_messages + [
        {"role": "assistant", "content": turn2_response},
        {
            "role": "user",
            "content": "Which backend framework am I using for this project?"
        }
    ]

    # Verify full 3-turn history is in formatted prompt
    turn3_prompt = adapter._convert_messages_to_prompt(turn3_messages)
    assert turn3_prompt.count("Human:") >= 3  # At least 3 user turns
    assert turn3_prompt.count("Assistant:") >= 2  # At least 2 assistant turns

    # Stream turn 3 and collect response
    turn3_response = ""
    async for chunk in adapter.stream_chat(
        messages=turn3_messages,
        system_prompt=system_prompt,
    ):
        if isinstance(chunk, StreamChunk) and chunk.chunk_type == "text":
            turn3_response += chunk.content

    assert turn3_response, "Turn 3 produced no response"

    # CRITICAL ASSERTION: The model must recall "FastAPI" from turn 1
    # This only works if the full conversation history was sent to the CLI subprocess.
    # If only the last message was sent (old broken behavior), the model would not
    # know what "this project" refers to and could not answer with "FastAPI".
    assert "fastapi" in turn3_response.lower(), (
        f"Turn 3 response did not mention FastAPI (conversation memory failure).\n"
        f"Turn 1: {turn1_messages[-1]['content'][:80]}\n"
        f"Turn 3 question: {turn3_messages[-1]['content']}\n"
        f"Turn 3 response: {turn3_response[:200]}"
    )
