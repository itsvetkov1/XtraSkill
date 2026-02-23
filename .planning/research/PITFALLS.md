# Pitfalls Research

**Domain:** Adding file generation to Assistant section + CLI `--dangerously-skip-permissions` fix
**Researched:** 2026-02-23
**Confidence:** HIGH (all pitfalls derived directly from the actual codebase, not general patterns)

---

## Critical Pitfalls

### Pitfall 1: Process Pool Pre-warmed Without `--dangerously-skip-permissions`

**What goes wrong:**
The `ClaudeProcessPool` in `claude_cli_adapter.py` spawns 2 warm processes at app startup via `_spawn_warm_process()`. These processes are started with a fixed command list (lines 178-190 of that file). If `--dangerously-skip-permissions` is only added to the `stream_chat()` inline command list, the warm pool processes remain interactive-permission processes. Requests that consume a warm process will still block on permission prompts silently.

**Why it happens:**
The flag must be added in **two places**: `_spawn_warm_process()` and `_cold_spawn()`. Both methods independently build the full process args. A developer fixes `stream_chat()` (where they see the cmd list), but the actual warm process creation is in the pool methods. Fixing only one path produces intermittent failures: works on cold-spawn fallback, blocks on warm pool (the common path after startup).

**How to avoid:**
Add `'--dangerously-skip-permissions'` to the cmd list in both `_spawn_warm_process()` and `_cold_spawn()`. Confirm with `ps aux | grep claude` after server startup — 2 pre-warmed processes should show the flag in their argument list.

**Warning signs:**
- CLI works for the very first request after a fresh server restart (cold-spawn), then blocks on subsequent requests once pool is filled
- Requests hang indefinitely with no error — the CLI is waiting for interactive permission confirmation
- `"Process pool empty, falling back to cold spawn"` log message never appears but requests still hang

**Phase to address:** CLI permissions phase (first phase of v3.2 milestone)

---

### Pitfall 2: `ArtifactType` Enum Is BA-Specific — Reusing It Breaks Semantics Silently

**What goes wrong:**
`frontend/lib/models/artifact.dart` defines `ArtifactType` as a closed enum: `userStories`, `acceptanceCriteria`, `requirementsDoc`, `brd`. Its `fromJson()` has a fallback that returns `requirementsDoc` for unknown values. If the backend sends a new type (e.g., `generated_file`) for Assistant file artifacts, `ArtifactCard` silently displays it as "Requirements Doc" with the wrong icon and wrong label. No crash, no error — the bug is completely invisible during development testing.

**Why it happens:**
The fallback to `requirementsDoc` makes the bug silent. In testing, the card appears to work because content still renders. The mismatch only surfaces in production UI where the label and icon are wrong, and users are confused by a "Requirements Doc" label on a Python script or JSON file.

**How to avoid:**
Build a separate `GeneratedFileCard` widget for the Assistant section that does not use `Artifact` or `ArtifactType` at all. The BA enum should stay BA-only. If a shared model is needed, create a `GeneratedFile` model with its own fields (no `artifactType` field). This is the clean separation — Assistant-generated files are conceptually different from BA artifacts.

**Warning signs:**
- `ArtifactCard` showing "Requirements Doc" label for Assistant-generated files
- Wrong icon (a document icon instead of a generic file icon) on generated files
- The `ArtifactType.fromJson()` fallback being triggered (add a log assertion to detect this)

**Phase to address:** File generation UI phase; the widget architecture decision must be made before implementation begins

---

### Pitfall 3: `AssistantConversationProvider` Has No Artifact State — Importing BA Patterns Brings BA Logic

**What goes wrong:**
`AssistantConversationProvider` was deliberately built without artifact state (no `_artifacts` list, no `ArtifactCreatedEvent` handler, no `generateArtifact()` method — see Key Decisions in PROJECT.md: "AssistantConversationProvider (not reuse ConversationProvider)"). If file generation state is added by copy-pasting from `ConversationProvider`, BA-specific business logic comes along: artifact deduplication checks, budget validation, mode validation, the `artifact_generation: true` flag pattern. None of these apply to Assistant file generation.

**Why it happens:**
`ConversationProvider` has solved artifact-related problems thoroughly (PITFALL-05, PITFALL-06, PITFALL-08 from Phase 42). The temptation is to copy those solutions. But `ConversationProvider`'s `_generateArtifactSilently()` pattern uses `artifact_generation: true` in the chat request body, which triggers BA-specific behavior in `conversations.py` (the ephemeral "Generate the artifact silently" message injection, lines 138-146). This is wrong for the Assistant section.

**How to avoid:**
Add minimal file state directly to `AssistantConversationProvider`: a `List<GeneratedFile> _generatedFiles` field, a `generateFile(String description)` method that calls a dedicated backend endpoint, and a completion handler that appends the result to `_generatedFiles`. Do not import `ArtifactService` — it calls `/api/artifacts/{id}` which is BA-only. Do not import `artifact_type_picker.dart` or `ArtifactType` anywhere in the assistant section.

**Warning signs:**
- `artifact_generation: true` being passed from the Assistant section's chat request
- `ArtifactType` imported in any `assistant/` screen or widget file
- `ConversationProvider` being considered as a base class or replacement for `AssistantConversationProvider`
- `generateArtifact()` being called from Assistant context

**Phase to address:** Provider integration phase for file generation

---

### Pitfall 4: Backend Chat Endpoint Injects BA System Prompt — Assistant Threads Must Not Hit It

**What goes wrong:**
`conversations.py` line 151 constructs `AIService(provider=provider, thread_type=thread.thread_type or "ba_assistant")`. The `or "ba_assistant"` fallback means any Assistant thread with a NULL `thread_type` in the database will route to BA behavior. The generate-file request gets the 7,437-token BA system prompt, and the CLI subprocess responds with "Which mode: (A) Meeting Mode..." instead of generating the requested file.

**Why it happens:**
The Phase 62 migration backfilled `thread_type` for existing threads. But if any older Assistant threads still have NULL in the column (e.g., threads created before v3.0), the `or "ba_assistant"` fallback silently routes them to BA logic. Developers would not notice this during testing with freshly-created threads.

**How to avoid:**
The generate-file request should go to a dedicated endpoint (`POST /api/threads/{id}/generate-file`) that explicitly uses the CLI adapter with a file-generation system prompt and does not have any `thread_type` routing. Also: verify the Phase 62 migration actually covered all Assistant threads — run `SELECT COUNT(*) FROM threads WHERE thread_type IS NULL AND model_provider = 'claude_code_cli'` before shipping.

**Warning signs:**
- Generated file response begins with "Which mode: (A) Meeting Mode..." (BA system prompt leaking)
- Backend logs show BA system prompt loaded for an Assistant thread request
- The `thread.thread_type or "ba_assistant"` fallback being triggered for any thread (log this explicitly)

**Phase to address:** Backend generate-file endpoint phase

---

### Pitfall 5: `sendMessage()` Auto-Retry Logic Will Fire on File Generation Errors

**What goes wrong:**
`AssistantConversationProvider.sendMessage()` includes auto-retry (lines 266-308): on `ErrorEvent`, it waits 2 seconds then calls `sendMessage(content)` again with the original content. If `generateFile()` is implemented by delegating to `sendMessage()` (passing the description as message content), a failed file generation triggers auto-retry. The retry sends the raw file description as a plain chat message, creating a user message bubble with the description text and initiating a normal chat response.

**Why it happens:**
`sendMessage()` is seen as the "send something to the AI" method. It handles streaming, error display, and retry. Building `generateFile()` on top of it avoids duplicating all that state management. But the auto-retry and user message creation in `sendMessage()` are wrong for file generation — file generation has different UX requirements (no user bubble, dialog-driven, different error display).

**How to avoid:**
`generateFile()` must be a completely standalone method in `AssistantConversationProvider`, exactly as the Key Decision from Phase 42 required `generateArtifact() separate from sendMessage()`. It must have its own `_isGeneratingFile` boolean state, its own error handling that does not set `_lastFailedMessage`, and must never call `sendMessage()`.

**Warning signs:**
- `_lastFailedMessage` being set during a file generation attempt
- A failed file generation causing a user message bubble to appear with the file description text
- `sendMessage()` being called from within `generateFile()` or any file generation code path

**Phase to address:** Provider integration phase for file generation

---

### Pitfall 6: `ArtifactCard` Lazy-Loads Content from BA-Only Endpoint

**What goes wrong:**
`ArtifactCard._loadContent()` calls `_artifactService.getArtifact(widget.artifact.id)` which hits `/api/artifacts/{id}`. This endpoint returns BA artifact data from the BA artifacts table. If Assistant-generated files are stored in a different table or use a different ID scheme, the existing `ArtifactCard` returns 404 when the user expands it. The error shows "Artifact not found" even though the file was generated successfully and saved correctly.

**Why it happens:**
`ArtifactCard` hardcodes `ArtifactService` via `final ArtifactService _artifactService = ArtifactService()` (line 28). There is no way to inject a different service or override the endpoint. The widget is not polymorphic.

**How to avoid:**
Build a `GeneratedFileCard` widget for the Assistant section. If content can be returned inline during generation (no lazy load), include it directly in the `GeneratedFile` model and the card never needs to fetch. This eliminates the endpoint dependency entirely. Only add a fetch if content is too large to return inline (unlikely for MVP).

**Warning signs:**
- 404 errors in logs for `/api/artifacts/{id}` when user expands an Assistant-generated file
- `ArtifactCard` receiving an ID that does not exist in the `artifacts` table
- `artifact_card.dart` imported in any file under `screens/assistant/`

**Phase to address:** File generation UI widget phase

---

### Pitfall 7: Export Endpoints Coupled to BA `ArtifactType` — New Type Causes Silent Fallback or DB Error

**What goes wrong:**
The backend `ArtifactType` SQLAlchemy enum (in `models.py`) is a closed set matching the frontend enum. If generated files are stored with a new type string (e.g., `generated_file`) not in the enum, SQLAlchemy raises a `DataError` on insert. If forced into an existing type (e.g., `requirements_doc`), the BA artifact deduplication logic in `conversation_service.py` may incorrectly suppress future BA artifact requests because it sees a "fulfilled" `requirements_doc` artifact in the thread.

**Why it happens:**
The path of least resistance when reusing the export infrastructure is to pick an existing `artifact_type` value. Developers pick `requirements_doc` because it's the most generic-sounding. The deduplication interference is not obvious — it only manifests when a user on the BA section of the same thread later tries to generate a BRD.

**How to avoid:**
Add `generated_file` to both the backend `ArtifactType` enum and the frontend `ArtifactType` enum with appropriate icon and label. This requires an Alembic migration but prevents both the DB error and the deduplication interference. The export endpoint already handles any `artifact_type` generically; adding the new value requires no changes to export logic.

**Warning signs:**
- SQLAlchemy `DataError` or `LookupError` when inserting a generated file artifact
- Generated files appearing in BA artifact lists with a "Requirements Doc" label
- BA artifact generation being suppressed in a thread where a file was previously generated

**Phase to address:** Backend generate-file endpoint phase (schema change must precede UI)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reuse `ArtifactCard` for generated files | No new widget to build | Silent type mismatch; wrong label/icon; 404 on expand from wrong endpoint | Never — the card is not polymorphic |
| Force `artifact_type: "requirements_doc"` for generated files | Reuses existing save/export pipeline | BA deduplication logic interference; semantically wrong metadata | Never — deduplication interference is a functional regression |
| Add `--dangerously-skip-permissions` to `stream_chat()` cmd only | Fixes the obvious code path | Warm pool processes (the common case) remain interactive; intermittent blocking | Never |
| Call `sendMessage()` from `generateFile()` | One fewer method to write | Auto-retry fires as chat; user message bubble created; streaming state conflicts | Never |
| Use existing BA chat endpoint for generate-file requests | No new endpoint needed | BA system prompt loaded; `thread_type` fallback risk; `artifact_generation: true` flag semantics wrong | Only if `thread_type` routing is verified airtight with no NULL fallback |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Claude CLI `--dangerously-skip-permissions` | Adding flag to `stream_chat()` inline cmd list only — ignores pool spawn path | Add to `_spawn_warm_process()` cmd list AND `_cold_spawn()` cmd list; both build process args independently |
| BA `ArtifactService` in Assistant section | Importing `ArtifactService` and calling `getArtifact()` with Assistant file IDs | Separate `AssistantFileService` or inline content in generation response to avoid lazy load entirely |
| `artifact_generation: true` flag | Using it for Assistant file generation because "it skips the chat message" | This flag injects a BA-specific ephemeral message. Use a dedicated endpoint or a different flag without BA semantics |
| `ContextVar` in `mcp_tools.py` | Assuming context vars are set for all code paths | The new generate-file path must explicitly call `_db_context.set()`, `_thread_id_context.set()` before triggering the CLI — same as `stream_chat()` lines 580-583 |
| `ClaudeProcessPool` warm processes | Assuming warm processes reflect the command in `stream_chat()` | The pool spawns independently; the `stream_chat()` cmd list is not used for warm processes at all |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Blocking file generation inside dialog confirm handler | Long UI freeze; dialog hangs while CLI subprocess runs (2-30s) | Close dialog immediately; show streaming progress in chat area | Every file generation attempt for any non-trivial content |
| Generating file inline during dialog without progress indicator | User sees nothing for 10-30 seconds; thinks app is broken | Show `AssistantStreamingMessage` with "Generating file..." status in chat area immediately after dialog closes | Files longer than a short paragraph |
| Pool exhausted by simultaneous chat + file generation | Both requests cold-spawn; lose pool latency benefit | Pool size 2 is sufficient for single-user dev; do not increase for MVP | If user sends a chat message during file generation |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| `--dangerously-skip-permissions` without documenting what it skips | The flag bypasses Claude Code file system and bash execution prompts. The CLI runs with the server process's OS permissions. Confused prompts could trigger unintended writes. | Document in Key Decisions table. Note that the CLI has no project directory context and no bash tool in the Assistant adapter. Risk is acceptable for this system but must be explicit. |
| Passing user file description directly to CLI without any boundary | Prompt injection: user types a description that redirects CLI to execute bash commands or write files | The `combined_prompt` wraps user content in `[USER]:` tags. Validate that generated output is text only. The CLI is not given bash tool permissions via MCP in the Assistant context. |
| Storing generated files in BA artifacts table without type discrimination | Generated files appear in BA artifact lists; deduplication logic may suppress BA requests | Use separate artifact type or separate model; maintain separation between BA artifacts and Assistant-generated files |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Loading spinner inside dialog after "Generate" tapped | User cannot see progress; dialog occupies screen for 10-30 seconds | Close dialog immediately; show `AssistantStreamingMessage` in chat with "Generating file..." status; display `GeneratedFileCard` when complete |
| Collapsing generated file card by default (matching BA pattern) | For short generated files the user just requested, they want to read immediately; the BA collapse was for very long BRDs | Default to expanded for generated files; the user just requested this content |
| Same export buttons (MD/PDF/Word) for arbitrary file types | A Python script or JSON file exported as "Word" is user-hostile | Offer "Copy" and "Download as text" for generated files; MD/PDF/Word only if content is clearly a document |
| File generation dialog accepting empty or very short descriptions | CLI generates vague or useless content; user confused | Require minimum description length (20+ chars) before enabling the Generate button; show character count |

---

## "Looks Done But Isn't" Checklist

- [ ] **CLI permissions flag in both spawn paths:** `ps aux | grep claude` after server startup shows `--dangerously-skip-permissions` on 2 pre-warmed processes — not just on cold-spawned processes
- [ ] **Pool restart after flag added:** Existing warm pool processes from before the code change do not have the flag; server must be restarted for the pool to refill with corrected processes
- [ ] **`generateFile()` never calls `sendMessage()`:** Trace the call graph; confirm `_lastFailedMessage` is never set during file generation; confirm no user message bubble appears
- [ ] **`ArtifactType` enum extended correctly:** `ArtifactType.fromJson('generated_file')` returns the new enum value — not the `requirementsDoc` fallback; write a unit test for this
- [ ] **Export endpoint accepts new type:** `/api/artifacts/{id}/export/md` returns 200 for a generated file record with no SQLAlchemy validation errors
- [ ] **BA deduplication not triggered:** Generate a file in an Assistant thread; confirm `conversation_service.py`'s deduplication logic does not suppress subsequent BA artifact requests in the same thread
- [ ] **`ContextVar` set before CLI spawn in generate-file path:** The generate-file code path calls `_db_context.set()`, `_thread_id_context.set()` before triggering the CLI subprocess
- [ ] **Dialog closes before CLI completes:** Generate button triggers immediate dialog close + streaming progress in chat; dialog does not remain open waiting for CLI

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong flag placement — pool processes lack flag | LOW | Add flag to both spawn methods; restart server; pool refills with correct processes within REFILL_DELAY (0.1s) |
| `ArtifactType` used for generated files, wrong labels in UI | MEDIUM | Add new enum value + Alembic migration; one-time UPDATE for existing records with wrong type; frontend enum update |
| `generateFile()` implemented via `sendMessage()` causing retry loops | MEDIUM | Extract standalone method; clear `_lastFailedMessage` and `_isStreaming` guards; no database migration needed |
| BA system prompt leaking into generate-file requests | LOW | Fix routing to use correct system prompt; no data to repair |
| `ArtifactCard` used for Assistant files (404 on expand) | LOW | Replace with `GeneratedFileCard`; purely UI change, no data impact |
| BA deduplication incorrectly suppressing requests | MEDIUM | Add `generated_file` type to deduplication exclusion list; no data migration; verify with test coverage |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Pool processes lack `--dangerously-skip-permissions` | Phase: CLI permissions fix | `ps aux | grep claude` confirms flag on 2 pre-warmed processes; make 5 consecutive requests without any hanging |
| `ArtifactType` enum reused for generated files | Phase: file generation UI (card widget) | Unit test: `ArtifactType.fromJson('generated_file')` returns new enum value, not fallback |
| BA logic imported into Assistant provider | Phase: provider integration for file generation | No `ArtifactType`, `ArtifactService`, or `artifact_generation: true` in any assistant file |
| BA chat endpoint used for generate-file requests | Phase: backend generate-file endpoint | Dedicated endpoint at `POST /api/threads/{id}/generate-file` exists; `artifact_generation` flag not involved |
| `sendMessage()` auto-retry fires on file generation errors | Phase: provider integration | Unit test: mock CLI error during `generateFile()`; confirm no `sendMessage()` called; no user message bubble |
| `ArtifactCard` calls wrong load endpoint | Phase: file generation UI (card widget) | `ArtifactCard` import absent from all assistant files; `GeneratedFileCard` used exclusively |
| Export endpoint rejects new artifact type | Phase: backend generate-file endpoint | Integration test: export generated file as MD, PDF, Word — all return 200 |
| BA deduplication interferes with Assistant threads | Phase: backend generate-file endpoint | Generate file in Assistant thread; confirm no deduplication suppression in subsequent BA requests |

---

## Sources

- Direct codebase analysis: `backend/app/services/llm/claude_cli_adapter.py` — process pool spawn methods `_spawn_warm_process()` (lines 170-193) and `_cold_spawn()` (lines 195-214); current cmd list does not include `--dangerously-skip-permissions`
- Direct codebase analysis: `frontend/lib/providers/assistant_conversation_provider.dart` — `sendMessage()` auto-retry logic (lines 266-308); no artifact state present
- Direct codebase analysis: `frontend/lib/screens/conversation/widgets/artifact_card.dart` — hardcoded `ArtifactService` (line 28); no polymorphism
- Direct codebase analysis: `frontend/lib/models/artifact.dart` — `ArtifactType.fromJson()` fallback to `requirementsDoc` (line 19); closed enum with 4 BA-specific values
- Direct codebase analysis: `backend/app/routes/conversations.py` — BA-specific `artifact_generation` flag and ephemeral message injection (lines 127-146); `thread_type or "ba_assistant"` fallback (line 151)
- Project KEY DECISIONS (`.planning/PROJECT.md`): `generateArtifact() separate from sendMessage()` (Phase 42); `AssistantConversationProvider (not reuse ConversationProvider)` (Phase 64)
- Project history: Phase 42 (PITFALL-06 — streaming state conflicts when artifact generation mixed with chat state); Phase 36 (PITFALL-08 — collapsible artifact cards collapsed by default)

---
*Pitfalls research for: v3.2 Assistant File Generation & CLI Permissions*
*Researched: 2026-02-23*
*Confidence: HIGH — Derived from direct codebase inspection, not general patterns*
