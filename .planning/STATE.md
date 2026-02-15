# Project State

## Project Reference

See: /Users/a1testingmac/projects/XtraSkill/.planning/PROJECT.md (updated 2026-02-12)

**Core value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

**Current focus:** v0.1-claude-code — Claude Code as AI Backend experiment

## Current Position

Milestone: v0.1-claude-code — Claude Code as AI Backend
Phase: 60 of 61 (Frontend Integration)
Current Plan: 1 completed
Status: Plan Complete
Last activity: 2026-02-15 — Completed Phase 60 Plan 01: Claude Code Provider Registration

Progress:
```
v1.0-v1.9.5: [##########] 48 phases, 115 plans, 11 milestones SHIPPED
v2.1:        [##########] 8/8 plans (Phase 54-56) SHIPPED
v2.0:        [          ] Backlogged (phases 49-53 preserved)

v0.1-claude-code: [█████████▓] 95% — Phase 60-01 complete, evaluation pending
```

## Performance Metrics

**Velocity:**
- Total plans completed: 127 (across 13 milestones)
- Average duration: ~1-3 minutes per plan

**Phase 57 Metrics:**

| Plan | Duration (s) | Tasks | Files | Status |
|------|--------------|-------|-------|--------|
| P01  | 13661        | 2     | 3     | ✅ Complete |
| P02  | 235          | 2     | 7     | ✅ Complete |

**Phase 58 Metrics:**

| Plan | Duration (s) | Tasks | Files | Status |
|------|--------------|-------|-------|--------|
| P01  | 368          | 2     | 4     | ✅ Complete |
| P02  | 562          | 2     | 5     | ✅ Complete |

**Phase 59 Metrics:**

| Plan | Duration (s) | Tasks | Files | Status |
|------|--------------|-------|-------|--------|
| P01  | 212          | 2     | 2     | ✅ Complete |
| P02  | 180          | 2     | 1     | ✅ Complete |

**Phase 60 Metrics:**

| Plan | Duration (s) | Tasks | Files | Status |
|------|--------------|-------|-------|--------|
| P01  | 184          | 2     | 4     | ✅ Complete |

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
| Dedup v1.9.4 | 40-42 | 5/5 | SHIPPED 2026-02-05 |
| Logging v1.9.5 | 43-48 | 8/8 | SHIPPED 2026-02-08 |
| Rich Docs v2.1 | 54-56 | 8/8 | SHIPPED 2026-02-12 |
| Security v2.0 | 49-53 | 0/TBD | BACKLOGGED 2026-02-13 |
| Claude Code v0.1 | 57-61 | 7/TBD | IN PROGRESS — Phase 60-01 complete |

**Total:** 130 plans shipped across 50 phases

## Accumulated Context

### Decisions

Recent key decisions (full archive in PROJECT.md):
- **Phase 59-01**: Combined prompt approach (prepend system prompt to user prompt) instead of --system-prompt flag for POC (2026-02-14)
- **Phase 59-01**: Track received_result flag to prevent duplicate completion chunks (2026-02-14)
- **Phase 59-01**: Exclude --include-partial-messages from CLI flags (deferred to production scope) (2026-02-14)
- **Phase 59-01**: Use ContextVars for MCP tool context (subprocess inherits context in-process for POC) (2026-02-14)
- **Phase 58-01**: POC uses in-process MCP with ContextVars (HTTP transport deferred to production hardening) (2026-02-14)
- **Phase 58-01**: StreamChunk.metadata field added as optional to avoid breaking existing adapters (2026-02-14)
- **Phase 58-01**: AIService routes based on is_agent_provider attribute, preserves manual tool loop for direct API (2026-02-14)
- **Phase 58-01**: Tool status messages map MCP names to user-friendly indicators ('Generating artifact...', 'Searching project documents...') (2026-02-14)
- **Phase 57-02**: Both Claude Code providers use ANTHROPIC_API_KEY (Claude Code uses same Anthropic key) (2026-02-13)
- **Phase 57-02**: SDK default model claude-sonnet-4-5-20250514, CLI uses claude-sonnet-4-5-20250929 (2026-02-13)
- **Phase 57-01**: Extracted MCP tool definitions to shared module for reuse across SDK and CLI adapters (2026-02-13)
- **Phase 57-01**: Recreated venv with Python 3.12 (SDK requires 3.10+) (2026-02-13)
- **Phase 57-01**: Used factory pattern (create_ba_mcp_server) for MCP server creation (2026-02-13)
- **v2.0 backlogged**: Security & Deployment paused to focus on Claude Code experiment (2026-02-13)
- **Experiment promoted**: Claude Code backend moved from `.planning/experiments/` to main `.planning/` flow
- **Branch isolation**: All experiment work on `feature/claude-code-backend`, Phase 61 gates merge to master
- **Research both approaches**: Compare SDK (Python API) and CLI (subprocess) before committing
- **v0.1-claude-code versioning**: Clean slate, doesn't interfere with v2.x production track
- [Phase 60-01]: Experimental badge pattern using Material 3 secondaryContainer color scheme
- [Phase 60-01]: Model name display format using em-dash separator for clean visual separation

### Critical Research Findings

**From research/SUMMARY.md:**
- SDK bundles CLI internally (v0.1.35+) — Phase 4.1 rejection reason no longer valid
- Event stream translation is CRITICAL pitfall — SDK's multi-turn events don't map cleanly to StreamChunk format
- ContextVar boundary issue — subprocess loses context, requires MCP HTTP transport solution
- Cost overhead: 30-50% increase per request (1,100+ token overhead)
- Decision criteria: Need >20% quality improvement to justify integration complexity

### Pending Todos

- [ ] Configure CODECOV_TOKEN secret in GitHub repository
- [ ] Link repository to Codecov dashboard

### Blockers/Concerns

**Validation needed during Phase 60 (Evaluation):**
- Multi-turn conversation handling (SDK vs CLI agent loops)
- Event stream completeness (any CLI events lost in translation?)
- Source attribution accuracy (documents_used tracking via ContextVar)
- Token usage reporting (input/output token counts)
- Subprocess overhead (memory usage, process cleanup verification)

**Measurement needed during Phase 61:**
- Quality metrics definition — what does "20% better" mean concretely?
- Cost-quality tradeoff — does improvement justify 35-52% cost increase?
- HTTP transport decision — if SDK chosen, implement HTTP MCP server for production context isolation
- Production hardening for CLI adapter (partial messages, MCP HTTP transport, system prompt separation)

## Session Continuity

Last session: 2026-02-15
Stopped at: Completed Phase 60 Plan 01 — Claude Code Provider Registration
Resume file: None
Next action: Continue Phase 60 (if more plans exist) or proceed to Phase 61 — Quality Evaluation

**Context for Next Session:**
- Phase 60-01 COMPLETE: Claude Code providers registered across full stack
  - Task 1: Backend and frontend registration (3ec4f4c)
    - Added claude-code-sdk and claude-code-cli to backend VALID_PROVIDERS
    - Extended ProviderConfig with isExperimental and modelName fields
    - Created claudeCodeSdk and claudeCodeCli provider configs
    - Added providers to ProviderProvider._availableProviders
  - Task 2: Settings dropdown UI enhancement (2c87b4d)
    - Experimental badge display for Claude Code providers
    - Model name display with em-dash separator
    - Material 3 color scheme for consistent styling
  - All tests pass: 265 backend unit tests, flutter analyze clean
  - Users can now select Claude Code providers in settings
  - Backend accepts Claude Code providers for thread creation
- Ready for manual E2E testing (add to TESTING-QUEUE.md)
- Phase 60 may have additional plans for quality evaluation/comparison

---

*State updated: 2026-02-14 (Phase 59 complete)*
