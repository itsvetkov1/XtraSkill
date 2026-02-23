# Project Research Summary

**Project:** BA Assistant — v3.2 Assistant File Generation & CLI Permissions
**Domain:** AI assistant file generation via Claude CLI subprocess
**Researched:** 2026-02-23
**Confidence:** HIGH

## Executive Summary

v3.2 is a focused milestone that adds two tightly-coupled capabilities to the existing Assistant section: fixing a CLI subprocess permissions bug that currently blocks all tool use, and layering a file generation flow on top of that fix. The recommended approach maximises reuse of the BA section's artifact infrastructure (export_service.py, Artifact model, ArtifactCard widget) while keeping the Assistant section's data model cleanly separated — no shared enum values, no shared service calls, and no shared state management paths. All research was conducted against the live codebase and verified Claude CLI v2.1.50 binary; there are no speculative findings.

The core risk is architectural bleed between the BA and Assistant sections. Seven specific pitfalls identify exactly where this bleed occurs: the ArtifactType closed enum, the ArtifactCard lazy-load endpoint, the BA chat endpoint's thread_type fallback, and the sendMessage() auto-retry logic. Each has a concrete prevention strategy. None require new packages, new database tables, or new API routes beyond what is already planned. The milestone is purely additive — no existing behaviour changes.

The recommended implementation order is dependency-driven: CLI permissions fix first (unblocks all tool use testing), then backend save_artifact wiring for Assistant threads, then provider state + dialog, then UI wire-up. This order means each phase can be verified independently before the next begins, which significantly reduces debugging complexity.

## Key Findings

### Recommended Stack

No new packages are required for v3.2. All needed libraries — python-docx, weasyprint, sse-starlette, flutter_client_sse, file_saver, flutter_markdown — are already in requirements.txt and pubspec.yaml. The only infrastructure change is one Alembic migration to add a `generated_file` value to the ArtifactType enum column. The existing migration pattern from Phase 62 (SQLite table recreation) applies directly.

**Core technologies:**
- Claude CLI 2.1.50: AI subprocess for Assistant threads — `--dangerously-skip-permissions` confirmed present in this version; required for non-interactive tool use
- FastAPI 0.115.x (existing): backend HTTP + SSE — no route changes, POST /api/threads/{id}/chat reused as-is
- Flutter SDK ^3.9.2 (existing): frontend — ArtifactCard and dialog patterns already established
- Alembic (existing): one migration for new ArtifactType enum value; pattern proven in Phase 62

### Expected Features

**Must have (table stakes — all P1, all required together for v3.2):**
- `--dangerously-skip-permissions` in ClaudeCLIAdapter subprocess args — without this, all tool use hangs indefinitely in non-interactive mode; confirmed against CLI v2.1.50 and GitHub issue #581
- "Generate File" button in AssistantChatInput + GenerateFileDialog — user entry point; dialog accepts free-text description, no preset types
- `generateFile()` on AssistantConversationProvider with artifact_created event handling — core logic; must be a standalone method, never delegating to sendMessage()
- ArtifactCard rendered in AssistantChatScreen conversation list — visible output; reuse existing ArtifactCard widget via thin AssistantArtifactCard wrapper

**Should have (add when possible, not blocking v3.2):**
- Skill context in generation: prepend selectedSkill.name to generation prompt when a skill is active — low complexity addition

**Defer (v3.3+):**
- Generation history panel listing all artifacts generated in a thread
- Bulk export of all artifacts from a thread
- In-app content editing before export

**Anti-features confirmed (do not build):**
- Preset artifact type picker for Assistant (BA-specific, wrong for general assistant)
- Streaming generation output (ClaudeCLIAdapter does not support partial message streaming)
- Auto-detect what to generate from conversation (unpredictable; explicit button+dialog is correct)
- `--allowedTools` flag instead of `--dangerously-skip-permissions` (tool set is dynamic, cannot enumerate upfront)

### Architecture Approach

The architecture keeps BA and Assistant sections separated at every layer: separate provider methods, separate widget (AssistantArtifactCard wrapper), separate system prompt constant (ASSISTANT_FILE_GENERATION_PROMPT), and a new `generated_file` ArtifactType value that prevents deduplication interference with BA artifact logic. The generation flow threads through the existing POST /api/threads/{id}/chat endpoint using artifact_generation=true, which already suppresses user message creation and text_delta SSE events. The key architectural decision is Option A for system prompt injection: pass artifact_generation boolean down from conversations.py into AIService.stream_chat() and _stream_agent_chat(), enabling a conditional minimal prompt for file generation without touching the BA system prompt path.

**Major components and changes:**
1. ClaudeCLIAdapter / ClaudeProcessPool — add `--dangerously-skip-permissions` to all 3 spawn paths; extract `_base_cli_args()` helper to keep them DRY
2. AIService._stream_agent_chat() — add ASSISTANT_FILE_GENERATION_PROMPT constant; conditional system prompt when thread_type=="assistant" and artifact_generation==True
3. AssistantConversationProvider — add _artifacts list, _isGeneratingFile flag, generateFile() method, ArtifactCreatedEvent handler
4. AssistantChatInput — add Generate File IconButton between SkillSelector and send button
5. GenerateFileDialog (new) — free-text description dialog; showModalBottomSheet pattern from ArtifactTypePicker
6. AssistantArtifactCard (new) — thin wrapper over existing ArtifactCard; passes artifact.threadId

### Critical Pitfalls

1. **Process pool pre-warmed without the flag** — `--dangerously-skip-permissions` must be added to `_spawn_warm_process()` AND `_cold_spawn()` AND `stream_chat()` inline cmd. Missing any one path causes intermittent blocking after startup (warm pool processes are the common case). Verify with `ps aux | grep claude` — 2 pre-warmed processes must show the flag.

2. **ArtifactType enum reuse causes silent wrong labels** — frontend ArtifactType.fromJson() falls back to `requirementsDoc` for unknown values; bug is invisible during development. Add `generated_file` to both backend enum (with Alembic migration) and frontend enum. Write a unit test for the new fromJson() value.

3. **generateFile() implemented via sendMessage()** — sendMessage() has auto-retry logic that fires on ErrorEvent, creating user message bubbles with the file description as chat content. generateFile() must be fully standalone with its own _isGeneratingFile boolean; must never call sendMessage() or set _lastFailedMessage.

4. **BA chat endpoint thread_type fallback** — conversations.py uses `thread.thread_type or "ba_assistant"`. Any Assistant thread with NULL thread_type routes to BA behavior, loading the full 7,437-token BA system prompt. Verify Phase 62 migration covered all threads: `SELECT COUNT(*) FROM threads WHERE thread_type IS NULL AND model_provider = 'claude_code_cli'` must return 0.

5. **ArtifactCard lazy-loads from BA-only endpoint** — ArtifactCard._loadContent() calls ArtifactService.getArtifact() which hits /api/artifacts/{id}. The AssistantArtifactCard wrapper must pass artifact.threadId correctly; generated files are stored in the same artifacts table so the endpoint will resolve correctly.

6. **BA deduplication interference** — Storing generated files with artifact_type="requirements_doc" causes conversation_service.py deduplication to suppress later BA requirements_doc requests in the same thread. The new `generated_file` enum value prevents this entirely.

7. **Dialog stays open during CLI generation** — Blocking inside the dialog after "Generate" tapped freezes the UI for 10-30 seconds. Close dialog immediately; show streaming progress in chat area; display GeneratedFileCard when complete.

## Implications for Roadmap

Based on combined research, the natural phase structure is dependency-driven: two independent backend changes followed by two sequential frontend changes.

### Phase 1: CLI Permissions Fix
**Rationale:** Hard prerequisite for all tool use. The smallest change (1 flag, 3 locations) with the highest unblocking value. Verifiable independently with a direct test tool invocation before touching any file generation code.
**Delivers:** All CLI tool use (including save_artifact) unblocked in all spawn paths; warm pool processes carry the flag from first request onward
**Addresses:** Table stakes — CLI runs without blocking on permission prompts
**Avoids:** Pitfall 1 (partial flag placement causing intermittent blocking)
**Estimate:** ~30 min

### Phase 2: Backend — save_artifact for Assistant Threads
**Rationale:** Backend must be ready before frontend can verify end-to-end. This phase adds ASSISTANT_FILE_GENERATION_PROMPT, wires artifact_generation param into _stream_agent_chat(), and adds the generated_file ArtifactType enum value with Alembic migration.
**Delivers:** POST /api/threads/{id}/chat with artifact_generation=True generates and stores a file artifact for Assistant threads; curl-testable before any Flutter changes
**Uses:** Existing mcp_tools.py save_artifact_tool, existing artifact routes, existing export_service fallback (no new Jinja2 template needed)
**Implements:** Conditional system prompt injection (Option A from ARCHITECTURE.md)
**Avoids:** Pitfalls 4 (BA system prompt leak), 6 (BA deduplication), 7 (export endpoint type rejection)
**Estimate:** ~1-2 hr

### Phase 3: Frontend — Provider State + Dialog
**Rationale:** Provider changes must land before UI wire-up; dialog is a standalone widget with no screen dependencies.
**Delivers:** AssistantConversationProvider.generateFile() method, artifact state management, ArtifactCreatedEvent handling, GenerateFileDialog widget, AssistantArtifactCard wrapper
**Implements:** Silent generation pattern (separate from sendMessage()), artifact list state
**Avoids:** Pitfalls 2 (ArtifactType enum silent fallback), 3 (BA logic imported into provider), 5 (sendMessage auto-retry on generation errors)
**Estimate:** ~2-3 hr

### Phase 4: Frontend — UI Wire-Up
**Rationale:** Wires all previously built pieces into the visible UI; can only begin after Phase 3 is complete.
**Delivers:** Generate File IconButton in AssistantChatInput, GenerateFileDialog triggered from button, AssistantArtifactCard rendered in AssistantChatScreen conversation list, dialog-closes-immediately UX
**Avoids:** Pitfall 7 (dialog blocking UI during CLI generation)
**Estimate:** ~1-2 hr

### Phase Ordering Rationale

- Phases 1 and 2 are backend-only and can be tested independently of the frontend with curl
- Phase 1 before Phase 2 because CLI tool use must work before save_artifact can be verified end-to-end
- Phase 3 before Phase 4 because the provider state drives all UI rendering
- The two-backend-then-two-frontend sequence enables backend verification before any Flutter changes are required
- No phase introduces a rollback risk (migration only adds a new enum value; no data changes to existing rows)

### Research Flags

All phases have well-documented patterns derived from direct codebase reading — no phases require a `/gsd:research-phase` deep-dive:

- **Phase 1 (CLI permissions):** Single-flag addition to known code locations. Verified against live binary. Zero unknowns.
- **Phase 2 (backend save_artifact):** Existing mcp_tools.py and export_service.py patterns are proven. Alembic migration pattern established in Phase 62. ASSISTANT_FILE_GENERATION_PROMPT is a new constant, not a new system.
- **Phase 3 (provider + dialog):** generateArtifact() in ConversationProvider is a direct reference implementation. ArtifactTypePicker is the dialog pattern template.
- **Phase 4 (UI wire-up):** ArtifactCard is self-contained; reuse via wrapper is fully documented with line references.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against live CLI v2.1.50 binary; all packages confirmed in requirements.txt and pubspec.yaml |
| Features | HIGH | Derived from direct codebase reading; CLI flag behavior confirmed via official docs and GitHub issues #581 and #25503 |
| Architecture | HIGH | All integration points identified from actual source files with line numbers; no speculation |
| Pitfalls | HIGH | All 7 pitfalls derived from direct code inspection; each includes specific file, line, and detection strategy |

**Overall confidence:** HIGH

### Gaps to Address

- **`generated_file` enum value vs letting CLI choose existing type:** STACK.md (section 2.4) originally suggested letting the model choose from existing types. PITFALLS.md (Pitfalls 2 and 7) identifies this as a functional regression risk via BA deduplication interference and silent wrong labels. **Resolution: add `generated_file` enum value with Alembic migration.** This is the correct approach and is the only genuine conflict between research files.

- **showDialog vs showModalBottomSheet for GenerateFileDialog:** FEATURES.md recommends showModalBottomSheet (consistent with ArtifactTypePicker); STACK.md says showDialog. **Resolution:** showModalBottomSheet for UX consistency with ArtifactTypePicker; user can dismiss by tapping outside. Either works functionally.

- **AssistantArtifactCard wrapper vs direct ArtifactCard reuse:** STACK.md recommends direct reuse; ARCHITECTURE.md recommends a thin wrapper. **Resolution:** Thin wrapper (AssistantArtifactCard) is correct — it costs one trivial file, provides a clean import boundary, and prevents future drift if the two cards need to diverge.

## Sources

### Primary (HIGH confidence)
- Claude CLI v2.1.50 `--help` output (verified 2026-02-23 on this machine) — confirmed `--dangerously-skip-permissions` flag presence and exact description
- `backend/app/services/llm/claude_cli_adapter.py` — all 3 spawn path locations identified with line numbers
- `backend/app/services/ai_service.py` — system_prompt logic at line 931; _stream_agent_chat() flow
- `backend/app/routes/conversations.py` — ChatRequest, artifact_generation flag, thread_type fallback at line 151
- `backend/app/services/mcp_tools.py` — save_artifact_tool, ContextVar pattern
- `backend/app/models.py` — ArtifactType enum, Artifact model, closed enum values confirmed
- `frontend/lib/providers/assistant_conversation_provider.dart` — confirmed no artifact state currently; sendMessage() auto-retry at lines 266-308
- `frontend/lib/providers/conversation_provider.dart` — generateArtifact() reference implementation
- `frontend/lib/screens/conversation/widgets/artifact_card.dart` — hardcoded ArtifactService at line 28 identified
- `frontend/lib/models/artifact.dart` — ArtifactType.fromJson() fallback to requirementsDoc confirmed
- `frontend/lib/screens/assistant/widgets/assistant_chat_input.dart` — existing input row layout confirmed
- `.planning/PROJECT.md` — Key Decisions log (Phase 42: generateArtifact() separate from sendMessage(); Phase 64: AssistantConversationProvider kept separate)

### Secondary (HIGH confidence — external verification)
- Official Claude Code headless docs: `--dangerously-skip-permissions` recommended for CI/automated non-interactive use
- GitHub Issue #581: Claude CLI non-interactive mode permission blocking confirmed
- GitHub Issue #25503: `--dangerously-skip-permissions` flag bypass behavior documented
- docs.bswen.com (2026-02-21): `--dangerously-skip-permissions` use case context

---
*Research completed: 2026-02-23*
*v3.2 milestone: Assistant File Generation & CLI Permissions*
*Ready for roadmap: yes*
