# Project State

## Project Reference

See: /Users/a1testingmac/projects/XtraSkill/.planning/PROJECT.md (updated 2026-02-12)

**Core value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

**Current focus:** Post-experiment — CLI adapter merged to master

## Current Position

Milestone: v0.1-claude-code — Claude Code as AI Backend — COMPLETE
Phase: 61 of 61 (Quality Comparison & Decision) — COMPLETE
Status: Experiment concluded — CLI adapter adopted, merged to master
Last activity: 2026-02-17 — Phase 61 wrapped up, branch merged to master

Progress:
```
v1.0-v1.9.5: [##########] 48 phases, 115 plans, 11 milestones SHIPPED
v2.1:        [##########] 8/8 plans (Phase 54-56) SHIPPED
v2.0:        [          ] Backlogged (phases 49-53 preserved)

v0.1-claude-code: [##########] 100% — COMPLETE (CLI adopted, merged to master 2026-02-17)
```

## Performance Metrics

**Velocity:**
- Total plans completed: 131 (across 13 milestones)
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
| P02  | 109          | 2     | 2     | ✅ Complete |

**Phase 61 Metrics:**

| Plan | Duration (s) | Tasks | Files | Status |
|------|--------------|-------|-------|--------|
| P01  | 191          | 2     | 4     | ✅ Complete |
| P02  | 242          | 2     | 4     | ✅ Complete |

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
| Claude Code v0.1 | 57-61 | 11/12 (1 skipped) | SHIPPED 2026-02-17 |

**Total:** 132 plans shipped across 50 phases
| Phase 61 P01 | 191 | 2 tasks | 4 files |

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
- [Phase 60-02]: Thread info accessed via info button in AppBar (positioned before edit button)
- [Phase 60-02]: Provider indicator two-line layout for Claude Code providers (name + model), single-line for existing providers
- [Phase 61-01]: Test scenario complexity distribution: 2 low, 2 medium, 1 high (prevents bias)
- [Phase 61-01]: Multi-turn simulation: initial + follow-ups + final prompt (exercises full pipeline)
- [Phase 61-01]: Cost calculation: 40% overhead for agent providers (midpoint of research 30-50%)
- [Phase 61-02]: Mann-Whitney U test with two-sided alternative (detects both improvement and degradation)
- [Phase 61-02]: Decision threshold: >20% average improvement AND 3+ significant dimensions required
- [Phase 61-02]: Cost-quality metric: improvement % / cost increase % for value comparison
- [Phase 61-02]: Statistical significance at alpha=0.05 (p < 0.05)

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

Last session: 2026-02-17
Stopped at: Phase 61 complete — experiment concluded, branch merged to master
Resume file: None
Next action: Resolve known issues with CLI adapter, then continue with v2.0 or next milestone

**Experiment Conclusion:**
- v0.1-claude-code milestone COMPLETE
- CLI adapter adopted without formal quality comparison (user decision)
- 5 CLI BRDs generated demonstrating adapter capabilities
- SDK excluded (Windows command line length limitation)
- Anthropic baseline skipped (user decided to ship as-is)
- Known issues to be resolved in future work

---

*State updated: 2026-02-17 (Phase 61 complete — CLI adopted, merged to master)*
