# Requirements: BA Assistant v1.9.1

**Defined:** 2026-02-02
**Core Value:** Comprehensive unit test coverage across all business logic with CI-ready test suite

## v1.9.1 Requirements

Requirements for unit test coverage milestone. Each maps to roadmap phases.

### Test Infrastructure

- [ ] **INFRA-01**: pytest-cov installed and configured for coverage reporting
- [ ] **INFRA-02**: Shared fixtures module created (`tests/fixtures/`)
- [ ] **INFRA-03**: MockLLMAdapter implemented for adapter-layer testing
- [ ] **INFRA-04**: Factory-boy test data factories for User, Project, Document, Thread, Message
- [ ] **INFRA-05**: Flutter lcov configured for HTML coverage reports

### Backend Service Tests

- [ ] **BSVC-01**: auth_service has unit test coverage
- [ ] **BSVC-02**: project_service has unit test coverage
- [ ] **BSVC-03**: document_service has unit test coverage
- [ ] **BSVC-04**: thread_service has unit test coverage
- [ ] **BSVC-05**: message_service has unit test coverage
- [ ] **BSVC-06**: ai_service has unit test coverage

### Backend LLM Adapter Tests

- [ ] **BLLM-01**: AnthropicAdapter has unit test coverage
- [ ] **BLLM-02**: GeminiAdapter has unit test coverage
- [ ] **BLLM-03**: DeepSeekAdapter has unit test coverage
- [ ] **BLLM-04**: SSE streaming test helper implemented
- [ ] **BLLM-05**: Document search (FTS5) has unit test coverage

### Backend API Tests

- [ ] **BAPI-01**: Auth router has contract tests
- [ ] **BAPI-02**: Projects router has contract tests
- [ ] **BAPI-03**: Documents router has contract tests
- [ ] **BAPI-04**: Threads router has contract tests
- [ ] **BAPI-05**: Messages router has contract tests
- [ ] **BAPI-06**: Chat router has contract tests
- [ ] **BAPI-07**: Error response consistency verified

### Frontend Provider Tests

- [ ] **FPROV-01**: AuthProvider has unit test coverage
- [ ] **FPROV-02**: ProjectsProvider has unit test coverage
- [ ] **FPROV-03**: DocumentsProvider has unit test coverage
- [ ] **FPROV-04**: ThreadsProvider has unit test coverage
- [ ] **FPROV-05**: MessagesProvider has unit test coverage
- [ ] **FPROV-06**: ChatsProvider has complete unit test coverage (expand existing)
- [ ] **FPROV-07**: ThemeProvider has unit test coverage
- [ ] **FPROV-08**: SettingsProvider has unit test coverage

### Frontend Service Tests

- [ ] **FSVC-01**: ApiService has unit test coverage
- [ ] **FSVC-02**: AuthService has unit test coverage

### Frontend Widget Tests

- [ ] **FWID-01**: ChatInput widget has unit test coverage
- [ ] **FWID-02**: MessageBubble widget has unit test coverage
- [ ] **FWID-03**: ThreadList widget has unit test coverage
- [ ] **FWID-04**: DocumentList widget has unit test coverage
- [ ] **FWID-05**: All screens have test coverage

### Frontend Model Tests

- [ ] **FMOD-01**: Model JSON serialization round-trip tests

### CI Integration

- [ ] **CI-01**: Coverage reporting enabled in CI pipeline
- [ ] **CI-02**: All tests pass gate enforced
- [ ] **CI-03**: Coverage threshold enforcement (fail-under)
- [ ] **CI-04**: Coverage badges added to README

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| E2E/integration tests | Already have some; focus on unit tests |
| UI snapshot tests | Low ROI for current stage |
| Performance/load testing | Different milestone |
| 100% coverage | Diminishing returns; target meaningful coverage |
| Mutation testing | Advanced technique, defer to future |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | TBD | Pending |
| INFRA-02 | TBD | Pending |
| INFRA-03 | TBD | Pending |
| INFRA-04 | TBD | Pending |
| INFRA-05 | TBD | Pending |
| BSVC-01 | TBD | Pending |
| BSVC-02 | TBD | Pending |
| BSVC-03 | TBD | Pending |
| BSVC-04 | TBD | Pending |
| BSVC-05 | TBD | Pending |
| BSVC-06 | TBD | Pending |
| BLLM-01 | TBD | Pending |
| BLLM-02 | TBD | Pending |
| BLLM-03 | TBD | Pending |
| BLLM-04 | TBD | Pending |
| BLLM-05 | TBD | Pending |
| BAPI-01 | TBD | Pending |
| BAPI-02 | TBD | Pending |
| BAPI-03 | TBD | Pending |
| BAPI-04 | TBD | Pending |
| BAPI-05 | TBD | Pending |
| BAPI-06 | TBD | Pending |
| BAPI-07 | TBD | Pending |
| FPROV-01 | TBD | Pending |
| FPROV-02 | TBD | Pending |
| FPROV-03 | TBD | Pending |
| FPROV-04 | TBD | Pending |
| FPROV-05 | TBD | Pending |
| FPROV-06 | TBD | Pending |
| FPROV-07 | TBD | Pending |
| FPROV-08 | TBD | Pending |
| FSVC-01 | TBD | Pending |
| FSVC-02 | TBD | Pending |
| FWID-01 | TBD | Pending |
| FWID-02 | TBD | Pending |
| FWID-03 | TBD | Pending |
| FWID-04 | TBD | Pending |
| FWID-05 | TBD | Pending |
| FMOD-01 | TBD | Pending |
| CI-01 | TBD | Pending |
| CI-02 | TBD | Pending |
| CI-03 | TBD | Pending |
| CI-04 | TBD | Pending |

**Coverage:**
- v1.9.1 requirements: 40 total
- Mapped to phases: 0
- Unmapped: 40

---
*Requirements defined: 2026-02-02*
*Last updated: 2026-02-02 after initial definition*
