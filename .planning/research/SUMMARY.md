# Research Summary: Unit Testing Coverage for BA Assistant

**Project:** BA Assistant v1.9.1 - Unit Test Coverage Milestone
**Synthesized:** 2026-02-02
**Research Files:**
- STACK-TESTING.md
- FEATURES.md
- TEST_ARCHITECTURE.md
- PITFALLS_UNIT_TESTING.md

---

## Executive Summary

BA Assistant already has a solid testing foundation with pytest-asyncio (backend) and mockito/flutter_test (frontend), with approximately 22 test files across both stacks. The v1.9.1 milestone should focus on **expanding coverage systematically** rather than replacing existing patterns. Key additions include pytest-cov for coverage reporting, respx for LLM API mocking, factory-boy for test data generation, and a MockLLMAdapter infrastructure for deterministic AI behavior testing.

The recommended approach is to build test infrastructure first (fixtures, mocking utilities, coverage tooling), then expand unit test coverage for service layers and providers (the current gaps), and finally add API contract tests and component-level widget tests. The existing patterns in conftest.py and widget tests are already following best practices for async testing, database isolation, and provider mocking.

Critical risks center on LLM testing complexity (mock at adapter layer, not HTTP layer), SSE streaming test isolation (fully consume streams), and Flutter animation handling (avoid pumpAndSettle with infinite animations). These are well-documented pitfalls with clear prevention strategies that should be addressed early in the infrastructure phase.

---

## Key Findings

### From STACK-TESTING.md (Technology Stack)

**Retain (Already Working):**
| Technology | Purpose | Status |
|------------|---------|--------|
| pytest >= 8.3.0 | Test runner | Installed |
| pytest-asyncio >= 0.24.0 | Async test support | Installed |
| httpx >= 0.27.0 | AsyncClient for tests | Installed |
| flutter_test (SDK) | Widget testing | Installed |
| mockito ^5.6.3 | Mock generation | Installed |

**Add (New):**
| Technology | Purpose | Rationale |
|------------|---------|-----------|
| pytest-cov >= 4.1.0 | Coverage reporting | CI badges, coverage thresholds |
| pytest-mock >= 3.12.0 | Cleaner mocking syntax | mocker fixture, auto-cleanup |
| respx >= 0.21.0 | Mock httpx requests | LLM adapter HTTP mocking |
| factory-boy >= 3.3.0 | Test data factories | Reduce boilerplate for User/Project/Thread |
| lcov (system) | Flutter coverage HTML | Coverage visualization |

**Do NOT Add:**
- pytest-bdd (overkill for single-developer project)
- mocktail (would require rewriting existing mockito tests)
- hypothesis (defer to Phase 2)

### From FEATURES.md (Test Coverage Targets)

**Table Stakes (Must Have):**

| Backend | Frontend |
|---------|----------|
| Service layer unit tests (auth, project, thread, message, document) | Provider unit tests (Auth, Project, Conversation, Chats) |
| API endpoint request/response validation | Widget rendering across states (loading, error, empty, populated) |
| Authentication/authorization paths | Form validation |
| Error handling paths | Model serialization (fromJson/toJson) |
| LLM adapter interface compliance | Navigation behavior |

**Coverage Targets:**
| Layer | Target |
|-------|--------|
| Backend Services | 80-90% |
| Backend API Routes | 70-80% |
| Frontend Providers | 80-90% |
| Frontend Widgets | 60-70% |
| Frontend Models | 90%+ |

**Critical Gaps Identified:**
1. No isolated service unit tests (current tests are integration-level)
2. No LLM adapter unit tests
3. Only ChatsProvider has unit tests (other providers missing)
4. No frontend service-level tests (ApiService, AuthService)

### From TEST_ARCHITECTURE.md (Patterns and Structure)

**Recommended Directory Structure:**

```
backend/tests/
+-- conftest.py                # Global fixtures only
+-- fixtures/
|   +-- auth_fixtures.py       # test_user, auth_headers
|   +-- project_fixtures.py    # test_project
|   +-- llm_fixtures.py        # MockLLMAdapter
+-- unit/
|   +-- services/              # Pure function tests
|   +-- llm/                   # Adapter tests
+-- integration/               # Full request cycle
+-- api/                       # Router contract tests

frontend/test/
+-- test_helpers/
|   +-- mock_providers.dart    # Reusable mock setup
|   +-- test_widgets.dart      # Widget wrappers
+-- unit/
|   +-- providers/             # Provider logic tests
|   +-- models/                # Serialization tests
|   +-- services/              # Service tests with mock Dio
+-- widget/
|   +-- screens/               # Full screen tests
|   +-- components/            # Individual widget tests
```

**Key Patterns to Implement:**
1. **MockLLMAdapter class** - Configurable mock returning text/tool_calls/errors
2. **Composable fixtures** - Fixtures that build on each other (user -> project -> thread)
3. **TestWidgetWrapper** - Standardized widget test setup with providers
4. **SSE stream helper** - Utility for parsing SSE responses in tests

### From PITFALLS_UNIT_TESTING.md (Critical Pitfalls)

**Critical (Must Address):**

| Pitfall | Risk | Prevention | Phase |
|---------|------|------------|-------|
| Using sync TestClient in async tests | Event loop conflicts | Use httpx.AsyncClient with ASGITransport (already correct) | Phase 1 |
| Mocking LLM at HTTP layer | Brittle tests | Mock at adapter layer, not httpx directly | Phase 2 |
| SSE streams not fully consumed | Resource leaks, hanging tests | Use async context managers, explicit termination | Phase 2 |
| Database isolation with shared state | Test interference | Function-scoped fixtures (already correct) | Phase 1 |
| FTS5 table not created | Search tests fail | Include DDL in db_engine fixture (already correct) | Phase 1 |
| pumpAndSettle with infinite animations | 10-minute timeouts | Mock loading states or use pump() with duration | Phase 3 |

**Moderate (Address During Implementation):**

| Pitfall | Risk | Prevention |
|---------|------|------------|
| Testing Provider without listeners | Miss notification bugs | Verify notifyListeners() called |
| JWT time-dependent failures | Flaky CI | Use dependency overrides or long-lived tokens |
| Cross-platform plugin differences | CI failures | Wrap plugins in injectable services |

---

## Implications for Roadmap

### Recommended Phase Structure

**Phase 1: Test Infrastructure (Build First)**
- Rationale: All subsequent phases depend on proper fixtures and mocking infrastructure
- Delivers: Coverage tooling, fixture modules, MockLLMAdapter, test helpers
- Features from FEATURES.md: Coverage reporting setup, fixture organization
- Pitfalls to avoid: Database isolation (verify existing patterns), verbose logging

**Phase 2: Backend Unit Tests**
- Rationale: Backend services have zero isolated unit tests; largest coverage gap
- Delivers: Service unit tests, LLM adapter tests, encryption tests
- Features from FEATURES.md: Service layer 80-90% coverage
- Pitfalls to avoid: LLM mocking at wrong layer, SSE stream handling, JWT timing

**Phase 3: Backend API Tests**
- Rationale: API contract tests ensure HTTP layer correctness, builds on service tests
- Delivers: Router-level tests, error response validation, auth requirement verification
- Features from FEATURES.md: API endpoint request/response validation
- Pitfalls to avoid: Over-testing (don't duplicate service tests)

**Phase 4: Frontend Unit Tests**
- Rationale: Only ChatsProvider has tests; providers are core business logic
- Delivers: Provider unit tests for Auth, Project, Conversation, Document, Thread
- Features from FEATURES.md: Provider 80-90% coverage, model serialization
- Pitfalls to avoid: Missing await, notification testing, mock implementations

**Phase 5: Frontend Widget Tests**
- Rationale: Expand existing patterns to components and missing screens
- Delivers: Component tests, screen coverage expansion, error state coverage
- Features from FEATURES.md: Widget 60-70% coverage
- Pitfalls to avoid: pumpAndSettle timeouts, cross-platform differences

**Phase 6: CI/CD Integration**
- Rationale: Coverage reporting makes testing visible and enforces thresholds
- Delivers: Codecov integration, coverage badges, fail-under thresholds
- Features from FEATURES.md: Coverage reporting, CI integration
- Pitfalls to avoid: Noisy CI output, slow test runs

### Research Flags

| Phase | Research Needed? | Notes |
|-------|-----------------|-------|
| Phase 1: Infrastructure | NO | Well-documented patterns, existing codebase has examples |
| Phase 2: Backend Unit Tests | PARTIAL | LLM adapter mocking may need exploration |
| Phase 3: Backend API Tests | NO | Standard FastAPI testing patterns |
| Phase 4: Frontend Unit Tests | NO | mockito patterns well-established |
| Phase 5: Frontend Widget Tests | NO | Existing widget tests provide clear patterns |
| Phase 6: CI/CD Integration | PARTIAL | Codecov setup details may need verification |

### Dependencies

```
Phase 1 (Infrastructure)
    |
    +-- Phase 2 (Backend Unit) -- Phase 3 (Backend API)
    |
    +-- Phase 4 (Frontend Unit) -- Phase 5 (Frontend Widget)
    |
    +--------------------------------------- Phase 6 (CI/CD)
```

---

## Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| Stack recommendations | HIGH | Based on existing codebase analysis and official documentation |
| Feature coverage targets | HIGH | Industry standards verified against multiple sources |
| Architecture patterns | HIGH | Existing patterns in codebase are best practices |
| Pitfall identification | HIGH | 14 pitfalls identified with clear prevention strategies |
| Phase structure | HIGH | Clear dependencies and logical progression |
| LLM mocking approach | MEDIUM | MockLLMAdapter design proposed but not validated |
| CI integration details | MEDIUM | Codecov specifics may need adjustment during implementation |

### Gaps to Address During Planning

1. **MockLLMAdapter implementation details** - Design proposed but implementation may reveal edge cases
2. **SSE test helper utility** - Needed but not fully specified
3. **Coverage threshold tuning** - 80% is standard but may need adjustment based on current state
4. **Existing test refactoring scope** - How much to refactor vs. build new unclear
5. **Tool execution flow testing** - document_search, artifact tools need specific patterns

---

## Aggregated Sources

### Official Documentation
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [pytest-cov](https://pypi.org/project/pytest-cov/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [respx](https://lundberg.github.io/respx/)
- [factory-boy](https://factoryboy.readthedocs.io/)
- [Flutter Testing](https://docs.flutter.dev/testing/overview)
- [Mockito Dart](https://pub.dev/packages/mockito)

### Best Practices
- [pytest-mock vs unittest.mock](https://codecut.ai/pytest-mock-vs-unittest-mock-simplifying-mocking-in-python-tests/)
- [FastAPI Testing Best Practices](https://pytest-with-eric.com/pytest-advanced/pytest-fastapi-testing/)
- [Unit Testing Anti-Patterns](https://blog.codepipes.com/testing/software-testing-antipatterns.html)
- [Flutter Testing Best Practices](https://www.walturn.com/insights/best-practices-for-testing-flutter-applications)

### CI/CD
- [GitHub Actions Coverage Badge](https://medium.com/@nunocarvalhodossantos/how-i-generate-and-display-coverage-badges-in-github-for-a-fastapi-project-f71861d620bb)
- [Codecov Action](https://github.com/codecov/codecov-action)

### LLM Testing
- [Mock LLM API Calls](https://markaicode.com/mock-llm-api-calls-unit-testing/)
- [Importance of Mocking in LLM Streaming](https://medium.com/@zazaneryawan/importance-of-mocking-in-llm-streaming-through-fastapi-python-5092984915d3)

---

## Summary for Roadmapper

**Key Decisions:**
1. Retain existing stack, add pytest-cov + respx + factory-boy
2. Build infrastructure first (MockLLMAdapter is critical)
3. Backend services have largest coverage gap - prioritize
4. Frontend providers need expansion (only ChatsProvider tested)
5. Target 80% coverage for services/providers, 70% for API/widgets

**Critical Path:**
Infrastructure -> Backend Unit Tests -> Frontend Unit Tests -> CI Integration

**High-Risk Areas Requiring Attention:**
- LLM adapter mocking strategy
- SSE streaming test patterns
- Flutter animation handling in tests

**Ready for requirements definition.**

---

*Synthesized from 4 research files on 2026-02-02*
