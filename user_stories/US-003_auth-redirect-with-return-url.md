# US-003: Auth Redirect with Return URL

**Priority:** High
**Status:** Ready for Development
**Related Bug:** BUG-001

---

## User Story

As an unauthenticated user,
I want the login flow to remember where I was trying to go,
So that I arrive at my intended destination after login.

---

## Acceptance Criteria

### AC-1: Protected route triggers login with return URL
- **Given** I access `/settings` while logged out
- **When** I'm redirected to `/login`
- **Then** the intended destination (`/settings`) is stored

### AC-2: Login completes to stored destination
- **Given** I was redirected to login from `/projects/123`
- **When** I complete OAuth login successfully
- **Then** I'm sent to `/projects/123` (not `/home`)

### AC-3: Direct login goes to home
- **Given** I navigate directly to `/login`
- **When** I complete OAuth login
- **Then** I'm sent to `/home` (default behavior)

### AC-4: Return URL cleared after use
- **Given** I logged in and was redirected to `/projects/123`
- **When** I log out and log back in directly
- **Then** I go to `/home` (return URL not reused)

### AC-5: Invalid return URL handled
- **Given** stored return URL is `/projects/999` (deleted project)
- **When** I complete login
- **Then** I'm redirected to the return URL
- **And** app handles 404 gracefully (shows error, offers navigation)

---

## Technical Notes

**Storage mechanism options:**
1. Query parameter: `/login?returnUrl=/projects/123`
2. Session storage: `sessionStorage.setItem('returnUrl', '/projects/123')`
3. Provider state: Store in AuthProvider (cleared on logout)

**Recommended:** Query parameter (visible, debuggable, works with refresh)

**Implementation:**
```dart
// In redirect logic
if (!isAuthenticated && !isLoading && !isSplash && !isLogin && !isCallback) {
  final returnUrl = Uri.encodeComponent(state.matchedLocation);
  return '/login?returnUrl=$returnUrl';
}

// After auth success
if (isAuthenticated && (isSplash || isLogin)) {
  final returnUrl = state.uri.queryParameters['returnUrl'];
  return returnUrl ?? '/home';
}
```
