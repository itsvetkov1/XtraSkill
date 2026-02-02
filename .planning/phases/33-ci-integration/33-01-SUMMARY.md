---
phase: 33-ci-integration
plan: 01
subsystem: devops
tags: [github-actions, codecov, ci-cd, coverage-tracking]

dependency_graph:
  requires:
    - 32-05-PLAN (all tests passing for CI)
    - 28-01-PLAN (pytest-cov infrastructure)
  provides:
    - CI workflow with coverage generation
    - Codecov integration with backend/frontend flags
    - Coverage badge in README
  affects:
    - Future development (coverage tracked automatically)

tech_stack:
  added:
    - codecov/codecov-action@v5
  patterns:
    - Manual/scheduled CI triggers
    - Codecov flags for monorepo coverage
    - Informational coverage thresholds

key_files:
  created:
    - codecov.yml
    - README.md
  modified:
    - .github/workflows/flutter-ci.yml

decisions:
  - id: D-33-01-01
    decision: Replace push/PR triggers with manual/scheduled/dispatch
    rationale: User wants control over when CI runs; scheduled for weekly health checks
  - id: D-33-01-02
    decision: Use informational: true for all coverage thresholds
    rationale: Coverage drops should warn but not block PRs
  - id: D-33-01-03
    decision: Set backend target 60%, frontend target 50%
    rationale: Backend currently ~67%; frontend baseline conservative start
  - id: D-33-01-04
    decision: No slash-command-dispatch workflow
    rationale: Requires PAT with repo scope; defer complexity to user request

metrics:
  duration: ~4 minutes
  completed: 2026-02-02
---

# Phase 33 Plan 01: CI Coverage Integration Summary

Configured GitHub Actions CI pipeline for coverage tracking with Codecov integration.

## One-liner

GitHub Actions CI with pytest/flutter coverage generation, Codecov upload with backend/frontend flags, and README badge.

## Tasks Completed

| Task | Name | Commit | Result |
|------|------|--------|--------|
| 1 | Modify CI workflow for coverage and Codecov | bf19a75 | 8 coverage-related patterns in workflow |
| 2 | Create Codecov configuration | ce9d9e7 | 10 flag/informational settings |
| 3 | Create README with coverage badge | 5caa14a | Badge URL verified |

## Changes Made

### .github/workflows/flutter-ci.yml (Modified)

**Triggers changed:**
- Removed: push to develop, all PR triggers
- Added: `workflow_dispatch` (manual), `schedule` (Monday 9 AM UTC), `repository_dispatch`
- Kept: push to main/master with `/test` commit message check

**Backend job changes:**
- Run ALL tests: `pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing -v`
- Added `TESTING=true` environment variable
- Added Codecov upload step with `backend` flag

**Frontend job changes:**
- Changed from separate widget/integration runs to: `flutter test --coverage`
- Added Codecov upload step with `frontend` flag

**Build job:**
- Added same trigger condition as test jobs

### codecov.yml (Created)

Configuration highlights:
- `informational: true` on all status checks (warn-only)
- Backend target: 60% (flags: backend, paths: app/)
- Frontend target: 50% (flags: frontend, paths: lib/)
- `carryforward: true` for partial CI runs
- PR comment layout: reach, diff, flags, files

### README.md (Created)

Root-level README with:
- Codecov coverage badge (auto-updates after CI runs)
- Project overview
- Quick start instructions for backend and frontend
- Testing commands with coverage options

## Verification Results

| Check | Result |
|-------|--------|
| YAML syntax (flutter-ci.yml) | Valid |
| YAML syntax (codecov.yml) | Valid |
| Workflow triggers | workflow_dispatch, schedule, repository_dispatch, push |
| Coverage commands | pytest --cov, flutter test --coverage |
| Codecov uploads | 2 (backend + frontend) |
| README badge | codecov.io URL present |

## Requirements Coverage

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| CI-01: Coverage reporting | pytest --cov, flutter --coverage, Codecov uploads | COMPLETE |
| CI-02: All tests pass gate | CI fails on non-zero exit from pytest/flutter test | COMPLETE |
| CI-03: Coverage threshold | codecov.yml with informational: true thresholds | COMPLETE |
| CI-04: Coverage badges | README.md with Codecov badge | COMPLETE |

## Deviations from Plan

None - plan executed exactly as written.

## Manual Steps Required

After this plan is pushed, user must:

1. **Add CODECOV_TOKEN secret to GitHub:**
   - Go to GitHub repo -> Settings -> Secrets and variables -> Actions
   - Add new repository secret: `CODECOV_TOKEN`
   - Get token from: Codecov Dashboard -> Settings -> General -> Repository Upload Token

2. **Link repository to Codecov:**
   - Visit https://app.codecov.io/gh
   - Add new repository -> Select itsvetkov1/XtraSkill

3. **Test workflow:**
   - Go to Actions tab -> Flutter CI/CD -> Run workflow
   - Or commit with `/test` in message

4. **Verify badge displays:**
   - Badge will show "unknown" until first successful upload
   - After upload, badge auto-updates with coverage percentage

## Success Criteria Status

| Criterion | Status |
|-----------|--------|
| CI workflow has manual dispatch trigger | PASS |
| CI workflow has scheduled trigger (Monday 9 AM UTC) | PASS |
| CI workflow has repository dispatch trigger | PASS |
| Push trigger with /test commit message check | PASS |
| Backend tests run ALL tests with --cov flags | PASS |
| Frontend tests run with --coverage flag | PASS |
| Codecov upload steps with backend/frontend flags | PASS |
| codecov.yml with informational: true | PASS |
| README.md with Codecov badge | PASS |

## Phase 33 Complete

This is the only plan in Phase 33. All 4 CI integration requirements are complete.

**v1.9.1 Unit Test Coverage Milestone Complete:**
- Phase 28: Test infrastructure (3 plans)
- Phase 29: Backend service tests (4 plans)
- Phase 30: Backend LLM/API tests (5 plans)
- Phase 31: Frontend provider/service tests (6 plans)
- Phase 32: Frontend widget/model tests (5 plans)
- Phase 33: CI integration (1 plan)

Total: 24 plans, 471 backend tests, 627 frontend tests, CI pipeline with coverage tracking.
