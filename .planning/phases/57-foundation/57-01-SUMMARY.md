---
phase: 57-foundation
plan: 01
subsystem: backend-infrastructure
tags:
  - sdk-upgrade
  - refactoring
  - mcp-tools
  - shared-infrastructure
dependency_graph:
  requires: []
  provides:
    - shared-mcp-tools
    - sdk-v0.1.35
  affects:
    - agent-service
    - future-adapters
tech_stack:
  added:
    - claude-agent-sdk: ">=0.1.35"
  patterns:
    - shared-tool-definitions
    - factory-pattern
    - contextvar-state-management
key_files:
  created:
    - backend/app/services/mcp_tools.py
  modified:
    - backend/requirements.txt
    - backend/app/services/agent_service.py
decisions:
  - Extracted tool definitions to shared module for reuse across SDK and CLI adapters
  - Upgraded SDK to v0.1.35 to get bundled CLI and ARG_MAX fixes
  - Recreated venv with Python 3.12 (SDK requires Python 3.10+)
  - Used factory pattern (create_ba_mcp_server) for MCP server creation
metrics:
  duration_seconds: 13661
  tasks_completed: 2
  files_created: 1
  files_modified: 2
  commits: 2
  completed_at: "2026-02-13"
---

# Phase 57 Plan 01: SDK Upgrade and Shared MCP Tools Summary

**One-liner:** Upgraded claude-agent-sdk to v0.1.35 and extracted MCP tool definitions to shared mcp_tools.py module for reuse across SDK and CLI adapters.

## Objectives Achieved

✅ Upgraded claude-agent-sdk from >=0.1.0 to >=0.1.35 (includes bundled CLI and ARG_MAX fixes)
✅ Created backend/app/services/mcp_tools.py with shared tool definitions
✅ Extracted search_documents_tool and save_artifact_tool from agent_service.py
✅ Implemented create_ba_mcp_server() factory for reuse across adapters
✅ Refactored agent_service.py to import from mcp_tools.py
✅ Verified no circular imports or initialization issues

## Tasks Completed

### Task 1: Upgrade SDK dependency and create shared mcp_tools.py

**Commit:** 2eb25b8

**Changes:**
- Updated requirements.txt: claude-agent-sdk>=0.1.0 → claude-agent-sdk>=0.1.35
- Created backend/app/services/mcp_tools.py with:
  - All 4 ContextVar declarations (_db_context, _project_id_context, _thread_id_context, _documents_used_context)
  - search_documents_tool function with @tool decorator
  - save_artifact_tool function with @tool decorator
  - create_ba_mcp_server() factory function
  - __all__ export list for clean API

**Files:**
- backend/requirements.txt (modified)
- backend/app/services/mcp_tools.py (created, 209 lines)

**Verification:** All exports import successfully, no errors.

### Task 2: Refactor agent_service.py to import from mcp_tools.py

**Commit:** 537f243

**Changes:**
- Removed 179 lines of inline tool definitions and ContextVar declarations
- Added import from mcp_tools: create_ba_mcp_server, _db_context, _project_id_context, _thread_id_context, _documents_used_context
- Simplified AgentService.__init__ to use create_ba_mcp_server() factory
- Removed unused imports: tool, create_sdk_mcp_server, search_documents, Artifact, ArtifactType, ContextVar
- No changes to stream_chat method (still works with imported ContextVars)

**Files:**
- backend/app/services/agent_service.py (modified, -179 lines)

**Verification:** AgentService imports and initializes successfully, no circular imports detected.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Python version incompatibility**
- **Found during:** Task 1 verification
- **Issue:** Existing venv used Python 3.9, but claude-agent-sdk>=0.1.35 requires Python 3.10+
- **Fix:** Recreated venv with Python 3.12 (found at /usr/local/bin/python3.12), reinstalled all dependencies
- **Files affected:** backend/venv/ (recreated)
- **Impact:** Required additional time for venv recreation and dependency installation, but resolved blocking import error

## Key Decisions Made

1. **Shared module location:** Placed mcp_tools.py in backend/app/services/ alongside agent_service.py for logical grouping
2. **Factory pattern:** Used create_ba_mcp_server() factory function instead of exposing tool list directly - cleaner API for adapters
3. **Export all ContextVars:** Included all 4 ContextVars in __all__ so adapters can set them when needed
4. **Python 3.12 for venv:** Chose Python 3.12 over 3.10/3.11 for latest features and better performance

## Technical Notes

**Tool definition preservation:** Both tools were copied exactly from agent_service.py with no logic changes - only location changed. This ensures:
- Identical behavior for existing AgentService usage
- Consistent tool signatures for future SDK and CLI adapters
- No risk of behavioral regressions

**ContextVar pattern:** ContextVars remain the state management mechanism for request-scoped data (db session, project_id, thread_id, documents_used). Future adapters (Phase 58-59) will set these before calling tools.

**Import structure:**
```
mcp_tools.py (new)
  ├─ Defines: search_documents_tool, save_artifact_tool
  ├─ Exports: create_ba_mcp_server factory
  └─ Declares: 4 ContextVars

agent_service.py (refactored)
  ├─ Imports: create_ba_mcp_server, ContextVars from mcp_tools
  └─ Uses: tools_server = create_ba_mcp_server()
```

## Verification Results

| Criterion | Status | Evidence |
|-----------|--------|----------|
| SDK version >=0.1.35 | ✅ PASS | requirements.txt line 33, pip show confirms 0.1.35 |
| mcp_tools.py exports | ✅ PASS | All 8 exports import successfully |
| agent_service.py refactor | ✅ PASS | Zero @tool decorators, imports from mcp_tools |
| AgentService initializes | ✅ PASS | Instance created, tools_server populated |
| No circular imports | ✅ PASS | Both modules import without error |
| Existing tests | ⚠️  NOTE | Pre-existing auth test failure (401 vs 403) unrelated to refactor |

**Test suite status:** One pre-existing test failure in test_artifact_routes.py::test_403_without_auth (expects 403, gets 401). This failure predates the refactor and is unrelated to MCP tools or SDK changes. No tests exist specifically for agent_service or mcp_tools.

## Files Changed

**Created (1):**
- backend/app/services/mcp_tools.py (209 lines)

**Modified (2):**
- backend/requirements.txt (1 line changed: SDK version)
- backend/app/services/agent_service.py (-179 lines, +9 lines import)

## Next Steps

**Phase 58 (Plan 02)** can now proceed with SDK adapter implementation:
- Import create_ba_mcp_server from mcp_tools
- Set ContextVars before tool execution
- Implement multi-turn streaming with proper event translation

**Phase 59 (Plan TBD)** can reuse the same tools for CLI adapter:
- Import create_ba_mcp_server from mcp_tools
- Solve ContextVar boundary with MCP HTTP transport (per research findings)
- Compare SDK vs CLI quality/cost metrics

## Self-Check

Verifying all claimed files and commits exist:

**Files:**
```bash
$ ls -l backend/app/services/mcp_tools.py
-rw-r--r--  1 user  staff  6824 Feb 13 10:15 backend/app/services/mcp_tools.py
FOUND: backend/app/services/mcp_tools.py
```

**Commits:**
```bash
$ git log --oneline --all | grep -E "(2eb25b8|537f243)"
537f243 refactor(57-01): refactor agent_service.py to import from mcp_tools.py
2eb25b8 feat(57-01): upgrade SDK to v0.1.35 and create shared mcp_tools.py
FOUND: 2eb25b8 (Task 1)
FOUND: 537f243 (Task 2)
```

**Requirements.txt SDK version:**
```bash
$ grep claude-agent-sdk backend/requirements.txt
claude-agent-sdk>=0.1.35
FOUND: SDK version >=0.1.35
```

## Self-Check: PASSED

All files exist, all commits are present, SDK version verified. Plan execution complete.
