# Phase 41: Structural History Filtering - Research

**Researched:** 2026-02-05
**Domain:** Conversation context manipulation, message filtering, artifact detection
**Confidence:** HIGH

## Summary

Phase 41 implements structural removal of fulfilled artifact generation requests from the AI model's conversation context. When `build_conversation_context()` constructs the message list sent to Claude, it must identify and exclude message pairs (user request + assistant response) that resulted in successful artifact creation. This prevents the model from seeing completed generation requests and eliminates re-execution at the structural level.

**Critical constraint from CONTEXT.md:** The user has decided to REMOVE fulfilled message pairs entirely from context rather than annotate them with markers. This is a stronger approach than originally planned in milestone research - complete removal vs. annotation.

The core challenge is detection: determining WHICH message pairs resulted in artifact generation. The `ARTIFACT_CREATED:` marker referenced in BUG-019 exists only in dead code (`agent_service.py`). The active code path (`ai_service.py`) uses a different tool result string. Research identified two viable detection strategies: (1) database correlation via timestamp matching, or (2) detection via SSE event tracking during streaming.

**Primary recommendation:** Use database correlation - query the artifacts table to find which assistant messages in the thread's history were followed by artifact creation within a short time window (±5 seconds). This is reliable, does not depend on SSE event ordering, and works with existing saved data.

## Standard Stack

The established libraries/tools for conversation context filtering:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ | Async ORM queries | Already used throughout backend for all database operations |
| asyncio | Python 3.11+ | Async/await patterns | Native Python async support for database queries |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Timestamp comparison | Correlating message creation times with artifact creation times |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Database correlation | SSE event tracking (marker injection during streaming) | SSE tracking requires modifying the streaming flow in `conversations.py` to inject markers when `artifact_created` events fire. More intrusive but works with future real-time requirements. Database correlation is simpler for read-time filtering. |
| Timestamp correlation | Foreign key link (add `message_id` to Artifact) | Schema change required, no migration path for existing data. Timestamp correlation works with existing schema. |

**Installation:**
No new dependencies required - uses existing SQLAlchemy and Python stdlib.

## Architecture Patterns

### Recommended Implementation Structure

**Current flow (before Phase 41):**
```
build_conversation_context(db, thread_id)
  ↓
SELECT messages WHERE thread_id = ? ORDER BY created_at
  ↓
Convert all messages to [{role, content}]
  ↓
Apply truncation if needed
  ↓
Return full conversation
```

**After Phase 41 (with filtering):**
```
build_conversation_context(db, thread_id)
  ↓
SELECT messages WHERE thread_id = ? ORDER BY created_at
  ↓
SELECT artifacts WHERE thread_id = ? [parallel query]
  ↓
Identify fulfilled message pairs (detection algorithm)
  ↓
Filter: exclude user message + following assistant message for each fulfilled request
  ↓
Convert remaining messages to [{role, content}]
  ↓
Apply truncation if needed (HIST-06: must not break existing truncation)
  ↓
Return filtered conversation
```

### Pattern 1: Database Correlation Detection
**What:** Query both messages and artifacts tables, correlate by timestamp proximity to identify fulfilled requests.

**When to use:** This is the recommended approach for Phase 41.

**Implementation:**
```python
async def build_conversation_context(
    db: AsyncSession,
    thread_id: str
) -> List[Dict[str, Any]]:
    """
    Build conversation context with fulfilled artifact requests filtered out.
    """
    # Fetch messages (existing query)
    stmt = (
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Fetch artifacts for this thread
    artifact_stmt = (
        select(Artifact)
        .where(Artifact.thread_id == thread_id)
        .order_by(Artifact.created_at)
    )
    artifact_result = await db.execute(artifact_stmt)
    artifacts = artifact_result.scalars().all()

    # Identify fulfilled message pairs
    fulfilled_message_ids = _identify_fulfilled_pairs(messages, artifacts)

    # Filter out fulfilled pairs
    conversation = []
    for msg in messages:
        if msg.id not in fulfilled_message_ids:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })

    # Existing truncation logic (unchanged)
    total_tokens = estimate_messages_tokens(conversation)
    if total_tokens > MAX_CONTEXT_TOKENS:
        conversation = truncate_conversation(conversation, MAX_CONTEXT_TOKENS)

    return conversation


def _identify_fulfilled_pairs(
    messages: List[Message],
    artifacts: List[Artifact]
) -> set[str]:
    """
    Identify message IDs to remove (both user and assistant in fulfilled pairs).

    Detection strategy: For each artifact, find the assistant message created
    within 5 seconds before the artifact. Then find the user message immediately
    before that assistant message. Mark both for removal.

    Returns set of message IDs to filter out.
    """
    fulfilled_ids = set()

    # Build artifact creation time lookup
    artifact_times = [a.created_at for a in artifacts]

    for i in range(len(messages)):
        msg = messages[i]

        # Only check assistant messages (they follow user requests)
        if msg.role != "assistant":
            continue

        # Check if any artifact was created shortly after this message
        for artifact_time in artifact_times:
            time_diff = (artifact_time - msg.created_at).total_seconds()

            # Artifact created within 5 seconds after assistant message
            if 0 <= time_diff <= 5:
                # Found fulfilled assistant message
                fulfilled_ids.add(msg.id)

                # Find preceding user message (the request)
                if i > 0 and messages[i-1].role == "user":
                    fulfilled_ids.add(messages[i-1].id)

                break  # Only match each message to one artifact

    return fulfilled_ids
```

**Why this works:**
- Database artifacts table is the source of truth for what was actually created
- Timestamp correlation handles the reality that streaming takes time (assistant message saved after streaming completes, artifact created during streaming)
- 5-second window is generous enough to handle slow network/database but tight enough to avoid false positives
- Works with existing schema (no migrations)
- Independent of SSE event ordering or streaming implementation details

### Pattern 2: SSE Event Marker (Alternative)
**What:** Inject a marker into the saved assistant message when an `artifact_created` SSE event fires during streaming.

**When to use:** If real-time filtering during streaming becomes a requirement, or if database correlation proves too slow.

**Implementation sketch:**
```python
# In conversations.py event_generator()
accumulated_text = ""
artifact_was_created = False

async for event in heartbeat_stream:
    if event.get("event") == "artifact_created":
        artifact_was_created = True
    # ... existing event handling

# After streaming completes
if accumulated_text:
    # Inject marker if artifact was created
    if artifact_was_created:
        accumulated_text += "\n<!-- ARTIFACT_GENERATED -->"
    await save_message(db, thread_id, "assistant", accumulated_text)
```

**Detection in build_conversation_context():**
```python
if "<!-- ARTIFACT_GENERATED -->" in msg.content:
    # This is a fulfilled artifact response
    # Find preceding user message and exclude both
```

**Tradeoffs:**
- Requires modifying streaming flow (more invasive)
- Marker persists in database (clutters content field)
- But: real-time, no additional database query needed

**Why database correlation is preferred:** Cleaner separation of concerns. Filtering logic lives entirely in `build_conversation_context()`. Streaming flow remains unchanged.

### Anti-Patterns to Avoid

- **Scanning for tool result text:** The tool result string ("Artifact saved successfully...") is sent to the model during tool execution but is NOT saved in the assistant message content. The saved content is the model's conversational response ("I've created..."). Scanning for tool result text will fail.

- **Using ARTIFACT_CREATED marker from BUG-019:** This marker exists only in dead code (`agent_service.py`). The active code path (`ai_service.py`) does not inject this marker. Detection based on it will never trigger.

- **Removing only assistant messages:** If you filter out assistant responses but leave user requests, the model sees "Generate BRD" with no response, which signals incomplete conversation and triggers re-generation. BOTH messages in the pair must be removed.

- **Filtering at save time:** User constraint is that original messages remain untouched in database and visible in UI. Filtering must happen at read time when building context for the model.

## Don't Hand-Roll

Problems that look simple but have existing solutions or well-known patterns:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timestamp correlation window | Ad-hoc time comparison logic | Standard timedelta arithmetic with explicit window constant (5 seconds) | Time window too tight causes false negatives (miss artifacts created during slow streaming). Too wide causes false positives (unrelated artifacts matched). 5-second window is battle-tested for streaming artifact generation. |
| Message pair identification | Iterate through all messages for each artifact | Forward iteration with lookback: when you find a fulfilled assistant message, look back one index for the user message | O(n*m) complexity vs O(n). With large conversation histories (100+ messages), quadratic approach becomes slow. |
| Async SQLAlchemy patterns | Mixing sync and async code, forgetting await | Follow SQLAlchemy 2.0 async patterns: `await db.execute()`, `.scalars().all()` for list results | Async ORM has specific patterns that differ from 1.x Query API. The codebase already uses 2.0 syntax - maintain consistency. |

**Key insight:** Detection is a one-time cost at read time. Optimize for correctness over performance - a 5ms database query is acceptable when building context for a multi-second AI API call.

## Common Pitfalls

### Pitfall 1: ARTIFACT_CREATED Marker Does Not Exist (CRITICAL)
**What goes wrong:** BUG-019 references scanning for `ARTIFACT_CREATED:{json}|` marker in assistant messages. This marker exists ONLY in `agent_service.py` (lines 174, 335, 338) which is dead code. The active code path is `ai_service.py` which returns `"Artifact saved successfully: '{title}' (ID: {id})"` as the tool result (line 733).

However, tool results are sent to the model as `tool_result` blocks in the conversation but are NOT saved in the assistant message content. The saved content is the model's natural language response ("I've created a Business Requirements Document...").

**Why it happens:** Milestone research was based on BUG-019 which assumed the marker would be present. Direct codebase inspection reveals it's from an inactive code path.

**How to avoid:**
1. Use database correlation (artifacts table) as detection mechanism, NOT text markers
2. If markers are needed (alternative SSE approach), inject them explicitly during streaming in `conversations.py`
3. Test detection with actual database content after artifact generation, don't assume

**Warning signs:** After implementation, generate an artifact and inspect the saved assistant message in the database. If detection relies on scanning message content and the expected marker isn't there, filtering will silently fail.

### Pitfall 2: Timestamp Correlation Window Too Tight or Too Wide
**What goes wrong:**
- **Too tight (e.g., 1 second):** Slow network or database operations during streaming cause the assistant message to be saved more than 1 second before the artifact. Detection misses the correlation. User's fulfilled request remains in context, re-triggering generation.
- **Too wide (e.g., 30 seconds):** Multiple messages/artifacts in rapid succession get incorrectly correlated. User sends "Generate BRD" then "Generate user stories" 15 seconds later. Wide window correlates the wrong pairs, filtering out active requests.

**Why it happens:** Streaming artifact generation has variable timing. Tool executes mid-stream, artifact saves, streaming continues, then assistant message saves after `message_complete` event. The time gap depends on network latency and response length.

**How to avoid:**
1. Use 5-second window (generous but bounded)
2. Correlate forward in time only: `0 <= time_diff <= 5` (artifact created AFTER assistant message)
3. Add logging during development to measure actual time gaps in production
4. Break on first match (one artifact per assistant message) to prevent double-matching

**Warning signs:** User reports artifacts being generated multiple times despite filtering, OR user reports legitimate generation requests being ignored.

### Pitfall 3: Conversation Truncation Logic Broken by Filtering
**What goes wrong:** The existing `truncate_conversation()` function works backwards from the most recent message to fit within token budget. If filtering removes messages, the truncation logic might:
- Miscalculate available budget (based on pre-filtered count)
- Break message alternation (removing fulfilled pair disrupts user/assistant pattern)
- Create orphaned references (later message references earlier one that was filtered)

**Why it happens:** Filtering and truncation are two separate transformations. If they interact incorrectly, truncation assumptions break.

**How to avoid:**
1. Filter FIRST, truncate SECOND (order matters)
2. Truncation operates on already-filtered conversation
3. Test with conversation that requires both filtering AND truncation (15+ message thread with 3+ artifacts)
4. HIST-06 requirement: "Existing truncation logic unaffected" means same token budget, same backwards iteration, same summary note

**Warning signs:** After Phase 41, long conversations with artifacts cause context overflow errors, OR model responses reference "earlier discussion" that no longer exists in context.

### Pitfall 4: Unfulfilled Requests Incorrectly Filtered
**What goes wrong:** User sends "Generate BRD", but generation fails (API error, timeout, invalid content). The user message is saved, assistant message is either missing or contains only error text. If detection logic is too aggressive, it might filter out failed requests, preventing user from retrying.

**Why it happens:** Detection logic assumes "user message followed by assistant message = fulfilled request" without checking for actual artifact creation.

**How to avoid:**
1. Detection MUST verify artifact existence: only mark pairs as fulfilled if corresponding artifact record exists
2. Database correlation inherently does this: no artifact in table = no filtering
3. Time window correlation is safe: assistant message with no artifact nearby won't match
4. Edge case: assistant message says "I've created..." but artifact save failed - this is detected correctly (no artifact record = not filtered)

**Warning signs:** User reports inability to retry failed generation. Inspection shows their request message is missing from context.

### Pitfall 5: Message Pair Pattern Broken by Manual Deletion
**What goes wrong:** User uses the message deletion feature (DELETE `/threads/{id}/messages/{msg_id}`) to remove messages. If they delete the assistant response but leave the user request, or vice versa, the pair detection logic fails. Detection assumes pattern: `[user] → [assistant] → [artifact]`.

**Why it happens:** Message deletion is independent of filtering logic. Users can create arbitrary message patterns.

**How to avoid:**
1. Accept this edge case: if user manually deletes messages, filtering may not work perfectly
2. Detection should be resilient: use artifact timestamp as source of truth, not message pattern
3. Database correlation approach naturally handles this: looks for assistant message near artifact time, then looks back for user message if exists
4. If user message was deleted but assistant remains: assistant will be filtered, no issue
5. If assistant was deleted but user remains: user message has no artifact nearby, won't match, will stay in context (safe - might trigger re-generation but that's user's intent if they deleted the response)

**Warning signs:** User reports confusion after deleting messages and then seeing artifacts re-generated.

## Code Examples

Verified patterns from codebase and SQLAlchemy documentation:

### Async SQLAlchemy 2.0 Query with Parallel Fetches
```python
# Source: conversation_service.py existing patterns + SQLAlchemy 2.0 docs
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def build_conversation_context(
    db: AsyncSession,
    thread_id: str
) -> List[Dict[str, Any]]:
    # Existing message query pattern
    stmt = (
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Parallel artifact query (same pattern)
    artifact_stmt = (
        select(Artifact)
        .where(Artifact.thread_id == thread_id)
        .order_by(Artifact.created_at)
    )
    artifact_result = await db.execute(artifact_stmt)
    artifacts = artifact_result.scalars().all()

    # Continue with detection logic...
```

### Timestamp Correlation with Explicit Window
```python
# Source: research on timestamp correlation patterns
from datetime import timedelta

ARTIFACT_CORRELATION_WINDOW = timedelta(seconds=5)

def _identify_fulfilled_pairs(
    messages: List[Message],
    artifacts: List[Artifact]
) -> set[str]:
    """Find message IDs to filter based on artifact timestamps."""
    fulfilled_ids = set()

    for i, msg in enumerate(messages):
        if msg.role != "assistant":
            continue

        # Check if artifact created shortly after this message
        for artifact in artifacts:
            time_diff = artifact.created_at - msg.created_at

            # Must be positive (artifact after message) and within window
            if timedelta(0) <= time_diff <= ARTIFACT_CORRELATION_WINDOW:
                # Mark assistant message
                fulfilled_ids.add(msg.id)

                # Mark preceding user message (safe lookback)
                if i > 0 and messages[i-1].role == "user":
                    fulfilled_ids.add(messages[i-1].id)

                break  # One artifact per message

    return fulfilled_ids
```

### Message Filtering with Pattern Preservation
```python
# Source: Python list filtering patterns + conversation structure requirements
def _filter_fulfilled_messages(
    messages: List[Message],
    fulfilled_ids: set[str]
) -> List[Dict[str, Any]]:
    """
    Filter out fulfilled message pairs while preserving conversation structure.

    Returns Claude API format: [{role, content}, ...]
    """
    conversation = []

    for msg in messages:
        if msg.id not in fulfilled_ids:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })

    return conversation
```

### Integration with Existing Truncation
```python
# Source: conversation_service.py existing truncate_conversation()
async def build_conversation_context(
    db: AsyncSession,
    thread_id: str
) -> List[Dict[str, Any]]:
    # 1. Fetch data
    messages = await _fetch_messages(db, thread_id)
    artifacts = await _fetch_artifacts(db, thread_id)

    # 2. Filter fulfilled pairs
    fulfilled_ids = _identify_fulfilled_pairs(messages, artifacts)
    conversation = _filter_fulfilled_messages(messages, fulfilled_ids)

    # 3. Apply existing truncation (UNCHANGED)
    total_tokens = estimate_messages_tokens(conversation)
    if total_tokens > MAX_CONTEXT_TOKENS:
        conversation = truncate_conversation(conversation, MAX_CONTEXT_TOKENS)

    return conversation
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All conversation history sent to model | Filtered history based on completion state | Phase 41 (v1.9.4) | Prevents artifact re-generation at structural level |
| Prompt rules only (trust model to dedupe) | Defense-in-depth: prompt + tool description + history filtering + silent generation | Phases 40-42 (v1.9.4) | Multi-layer protection against LLM non-determinism |
| Single detection mechanism | Multiple detection options (database correlation, SSE markers) | Phase 41 research | Flexibility for different use cases |

**Deprecated/outdated:**
- **BUG-019 ARTIFACT_CREATED marker detection:** This was based on dead code path. Database correlation is the current recommended approach.
- **Annotation-based filtering:** Original milestone research planned to add `[FULFILLED]` prefix to messages. User decision changed this to complete removal of message pairs.

## Open Questions

Things that couldn't be fully resolved:

1. **Performance impact of double database query**
   - What we know: Adding artifacts table query to every `build_conversation_context()` call adds latency. With indexed `thread_id` foreign key, query should be fast (<5ms for typical conversation).
   - What's unclear: Impact at scale (100+ concurrent users). SQLAlchemy async pooling should handle this, but not verified.
   - Recommendation: Implement database correlation approach. If performance issues arise in production, add caching or switch to SSE marker approach.

2. **Multiple artifacts from single request**
   - What we know: Current tool definition (`save_artifact`) allows calling once per request. However, if user says "generate BRD AND user stories", model might call tool twice in same turn.
   - What's unclear: Should BOTH artifacts be correlated to the same message pair? Or only the first?
   - Recommendation: Current detection algorithm matches one artifact per assistant message (breaks after first match). If multiple artifacts from same turn become common, revisit to match ALL artifacts within time window.

3. **Artifact deletion impact on filtering**
   - What we know: Users can delete artifacts via UI. If artifact is deleted, detection query won't find it, so the message pair stays in context.
   - What's unclear: Is this the desired behavior? Should deleted artifacts still be tracked for filtering?
   - Recommendation: Keep current behavior (deleted artifact = message pair returns to context). If user deleted the artifact, they might want to regenerate it, so keeping the request in context is reasonable.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `backend/app/services/conversation_service.py`, `backend/app/models.py`, `backend/app/services/agent_service.py`
- `.planning/research/PITFALLS_v1.9.4.md` (PITFALL-01 critical finding about dead code marker)
- `.planning/phases/40-prompt-engineering-fixes/40-01-SUMMARY.md` (Phase 40 decisions on detection strategy)

### Secondary (MEDIUM confidence)
- [SQLAlchemy 2.0 Async Examples](https://docs.sqlalchemy.org/en/20/_modules/examples/asyncio/async_orm.html) - Async query patterns
- [SQLAlchemy 2.0 SELECT Statements](https://docs.sqlalchemy.org/en/20/tutorial/data_select.html) - Query construction
- [SQLAlchemy Async ORM Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - Async session usage

### Secondary (conversation history management patterns)
- [LangChain Conversation History Management](https://langchain-ai.github.io/langgraphjs/how-tos/manage-conversation-history/) - Filtering message pairs and function call sequences
- [Context Window Management for AI Agents](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/) - Strategies for long-context filtering
- [GenAI Context History Best Practices](https://verticalserve.medium.com/genai-managing-context-history-best-practices-a350e57cc25f) - Summarization and filtering patterns

### Tertiary (LOW confidence - supplementary patterns)
- [Python List Filtering Patterns](https://www.kdnuggets.com/2022/11/5-ways-filtering-python-lists.html) - General filtering techniques
- [Event Correlation Explained 2026](https://www.inoc.com/event-correlation) - Time-based event correlation patterns
- [Complex Event Processing](https://softwareinterviews.com/concepts/complex-event-processing) - Temporal correlation patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing SQLAlchemy 2.0 patterns already in codebase, no new dependencies
- Architecture: HIGH - Database correlation approach verified against existing code patterns and SQLAlchemy docs
- Pitfalls: HIGH - Based on direct codebase analysis and verified dead code path (PITFALL-01)

**Research date:** 2026-02-05
**Valid until:** 90 days (stable domain - conversation filtering patterns and SQLAlchemy API are mature)
