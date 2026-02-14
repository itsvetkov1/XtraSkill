# Claude Code Backend Integration Research Summary

**Project:** BA Assistant Claude Code Integration Experiment
**Domain:** AI agent backend integration (Python SDK + CLI subprocess)
**Researched:** 2026-02-13
**Confidence:** HIGH

## Executive Summary

Claude Code Agent SDK provides structured agent loop capabilities through Python integration that adds multi-turn reasoning, file-based validation, and specialized subagent delegation beyond the existing direct API approach. Research confirms two viable integration paths: **Agent SDK Python library (recommended)** and **CLI subprocess (experimental)**. A critical finding invalidates the Phase 4.1 rejection rationale: the SDK **does NOT require separate Claude Code CLI installation** — the CLI is bundled with the package (v0.1.35+), eliminating the assumed infrastructure barrier.

The recommended approach is to implement both adapters as parallel experiments to measure quality differences for BRD generation. The Agent SDK adapter integrates via the existing `LLMAdapter` pattern but requires significant architectural considerations: event stream translation (SDK's multi-turn agent loop events ≠ API's single-turn events), subprocess lifecycle management in async FastAPI context, ContextVar boundary issues (does not cross subprocess boundaries), and tool execution model mismatch (agent's automatic loop vs manual AIService loop). Success depends on measurable quality improvements that justify 30-50% cost increases (1,100+ token overhead per request) and additional integration complexity.

Key risk: **PITFALL-01 (Event Stream Translation Data Loss)** — high probability of data loss when mapping SDK's multi-turn agent loop events to the existing `StreamChunk` format designed for single-turn API responses. Prevention requires defining an extended event vocabulary and frontend contract updates before implementation begins. If agent-based generation does not demonstrably improve document quality, the existing direct API approach with multi-pass prompting (generate → critique → revise) offers similar benefits without subprocess complexity.

## Key Findings

### Recommended Stack

Two integration approaches available, each with distinct technology profiles. See [STACK.md](./STACK.md) for detailed analysis.

**Approach 1: Agent SDK Python Library (RECOMMENDED)**

The Agent SDK is production-ready with bundled CLI, requiring only Python 3.10+ and no separate Node.js installation. Version 0.1.35 includes critical fixes for large agent payloads (no longer silently fail due to ARG_MAX limits) and native async support compatible with FastAPI. The backend already uses SDK v0.1.22 in `agent_service.py`, so this is an **upgrade path**, not a new dependency.

**Core technologies:**
- `claude-agent-sdk==0.1.35` (Python package) — Core agent loop orchestration, bundled CLI eliminates infrastructure dependency
- Python 3.10+ (already using 3.11) — Native async/await support for FastAPI integration
- Docker (optional) — Only needed if sandboxing becomes a requirement, not for basic integration

**Approach 2: CLI Subprocess (EXPERIMENTAL)**

CLI subprocess approach useful for quality comparison testing. Requires native binary installation, adds subprocess management complexity, but provides full Claude Code feature set.

**Core technologies:**
- Claude Code CLI v2.1.39+ (native binary) — Non-interactive agent execution with `--output-format stream-json`
- Node.js 18+ (only if using MCP servers) — Not required for basic CLI operation, native binary is standalone
- `asyncio.create_subprocess_exec` — Python subprocess management for CLI spawning

**Critical dependency insight:** Neither approach requires Node.js runtime unless adding MCP servers like Context7 or Playwright. The Phase 4.1 rejection reason ("requires Claude Code CLI as runtime dependency") is **no longer valid** — the SDK bundles its CLI internally.

### Expected Features

Claude Code enables agent-based generation workflows that differ architecturally from direct API approaches. See [FEATURES.md](./FEATURES.md) for detailed feature landscape.

**Must have (table stakes):**
- **Streaming responses** — SSE streaming via `query()` generator pattern, maintains current UX
- **Multi-turn conversations** — Sessions API maintains conversation history automatically
- **Tool integration** — Built-in tools (Read, Write, Bash) + custom MCP tools for existing backend integration
- **Model selection** — `model` parameter in ClaudeAgentOptions supports all Claude models
- **Error handling** — Hooks for PreToolUse/PostToolUse validation, graceful degradation
- **Token management** — `maxTurns` limit prevents runaway costs, usage metrics for tracking
- **Concurrent requests** — Stateless SDK instances with session isolation

**Should have (differentiators):**
- **Multi-turn agent loops (critique → revise)** — Agent generates document, spawns review subagent, incorporates feedback iteratively until quality threshold met
- **File-based validation workflows** — Write generated document to file, run validation scripts (schema checks, business rules), surface errors for agent to fix before returning to user
- **Extended thinking for document planning** — Enable adaptive thinking mode for initial planning phase (structure, sections, content strategy) before generation
- **Progressive content loading via Skills** — Package domain-specific templates and guidelines that load on-demand without context penalty
- **Specialized document review subagents** — Pre-configured subagents for each artifact type (BRD reviewer, user story reviewer) with focused quality prompts in separate context
- **Interleaved thinking with tool use** — Agent thinks BETWEEN tool calls (after document search results, after validation errors) to reason about next steps

**Defer (experimental/future):**
- **Background subagent processing** — Spawn long-running subagents (compliance check, batch validation) that don't block main conversation
- **Nested subagents** — SDK limitation: subagents cannot spawn other subagents, must chain sequentially
- **Custom package installation** — SDK cannot install packages at runtime for security reasons

**Anti-features (explicitly avoid):**
- **Forced tool use** — Incompatible with extended thinking, let agent autonomously decide
- **Real-time collaboration** — Agent SDK is request-response, not pub/sub; keep existing WebSocket architecture
- **Model fine-tuning** — SDK uses pre-trained models, achieve customization through Skills and few-shot examples

**MVP Recommendation:** Prioritize custom MCP tools (wrap existing backend services), basic review subagent, file-based validation, and streaming responses. Defer extended thinking and Skills to Phase 2 after measuring baseline quality improvement.

### Architecture Approach

Two adapter implementations required to conform to existing `LLMAdapter` ABC pattern, each with distinct integration complexity. See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed patterns and data flow.

**Approach A: Agent SDK Python Library (Primary)**

Integration centers on event stream translation and tool execution model alignment. The SDK produces multi-turn agent loop events (`AssistantMessage`, `StreamEvent`, `ResultMessage`) that must map to single-turn `StreamChunk` format. Critical challenge: SDK handles tool execution internally via MCP servers, but `AIService` expects external tool loop — adapter must bypass manual tool loop to avoid duplicate execution.

**Major components:**
1. **ClaudeAgentAdapter** (`llm/claude_agent_adapter.py`) — Translates SDK events to StreamChunk format, manages MCP server with BA tools, handles session state
2. **Shared MCP Tools** (`services/mcp_tools.py`) — Extracted from existing `agent_service.py`, wraps `search_documents` and `save_artifact` for reuse across adapters
3. **Event Translation Layer** — Maps SDK message types: `TextBlock` → text chunk, `ToolUseBlock` → tool_use chunk (visibility only, SDK executes), `ResultMessage` → complete chunk with usage

**Key integration challenge:** ContextVar does NOT cross subprocess boundaries. Existing `agent_service.py` uses ContextVar for database session and project_id propagation to tools. SDK spawns subprocess, so ContextVar lookups fail. **Solution:** Use MCP HTTP transport instead of stdio, pass context in HTTP headers, look up database session from pool in tool execution.

**Approach B: CLI Subprocess (Secondary)**

CLI subprocess approach adds process lifecycle management and JSON parsing. Spawn Claude Code CLI with `--output-format stream-json`, parse line-delimited JSON from stdout, translate to StreamChunk events. Subprocess overhead adds 200-500ms startup latency and complexity for process cleanup (zombies, memory leaks in async context).

**Major components:**
1. **ClaudeCLIAdapter** (`llm/claude_cli_adapter.py`) — Subprocess spawning with proper flags, line-buffered JSON parsing, event translation
2. **CLI Process Manager** (`services/cli_process.py`) — Process lifecycle (timeout, cleanup, zombie prevention), stderr capture for error translation
3. **MCP Server Process** (optional) — Separate process for BA tools if tool support needed, communicates via stdio

**Build order:**
1. **Phase 1: Shared MCP Tools** — Extract tool wrappers from `agent_service.py` (1-2 hours)
2. **Phase 2: Agent SDK Adapter** — Implement SDK adapter with event translation (4-6 hours)
3. **Phase 3: CLI Subprocess Adapter** — Implement CLI adapter for comparison (6-8 hours)
4. **Phase 4: Quality Comparison** — Generate BRDs with both approaches, measure quality differences (3-4 hours)

**Unchanged files:** `ai_service.py` and `routes/threads.py` remain unchanged — adapter pattern isolates changes.

### Critical Pitfalls

Research identified 18+ integration pitfalls across event translation, subprocess management, context propagation, tool execution, cost overhead, and error handling. See [PITFALLS.md](./PITFALLS.md) for comprehensive prevention strategies.

**Top 5 pitfalls by impact:**

1. **Event Stream Translation Data Loss (CRITICAL)** — SDK's multi-turn agent loop produces events that don't map cleanly to existing `StreamChunk` format designed for single-turn API responses. Data loss scenarios: intermediate reasoning lost, multi-turn text concatenated without boundaries, tool result content dropped, usage stats overwritten. **Prevention:** Define extended event vocabulary (`agent_turn_start`, `agent_turn_complete`, `agent_thinking`) before implementation, update frontend contract, accumulate usage across all turns.

2. **Subprocess Lifecycle Management in Async Context (CRITICAL)** — SDK spawns CLI as subprocess in FastAPI's async event loop. Memory leaks occur when debugging code with repeated subprocess calls, zombie processes accumulate if `wait()` not called, Uvicorn graceful shutdown does NOT terminate child processes (v0.29.0 issue). **Prevention:** Implement process pool with lifespan management, use `tini` with `-g` flag in Docker, add subprocess health checks and cleanup handlers.

3. **ContextVar Does NOT Cross Subprocess Boundaries (CRITICAL)** — Existing `agent_service.py` uses ContextVar for database session and project_id propagation. SDK spawns subprocess with separate Python interpreter, so ContextVar lookups fail with `LookupError`. **Prevention:** Use MCP HTTP transport (not stdio), pass context in HTTP headers, look up database session from pool in tool execution. Alternative: serialize context to environment variables (fragile, database sessions cannot pickle).

4. **Tool Execution Model Mismatch (CRITICAL)** — Existing `AIService` has manual tool loop (adapter yields `tool_use` chunk, AIService executes tool, calls adapter again with result). SDK has automatic agent loop (executes tools internally via MCP). Wrapping SDK in LLMAdapter causes duplicate tool execution or infinite loops. **Prevention:** Bypass adapter pattern for agent provider (separate code path) OR disable AIService tool loop for agent adapter instances.

5. **Cost and Latency Overhead (HIGH)** — SDK adds ~1,100 tokens per request (346 token tool use system prompt + 750 tokens for 5 tool definitions) before user message. Multi-turn agent loops compound cost: direct API 1 turn (5K input/3K output = $0.060), SDK 3 turns (7K input/4K output = $0.081) = **35% cost increase**. Subprocess IPC adds 100-500ms latency (CLI startup 200ms + first API call 100ms). **Prevention:** Use Agent SDK only for complex tasks (BRD generation), optimize tool descriptions (reduce token count), monitor usage and implement budget-based routing.

**Additional critical pitfalls:**
- **Error Handling Asymmetry** — Subprocess errors lose context during IPC, manifest as generic "process exited with code 1" instead of structured API errors. Capture stderr, map error patterns to user-friendly messages.
- **Session State Management Asymmetry** — Database is source of truth, but SDK's ConversationSession maintains separate state. Use stateless mode (pass full conversation history each time) to avoid desync.
- **Streaming Latency** — Line buffering in subprocess stdout delays first token. Flush stdout aggressively, measure time-to-first-token.

## Cross-Cutting Concerns

**Cost Management:**
Agent SDK adds 30-50% cost overhead per request. Implement routing logic: complex tasks (BRD generation) use Agent SDK for quality, simple chat uses direct API for cost. Monitor token usage, set per-user budgets, optimize tool definitions.

**Quality Measurement:**
Success depends on measurable quality improvements. Define metrics: section completeness (all 13 BRD sections present), acceptance criteria quality (measurable thresholds, explicit actors), error scenario coverage (at least 2 per requirement), structural consistency (no duplicate headings). A/B test: generate BRDs with direct API (baseline), SDK adapter, and CLI adapter. Decision: if SDK/CLI > 20% better than direct API, adopt for production; if no measurable improvement, stay with direct API + multi-pass prompting.

**Process Safety:**
Async subprocess management is error-prone. Use FastAPI lifespan events for process pool initialization/cleanup, implement subprocess health checks, use `tini` in Docker for signal propagation, monitor process count with middleware, add timeouts and cleanup handlers.

**Tool Integration:**
Existing tools (`search_documents`, `save_artifact`) must work across SDK and CLI adapters. Extract to shared `mcp_tools.py`, use MCP HTTP transport to avoid ContextVar boundary issues, validate MCP configuration on startup.

**Debugging:**
Subprocess errors are opaque. Capture stderr from CLI, add structured logging to adapter translation layers, implement error category mapping for user-friendly messages, use health check middleware to detect CLI availability issues early.

## Recommended Phase Structure

Based on research findings, suggested experimentation roadmap to validate quality improvement hypothesis and measure integration complexity.

### Phase 1: Shared MCP Tools (Prerequisite)
**Rationale:** Both adapters need reusable tool wrappers. Extract before implementing adapters to avoid duplication.
**Delivers:** `mcp_tools.py` with shared tool wrappers for `search_documents` and `save_artifact`
**Addresses:** Tool integration (table stakes feature), ContextVar boundary issues (PITFALL-03)
**Avoids:** Tool execution model mismatch (PITFALL-04) by separating tool logic from adapter implementations
**Estimated effort:** 1-2 hours
**Research flags:** Standard refactoring pattern, no deeper research needed

### Phase 2: Agent SDK Adapter (Primary Integration)
**Rationale:** SDK is recommended approach with bundled CLI, lower operational complexity than subprocess
**Delivers:** `ClaudeAgentAdapter` implementing `LLMAdapter` ABC with full event translation
**Uses:** `claude-agent-sdk==0.1.35` (STACK.md), shared MCP tools from Phase 1
**Implements:** Event translation layer (ARCHITECTURE.md), MCP HTTP transport for context propagation
**Addresses:** Multi-turn agent loops, streaming responses, tool integration (FEATURES.md table stakes)
**Avoids:** Event stream data loss (PITFALL-01) via extended event vocabulary, subprocess lifecycle issues (PITFALL-02) via proper async handling, ContextVar boundary issues (PITFALL-03) via MCP HTTP transport
**Estimated effort:** 4-6 hours
**Research flags:** No deeper research needed, implementation follows documented SDK patterns

### Phase 3: CLI Subprocess Adapter (Experimental Comparison)
**Rationale:** Build second adapter to measure quality differences between SDK and CLI approaches
**Delivers:** `ClaudeCLIAdapter` with subprocess management and JSON parsing
**Uses:** Claude Code CLI v2.1.39+ (STACK.md)
**Implements:** Subprocess lifecycle management, JSON event translation (ARCHITECTURE.md)
**Addresses:** Same feature set as Phase 2 for apples-to-apples comparison
**Avoids:** Memory leaks (PITFALL-02) via process pool, zombie processes via cleanup handlers, graceful shutdown failures via lifespan management
**Estimated effort:** 6-8 hours
**Research flags:** Subprocess management in async context may need validation testing — patterns documented but error-prone

### Phase 4: Quality Comparison & Decision (Measurement)
**Rationale:** Success depends on measurable quality improvements justifying integration complexity
**Delivers:** Quality metrics report, cost analysis, latency measurements, go/no-go decision
**Approach:** Generate 5 BRDs each with direct API (baseline), SDK adapter, CLI adapter. Compare: section completeness, acceptance criteria quality, error scenario coverage, structural consistency.
**Metrics:**
- Quality: Validation pass rate, user-reported issues
- Cost: Token usage per request, 30-day projected spend
- Performance: Time-to-first-token, total generation time
**Decision criteria:**
- If SDK/CLI > 20% better quality than direct API → adopt for production
- If SDK significantly better than CLI → deprecate CLI path
- If no measurable improvement → stay with direct API + multi-pass prompting
**Estimated effort:** 3-4 hours
**Research flags:** Standard A/B testing, no deeper research needed

### Phase 5: Production Hardening (If Proceeding)
**Rationale:** If Phase 4 shows quality improvement, harden for production deployment
**Delivers:** Process pool with lifespan management, error translation layer, cost tracking, monitoring
**Addresses:** Cost overhead (PITFALL-06) via routing logic, error handling asymmetry (PITFALL-07) via stderr capture and category mapping
**Avoids:** Subprocess leaks (PITFALL-02) via monitoring middleware, session state issues (PITFALL-05) via stateless mode
**Estimated effort:** 6-8 hours
**Research flags:** Production deployment patterns well-documented, follow official hosting guide

### Phase Ordering Rationale

- **Phase 1 first:** Tool extraction is prerequisite for both adapters, prevents duplication
- **Phase 2 before 3:** SDK is recommended approach with lower risk, validate integration pattern before adding subprocess complexity
- **Phase 3 for comparison:** CLI adapter useful only if SDK proves viable, skip if Phase 2 uncovers blockers
- **Phase 4 gates Phase 5:** Do not proceed with production hardening until quality improvement proven
- **Dependencies:** Phase 2 depends on Phase 1 (shared tools), Phase 4 depends on Phases 2+3 (need both adapters for comparison), Phase 5 depends on Phase 4 decision (conditional)

### Research Flags

**Phases needing validation during implementation:**
- **Phase 3:** Subprocess management in async FastAPI context — patterns documented but memory leaks and zombie processes common, may need trial-and-error for graceful cleanup
- **Phase 4:** Quality measurement methodology — need to define what "20% better" means concretely (validation pass rate? user satisfaction? specific structural checks?)

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Tool extraction is standard refactoring, existing `agent_service.py` already implements MCP tool pattern
- **Phase 2:** SDK integration follows official documentation, event translation is well-defined mapping
- **Phase 5:** Production hosting patterns documented in official Agent SDK hosting guide, Docker deployment is standard FastAPI pattern

## Decision Criteria

**Proceed with Agent SDK integration if:**
- Phase 4 quality comparison shows >20% improvement in validation pass rate OR significant reduction in user-reported quality issues
- Team has capacity for 2-3 weeks integration effort (15-25 hours total across all phases)
- Infrastructure supports subprocess orchestration (Docker deployment, process monitoring)
- Budget accommodates 30-50% cost increase (or routing logic can mitigate by using SDK only for complex tasks)

**Stay with direct API approach if:**
- Phase 4 shows no measurable quality improvement
- Cost increase (35-52% per PITFALL-06) not justified by quality gains
- Integration complexity (event translation, subprocess management) too high for current team capacity
- Existing multi-pass prompting (generate → critique → revise) achieves similar quality without architectural changes

**Alternative approach to consider:**
Enhance direct API with multi-pass prompting before committing to Agent SDK. Implement critique-revise loop using existing `AnthropicAdapter`:
1. Generate BRD with direct API
2. Send to same model with review prompt ("Check this BRD for completeness, consistency, clarity")
3. Incorporate feedback and regenerate
4. Compare quality to single-pass generation

This achieves similar quality benefits (review loop, iterative refinement) without subprocess complexity, ContextVar boundary issues, or 30-50% cost overhead.

## Open Questions

**To resolve during Phase 1-2 (Architecture Validation):**
1. **MCP HTTP transport:** Does it solve ContextVar boundary issue? Can database session be looked up from pool using session ID passed in headers? (CRITICAL for PITFALL-03)
2. **Event vocabulary completeness:** What additional event types does frontend need for agent turn boundaries? Can existing `StreamChunk` format be extended or does it require breaking change?
3. **Adapter pattern viability:** Can Agent SDK fit into `LLMAdapter` ABC without bypassing AIService tool loop? Or does it require separate code path? (CRITICAL for PITFALL-04)

**To measure during Phase 4 (Quality Comparison):**
1. **Quality improvement magnitude:** Is difference between SDK and direct API >20% on validation pass rate? Which specific quality aspects improve (completeness? consistency? clarity?)
2. **Cost justification:** Does quality improvement justify 35-52% cost increase? Can routing logic (complex tasks → SDK, simple chat → direct API) mitigate cost while preserving quality gains?
3. **SDK vs CLI quality:** Is there measurable difference between SDK adapter and CLI adapter output quality? If CLI significantly better, does it justify subprocess complexity?

**To validate during Phase 5 (Production Hardening):**
1. **Subprocess stability:** Under load testing (100+ concurrent requests), do memory leaks or zombie processes occur? Do graceful shutdown handlers properly terminate all subprocesses?
2. **Error handling sufficiency:** Do stderr capture and error category mapping provide actionable error messages for debugging production issues?
3. **Monitoring coverage:** Are subprocess health checks, token usage tracking, and process count monitoring sufficient for production operations?

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | SDK v0.1.35 verified on PyPI with release notes, bundled CLI documented in official SDK docs, dependency requirements clear |
| Features | MEDIUM | Core capabilities documented in official SDK docs, but quality improvement claims theoretical (no BA-specific benchmarks found) |
| Architecture | HIGH | Integration patterns documented, existing `agent_service.py` provides implementation reference, adapter pattern well-understood |
| Pitfalls | HIGH | All 18 pitfalls verified against official docs, Python issue trackers, and recent technical articles (2026), prevention strategies sourced from production guides |

**Overall confidence:** HIGH

### Gaps to Address

**During Phase 1-2 (Architecture Validation):**
- **MCP HTTP transport validation:** Research documents MCP HTTP as solution for ContextVar boundary, but no production examples found for FastAPI + SQLAlchemy AsyncSession context. Need proof-of-concept to validate before committing to SDK approach.
- **Event mapping completeness:** PITFALL-01 prevention requires extended event vocabulary, but frontend contract update scope unknown. Need to prototype event translation layer to identify all required event types before implementation.

**During Phase 4 (Quality Comparison):**
- **Quality metrics definition:** "Measurable quality improvement" needs concrete metrics. Define specific checks: validation pass rate threshold (e.g., SDK passes 85% vs direct API passes 70%), user-reported issues reduction target (e.g., 30% fewer structure complaints), structural consistency checks (e.g., zero duplicate headings).
- **Cost-quality tradeoff analysis:** 35-52% cost increase needs business justification framework. Define acceptable cost per quality point improvement (e.g., $0.01 extra cost for 10% validation improvement is acceptable).

**During Phase 5 (Production Hardening):**
- **Subprocess monitoring completeness:** Prevention strategies documented for memory leaks and zombie processes, but no comprehensive subprocess monitoring framework found for FastAPI. May need to build custom monitoring middleware.
- **Graceful shutdown validation:** Uvicorn #2281 documents child process termination issue, `tini` with `-g` flag suggested as solution, but no production validation examples found. Need load testing to verify cleanup handlers work under concurrent request load.

## Sources

### Primary Sources (HIGH confidence)

**Official Anthropic Documentation:**
- [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview) — Core capabilities, integration patterns
- [Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python) — API documentation, message types, query() function
- [Agent SDK Hosting Guide](https://platform.claude.com/docs/en/agent-sdk/hosting) — Production deployment patterns
- [Agent SDK Streaming Output](https://platform.claude.com/docs/en/agent-sdk/streaming-output) — Event types, streaming patterns
- [Agent SDK Sessions](https://platform.claude.com/docs/en/agent-sdk/sessions) — Conversation state management
- [Agent SDK Cost Tracking](https://platform.claude.com/docs/en/agent-sdk/cost-tracking) — Token overhead analysis
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference) — CLI flags, output formats
- [Extended Thinking Documentation](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) — Adaptive thinking, interleaved thinking
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — Progressive content loading
- [Custom Tools Documentation](https://platform.claude.com/docs/en/agent-sdk/custom-tools) — MCP tool integration

**Package Repositories:**
- [claude-agent-sdk on PyPI](https://pypi.org/project/claude-agent-sdk/) — Version 0.1.35 release notes, dependency requirements
- [Agent SDK GitHub Releases](https://github.com/anthropics/claude-agent-sdk-python/releases) — Breaking changes v0.1.22 → v0.1.35, ARG_MAX fix in v0.1.31

**Python Official Documentation:**
- [contextvars Documentation](https://docs.python.org/3/library/contextvars.html) — ContextVar behavior, subprocess boundaries
- [asyncio subprocess](https://docs.python.org/3/library/asyncio-subprocess.html) — Subprocess management in async context

### Secondary Sources (MEDIUM confidence)

**Technical Articles (2026):**
- [Claude Code Internals Part 7: SSE Stream Processing](https://kotrotsos.medium.com/claude-code-internals-part-7-sse-stream-processing-c620ae9d64a1) — Event stream structure
- [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — Integration patterns
- [FastAPI Best Practices for Production: Complete 2026 Guide](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026) — Lifespan management, async patterns
- [Gracefully Implementing Graceful Shutdowns](https://oneuptime.com/blog/post/2026-02-09-graceful-shutdown-handlers/view) — Subprocess cleanup, tini usage
- [Claude Agent SDK and Microsoft Agent Framework](https://devblogs.microsoft.com/semantic-kernel/build-ai-agents-with-claude-agent-sdk-and-microsoft-agent-framework/) — Integration examples

**Community Resources:**
- [Building agents with critique loops](https://medium.com/flow-specialty/ai-assisted-coding-automating-plan-reviews-with-claude-code-and-codex-for-higher-quality-plans-c7e373a625ca) — Multi-turn review patterns
- [Tracing Claude Code's agent loop](https://medium.com/@georgesung/tracing-claude-codes-llm-traffic-agentic-loop-sub-agents-tool-use-prompts-7796941806f5) — Agent loop architecture
- [File-based validation workflows](https://github.com/Pimzino/claude-code-spec-workflow) — Validation integration examples
- [Running Claude Code from Windows CLI](https://dstreefkerk.github.io/2026-01-running-claude-code-from-windows-cli/) — Subprocess patterns, JSON parsing
- [Docker Sandbox Configuration](https://docs.docker.com/ai/sandboxes/claude-code/) — Container deployment

### Tertiary Sources (LOW confidence, needs validation)

**GitHub Issues (Python ecosystem):**
- [Python #25829](https://bugs.python.org/issue25829) — Zombie process creation with asyncio + subprocess
- [Python #28165](https://bugs.python.org/issue28165) — Subprocess memory leak
- [Debugpy #1884](https://github.com/microsoft/debugpy/issues/1884) — Memory leak with repeated subprocess calls
- [Uvicorn #2281](https://github.com/Kludex/uvicorn/discussions/2281) — Child process termination issue (v0.29.0)

**Community Discussions:**
- [Asyncio Context Variables For Shared State](https://superfastpython.com/asyncio-context-variables/) — ContextVar propagation behavior
- [The contextvars and chain of asyncio tasks in Python](https://valarmorghulis.io/tech/202408-the-asyncio-tasks-and-contextvars-in-python/) — ContextVar subprocess boundaries
- [Back-propagation of ContextVar changes from worker threads](https://discuss.python.org/t/back-propagation-of-contextvar-changes-from-worker-threads/15928) — ContextVar limitations

---

**Research completed:** 2026-02-13
**Ready for roadmap:** No — this is an experimental integration to validate quality improvement hypothesis. Do NOT proceed with roadmap until Phase 4 quality comparison confirms >20% improvement over existing direct API approach. If quality improvement not proven, stay with direct API + multi-pass prompting enhancement.
