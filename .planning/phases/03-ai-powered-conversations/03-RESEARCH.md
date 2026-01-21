# Phase 3: AI-Powered Conversations - Research

**Researched:** 2026-01-21
**Domain:** AI integration, streaming, RAG, conversation management, token tracking
**Confidence:** HIGH

## Summary

Phase 3 implements AI-powered conversations using Claude as the conversational AI. This research covers two architectural approaches: (1) the standard Anthropic Python SDK for direct API control with tool use, and (2) the Claude Agent SDK for autonomous agent execution. Given the requirements for custom tools (document search, summarization), streaming SSE responses, and token tracking, the **standard Anthropic Python SDK** is recommended over the Agent SDK for this phase.

The standard SDK provides fine-grained control over the tool execution loop, streaming responses, and token tracking, all of which are essential for this phase's requirements. The Claude Agent SDK is more suited for autonomous file/code editing agents and would add unnecessary complexity for a conversational assistant.

**Critical discovery:** The Anthropic SDK already installed (v0.76.0) provides built-in streaming helpers (`client.messages.stream()`), async support, and a tool runner beta that handles the tool call loop automatically. Token usage is available in the `message_delta` event during streaming and in `get_final_message()` after stream completion.

**Primary recommendation:** Use the standard `anthropic` Python SDK with manual tool definitions, streaming via `client.messages.stream()`, and FastAPI's `StreamingResponse` with SSE format. Define custom tools for document search (using existing FTS5 infrastructure) and thread summarization. Implement a token tracking middleware to log usage per request.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.76.0+ | Claude API client | Official SDK, async support, streaming helpers, tool runner beta |
| sse-starlette | 3.2+ | FastAPI SSE support | Production-ready, async generators, connection management |
| flutter_client_sse | 3.0+ | Flutter SSE client | Parses SSE events, authentication headers, reconnection support |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.0+ | Tool input validation | Already in project, validate tool parameters |
| asyncio | Built-in | Async coordination | Stream handling, concurrent operations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Anthropic SDK + manual tools | Claude Agent SDK | Agent SDK is for autonomous file operations; too heavy for conversational AI |
| sse-starlette | FastAPI StreamingResponse | sse-starlette provides better connection management and standard compliance |
| flutter_client_sse | flutter_http_sse | Both work; flutter_client_sse has simpler API, more downloads |

**Installation:**
```bash
# Backend - anthropic already installed
pip install sse-starlette

# Frontend (pubspec.yaml)
dependencies:
  flutter_client_sse: ^3.0.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── services/
│   │   ├── ai_service.py           # Claude API wrapper, tool definitions
│   │   ├── conversation_service.py  # Message handling, context building
│   │   ├── summarization_service.py # Thread summary generation
│   │   └── token_tracking.py        # Usage logging and budget enforcement
│   └── routes/
│       └── conversations.py         # SSE streaming endpoint

frontend/
├── lib/
│   ├── services/
│   │   └── ai_service.dart          # SSE stream consumption
│   ├── providers/
│   │   └── conversation_provider.dart # Streaming state management
│   └── screens/
│       └── conversation/
│           ├── conversation_screen.dart
│           └── widgets/
│               ├── message_bubble.dart
│               └── streaming_message.dart
```

### Pattern 1: Claude API with Tool Use (Manual Loop)
**What:** Define tools with JSON Schema, execute tool calls in a loop until stop_reason is "end_turn"
**When to use:** Full control over tool execution, custom tools, token tracking

**Example:**
```python
# Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use
import anthropic
from typing import List, Dict, Any

# Define document search tool
DOCUMENT_SEARCH_TOOL = {
    "name": "search_documents",
    "description": "Search project documents for relevant information. Use when user mentions documents, references, policies, or asks about project context. Returns snippets with relevance scores.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to find relevant documents"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default 5)",
                "default": 5
            }
        },
        "required": ["query"]
    }
}

async def execute_tool(tool_name: str, tool_input: dict, project_id: str, db) -> str:
    """Execute a tool and return result as string."""
    if tool_name == "search_documents":
        results = await search_documents(db, project_id, tool_input["query"])
        if not results:
            return "No relevant documents found."
        formatted = []
        for doc_id, filename, snippet, score in results[:tool_input.get("max_results", 5)]:
            formatted.append(f"**{filename}**: {snippet}")
        return "\n\n".join(formatted)
    return "Unknown tool"

async def chat_with_tools(
    client: anthropic.AsyncAnthropic,
    messages: List[dict],
    tools: List[dict],
    project_id: str,
    db
) -> anthropic.Message:
    """Execute tool loop until Claude returns end_turn."""
    while True:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=messages,
            tools=tools,
            system="You are a Business Analyst assistant. Proactively identify edge cases, ask clarifying questions, and search documents when context is needed."
        )

        # Check if we need to execute tools
        if response.stop_reason != "tool_use":
            return response

        # Execute each tool use block
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = await execute_tool(block.name, block.input, project_id, db)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        # Add assistant response and tool results to messages
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

### Pattern 2: Streaming SSE Endpoint with FastAPI
**What:** Stream Claude responses as SSE events to the frontend
**When to use:** Progressive UI updates during AI response generation

**Example:**
```python
# Source: https://github.com/sysid/sse-starlette
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
import anthropic
import json
from typing import AsyncGenerator

router = APIRouter()

async def generate_sse_events(
    client: anthropic.AsyncAnthropic,
    messages: list,
    tools: list,
    project_id: str,
    db,
    thread_id: str
) -> AsyncGenerator[dict, None]:
    """Generate SSE events from Claude streaming response."""

    # Build conversation context
    conversation_messages = await build_conversation_context(db, thread_id, messages)

    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=conversation_messages,
        tools=tools,
        system="You are a Business Analyst assistant..."
    ) as stream:
        # Stream text deltas
        async for text in stream.text_stream:
            yield {
                "event": "text_delta",
                "data": json.dumps({"text": text})
            }

        # Get final message for metadata
        final_message = await stream.get_final_message()

        # Handle tool use if needed
        if final_message.stop_reason == "tool_use":
            yield {
                "event": "tool_use",
                "data": json.dumps({
                    "tools": [
                        {"name": block.name, "input": block.input}
                        for block in final_message.content
                        if block.type == "tool_use"
                    ]
                })
            }
            # Execute tools and continue streaming...

        # Send usage stats
        yield {
            "event": "message_complete",
            "data": json.dumps({
                "usage": {
                    "input_tokens": final_message.usage.input_tokens,
                    "output_tokens": final_message.usage.output_tokens
                }
            })
        }

@router.post("/threads/{thread_id}/chat")
async def chat_stream(
    thread_id: str,
    request: Request,
    message: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stream AI response as Server-Sent Events."""
    # Validate thread ownership
    thread = await get_thread_with_owner_check(db, thread_id, current_user["user_id"])

    # Save user message
    user_msg = await save_message(db, thread_id, "user", message.content)

    # Initialize Claude client
    client = anthropic.AsyncAnthropic()

    async def event_generator():
        async for event in generate_sse_events(
            client,
            [{"role": "user", "content": message.content}],
            [DOCUMENT_SEARCH_TOOL],
            thread.project_id,
            db,
            thread_id
        ):
            # Check for client disconnect
            if await request.is_disconnected():
                break
            yield event

    return EventSourceResponse(event_generator())
```

### Pattern 3: Conversation Context Building
**What:** Build conversation history from database messages with token-aware truncation
**When to use:** Loading thread history for Claude API calls

**Example:**
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/context-windows
from typing import List, Dict
import tiktoken  # Or use anthropic's count_tokens if available

MAX_CONTEXT_TOKENS = 150000  # Leave room for response and system prompt
SUMMARY_THRESHOLD = 100000

async def build_conversation_context(
    db: AsyncSession,
    thread_id: str,
    new_message: str
) -> List[Dict]:
    """Build conversation context from thread messages."""

    # Fetch all messages in chronological order
    stmt = select(Message).where(
        Message.thread_id == thread_id
    ).order_by(Message.created_at)
    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Convert to Claude message format
    conversation = []
    for msg in messages:
        conversation.append({
            "role": msg.role,
            "content": msg.content
        })

    # Add new user message
    conversation.append({
        "role": "user",
        "content": new_message
    })

    # Token counting and truncation
    total_tokens = estimate_tokens(conversation)

    if total_tokens > MAX_CONTEXT_TOKENS:
        # Strategy: Keep system context + recent messages + summarize old
        conversation = truncate_with_summary(conversation, MAX_CONTEXT_TOKENS)

    return conversation

def truncate_with_summary(
    messages: List[Dict],
    max_tokens: int
) -> List[Dict]:
    """Truncate old messages, keeping recent context."""
    # Keep last N messages that fit in budget
    recent_messages = []
    token_count = 0

    for msg in reversed(messages):
        msg_tokens = estimate_tokens([msg])
        if token_count + msg_tokens > max_tokens * 0.8:  # 80% for messages
            break
        recent_messages.insert(0, msg)
        token_count += msg_tokens

    # If we had to truncate, add summary of older messages
    if len(recent_messages) < len(messages):
        summary = {
            "role": "user",
            "content": f"[Previous conversation summary: {len(messages) - len(recent_messages)} earlier messages discussed...]"
        }
        recent_messages.insert(0, summary)

    return recent_messages
```

### Pattern 4: Flutter SSE Consumption
**What:** Consume SSE stream in Flutter and update UI progressively
**When to use:** Real-time AI response display with streaming

**Example:**
```dart
// Source: https://pub.dev/packages/flutter_client_sse
import 'package:flutter_client_sse/flutter_client_sse.dart';
import 'dart:convert';

class AIService {
  final String baseUrl;
  final FlutterSecureStorage _storage;

  AIService({required this.baseUrl}) : _storage = FlutterSecureStorage();

  Stream<ChatEvent> streamChat(String threadId, String message) async* {
    final token = await _storage.read(key: 'auth_token');
    if (token == null) throw Exception('Not authenticated');

    final stream = SSEClient.subscribeToSSE(
      method: SSERequestType.POST,
      url: '$baseUrl/api/threads/$threadId/chat',
      header: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
      body: jsonEncode({'content': message}),
    );

    await for (final event in stream) {
      final data = jsonDecode(event.data ?? '{}');

      switch (event.event) {
        case 'text_delta':
          yield TextDeltaEvent(text: data['text']);
          break;
        case 'tool_use':
          yield ToolUseEvent(tools: data['tools']);
          break;
        case 'message_complete':
          yield MessageCompleteEvent(
            inputTokens: data['usage']['input_tokens'],
            outputTokens: data['usage']['output_tokens'],
          );
          break;
        case 'error':
          yield ErrorEvent(message: data['message']);
          break;
      }
    }
  }
}

// Event types
abstract class ChatEvent {}
class TextDeltaEvent extends ChatEvent {
  final String text;
  TextDeltaEvent({required this.text});
}
class ToolUseEvent extends ChatEvent {
  final List tools;
  ToolUseEvent({required this.tools});
}
class MessageCompleteEvent extends ChatEvent {
  final int inputTokens;
  final int outputTokens;
  MessageCompleteEvent({required this.inputTokens, required this.outputTokens});
}
class ErrorEvent extends ChatEvent {
  final String message;
  ErrorEvent({required this.message});
}
```

### Pattern 5: Token Usage Tracking
**What:** Track token usage per request, conversation, and user
**When to use:** Cost monitoring, budget enforcement

**Example:**
```python
# Source: https://docs.anthropic.com/en/api/messages-streaming
from decimal import Decimal
from app.models import TokenUsage

# Claude Sonnet 4.5 pricing (as of Jan 2026)
PRICING = {
    "claude-sonnet-4-5-20250929": {
        "input": Decimal("0.003"),   # $3 per 1M input tokens
        "output": Decimal("0.015"),  # $15 per 1M output tokens
    }
}

async def track_token_usage(
    db: AsyncSession,
    user_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    endpoint: str
) -> TokenUsage:
    """Record token usage for billing and monitoring."""

    pricing = PRICING.get(model, PRICING["claude-sonnet-4-5-20250929"])

    input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * pricing["input"]
    output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * pricing["output"]
    total_cost = input_cost + output_cost

    usage = TokenUsage(
        user_id=user_id,
        request_tokens=input_tokens,
        response_tokens=output_tokens,
        total_cost=total_cost,
        endpoint=endpoint,
        model=model
    )

    db.add(usage)
    await db.commit()

    return usage

async def check_user_budget(
    db: AsyncSession,
    user_id: str,
    monthly_limit: Decimal = Decimal("50.00")  # $50 default
) -> bool:
    """Check if user is within monthly budget."""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.sum(TokenUsage.total_cost))
        .where(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= month_start
        )
    )
    monthly_total = result.scalar() or Decimal("0")

    return monthly_total < monthly_limit
```

### Pattern 6: Thread Summarization
**What:** Generate and update thread summaries based on conversation content
**When to use:** Thread title generation, conversation overview

**Example:**
```python
# Summarization tool for AI-generated thread titles
async def generate_thread_summary(
    client: anthropic.AsyncAnthropic,
    messages: List[Dict],
    current_title: str | None
) -> str:
    """Generate a concise summary title for a thread."""

    # Use Claude to generate summary
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"""Based on this conversation, generate a concise title (max 50 chars) that captures the main topic.

Current title: {current_title or "New Conversation"}

Conversation:
{format_messages_for_summary(messages[-10:])}  # Last 10 messages

Return ONLY the title, no quotes or explanation."""
        }]
    )

    return response.content[0].text.strip()[:50]

async def maybe_update_summary(
    db: AsyncSession,
    client: anthropic.AsyncAnthropic,
    thread_id: str,
    message_count: int
) -> None:
    """Update thread summary every N messages."""

    SUMMARY_INTERVAL = 5  # Update every 5 messages

    if message_count % SUMMARY_INTERVAL != 0:
        return

    thread = await get_thread(db, thread_id)
    messages = await get_thread_messages(db, thread_id)

    new_title = await generate_thread_summary(
        client,
        [{"role": m.role, "content": m.content} for m in messages],
        thread.title
    )

    thread.title = new_title
    await db.commit()
```

### Anti-Patterns to Avoid

- **Using Claude Agent SDK for conversational AI:** Agent SDK is designed for autonomous file operations; adds unnecessary complexity for chat
- **Polling instead of SSE:** Wastes resources and adds latency; use SSE for real-time streaming
- **Synchronous Claude API calls in async context:** Always use AsyncAnthropic with async/await
- **Unbounded context windows:** Always implement token counting and truncation strategies
- **Missing tool error handling:** Always return errors to Claude with `is_error: true` so it can retry
- **Buffering entire response before sending:** Stream incrementally with SSE for better UX
- **Not tracking token usage:** Essential for cost control and budget enforcement

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE streaming | Custom HTTP chunking | sse-starlette | Handles connection management, proper event formatting |
| Tool execution loop | Manual while loop | SDK tool_runner (beta) | Handles tool results, message formatting, error recovery |
| Token counting | Character-based estimation | Anthropic's tiktoken or API | Accurate BPE tokenization |
| SSE client (Flutter) | Raw HTTP stream parsing | flutter_client_sse | Parses events, handles reconnection |
| Conversation context | Load all messages | Token-aware truncation | Context window limits, costs |

**Key insight:** The Anthropic SDK provides streaming helpers and tool runners that handle most complexity. Focus on business logic (tool implementations, context building) rather than API plumbing.

## Common Pitfalls

### Pitfall 1: SSE Buffering by Reverse Proxy
**What goes wrong:** SSE events are delayed or batched, breaking real-time streaming
**Why it happens:** Nginx/Apache buffer responses by default
**How to avoid:** Add `X-Accel-Buffering: no` header or configure proxy_buffering off
**Warning signs:** Events arrive in batches instead of individually

**Code:**
```python
# FastAPI SSE endpoint with buffering disabled
from sse_starlette.sse import EventSourceResponse

@router.post("/threads/{thread_id}/chat")
async def chat_stream(...):
    async def generator():
        # ... yield events
        pass

    return EventSourceResponse(
        generator(),
        headers={"X-Accel-Buffering": "no"}  # Disable Nginx buffering
    )
```

### Pitfall 2: Tool Result Formatting Errors
**What goes wrong:** 400 errors with "tool_result blocks must come FIRST"
**Why it happens:** Text added before tool_result in content array
**How to avoid:** Always place tool_result blocks first, text after
**Warning signs:** "tool_use ids were found without tool_result blocks immediately after"

**Correct format:**
```python
# CORRECT
{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "toolu_01", "content": "result"},
    {"type": "text", "text": "Any follow-up text goes AFTER"}  # OK here
]}

# WRONG
{"role": "user", "content": [
    {"type": "text", "text": "Here are the results:"},  # NOT OK
    {"type": "tool_result", "tool_use_id": "toolu_01", "content": "result"}
]}
```

### Pitfall 3: Context Window Overflow
**What goes wrong:** API returns validation error, conversation breaks
**Why it happens:** Long conversations exceed 200K token limit
**How to avoid:** Implement token counting, truncation with summaries
**Warning signs:** Conversations failing after 30-50 messages

### Pitfall 4: Missing Token Usage in Streaming
**What goes wrong:** Cannot track costs, budget enforcement fails
**Why it happens:** Token usage only available in final message_delta event
**How to avoid:** Always call `get_final_message()` after stream to get usage
**Warning signs:** TokenUsage records showing 0 tokens

**Code:**
```python
async with client.messages.stream(...) as stream:
    async for text in stream.text_stream:
        yield {"event": "text_delta", "data": text}

    # IMPORTANT: Get usage after stream completes
    final = await stream.get_final_message()
    await track_token_usage(
        db, user_id, model,
        final.usage.input_tokens,
        final.usage.output_tokens,
        endpoint
    )
```

### Pitfall 5: Flutter Web SSE Issues
**What goes wrong:** SSE doesn't work on Flutter Web, events not received
**Why it happens:** Browser fetch() buffers responses differently
**How to avoid:** Use XMLHttpRequest directly or flutter_client_sse which handles this
**Warning signs:** Works on mobile, fails on web

### Pitfall 6: AI Not Using Tools
**What goes wrong:** AI gives generic answers instead of searching documents
**Why it happens:** Tool descriptions don't clearly indicate when to use
**How to avoid:** Write detailed tool descriptions explaining WHEN to use
**Warning signs:** AI says "I don't have access to your documents"

**Good tool description:**
```python
{
    "name": "search_documents",
    "description": """Search project documents for relevant information.

USE THIS TOOL WHEN:
- User mentions documents, files, or project materials
- User asks about policies, requirements, or specifications
- User references something that might be in uploaded documents
- You need context about the project to answer accurately

DO NOT USE WHEN:
- User is asking general questions not related to project documents
- You already have sufficient context from conversation history

Returns: Document snippets with filenames and relevance scores.""",
    ...
}
```

## Code Examples

### Complete Chat Endpoint with Streaming and Tools
```python
# Source: Anthropic SDK docs + sse-starlette
from fastapi import APIRouter, Depends, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import anthropic
import json

router = APIRouter()

class ChatRequest(BaseModel):
    content: str

TOOLS = [
    {
        "name": "search_documents",
        "description": "Search project documents for relevant information...",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
]

SYSTEM_PROMPT = """You are a Business Analyst AI assistant. Your role is to:

1. PROACTIVELY IDENTIFY EDGE CASES: When users describe requirements, think about what could go wrong. Ask questions like "What happens if...?" without being prompted.

2. ASK CLARIFYING QUESTIONS: Explore requirements deeply. Don't assume - ask about user personas, error handling, performance needs, integrations.

3. SEARCH DOCUMENTS AUTONOMOUSLY: When users mention anything that might be documented, use the search_documents tool to find relevant context.

4. MAINTAIN CONTEXT: Reference earlier parts of the conversation. Remember decisions made and requirements discussed.

Be conversational but thorough. Help users think through their requirements completely."""

@router.post("/threads/{thread_id}/chat")
async def stream_chat(
    thread_id: str,
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate thread ownership
    thread = await validate_thread_access(db, thread_id, current_user["user_id"])
    if not thread:
        raise HTTPException(404, "Thread not found")

    # Check budget
    if not await check_user_budget(db, current_user["user_id"]):
        raise HTTPException(429, "Monthly token budget exceeded")

    # Save user message
    await save_message(db, thread_id, "user", body.content)

    # Build conversation context
    conversation = await build_conversation_context(db, thread_id)
    conversation.append({"role": "user", "content": body.content})

    client = anthropic.AsyncAnthropic()

    async def event_generator():
        accumulated_text = ""
        total_input = 0
        total_output = 0

        try:
            messages = conversation.copy()

            while True:
                async with client.messages.stream(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    messages=messages,
                    tools=TOOLS,
                    system=SYSTEM_PROMPT
                ) as stream:
                    async for text in stream.text_stream:
                        if await request.is_disconnected():
                            return
                        accumulated_text += text
                        yield {
                            "event": "text_delta",
                            "data": json.dumps({"text": text})
                        }

                    final = await stream.get_final_message()
                    total_input += final.usage.input_tokens
                    total_output += final.usage.output_tokens

                    if final.stop_reason != "tool_use":
                        break

                    # Execute tools
                    yield {
                        "event": "tool_executing",
                        "data": json.dumps({"status": "searching documents..."})
                    }

                    tool_results = []
                    for block in final.content:
                        if block.type == "tool_use":
                            result = await execute_tool(
                                block.name, block.input,
                                thread.project_id, db
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })

                    messages.append({"role": "assistant", "content": final.content})
                    messages.append({"role": "user", "content": tool_results})

            # Save assistant message
            await save_message(db, thread_id, "assistant", accumulated_text)

            # Track token usage
            await track_token_usage(
                db, current_user["user_id"],
                "claude-sonnet-4-5-20250929",
                total_input, total_output,
                f"/threads/{thread_id}/chat"
            )

            # Maybe update thread summary
            message_count = await get_message_count(db, thread_id)
            if message_count % 5 == 0:
                await update_thread_summary(db, client, thread_id)

            yield {
                "event": "message_complete",
                "data": json.dumps({
                    "usage": {"input_tokens": total_input, "output_tokens": total_output}
                })
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }

    return EventSourceResponse(
        event_generator(),
        headers={"X-Accel-Buffering": "no"}
    )
```

### Flutter Streaming Message Widget
```dart
// Source: flutter_client_sse + Provider patterns
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class ConversationScreen extends StatefulWidget {
  final String threadId;

  @override
  _ConversationScreenState createState() => _ConversationScreenState();
}

class _ConversationScreenState extends State<ConversationScreen> {
  final TextEditingController _controller = TextEditingController();
  String _streamingText = '';
  bool _isStreaming = false;

  Future<void> _sendMessage() async {
    final message = _controller.text.trim();
    if (message.isEmpty || _isStreaming) return;

    _controller.clear();
    setState(() {
      _isStreaming = true;
      _streamingText = '';
    });

    final aiService = context.read<AIService>();

    try {
      await for (final event in aiService.streamChat(widget.threadId, message)) {
        if (event is TextDeltaEvent) {
          setState(() {
            _streamingText += event.text;
          });
        } else if (event is MessageCompleteEvent) {
          // Refresh thread to get persisted messages
          await context.read<ThreadProvider>().selectThread(widget.threadId);
          setState(() {
            _isStreaming = false;
            _streamingText = '';
          });
        } else if (event is ErrorEvent) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: ${event.message}')),
          );
          setState(() => _isStreaming = false);
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Connection error: $e')),
      );
      setState(() => _isStreaming = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ThreadProvider>(
      builder: (context, provider, child) {
        final messages = provider.selectedThread?.messages ?? [];

        return Column(
          children: [
            Expanded(
              child: ListView.builder(
                reverse: true,
                itemCount: messages.length + (_isStreaming ? 1 : 0),
                itemBuilder: (context, index) {
                  if (_isStreaming && index == 0) {
                    return StreamingMessageBubble(text: _streamingText);
                  }

                  final msgIndex = _isStreaming ? index - 1 : index;
                  final message = messages[messages.length - 1 - msgIndex];

                  return MessageBubble(
                    content: message.content,
                    isUser: message.role == MessageRole.user,
                  );
                },
              ),
            ),
            ChatInputBar(
              controller: _controller,
              onSend: _sendMessage,
              enabled: !_isStreaming,
            ),
          ],
        );
      },
    );
  }
}

class StreamingMessageBubble extends StatelessWidget {
  final String text;

  const StreamingMessageBubble({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(
              text.isEmpty ? 'Thinking...' : text,
              style: TextStyle(
                fontStyle: text.isEmpty ? FontStyle.italic : FontStyle.normal,
              ),
            ),
          ),
          SizedBox(width: 8),
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ],
      ),
    );
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual tool loops | SDK tool_runner (beta) | 2025 | Automatic tool execution, less boilerplate |
| Claude Code SDK | Claude Agent SDK | Jan 2026 | Renamed, expanded capabilities for autonomous agents |
| Hardcoded context limits | 1M token context (beta) | 2025 | Longer conversations possible with premium pricing |
| Manual JSON streaming | SDK streaming helpers | 2024 | Simpler streaming with text_stream, get_final_message |
| WebSocket for AI streaming | SSE with sse-starlette | 2024-2025 | Simpler, PaaS-friendly, unidirectional is sufficient |

**Deprecated/outdated:**
- **Claude Code SDK:** Renamed to Claude Agent SDK in Jan 2026
- **anthropic.Anthropic() synchronous calls:** Use AsyncAnthropic for FastAPI
- **Manual SSE formatting:** Use sse-starlette for proper event formatting

## Open Questions

1. **Token Counting Accuracy**
   - What we know: Anthropic SDK provides usage in final message
   - What's unclear: How to estimate tokens BEFORE making a request for budget enforcement
   - Recommendation: Use tiktoken for estimation, track actual usage after response. Consider rejecting requests that would exceed budget based on estimate.

2. **Conversation Summarization Strategy**
   - What we know: Context can be compacted with summaries
   - What's unclear: Best approach for BA conversation summaries (preserve decisions, edge cases)
   - Recommendation: Implement hierarchical summarization, prioritize preserving: decisions made, requirements identified, edge cases discussed, action items.

3. **Tool Execution Timeout**
   - What we know: FTS5 search is fast, but future tools might be slower
   - What's unclear: How to handle slow tool execution without blocking stream
   - Recommendation: Set reasonable timeouts (5s for search), yield progress events, consider async tool execution for slow operations.

4. **Concurrent Conversations**
   - What we know: AsyncAnthropic handles concurrent requests
   - What's unclear: Rate limits per API key, concurrent stream limits
   - Recommendation: Implement request queuing at application level, monitor rate limit headers.

## Sources

### Primary (HIGH confidence)
- [Claude Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview) - Agent SDK capabilities, when to use
- [Anthropic Tool Use Implementation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) - Tool schemas, tool runner, error handling
- [Anthropic Streaming Messages](https://platform.claude.com/docs/en/api/messages-streaming) - SSE event types, streaming patterns
- [Anthropic Python SDK GitHub](https://github.com/anthropics/anthropic-sdk-python) - Streaming helpers, async usage
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) - FastAPI SSE implementation
- [flutter_client_sse Pub.dev](https://pub.dev/packages/flutter_client_sse) - Flutter SSE client

### Secondary (MEDIUM confidence)
- [Context Windows Documentation](https://platform.claude.com/docs/en/build-with-claude/context-windows) - Token limits, context management
- [Automatic Context Compaction Cookbook](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction) - SDK compaction features
- [FastAPI SSE Medium Article](https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154) - SSE best practices

### Tertiary (LOW confidence - WebSearch findings)
- [Claude Context Window 2025 Rules](https://www.datastudios.org/post/claude-context-window-token-limits-memory-policy-and-2025-rules) - Pricing, limits overview
- [Flutter Web SSE with XMLHttpRequest](https://medium.com/@thorsten_79724/actual-real-time-server-sent-events-sse-in-flutter-web-3e22f3d65445) - Web-specific SSE handling

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Anthropic SDK officially documented, sse-starlette mature
- Streaming architecture: HIGH - Official SDK streaming helpers with examples
- Tool use patterns: HIGH - Official documentation with complete examples
- Token tracking: HIGH - Usage available in API response, pricing documented
- Context management: MEDIUM - Strategies documented but need validation for BA use case
- Thread summarization: MEDIUM - Approach clear, specific prompt needs testing
- Flutter SSE: MEDIUM - Package documented, web platform needs validation

**Research date:** 2026-01-21
**Valid until:** 60 days (Anthropic SDK stable, patterns established)

**Key uncertainties flagged for validation:**
- Token counting estimation before request (test tiktoken accuracy)
- Flutter Web SSE behavior (test on actual web target)
- BA-specific summarization prompts (tune through testing)
- Rate limits for concurrent streams (monitor in production)
