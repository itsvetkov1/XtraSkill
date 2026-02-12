# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-12)

**Core value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

**Current focus:** v2.1 — Rich Document Support (defining requirements)

## Current Position

Milestone: v2.1 Rich Document Support
Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-02-12 — Milestone v2.1 started

Progress:
```
v1.0-v1.9.5: [##########] 48 phases, 114 plans, 11 milestones SHIPPED

v2.0:        [#         ] 1/5 phases (49-01 complete, paused for v2.1)
v2.1:        [          ] 0/TBD phases (defining requirements)
```

## Performance Metrics

**Velocity:**
- Total plans completed: 115 (across 11 milestones)
- Average duration: ~1-18 minutes per plan

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
| Security v2.0 | 49-53 | 1/TBD | In progress |

**Total:** 115 plans shipped across 48 phases

## Accumulated Context

### Decisions

Recent key decisions (full archive in MILESTONES.md):
- v2.0: Railway (backend) + Cloudflare Pages (frontend) for PaaS deployment
- v2.0: secure.py for security headers middleware (zero dependencies)
- v2.0: bandit + pip-audit for security scanning (Python-native, free)
- v2.0: Cloudflare DNS for CNAME flattening at apex domain
- Phase 49-01: Environment-aware SQL echo (disabled in production) to prevent log flooding

### Pending Todos

- [ ] Configure CODECOV_TOKEN secret in GitHub repository
- [ ] Link repository to Codecov dashboard

### Blockers/Concerns

**No current blockers**

## Session Continuity

Last session: 2026-02-12
Stopped at: Started v2.1 Rich Document Support milestone
Resume file: None
Next action: Define requirements for v2.1

**Context for Next Session:**
- v2.0 paused at phase 49-02 (Railway deployment checkpoint — env vars pending)
- v2.1 milestone: Excel, CSV, PDF, Word parsing with AI context, preview, and export
- Bug fixes shipped: FTS5 auto-creation, invalid FTS5 query handling, PDF export (WeasyPrint)
- Key constraint: Text-Only Documents constraint being removed in v2.1

---

*State updated: 2026-02-12 (v2.1 milestone started)*
