"""
Thread summarization service for AI-generated titles.

Generates concise thread titles based on conversation content.
Updates automatically as conversation progresses.
import logging
logger = logging.getLogger(__name__)
"""
import anthropic
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Thread, Message
from app.config import settings
from app.services.token_tracking import track_token_usage

# Model for summarization (can use faster/cheaper model)
SUMMARY_MODEL = "claude-sonnet-4-5-20250929"

# Update summary every N messages
SUMMARY_INTERVAL = 5

# Max title length
MAX_TITLE_LENGTH = 100


def format_messages_for_summary(messages: List[Dict[str, Any]]) -> str:
    """Format messages for summary prompt."""
    formatted = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, str):
            # Truncate long messages
            if len(content) > 500:
                content = content[:500] + "..."
            formatted.append(f"{role.upper()}: {content}")
    return "\n\n".join(formatted)


async def generate_thread_summary(
    client: anthropic.AsyncAnthropic,
    messages: List[Dict[str, Any]],
    current_title: Optional[str] = None
) -> tuple[str, dict]:
    """
    Generate a concise summary title for a thread.

    Args:
        client: Anthropic client
        messages: Conversation messages
        current_title: Current thread title (if any)

    Returns:
        Tuple of (new_title, usage_dict)
    """
    # Use last 10 messages for context (avoid token explosion)
    recent_messages = messages[-10:] if len(messages) > 10 else messages
    formatted = format_messages_for_summary(recent_messages)

    prompt = f"""Based on this conversation between a user and a Business Analyst AI assistant, generate a concise title (max {MAX_TITLE_LENGTH} characters) that captures the main topic being discussed.

The title should:
- Describe the feature or requirement being explored
- Be specific enough to distinguish from other conversations
- Use natural language (not technical jargon)

Current title: {current_title or "New Conversation"}

Conversation:
{formatted}

Return ONLY the title text, no quotes, no explanation, no punctuation at the end."""

    response = await client.messages.create(
        model=SUMMARY_MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    title = response.content[0].text.strip()

    # Ensure title fits limit
    if len(title) > MAX_TITLE_LENGTH:
        title = title[:MAX_TITLE_LENGTH - 3] + "..."

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens
    }

    return title, usage


async def maybe_update_summary(
    db: AsyncSession,
    thread_id: str,
    user_id: str
) -> Optional[str]:
    """
    Update thread summary if enough messages have accumulated.

    Updates title every SUMMARY_INTERVAL messages.

    Args:
        db: Database session
        thread_id: Thread ID
        user_id: User ID (for token tracking)

    Returns:
        New title if updated, None otherwise
    """
    from app.services.conversation_service import get_message_count

    message_count = await get_message_count(db, thread_id)

    # Only update at intervals (after 5, 10, 15... messages)
    if message_count < SUMMARY_INTERVAL or message_count % SUMMARY_INTERVAL != 0:
        return None

    # Get thread
    stmt = select(Thread).where(Thread.id == thread_id)
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread:
        return None

    # Get messages
    stmt_msgs = (
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
    )
    result_msgs = await db.execute(stmt_msgs)
    messages = result_msgs.scalars().all()

    # Convert to dict format
    msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

    # Generate summary
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        new_title, usage = await generate_thread_summary(
            client,
            msg_dicts,
            thread.title
        )

        # Update thread title
        thread.title = new_title
        await db.commit()

        # Track token usage for summarization
        await track_token_usage(
            db,
            user_id,
            SUMMARY_MODEL,
            usage["input_tokens"],
            usage["output_tokens"],
            f"/threads/{thread_id}/summarize"
        )

        return new_title

    except Exception as e:
        # Log error but don't fail the main request
        logger.error("Summarization failed", exc_info=True)
        return None
