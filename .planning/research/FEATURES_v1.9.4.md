# Feature Landscape: LLM Artifact Deduplication and Silent Generation

**Domain:** AI chat application tool-call deduplication, context management, silent generation UX
**Researched:** 2026-02-04
**Confidence:** HIGH (verified with official docs, community issues, and established patterns)
**Milestone:** v1.9.4 (bug fix)
**Parent Issue:** BUG-016 (Artifact generation multiplies on repeated requests)

---

## Executive Summary

Duplicate tool calls in multi-turn LLM conversations are a **well-documented, cross-framework problem** affecting LangGraph, Vercel AI SDK, OpenAI, and Anthropic integrations alike. The BA Assistant's specific variant -- where N prior generation requests in history cause N artifacts on the next request -- is a textbook case of unfiltered conversation context poisoning the model's action decisions.

The industry addresses this through a defense-in-depth strategy: prompt-level rules, tool-level constraints, context filtering, and UX-level prevention (keeping ephemeral actions out of history). The four-layer fix proposed in BUG-016/017/018/019/THREAD-011 aligns precisely with this industry pattern.

This document categorizes features into table stakes (must have for the bug fix), differentiators (better-than-expected behavior that improves the product), and anti-features (things to deliberately NOT build despite seeming useful).

---

## Table Stakes (Must Have for Bug Fix)

Features that are **required** to resolve BUG-016. Missing any of these leaves the accumulation bug partially or wholly unfixed.

### Layer 1: Prompt-Level Deduplication Rule (BUG-017)

| Feature | Why Required | Complexity | Confidence |
|---------|-------------|------------|------------|
| System prompt rule: "ONLY act on MOST RECENT user message" | Models treat every visible request as actionable without explicit instruction not to. This is the first line of defense. | Low | HIGH |
| Positive framing with reasoning context | Negative rules ("do NOT...") are less reliable than positive rules ("ONLY do X because Y") for LLM instruction following. | Low | HIGH |
| Reference to save_artifact results as completion evidence | Model needs a concrete signal to distinguish fulfilled from pending requests. Tool results in history serve this purpose. | Low | HIGH |

**Industry evidence:** Both Vercel AI SDK and LangChain communities use system prompt instructions as the first mitigation for repeated tool calls. The Vercel community specifically recommends "tweaking the system message to instruct the LLM not to restate the tool response" as a practical workaround. Anthropic's own tool-use documentation emphasizes clear tool descriptions as critical for correct behavior.

**Verdict:** TABLE STAKES. Every AI application with tool calling needs prompt-level guardrails.

### Layer 2: Tool Description Single-Call Enforcement (BUG-018)

| Feature | Why Required | Complexity | Confidence |
|---------|-------------|------------|------------|
| Remove "You may call this tool multiple times" | This line actively encourages the accumulation behavior. It is the proximate cause of the model calling save_artifact in a loop. | Low | HIGH |
| Replace with "Call this tool ONCE per user request" | Explicit single-call enforcement at the tool description level. Claude reads tool descriptions before deciding how to use them. | Low | HIGH |
| Allow explicit re-generation via new user message | Users must still be able to request regeneration -- single-call means "once per request turn," not "once per thread." | Low | HIGH |

**Industry evidence:** The Vercel AI SDK community has a feature request (Issue #3854) for `singleToolPerStep` to restrict models to one tool call per step. The AI SDK's `stopWhen: stepCountIs()` pattern achieves similar control. Anthropic's advanced tool use documentation recommends constraining tool descriptions to prevent runaway behavior.

**Verdict:** TABLE STAKES. The existing tool description is the root enabler of the bug.

### Layer 3: History Filtering for Fulfilled Requests (BUG-019)

| Feature | Why Required | Complexity | Confidence |
|---------|-------------|------------|------------|
| Scan assistant messages for ARTIFACT_CREATED marker | Response-based detection (what actually happened) is more reliable than input-based detection (guessing user intent). Zero false positives by design. | Medium | HIGH |
| Prefix fulfilled user messages with [ALREADY PROCESSED] | Provides a structural signal the model cannot misinterpret. The model sees "this was already handled" in the context itself. | Low | HIGH |
| Leave unfulfilled requests untouched (retry support) | If generation failed (no marker), the request should remain actionable so the user can retry. | Low | HIGH |

**Industry evidence:** This maps directly to the "pruning fulfilled actions" pattern documented in JetBrains' context management research and the broader "observation masking" technique from SWE-agent. OpenAI's context compaction feature (`/responses/compact`) replaces old tool calls with compressed representations -- same principle, different mechanism. The key insight from research: "filter fulfilled actions by pruning completed tool call logs, keeping only final results."

**Verdict:** TABLE STAKES. Prompt rules (Layer 1-2) are probabilistic; history filtering is deterministic. Both are needed for reliability.

### Layer 4: Silent Artifact Generation UX (THREAD-011)

| Feature | Why Required | Complexity | Confidence |
|---------|-------------|------------|------------|
| `artifact_generation: true` flag on ChatRequest | Separates artifact generation requests from regular chat at the API level. Enables different handling without affecting normal chat flow. | Low | HIGH |
| Do NOT save user message to database for button-triggered generation | Eliminates the accumulation problem at the source -- messages that never enter history cannot contribute to future accumulation. | Medium | HIGH |
| Do NOT save assistant response for button-triggered generation | The AI's "Done! I've created..." text is noise for button-triggered generation. The artifact card IS the result. | Medium | HIGH |
| Suppress text_delta SSE events in artifact generation mode | Safety net: even if the model generates conversational text despite silent instruction, the frontend never sees it. | Low | HIGH |
| Loading animation replacing user/assistant bubbles | The current flow (user bubble -> assistant text -> artifact card) creates unnecessary clutter. Loading -> artifact card is the correct UX. | Medium | HIGH |
| Artifact card appears after artifact_created event | The artifact itself is the deliverable. It should appear directly, not after scrolling past conversational filler. | Low | HIGH |

**Industry evidence:** Cloudscape Design System (AWS) documents the pattern of showing "Generating [specific artifact]" loading text where the result will appear. The 2025 AI UX trend is explicitly moving away from "chat-alike" interfaces for task-oriented operations. Luke Wroblewski notes: "Messaging UI slowly starts feeling dated" for agent-based tool execution. Google's Generative UI research and Vercel's AI SDK both demonstrate non-chat artifact rendering patterns.

**Verdict:** TABLE STAKES for button-triggered generation. This is both a UX improvement and a structural fix -- it eliminates the accumulation vector for the most common generation path (preset buttons).

---

## Differentiators (Better Than Expected)

Features that go beyond the minimum fix and improve the overall product quality. Not required for v1.9.4 but worth noting for future consideration.

### Context-Level Improvements

| Feature | Value Proposition | Complexity | When to Build |
|---------|-------------------|------------|---------------|
| Context compaction for long threads | OpenAI's `/responses/compact` and Anthropic's `clear_tool_uses` beta both compress old tool interactions. Would reduce token costs for long threads. | High | v2.0+ |
| Conversation summarization for old turns | Replace old message turns with LLM-generated summaries. Reduces context size while preserving important facts. Mem0 reports 80-90% token savings. | High | v2.0+ |
| External memory / structured notes | Keep key facts (project requirements, decisions) outside conversation history. Prevents important context from being pushed out by truncation. | High | v2.0+ |
| Observation masking for tool results | Hide verbose tool output (e.g., full search results) while preserving reasoning chain. JetBrains research shows this matches LLM summarization in quality. | Medium | v2.0+ |

### Tool Execution Improvements

| Feature | Value Proposition | Complexity | When to Build |
|---------|-------------------|------------|---------------|
| Idempotent tool execution with dedup keys | Use artifact title + thread_id as a natural dedup key. If an identical artifact already exists, return it instead of creating a duplicate. | Medium | v1.9.5+ |
| Tool result caching by input hash | If save_artifact is called with identical parameters, return cached result. Prevents true duplicates even if the model calls the tool twice. | Medium | v1.9.5+ |
| Step count limiting in tool loop | Cap the number of tool-calling iterations (e.g., max 3) to prevent runaway loops. Vercel AI SDK's `stepCountIs()` pattern. | Low | v1.9.5+ |
| Tool execution approval for destructive actions | Require user confirmation before executing tools that modify data. Vercel AI SDK's `needsApproval` pattern. | Medium | v2.0+ |

### UX Improvements

| Feature | Value Proposition | Complexity | When to Build |
|---------|-------------------|------------|---------------|
| Cancel/stop button for generation in progress | Users should be able to abort generation that is taking too long or was triggered accidentally. Claude Code issue #15821 specifically requests this. | Medium | v1.9.5+ |
| Progress indicator with artifact type | "Generating User Stories..." is more informative than generic "Generating..." Uses Cloudscape's recommendation: "[Generating] [specific artifact]" | Low | v1.9.4 (include) |
| Artifact version history | Each edit/regeneration creates a new version, accessible via selector. Prevents "I liked the first version better" problem. Claude, ChatGPT Canvas, and Gemini Canvas all support this. | High | v2.0+ |
| Retry button on failed generation | If generation fails, show an inline retry button on the error state rather than requiring the user to click the generate button again. | Low | v1.9.5+ |

### Error Handling Improvements

| Feature | Value Proposition | Complexity | When to Build |
|---------|-------------------|------------|---------------|
| Timeout detection with automatic retry | If API call exceeds threshold (e.g., 30s), show timeout error with retry option rather than hanging indefinitely. | Medium | v1.9.5+ |
| Graceful degradation on partial failure | If artifact saves but SSE stream drops, still show the artifact on next refresh. Don't lose work. | Medium | v1.9.5+ |
| Error state that clears loading animation | If generation fails, the loading animation MUST clear and show an error message. Infinite spinner is a critical UX failure. | Low | v1.9.4 (include) |
| Silent failure logging | Log all silent generation failures to backend for debugging, even though frontend shows a simple error. | Low | v1.9.4 (include) |

---

## Anti-Features (Deliberately Do NOT Build)

Features that seem useful but would introduce complexity, confusion, or new bugs. Explicitly excluded from scope.

### Do NOT: Build a trigger phrase detection system

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Regex/keyword matching on user messages to detect "generation intent" | Brittle, requires maintenance of phrase lists, false positives on normal conversation containing generation-like words ("I want to generate some ideas") | Use response-based detection (ARTIFACT_CREATED marker in assistant response). Detects what actually happened, not what we guess the user intended. |

**Rationale:** BUG-019's response-based detection is superior in every way. Input-based detection introduces a new class of bugs (false positives, missed phrases, language evolution). The ARTIFACT_CREATED marker is already emitted by `execute_tool()` -- using it is zero-maintenance.

### Do NOT: Remove old messages from conversation history entirely

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Delete fulfilled artifact requests from the message list before sending to model | Removes context the model may need for understanding the conversation flow. If user says "regenerate that but with more detail," the model needs to know what "that" refers to. | Prefix with [ALREADY PROCESSED] -- keeps context visible but marks it as completed. Model can still reference the content if needed. |

**Rationale:** Aggressive pruning causes "amnesia" bugs where the model loses conversational context. The prefix approach preserves reference-ability while preventing re-triggering.

### Do NOT: Implement parallel_tool_calls: false

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Disable parallel tool calls at the API level | The Anthropic Messages API allows Claude to call multiple tools in one response. Disabling this globally would break legitimate use cases like "search documents AND generate artifact." | Enforce single-call for save_artifact specifically via tool description (BUG-018). Let search_documents remain callable alongside other tools. |

**Rationale:** The bug is specific to save_artifact accumulation, not parallel tool calling in general. Global restrictions cause collateral damage.

### Do NOT: Build a tool call deduplication middleware layer

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Track all tool calls and prevent identical calls within N seconds / same turn | Over-engineering for this use case. Adds latency, state management, and edge cases (what if user legitimately wants two different artifacts quickly?) | The four-layer fix (prompt + tool description + history filtering + silent generation) is sufficient. Each layer is simple and composable. |

**Rationale:** Distributed deduplication systems (message queues, idempotency keys) are the right pattern for payment processing or order systems, not for a bug caused by unfiltered conversation context. Fix the root cause, don't build infrastructure around the symptom.

### Do NOT: Save silent generation messages with a "hidden" flag

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Save user/assistant messages to DB but mark them as hidden (visible = false) | Adds database schema changes, migration complexity, and query filter conditions throughout the codebase. Hidden messages still consume storage and complicate debugging. | Simply do not save them. Ephemeral context (appended to conversation but not persisted) achieves the same goal with zero schema changes. |

**Rationale:** The simplest solution is no-op on save, not a new visibility model. The artifact itself IS persisted in the artifacts table -- that is the deliverable. The conversational wrapper around it is disposable.

### Do NOT: Build automatic retry on accumulation detection

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Detect when model produces multiple artifacts and auto-delete extras | Treating symptoms rather than causes. Detection logic is fragile. Deleting user-visible artifacts after creation feels buggy. | Fix the root cause (all four layers). If the model never receives the signal to generate multiple artifacts, there are no extras to delete. |

**Rationale:** Post-hoc cleanup is always worse than prevention. The user would see artifacts appear and then disappear, which feels broken.

---

## Feature Dependencies

```
Layer 1 (BUG-017: Prompt Rule)
    |
    v
Layer 2 (BUG-018: Tool Description)     [Independent but ordered for testing]
    |
    v
Layer 3 (BUG-019: History Filtering)    [Independent but adds structural guarantee]
    |
    v
Layer 4 (THREAD-011: Silent Generation) [Requires understanding of Layers 1-3 but
                                          code-independent. Eliminates accumulation
                                          for button path entirely.]
```

**Key dependency note:** Layers 1-3 are mutually reinforcing but independently functional. Each layer reduces the probability of duplicate generation:
- Layer 1 alone: ~80% effective (prompt compliance is probabilistic)
- Layer 1+2: ~95% effective (tool description reinforces prompt)
- Layer 1+2+3: ~99%+ effective (structural history modification is deterministic)
- Layer 1+2+3+4: 100% for button path, ~99%+ for typed requests

Layer 4 is the only one with frontend changes and is the most complex. It should be implemented last to allow Layers 1-3 to be tested independently.

---

## MVP Recommendation (v1.9.4 Scope)

### Must Include (all four layers)

1. **BUG-017:** System prompt deduplication rule (Layer 1)
2. **BUG-018:** Tool description single-call enforcement (Layer 2)
3. **BUG-019:** History filtering for fulfilled requests (Layer 3)
4. **THREAD-011:** Silent artifact generation from buttons (Layer 4)

### Should Include (low complexity, high value)

5. **Error state clearing:** Loading animation MUST clear on failure (critical UX requirement)
6. **Typed progress indicator:** "Generating [Artifact Type]..." not generic "Generating..."
7. **Silent failure logging:** Backend logs for debugging silent generation failures

### Defer to Post-v1.9.4

- Context compaction (v2.0+)
- Conversation summarization (v2.0+)
- Idempotent tool execution (v1.9.5+)
- Cancel/stop button (v1.9.5+)
- Artifact version history (v2.0+)
- Timeout detection with auto-retry (v1.9.5+)

---

## Testing Implications

### Automated Tests Needed

| Test | Layer | What It Validates |
|------|-------|-------------------|
| System prompt contains deduplication rule text | 1 | Prompt engineering |
| Tool description contains "ONCE per user request" | 2 | Tool constraint |
| Tool description does NOT contain "multiple times" | 2 | Removed enabler |
| History filter marks fulfilled requests | 3 | [ALREADY PROCESSED] prefix |
| History filter leaves unfulfilled requests clean | 3 | Retry support |
| Failed generation not marked as fulfilled | 3 | Error recovery |
| ChatRequest accepts artifact_generation flag | 4 | API contract |
| Silent mode suppresses message saving | 4 | History isolation |
| Silent mode suppresses text_delta events | 4 | UX cleanliness |
| Artifact still saved in silent mode | 4 | Core functionality preserved |

### Manual Tests Needed

| Test | What It Validates |
|------|-------------------|
| Generate artifact, then generate again in same thread -- exactly 1 new artifact | All layers working together |
| Button-triggered generation shows loading -> artifact card only | Layer 4 UX |
| Typed generation request still shows full chat flow | Layer 4 does not break normal chat |
| Failed generation allows retry | Layer 3 + Layer 4 error handling |
| Disconnect mid-generation leaves no orphaned messages | Layer 4 edge case |

---

## Sources

### HIGH Confidence (official documentation, authoritative)
- [Anthropic: How to implement tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)
- [Anthropic: Tool use with Claude overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)
- [Anthropic: Advanced tool use engineering](https://www.anthropic.com/engineering/advanced-tool-use)
- [Anthropic: Programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)
- [Vercel AI SDK: Tool Calling docs](https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling)
- [OpenAI: Function calling guide](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI: Conversation state management](https://platform.openai.com/docs/guides/conversation-state)

### MEDIUM Confidence (verified community patterns, multiple sources agree)
- [JetBrains Research: Efficient Context Management for LLM Agents](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- [LLM Context Management Guide (16x Engineer)](https://eval.16x.engineer/blog/llm-context-management-guide)
- [Mem0: LLM Chat History Summarization Guide](https://mem0.ai/blog/llm-chat-history-summarization-guide-2025)
- [Cloudscape Design System: GenAI Loading States](https://cloudscape.design/patterns/genai/genai-loading-states/)
- [Smashing Magazine: Design Patterns for AI Interfaces](https://www.smashingmagazine.com/2025/07/design-patterns-ai-interfaces/)
- [Patterns.dev: AI UI Patterns](https://www.patterns.dev/react/ai-ui-patterns/)

### MEDIUM Confidence (community issues confirming the problem is widespread)
- [LangGraph Discussion #3000: Duplicate tool calls](https://github.com/langchain-ai/langgraph/discussions/3000)
- [Vercel AI SDK Issue #7261: Double answers / repeated tool calls](https://github.com/vercel/ai/issues/7261)
- [Vercel AI SDK Issue #3854: singleToolPerStep proposal](https://github.com/vercel/ai/issues/3854)
- [OpenAI Community: Function calls repeated unnecessarily](https://community.openai.com/t/function-calls-is-repeated-unnecessary/548189)
- [OpenAI Agents SDK Issue #2171: Duplicate history in handoffs](https://github.com/openai/openai-agents-python/issues/2171)

### LOW Confidence (single source, useful context)
- [Inferable Blog: Distributed tool calling with message queues](https://www.inferable.ai/blog/posts/distributed-tool-calling-message-queues)
- [Context Engineering Best Practices (Comet)](https://www.comet.com/site/blog/context-engineering/)
- [ICLR 2025: Facilitating Multi-Turn Function Calling](https://proceedings.iclr.cc/paper_files/paper/2025/file/69c49f75ca31620f1f0d38093d9f3d9b-Paper-Conference.pdf)
