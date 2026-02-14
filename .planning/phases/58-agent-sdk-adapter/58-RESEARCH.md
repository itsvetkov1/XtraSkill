# Phase 58: Agent SDK Adapter - Research

**Researched:** 2026-02-14
**Domain:** Claude Agent SDK Python Integration
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
**Multi-turn streaming visibility**
- Show tool activity indicators to user during agent execution (e.g., "Searching documents...")
- Show thinking indicator (not full thinking content) — match existing Claude thinking behavior
- Continuous stream across agent rounds — all text appends seamlessly into a single response, no visual segmentation between turns
- Source attribution chips must work identically to direct API — search_documents tool calls produce the same chip data

**Agent behavior & personality**
- Use the current BA system prompt (identical to direct API adapter) for POC
- Deferred: Future goal is to leverage Claude Code skills (business-analyst skill) instead of system prompt
- SDK uses ANTHROPIC_API_KEY (API billing) — accepted for POC evaluation
- Both SDK and CLI adapters will be built as planned (SDK = API key, CLI = subscription)

**Timeout & failure policy**
- No turn limit — POC is testing the frontier of agent capabilities, used only by controlled test group
- No request timeout — let the agent run as long as needed
- On failure: clean error only — discard partial output, show error with retry option
- Error messages include diagnostic info (which tool failed, which turn) — useful for POC debugging

**Tool context strategy**
- Use proper HTTP-based MCP transport for context propagation — production-ready architecture, not shortcuts
- Tools enhanced for agent context — SDK tools can return richer results than direct API tools
- Proactive tool use allowed — agent decides when to search docs or save artifacts (this IS the agentic advantage being tested)
- Larger context windows for search results — give the agent more document context per search to test if more context = better output

### Claude's Discretion
- Exact MCP HTTP transport implementation approach (stdio vs SSE vs streamable HTTP)
- StreamChunk event vocabulary extensions needed for agent-specific events
- How to surface tool activity indicators through existing SSE format
- Enhanced search result format details (chunk sizes, metadata richness)

### Deferred Ideas (OUT OF SCOPE)
- Claude Code skills integration (business-analyst skill as system prompt replacement) — future phase after POC evaluation
- Subscription-based billing for SDK (if Anthropic adds subscription API access) — monitor
- Production hardening (turn limits, timeouts, rate limiting) — Phase 61 decision or post-experiment
</user_constraints>

## Summary

Phase 58 implements ClaudeAgentAdapter as a production-viable LLM provider using the Claude Agent SDK Python library. The adapter translates SDK streaming events (AssistantMessage, StreamEvent, ResultMessage) into the existing StreamChunk format for SSE streaming, integrates MCP tools for search_documents and save_artifact with proper context propagation, and enables multi-turn agent loops without manual tool execution.

**Primary recommendation:** Use SDK Python library with in-process MCP tools via create_sdk_mcp_server(). Context propagation via ContextVars works for in-process tools but requires HTTP-based MCP transport for subprocess isolation (user's preferred architecture).

**Key findings:**
1. SDK v0.1.35 provides query() generator for streaming and ClaudeSDKClient for bidirectional conversations
2. Message types require translation: AssistantMessage.content[TextBlock|ToolUseBlock] → StreamChunk
3. Shared MCP tools from Phase 57 can be reused via create_ba_mcp_server() factory
4. Agent loop handles tool execution internally — adapter must NOT duplicate tool execution
5. Context propagation requires architectural decision: ContextVar (in-process) vs HTTP MCP (subprocess)

## Standard Stack

### Core Libraries

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| claude-agent-sdk | 0.1.35+ | Agent SDK client and types | Official Anthropic SDK for agent integration |
| mcp | (bundled) | MCP server protocol | Bundled with claude-agent-sdk, standard for tool integration |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| anthropic | 0.76.0 | Direct API (existing) | Already in requirements.txt, SDK uses same API key |
| asyncio | stdlib | Async generators | Required for streaming translation |
| contextvars | stdlib | Request context propagation | Passing db/project_id to tools (in-process only) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| In-process MCP (create_sdk_mcp_server) | HTTP MCP server | HTTP = subprocess isolation (user's preference) but adds latency/complexity |
| SDK query() function | ClaudeSDKClient class | Client = bidirectional streaming, but query() simpler for single-turn adapter pattern |
| ContextVar for context | HTTP headers in MCP | HTTP headers = proper isolation, ContextVar = simpler but no subprocess boundary |

**Installation:**
```bash
# Already in requirements.txt from Phase 57
pip install claude-agent-sdk>=0.1.35
```

## Architecture Patterns

### Recommended Project Structure

```
backend/app/services/
├── llm/
│   ├── base.py                    # LLMAdapter ABC, StreamChunk, LLMProvider enum
│   ├── claude_agent_adapter.py    # NEW: Agent SDK adapter (Phase 58)
│   ├── anthropic_adapter.py       # Existing direct API adapter
│   └── factory.py                 # LLMFactory with claude-code-sdk registration
├── mcp_tools.py                   # Shared MCP tool wrappers (Phase 57)
└── ai_service.py                  # AIService (unchanged - adapter pattern isolation)
```

### Pattern 1: Message Type Translation

**What:** Convert Agent SDK streaming events to StreamChunk format

**When to use:** In ClaudeAgentAdapter.stream_chat() method

**Example:**
```python
# Source: Official docs + Phase 57 research
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, StreamEvent, ResultMessage, TextBlock, ToolUseBlock

async def stream_chat(self, messages, system_prompt, tools, max_tokens):
    # Configure SDK options
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        mcp_servers={"ba": self.mcp_server},
        include_partial_messages=True,  # Enable StreamEvent for incremental text
        model=self.model,
    )

    # Convert messages to prompt format
    prompt = self._convert_messages_to_prompt(messages)

    # Stream from SDK
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, StreamEvent):
            # Partial streaming events
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    yield StreamChunk(chunk_type="text", content=delta.get("text", ""))

        elif isinstance(message, AssistantMessage):
            # Complete message with all content blocks
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Only yield if not already streamed via StreamEvent
                    if not options.include_partial_messages:
                        yield StreamChunk(chunk_type="text", content=block.text)

                elif isinstance(block, ToolUseBlock):
                    # Yield tool_use for visibility (SDK executes internally)
                    yield StreamChunk(
                        chunk_type="tool_use",
                        tool_call={
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )

        elif isinstance(message, ResultMessage):
            # Final result with usage stats
            yield StreamChunk(
                chunk_type="complete",
                usage={
                    "input_tokens": message.usage.get("input_tokens", 0),
                    "output_tokens": message.usage.get("output_tokens", 0),
                }
            )
```

### Pattern 2: MCP Server Integration with Context Propagation

**What:** Connect SDK agent to BA Assistant tools with database/user context

**When to use:** During adapter initialization

**Example:**
```python
# Source: mcp_tools.py from Phase 57 + SDK docs
from app.services.mcp_tools import (
    create_ba_mcp_server,
    _db_context,
    _project_id_context,
    _thread_id_context,
    _documents_used_context
)

class ClaudeAgentAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

        # Create shared MCP server (from Phase 57 factory)
        self.mcp_server = create_ba_mcp_server()

    async def stream_chat(self, messages, system_prompt, tools, max_tokens):
        # Set context variables for tool access
        # NOTE: This works for in-process tools only
        # For subprocess isolation (user's preference), use HTTP MCP transport
        _db_context.set(db)
        _project_id_context.set(project_id)
        _thread_id_context.set(thread_id)
        _documents_used_context.set([])  # Track docs for source attribution

        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"ba": self.mcp_server},  # SDK connects to MCP server
            model=self.model,
        )

        # ... stream_chat implementation
```

**Alternative: HTTP MCP Transport (for subprocess isolation)**
```python
# Source: Phase 57 research PITFALL-03
# This approach enables subprocess isolation (user's preferred architecture)
from mcp.server.streamable_http import StreamableHTTPServerManager

# Start HTTP MCP server in background
mcp_http_server = StreamableHTTPServerManager(
    server=self.mcp_server,
    port=8001
)
await mcp_http_server.start()

# Pass context via HTTP headers
options = ClaudeAgentOptions(
    mcp_servers={
        "ba": {
            "type": "http",
            "url": "http://localhost:8001",
            "headers": {
                "X-Project-ID": project_id,
                "X-Thread-ID": thread_id,
                "X-DB-Session-ID": db_session_id  # Lookup session from pool
            }
        }
    }
)

# Tools read context from HTTP headers instead of ContextVar
```

### Pattern 3: Agent Loop Integration (Bypass Manual Tool Loop)

**What:** Let SDK handle tool execution internally, don't duplicate in AIService

**When to use:** AIService must detect agent providers and skip manual tool loop

**Example:**
```python
# Source: Phase 57 research PITFALL-04
class AIService:
    async def stream_chat(self, conversation, project_id, thread_id, db):
        adapter = LLMFactory.create(provider)

        # Check if adapter is agent-based (handles tools internally)
        if isinstance(adapter, ClaudeAgentAdapter):
            # Agent SDK executes tools internally via MCP
            # AIService just forwards events (no manual tool loop)
            async for chunk in adapter.stream_chat(conversation, system_prompt, tools):
                yield chunk
        else:
            # Direct API adapters need manual tool loop
            async for chunk in self._stream_with_manual_tool_loop(adapter, conversation):
                yield chunk
```

### Anti-Patterns to Avoid

- **Double tool execution:** Yielding tool_use chunks AND manually executing tools in AIService (causes duplicate calls)
- **ContextVar across subprocess boundaries:** ContextVar does NOT propagate to subprocesses (Phase 57 PITFALL-03)
- **Buffering entire response:** SDK streams incrementally, don't accumulate all text before yielding
- **Ignoring ResultMessage usage:** Frontend needs usage stats for token tracking

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Streaming event parsing | Custom JSON parser for SDK events | Built-in isinstance() checks on message types | SDK provides typed message classes (AssistantMessage, StreamEvent, etc.) |
| Tool execution loop | Manual tool calling after tool_use chunks | SDK's internal agent loop via MCP servers | SDK handles multi-turn tool execution automatically |
| Session state management | Custom conversation history storage | SDK's ConversationSession (if needed) OR stateless query() | query() is simpler for adapter pattern, ConversationSession adds complexity |
| Context propagation | Custom serialization for DB sessions | HTTP MCP transport with headers | Proper isolation, production-ready pattern |

**Key insight:** Agent SDK is designed for autonomous multi-turn workflows. Fighting this design (trying to manually control tool execution) creates complexity and bugs. Lean into the agent loop pattern.

## Common Pitfalls

### Pitfall 1: Event Stream Translation Data Loss

**What goes wrong:** SDK produces multi-turn agent loop events that don't map cleanly to existing StreamChunk format designed for single-turn API responses

**Why it happens:** AssistantMessage can contain multiple TextBlocks, ToolUseBlocks, and ToolResultBlocks in nested/interleaved order across multiple turns

**How to avoid:**
- Set `include_partial_messages=True` to get StreamEvent deltas for incremental text
- Yield separate StreamChunk for each content block (don't merge)
- Track whether text was already streamed via StreamEvent to avoid duplicates
- Accumulate usage across ALL turns, not just final ResultMessage

**Warning signs:**
- Frontend receives incomplete text (missing sections)
- Token usage in UI differs from API response
- Tool result content missing from UI

**Source:** Phase 57 research PITFALL-01

### Pitfall 2: ContextVar Does NOT Cross Subprocess Boundaries

**What goes wrong:** Existing mcp_tools.py uses ContextVar to access database sessions, but ContextVar does NOT propagate to subprocess (if SDK spawns CLI internally)

**Why it happens:** ContextVar is tied to asyncio event loop and task tree, subprocess runs in different Python interpreter

**How to avoid:**
- **Option A (simpler):** Use in-process MCP via create_sdk_mcp_server() — ContextVar works
- **Option B (user's preference):** Use HTTP MCP transport — pass context via HTTP headers
- Validate context propagation in unit tests (mock tool calls should receive expected context)

**Warning signs:**
- Tools fail with "context not available" errors
- LookupError when accessing _db_context.get()
- Tools work in direct API mode but fail in agent mode

**Source:** Phase 57 research PITFALL-03

### Pitfall 3: Tool Execution Model Mismatch

**What goes wrong:** AIService sees tool_use chunks and tries to execute tools manually, but SDK already executed them internally

**Why it happens:** LLMAdapter pattern assumes stateless single-turn executors, Agent SDK is stateful multi-turn orchestrator

**How to avoid:**
- Add provider check in AIService.stream_chat()
- Skip manual tool loop for ClaudeAgentAdapter
- Yield tool_use chunks for visibility ONLY (not for execution trigger)
- Document that agent providers handle tools internally

**Warning signs:**
- Tools executed twice (check database logs)
- Infinite agent loops (max_turns reached on simple requests)
- "Tool result without preceding tool call" errors

**Source:** Phase 57 research PITFALL-04

### Pitfall 4: Cost and Latency Overhead

**What goes wrong:** SDK adds ~1,100 tokens overhead per request (tool definitions, system prompt) and 200-500ms subprocess spawn latency

**Why it happens:** Agent SDK designed for complex multi-turn workflows where overhead is amortized

**How to avoid:**
- Monitor token usage via ResultMessage.usage
- For POC, accept overhead (testing quality, not cost optimization)
- Log input/output tokens separately for analysis
- Consider tool description optimization (Phase 57 research PITFALL-06)

**Warning signs:**
- Input token counts 2-3x higher than direct API for same conversation
- Streaming starts 300ms+ after request (vs <100ms for direct API)

**Source:** Phase 57 research PITFALL-06

## Code Examples

Verified patterns from official sources and Phase 57 research:

### Complete Adapter Implementation Skeleton

```python
# Source: Phase 57 architecture + SDK docs
from typing import AsyncGenerator, Dict, Any, List, Optional
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, StreamEvent, ResultMessage, TextBlock, ToolUseBlock

from .base import LLMAdapter, LLMProvider, StreamChunk
from app.services.mcp_tools import (
    create_ba_mcp_server,
    _db_context,
    _project_id_context,
    _thread_id_context,
    _documents_used_context
)

DEFAULT_MODEL = "claude-sonnet-4-5-20250514"

class ClaudeAgentAdapter(LLMAdapter):
    """
    Claude Agent SDK adapter.

    Translates SDK streaming events to StreamChunk format. Uses shared
    MCP tools from mcp_tools.py for search_documents and save_artifact.

    Agent loop handles tool execution internally — AIService must NOT
    execute tools manually for this provider.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.mcp_server = create_ba_mcp_server()

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.CLAUDE_CODE_SDK

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response from Agent SDK.

        SDK handles multi-turn agent loop internally via MCP tools.
        This method translates SDK events to StreamChunk format.
        """
        # Set context for in-process MCP tools
        # NOTE: For subprocess isolation, use HTTP MCP transport instead
        db = get_db_from_request_context()  # Implementation detail
        project_id = get_project_id_from_messages(messages)
        thread_id = get_thread_id_from_request_context()

        _db_context.set(db)
        _project_id_context.set(project_id)
        _thread_id_context.set(thread_id)
        _documents_used_context.set([])

        # Configure SDK options
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"ba": self.mcp_server},
            include_partial_messages=True,  # Enable StreamEvent
            model=self.model,
        )

        # Convert messages to SDK prompt format
        prompt = self._convert_messages_to_prompt(messages)

        try:
            # Stream from SDK
            async for message in query(prompt=prompt, options=options):
                # Handle partial streaming events
                if isinstance(message, StreamEvent):
                    event = message.event
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield StreamChunk(
                                chunk_type="text",
                                content=delta.get("text", "")
                            )

                # Handle complete assistant messages
                elif isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            # Yield for visibility (SDK executes internally)
                            yield StreamChunk(
                                chunk_type="tool_use",
                                tool_call={
                                    "id": block.id,
                                    "name": block.name,
                                    "input": block.input,
                                }
                            )

                # Handle final result
                elif isinstance(message, ResultMessage):
                    yield StreamChunk(
                        chunk_type="complete",
                        usage={
                            "input_tokens": message.usage.get("input_tokens", 0),
                            "output_tokens": message.usage.get("output_tokens", 0),
                        }
                    )

        except Exception as e:
            yield StreamChunk(
                chunk_type="error",
                error=f"Agent SDK error: {str(e)}"
            )

    def _convert_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """Convert LLMAdapter message format to SDK prompt string."""
        # Implementation: Extract last user message or format conversation
        if messages:
            return messages[-1].get("content", "")
        return ""
```

### AIService Integration (Skip Manual Tool Loop)

```python
# Source: Phase 57 research
class AIService:
    async def stream_chat(self, conversation, project_id, thread_id, db):
        provider = get_provider_for_thread(thread_id)
        adapter = LLMFactory.create(provider)

        # Agent providers handle tools internally
        if isinstance(adapter, (ClaudeAgentAdapter, ClaudeCLIAdapter)):
            async for chunk in adapter.stream_chat(conversation, SYSTEM_PROMPT, tools):
                # No manual tool execution — just forward chunks
                yield self._format_sse_event(chunk)
        else:
            # Direct API providers need manual tool loop
            async for chunk in self._stream_with_manual_tool_loop(adapter, conversation):
                yield self._format_sse_event(chunk)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual tool loops in application code | SDK-managed agent loops via MCP | SDK v0.1.0+ (2025) | Simpler application code, but less control |
| Custom streaming parsers | Typed message classes (AssistantMessage, StreamEvent) | SDK v0.1.0+ | Type safety, easier event handling |
| Session state in database | SDK ConversationSession API | SDK v0.1.0+ | Optional — stateless query() still works |
| Subprocess CLI spawning | Bundled CLI with Python SDK | SDK v0.1.30+ | No separate installation needed |

**Deprecated/outdated:**
- **Force tool use:** Extended thinking incompatible with forced tool use (use autonomous tool selection)
- **Nested subagents:** SDK limitation — chain subagents sequentially from main conversation

## Open Questions

1. **HTTP MCP Transport Implementation**
   - What we know: mcp.server.streamable_http available, enables subprocess isolation
   - What's unclear: Best practice for starting/stopping HTTP MCP server per request vs singleton
   - Recommendation: Research mcp.server.streamable_http_manager during implementation

2. **StreamChunk Event Vocabulary Extensions**
   - What we know: User wants tool activity indicators ("Searching documents...")
   - What's unclear: Should we add new chunk_type values (e.g., "tool_executing") or use existing "tool_use" with metadata?
   - Recommendation: Extend StreamChunk with optional metadata field for tool status

3. **Enhanced Search Result Format**
   - What we know: User wants larger context windows for agent mode
   - What's unclear: How much larger? 3 results vs 5? Longer snippets?
   - Recommendation: Make configurable, start with 5 results (vs 3 for direct API) and 500-char snippets (vs 300)

## Sources

### Primary (HIGH confidence)
- [Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python) - Official API documentation
- [Agent SDK Streaming Output](https://platform.claude.com/docs/en/agent-sdk/streaming-output) - StreamEvent and message types
- [claude-agent-sdk GitHub](https://github.com/anthropics/claude-agent-sdk-python) - Examples and source code
- Phase 57 research documents:
  - ARCHITECTURE.md - Integration patterns and data flow
  - PITFALLS.md - Critical implementation warnings
  - FEATURES.md - Agent capabilities vs direct API

### Secondary (MEDIUM confidence)
- [Getting started with Anthropic Claude Agent SDK — Python](https://medium.com/@aiablog/getting-started-with-anthropic-claude-agent-sdk-python-826a2216381d) - Tutorial (verified with official docs)
- [Streaming Mode Example](https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/streaming_mode.py) - Official example code

### Tertiary (LOW confidence)
- None — all research verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official SDK documentation and phase 57 research
- Architecture: HIGH - Patterns from official docs + verified with existing codebase
- Pitfalls: HIGH - Documented in phase 57 research with official source verification

**Research date:** 2026-02-14
**Valid until:** 60 days (stable SDK API, minimal churn expected)

---

## Ready for Planning

Research complete. Planner can now create detailed PLAN.md files with:
- Task-level implementation steps
- Verification commands
- Integration points with existing codebase
- Test strategy for adapter functionality

Sources:
- [Agent SDK reference - Python - Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/python)
- [Stream responses in real-time - Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/streaming-output)
- [GitHub - anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
- [claude-agent-sdk-python/examples/streaming_mode.py](https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/streaming_mode.py)
