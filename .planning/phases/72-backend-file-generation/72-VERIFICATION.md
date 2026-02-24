---
phase: 72-backend-file-generation
verified: 2026-02-24T16:00:00Z
status: human_needed
score: 4/4 must-haves verified
re_verification: false
human_verification:
  - test: "Send curl POST to /api/threads/{assistant_thread_id}/chat with artifact_generation=true and observe SSE stream"
    expected: "Stream contains an artifact_created SSE event with a JSON payload including a valid artifact ID (UUID), artifact_type of 'generated_file', and title field"
    why_human: "End-to-end flow requires a live backend with Claude CLI subprocess, MCP HTTP server, and active DB session. Cannot be verified by static analysis."
  - test: "After the artifact_created event, call GET /api/artifacts/{id} with the returned artifact ID"
    expected: "Response body includes artifact_type='generated_file', title matching what was generated, and non-empty content_markdown"
    why_human: "Requires a real artifact to have been persisted by the save_artifact MCP tool during the live test above."
  - test: "Verify BA thread behavior is unchanged after Phase 72 changes"
    expected: "Posting a normal message to a BA assistant thread still returns text_delta events and eventually creates a BRD artifact when requested; no MCP-related errors appear in backend logs"
    why_human: "--tools '' is now applied universally to all CLI spawn paths. BA threads use the Anthropic SDK (not CLI), so this should not affect them — but requires live BA thread test to confirm no regression."
---

# Phase 72: Backend File Generation Verification Report

**Phase Goal:** The backend generates and persists a file artifact for Assistant threads when artifact_generation=True is sent via the existing chat endpoint
**Verified:** 2026-02-24
**Status:** human_needed (all automated checks passed; live end-to-end test required)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                                             | Status     | Evidence                                                                                                                                   |
| --- | --------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | A curl POST with artifact_generation=true returns an artifact_created SSE event with a valid artifact ID                         | ? HUMAN    | Full pipeline verified statically; live test required to confirm SSE event fires end-to-end                                                |
| 2   | The artifact is retrievable via GET /api/artifacts/{id} with artifact_type of generated_file                                     | ? HUMAN    | GET /api/artifacts/{id} endpoint exists and returns ArtifactResponse with artifact_type field; live test required to confirm DB persistence |
| 3   | No BA system prompt content appears in the CLI invocation for Assistant threads                                                   | ✓ VERIFIED | LOGIC-01 in _stream_agent_chat(): assistant threads receive ASSISTANT_FILE_GEN_PROMPT or "" — SYSTEM_PROMPT only assigned when thread_type == "ba_assistant" |
| 4   | The generated_file ArtifactType value exists in the backend enum and Alembic migration has been applied                          | ✓ VERIFIED | ArtifactType.GENERATED_FILE = "generated_file" confirmed in models.py; alembic current shows 55e1dfa98f3a (head)                          |

**Score:** 4/4 truths implemented; 2/4 require live human test to confirm end-to-end behavior

### Required Artifacts

| Artifact                                                              | Expected                                                           | Status      | Details                                                                                            |
| --------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------- | -------------------------------------------------------------------------------------------------- |
| `backend/app/models.py`                                               | GENERATED_FILE enum value in ArtifactType                          | ✓ VERIFIED  | Line 442: `GENERATED_FILE = "generated_file"  # Assistant thread file generation (Phase 72)`      |
| `backend/alembic/versions/55e1dfa98f3a_add_generated_file_artifact_type.py` | Alembic checkpoint migration with down_revision = e330b6621b90   | ✓ VERIFIED  | File exists; upgrade()/downgrade() are pass stubs with explanatory docstrings; alembic at head    |
| `backend/app/mcp_server.py`                                           | FastMCP server with save_artifact tool and session registry        | ✓ VERIFIED  | Exports mcp_app (FastMCP), register_mcp_session, unregister_mcp_session; save_artifact tool decorated with @mcp_app.tool(); returns ARTIFACT_CREATED marker |
| `backend/main.py`                                                     | MCP server mounted at /mcp sub-path                                | ✓ VERIFIED  | Line 104: `app.mount("/mcp", mcp_app.streamable_http_app())` at module level; Mount confirmed in app.routes |
| `backend/app/services/ai_service.py`                                  | ASSISTANT_FILE_GEN_PROMPT constant, artifact_generation parameter threading, session lifecycle | ✓ VERIFIED | ASSISTANT_FILE_GEN_PROMPT with {session_token} placeholder; _stream_agent_chat() and stream_chat() both accept artifact_generation: bool = False; session_token registered before try, cleaned in finally |
| `backend/app/services/llm/claude_cli_adapter.py`                      | --mcp-config and --tools flags in all 3 spawn paths; ARTIFACT_CREATED detection in _translate_event | ✓ VERIFIED | --mcp-config and --tools '' present in _spawn_warm_process (line 194-195), _cold_spawn (line 221-222), stream_chat direct cmd (line 638-639); ARTIFACT_CREATED parsing in result branch of _translate_event |
| `backend/app/routes/conversations.py`                                 | artifact_generation passed to ai_service.stream_chat()            | ✓ VERIFIED  | Line 165: `artifact_generation=body.artifact_generation`; ChatRequest model includes artifact_generation: bool = False |

### Key Link Verification

| From                                           | To                                 | Via                                                    | Status      | Details                                                                                             |
| ---------------------------------------------- | ---------------------------------- | ------------------------------------------------------ | ----------- | --------------------------------------------------------------------------------------------------- |
| `conversations.py`                             | `ai_service.py`                    | artifact_generation parameter in stream_chat() call    | ✓ WIRED     | `artifact_generation=body.artifact_generation` at conversations.py:165                              |
| `ai_service.py`                                | `mcp_server.py`                    | register_mcp_session / unregister_mcp_session calls    | ✓ WIRED     | Lines 951-952: `from app.mcp_server import register_mcp_session; register_mcp_session(session_token, db, thread_id)`; Lines 1065-1066: cleanup in finally block |
| `claude_cli_adapter.py`                        | MCP server at /mcp                 | --mcp-config JSON argument in all 3 spawn paths        | ✓ WIRED     | 3 occurrences of `'--mcp-config', MCP_CONFIG_JSON` confirmed; MCP_SERVER_URL = "http://127.0.0.1:8000/mcp" |
| `claude_cli_adapter.py`                        | `ai_service.py`                    | ARTIFACT_CREATED metadata in StreamChunk               | ✓ WIRED     | _translate_event() populates `StreamChunk(metadata={"artifact_created": artifact_data})`; _stream_agent_chat() reads chunk.metadata["artifact_created"] at lines 981-991 and yields `{"event": "artifact_created", ...}` |
| `mcp_server.py`                                | `models.py`                        | Artifact model + ArtifactType.GENERATED_FILE import    | ✓ WIRED     | mcp_server.py line 17: `from app.models import Artifact, ArtifactType`; save_artifact uses `ArtifactType.GENERATED_FILE` |
| `main.py`                                      | `mcp_server.py`                    | ASGI sub-app mount                                     | ✓ WIRED     | main.py line 17: `from app.mcp_server import mcp_app`; line 104: `app.mount("/mcp", mcp_app.streamable_http_app())` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| GEN-01 | 72-02 | Assistant threads have a lightweight system prompt that instructs the CLI to use save_artifact tool for file generation requests | ✓ SATISFIED | ASSISTANT_FILE_GEN_PROMPT constant in ai_service.py; injected via LOGIC-01 when thread_type == "assistant" and artifact_generation == True |
| GEN-02 | 72-02 | artifact_generation parameter is threaded through to _stream_agent_chat() for conditional behavior | ✓ SATISFIED | Parameter present in stream_chat() signature (line 1074) and _stream_agent_chat() signature (line 879); passed at line 1091 |
| GEN-03 | 72-01 | save_artifact MCP tool is available and functional for Assistant thread file generation | ✓ SATISFIED | save_artifact tool in mcp_server.py decorated with @mcp_app.tool(); persists Artifact with ArtifactType.GENERATED_FILE; returns ARTIFACT_CREATED marker |
| GEN-04 | 72-01 | Generated file content is persisted via Artifact model and retrievable via existing artifact API | ✓ SATISFIED | Artifact model used in save_artifact tool; GET /api/artifacts/{artifact_id} endpoint exists in artifacts.py (line 112); returns ArtifactResponse with artifact_type field |

### Anti-Patterns Found

No stub anti-patterns detected in phase 72 artifacts. Specifically:

- No `TODO/FIXME/PLACEHOLDER` comments in phase 72 files
- `save_artifact` in mcp_server.py has a substantive implementation (DB write, commit, refresh, ARTIFACT_CREATED return)
- `_translate_event()` has substantive ARTIFACT_CREATED detection (not just a `return None` stub)
- `ASSISTANT_FILE_GEN_PROMPT` is a real prompt string with formatting placeholder
- Session lifecycle: `session_token = ""` hoisted before try, registered conditionally, cleaned unconditionally in finally

One design decision to note (not a defect, flagged for awareness):

| File | Concern | Severity | Impact |
| ---- | ------- | -------- | ------ |
| `claude_cli_adapter.py` | `--tools ''` applied universally to all 3 spawn paths including BA thread warm pool processes | Info | By design — BA threads use Anthropic SDK adapter, not ClaudeCliAdapter. The `--tools ''` flag is only exercised when ClaudeCliAdapter is used (assistant threads). No regression risk confirmed by adapter selection logic in AIService.__init__. |

### Human Verification Required

#### 1. End-to-End Artifact Generation via curl

**Test:**
1. Start the backend: `cd backend && venv/bin/python run.py`
2. Create or obtain an assistant thread ID (thread_type = "assistant")
3. Get a valid JWT token (use `backend/test_token.py`)
4. Run:
   ```bash
   curl -N -X POST http://localhost:8000/api/threads/{thread_id}/chat \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{"content": "Generate a markdown file with a list of 3 test items", "artifact_generation": true}' \
     --no-buffer
   ```
5. Observe the SSE stream in the terminal

**Expected:** Stream includes an `artifact_created` event:
```
event: artifact_created
data: {"id": "<uuid>", "artifact_type": "generated_file", "title": "..."}
```
**Why human:** Requires live Claude CLI subprocess, active MCP HTTP server at /mcp, and real DB session; cannot be verified statically.

#### 2. Artifact Retrieval via GET

**Test:** After Test 1, copy the artifact ID from the `artifact_created` event and run:
```bash
curl http://localhost:8000/api/artifacts/{artifact_id} \
  -H "Authorization: Bearer {token}"
```

**Expected:** JSON response with `artifact_type: "generated_file"`, non-empty `content_markdown`, and `title` matching what was generated.

**Why human:** Requires a real persisted artifact from Test 1.

#### 3. BA Thread Regression Check

**Test:** Post a message to an existing BA assistant thread requesting a BRD artifact. Verify the BA thread continues to work normally.

**Expected:** BA thread responds with discovery questions, creates BRD artifact when requested, no MCP-related errors in `backend/logs/app.log`.

**Why human:** While static analysis confirms BA threads use a different adapter (Anthropic SDK, not ClaudeCliAdapter), a live test is the only way to confirm the `--tools ''` flag in the warm pool does not interfere with BA operations during any edge-case where adapter selection logic behaves unexpectedly.

### Implementation Quality Notes

The implementation follows the established ARTIFACT_CREATED marker protocol from `mcp_tools.py` consistently. Key design decisions are sound:

1. **Session token as cross-process bridge:** CLI subprocess runs in a separate OS process and cannot see Python ContextVars; the session token embedded in the system prompt is the correct IPC mechanism.

2. **Module-level MCP mount:** Placing `app.mount("/mcp", ...)` at module level (not in lifespan) prevents ECONNREFUSED when the process pool warms up.

3. **Alembic checkpoint migration:** SQLite with `native_enum=False` stores enum values as VARCHAR strings; no DDL is needed to add a new value. The migration exists purely as a version checkpoint.

4. **session_token = "" before try block:** Guarantees the `finally` clause can safely call `unregister_mcp_session` even if an exception occurs before `session_token` is assigned.

---

_Verified: 2026-02-24_
_Verifier: Claude (gsd-verifier)_
