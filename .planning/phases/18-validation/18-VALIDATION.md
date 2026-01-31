# Phase 18: End-to-End Validation Test Matrix

**Created:** 2026-01-31
**Status:** Pending execution

## Test Environment Setup

### Start Backend
```bash
cd backend && python run.py
```

### Start Frontend
```bash
cd frontend && flutter run -d chrome
```

### Testing Tips
- Use incognito/private window for clean state between auth tests
- Clear sessionStorage between tests: `sessionStorage.clear()` in browser DevTools
- Record project/thread IDs before deletion tests

---

## Test Matrix

### Category 1: Route Navigation (ROUTE-01 through ROUTE-04)

| Test ID | Requirement | Scenario | Steps | Expected | Status |
|---------|-------------|----------|-------|----------|--------|
| VAL-01 | ROUTE-01 | Conversations have unique URLs | 1. Login and navigate to a thread<br>2. Check browser address bar | URL shows `/projects/{projectId}/threads/{threadId}` | Pending |
| VAL-02 | ROUTE-02 | Browser back/forward works | 1. Navigate: Home > Projects > Project > Thread<br>2. Click browser Back button<br>3. Click browser Forward button | Back returns to Project, Forward returns to Thread | Pending |
| VAL-03 | ROUTE-03 | Invalid route shows 404 | 1. Navigate to `/this-route-does-not-exist`<br>2. Observe screen | NotFoundScreen displays with navigation options | Pending |
| VAL-04 | ROUTE-04 | ConversationScreen accepts URL params | 1. Copy a thread URL<br>2. Paste directly into new tab<br>3. Login if prompted | ConversationScreen loads correct thread | Pending |

### Category 2: URL Preservation (URL-01 through URL-04)

| Test ID | Requirement | Scenario | Steps | Expected | Status |
|---------|-------------|----------|-------|----------|--------|
| VAL-05 | URL-01 | Page refresh preserves URL (authenticated) | 1. Login and navigate to `/projects/{id}`<br>2. Press F5 to refresh | URL remains `/projects/{id}`, page reloads correctly | Pending |
| VAL-06 | URL-02 | URL preserved through OAuth | 1. In incognito, access `/projects/{id}`<br>2. Complete OAuth login<br>3. Check final URL | After login, lands on `/projects/{id}` (not `/home`) | Pending |
| VAL-07 | URL-03 | Settings refresh returns to /settings | 1. Login and navigate to `/settings`<br>2. Press F5 to refresh | URL remains `/settings`, settings page reloads | Pending |
| VAL-08 | URL-04 | Project detail refresh returns correctly | 1. Login and navigate to `/projects/{id}`<br>2. Press F5 to refresh | URL remains `/projects/{id}`, project loads correctly | Pending |

### Category 3: Auth Flow (AUTH-01 through AUTH-04)

| Test ID | Requirement | Scenario | Steps | Expected | Status |
|---------|-------------|----------|-------|----------|--------|
| VAL-09 | AUTH-01 | Auth redirect captures returnUrl | 1. In incognito, access `/projects/{id}`<br>2. Observe login screen URL | Login URL contains `?returnUrl=%2Fprojects%2F{id}` | Pending |
| VAL-10 | AUTH-02 | Login completes to stored returnUrl | 1. In incognito, access `/projects/{id}`<br>2. Complete OAuth login<br>3. Check destination | Lands on `/projects/{id}` | Pending |
| VAL-11 | AUTH-03 | Direct login goes to /home | 1. In incognito, access `/login` directly<br>2. Complete OAuth login<br>3. Check destination | Lands on `/home` (no returnUrl was set) | Pending |
| VAL-12 | AUTH-04 | returnUrl cleared after use | 1. Complete VAL-10 (login with returnUrl)<br>2. In DevTools: `sessionStorage.getItem('returnUrl')`<br>3. Check value | Returns `null` (returnUrl was cleared) | Pending |

### Category 4: Error Handling (ERR-01 through ERR-04)

| Test ID | Requirement | Scenario | Steps | Expected | Status |
|---------|-------------|----------|-------|----------|--------|
| VAL-13 | ERR-01 | Invalid route shows 404 page | 1. Navigate to `/invalid/route/path`<br>2. Observe screen | NotFoundScreen with "Page not found" message | Pending |
| VAL-14 | ERR-02 | Non-existent project shows not-found | 1. Navigate to `/projects/nonexistent-uuid`<br>2. Observe screen | ResourceNotFoundState: "Project not found" with folder_off icon | Pending |
| VAL-15 | ERR-03 | Non-existent thread shows not-found | 1. Navigate to `/projects/{validId}/threads/nonexistent-uuid`<br>2. Observe screen | ResourceNotFoundState: "Thread not found" with speaker_notes_off icon | Pending |
| VAL-16 | ERR-04 | Deleted resource via returnUrl handled | 1. Create a project, note its ID<br>2. Delete the project<br>3. In incognito, access `/projects/{deleted-id}` (logged out)<br>4. Complete OAuth login | After login, shows "Project not found" state (not crash) | Pending |

---

## Security Validation

| Test ID | Scenario | Steps | Expected | Status |
|---------|----------|-------|----------|--------|
| SEC-01 | External URL in returnUrl rejected | 1. In incognito, access `/login`<br>2. In DevTools: `sessionStorage.setItem('returnUrl', 'https://evil.com')`<br>3. Complete OAuth login | Lands on `/home` (external URL rejected, not redirected to evil.com) | Pending |
| SEC-02 | Malformed returnUrl fallback | 1. In incognito, access `/login`<br>2. In DevTools: `sessionStorage.setItem('returnUrl', 'not-a-valid-path')`<br>3. Complete OAuth login | Lands on `/home` (malformed URL rejected) | Pending |

---

## Edge Cases

*To be filled during testing execution*

| ID | Scenario | Steps | Expected | Actual | Notes |
|----|----------|-------|----------|--------|-------|
| EDGE-01 | | | | | |
| EDGE-02 | | | | | |
| EDGE-03 | | | | | |

---

## Summary

**Pass Rate:** Pending execution

| Category | Total | Passed | Failed | Pending |
|----------|-------|--------|--------|---------|
| Route Navigation | 4 | 0 | 0 | 4 |
| URL Preservation | 4 | 0 | 0 | 4 |
| Auth Flow | 4 | 0 | 0 | 4 |
| Error Handling | 4 | 0 | 0 | 4 |
| Security | 2 | 0 | 0 | 2 |
| **Total** | **18** | **0** | **0** | **18** |

---

*Validation document created: 2026-01-31*
*Last updated: 2026-01-31*
