---
phase: 30
plan: 04
subsystem: backend-testing
tags: ["pytest", "api-tests", "documents", "threads", "contract-tests"]

dependency_graph:
  requires:
    - "phase-28: test infrastructure (fixtures, factories)"
    - "phase-29: service test patterns"
  provides:
    - "backend/tests/api/test_document_routes.py: Documents router contract tests"
    - "backend/tests/api/test_thread_routes.py: Threads router contract tests"
  affects:
    - "phase-30-05: remaining API tests (auth, projects)"

tech_stack:
  added: []
  patterns:
    - "API contract tests with status code verification"
    - "Class-based test organization by endpoint"
    - "Authentication header injection with JWT"

key_files:
  created:
    - "backend/tests/api/__init__.py"
    - "backend/tests/api/test_document_routes.py"
    - "backend/tests/api/test_thread_routes.py"
  modified: []

decisions:
  - decision: "Create api/ subdirectory for route tests"
    rationale: "Separates route contract tests from integration tests in root"
  - decision: "Group tests by endpoint (TestUploadDocument, TestGetThread, etc.)"
    rationale: "Clear mapping between test classes and API operations"
  - decision: "Test both success and error cases in each class"
    rationale: "Complete contract coverage with 403/404/400/413 verification"

metrics:
  duration: "8 minutes"
  completed: "2026-02-02"
---

# Phase 30 Plan 04: Documents & Threads API Tests Summary

**One-liner:** 58 contract tests for Documents (upload/list/get/search/delete) and Threads (create/list/get/update/delete) API endpoints

## What Was Built

### Documents Router Tests (26 tests, 835 lines)

**TestUploadDocument (9 tests):**
- 201 success for .txt and .md files
- 400 for invalid content types (PDF)
- 413 for files over 1MB
- 400 for invalid UTF-8 content
- 403 without auth, 404 project not found/owned
- Response schema validation

**TestListDocuments (4 tests):**
- 200 returns array with documents
- 403 without auth, 404 project not found
- Empty list for new project

**TestGetDocument (5 tests):**
- 200 with decrypted content
- 403 without auth, 404 not found/owned
- Response schema validation (id, filename, content, created_at)

**TestSearchDocuments (4 tests):**
- 200 with search results
- 200 empty results for no matches
- 403 without auth, 404 project not found

**TestDeleteDocument (4 tests):**
- 204 successful deletion
- 403 without auth, 404 not found/owned

### Threads Router Tests (32 tests, 976 lines)

**TestCreateGlobalThread (6 tests):**
- 201 creates projectless (global) thread
- 201 creates project-associated thread
- 400 invalid model_provider
- 403 without auth, 404 project not found
- Response schema validation

**TestListAllThreads (4 tests):**
- 200 paginated response
- 403 without auth
- Pagination params (page, page_size) work correctly
- Response schema (threads, total, page, page_size, has_more)

**TestCreateProjectThread (4 tests):**
- 201 creates thread in project
- 400 invalid provider, 403/404 errors

**TestListProjectThreads (4 tests):**
- 200 returns array
- 403 without auth, 404 project not found
- message_count field included

**TestGetThread (5 tests):**
- 200 with messages array
- 403 without auth, 404 not found/owned
- Messages ordered chronologically (oldest first)

**TestUpdateThread (5 tests):**
- 200 updates title
- 200 associates global thread with project
- 400 when thread already associated (re-association blocked)
- 403 without auth, 404 not found

**TestDeleteThread (4 tests):**
- 204 successful deletion
- 403 without auth, 404 not found/owned

## Key Implementation Patterns

### Authentication Testing
```python
# Create user and get JWT token
user = User(id=str(uuid4()), email="test@example.com", ...)
token = create_access_token(user.id, user.email)

# Include in request
response = await client.get(
    "/api/documents/...",
    headers={"Authorization": f"Bearer {token}"}
)

# Test without auth (403 expected)
response = await client.get("/api/documents/...")
assert response.status_code == 403
```

### Ownership Testing
```python
# Create owner with resource
owner = User(id=str(uuid4()), ...)
project = Project(user_id=owner.id, ...)
document = Document(project_id=project.id, ...)

# Create different user
other_user = User(id=str(uuid4()), ...)
token = create_access_token(other_user.id, other_user.email)

# Attempt access (404 expected)
response = await client.get(f"/api/documents/{doc.id}", headers=...)
assert response.status_code == 404
```

### File Upload Testing
```python
from io import BytesIO

files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
response = await client.post(
    f"/api/projects/{project.id}/documents",
    headers={"Authorization": f"Bearer {token}"},
    files=files
)
assert response.status_code == 201
```

## Verification Results

```
tests/api/test_document_routes.py - 26 tests PASSED
tests/api/test_thread_routes.py - 32 tests PASSED
Total: 58 tests in 2.84s
```

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for 30-05:** Auth and Projects router tests can follow the same patterns:
- Use `create_access_token()` for JWT generation
- Use `client.post/get/patch/delete()` for API calls
- Test 200/201/204 success codes and 400/403/404 error codes
- Verify ownership with multiple users
