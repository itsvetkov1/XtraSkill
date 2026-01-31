---
phase: 16-auth-url-preservation
plan: 01
subsystem: navigation
tags: [gorouter, auth, deep-linking, session-storage]

dependency-graph:
  requires:
    - "15-01: GoRouter setup with StatefulShellRoute"
    - "15-02: ResponsiveScaffold with sidebar navigation"
  provides:
    - "UrlStorageService for sessionStorage access"
    - "GoRouter redirect with returnUrl query parameter preservation"
  affects:
    - "16-02: Login and Callback screens will use UrlStorageService"

tech-stack:
  added: []
  patterns:
    - "Query parameter forwarding for auth flow"
    - "sessionStorage for OAuth redirect preservation"

key-files:
  created:
    - frontend/lib/services/url_storage_service.dart
  modified:
    - frontend/lib/main.dart

decisions:
  - id: DEC-16-01-01
    decision: "Use dart:html for sessionStorage access"
    rationale: "Simpler API than package:web, works now. Migrate to package:web in future when Wasm becomes default"
  - id: DEC-16-01-02
    decision: "CallbackScreen handles navigation instead of redirect callback"
    rationale: "Simpler architecture - redirect callback doesn't need service injection"
  - id: DEC-16-01-03
    decision: "Removed unused UrlStorageService import from main.dart"
    rationale: "Service used in CallbackScreen (plan 02), not in redirect callback"

metrics:
  duration: ~4 minutes
  completed: 2026-01-31
---

# Phase 16 Plan 01: URL Preservation Foundation Summary

**One-liner:** sessionStorage service and GoRouter returnUrl query parameter forwarding for deep link preservation through auth flow.

## What Was Built

### Task 1: UrlStorageService
Created `frontend/lib/services/url_storage_service.dart` with sessionStorage wrapper:
- `storeReturnUrl(String url)` - Store before OAuth redirect
- `getReturnUrl()` - Retrieve after callback
- `clearReturnUrl()` - Clear after successful navigation

Uses browser sessionStorage which auto-clears on tab close (correct ephemeral behavior for returnUrl).

### Task 2: GoRouter Redirect Enhancement
Extended `_createRouter` redirect callback in `frontend/lib/main.dart`:
- Extracts `returnUrl` from query parameters
- Captures intended URL when redirecting unauthenticated users to login
- Forwards returnUrl through splash to login
- Redirects authenticated user to returnUrl instead of hardcoded `/home`
- Uses `state.uri.toString()` to preserve full URL including query params

**Redirect Flow:**
```
User accesses /projects/123
  -> Loading, redirect to /splash?returnUrl=%2Fprojects%2F123
  -> Auth complete (not authenticated), redirect to /login?returnUrl=%2Fprojects%2F123
  -> [User logs in via OAuth - plan 02]
  -> Authenticated, redirect from /login to /projects/123
```

## Implementation Details

### Key Code Changes

**url_storage_service.dart (new):**
```dart
import 'dart:html' as html;

class UrlStorageService {
  static const String _returnUrlKey = 'auth_return_url';

  void storeReturnUrl(String url) {
    html.window.sessionStorage[_returnUrlKey] = url;
  }

  String? getReturnUrl() {
    return html.window.sessionStorage[_returnUrlKey];
  }

  void clearReturnUrl() {
    html.window.sessionStorage.remove(_returnUrlKey);
  }
}
```

**main.dart redirect (enhanced):**
```dart
redirect: (context, state) {
  // Extract existing returnUrl from query params
  final existingReturnUrl = currentUri.queryParameters['returnUrl'];

  // Callback: let CallbackScreen handle navigation
  if (isCallback) {
    return null;
  }

  // Authenticated user on splash/login: go to returnUrl or /home
  if (isAuthenticated && (isSplash || isLogin)) {
    if (existingReturnUrl != null) {
      return Uri.decodeComponent(existingReturnUrl);
    }
    return '/home';
  }

  // Loading: redirect to splash, preserve returnUrl
  if (isLoading && !isSplash && !isLogin && !isCallback) {
    final intendedUrl = currentUri.toString();
    return '/splash?returnUrl=${Uri.encodeComponent(intendedUrl)}';
  }

  // ... additional cases
}
```

## Verification Results

| Check | Result |
|-------|--------|
| flutter analyze url_storage_service.dart | info-level only (dart:html deprecation expected) |
| flutter analyze main.dart | info-level only (pre-existing print warnings) |
| flutter build web | Success |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused import**
- **Found during:** Task 2 verification
- **Issue:** Plan included import of UrlStorageService in main.dart, but redirect callback doesn't use it (CallbackScreen does)
- **Fix:** Removed unused import to eliminate warning
- **Files modified:** frontend/lib/main.dart
- **Commit:** 86e39c1

## Commits

| Hash | Message |
|------|---------|
| 723905e | feat(16-01): create UrlStorageService for sessionStorage access |
| 86e39c1 | feat(16-01): extend GoRouter redirect with returnUrl preservation |

## Next Phase Readiness

**Ready for 16-02:** Login and Callback Screen Integration

**Prerequisites met:**
- UrlStorageService ready for use in login_screen.dart and callback_screen.dart
- GoRouter passes returnUrl through query parameters
- Callback route stays on callback (doesn't redirect to /home in redirect callback)

**Plan 02 will:**
1. LoginScreen: Extract returnUrl from query params, store in sessionStorage before OAuth redirect
2. CallbackScreen: Retrieve returnUrl from sessionStorage after successful auth, navigate there
3. Clear returnUrl after successful navigation to prevent stale redirects
