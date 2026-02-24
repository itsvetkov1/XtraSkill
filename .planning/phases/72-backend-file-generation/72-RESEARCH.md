# Phase 72: Backend File Generation - Research

**Researched:** 2026-02-24
**Domain:** FastAPI backend — Claude CLI subprocess + MCP tool execution + Alembic migrations
**Confidence:** HIGH

## Summary

Phase 72 wires up file generation for Assistant threads. When `artifact_generation=True` is posted to the existing `/api/threads/{thread_id}/chat` endpoint, the backend must instruct the Claude CLI subprocess to call a `save_artifact` MCP tool, persist the file to the Artifact table with a new `generated_file` type, and emit an `artifact_created` SSE event to the client.

The critical architectural insight: the CLI subprocess runs in its own process, so Python ContextVars cannot carry database context across the process boundary. The existing BA workflow relies on the Claude Agent SDK (in-process MCP), not the CLI subprocess. For Assistant threads the CLI is used, and the "MCP via system prompt" POC approach does not actually execute tools — the model generates text that looks like a tool result but nothing is persisted. Phase 72 must add a real MCP server that the CLI subprocess can connect to via `--mcp-config`, backed by an HTTP endpoint that FastAPI serves.

The simplest viable approach given existing infrastructure: a **FastAPI-mounted MCP sub-app** using `mcp.server.fastmcp.FastMCP` (MCP SDK v1.12.4, already installed in venv). `FastMCP.streamable_http_app()` returns a `Starlette` ASGI app that mounts at a sub-path. The CLI subprocess connects to it via `--mcp-config` with a JSON HTTP transport config. Per-request context (db session, thread_id) is threaded via a session token embedded in the system prompt and resolved by a server-side registry. The system prompt for Assistant threads changes from empty to a minimal file-gen instruction only when `artifact_generation=True`. Separately, the `generated_file` enum value must be added to `ArtifactType` and an Alembic migration applied.

**Primary recommendation:** Add `generated_file` to `ArtifactType`, create an Alembic migration (checkpoint; no SQL change needed for SQLite native_enum=False), mount a lightweight `FastMCP` server in FastAPI at `/mcp` for the `save_artifact` tool using `mcp.streamable_http_app()`, pass `--mcp-config` as a JSON string and `--tools ""` to the CLI subprocess when building the assistant command, add a minimal `ASSISTANT_FILE_GEN_PROMPT` used only when `artifact_generation=True`, thread `artifact_generation` through `AIService.stream_chat()` and `_stream_agent_chat()`, and add `ARTIFACT_CREATED:` scanning to `_translate_event` in `claude_cli_adapter.py` for the `result` event type.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GEN-01 | Assistant threads have a lightweight system prompt that instructs the CLI to use `save_artifact` tool for file generation requests | System prompt is conditionally applied in `ai_service.py` at LOGIC-01; currently `""` for `thread_type == "assistant"`; Phase 72 adds `ASSISTANT_FILE_GEN_PROMPT` used only when `artifact_generation=True` |
| GEN-02 | `artifact_generation` parameter is threaded through to `_stream_agent_chat()` for conditional behavior | `artifact_generation` already on `ChatRequest` and modifies conversation in `conversations.py`; `AIService.stream_chat()` and `_stream_agent_chat()` do not yet receive it — Phase 72 adds the parameter and conditional logic at both call sites |
| GEN-03 | `save_artifact` MCP tool is available and functional for Assistant thread file generation | CLI subprocess needs `--mcp-config` JSON pointing to FastAPI-mounted FastMCP server; `mcp==1.12.4` already in venv; `FastMCP.streamable_http_app()` confirmed available; session registry pattern confirmed in existing `mcp_tools.py` |
| GEN-04 | Generated file content is persisted via Artifact model and retrievable via existing artifact API | Artifact model and GET `/api/artifacts/{id}` endpoint already exist; `ArtifactType.GENERATED_FILE = "generated_file"` must be added to `models.py` + Alembic migration; Pydantic response model uses `ArtifactType` directly — picks up new value automatically |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp` (FastMCP) | 1.12.4 (installed in venv) | HTTP MCP server the CLI subprocess connects to | Already in venv; `from mcp.server.fastmcp import FastMCP` confirmed; `streamable_http_app()` returns `Starlette` ASGI app |
| SQLAlchemy async | 2.0.46 (installed) | Artifact persistence from MCP tool handler | Project standard for all DB writes |
| `alembic` | 1.18.4 (installed) | Checkpoint migration for `generated_file` ArtifactType | Project standard for schema migrations |
| FastAPI | 0.129.0 (installed) | Mount MCP server as sub-app via `app.mount()` | Project backbone |
| `asyncio.create_subprocess_exec` | stdlib | CLI subprocess spawn with `--mcp-config` flag | Already used in all three spawn paths in `claude_cli_adapter.py` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `json` | stdlib | Serialize `--mcp-config` JSON string for CLI arg | Always — CLI `--mcp-config` accepts a JSON string literal |
| `uuid` | stdlib | Generate session tokens for MCP registry | Per file generation request |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| HTTP MCP server (FastMCP, single instance) | stdio MCP server (subprocess per request) | stdio avoids port management but requires spawning a Python subprocess per CLI request; HTTP reuses one server across all requests |
| FastAPI sub-path mount (`/mcp`) on port 8000 | Dedicated port (e.g. 8001) | Sub-path on 8000 is simpler (no port mgmt); dedicated port avoids URL path conflicts; either works for localhost |
| `--mcp-config` JSON string in args | Temp file per request | JSON string avoids temp file lifecycle; `create_subprocess_exec` takes a list so no quoting issues |

**Installation:** Nothing new to install — `mcp==1.12.4` is already in `backend/venv`.

## Architecture Patterns

### Recommended Project Structure

```
backend/app/
├── services/
│   ├── ai_service.py           # Add ASSISTANT_FILE_GEN_PROMPT; thread artifact_generation param
│   └── llm/
│       └── claude_cli_adapter.py  # Add --mcp-config + --tools "" flags; ARTIFACT_CREATED detection
├── routes/
│   └── conversations.py        # Pass artifact_generation to AIService (currently not passed)
├── mcp_server.py               # NEW: FastMCP instance + save_artifact tool + session registry
└── models.py                   # Add GENERATED_FILE to ArtifactType
backend/alembic/versions/
└── XXXX_add_generated_file_artifact_type.py  # NEW: checkpoint migration
```

### Pattern 1: FastMCP HTTP Server Mounted in FastAPI

**What:** A `FastMCP` instance with a `save_artifact` tool, mounted as an ASGI sub-application in FastAPI at `/mcp`. Per-request context (db session, thread_id) is propagated via a session token embedded in the system prompt; the MCP tool resolves it from an in-memory registry.

**When to use:** When the CLI subprocess needs to call Python functions that require database access.

**Context propagation problem:** The process pool pre-warms processes at startup with fixed argv. `--mcp-config` is baked in at spawn time. The MCP server URL must be static (`http://127.0.0.1:8000/mcp`). Per-request context must travel via the prompt text (session token in system prompt), not via process args.

**Confirmed FastMCP API (from venv inspection):**
- `FastMCP.streamable_http_app()` — returns `starlette.applications.Starlette` ASGI app
- Mount with `app.mount("/mcp", mcp.streamable_http_app())`
- `@mcp.tool()` decorator registers tools
- `mcp.run_streamable_http_async()` — not needed; use `streamable_http_app()` for ASGI mounting

**Example — MCP server (`backend/app/mcp_server.py`):**
```python
# Source: mcp==1.12.4, FastMCP confirmed available in venv
import json
from mcp.server.fastmcp import FastMCP
from app.models import Artifact, ArtifactType

mcp = FastMCP("assistant-tools")

_session_registry: dict[str, dict] = {}  # session_token -> {db, thread_id}


def register_mcp_session(token: str, db, thread_id: str) -> None:
    _session_registry[token] = {"db": db, "thread_id": thread_id}


def unregister_mcp_session(token: str) -> None:
    _session_registry.pop(token, None)


@mcp.tool()
async def save_artifact(session_token: str, title: str, content_markdown: str) -> str:
    """Save a generated file artifact for the current Assistant thread.
    Call ONCE then stop. Do not produce any other text."""
    ctx = _session_registry.get(session_token)
    if not ctx:
        return "Error: session context not found"
    artifact = Artifact(
        thread_id=ctx["thread_id"],
        artifact_type=ArtifactType.GENERATED_FILE,
        title=title,
        content_markdown=content_markdown,
    )
    ctx["db"].add(artifact)
    await ctx["db"].commit()
    await ctx["db"].refresh(artifact)
    event_data = {"id": artifact.id, "artifact_type": "generated_file", "title": artifact.title}
    return f"ARTIFACT_CREATED:{json.dumps(event_data)}|File generated successfully."
```

**Example — Mount in FastAPI (`backend/main.py`):**
```python
# Source: FastMCP streamable_http_app() confirmed returns Starlette app
from app.mcp_server import mcp
app.mount("/mcp", mcp.streamable_http_app())
```

**Example — CLI spawn with --mcp-config:**
```python
# Source: claude --help confirmed --mcp-config and --tools flags
import json

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

mcp_config_json = json.dumps({
    "mcpServers": {
        "assistant": {
            "type": "http",
            "url": MCP_SERVER_URL
        }
    }
})
cmd_for_assistant = [
    self.cli_path,
    "-p",
    DANGEROUSLY_SKIP_PERMISSIONS,
    "--output-format", "stream-json",
    "--verbose",
    "--model", self.model,
    "--mcp-config", mcp_config_json,
    "--tools", "",  # Disable built-in Bash/Edit/Read tools
]
```

### Pattern 2: Minimal Assistant System Prompt (GEN-01)

**What:** A minimal system prompt for Assistant threads used only when `artifact_generation=True`. Replaces the current empty string at LOGIC-01. The session token is formatted into the prompt at call time.

**When to use:** `thread_type == "assistant"` AND `artifact_generation=True`. Regular assistant chat keeps empty system prompt.

**Example:**
```python
# backend/app/services/ai_service.py
ASSISTANT_FILE_GEN_PROMPT = (
    "You are a file generation assistant. When asked to generate a file:\n"
    "1. Call the save_artifact tool with title, content_markdown, and session_token='{session_token}'\n"
    "2. Call save_artifact ONCE and stop immediately after\n"
    "3. Do not produce any conversational text before or after calling the tool"
)
```

The prompt is `.format(session_token=session_token)` before being passed to `stream_chat`.

### Pattern 3: artifact_generation Threading (GEN-02)

**What:** Pass `artifact_generation: bool` from `conversations.py` route handler through `AIService.stream_chat()` and `_stream_agent_chat()`.

**Current call chain (missing the parameter):**
```
conversations.py:stream_chat()           # has artifact_generation from body
  → ai_service.AIService.stream_chat()   # does NOT receive artifact_generation
      → _stream_agent_chat()             # does NOT receive artifact_generation
```

**Changes needed:**
1. `AIService.stream_chat()` signature: add `artifact_generation: bool = False`
2. `AIService._stream_agent_chat()` signature: add `artifact_generation: bool = False`
3. `conversations.py`: pass `body.artifact_generation` when calling `ai_service.stream_chat()`
4. Inside `_stream_agent_chat()`: use `artifact_generation` to select system prompt and build session token

### Pattern 4: ARTIFACT_CREATED Detection in CLI Adapter (GEN-02 dependency)

**What:** Extend `_translate_event()` in `claude_cli_adapter.py` to scan the `result` event's `"result"` field for the `ARTIFACT_CREATED:...|` marker. This populates `chunk.metadata["artifact_created"]` which `_stream_agent_chat()` already knows to check.

**Why needed:** `_stream_agent_chat()` already handles `chunk.metadata["artifact_created"]` (lines 957-967) but `_translate_event()` does not currently populate it for CLI output. The SDK adapter (`claude_agent_adapter.py`) does populate it by scanning tool result blocks. The CLI adapter's `result` event processing must be extended to match.

**Example:**
```python
# Source: claude_agent_adapter.py lines 230-236 (existing pattern)
# Add to _translate_event() in claude_cli_adapter.py:
elif event_type == "result":
    result_text = event.get("result", "")
    usage = event.get("usage", {})
    received_result = True  # (already tracked by caller)

    artifact_data = None
    if "ARTIFACT_CREATED:" in result_text:
        try:
            marker_start = result_text.index("ARTIFACT_CREATED:") + len("ARTIFACT_CREATED:")
            marker_end = result_text.index("|", marker_start)
            artifact_data = json.loads(result_text[marker_start:marker_end])
        except (ValueError, json.JSONDecodeError):
            logger.warning("Failed to parse ARTIFACT_CREATED marker in result")

    return StreamChunk(
        chunk_type="complete",
        usage={
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        },
        metadata={"artifact_created": artifact_data} if artifact_data else None,
    )
```

### Pattern 5: Alembic Migration — Additive Enum Value (GEN-04)

**What:** Checkpoint migration to add `generated_file` to `ArtifactType`. For SQLite with `native_enum=False` (VARCHAR storage), no SQL column change is required.

**Run command:** `cd backend && venv/bin/alembic revision --autogenerate -m "add_generated_file_artifact_type"`

**Migration body (SQLite — no column change needed):**
```python
# Source: alembic/versions/e330b6621b90_*.py pattern (confirmed native_enum=False)
def upgrade() -> None:
    """Add generated_file to ArtifactType enum.

    ArtifactType uses native_enum=False (VARCHAR storage in SQLite).
    Adding a new enum value only requires updating the Python enum class.
    This migration is a version checkpoint; no SQL DDL is needed for SQLite.
    PostgreSQL would require: ALTER TYPE artifacttype ADD VALUE 'generated_file'
    """
    pass  # No SQL change for SQLite

def downgrade() -> None:
    pass  # Removing enum values requires data migration; skipped for SQLite
```

### Anti-Patterns to Avoid

- **Using ContextVars to pass db to the MCP tool:** ContextVars are process-local. The CLI subprocess calls the MCP server via HTTP — a separate process. Use the session registry in `mcp_server.py` instead.
- **Pre-warming pool with per-request MCP config:** The pool processes have fixed argv. The `--mcp-config` URL must be static; context travels via the session token in the prompt.
- **Applying `--mcp-config` only to Assistant threads at the process level:** The process pool is shared. Use the same `--mcp-config` for all pre-warmed processes (BA threads ignore MCP since their system prompt does not reference MCP tools). Conditional logic can live in the system prompt selection, not the process args.
- **Passing `--tools ""` only for file generation and not for regular assistant chat:** For consistency, disable built-in tools for all CLI processes (BA in-process MCP approach doesn't need Bash/Edit/Read; Assistant file gen definitely does not). This prevents accidental file system writes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP MCP server | Custom FastAPI routes speaking MCP JSON-RPC | `FastMCP` + `mcp.streamable_http_app()` (confirmed in venv) | FastMCP handles MCP handshake, tool schema generation, and streaming protocol |
| Artifact persistence in MCP tool | Raw `sqlite3` calls or custom ORM bypass | `AsyncSession` from session registry via existing SQLAlchemy pattern | Consistent with all other DB writes in the project |
| Shell-safe CLI argument building | `shlex.quote()` on args | Pass list to `create_subprocess_exec` (no `shell=True`) | List form is already used throughout `claude_cli_adapter.py`; no quoting needed |
| ARTIFACT_CREATED marker format | New protocol | Reuse `ARTIFACT_CREATED:{json}|` (existing marker in `mcp_tools.py` and parsed by `ai_service.py`) | Protocol already implemented; reusing it means zero changes to `_stream_agent_chat` detection logic |

**Key insight:** The `ARTIFACT_CREATED:...|` marker protocol is already understood by `_stream_agent_chat()`. The only gap is that `_translate_event()` in the CLI adapter does not yet parse it from the `result` event. Adding that one scan is the bridge.

## Common Pitfalls

### Pitfall 1: Process Pool Cannot Accept Per-Request MCP Config

**What goes wrong:** Attempting to set `--mcp-config` with a session-specific token baked into the URL per request, using pre-warmed pool processes. Pool processes have fixed argv.

**Why it happens:** `ClaudeProcessPool._spawn_warm_process()` spawns at startup; there is no way to change a running process's argv.

**How to avoid:** Keep the `--mcp-config` URL static (`http://127.0.0.1:8000/mcp`). Thread per-request context via the session token in the system prompt. Register the token in `mcp_server._session_registry` before writing the prompt to the process stdin.

**Warning signs:** MCP tool returns "Error: session context not found" because the token was never registered before the CLI tried to call the tool.

### Pitfall 2: Built-in CLI Tools Write Files to Disk Instead of Calling MCP Tool

**What goes wrong:** The CLI's agent loop uses built-in `Write` or `Bash` tools to save a file to disk instead of calling the `save_artifact` MCP tool. No artifact is persisted to the database.

**Why it happens:** With `--dangerously-skip-permissions`, the CLI freely uses built-in tools. If the system prompt does not exclusively direct it to use `save_artifact`, it may choose its own approach.

**How to avoid:** Pass `--tools ""` to disable all built-in tools. Only the MCP `save_artifact` tool will be available. Also make the system prompt explicit: "ONLY call the save_artifact tool."

**Warning signs:** CLI exits cleanly but no `artifact_created` SSE event; checking disk shows new files created under the working directory.

### Pitfall 3: ArtifactType Enum Value Not Recognized

**What goes wrong:** `ValueError: 'generated_file' is not a valid ArtifactType` when creating an Artifact in the MCP tool.

**Why it happens:** Python enum not updated, or code running against old `.pyc` cache.

**How to avoid:** Add `GENERATED_FILE = "generated_file"` to `ArtifactType` in `models.py`. Column length is 30 chars; `"generated_file"` is 14 chars — safe. Restart FastAPI server after updating code.

**Warning signs:** MCP tool returns error string; no artifact in DB.

### Pitfall 4: MCP Server Not Ready at Startup

**What goes wrong:** Process pool pre-warms before FastAPI finishes startup; first request fails with `ECONNREFUSED`.

**Why it happens:** If process pool warm-up races with ASGI server initialization.

**How to avoid:** Mount the MCP server in the `app` definition (not in a lifespan event). The `app.mount("/mcp", ...)` call registers routes before the lifespan events run. The pool warm-up (in lifespan) happens after ASGI routes are registered.

**Warning signs:** First request errors with CLI stderr showing connection refused; subsequent requests may work.

### Pitfall 5: ARTIFACT_CREATED Not Detected in CLI Output

**What goes wrong:** Artifact IS persisted in DB but `artifact_created` SSE event never reaches the client.

**Why it happens:** `_translate_event()` in `claude_cli_adapter.py` currently handles `result` events by emitting a `StreamChunk(chunk_type="complete")` with no metadata. The `ARTIFACT_CREATED:` marker in the result text is discarded.

**How to avoid:** Extend the `result` branch of `_translate_event()` to scan `event.get("result", "")` for the `ARTIFACT_CREATED:` marker. Set `metadata={"artifact_created": parsed_data}` on the complete chunk. The `_stream_agent_chat()` in `ai_service.py` already reads `chunk.metadata["artifact_created"]` at lines 957-967.

**Warning signs:** DB shows artifact with correct content; SSE stream shows `message_complete` but no `artifact_created` event.

### Pitfall 6: BA Thread System Prompt Regression

**What goes wrong:** After adding `artifact_generation` parameter to `_stream_agent_chat()`, the BA thread system prompt conditional at LOGIC-01 is accidentally changed and BA threads receive the wrong prompt.

**Why it happens:** Modifying the conditional `system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""` without preserving BA behavior.

**How to avoid:** Add the new condition as an `elif` for Assistant with file gen, not by replacing the existing conditional. The BA branch must remain identical:
```python
if self.thread_type == "ba_assistant":
    system_prompt = SYSTEM_PROMPT
elif self.thread_type == "assistant" and artifact_generation:
    system_prompt = ASSISTANT_FILE_GEN_PROMPT.format(session_token=session_token)
else:
    system_prompt = ""
```

**Warning signs:** BA threads start asking "Which mode: (A) Meeting Mode..." — meaning BA prompt was delivered — or BA threads get an empty prompt and behave like a raw CLI without guidance.

## Code Examples

Verified patterns from direct codebase inspection:

### Current _stream_agent_chat Signature to Extend
```python
# Source: backend/app/services/ai_service.py lines 864-872
async def _stream_agent_chat(
    self,
    messages: List[Dict[str, Any]],
    project_id: str,
    thread_id: str,
    db
) -> AsyncGenerator[Dict[str, Any], None]:
    # Add: artifact_generation: bool = False
```

### LOGIC-01 Replacement in _stream_agent_chat
```python
# Source: backend/app/services/ai_service.py line 931
# BEFORE:
system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""

# AFTER:
import uuid as _uuid
session_token = str(_uuid.uuid4()) if artifact_generation else ""

if self.thread_type == "ba_assistant":
    system_prompt = SYSTEM_PROMPT
elif self.thread_type == "assistant" and artifact_generation:
    from app.mcp_server import register_mcp_session
    register_mcp_session(session_token, db, thread_id)
    system_prompt = ASSISTANT_FILE_GEN_PROMPT.format(session_token=session_token)
else:
    system_prompt = ""
```

### ArtifactType Addition in models.py
```python
# Source: backend/app/models.py lines 436-442
class ArtifactType(str, PyEnum):
    """Types of generated business analysis artifacts."""
    USER_STORIES = "user_stories"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    REQUIREMENTS_DOC = "requirements_doc"
    BRD = "brd"
    GENERATED_FILE = "generated_file"  # NEW: Assistant thread file generation (Phase 72)
```

### Alembic Migration Boilerplate
```python
# Source: Pattern from alembic/versions/e330b6621b90_*.py
"""add generated_file artifact type

Revision ID: <auto>
Revises: e330b6621b90
Create Date: 2026-02-24
"""
from alembic import op
import sqlalchemy as sa

revision = '<auto>'
down_revision = 'e330b6621b90'

def upgrade() -> None:
    """Checkpoint migration for generated_file ArtifactType.
    ArtifactType uses native_enum=False (VARCHAR). No SQL DDL needed for SQLite.
    """
    pass  # Python enum addition in models.py is sufficient for SQLite

def downgrade() -> None:
    pass
```

### CLI Spawn Command for Assistant Threads
```python
# Source: claude --help flags confirmed; asyncio.create_subprocess_exec pattern from claude_cli_adapter.py
import json

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

def _build_cmd(self) -> list[str]:
    """Base CLI command — includes --mcp-config and disables built-in tools."""
    mcp_config = json.dumps({
        "mcpServers": {
            "assistant": {"type": "http", "url": MCP_SERVER_URL}
        }
    })
    return [
        self.cli_path,
        "-p",
        DANGEROUSLY_SKIP_PERMISSIONS,
        "--output-format", "stream-json",
        "--verbose",
        "--model", self.model,
        "--mcp-config", mcp_config,
        "--tools", "",  # Disable built-in Bash/Edit/Read tools
    ]
```

### FastMCP Mounting in main.py
```python
# Source: mcp==1.12.4, streamable_http_app() confirmed returns starlette.applications.Starlette
from app.mcp_server import mcp
app.mount("/mcp", mcp.streamable_http_app())
```

### ARTIFACT_CREATED Detection Added to _translate_event
```python
# Source: claude_agent_adapter.py lines 230-236 (existing pattern to replicate in CLI adapter)
elif event_type == "result":
    result_text = event.get("result", "")
    usage = event.get("usage", {})

    artifact_data = None
    if "ARTIFACT_CREATED:" in result_text:
        try:
            marker_start = result_text.index("ARTIFACT_CREATED:") + len("ARTIFACT_CREATED:")
            marker_end = result_text.index("|", marker_start)
            artifact_data = json.loads(result_text[marker_start:marker_end])
        except (ValueError, json.JSONDecodeError):
            logger.warning("Failed to parse ARTIFACT_CREATED marker from CLI result")

    return StreamChunk(
        chunk_type="complete",
        usage={
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        },
        metadata={"artifact_created": artifact_data} if artifact_data else None,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "MCP via system prompt" (POC — no real execution) | Real HTTP MCP server via `--mcp-config` (actual DB writes) | Phase 72 | Artifacts are actually persisted; `artifact_created` SSE event fires reliably |
| Empty system prompt for all Assistant threads | Minimal file-gen prompt for `artifact_generation=True` only | Phase 72 | Model knows to call `save_artifact`; regular assistant chat unchanged |
| `ArtifactType` has 4 values | 5 values including `generated_file` | Phase 72 | Distinct type prevents BA deduplication logic from filtering Assistant artifacts |
| `_stream_agent_chat()` ignores `artifact_generation` | `_stream_agent_chat()` accepts and acts on `artifact_generation` | Phase 72 | Session lifecycle tied to request; system prompt conditional on flag |

**Note from STATE.md:** The decision log contains: "Add generated_file ArtifactType enum value + Alembic migration (prevents BA deduplication interference)". The REQUIREMENTS.md "Out of Scope" note about DB migration referred to a pre-discussion draft — the final SUCCESS CRITERIA for Phase 72 explicitly require the migration.

## Open Questions

1. **Where does `ARTIFACT_CREATED:` marker appear in the CLI `stream-json` output when an MCP tool returns it?**
   - What we know: CLI emits `{"type": "result", "result": "..."}` as the final event; the `result` field contains the session's final text output
   - What's unclear: Whether the MCP tool's return value text appears verbatim in `result`, or if it appears in an intermediate `assistant`-type event
   - Recommendation: The research plan should include a verification step: run a minimal CLI call with an MCP tool that returns `ARTIFACT_CREATED:...` and inspect which event carries the marker. The `result` branch of `_translate_event()` is the most likely location based on how the existing `result` event is handled. If the marker appears in an `assistant` event instead, add scanning there too.

2. **`--tools ""` with warm pool: does it require separate pool for BA vs Assistant threads?**
   - What we know: Passing `--tools ""` disables built-in tools for all pre-warmed processes; BA threads do not use built-in tools (their tooling is the in-process system prompt); Assistant threads actively need built-in tools disabled
   - What's unclear: Whether any BA thread behavior depends on built-in tools being available (unlikely based on code inspection)
   - Recommendation: Apply `--tools ""` to all pool processes; safe for BA threads since their system prompt never instructs use of built-in tools

## Sources

### Primary (HIGH confidence)

- `backend/app/services/llm/claude_cli_adapter.py` — direct codebase inspection; confirmed three spawn paths, LOGIC-01 pattern, `_translate_event` structure, result event handling
- `backend/app/services/ai_service.py` — direct codebase inspection; confirmed `_stream_agent_chat` signature, `artifact_created_data` detection at lines 957-967, LOGIC-01/02/03 markers
- `backend/app/services/mcp_tools.py` — direct codebase inspection; confirmed `ARTIFACT_CREATED:` marker protocol and return format; session registry pattern in `_session_registry`
- `backend/app/models.py` — direct codebase inspection; confirmed `ArtifactType(str, PyEnum)` with `native_enum=False`, `length=30` column, existing 4 values
- `backend/app/routes/conversations.py` — direct codebase inspection; confirmed `artifact_generation` on `ChatRequest`, existing silent mode logic, `ai_service.stream_chat()` call site
- `backend/alembic/versions/e330b6621b90_*.py` — direct codebase inspection; confirmed 3-step SQLite migration pattern, `batch_alter_table` usage
- `claude --help` (CLI v2.1.50) — confirmed `--mcp-config`, `--tools`, `--system-prompt` flags
- `venv/bin/pip list` — confirmed `mcp==1.12.4` installed
- `python -c "from mcp.server.fastmcp import FastMCP; ..."` (run in venv) — confirmed `FastMCP` importable; `streamable_http_app()` confirmed present and returns `starlette.applications.Starlette`

### Secondary (MEDIUM confidence)

- `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` example from CLI help — inferred `--mcp-config` JSON format uses `"type": "http"` and `"url"` keys; exact JSON key names not directly verified (would require a real CLI call)

### Tertiary (LOW confidence)

- **`--mcp-config` JSON exact schema**: Inferred from `claude mcp add --transport http` pattern; the exact keys (`"type"`, `"url"`, `"mcpServers"`) match MCP config conventions but were not directly tested in this environment due to nested session restriction

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed installed; `FastMCP.streamable_http_app()` confirmed via venv inspection
- Architecture: HIGH — all code paths traced in codebase; session registry pattern confirmed in existing `mcp_tools.py`; ARTIFACT_CREATED protocol confirmed
- `--mcp-config` JSON format: MEDIUM — inferred from CLI help examples; exact schema not live-tested
- Pitfalls: HIGH — all pitfalls derived from direct code inspection (process pool constraint, built-in tool interference, result event scanning gap)

**Research date:** 2026-02-24
**Valid until:** 2026-03-25 (stable dependencies; CLI flags confirmed on installed binary)
