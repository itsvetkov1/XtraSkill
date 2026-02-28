"""
Conversation service for message persistence and context building.

Handles saving messages to database and building conversation context
for Claude API calls with token-aware truncation.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Message, Thread, Artifact

# Context window limits
MAX_CONTEXT_TOKENS = 150000  # Leave room for response and system prompt
# Rough estimate: 1 token ~= 4 characters
CHARS_PER_TOKEN = 4
# Artifact correlation window for fulfilled pair detection
ARTIFACT_CORRELATION_WINDOW = timedelta(seconds=5)


def estimate_tokens(text: str) -> int:
    """Rough token estimation based on character count."""
    return len(text) // CHARS_PER_TOKEN


def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """Estimate total tokens in message list."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            # Handle tool results or multi-part content
            for part in content:
                if isinstance(part, dict):
                    total += estimate_tokens(str(part.get("content", "")))
    return total


def _identify_fulfilled_pairs(
    messages: list,
    artifacts: list
) -> set:
    """
    Identify message pairs (user + assistant) that resulted in artifact creation.

    Uses timestamp correlation: if an artifact was created within 0-5 seconds
    after an assistant message, that message pair is considered "fulfilled"
    and should be excluded from conversation context.

    Args:
        messages: List of Message objects with id, role, created_at attributes
        artifacts: List of Artifact objects with created_at attribute

    Returns:
        Set of message IDs to exclude from conversation context
    """
    fulfilled_ids = set()

    for i, msg in enumerate(messages):
        if msg.role != "assistant":
            continue

        # Check for ARTIFACT_CREATED marker in assistant message content
        if hasattr(msg, 'content') and msg.content and 'ARTIFACT_CREATED:' in msg.content:
            # Mark assistant message as fulfilled via marker
            fulfilled_ids.add(msg.id)
            if i > 0 and messages[i - 1].role == 'user':
                fulfilled_ids.add(messages[i - 1].id)
            continue  # Skip timestamp check - marker found

        # Fallback: Check if any artifact was created within correlation window
        for artifact in artifacts:
            time_diff = (artifact.created_at - msg.created_at).total_seconds()

            if 0 <= time_diff <= ARTIFACT_CORRELATION_WINDOW.total_seconds():
                # Mark assistant message as fulfilled
                fulfilled_ids.add(msg.id)

                # Mark preceding user message if it exists
                if i > 0 and messages[i - 1].role == "user":
                    fulfilled_ids.add(messages[i - 1].id)

                # Break after first match (one artifact per message)
                break

    return fulfilled_ids


async def save_message(
    db: AsyncSession,
    thread_id: str,
    role: str,
    content: str
) -> Message:
    """
    Save a message to the database.

    Args:
        db: Database session
        thread_id: ID of the thread
        role: 'user' or 'assistant'
        content: Message content

    Returns:
        Created Message object
    """
    message = Message(
        thread_id=thread_id,
        role=role,
        content=content
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    # Update thread's updated_at timestamp
    stmt = select(Thread).where(Thread.id == thread_id)
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if thread:
        thread.updated_at = datetime.now(timezone.utc)
        await db.commit()

    return message


async def build_conversation_context(
    db: AsyncSession,
    thread_id: str
) -> List[Dict[str, Any]]:
    """
    Build conversation context from thread messages.

    Loads all messages from thread and converts to Claude message format.
    Filters out fulfilled artifact request pairs before truncation.
    Implements token-aware truncation if conversation is too long.

    Args:
        db: Database session
        thread_id: ID of the thread

    Returns:
        List of messages in Claude API format
    """
    # Fetch all messages in chronological order
    stmt = (
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Fetch all artifacts for this thread
    artifact_stmt = (
        select(Artifact)
        .where(Artifact.thread_id == thread_id)
        .order_by(Artifact.created_at)
    )
    artifact_result = await db.execute(artifact_stmt)
    artifacts = artifact_result.scalars().all()

    # Identify fulfilled pairs to exclude
    fulfilled_ids = _identify_fulfilled_pairs(messages, artifacts)

    # Convert to Claude message format, excluding fulfilled pairs
    conversation = []
    for msg in messages:
        if msg.id not in fulfilled_ids:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })

    # Check token count and truncate if needed
    total_tokens = estimate_messages_tokens(conversation)

    if total_tokens > MAX_CONTEXT_TOKENS:
        conversation = truncate_conversation(conversation, MAX_CONTEXT_TOKENS)

    return conversation


def truncate_conversation(
    messages: List[Dict[str, Any]],
    max_tokens: int
) -> List[Dict[str, Any]]:
    """
    Truncate conversation to fit within token budget.

    Strategy: Keep recent messages that fit in 80% of budget.
    Prepend summary note about truncated messages.

    Args:
        messages: Full conversation history
        max_tokens: Maximum tokens allowed

    Returns:
        Truncated message list
    """
    budget = int(max_tokens * 0.8)  # 80% for messages, 20% buffer
    recent_messages = []
    token_count = 0

    # Work backwards from most recent
    for msg in reversed(messages):
        msg_tokens = estimate_messages_tokens([msg])
        if token_count + msg_tokens > budget:
            break
        recent_messages.insert(0, msg)
        token_count += msg_tokens

    # If we truncated, add summary
    truncated_count = len(messages) - len(recent_messages)
    if truncated_count > 0:
        summary = {
            "role": "user",
            "content": f"[System note: {truncated_count} earlier messages in this conversation have been summarized to fit context limits. The conversation began earlier and covered additional topics not shown here.]"
        }
        recent_messages.insert(0, summary)

    return recent_messages


async def get_message_count(db: AsyncSession, thread_id: str) -> int:
    """Get count of messages in a thread."""
    from sqlalchemy import func
    stmt = select(func.count(Message.id)).where(Message.thread_id == thread_id)
    result = await db.execute(stmt)
    return result.scalar() or 0


# Skill prompt loading
SKILLS_DIR = "/home/i_tsvetkov/claude_skills"

def load_skill_prompt(skill_id: str) -> str | None:
    """Load skill system prompt from skills directory."""
    import os
    skill_path = os.path.join(SKILLS_DIR, skill_id, "SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path, 'r') as f:
            content = f.read()
            # Extract system prompt section if exists
            if "## System Prompt" in content:
                section = content.split("## System Prompt")[1].split("##")[0]
                return section.strip()
            # Otherwise return first 2000 chars as prompt
            return content[:2000]
    return None


async def inject_skill_context(
    db: AsyncSession,
    thread_id: str,
    conversation: list
) -> list:
    """
    Inject skill system prompt into conversation if thread has selected_skill.
    
    Args:
        db: Database session
        thread_id: ID of the thread
        conversation: Current conversation context
        
    Returns:
        Modified conversation with skill prompt prepended
    """
    # Fetch thread to get selected_skill
    stmt = select(Thread).where(Thread.id == thread_id)
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    
    if not thread or not thread.selected_skill:
        return conversation
    
    # Load skill prompt
    skill_prompt = load_skill_prompt(thread.selected_skill)
    if not skill_prompt:
        return conversation
    
    # Prepend skill system message
    skill_message = {
        "role": "system",
        "content": f"[SKILL: {thread.selected_skill}]\n\n{skill_prompt}"
    }
    
    return [skill_message] + conversation
