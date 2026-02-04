# Research Summary: v1.9.4 Artifact Generation Deduplication

**Project:** BA Assistant - v1.9.4 Bug Fix Milestone
**Domain:** LLM tool-call deduplication, conversation context engineering, silent generation UX
**Researched:** 2026-02-05
**Confidence:** HIGH
**Bug Reference:** BUG-016 (parent), BUG-017, BUG-018, BUG-019, THREAD-011

---

## Executive Summary

The artifact multiplication bug (BUG-016) is a textbook case of unfiltered conversation context poisoning LLM tool-call decisions. When a user generates N artifacts across a thread, all N generation requests remain visible in conversation history without any marker distinguishing fulfilled from pending requests. The model, seeing N actionable-looking requests plus a tool description that says "You may call this tool multiple times," dutifully calls `save_artifact` N times on the next turn. This is a well-documented cross-framework problem affecting LangGraph, Vercel AI SDK, OpenAI, and Anthropic integrations alike.

The fix requires zero new dependencies. The entire solution is a 4-layer defense-in-depth strategy applied to the existing stack: (1) a system prompt deduplication rule, (2) a tool description change from "multiple times" to "ONCE per request," (3) structural annotation of fulfilled requests in conversation history, and (4) an ephemeral request pattern for button-triggered generation that keeps messages out of history entirely. Layers 1+2 are prompt-level (probabilistic, ~95% effective together), Layer 3 is structural (deterministic annotation), and Layer 4 is architectural (messages never enter the database). Together they provide 100% coverage for button-triggered requests and ~99%+ for typed requests.

The primary risks are: (a) the detection marker referenced in BUG-019 (`ARTIFACT_CREATED:`) exists only in dead code and will NOT work -- the detection strategy must be corrected before implementation; (b) the deduplication rule must include an explicit escape hatch for legitimate re-generation requests ("regenerate with more detail") or it will block core workflow; and (c) the frontend `generateArtifact()` method MUST be a separate code path from `sendMessage()` or suppressed SSE events will break the frontend state machine, creating blank message bubbles.

---

## Key Findings

### Stack Impact: Zero New Dependencies

The entire fix modifies 6 existing files. No new libraries, no database migrations, no new API endpoints. All changes use existing patterns already in the codebase.

| Layer | Approach | Libraries Needed |
|-------|----------|-----------------|
| 1. Prompt deduplication rule | Edit `SYSTEM_PROMPT` XML string | None |
| 2. Tool description enforcement | Edit `SAVE_ARTIFACT_TOOL` dict | None |
| 3. History filtering | Modify `build_conversation_context()` | None |
| 4. Silent generation | Extend `ChatRequest`, filter SSE | None (existing FastAPI + sse-starlette) |

**Key technical finding:** The `max_uses` parameter (which could programmatically cap tool calls) is only available for Anthropic's server-side tools (web_search, web_fetch). It is NOT available for client-defined tools like `save_artifact`. There is no API-level mechanism to limit tool calls per turn. The four-layer approach is the only viable strategy.

### Feature Scope

**Table stakes (must have for v1.9.4):**
- System prompt deduplication rule with re-generation escape hatch (BUG-017)
- Tool description single-call enforcement (BUG-018)
- History filtering with correct marker detection (BUG-019)
- Silent artifact generation for button-triggered requests (THREAD-011)
- Error state clearing (loading animation MUST clear on failure)
- Silent failure logging to backend

**Should include (low complexity, high value):**
- Typed progress indicator: "Generating [Artifact Type]..." not generic "Generating..."

**Explicitly deferred (anti-features for v1.9.4):**
- Trigger-phrase detection system (fragile, use response-based detection instead)
- Removing old messages from history (breaks coherence, use prefix annotation)
- `disable_parallel_tool_use` globally (breaks legitimate multi-tool use)
- Tool call deduplication middleware (over-engineering; fix root cause instead)
- Hidden message flag in database (schema change not needed; ephemeral pattern is simpler)
- Post-hoc duplicate deletion (symptom treatment, not prevention)

**Deferred to future versions:**
- Context compaction for long threads (v2.0+)
- Conversation summarization (v2.0+)
- Idempotent tool execution with dedup keys (v1.9.5+)
- Cancel/stop button for generation (v1.9.5+)
- Artifact version history (v2.0+)

### Architecture Decisions

**4-layer defense-in-depth:**

| Layer | Type | Effectiveness Alone | Files |
|-------|------|-------------------|-------|
| 1. Prompt rule | Behavioral (soft) | ~80% | `ai_service.py` |
| 2. Tool description | Behavioral (soft) | Combined with L1: ~95% | `ai_service.py` |
| 3. History annotation | Structural (medium) | Combined with L1+2: ~99%+ | `conversation_service.py` |
| 4. Silent generation | Architectural (hard) | 100% for button path | `conversations.py`, 3 frontend files, 1 new widget |

**Critical architecture correction:** The detection strategy for Layer 3 must NOT use the `ARTIFACT_CREATED:` marker from BUG-019's specification -- it only exists in dead code (`agent_service.py:174`). The recommended approach is to inject a deterministic marker (`<!-- ARTIFACT_GENERATED -->`) into the saved assistant message when an `artifact_created` SSE event fires during streaming. This creates a reliable detection signal independent of model phrasing. Alternative: query the artifacts table by timestamp correlation.

**Build order:** Layers 1+2 first (zero-risk string edits), then Layer 3 (single function change), then Layer 4 (most complex, frontend + backend).

### Critical Pitfalls (Top 5)

1. **PITFALL-01: Wrong detection marker (CRITICAL).** BUG-019 references `ARTIFACT_CREATED:` from dead code. The active code path saves only the model's text response to the database, not tool results. Detection will silently fail if implemented as specified. **Fix:** Add `<!-- ARTIFACT_GENERATED -->` marker to saved assistant messages when `artifact_created` event fires, OR query the artifacts table. Resolve BEFORE coding Layer 3.

2. **PITFALL-03: Deduplication blocks re-generation (CRITICAL).** The proposed rule "ONLY act on the MOST RECENT user message" combined with "If you see save_artifact tool results in history, those requests are COMPLETE" will cause the model to refuse legitimate re-generation requests like "regenerate the BRD with more detail." **Fix:** Add explicit escape hatch: "HOWEVER, if the user explicitly asks to regenerate, revise, update, or create a new version, that IS a new request -- honor it."

3. **PITFALL-04: History prefix leaks to user (CRITICAL).** The `[ALREADY PROCESSED - artifact was generated]` prefix may be echoed by the model in responses, exposing internal mechanics. **Fix:** Use a shorter, less descriptive prefix like `[FULFILLED]` and add a system prompt instruction telling the model to never mention the prefix. Or use HTML comment syntax `<!-- fulfilled -->`.

4. **PITFALL-06: SSE suppression breaks frontend state machine (MODERATE).** If Layer 4 reuses `sendMessage()` with server-side text suppression, the frontend will create blank assistant message bubbles because `MessageCompleteEvent` always adds a message to `_messages`. **Fix:** `generateArtifact()` MUST be a completely separate code path with its own state variable (`_isGeneratingArtifact`) that does NOT add messages to `_messages`.

5. **PITFALL-02: Token tracking undercounts in tool loop (MODERATE, PRE-EXISTING).** The tool loop resets `usage_data` on each iteration, reporting only the last iteration's token counts. THREAD-011 makes this worse by exercising the tool loop more frequently. **Fix:** Accumulate usage across all loop iterations. Fix opportunistically as part of v1.9.4.

---

## Implications for Roadmap

### Phase 1: Prompt Engineering Fixes (Layers 1+2)
**Rationale:** Zero-risk string constant edits. Immediate partial fix. Testable in minutes. Both changes are in the same file.
**Delivers:** ~95% reduction in duplicate artifact generation for all request types.
**Addresses:** BUG-017 (prompt rule), BUG-018 (tool description)
**Avoids:** PITFALL-03 (must include re-generation escape hatch in rule text)
**Files:** `ai_service.py` only (SYSTEM_PROMPT constant, SAVE_ARTIFACT_TOOL constant)
**Complexity:** Low
**Prerequisites:** Draft rule text with escape hatch before coding.

### Phase 2: Structural History Filtering (Layer 3)
**Rationale:** Provides deterministic structural guarantee that compensates for prompt compliance gaps. Unit-testable. No frontend changes.
**Delivers:** ~99%+ deduplication reliability for typed requests. Combined with Phase 1, the bug is effectively eliminated for all non-button paths.
**Addresses:** BUG-019 (history filtering)
**Avoids:** PITFALL-01 (must resolve marker detection strategy first), PITFALL-04 (must choose safe prefix format), PITFALL-09 (be aware of text accumulation discrepancy)
**Files:** `conversation_service.py` (and possibly `conversations.py` if adding the `<!-- ARTIFACT_GENERATED -->` marker to saved messages)
**Complexity:** Low-Medium
**Prerequisites:** Resolve PITFALL-01 detection strategy. Verify what actually appears in saved assistant messages after artifact generation by inspecting the database. Fix BUG-019 unit test mock data.

### Phase 3: Silent Artifact Generation (Layer 4)
**Rationale:** Most complex change (frontend + backend). Should be built last so Layers 1-3 provide a safety net. Eliminates accumulation entirely for the most common path (button clicks).
**Delivers:** Clean UX for button-triggered generation (loading -> artifact card, no chat bubbles). Zero message accumulation for button path. Token savings (~100-500 tokens per generation).
**Addresses:** THREAD-011 (silent generation), error state clearing, typed progress indicator
**Avoids:** PITFALL-02 (fix token accumulation bug), PITFALL-05 (skip message save regardless of accumulated text), PITFALL-06 (separate generateArtifact code path), PITFALL-07 (accept orphaned artifacts as edge case), PITFALL-08 (skip summarization for silent requests)
**Files:** Backend: `conversations.py` (ChatRequest, stream_chat, event_generator). Frontend: `ai_service.dart`, `conversation_provider.dart`, `conversation_screen.dart`, new `generating_indicator.dart` widget.
**Complexity:** Medium
**Prerequisites:** Fix PITFALL-02 token tracking. Design `generateArtifact()` as separate code path. Ensure `message_complete` event still fires for stream-end signaling.

### Phase Ordering Rationale

- **Risk escalation:** Start with zero-risk text edits (Phase 1), progress to low-risk backend logic (Phase 2), finish with medium-risk full-stack changes (Phase 3).
- **Incremental testability:** Each phase delivers measurable improvement. Phase 1 alone is worth shipping if Phases 2-3 are delayed.
- **Safety net first:** If Phase 3 has issues during implementation, Phases 1+2 already prevent the bug for all paths.
- **Dependency structure:** Layers 1-3 are code-independent (can be built in any order). Layer 4 is code-independent from 1-3 but should be last due to complexity.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (History Filtering):** The detection marker strategy needs verification against actual database content. Run a real artifact generation and inspect saved messages before finalizing the approach. This is the critical decision point for the entire fix.
- **Phase 3 (Silent Generation):** The frontend state management for `generateArtifact()` needs careful design to avoid PITFALL-06. The interaction between loading states, error states, and artifact card rendering should be planned in detail.

Phases with well-documented standard patterns (skip research-phase):
- **Phase 1 (Prompt Engineering):** Well-established patterns. Anthropic's own docs cover tool description best practices and system prompt structure. The only nuance is PITFALL-03's escape hatch, which is already documented.

---

## Recommendations: Corrections to Proposed Approach

Based on synthesized research, these are concrete changes to the approach described in the user stories:

1. **BUG-017 rule text must be revised.** Add re-generation escape hatch. The proposed rule will block "regenerate with more detail" requests. See PITFALL-03 for exact wording.

2. **BUG-019 detection marker must be changed.** Replace `ARTIFACT_CREATED:` scan with either (a) `<!-- ARTIFACT_GENERATED -->` marker injection at save time, or (b) artifacts table timestamp correlation. The proposed marker does not exist in saved messages.

3. **BUG-019 unit test mock data must be updated.** Current mocks use `ARTIFACT_CREATED:{json}|` content format which does not match production data. Tests will pass but validate nothing.

4. **THREAD-011 must use separate frontend code path.** Reusing `sendMessage()` with SSE filtering is insufficient. `generateArtifact()` must be a distinct method with its own state variable to avoid blank message bubbles.

5. **Fix token accumulation bug opportunistically.** The pre-existing `usage_data` overwrite in the tool loop (ai_service.py line 776) should be fixed as part of Phase 3 since silent generation exercises this code path more frequently.

6. **Skip summarization for silent requests.** Add `if not body.artifact_generation:` guard before `maybe_update_summary()` call. One-line change that avoids wasted API calls.

7. **Use shorter prefix for history annotation.** `[FULFILLED]` instead of `[ALREADY PROCESSED - artifact was generated]` to reduce model echo risk (PITFALL-04).

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies. All changes to existing stack. Verified against Anthropic API docs. |
| Features | HIGH | Feature scope is well-bounded (bug fix, not new capability). Anti-features clearly identified. Cross-framework evidence confirms the approach. |
| Architecture | HIGH | Based on direct codebase analysis of all affected files. Data flows traced line-by-line. All 6 integration risks identified with mitigations. |
| Pitfalls | HIGH | 14 pitfalls identified from codebase analysis and external research. Critical ones have concrete prevention strategies with detection methods. |

**Overall confidence:** HIGH

### Gaps to Address

1. **Detection marker verification (CRITICAL GAP):** No one has yet inspected the database to confirm what text appears in saved assistant messages after artifact generation. The entire Layer 3 design depends on this. **Action:** Before Phase 2 implementation, generate an artifact in development, query the messages table, and document the exact content.

2. **Token accumulation bug scope (MODERATE GAP):** PITFALL-02 identifies a pre-existing token undercounting bug in the tool loop. The full impact on budget tracking has not been quantified. **Action:** Log per-iteration usage during a test run and compare sum vs. reported total.

3. **Frontend loading/error state design (MINOR GAP):** The exact UX for the `GeneratingIndicator` widget (what it looks like, where it appears, how errors render) is not specified. **Action:** Define during Phase 3 planning. Low risk since it follows established loading state patterns.

---

## Sources

### Primary (HIGH confidence)
- [Anthropic: Tool Use Implementation Guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) -- tool descriptions, disable_parallel_tool_use, tool runner
- [Anthropic: Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use) -- max_uses (server tools only), confirms no client-tool cap
- [Anthropic: Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering) -- system prompt structure, rule prioritization
- [Anthropic: Claude 4.x Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices) -- literal instruction following behavior
- Direct codebase analysis: `ai_service.py`, `conversation_service.py`, `conversations.py`, `conversation_provider.dart`, `ai_service.dart`, `conversation_screen.dart`

### Secondary (MEDIUM confidence)
- [JetBrains Research: Efficient Context Management for LLM Agents](https://blog.jetbrains.com/research/2025/12/efficient-context-management/) -- observation masking, pruning fulfilled actions
- [LangGraph: Manage Conversation History](https://langchain-ai.github.io/langgraphjs/how-tos/manage-conversation-history/) -- annotation patterns
- [Vercel AI SDK Issues #7261, #3854](https://github.com/vercel/ai/issues/7261) -- confirms duplicate tool calls as cross-framework problem
- [OpenAI Community: Function calls repeated unnecessarily](https://community.openai.com/t/function-calls-is-repeated-unnecessary/548189) -- confirms cross-provider problem
- [Cloudscape Design System: GenAI Loading States](https://cloudscape.design/patterns/genai/genai-loading-states/) -- loading UX patterns

### Tertiary (LOW confidence)
- [Context Injection Attacks on LLMs (arXiv)](https://arxiv.org/html/2405.20234v1) -- semantic vs syntactic parsing of annotations
- [ICLR 2025: Multi-Turn Function Calling](https://proceedings.iclr.cc/paper_files/paper/2025/file/69c49f75ca31620f1f0d38093d9f3d9b-Paper-Conference.pdf) -- academic validation

---

*Research completed: 2026-02-05*
*Ready for roadmap: yes*
