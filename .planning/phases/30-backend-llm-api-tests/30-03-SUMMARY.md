---
phase: 30-backend-llm-api-tests
plan: 03
subsystem: backend-tests
tags: [api, contract-tests, auth, projects, fastapi, pytest]
dependency-graph:
  requires: [28-01, 30-01]
  provides: [auth-route-tests, project-route-tests]
  affects: [30-04, 30-05]
tech-stack:
  added: []
  patterns: [api-contract-testing, authenticated-client-fixture]
key-files:
  created:
    - backend/tests/api/__init__.py
    - backend/tests/api/conftest.py
    - backend/tests/api/test_auth_routes.py
    - backend/tests/api/test_project_routes.py
  modified: []
decisions:
  - decision: "Create separate authenticated_client fixture for API tests"
    rationale: "Pre-configures JWT auth headers and attaches test_user for easy access"
  - decision: "Mock OAuth2Service for auth initiate tests"
    rationale: "Avoid real OAuth calls while testing HTTP contract"
  - decision: "Use 404 for not-owned resources (not 403)"
    rationale: "Security best practice - don't leak existence of resources"
metrics:
  duration: ~3 minutes
  completed: 2026-02-02
---

# Phase 30 Plan 03: Auth & Projects API Tests Summary

API contract tests verifying HTTP status codes and response schemas for Auth and Projects routers.

## One-Liner

Contract tests for Auth OAuth flows (/me, /usage) and Projects CRUD with 37 passing tests across 2 test files.

## What Was Built

### 1. API Test Module Structure
- `backend/tests/api/__init__.py` - Module initialization
- `backend/tests/api/conftest.py` - API-specific fixtures
  - `authenticated_client` - AsyncClient with valid JWT and attached `test_user`
  - `create_auth_token` - Factory for custom user JWT tokens

### 2. Auth Router Contract Tests (15 tests)

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestGoogleOAuthInitiate | 2 | 200 returns auth_url, URL is Google domain |
| TestGoogleOAuthCallback | 2 | 400 invalid state, 422 missing code |
| TestMicrosoftOAuthInitiate | 2 | 200 returns auth_url, URL is Microsoft domain |
| TestMicrosoftOAuthCallback | 2 | 400 invalid state, 422 missing code |
| TestLogout | 1 | 200 returns success message |
| TestGetMe | 3 | 200 with token, 403 without, schema fields |
| TestGetUsage | 3 | 200 with token, 403 without, usage fields |

### 3. Projects Router Contract Tests (22 tests)

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestCreateProject | 5 | 201 success, 403 no auth, 422 validation, schema |
| TestListProjects | 4 | 200 array, 403 no auth, empty list, ownership isolation |
| TestGetProject | 4 | 200 with details, 403/404 error cases |
| TestUpdateProject | 5 | 200 updates, 403/404 error cases |
| TestDeleteProject | 4 | 204 success, 403/404 error cases |

## Verification Results

```
pytest tests/api/test_auth_routes.py tests/api/test_project_routes.py -v
======================= 37 passed in 1.76s =======================
```

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Separate `authenticated_client` fixture | Cleaner than passing auth headers manually, attaches user for easy access |
| Mock OAuth2Service at route level | Tests HTTP contract without hitting real OAuth providers |
| Return 404 for non-owned resources | Security best practice (don't leak resource existence) |
| Class-based test organization | Groups related tests (TestCreateProject, TestListProjects, etc.) |

## Files Modified

### Created (4 files, 584 lines)
- `backend/tests/api/__init__.py` (1 line)
- `backend/tests/api/conftest.py` (57 lines)
- `backend/tests/api/test_auth_routes.py` (233 lines)
- `backend/tests/api/test_project_routes.py` (351 lines)

## Deviations from Plan

None - plan executed exactly as written.

## Test Count Impact

| Before | After | Delta |
|--------|-------|-------|
| 97 backend tests | 134 backend tests | +37 |

## Requirements Addressed

- **BAPI-01**: Auth router contract tests (all endpoints)
- **BAPI-02**: Projects router contract tests (CRUD operations)

## Next Phase Readiness

**Unblocked:**
- Plan 30-04: Documents & Threads API Tests (same pattern)
- Plan 30-05: Chat & Messages API Tests (same pattern)

**No blockers identified.**
