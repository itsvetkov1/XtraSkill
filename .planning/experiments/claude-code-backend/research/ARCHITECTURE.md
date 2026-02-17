# Architecture Patterns: Claude Code Integration

**Domain:** AI Backend Provider Integration
**Researched:** 2026-02-13
**Overall confidence:** HIGH

## Executive Summary

Claude Code can integrate with the BA Assistant backend using two distinct architectural approaches: **Agent SDK (Python library)** and **CLI subprocess**. Both must conform to the existing `LLMAdapter` abstract base class pattern.

**Key finding:** The Agent SDK Python library **does NOT require separate Claude Code CLI installation** — the CLI is bundled with the package (v0.1.35+). This invalidates the Phase 4.1 rejection rationale that assumed heavy infrastructure dependencies.

**Integration challenges:**
1. **SDK approach:** Event stream translation (AssistantMessage → StreamChunk), tool execution model mismatch (MCP tools vs Anthropic format), session state management
2. **CLI approach:** JSON parsing, subprocess lifecycle, stderr handling, process isolation

Both approaches require **new adapter classes** but minimal changes to existing `ai_service.py` tool loop.

## Approach A: Agent SDK Python Library Integration

### Current State (2026)

**Runtime dependencies:** Python 3.10+, Node.js 18+ (bundled with package)
**Installation:** `pip install claude-agent-sdk` (v0.1.35)
**CLI dependency:** Bundled automatically — NO separate installation needed

**Sources:**
- [Claude Agent SDK Python - PyPI](https://pypi.org/project/claude-agent-sdk/)
- [Agent SDK Overview - Official Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)

### Architecture Components

#### New Components Required

**File:** `backend/app/services/llm/claude_agent_adapter.py`
```python
class ClaudeAgentAdapter(LLMAdapter):
    """
    Claude Agent SDK adapter.

    Translates Agent SDK streaming events to StreamChunk format.
    Uses existing BA Assistant tool definitions via MCP wrapper.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or "claude-sonnet-4-5-20250514"
        self.tools_server = None  # MCP server for BA tools

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.CLAUDE_CODE

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Convert SDK events to StreamChunk format."""
        # Implementation details below
```

**File:** `backend/app/services/llm/base.py` (MODIFIED)
```python
class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    CLAUDE_CODE = "claude_code"  # NEW
```

**File:** `backend/app/services/agent_service.py` (REFACTORED)
- Extract tool wrappers from existing `agent_service.py` (lines 40-196)
- Create reusable `create_ba_mcp_server()` function
- Both `AgentService` (existing) and `ClaudeAgentAdapter` (new) use same MCP server

### Data Flow Diagram

```
[FastAPI Endpoint]
    |
    v
[AIService.stream_chat()]
    |
    +-- Uses LLMFactory.create("claude_code")
    |
    v
[ClaudeAgentAdapter.stream_chat()]
    |
    +-- Creates ClaudeAgentOptions with:
    |   - system_prompt (BA Assistant prompt)
    |   - mcp_servers (search_documents, save_artifact)
    |   - max_turns (prevent loops)
    |
    v
[claude_agent_sdk.query()]
    |
    +-- Yields: AssistantMessage, StreamEvent, ResultMessage
    |
    v
[Translation Layer]
    |
    +-- AssistantMessage.content[TextBlock] → StreamChunk(chunk_type="text")
    +-- AssistantMessage.content[ToolUseBlock] → StreamChunk(chunk_type="tool_use")
    +-- ResultMessage.usage → StreamChunk(chunk_type="complete")
    +-- StreamEvent (if include_partial_messages) → StreamChunk(chunk_type="text")
    |
    v
[AIService tool loop]
    |
    +-- NO CHANGES NEEDED (adapter handles tool execution via MCP)
    +-- Tool results flow through SDK's internal loop
    |
    v
[SSE Response to Frontend]
```

### Message Type Translation

**SDK → StreamChunk mapping:**

| SDK Message Type | StreamChunk Type | Notes |
|-----------------|------------------|-------|
| `AssistantMessage.content[TextBlock]` | `chunk_type="text"` | Direct text streaming |
| `AssistantMessage.content[ToolUseBlock]` | `chunk_type="tool_use"` | Tool call request |
| `ResultMessage.usage` | `chunk_type="complete"` | Final usage stats |
| `StreamEvent` (partial) | `chunk_type="text"` | Incremental text deltas |
| SDK error | `chunk_type="error"` | Error handling |

**Key challenge:** SDK handles tool execution internally (via MCP), but AIService expects external tool loop. **Solution:** Let SDK handle tools internally, yield tool_use chunks for visibility only (not for AIService to execute).

### Tool Integration Pattern

**Existing BA Assistant tools** (`search_documents`, `save_artifact`) need wrapping:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("search_documents", "Search project documents...", {"query": str})
async def search_documents_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    # Get DB session from ContextVar
    db = _db_context.get()
    project_id = _project_id_context.get()

    # Call existing search_documents function
    results = await search_documents(db, project_id, args["query"])

    # Format for SDK
    return {"content": [{"type": "text", "text": format_results(results)}]}

# Create MCP server
ba_tools_server = create_sdk_mcp_server(
    name="ba-tools",
    version="1.0.0",
    tools=[search_documents_tool, save_artifact_tool]
)
```

**Context variables:** Reuse existing pattern from `agent_service.py` (lines 32-36):
```python
_db_context: ContextVar[Any] = ContextVar("db_context")
_project_id_context: ContextVar[str] = ContextVar("project_id_context")
_thread_id_context: ContextVar[str] = ContextVar("thread_id_context")
```

### Integration Points

**Modified files:**
1. `backend/app/services/llm/base.py` — Add `LLMProvider.CLAUDE_CODE`
2. `backend/app/services/llm/factory.py` — Register `ClaudeAgentAdapter`
3. `backend/app/services/llm/claude_agent_adapter.py` — NEW adapter implementation
4. `backend/app/services/mcp_tools.py` — NEW shared MCP tool wrappers
5. `backend/app/services/agent_service.py` — REFACTOR to use shared MCP tools

**Unchanged files:**
- `backend/app/services/ai_service.py` — NO changes (adapter conforms to LLMAdapter)
- `backend/app/routes/threads.py` — NO changes (provider selection via DB field)

### Pros/Cons

**Advantages:**
- Agent-level capabilities (self-review, multi-turn reasoning)
- Built-in tool execution (no external loop needed)
- Session management (conversation continuity)
- File operations (could enable artifact validation)
- Hooks for auditing/logging
- Python native (no subprocess overhead)

**Disadvantages:**
- Dual tool execution models (MCP + Anthropic format)
- Complex event translation layer
- Session state management overhead
- Heavier dependency footprint (Node.js bundled)
- Requires refactoring existing `agent_service.py` tools

**Confidence:** HIGH (official SDK with production hosting patterns documented)

---

## Approach B: CLI Subprocess Integration

### Architecture Components

#### New Components Required

**File:** `backend/app/services/llm/claude_cli_adapter.py`
```python
class ClaudeCLIAdapter(LLMAdapter):
    """
    Claude Code CLI subprocess adapter.

    Spawns CLI process, parses JSON output, translates to StreamChunk.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or "claude-sonnet-4-5-20250929"
        self.cli_path = "claude"  # Assumes CLI in PATH

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Spawn CLI subprocess and parse JSON output."""
        # Implementation details below
```

**File:** `backend/app/services/tool_registry.py` (NEW)
```python
class ToolRegistry:
    """
    Converts BA Assistant tools to CLI-compatible format.

    Translates tool calls from CLI JSON to function executions.
    """

    def register_tool(self, name: str, fn: Callable):
        """Register tool with name."""

    async def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute registered tool and return result string."""
```

### Data Flow Diagram

```
[FastAPI Endpoint]
    |
    v
[AIService.stream_chat()]
    |
    +-- Uses LLMFactory.create("claude_cli")
    |
    v
[ClaudeCLIAdapter.stream_chat()]
    |
    +-- Builds CLI command:
    |   claude -p "prompt" \
    |     --output-format stream-json \
    |     --system-prompt "BA Assistant prompt" \
    |     --max-turns 3 \
    |     --model claude-sonnet-4-5-20250929
    |
    v
[subprocess.Popen]
    |
    +-- stdin: user prompt
    +-- stdout: JSON stream (line-delimited)
    +-- stderr: debug logs (ignored or logged)
    |
    v
[JSON Parser]
    |
    +-- Reads stdout line-by-line
    +-- json.loads() each line
    +-- Handles StreamEvent, ResultMessage, errors
    |
    v
[Translation Layer]
    |
    +-- CLI "text_delta" → StreamChunk(chunk_type="text")
    +-- CLI "tool_use" → StreamChunk(chunk_type="tool_use")
    +-- CLI "result" → StreamChunk(chunk_type="complete")
    +-- CLI "error" → StreamChunk(chunk_type="error")
    |
    v
[AIService tool loop]
    |
    +-- Executes tools via ToolRegistry
    +-- Returns results to CLI via stdin continuation (?)
    |   OR: Re-spawn CLI with updated conversation history
    |
    v
[SSE Response to Frontend]
```

### CLI Subprocess Pattern

**Based on search results:**
- Use `--print` (headless mode) with `--output-format stream-json`
- Parse line-delimited JSON from stdout
- Handle UTF-8 encoding
- Use `CREATE_NEW_PROCESS_GROUP` on Windows for process tree management

**Example command:**
```bash
claude -p \
  --output-format stream-json \
  --system-prompt-file /tmp/ba_system_prompt.txt \
  --max-turns 3 \
  --model claude-sonnet-4-5-20250929 \
  "User message here"
```

**JSON output structure (from search results):**
```json
{
  "type": "stream_event",
  "subtype": "text_delta",
  "content": "text chunk",
  "session_id": "uuid",
  "uuid": "event-id"
}
```

**Sources:**
- [CLI Reference - Official Docs](https://code.claude.com/docs/en/cli-reference)
- [Running Claude Code from Windows CLI - Practical Guide](https://dstreefkerk.github.io/2026-01-running-claude-code-from-windows-cli/)
- [What is --output-format in Claude Code](https://claudelog.com/faqs/what-is-output-format-in-claude-code/)

### Tool Execution Challenge

**Problem:** CLI expects built-in tools (Read, Write, Bash), not BA Assistant tools (search_documents, save_artifact).

**Solution options:**

1. **MCP server approach (recommended):**
   - Create MCP server process for BA tools
   - Pass to CLI via `--mcp-config` flag
   - CLI handles tool execution internally
   - Parse tool results from JSON stream

2. **Tool-less mode:**
   - Disable all tools (`--tools ""`)
   - CLI acts as pure LLM (no agent capabilities)
   - Defeats purpose of using Claude Code

3. **Hybrid approach:**
   - Use CLI for text generation only
   - Parse tool_use requests from JSON
   - Execute tools in Python (via AIService loop)
   - Re-invoke CLI with tool results

**Recommended:** Option 1 (MCP server) — maintains agent capabilities while integrating BA tools.

### Pros/Cons

**Advantages:**
- Full Claude Code feature set (all CLI flags available)
- Process isolation (security)
- No Python dependency conflicts
- Easier debugging (can test CLI independently)
- Structured JSON output mode
- Session management via `--session-id` flag

**Disadvantages:**
- Subprocess overhead (spawn per request)
- JSON parsing complexity
- Tool integration via MCP server (additional process)
- Harder to handle streaming (line buffering)
- Process lifecycle management (zombies, timeouts)
- Windows-specific quirks (process groups)

**Confidence:** MEDIUM (documented patterns exist, but subprocess integration adds complexity)

---

## Comparison Matrix

| Criterion | Agent SDK | CLI Subprocess |
|-----------|-----------|----------------|
| **Installation** | `pip install claude-agent-sdk` | `npm install -g @anthropic-ai/claude-code` |
| **Dependencies** | Python 3.10+, Node.js 18+ (bundled) | Node.js 18+, separate install |
| **Integration complexity** | Medium (event translation) | High (subprocess + JSON parsing) |
| **Tool execution** | MCP (internal) | MCP server (external process) OR Python fallback |
| **Streaming** | Native AsyncGenerator | Line-buffered JSON parsing |
| **Session management** | Built-in (ClaudeSDKClient) | `--session-id` flag |
| **Error handling** | Python exceptions | Exit codes + stderr |
| **Process isolation** | In-process | Subprocess |
| **Performance** | Lower latency (no subprocess) | Higher latency (spawn overhead) |
| **Debugging** | Python debugger | CLI logs + JSON output |
| **Production viability** | HIGH (documented hosting patterns) | MEDIUM (subprocess management risks) |

---

## Recommended Approach

**PRIMARY: Agent SDK Python Library (Approach A)**

**Rationale:**
1. **Invalidated rejection reason:** Phase 4.1 rejected SDK due to "requires Claude Code CLI as runtime dependency" — this is **no longer true** (CLI bundled with package)
2. **Native Python integration:** No subprocess overhead, direct async/await support
3. **Production hosting patterns:** Official docs provide container deployment guides
4. **Tool execution model:** MCP server approach aligns with SDK's design
5. **Lower operational complexity:** No process lifecycle management

**SECONDARY: CLI Subprocess (Approach B for comparison)**

Build both as experiment to measure quality differences. CLI approach useful if:
- Agent SDK proves too heavyweight in production
- Subprocess isolation provides security benefits
- CLI-specific flags needed (e.g., `--json-schema` for structured outputs)

---

## Build Order (Phased Approach)

### Phase 1: Shared MCP Tools (Prerequisite)
**Goal:** Extract tool wrappers from `agent_service.py` into reusable module

**Files created:**
- `backend/app/services/mcp_tools.py` — Shared MCP tool wrappers

**Files modified:**
- `backend/app/services/agent_service.py` — Import from `mcp_tools.py`

**Verification:** Existing `AgentService` works unchanged

**Estimated effort:** 1-2 hours

---

### Phase 2: Agent SDK Adapter (Primary)
**Goal:** Create Claude Agent SDK adapter conforming to `LLMAdapter` ABC

**Files created:**
- `backend/app/services/llm/claude_agent_adapter.py` — New adapter

**Files modified:**
- `backend/app/services/llm/base.py` — Add `LLMProvider.CLAUDE_CODE`
- `backend/app/services/llm/factory.py` — Register adapter
- `backend/requirements.txt` — Add `claude-agent-sdk==0.1.35`

**Implementation steps:**
1. Create adapter class skeleton
2. Implement message type translation (AssistantMessage → StreamChunk)
3. Configure MCP server with BA tools
4. Handle tool execution via SDK internal loop
5. Add error handling (CLINotFoundError, ProcessError)
6. Test with existing `/api/threads/{thread_id}/chat` endpoint

**Verification:**
- New thread with `model_provider="claude_code"` streams correctly
- Tool calls (search_documents, save_artifact) work
- Usage stats captured
- Error handling graceful

**Estimated effort:** 4-6 hours

---

### Phase 3: CLI Subprocess Adapter (Secondary)
**Goal:** Create CLI subprocess adapter for comparison

**Files created:**
- `backend/app/services/llm/claude_cli_adapter.py` — New adapter
- `backend/app/services/cli_process.py` — Subprocess management utilities

**Files modified:**
- `backend/app/services/llm/factory.py` — Register CLI adapter

**Implementation steps:**
1. Subprocess spawning with proper flags
2. Line-buffered JSON parsing
3. Event translation (CLI JSON → StreamChunk)
4. Process lifecycle (timeout, cleanup, zombie prevention)
5. Error handling (exit codes, stderr)
6. MCP server integration (if tool support needed)

**Verification:**
- Same tests as Phase 2
- Compare quality/performance with SDK adapter

**Estimated effort:** 6-8 hours

---

### Phase 4: Quality Comparison
**Goal:** Measure document quality differences

**Approach:**
- Generate 5 BRDs using direct Anthropic API (baseline)
- Generate 5 BRDs using Agent SDK adapter
- Generate 5 BRDs using CLI adapter
- Compare: completeness, structural consistency, error handling

**Metrics:**
- Section completeness (all 13 BRD sections present?)
- Acceptance criteria quality (measurable thresholds, explicit actors)
- Error scenario coverage (at least 2 per requirement)
- Consistency (no duplicate headings, no missing definitions)

**Decision criteria:**
- If SDK/CLI > 20% better than direct API → adopt for production
- If SDK significantly better than CLI → deprecate CLI path
- If no measurable improvement → stay with direct API

**Estimated effort:** 3-4 hours

---

## Integration Points Summary

### New Files
| File | Purpose | Approach A | Approach B |
|------|---------|------------|------------|
| `llm/claude_agent_adapter.py` | Agent SDK adapter | Required | — |
| `llm/claude_cli_adapter.py` | CLI subprocess adapter | — | Required |
| `mcp_tools.py` | Shared MCP tool wrappers | Required | Optional |
| `cli_process.py` | Subprocess utilities | — | Required |

### Modified Files
| File | Change | Approach A | Approach B |
|------|--------|------------|------------|
| `llm/base.py` | Add `LLMProvider.CLAUDE_CODE` | Modified | Modified |
| `llm/factory.py` | Register new adapter | Modified | Modified |
| `agent_service.py` | Use shared MCP tools | Refactored | Unchanged |

### Unchanged Files (Both Approaches)
- `ai_service.py` — Adapter pattern isolates changes
- `routes/threads.py` — Provider selection via DB field
- `frontend/` — No changes (provider transparent to UI)

---

## Architecture Diagrams

### Current Architecture (Baseline)

```
┌─────────────────────────────────────────────────────┐
│ FastAPI Endpoint (/api/threads/{id}/chat)          │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ AIService.stream_chat()                             │
│ - Builds conversation context                       │
│ - Calls LLMAdapter.stream_chat()                    │
│ - Executes tools (search_documents, save_artifact) │
│ - Handles tool use loop                             │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ LLMAdapter (ABC)                                    │
│ ├─ AnthropicAdapter                                 │
│ ├─ GeminiAdapter                                    │
│ └─ DeepSeekAdapter                                  │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ StreamChunk (normalized format)                     │
│ - chunk_type: text | tool_use | complete | error    │
│ - content: str                                       │
│ - tool_call: {id, name, input}                      │
│ - usage: {input_tokens, output_tokens}              │
└─────────────────────────────────────────────────────┘
```

### Agent SDK Integration (Approach A)

```
┌─────────────────────────────────────────────────────┐
│ AIService.stream_chat()                             │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ ClaudeAgentAdapter                                  │
│ - Sets context variables (db, project_id, thread_id)│
│ - Creates ClaudeAgentOptions:                       │
│   - system_prompt                                    │
│   - mcp_servers (ba-tools)                          │
│   - max_turns (prevent loops)                       │
│ - Calls query() from claude_agent_sdk              │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ claude_agent_sdk.query()                            │
│ - Yields AssistantMessage, StreamEvent, ResultMsg   │
│ - Executes tools internally via MCP                 │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ MCP Server (ba-tools)                               │
│ ├─ @tool("search_documents")                        │
│ │   └─ Reads ContextVar → calls search_documents() │
│ └─ @tool("save_artifact")                           │
│     └─ Reads ContextVar → creates Artifact         │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ Translation Layer (in ClaudeAgentAdapter)           │
│ - AssistantMessage.content[TextBlock] → text chunk  │
│ - ToolUseBlock → tool_use chunk (visibility only)   │
│ - ResultMessage.usage → complete chunk              │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ StreamChunk → SSE Response                          │
└─────────────────────────────────────────────────────┘
```

### CLI Subprocess Integration (Approach B)

```
┌─────────────────────────────────────────────────────┐
│ AIService.stream_chat()                             │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ ClaudeCLIAdapter                                    │
│ - Builds CLI command:                               │
│   claude -p --output-format stream-json \           │
│     --system-prompt-file /tmp/ba_prompt.txt \       │
│     --mcp-config /tmp/ba_tools_mcp.json \           │
│     --max-turns 3 "user message"                    │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ subprocess.Popen (claude CLI process)               │
│ - stdout: Line-delimited JSON                       │
│ - stderr: Debug logs (logged or ignored)            │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ JSON Parser                                         │
│ - Reads stdout line-by-line                         │
│ - json.loads() each line                            │
│ - Handles: text_delta, tool_use, result, error     │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ MCP Server Process (ba-tools) [OPTIONAL]           │
│ - Separate process spawned by CLI                   │
│ - Communicates via stdio                            │
│ - Executes search_documents, save_artifact          │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ Translation Layer (in ClaudeCLIAdapter)             │
│ - CLI "text_delta" → text chunk                     │
│ - CLI "tool_use" → tool_use chunk                   │
│ - CLI "result" → complete chunk                     │
└───────────────────┬─────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────┐
│ StreamChunk → SSE Response                          │
└─────────────────────────────────────────────────────┘
```

---

## Critical Implementation Details

### Agent SDK: Message Translation

```python
async def stream_chat(self, messages, system_prompt, tools, max_tokens):
    # Configure SDK options
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        mcp_servers={"ba": self.tools_server},
        allowed_tools=["mcp__ba__search_documents", "mcp__ba__save_artifact"],
        permission_mode="acceptEdits",
        include_partial_messages=True,  # Enable StreamEvent
        max_turns=3,  # Prevent infinite loops
        model=self.model,
    )

    # Convert messages to prompt format
    prompt = self._convert_messages_to_prompt(messages)

    # Stream from SDK
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield StreamChunk(chunk_type="text", content=block.text)
                elif isinstance(block, ToolUseBlock):
                    # Yield for visibility only (SDK handles execution)
                    yield StreamChunk(
                        chunk_type="tool_use",
                        tool_call={
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )

        elif isinstance(message, StreamEvent):
            # Partial message streaming
            if message.event.get("type") == "content_block_delta":
                delta = message.event.get("delta", {})
                if delta.get("type") == "text_delta":
                    yield StreamChunk(chunk_type="text", content=delta.get("text", ""))

        elif isinstance(message, ResultMessage):
            # Final result with usage
            yield StreamChunk(
                chunk_type="complete",
                usage={
                    "input_tokens": message.usage.get("input_tokens", 0),
                    "output_tokens": message.usage.get("output_tokens", 0),
                }
            )
```

### CLI Subprocess: JSON Parsing

```python
async def stream_chat(self, messages, system_prompt, tools, max_tokens):
    # Build command
    cmd = [
        "claude", "-p",
        "--output-format", "stream-json",
        "--system-prompt", system_prompt,
        "--max-turns", "3",
        "--model", self.model,
        self._convert_messages_to_prompt(messages)
    ]

    # Spawn process
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "ANTHROPIC_API_KEY": self.api_key}
    )

    # Parse stdout line-by-line
    async for line in process.stdout:
        try:
            event = json.loads(line)

            if event["type"] == "stream_event":
                if event["subtype"] == "text_delta":
                    yield StreamChunk(chunk_type="text", content=event["content"])
                elif event["subtype"] == "tool_use":
                    yield StreamChunk(
                        chunk_type="tool_use",
                        tool_call={
                            "id": event["tool_use_id"],
                            "name": event["tool_name"],
                            "input": event["tool_input"],
                        }
                    )

            elif event["type"] == "result":
                yield StreamChunk(
                    chunk_type="complete",
                    usage={
                        "input_tokens": event.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": event.get("usage", {}).get("output_tokens", 0),
                    }
                )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse CLI output: {line}")

    # Wait for process completion
    await process.wait()
    if process.returncode != 0:
        stderr = await process.stderr.read()
        yield StreamChunk(chunk_type="error", error=f"CLI error: {stderr.decode()}")
```

---

## Risk Assessment

### Agent SDK Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Event translation bugs | Medium | Comprehensive unit tests, side-by-side comparison |
| Tool execution mismatch | High | Use existing MCP tools from `agent_service.py` |
| Session state leaks | Medium | Properly manage ContextVars, session isolation |
| Performance overhead | Low | Benchmark against direct API |
| Dependency conflicts | Low | Isolated venv, pin versions |

### CLI Subprocess Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Process zombie/hanging | High | Timeout enforcement, cleanup handlers |
| JSON parsing errors | Medium | Robust error handling, line buffering |
| Tool integration complexity | High | MCP server or fallback to Python execution |
| Subprocess overhead | Medium | Consider connection pooling (if stateless) |
| Platform-specific issues | Medium | Windows/Linux/macOS testing |

---

## Success Criteria

Integration is successful when:

- [ ] New adapter conforms to `LLMAdapter` ABC
- [ ] Streams text incrementally (no buffering delays)
- [ ] Tool calls (search_documents, save_artifact) execute correctly
- [ ] Usage statistics captured in `complete` chunk
- [ ] Error handling graceful (API errors, tool failures)
- [ ] Existing tests pass (no regression)
- [ ] Document quality measurably improved (Phase 4 comparison)
- [ ] Production deployment viable (container pattern documented)

---

## Sources

### Agent SDK
- [Agent SDK Overview - Official Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [Hosting the Agent SDK](https://platform.claude.com/docs/en/agent-sdk/hosting)
- [Claude Agent SDK - PyPI](https://pypi.org/project/claude-agent-sdk/)
- [Claude Agent SDK - GitHub](https://github.com/anthropics/claude-agent-sdk-python)

### CLI Subprocess
- [CLI Reference - Official Docs](https://code.claude.com/docs/en/cli-reference)
- [What is --output-format in Claude Code](https://claudelog.com/faqs/what-is-output-format-in-claude-code/)
- [Running Claude Code from Windows CLI - Practical Guide](https://dstreefkerk.github.io/2026-01-running-claude-code-from-windows-cli/)

### Streaming & Integration
- [Agent SDK Streaming Output](https://platform.claude.com/docs/en/agent-sdk/streaming-output)
- [Build AI Agents with Claude Agent SDK](https://devblogs.microsoft.com/semantic-kernel/build-ai-agents-with-claude-agent-sdk-and-microsoft-agent-framework/)

**Confidence levels:**
- Agent SDK integration: **HIGH** (official docs, production patterns, bundled CLI)
- CLI subprocess integration: **MEDIUM** (documented patterns, subprocess complexity)
- Tool integration via MCP: **HIGH** (existing implementation in `agent_service.py`)
- Quality improvement claims: **LOW** (needs Phase 4 measurement)
