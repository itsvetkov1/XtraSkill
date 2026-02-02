# Phase 33: CI Integration - Context

**Gathered:** 2026-02-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Configure CI pipeline to track test coverage, enforce quality gates, and display coverage metrics. Tests already exist from Phases 28-32. This phase wires them into automated CI with visibility and enforcement.

</domain>

<decisions>
## Implementation Decisions

### CI Platform & Triggers
- GitHub Actions (already hosting on GitHub)
- Manual trigger via "/test" keyword in PR comment OR commit message
- Weekly scheduled run on Monday morning
- Remove existing push/commit trigger (no automatic runs on every push)

### Coverage Thresholds
- Separate thresholds for backend/frontend (Claude determines appropriate values based on current coverage)
- Warn only when coverage drops below threshold (don't fail the build)
- Track coverage history and trends over time via Codecov

### Badge & Visibility
- Codecov for badge generation and history tracking
- Single coverage badge (no build status badge)
- Badge placement: top of README, right after project title

### Failure Behavior
- Test failures: run all tests, report failures at end, mark build as failed
- Branch protection on master requiring CI to pass before merge
- Admin bypass available for emergency merges

### Claude's Discretion
- Exact threshold percentages (based on analyzing current coverage levels)
- Workflow file organization (single vs multiple workflow files)
- Codecov configuration details
- Monday morning timezone (project timezone or UTC)

</decisions>

<specifics>
## Specific Ideas

- User wants "/test" to work in both PR comments and commit messages
- Weekly run should catch flaky tests and regressions from direct pushes
- Coverage drops should warn but not block - informational enforcement
- Test failures should always fail the build (zero tolerance for broken tests)

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 33-ci-integration*
*Context gathered: 2026-02-02*
