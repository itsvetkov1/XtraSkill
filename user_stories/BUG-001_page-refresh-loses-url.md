# BUG-001: Page Refresh Redirects to Home Instead of Preserving URL

**Reported:** 2026-01-30
**Severity:** High
**Status:** Open

---

## Environment

- **Platform:** Flutter Web (Chrome), affects all platforms
- **Version:** Beta v1.6

---

## Preconditions

- User is authenticated
- User is viewing any page other than `/home`

---

## Steps to Reproduce

1. Navigate to any protected route (e.g., `/projects`, `/projects/:id`, `/settings`)
2. Press F5 or click browser refresh button
3. Observe navigation behavior

---

## Expected Behavior

User remains on the same page after refresh (e.g., `/projects/123` stays at `/projects/123`)

---

## Actual Behavior

User is redirected: `/splash` → `/home`

Navigation context is lost regardless of original page.

---

## Root Cause Analysis

Per `frontend/lib/main.dart:150-167`:

1. Router hardcodes `initialLocation: '/splash'` (line 150)
2. On refresh, auth state starts with `isLoading=true`
3. Redirect logic (line 172-174) sends any protected route to `/splash` while loading
4. Once authenticated, redirect logic (line 165-167) sends `/splash` to `/home`
5. **No mechanism exists to store/restore the intended destination URL**

Per `.planning/APP-FEATURES-AND-FLOWS.md` (lines 66-72), this behavior is documented as expected:
```
| Authenticated + on splash/login | → `/home` |
```

This is a **missing feature**, not an implementation error.

---

## Impact

- Users lose navigation context on every refresh
- Bookmarked URLs don't work (always land on `/home`)
- Shared links don't work
- Disrupts testing workflow significantly

---

## Related Stories

- US-001: URL Preservation on Refresh
- US-002: Deep Link Support
- US-003: Auth Redirect with Return URL
