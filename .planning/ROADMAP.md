# Roadmap: BA Assistant v1.9.1

**Milestone:** Unit Test Coverage
**Created:** 2026-02-02
**Depth:** Quick
**Phases:** 6 (28-33)

---

## Overview

This milestone establishes comprehensive unit test coverage across backend services, LLM adapters, API routes, frontend providers, widgets, and models. Infrastructure comes first (fixtures, mocking utilities, coverage tooling), then systematic test expansion follows a backend-then-frontend progression, concluding with CI integration for coverage enforcement and visibility.

---

## Phase 28: Test Infrastructure

**Goal:** Development environment has all testing utilities needed for subsequent phases

**Dependencies:** None (foundation phase)

**Plans:** 3 plans

Plans:
- [ ] 28-01-PLAN.md — Backend pytest-cov and dependencies
- [ ] 28-02-PLAN.md — Flutter lcov coverage setup
- [ ] 28-03-PLAN.md — Fixtures module, MockLLMAdapter, Factory-boy

**Requirements:**
- INFRA-01: pytest-cov installed and configured for coverage reporting
- INFRA-02: Shared fixtures module created (`tests/fixtures/`)
- INFRA-03: MockLLMAdapter implemented for adapter-layer testing
- INFRA-04: Factory-boy test data factories for User, Project, Document, Thread, Message
- INFRA-05: Flutter lcov configured for HTML coverage reports

**Success Criteria:**
1. Running `pytest --cov=app --cov-report=html` generates coverage report in htmlcov/
2. Test files can import shared fixtures from `tests/fixtures/` module
3. MockLLMAdapter can be instantiated and returns configurable responses (text, tool_calls, errors)
4. Factory-boy factories create valid database objects with single calls (e.g., `UserFactory()`)
5. Running `flutter test --coverage && genhtml coverage/lcov.info` produces HTML report

---

## Phase 29: Backend Service Tests

**Goal:** All backend service modules have isolated unit test coverage

**Dependencies:** Phase 28 (requires fixtures and MockLLMAdapter)

**Requirements:**
- BSVC-01: auth_service has unit test coverage
- BSVC-02: project_service has unit test coverage
- BSVC-03: document_service has unit test coverage
- BSVC-04: thread_service has unit test coverage
- BSVC-05: message_service has unit test coverage
- BSVC-06: ai_service has unit test coverage

**Success Criteria:**
1. Each service module in `app/services/` has corresponding test file in `tests/unit/services/`
2. Service tests achieve 80%+ line coverage for their target module
3. All service tests pass with `pytest tests/unit/services/ -v`
4. Tests use factory fixtures (not raw SQL or manual object creation)
5. ai_service tests use MockLLMAdapter (no real API calls)

---

## Phase 30: Backend LLM & API Tests

**Goal:** LLM adapters have compliance tests and all API routes have contract tests

**Dependencies:** Phase 28 (requires MockLLMAdapter, SSE helper), Phase 29 (service tests validate underlying logic)

**Requirements:**
- BLLM-01: AnthropicAdapter has unit test coverage
- BLLM-02: GeminiAdapter has unit test coverage
- BLLM-03: DeepSeekAdapter has unit test coverage
- BLLM-04: SSE streaming test helper implemented
- BLLM-05: Document search (FTS5) has unit test coverage
- BAPI-01: Auth router has contract tests
- BAPI-02: Projects router has contract tests
- BAPI-03: Documents router has contract tests
- BAPI-04: Threads router has contract tests
- BAPI-05: Messages router has contract tests
- BAPI-06: Chat router has contract tests
- BAPI-07: Error response consistency verified

**Success Criteria:**
1. Each LLM adapter in `app/llm/` has corresponding test file with mocked HTTP responses
2. SSE streaming tests can parse server-sent events and verify chunk sequences
3. FTS5 search tests verify ranking, highlighting, and empty-result handling
4. Each router in `app/routers/` has contract tests verifying request/response schemas
5. All API tests pass with `pytest tests/api/ -v`
6. Error responses follow consistent format (tested by BAPI-07)

---

## Phase 31: Frontend Provider & Service Tests

**Goal:** All frontend providers and services have isolated unit test coverage

**Dependencies:** Phase 28 (requires Flutter lcov setup)

**Requirements:**
- FPROV-01: AuthProvider has unit test coverage
- FPROV-02: ProjectsProvider has unit test coverage
- FPROV-03: DocumentsProvider has unit test coverage
- FPROV-04: ThreadsProvider has unit test coverage
- FPROV-05: MessagesProvider has unit test coverage
- FPROV-06: ChatsProvider has complete unit test coverage (expand existing)
- FPROV-07: ThemeProvider has unit test coverage
- FPROV-08: SettingsProvider has unit test coverage
- FSVC-01: ApiService has unit test coverage
- FSVC-02: AuthService has unit test coverage

**Success Criteria:**
1. Each provider in `lib/providers/` has corresponding test file in `test/unit/providers/`
2. Each service in `lib/services/` has corresponding test file in `test/unit/services/`
3. Provider tests verify state changes AND notifyListeners() calls
4. Service tests mock HTTP layer (Dio) and verify request construction
5. All provider/service tests pass with `flutter test test/unit/`

---

## Phase 32: Frontend Widget & Model Tests

**Goal:** Key widgets have component tests and models have serialization coverage

**Dependencies:** Phase 31 (provider tests validate underlying state management)

**Requirements:**
- FWID-01: ChatInput widget has unit test coverage
- FWID-02: MessageBubble widget has unit test coverage
- FWID-03: ThreadList widget has unit test coverage
- FWID-04: DocumentList widget has unit test coverage
- FWID-05: All screens have test coverage
- FMOD-01: Model JSON serialization round-trip tests

**Success Criteria:**
1. ChatInput tests verify text entry, send button states, and submission callbacks
2. MessageBubble tests verify user vs assistant styling and copy functionality
3. ThreadList and DocumentList tests verify item rendering and selection callbacks
4. All screens have at least smoke tests (render without error in loading/empty/populated states)
5. Model fromJson/toJson round-trip tests pass for all models in `lib/models/`

---

## Phase 33: CI Integration

**Goal:** Coverage is tracked, enforced, and visible in CI pipeline

**Dependencies:** Phases 29-32 (tests must exist before CI can run them)

**Requirements:**
- CI-01: Coverage reporting enabled in CI pipeline
- CI-02: All tests pass gate enforced
- CI-03: Coverage threshold enforcement (fail-under)
- CI-04: Coverage badges added to README

**Success Criteria:**
1. CI workflow runs `pytest --cov` and `flutter test --coverage` on every push
2. CI fails if any test fails (zero tolerance gate)
3. CI fails if coverage drops below threshold (configurable, start at 70%)
4. README displays coverage badges that update automatically

---

## Progress

| Phase | Name | Requirements | Plans | Status |
|-------|------|--------------|-------|--------|
| 28 | Test Infrastructure | 5 | 3 | Planned |
| 29 | Backend Service Tests | 6 | - | Pending |
| 30 | Backend LLM & API Tests | 12 | - | Pending |
| 31 | Frontend Provider & Service Tests | 10 | - | Pending |
| 32 | Frontend Widget & Model Tests | 6 | - | Pending |
| 33 | CI Integration | 4 | - | Pending |

**Total Requirements:** 43
**Mapped:** 43/43

---

## Dependency Graph

```
Phase 28 (Infrastructure)
    |
    +-- Phase 29 (Backend Services)
    |       |
    |       +-- Phase 30 (Backend LLM & API)
    |
    +-- Phase 31 (Frontend Providers & Services)
    |       |
    |       +-- Phase 32 (Frontend Widgets & Models)
    |
    +-- Phases 29-32 all feed into Phase 33 (CI Integration)
```

---

*Roadmap created: 2026-02-02*
*Depth: Quick (6 phases for 43 requirements)*
*Phase 28 planned: 2026-02-02 (3 plans in 2 waves)*
