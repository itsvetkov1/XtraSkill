---
phase: 31-frontend-provider-service-tests
plan: 05
outcome: success
duration: 4m
completed: 2026-02-02

subsystem: frontend-services
tags: [unit-tests, flutter, mockito, dio, auth-service, project-service]

dependency-graph:
  requires: [31-RESEARCH]
  provides: [FSVC-02 complete, FSVC-01 partial]
  affects: []

tech-stack:
  added: []
  patterns: [Dio mocking with @GenerateNiceMocks, FlutterSecureStorage mocking]

key-files:
  created:
    - frontend/test/unit/services/auth_service_test.dart
    - frontend/test/unit/services/auth_service_test.mocks.dart
    - frontend/test/unit/services/project_service_test.dart
    - frontend/test/unit/services/project_service_test.mocks.dart
  modified: []

decisions:
  - decision: "Test JWT validation with actual base64 encoding"
    rationale: "Verify real token parsing logic, not just mock returns"
  - decision: "Skip launchUrl testing in OAuth methods"
    rationale: "url_launcher not available in test environment; test initiate endpoint only"
  - decision: "Use createTestJwt helper for JWT tests"
    rationale: "Consistent test token generation with real base64 encoding"

metrics:
  tests-added: 68
  coverage-impact: "FSVC-02 complete (AuthService), FSVC-01 partial (ProjectService)"
---

# Phase 31 Plan 05: Service Tests Summary

AuthService (35 tests) and ProjectService (33 tests) unit tests with comprehensive HTTP contract testing via Dio mocking.

## Changes Made

### Task 1: AuthService unit tests (562 lines)

Created comprehensive tests for AuthService covering:

1. **Constructor injection** (4 tests): Service accepts optional Dio, FlutterSecureStorage, baseUrl parameters
2. **storeToken** (3 tests): Writes token to secure storage with correct key
3. **getStoredToken** (2 tests): Reads token from secure storage, handles null
4. **isTokenValid** (9 tests): Full JWT validation testing
   - Returns false for missing token, invalid format (< 3 parts, > 3 parts)
   - Returns false for invalid base64, invalid JSON, missing exp field
   - Returns false for expired tokens
   - Returns true for valid unexpired tokens
5. **getCurrentUser** (5 tests): Makes GET /auth/me with Bearer token
6. **getUsage** (4 tests): Makes GET /auth/usage with Bearer token
7. **logout** (4 tests): Deletes token, calls backend, ignores errors
8. **loginWithGoogle/loginWithMicrosoft** (4 tests): Tests OAuth initiation endpoints

Test helper created:
```dart
String createTestJwt({required int expSeconds}) {
  final header = base64Url.encode(utf8.encode('{"alg":"HS256","typ":"JWT"}'));
  final payload = base64Url.encode(utf8.encode('{"exp":$expSeconds,"sub":"user123"}'));
  return '$headerNoPad.$payloadNoPad.fake-signature';
}
```

### Task 2: ProjectService unit tests (748 lines)

Created comprehensive tests for ProjectService covering:

1. **Constructor injection** (4 tests): Service accepts optional parameters
2. **getProjects** (6 tests): Makes GET /api/projects, returns List<Project>
3. **createProject** (6 tests): Makes POST with name/description, handles 422 validation
4. **getProject** (5 tests): Makes GET /api/projects/{id}, handles 404
5. **updateProject** (6 tests): Makes PUT with name/description, handles 404/422
6. **deleteProject** (6 tests): Makes DELETE, handles 401/404

### Task 3: Mock generation

Services directory created at `frontend/test/unit/services/`. Build runner generated mock files for both test files containing MockDio and MockFlutterSecureStorage classes.

## Verification Results

```
AuthService tests: 35 passed
ProjectService tests: 33 passed
All services combined: 93 passed (includes existing DocumentService)
```

## Test Counts

| Service | Tests | Lines |
|---------|-------|-------|
| AuthService | 35 | 562 |
| ProjectService | 33 | 748 |
| **Total (this plan)** | **68** | **1310** |

## Success Criteria Met

- [x] AuthService has 15+ test cases (35 actual) covering token management, user info, and validation
- [x] ProjectService has 10+ test cases (33 actual) covering CRUD operations
- [x] Both services mock Dio and FlutterSecureStorage correctly
- [x] 404 error handling tested
- [x] All tests pass with `flutter test test/unit/services/`

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Description |
|------|-------------|
| 4126c1f | test(31-05): add AuthService unit tests |
| 0f17f13 | test(31-05): add ProjectService unit tests |

## Requirements Covered

| Requirement | Description | Status |
|-------------|-------------|--------|
| FSVC-02 | AuthService has unit test coverage | Complete |
| FSVC-01 | ApiService (partial - ProjectService CRUD) | Partial |

## Running Phase 31 Totals

| Plan | Tests Added | Cumulative |
|------|-------------|------------|
| 31-01 | 28 | 28 |
| 31-02 | 41 | 69 |
| 31-03 | 35 | 104 |
| 31-04 | 27 | 131 |
| 31-05 | 68 | 199 |

## Next Phase Readiness

Phase 31 complete. All 5 plans executed successfully.

**Phase 31 Final Summary:**
- 199 total tests added
- 10 providers tested
- 2 services tested (AuthService, ProjectService)
- Coverage: FPROV-01 through FPROV-09, FSVC-01 (partial), FSVC-02
