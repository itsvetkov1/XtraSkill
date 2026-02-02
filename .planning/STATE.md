# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-02)

**Core value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

**Current focus:** v1.9.1 Unit Test Coverage milestone

## Current Position

Milestone: v1.9.1 Unit Test Coverage
Phase: 32 of 33 (Frontend Widget & Model Tests)
Plan: All 5 plans complete (including gap closure)
Status: Phase 32 verified complete, ready for Phase 33
Last activity: 2026-02-02 - Completed 32-05-PLAN.md (gap closure: DocumentListScreen/LoginScreen fixes)
Next action: Execute Phase 33

Progress: [==========================----] 5/6 phases complete - 23/24 plans total in v1.9.1

## Performance Metrics

**Velocity:**
- Total plans completed: 84 (20 in MVP v1.0, 15 in Beta v1.5, 5 in UX v1.6, 8 in URL v1.7, 8 in LLM v1.8, 9 in UX v1.9, 19 in Unit Tests v1.9.1)
- Average duration: ~18 minutes (MVP v1.0), ~7 minutes (Beta v1.5), ~5 minutes (UX v1.6), ~4 minutes (URL v1.7), ~5 minutes (LLM v1.8), ~4 minutes (UX v1.9), ~4 minutes (Unit Tests v1.9.1)

**By Milestone:**

| Milestone | Phases | Plans | Status |
|-----------|--------|-------|--------|
| MVP v1.0 | 1-5 (includes 4.1) | 20/20 | SHIPPED 2026-01-28 |
| Beta v1.5 | 6-10 | 15/15 | SHIPPED 2026-01-30 |
| UX v1.6 | 11-14 | 5/5 | SHIPPED 2026-01-30 |
| URL v1.7 | 15-18 | 8/8 | SHIPPED 2026-01-31 |
| LLM v1.8 | 19-22 | 8/8 | SHIPPED 2026-01-31 |
| UX v1.9 | 23-27 | 9/9 | SHIPPED 2026-02-02 |
| Unit Tests v1.9.1 | 28-33 | 23/24 | In Progress |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Previous milestone decisions archived in:
- .planning/milestones/v1.5-ROADMAP.md
- .planning/milestones/v1.6-ROADMAP.md
- .planning/milestones/v1.7-ROADMAP.md
- .planning/milestones/v1.8-ROADMAP.md
- .planning/milestones/v1.9-ROADMAP.md

### v1.9.1 Milestone Notes

- 43 requirements across 6 phases
- Quick depth: phases combine related requirements
- Phase 30 is largest (12 requirements: BLLM + BAPI combined)
- Infrastructure-first approach (Phase 28 unblocks all others)
- Research identified MockLLMAdapter and SSE streaming as key patterns

### Phase 28 Decisions

| Decision | Rationale |
|----------|-----------|
| pytest_plugins for fixture discovery | Proper pytest handling of fixture registration |
| MockLLMAdapter with call_history | Enable assertions on LLM inputs, not just outputs |
| Keep skill fixtures in conftest | Low-use fixtures stay in legacy location |
| Factory-boy with @register decorator | Auto-creates pytest fixtures for all models |

### Phase 29 Decisions

| Decision | Rationale |
|----------|-----------|
| Class-based test organization | Groups related tests logically (TestXxx classes) |
| Use db_session fixture for all DB tests | Consistent with Phase 28 infrastructure |
| Test token_tracking with explicit cost assertions | Verify pricing calculations for Claude 4.5 Sonnet |
| Mock at AsyncOAuth2Client level | Cleaner than HTTP-level mocking for OAuth tests |
| Skip heartbeat timing tests | 1s asyncio.sleep makes sub-second testing impossible |
| AIService.__new__ for mock injection | Clean dependency injection for adapter |

### Phase 30 Decisions

| Decision | Rationale |
|----------|-----------|
| Separate authenticated_client fixture | Pre-configures JWT auth and attaches test_user |
| Mock OAuth2Service at route level | Test HTTP contract without real OAuth calls |
| Return 404 for non-owned resources | Security best practice (don't leak existence) |
| Create api/ subdirectory for route tests | Separates route contract tests from integration tests |
| Group tests by endpoint class | Clear mapping (TestUploadDocument, TestGetThread, etc.) |
| Skip stream iteration tests | Verify SSE headers instead of iterating - httpx lifecycle issues with mocked async generators |

### Pending Todos

- Manual testing of remaining v1.7-v1.9 features (see TESTING-QUEUE.md)

### Blockers/Concerns

**No current blockers**

**Note:** Pre-existing test failure in test_cascade_delete_project (thread cascade) - not related to Phase 28-30 work.

### Phase 31 Decisions

| Decision | Rationale |
|----------|-----------|
| Skip deleteProject timer testing (31-01) | 10s timer impractical; requires BuildContext for SnackBar |
| Future.delayed for microtask completion (31-01) | AuthProvider uses Future.microtask() for Flutter Web compatibility |
| Capture onSendProgress callback for testing (31-02) | Allows simulating progress updates and asserting mid-upload state |
| Test filteredThreads getter with all sort options (31-02) | Getter encapsulates complex filtering/sorting logic |
| Skip timer-based delete testing (31-02) | Requires BuildContext and Timer - difficult to mock in unit tests |
| Stream event mocking with async* generators (31-03) | Mock AIService.streamChat to return Stream.fromIterable with event sequence |
| Listener notification testing via addListener (31-03) | Count notifyListeners calls with callback counter |
| FPROV-06 test groups separate from original (31-03) | Clear distinction between original and expanded tests |
| No mocks for DocumentColumnProvider (31-04) | Pure state management with no external dependencies |
| Test graceful degradation explicitly (31-04) | Verify UI continues working when SharedPreferences fails |
| Conditional notification testing (31-04) | expand()/collapse() skip notification when state unchanged |
| Test JWT validation with actual base64 encoding (31-05) | Verify real token parsing logic, not just mock returns |
| Skip launchUrl testing in OAuth methods (31-05) | url_launcher not available in test environment; test initiate endpoint only |
| Use createTestJwt helper for JWT tests (31-05) | Consistent test token generation with real base64 encoding |
| SSE streaming limitation documented (31-06) | flutter_client_sse cannot be mocked; test ChatEvent types separately |
| Options capture pattern for auth (31-06) | Verify auth headers in mocked Dio calls |

### Phase 32 Decisions

| Decision | Rationale |
|----------|-----------|
| Test ISO 8601 datetime parsing variants (32-01) | DateTime parsing handles both with/without timezone suffix |
| Test empty string vs null for content (32-01) | Document content can be empty string (valid) vs null (not loaded) |
| Test empty arrays vs null for collections (32-01) | Project documents/threads can be [] (loaded, none) vs null (not loaded) |
| Test Thread.hasProject edge cases (32-02) | Computed property has empty string check beyond null |
| Test TokenUsage costPercentage clamping (32-02) | Verify 0.0-1.0 range enforcement per model implementation |
| Comprehensive PaginatedThreads tests (32-02) | Nested Thread array with pagination fields needs validation |
| findsWidgets for Consumer rebuild duplicates (32-04) | SettingsScreen Consumer widgets may render multiple times during test |
| pump-with-duration for async dialogs (32-04) | SettingsScreen has async usage loading that never settles |
| Skip confirm logout test (32-04) | Logout triggers GoRouter redirect requiring full router setup |
| scrollUntilVisible for off-screen buttons (32-04) | Logout button may be off-screen in Actions section |
| Conditional export for dart:html (32-05) | UrlStorageService uses dart:html which fails in flutter test |
| Stub implementation pattern (32-05) | No-op stub provides test-compatible API for web-only services |
| textContaining for date assertions (32-05) | DateFormatter.format() returns variable relative text |

## Session Continuity

Last session: 2026-02-02
Stopped at: Completed 32-05-PLAN.md (gap closure)
Resume file: None
Next action: Execute Phase 33

---

*State updated: 2026-02-02 (32-05 complete - gap closure, 103 widget tests passing)*
