# Feature Landscape: Unit Testing Coverage Patterns

**Domain:** Comprehensive unit testing for FastAPI + Flutter application
**Researched:** 2026-02-02
**Confidence:** HIGH (verified with official docs and established patterns)

---

## Executive Summary

Unit testing for a FastAPI + Flutter application follows well-established patterns. This research identifies what MUST be tested (table stakes), what DIFFERENTIATES high-quality test suites, and common ANTI-PATTERNS to avoid. The BA Assistant project has a foundation of ~22 test files but gaps in service layer unit tests and LLM adapter coverage.

---

## Table Stakes (Must Test)

Features users (developers, CI/CD) expect. Missing = code quality feels incomplete.

### Backend (FastAPI/Python)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Service layer business logic | Core application behavior validation | Medium | auth_service, project_service, thread_service, message_service, document_service |
| API endpoint request/response | Contract validation with clients | Low | Input validation, status codes, response shapes |
| Authentication/authorization | Security-critical functionality | Medium | Token validation, user isolation, permission checks |
| Error handling paths | Graceful degradation assurance | Low | Exception handling, error responses, edge cases |
| Database operations (via service layer) | Data integrity | Medium | CRUD operations, cascade deletes, constraints |
| Model validation | Data contract enforcement | Low | Pydantic model serialization/deserialization |
| LLM adapter interface compliance | Multi-provider contract | Medium | StreamChunk generation, error handling, format conversion |

### Frontend (Flutter/Dart)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Provider state management | Business logic correctness | Medium | All *Provider classes - state transitions, error handling |
| Widget rendering states | UI correctness across states | Low | Loading, error, empty, populated states |
| Form validation | User input handling | Low | Login, project creation, message input |
| Error display/recovery | UX completeness | Low | Error banners, retry buttons, snackbars |
| Navigation behavior | App flow correctness | Medium | Route guards, deep links, back navigation |
| Model serialization | API contract compliance | Low | fromJson/toJson round-trips |

### Coverage Targets

| Layer | Recommended Coverage | Rationale |
|-------|---------------------|-----------|
| Backend Services | 80-90% | Core business logic, most critical |
| Backend API Routes | 70-80% | Integration testing covers much |
| Frontend Providers | 80-90% | Business logic separation |
| Frontend Widgets | 60-70% | Widget tests are comprehensive |
| Frontend Services | 70-80% | API communication layer |
| Frontend Models | 90%+ | Simple, high-value tests |

---

## Differentiators (Good to Test)

Features that set testing quality apart. Not expected but valued.

### Backend Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| LLM streaming mock tests | Deterministic AI behavior testing | High | Mock streaming responses for predictable tests |
| Tool execution flow | Validate agent behavior | High | document_search, artifact tools |
| Concurrent request handling | Race condition prevention | Medium | Parallel thread creation, message sending |
| Token tracking accuracy | Budget enforcement reliability | Medium | Input/output token counting |
| Document encryption/decryption | Security verification | Medium | Round-trip encryption tests |
| System prompt generation | Skill-based behavior | Medium | Context assembly, document injection |

### Frontend Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Streaming message display | Real-time UX correctness | High | Text accumulation, cursor position |
| Optimistic UI updates | Responsive UX testing | Medium | Pre-emptive state changes |
| Pagination behavior | Large data handling | Medium | Load more, infinite scroll |
| Theme switching persistence | Settings reliability | Low | Immediate apply, persist across sessions |
| Responsive layout breakpoints | Multi-device support | Medium | Mobile, tablet, desktop layouts |
| Copy/export functionality | User utility features | Low | Clipboard operations, formatting |

### Advanced Patterns

| Pattern | Value | When to Implement |
|---------|-------|-------------------|
| Snapshot testing | UI regression detection | After visual design stabilizes |
| Golden file tests | Rendering consistency | For complex widgets |
| Contract testing | API version compatibility | Before major releases |
| Mutation testing | Test quality verification | For critical paths |

---

## Anti-Features (Things NOT to Unit Test)

Features to explicitly NOT unit test. Common mistakes in this domain.

### Do NOT Unit Test

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Private methods directly** | Implementation detail coupling, tests break on refactoring | Test through public interfaces |
| **Framework code** | Already tested by Flutter/FastAPI maintainers | Trust framework, test your usage |
| **Simple getters/setters** | No logic = no value, inflates coverage artificially | Only test if they have side effects |
| **Constructor-only classes** | No behavior to verify | Test classes that use them |
| **Database connection setup** | Infrastructure concern, not unit behavior | Integration tests or manual verification |
| **External API responses** | Real APIs are flaky, slow, costly | Mock external services |
| **Exact error message text** | Brittle, changes frequently | Test error type/category instead |
| **UI pixel positions** | Fragile, varies by platform | Test presence and interaction, not position |
| **Configuration files** | Static data, no logic | Validate schema, not content |
| **Third-party library internals** | Out of your control | Test wrapper functions you create |

### Patterns That Indicate Over-Testing

| Anti-Pattern Name | Description | Fix |
|-------------------|-------------|-----|
| **Mockery** | So many mocks that you're testing mock behavior, not real code | Reduce mock count, use fakes for complex deps |
| **Inspector** | Test knows too much about implementation, breaks on any refactor | Test behavior, not implementation |
| **Test-per-Method** | One test per production method regardless of behavior | Test behaviors, some methods need multiple tests |
| **100% Coverage Theater** | Adding tests just to hit coverage numbers | Focus on behavior coverage, not line coverage |
| **Nitpicker** | Comparing full output when only parts matter | Assert specific fields that matter |

### Testing Pyramid Violations

| Violation | Symptom | Correction |
|-----------|---------|------------|
| Ice Cream Cone | Most tests are E2E/integration | Add unit tests for business logic |
| Hourglass | Middle layer under-tested | Add service layer unit tests |
| Inverted Pyramid | Too few integration tests | Keep unit tests but add integration tests |

---

## Feature Dependencies

```
Backend Testing Dependencies:
  conftest.py (fixtures)
    -> test_*.py (individual tests)
    -> Mocked services
    -> Test database session

Frontend Testing Dependencies:
  mock_*.dart (generated mocks)
    -> *_test.dart (test files)
    -> Widget test utilities (pumpWidget, pumpAndSettle)
    -> Provider mocks (Mockito)
```

### Test Isolation Requirements

| Component | Isolation Method | Reason |
|-----------|-----------------|--------|
| Backend Services | Mock database session | Speed, determinism |
| Backend API Routes | TestClient + mock services | HTTP layer testing |
| LLM Adapters | Mock SDK clients | No API calls, deterministic |
| Frontend Providers | Mock services | State logic isolation |
| Frontend Widgets | Mock providers | UI logic isolation |
| Frontend Services | Mock HTTP client | No network calls |

---

## MVP Test Recommendation

For initial comprehensive coverage, prioritize:

### Phase 1: Foundation (HIGH priority)
1. **Backend service layer** - auth_service, project_service, thread_service
2. **Frontend providers** - AuthProvider, ProjectProvider, ConversationProvider
3. **Model serialization** - All JSON round-trips

### Phase 2: Core Features (MEDIUM priority)
4. **API endpoint tests** - All CRUD endpoints
5. **Widget tests** - Key screens (Login, ProjectList, Conversation)
6. **Error handling** - All error paths in services

### Phase 3: Advanced (LOWER priority)
7. **LLM adapter mocking** - Streaming behavior
8. **Edge cases** - Pagination, concurrent access
9. **Differentiators** - Token tracking, encryption

### Defer to Integration Tests

- Full OAuth flow (requires external services)
- Real LLM responses (costly, non-deterministic)
- Full database migrations (E2E concern)
- Cross-screen navigation (integration concern)

---

## Existing Test Analysis

Current test files in project:

### Backend (11 test files in backend/tests/)
- `test_projects.py` - Project CRUD, cascade delete (GOOD pattern)
- `test_threads.py` - Thread CRUD, isolation (GOOD pattern)
- `test_documents.py` - Document operations
- `test_auth_integration.py` - Auth flow (integration level)
- `test_backend_integration.py` - Full integration tests
- Others: skill, document_search, global_threads

### Frontend (11 test files)
- `unit/chats_provider_test.dart` - Provider state testing (EXCELLENT pattern)
- `widget/login_screen_test.dart` - Widget state rendering
- `widget/project_list_screen_test.dart` - List rendering, states
- `widget/conversation_screen_test.dart` - Message display, streaming
- Integration tests for auth_flow, project_flow

### Gaps Identified

| Missing Test | Priority | Rationale |
|--------------|----------|-----------|
| Service unit tests (isolated from API) | HIGH | Services have no direct unit tests |
| LLM adapter unit tests | HIGH | Critical path, no coverage |
| Encryption service tests | MEDIUM | Security-sensitive |
| Token tracking tests | MEDIUM | Budget enforcement |
| More provider unit tests | HIGH | Only ChatsProvider tested |
| API service (frontend) tests | MEDIUM | Network layer |

---

## BA Assistant Component Coverage Map

### Backend Components Requiring Tests

| Component | File(s) | Test Priority | Coverage Goal |
|-----------|---------|---------------|---------------|
| **AuthService** | `auth_service.py` | HIGH | 85% |
| **ProjectService** | (part of API routes) | HIGH | 80% |
| **ThreadService** | (part of API routes) | HIGH | 80% |
| **DocumentService** | (part of API routes) | HIGH | 80% |
| **MessageService** | (part of API routes) | HIGH | 80% |
| **AIService** | `ai_service.py` | HIGH | 75% (mock LLM) |
| **AnthropicAdapter** | `anthropic_adapter.py` | HIGH | 80% |
| **GeminiAdapter** | `gemini_adapter.py` | MEDIUM | 75% |
| **DeepSeekAdapter** | `deepseek_adapter.py` | MEDIUM | 75% |
| **EncryptionService** | `encryption.py` | MEDIUM | 90% |
| **TokenTracking** | `token_tracking.py` | MEDIUM | 80% |
| **DocumentSearch** | `document_search.py` | MEDIUM | 75% |
| **SkillLoader** | `skill_loader.py` | LOW | 70% |
| **BRDGenerator** | `brd_generator.py` | LOW | 70% |

### Frontend Components Requiring Tests

| Component | File(s) | Test Priority | Coverage Goal |
|-----------|---------|---------------|---------------|
| **AuthProvider** | `auth_provider.dart` | HIGH | 85% |
| **ProjectProvider** | `project_provider.dart` | HIGH | 85% |
| **ConversationProvider** | `conversation_provider.dart` | HIGH | 85% |
| **ChatsProvider** | `chats_provider.dart` | HIGH | 85% (has tests) |
| **ThreadProvider** | `thread_provider.dart` | HIGH | 80% |
| **DocumentProvider** | `document_provider.dart` | HIGH | 80% |
| **ThemeProvider** | `theme_provider.dart` | MEDIUM | 75% |
| **SettingsProvider** | (if exists) | MEDIUM | 75% |
| **ApiService** | `api_service.dart` | HIGH | 80% |
| **AuthService** | `auth_service.dart` | HIGH | 80% |
| **Models (all)** | `models/*.dart` | HIGH | 90% |

---

## Sources

### Official Documentation
- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [Flutter Testing Overview](https://docs.flutter.dev/testing/overview)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock-examples.html)

### Testing Patterns and Anti-Patterns
- [Unit Testing Anti-Patterns Full List](https://dzone.com/articles/unit-testing-anti-patterns-full-list)
- [Software Testing Anti-Patterns](https://blog.codepipes.com/testing/software-testing-antipatterns.html)
- [Unit Testing Best Practices - .NET (applicable concepts)](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices)
- [Structural Inspection Anti-Pattern](https://enterprisecraftsmanship.com/posts/structural-inspection)

### Python/FastAPI Testing
- [Python Testing with PyTest 2025](https://www.johal.in/python-testing-frameworks-pytest-advanced-features-and-mocking-strategies-for-unit-tests-2025/)
- [Advanced Integration Testing Python 2025](https://moldstud.com/articles/p-advanced-integration-testing-techniques-for-python-developers-expert-guide-2025)
- [Service Layer and Repository Pattern Testing](https://www.oreilly.com/library/view/architecture-patterns-with/9781492052197/ch04.html)

### LLM Testing
- [Mock LLM API Calls for Unit Testing](https://markaicode.com/mock-llm-api-calls-unit-testing/)
- [LiteLLM Mock Requests](https://docs.litellm.ai/docs/completion/mock_requests)
- [Importance of Mocking in LLM Streaming](https://medium.com/@zazaneryawan/importance-of-mocking-in-llm-streaming-through-fastapi-python-5092984915d3)
- [MockLLM - Simulated LLM API](https://github.com/StacklokLabs/mockllm)
- [llm-mocks PyPI Package](https://pypi.org/project/llm-mocks/)

### Flutter Testing
- [Flutter Test Coverage](https://testsigma.com/blog/flutter-test-coverage/)
- [Best Practices for Testing Flutter Applications](https://www.walturn.com/insights/best-practices-for-testing-flutter-applications)
- [Flutter Unit Testing 2025](https://www.bacancytechnology.com/blog/flutter-unit-testing)
- [Strategies to Improve Flutter Test Coverage](https://www.dhiwise.com/post/the-ultimate-guide-to-improving-flutter-test-coverage)

### Coverage Best Practices
- [Code Coverage vs Test Coverage](https://blog.codacy.com/code-coverage-vs-test-coverage)
- [Achieving High Code Coverage with Unit Tests](https://www.sonarsource.com/resources/library/code-coverage-unit-tests/)
- [How to Decide on Unit Test Coverage](https://softteco.com/blog/unit-test-coverage)

---

*Research completed 2026-02-02. Ready for requirements definition.*
