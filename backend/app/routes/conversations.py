"""
Conversation streaming endpoints for AI-powered chat.

Provides SSE streaming endpoint for real-time AI responses with tool use.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import Thread, Project
from app.utils.jwt import get_current_user
from app.services.ai_service import AIService
from app.services.conversation_service import (
    save_message,
    build_conversation_context,
    get_message_count
)

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat message."""
    content: str = Field(..., min_length=1, max_length=32000)


async def validate_thread_access(
    db: AsyncSession,
    thread_id: str,
    user_id: str
) -> Thread:
    """
    Validate thread exists and belongs to user's project.

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

    Accepts user message, saves to database, streams AI response via SSE.
    AI can use tools (document search) and maintains conversation context.

    SSE Events:
    - text_delta: Incremental text from AI
    - tool_executing: AI is executing a tool
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

    # Save user message to database
    await save_message(db, thread_id, "user", body.content)

    # Build conversation context from thread history
    conversation = await build_conversation_context(db, thread_id)

    # Initialize AI service
    ai_service = AIService()

    async def event_generator():
        """Generate SSE events from AI response."""
        accumulated_text = ""
        usage_data = None

        try:
            async for event in ai_service.stream_chat(
                conversation,
                thread.project_id,
                db
            ):
                # Check for client disconnect
                if await request.is_disconnected():
                    break

                # Track accumulated text for saving
                if event["event"] == "text_delta":
                    data = json.loads(event["data"])
                    accumulated_text += data.get("text", "")

                # Track usage for token tracking
                if event["event"] == "message_complete":
                    data = json.loads(event["data"])
                    usage_data = data.get("usage", {})
                    accumulated_text = data.get("content", accumulated_text)

                yield event

            # Save assistant message after streaming completes
            if accumulated_text:
                await save_message(db, thread_id, "assistant", accumulated_text)

            # TODO: Track token usage (Plan 02)
            # TODO: Update thread summary (Plan 02)

        except Exception as e:
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
