# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

**Current focus:** v1.9.4 Artifact Generation Deduplication

## Current Position

Milestone: v1.9.4
Phase: 42 (Silent Artifact Generation)
Plan: 2 of 3 complete (42-01, 42-02)
Status: In progress
Last activity: 2026-02-05 - Completed 42-02-PLAN.md
Next action: Execute 42-03-PLAN.md (Integration testing / UI wiring)

Progress:
```
v1.9.4: [███████...] 16/35 requirements (46%)

Phase 40 - Prompt Engineering Fixes:     Complete (8 reqs)
Phase 41 - Structural History Filtering: Complete (6 reqs)
Phase 42 - Silent Artifact Generation:   In Progress (2/3 plans, 42-01 + 42-02 done)
```

## Performance Metrics

**Velocity:**
- Total plans completed: 105 (across 10 milestones)
- Average duration: ~2-18 minutes per plan (improving with experience)

**By Milestone:**

| Milestone | Phases | Plans | Status |
|-----------|--------|-------|--------|
| MVP v1.0 | 1-5 (includes 4.1) | 20/20 | SHIPPED 2026-01-28 |
| Beta v1.5 | 6-10 | 15/15 | SHIPPED 2026-01-30 |
| UX v1.6 | 11-14 | 5/5 | SHIPPED 2026-01-30 |
| URL v1.7 | 15-18 | 8/8 | SHIPPED 2026-01-31 |
| LLM v1.8 | 19-22 | 8/8 | SHIPPED 2026-01-31 |
| UX v1.9 | 23-27 | 9/9 | SHIPPED 2026-02-02 |
| Unit Tests v1.9.1 | 28-33 | 24/24 | SHIPPED 2026-02-02 |
| Resilience v1.9.2 | 34-36 | 9/9 | SHIPPED 2026-02-04 |
| Doc & Nav v1.9.3 | 37-39 | 3/3 | SHIPPED 2026-02-04 |
| Dedup v1.9.4 | 40-42 | 4/5 | IN PROGRESS |

**Total:** 105 plans shipped across 42 phases

## Accumulated Context

### Decisions

| Decision | Phase | Rationale |
|----------|-------|-----------|
| Deduplication rule at priority 2 | 40-01 | After one-question-at-a-time but before mode detection - critical for all phases |
| Tool results as completion evidence | 40-01 | ARTIFACT_CREATED marker from BUG-019 is dead code - tool results are reliable |
| Escape hatch: regenerate/revise/update/create-new-version | 40-01 | Covers user intent to modify artifacts without overly broad catch-all |
| Positive framing in deduplication rule | 40-01 | "ONLY act on MOST RECENT" clearer than negative framing per PROMPT-02 |
| Single-call enforcement in tool description | 40-01 | Tool description guides model directly - explicit constraint prevents duplication |
| Filter fulfilled pairs before truncation | 41-01 | Ensures truncation works on already-filtered conversation for accurate token estimation |
| 5-second correlation window for artifacts | 41-01 | Wide enough to catch typical latency, narrow enough to avoid false positives |
| Use total_seconds() for timestamp comparison | 41-01 | Handles timezone-aware vs naive datetime issues safely across DBs |
| text_delta is only SSE event suppressed in silent mode | 42-01 | message_complete needed for usage, artifact_created for frontend, error for debugging |
| Ephemeral instruction appended in-memory only | 42-01 | Guides model to artifact-only generation without persisting to DB |
| Token tracking unconditional in silent mode | 42-01 | All API calls must be tracked for budget enforcement (ERR-04) |
| generateArtifact() separate state machine from sendMessage() | 42-02 | PITFALL-06: prevents blank message bubbles, streaming UI conflicts |
| State clears on ArtifactCreatedEvent not MessageCompleteEvent | 42-02 | PITFALL-05: artifact appears before stream ends; user sees result immediately |
| Error source tagging via _lastOperationWasGeneration | 42-02 | UI can distinguish generation errors from chat errors for appropriate retry UI |

Milestone decisions archived in:
- .planning/milestones/v1.5-ROADMAP.md
- .planning/milestones/v1.6-ROADMAP.md
- .planning/milestones/v1.7-ROADMAP.md
- .planning/milestones/v1.8-ROADMAP.md
- .planning/milestones/v1.9-ROADMAP.md
- .planning/milestones/v1.9.1-ROADMAP.md
- .planning/milestones/v1.9.2-ROADMAP.md
- .planning/milestones/v1.9.3-ROADMAP.md

### v1.9.4 Key Context

**Bug:** BUG-016 (artifact multiplication). Root cause: unfiltered conversation context + permissive tool description causes model to re-execute fulfilled artifact requests.

**Strategy:** 4-layer defense-in-depth (prompt rule, tool description, history annotation, silent generation). Zero new dependencies.

**Critical pitfalls to remember:**
- PITFALL-01: BUG-019's `ARTIFACT_CREATED:` marker is from dead code -- must use alternative detection
- PITFALL-03: Deduplication rule must include re-generation escape hatch
- PITFALL-04: History prefix must not leak to user (use short/HTML-comment format)
- PITFALL-05: State clears on ArtifactCreatedEvent not MessageCompleteEvent (DONE in 42-02)
- PITFALL-06: `generateArtifact()` must be separate code path from `sendMessage()` (DONE in 42-02)

**Research:** .planning/research/SUMMARY.md (HIGH confidence, 2026-02-05)

### Pending Todos

- [ ] Configure CODECOV_TOKEN secret in GitHub repository
- [ ] Link repository to Codecov dashboard
- [ ] Manual testing of remaining features (see TESTING-QUEUE.md)
- [ ] Fix 2 pre-existing test failures in conversation_provider_test.dart (streamingText preservation)

### Blockers/Concerns

**No current blockers**

## Session Continuity

Last session: 2026-02-05
Stopped at: Completed 42-02-PLAN.md
Resume file: None
Next action: Execute 42-03-PLAN.md (Integration testing / UI wiring)

**Context for Next Session:**
- Phase 40 complete: Layers 1+2 of deduplication (prompt rule + tool description)
- Phase 41 complete: Layer 3 (structural history filtering via timestamp correlation)
- Phase 42 in progress: Layer 4 (silent generation) - most complex phase
  - 42-01 DONE: Backend ChatRequest.artifact_generation flag, conditional persistence, SSE filtering
  - 42-02 DONE: Frontend generateArtifact() separate from sendMessage(), retry/cancel, state management
  - 42-03 NEXT: Integration testing and wiring preset buttons to silent generation
- Phase 42 is the final phase for v1.9.4 milestone

---

*State updated: 2026-02-05 (42-02 complete)*
