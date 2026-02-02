# Requirements: BA Assistant v1.9.1

**Defined:** 2026-02-02
**Core Value:** Comprehensive unit test coverage across all business logic with CI-ready test suite

## v1.9.1 Requirements

Requirements for unit test coverage milestone. Each maps to roadmap phases.

### Test Infrastructure

- [x] **INFRA-01**: pytest-cov installed and configured for coverage reporting
- [x] **INFRA-02**: Shared fixtures module created (`tests/fixtures/`)
- [x] **INFRA-03**: MockLLMAdapter implemented for adapter-layer testing
- [x] **INFRA-04**: Factory-boy test data factories for User, Project, Document, Thread, Message
- [x] **INFRA-05**: Flutter lcov configured for HTML coverage reports

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
| INFRA-01 | Phase 28 | Complete |
| INFRA-02 | Phase 28 | Complete |
| INFRA-03 | Phase 28 | Complete |
| INFRA-04 | Phase 28 | Complete |
| INFRA-05 | Phase 28 | Complete |
| BSVC-01 | Phase 29 | Pending |
| BSVC-02 | Phase 29 | Pending |
| BSVC-03 | Phase 29 | Pending |
| BSVC-04 | Phase 29 | Pending |
| BSVC-05 | Phase 29 | Pending |
| BSVC-06 | Phase 29 | Pending |
| BLLM-01 | Phase 30 | Pending |
| BLLM-02 | Phase 30 | Pending |
| BLLM-03 | Phase 30 | Pending |
| BLLM-04 | Phase 30 | Pending |
| BLLM-05 | Phase 30 | Pending |
| BAPI-01 | Phase 30 | Pending |
| BAPI-02 | Phase 30 | Pending |
| BAPI-03 | Phase 30 | Pending |
| BAPI-04 | Phase 30 | Pending |
| BAPI-05 | Phase 30 | Pending |
| BAPI-06 | Phase 30 | Pending |
| BAPI-07 | Phase 30 | Pending |
| FPROV-01 | Phase 31 | Pending |
| FPROV-02 | Phase 31 | Pending |
| FPROV-03 | Phase 31 | Pending |
| FPROV-04 | Phase 31 | Pending |
| FPROV-05 | Phase 31 | Pending |
| FPROV-06 | Phase 31 | Pending |
| FPROV-07 | Phase 31 | Pending |
| FPROV-08 | Phase 31 | Pending |
| FSVC-01 | Phase 31 | Pending |
| FSVC-02 | Phase 31 | Pending |
| FWID-01 | Phase 32 | Pending |
| FWID-02 | Phase 32 | Pending |
| FWID-03 | Phase 32 | Pending |
| FWID-04 | Phase 32 | Pending |
| FWID-05 | Phase 32 | Pending |
| FMOD-01 | Phase 32 | Pending |
| CI-01 | Phase 33 | Pending |
| CI-02 | Phase 33 | Pending |
| CI-03 | Phase 33 | Pending |
| CI-04 | Phase 33 | Pending |

**Coverage:**
- v1.9.1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0

---
*Requirements defined: 2026-02-02*
*Last updated: 2026-02-02 after roadmap creation (traceability complete)*
