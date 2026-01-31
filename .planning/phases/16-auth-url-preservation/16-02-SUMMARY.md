---
phase: 16-auth-url-preservation
plan: 02
subsystem: navigation
tags: [gorouter, auth, deep-linking, session-storage, oauth]

dependency-graph:
  requires:
    - "16-01: UrlStorageService for sessionStorage access"
    - "16-01: GoRouter redirect with returnUrl query parameter preservation"
  provides:
    - "Complete deep linking through OAuth flow"
    - "LoginScreen stores returnUrl before OAuth redirect"
    - "CallbackScreen navigates to returnUrl after successful auth"
  affects:
    - "17-*: Project and thread URL routing can rely on deep linking"

tech-stack:
  added: []
  patterns:
    - "Pre-OAuth URL storage to sessionStorage"
    - "Post-OAuth URL retrieval and navigation"
    - "Open redirect prevention via relative path validation"

key-files:
  created: []
  modified:
    - frontend/lib/screens/auth/login_screen.dart
    - frontend/lib/screens/auth/callback_screen.dart

decisions:
  - id: DEC-16-02-01
    decision: "Validate returnUrl starts with '/' to prevent open redirect"
    rationale: "Security requirement - external URLs (https://evil.com) rejected, only relative paths allowed"
  - id: DEC-16-02-02
    decision: "Clear returnUrl immediately after retrieval"
    rationale: "One-time use prevents stale redirects on subsequent logins"

metrics:
  duration: ~4 minutes
  completed: 2026-01-31
---

# Phase 16 Plan 02: Login and Callback Screen Integration Summary

**One-liner:** LoginScreen stores returnUrl to sessionStorage before OAuth, CallbackScreen retrieves and navigates there after successful auth with open redirect protection.

## What Was Built

### Task 1: LoginScreen returnUrl Storage

Updated `frontend/lib/screens/auth/login_screen.dart`:
- Added imports for `go_router` and `url_storage_service.dart`
- Both `_handleGoogleLogin` and `_handleMicrosoftLogin` now:
  1. Extract returnUrl from query parameters via `GoRouterState.of(context).uri`
  2. If returnUrl exists, decode it and store to sessionStorage before OAuth redirect
  3. Proceed with OAuth (browser will leave Flutter app)

**Key code:**
```dart
void _handleGoogleLogin(BuildContext context) {
  // Extract returnUrl from current URL query params
  final uri = GoRouterState.of(context).uri;
  final returnUrl = uri.queryParameters['returnUrl'];

  // Store before OAuth redirect (browser will leave app)
  if (returnUrl != null) {
    final urlStorage = UrlStorageService();
    urlStorage.storeReturnUrl(Uri.decodeComponent(returnUrl));
  }

  // Proceed with OAuth
  final authProvider = context.read<AuthProvider>();
  authProvider.loginWithGoogle();
}
```

### Task 2: CallbackScreen returnUrl Navigation

Updated `frontend/lib/screens/auth/callback_screen.dart`:
- Added import for `url_storage_service.dart`
- After successful authentication:
  1. Retrieve returnUrl from sessionStorage
  2. Clear returnUrl immediately (one-time use)
  3. Validate returnUrl starts with '/' (security: prevent open redirect)
  4. Navigate to destination with `context.go()`
  5. Default to `/home` if no returnUrl or invalid returnUrl

**Key code:**
```dart
if (mounted && authProvider.isAuthenticated) {
  // Get stored return URL from sessionStorage
  final urlStorage = UrlStorageService();
  final returnUrl = urlStorage.getReturnUrl();

  // Clear after retrieval (one-time use, prevents stale redirects)
  urlStorage.clearReturnUrl();

  // Validate returnUrl (security: prevent open redirect)
  String destination = '/home';
  if (returnUrl != null && returnUrl.startsWith('/')) {
    destination = returnUrl;
  }

  // Navigate directly
  context.go(destination);
}
```

## Complete Deep Link Flow

With plans 16-01 and 16-02 complete, the full flow is:

```
1. User accesses /projects/123 (not logged in)
2. GoRouter redirect captures URL, sends to /splash?returnUrl=%2Fprojects%2F123
3. Auth check completes (not authenticated)
4. GoRouter redirect forwards returnUrl, sends to /login?returnUrl=%2Fprojects%2F123
5. User clicks "Sign in with Google"
6. LoginScreen extracts returnUrl from query, stores "/projects/123" to sessionStorage
7. Browser leaves Flutter app, goes to Google OAuth
8. User authenticates with Google
9. Backend redirects to /auth/callback?token=...
10. CallbackScreen processes token, stores JWT
11. CallbackScreen retrieves "/projects/123" from sessionStorage
12. CallbackScreen clears sessionStorage (one-time use)
13. CallbackScreen navigates to /projects/123
14. User lands on intended page!
```

## Security Implementation

**Open Redirect Prevention:**
- returnUrl validated to start with '/' (relative paths only)
- External URLs like `https://evil.com/phishing` are rejected
- Falls back safely to `/home` when validation fails

**Session Storage Behavior:**
- Clears automatically when tab/window closes
- Cleared programmatically after retrieval
- No stale returnUrl on subsequent logins

## Verification Results

| Check | Result |
|-------|--------|
| flutter analyze login_screen.dart | No issues |
| flutter analyze callback_screen.dart | 12 info (pre-existing debug prints) |
| flutter build web | Success |

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Message |
|------|---------|
| b88ce47 | feat(16-02): store returnUrl before OAuth redirect in LoginScreen |
| a567e16 | feat(16-02): navigate to stored returnUrl after OAuth callback |

## Next Phase Readiness

**Phase 16 Complete:** Auth URL Preservation

**Full deep linking capability now available:**
- Users can share direct URLs to projects/threads
- Unauthenticated users redirected to login with returnUrl
- After OAuth, users land on originally requested page
- Security validated (no open redirect vulnerability)

**Ready for Phase 17:** Project and Thread URL Routing
- Can implement `/projects/:id` and `/projects/:id/threads/:id` routes
- Deep linking infrastructure complete
