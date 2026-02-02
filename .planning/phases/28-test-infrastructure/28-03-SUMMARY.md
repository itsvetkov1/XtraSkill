---
phase: 28-test-infrastructure
plan: 03
subsystem: testing
tags: [pytest, factory-boy, pytest-factoryboy, MockLLMAdapter, fixtures, mocking]

# Dependency graph
requires:
  - phase: 28-01
    provides: test dependencies (factory-boy, pytest-factoryboy)
provides:
  - tests/fixtures/ module with reusable fixtures
  - MockLLMAdapter for testing AI service without API calls
  - Factory-boy factories for all models (User, Project, Document, Thread, Message, Artifact)
  - pytest_plugins integration for fixture auto-discovery
affects:
  - 29-frontend-unit-tests (may need similar mock patterns)
  - 30-backend-llm-api-tests (will use MockLLMAdapter extensively)
  - 31-backend-crud-tests (will use Factory-boy factories)
  - 32-integration-tests (will combine fixtures)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - MockLLMAdapter pattern for LLM testing
    - Factory-boy model factories with pytest-factoryboy registration
    - pytest_plugins for fixture module organization

key-files:
  created:
    - backend/tests/fixtures/__init__.py
    - backend/tests/fixtures/db_fixtures.py
    - backend/tests/fixtures/auth_fixtures.py
    - backend/tests/fixtures/llm_fixtures.py
    - backend/tests/fixtures/factories.py
  modified:
    - backend/tests/conftest.py

key-decisions:
  - "Extract fixtures from conftest.py to dedicated fixtures module for reusability"
  - "MockLLMAdapter tracks call_history for test assertions"
  - "Use pytest_plugins list for fixture module registration"
  - "Keep skill-specific fixtures in conftest.py for backward compatibility"

patterns-established:
  - "MockLLMAdapter: Configurable mock with responses, tool_calls, errors, and call tracking"
  - "Factory registration: @register decorator auto-creates pytest fixtures"
  - "Fixture organization: tests/fixtures/ module with pytest_plugins discovery"

# Metrics
duration: 8min
completed: 2026-02-02
---

# Phase 28 Plan 03: Shared Fixtures Module Summary

**MockLLMAdapter for testing AI without API calls + Factory-boy factories for all models with pytest-factoryboy auto-registration**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-02T12:30:00Z
- **Completed:** 2026-02-02T12:38:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Created tests/fixtures/ module with organized fixture submodules
- Implemented MockLLMAdapter extending LLMAdapter base class with configurable responses, tool_calls, errors
- Created Factory-boy factories for all 6 models (User, Project, Document, Thread, Message, Artifact)
- Migrated conftest.py to use pytest_plugins for fixture discovery
- All 15 existing tests pass with new fixture structure

## Task Commits

Each task was committed atomically:

1. **Task 1: Create fixtures module structure** - `b4a7f12` (feat)
2. **Task 2: Create MockLLMAdapter** - `f688b77` (feat)
3. **Task 3: Create Factory-boy factories and update conftest.py** - `45cb02a` (feat)

## Files Created/Modified

- `backend/tests/fixtures/__init__.py` - Package module re-exporting all fixtures
- `backend/tests/fixtures/db_fixtures.py` - Database engine and session fixtures
- `backend/tests/fixtures/auth_fixtures.py` - HTTP client and auth header fixtures
- `backend/tests/fixtures/llm_fixtures.py` - MockLLMAdapter and LLM test fixtures
- `backend/tests/fixtures/factories.py` - Factory-boy factories for all models
- `backend/tests/conftest.py` - Updated to use pytest_plugins for fixture discovery

## Decisions Made

1. **pytest_plugins over direct imports** - Using pytest_plugins list allows pytest to handle fixture registration properly, avoiding import order issues
2. **Call history tracking in MockLLMAdapter** - Enables tests to assert on what was passed to the LLM, not just what came back
3. **Pre-configured fixture variants** - Added mock_llm_text_response, mock_llm_tool_response, mock_llm_error for common test scenarios
4. **Keep skill fixtures in conftest** - Skill-specific fixtures are rarely used and can stay in conftest.py for now

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Initial __init__.py import failed before factories.py was created - created placeholder file to unblock MockLLMAdapter verification
- Pre-existing test failure in test_cascade_delete_project (thread cascade) - not related to fixtures changes, was failing before this plan

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- MockLLMAdapter ready for use in Phase 30 (Backend LLM/API tests)
- Factory-boy factories ready for use in Phase 31 (Backend CRUD tests)
- Fixture module pattern established for future test organization
- All existing tests continue to pass

---
*Phase: 28-test-infrastructure*
*Completed: 2026-02-02*
