"""
Conversation streaming endpoints for AI-powered chat.

Provides SSE streaming endpoint for real-time AI responses with tool use.
Uses direct Anthropic API for Claude conversations with document search
and artifact generation tools.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import Message, Thread, Project
from app.utils.jwt import get_current_user
from app.services.ai_service import AIService, stream_with_heartbeat
from app.services.conversation_service import (
    save_message,
    build_conversation_context,
    get_message_count
)
from app.services.token_tracking import track_token_usage, check_user_budget
from app.services.summarization_service import maybe_update_summary

# Model name for token tracking (AgentService uses claude-sonnet-4-5-20250514)
AGENT_MODEL = "claude-sonnet-4-5-20250514"

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat message."""
    content: str = Field(..., min_length=1, max_length=32000)
    artifact_generation: bool = Field(default=False)


async def validate_thread_access(
    db: AsyncSession,
    thread_id: str,
    user_id: str
) -> Thread:
    """
    Validate thread exists and belongs to user (directly or via project).

    Supports two ownership models:
    - Project-less threads: thread.user_id matches current user
    - Project threads: thread.project.user_id matches current user

    Returns Thread with project loaded, or raises 404.
    """
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Project-less thread: check direct ownership
    if thread.project_id is None:
        if thread.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
    # Project thread: check project ownership
    else:
        if thread.project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )

    return thread


@router.post("/threads/{thread_id}/chat")
async def stream_chat(
    thread_id: str,
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream AI response for a chat message.

    Uses Claude Agent SDK with business-analyst skill for structured discovery.
    AI follows one-question-at-a-time protocol and can generate BRDs.

    SSE Events:
    - text_delta: Incremental text from AI
    - tool_executing: AI is executing a tool
    - artifact_created: An artifact was generated and saved
    - message_complete: Response complete with usage stats
    - error: Error occurred

    Args:
        thread_id: ID of the thread
        body: Chat message content
        current_user: Authenticated user
        db: Database session

    Returns:
        EventSourceResponse streaming AI response
    """
    # Validate thread access
    thread = await validate_thread_access(db, thread_id, current_user["user_id"])

    # Check user budget before allowing chat
    if not await check_user_budget(db, current_user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly token budget exceeded. Please try again next month."
        )

    # Save user message to database (skip for silent artifact generation)
    if not body.artifact_generation:
        await save_message(db, thread_id, "user", body.content)

    # Update thread activity timestamp
    from datetime import datetime
    thread.last_activity_at = datetime.utcnow()
    await db.commit()

    # Build conversation context from thread history
    conversation = await build_conversation_context(db, thread_id)

    # Append ephemeral instruction for silent generation (in-memory only, NOT persisted)
    if body.artifact_generation:
        conversation.append({
            "role": "user",
            "content": f"{body.content}\n\n"
                       "IMPORTANT: Generate the artifact silently. "
                       "Do not include any conversational text. "
                       "Only call the save_artifact tool and stop."
        })

    # Use thread's bound provider (set at creation time)
    # This ensures consistency - conversations stay with their original provider
    provider = thread.model_provider or "anthropic"
    ai_service = AIService(provider=provider, thread_type=thread.thread_type or "ba_assistant")

    async def event_generator():
        """Generate SSE events from AI response with heartbeat during silence."""
        accumulated_text = ""
        usage_data = None

        try:
            # Create raw stream generator
            raw_stream = ai_service.stream_chat(
                conversation,
                thread.project_id,
                thread_id,
                db,
                artifact_generation=body.artifact_generation
            )

            # Wrap with heartbeat for long thinking periods
            heartbeat_stream = stream_with_heartbeat(raw_stream)

            async for event in heartbeat_stream:
                # Check for client disconnect
                if await request.is_disconnected():
                    break

                # Heartbeat events pass through directly (no accumulation)
                if "comment" in event:
                    yield event
                    continue

                # Suppress text_delta for silent artifact generation
                if body.artifact_generation and event.get("event") == "text_delta":
                    continue  # Skip yielding - frontend doesn't need text for silent mode

                # Track accumulated text for saving (skip for silent mode)
                if not body.artifact_generation and event.get("event") == "text_delta":
                    data = json.loads(event["data"])
                    accumulated_text += data.get("text", "")

                # Track usage for token tracking
                if event.get("event") == "message_complete":
                    data = json.loads(event["data"])
                    usage_data = data.get("usage", {})
                    accumulated_text = data.get("content", accumulated_text)

                yield event

            # Save assistant message after streaming completes (skip for silent generation)
            if accumulated_text and not body.artifact_generation:
                await save_message(db, thread_id, "assistant", accumulated_text)

            # Track token usage
            if usage_data:
                await track_token_usage(
                    db,
                    current_user["user_id"],
                    AGENT_MODEL,
                    usage_data.get("input_tokens", 0),
                    usage_data.get("output_tokens", 0),
                    f"/threads/{thread_id}/chat",
                    thread_type=thread.thread_type or "ba_assistant"
                )

            # Update thread summary (skip for silent generation - no new messages to summarize)
            if not body.artifact_generation:
                await maybe_update_summary(db, thread_id, current_user["user_id"])

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            if body.artifact_generation:
                logger.error(f"Silent artifact generation failed for thread {thread_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }

    return EventSourceResponse(
        event_generator(),
        headers={
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Cache-Control": "no-cache",
        }
    )


@router.delete(
    "/threads/{thread_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_message(
    thread_id: str,
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a single message from a thread.

    Args:
        thread_id: Thread UUID
        message_id: Message UUID
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        404: Thread/message not found or not owned by user
    """
    # First validate thread ownership
    await validate_thread_access(db, thread_id, current_user["user_id"])

    # Query message by ID and thread_id
    stmt = select(Message).where(
        Message.id == message_id,
        Message.thread_id == thread_id
    )
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Delete message
    await db.delete(message)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
