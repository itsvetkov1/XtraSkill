# Session: BRD Infinite Loop Bug Fix
**Date:** 2026-02-03
**Issue:** App stuck on "generating artifact" with infinite BRD generation loop

---

## Problem Description

User reported the app getting stuck when trying to generate a BRD. After asking Claude to generate the document, the frontend showed "generating artifact" loading animation indefinitely.

### Symptoms Observed in Backend Logs

After user said "yes i like it as it is. just generate it now" at `00:23:40`:
- System entered infinite loop creating BRD artifacts every ~13 seconds
- 20+ duplicate artifacts created (`INSERT INTO artifacts` statements)
- Multiple SQLAlchemy connection leak warnings (garbage collector cleanup)
- HTTP response returned 200 OK immediately, but streaming/tool execution continued
- `message_complete` event never sent to frontend

---

## Root Cause Analysis

### 1. No Tool Execution Limit
**File:** `backend/app/services/agent_service.py:262-277`

`ClaudeAgentOptions` had no `max_turns` parameter. The Claude Agent SDK continued executing tools indefinitely.

### 2. Tool Description Encouraged Multiple Calls
**File:** `backend/app/services/agent_service.py:113`

```python
"You may call this tool multiple times to create multiple artifacts."
```

This explicitly told the model it could keep calling the tool.

### 3. Two Overlapping BRD Generation Tools
**File:** `backend/app/services/agent_service.py:179`

Both `save_artifact_tool` AND `generate_brd_tool` were registered, causing model confusion.

### 4. No "Stop After Generation" Signal
Tool results said "saved successfully" but didn't signal task completion or tell the model to stop.

### 5. SKILL.md Lacked Post-Generation Instructions
The skill said to continue discovery until BRD request, but didn't say "After generating ONE BRD, STOP."

---

## Fixes Applied

### Fix 1: Added `max_turns=10` to SDK Options
**File:** `backend/app/services/agent_service.py`

```python
options = ClaudeAgentOptions(
    ...
    max_turns=10  # Limits tool execution rounds to prevent infinite loops
)
```

### Fix 2: Updated save_artifact Tool Description
**File:** `backend/app/services/agent_service.py:97-118`

Removed: `"You may call this tool multiple times to create multiple artifacts."`

Added:
```python
"""CRITICAL: Call this tool ONCE per user request. After saving the artifact:
1. STOP generating - do not call this tool again
2. Present the result to the user
3. Wait for explicit user feedback before taking any further action
4. Do NOT generate additional versions unless user explicitly asks"""
```

### Fix 3: Updated Tool Result Message
**File:** `backend/app/services/agent_service.py:157-163`

Changed from:
```python
"Artifact saved successfully... User can now export..."
```

To:
```python
"SUCCESS: Artifact saved... TASK COMPLETE - Present this result to the user and wait for their feedback. Do NOT generate additional artifacts unless explicitly requested."
```

### Fix 4: Removed Duplicate generate_brd_tool
**File:** `backend/app/services/agent_service.py`

- Removed import: `from app.services.brd_generator import generate_brd_tool`
- Removed from MCP server tools list
- Removed from allowed_tools list
- Removed brd_generator context setup

Now only `save_artifact_tool` handles all artifact generation.

### Fix 5: Updated SKILL.md with Post-Generation Behavior
**File:** `.claude/business-analyst/SKILL.md`

Added section:
```markdown
**CRITICAL POST-GENERATION BEHAVIOR:**
After generating ONE BRD artifact:
1. **STOP IMMEDIATELY** - Do NOT generate additional versions or artifacts
2. **Do NOT call save_artifact again** unless user explicitly requests a new document
3. Present the result to the user and WAIT for their explicit feedback
4. Only modify or regenerate if user specifically asks for changes

...

Then STOP and wait for the user's response before taking any action.
```

---

## Commit Details

**Commit:** `9f6a578`
**Message:** `fix(agent): prevent infinite artifact generation loop`

**Files Changed:**
- `backend/app/services/agent_service.py` - Core fixes
- `.claude/business-analyst/SKILL.md` - Behavior instructions

**Pushed to:** `origin/master`

---

## Testing Instructions

1. Restart backend server: `uvicorn main:app --reload --port 8000`
2. Start new conversation in app
3. Go through discovery process
4. Request BRD generation ("generate the BRD")
5. Verify:
   - Exactly ONE artifact is created
   - Agent stops and presents result
   - Agent waits for user feedback
   - No infinite loop occurs

If loop still occurs, `max_turns=10` will hard-stop after 10 rounds.

---

## Related Files

- `backend/app/services/agent_service.py` - Main agent service with tools
- `backend/app/services/brd_generator.py` - BRD generation (now unused for tool)
- `.claude/business-analyst/SKILL.md` - Skill prompt with behavior rules
- `backend/app/services/skill_loader.py` - Loads skill prompt

---

## Architecture Notes

### Agent Service Flow
1. `stream_chat()` receives user message
2. Builds prompt from message history
3. Calls Claude Agent SDK `query()` with options
4. SDK executes tools via MCP server
5. Tool results streamed back to frontend via SSE
6. `message_complete` event signals end

### Tool Registration
Tools are registered via `create_sdk_mcp_server()` and listed in `allowed_tools`.
Only tools in both lists can be called by the agent.

### Context Variables
Database session and thread_id passed to tools via Python `contextvars`:
- `_db_context` - AsyncSession for database operations
- `_project_id_context` - Current project ID
- `_thread_id_context` - Current thread ID for artifact association
