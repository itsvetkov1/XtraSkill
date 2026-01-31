# Phase 16: Auth URL Preservation - Research

**Researched:** 2026-01-31
**Domain:** GoRouter redirect logic, session storage for URL preservation, OAuth callback handling
**Confidence:** HIGH

## Summary

Phase 16 implements URL preservation through the authentication flow so users don't lose their intended destination after login. This builds directly on Phase 15's route architecture. The existing GoRouter + AuthProvider architecture is well-suited for this enhancement.

The implementation requires three key changes:
1. **Redirect logic extension** - Capture intended URL as `returnUrl` query parameter when redirecting unauthenticated users
2. **Session storage for OAuth flow** - Store returnUrl before OAuth redirect (browser leaves app), retrieve after callback
3. **Callback screen enhancement** - Navigate to stored returnUrl instead of hardcoded `/home`

**Primary recommendation:** Use query parameters for splash/login transitions (visible, debuggable) and web sessionStorage for OAuth flow preservation (survives external browser redirect). Clear returnUrl from storage after successful navigation to prevent stale redirects.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| go_router | ^17.0.1 | Declarative routing with redirect | Already in use, has built-in returnUrl support via query params |
| dart:html | SDK | Web sessionStorage access | Flutter SDK, works for web platform |
| flutter_secure_storage | ^9.0.0 | Token storage | Already in use for JWT tokens |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| provider | ^6.1.5+1 | State management | Already used, AuthProvider triggers router refresh |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Query parameter + sessionStorage | SharedPreferences only | SharedPreferences persists across sessions - wrong for returnUrl which should be ephemeral |
| dart:html | package:web | package:web is future (Wasm), dart:html works now and is simpler |
| In-memory returnUrl | Persist to storage | In-memory lost on page refresh - sessionStorage survives refresh |

**Installation:**
```bash
# No new packages needed - all already installed
# dart:html is part of Flutter SDK for web
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/
|-- main.dart                    # MODIFY: extend redirect logic with returnUrl
|-- providers/
|   +-- auth_provider.dart       # MODIFY: add returnUrl handling (optional)
|-- services/
|   |-- auth_service.dart        # MODIFY: add sessionStorage methods
|   +-- url_storage_service.dart # NEW (optional): platform-conditional storage
+-- screens/auth/
    |-- callback_screen.dart     # MODIFY: retrieve returnUrl, navigate there
    +-- login_screen.dart        # MODIFY: store returnUrl before OAuth
```

### Pattern 1: Query Parameter for Redirect Chain
**What:** Pass intended destination as `returnUrl` query parameter through login flow
**When to use:** For splash-to-login and login-to-callback transitions
**Example:**
```dart
// Source: GoRouter redirect pattern from official documentation
redirect: (context, state) {
  final isAuthenticated = authProvider.isAuthenticated;
  final isLoading = authProvider.isLoading;
  final currentPath = state.matchedLocation;
  final currentUri = state.uri;

  // Extract existing returnUrl from query params, or use current path if protected
  final existingReturnUrl = currentUri.queryParameters['returnUrl'];
  final returnUrl = existingReturnUrl ??
    (_isProtectedRoute(currentPath) ? currentUri.toString() : null);

  // Unauthenticated user on protected route -> login with returnUrl
  if (!isAuthenticated && !isLoading && _isProtectedRoute(currentPath)) {
    return _buildUrlWithReturn('/login', returnUrl);
  }

  // Authenticated user on login -> go to returnUrl or home
  if (isAuthenticated && currentPath == '/login') {
    final destination = returnUrl != null
      ? Uri.decodeComponent(returnUrl)
      : '/home';
    return destination;
  }

  return null;
}

// Helper: Check if route requires authentication
bool _isProtectedRoute(String path) {
  return path.startsWith('/home') ||
         path.startsWith('/projects') ||
         path.startsWith('/settings');
}

// Helper: Append returnUrl query parameter
String _buildUrlWithReturn(String base, String? returnUrl) {
  if (returnUrl == null) return base;
  return '$base?returnUrl=${Uri.encodeComponent(returnUrl)}';
}
```

### Pattern 2: Session Storage for OAuth Flow
**What:** Store returnUrl in browser sessionStorage before OAuth redirect (leaves app), retrieve after callback
**When to use:** OAuth flow where browser navigates away from Flutter app
**Example:**
```dart
// Source: dart:html sessionStorage API
// In auth_service.dart or dedicated url_storage_service.dart

import 'dart:html' as html;

class UrlStorageService {
  static const String _returnUrlKey = 'auth_return_url';

  /// Store return URL before OAuth redirect
  void storeReturnUrl(String url) {
    html.window.sessionStorage[_returnUrlKey] = url;
  }

  /// Retrieve return URL after OAuth callback
  String? getReturnUrl() {
    return html.window.sessionStorage[_returnUrlKey];
  }

  /// Clear return URL after successful navigation
  void clearReturnUrl() {
    html.window.sessionStorage.remove(_returnUrlKey);
  }
}
```

### Pattern 3: Callback Screen Return URL Handling
**What:** After OAuth token processing, navigate to stored returnUrl instead of /home
**When to use:** In CallbackScreen after successful authentication
**Example:**
```dart
// Source: GoRouter callback pattern + session storage
Future<void> _processCallback() async {
  final uri = GoRouterState.of(context).uri;
  final token = uri.queryParameters['token'];

  if (token == null || token.isEmpty) {
    setState(() {
      _error = 'No authentication token received';
      _isProcessing = false;
    });
    return;
  }

  // Handle callback through auth provider
  final authProvider = context.read<AuthProvider>();
  await authProvider.handleCallback(token);

  if (authProvider.isAuthenticated) {
    // Retrieve stored returnUrl
    final urlStorage = UrlStorageService();
    final returnUrl = urlStorage.getReturnUrl();

    // Clear after retrieval (one-time use)
    urlStorage.clearReturnUrl();

    // Navigate to returnUrl or default to /home
    if (mounted) {
      context.go(returnUrl ?? '/home');
    }
  } else {
    setState(() {
      _error = authProvider.errorMessage ?? 'Authentication failed';
      _isProcessing = false;
    });
  }
}
```

### Pattern 4: Login Screen Stores ReturnUrl Before OAuth
**What:** Extract returnUrl from current URL, store in sessionStorage before OAuth redirect
**When to use:** In LoginScreen when user clicks OAuth button
**Example:**
```dart
// Source: Login flow with return URL preservation
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

### Anti-Patterns to Avoid
- **Storing returnUrl in AuthProvider state only:** Lost on page refresh; use sessionStorage
- **Using SharedPreferences for returnUrl:** Persists across sessions, causes stale redirects
- **Not clearing returnUrl after use:** Next login reuses old destination
- **Using `state.matchedLocation` instead of `state.uri.toString()`:** Loses query parameters
- **Circular redirect with returnUrl:** `/login?returnUrl=/login` causes loops

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL encoding/decoding | Manual string manipulation | `Uri.encodeComponent()` / `Uri.decodeComponent()` | Handles special chars, unicode properly |
| Query param parsing | RegEx or split | `state.uri.queryParameters` | GoRouter provides this correctly |
| Browser storage | Custom JS interop | `dart:html window.sessionStorage` | SDK provided, well-tested |
| Redirect guards | Manual route checking | GoRouter `redirect` callback | Centralized, re-evaluated on auth change |

**Key insight:** The GoRouter redirect callback is evaluated on EVERY navigation AND when `refreshListenable` (AuthProvider) notifies. This means returnUrl preservation must be idempotent - extracting the same returnUrl multiple times should produce the same result.

## Common Pitfalls

### Pitfall 1: Infinite Redirect Loop with returnUrl
**What goes wrong:** App freezes, browser tab becomes unresponsive, stack overflow errors
**Why it happens:** Redirect returns a URL that also triggers a redirect with the same parameters
**How to avoid:**
- Always check `if (state.matchedLocation == targetLocation) return null`
- Never set returnUrl to a public route (/login, /splash)
- Validate returnUrl format before using
**Warning signs:** Console shows repeated redirect logs, CPU spike

### Pitfall 2: Query Parameters Lost During OAuth
**What goes wrong:** User was on `/projects?filter=active`, after login lands on `/projects` without filter
**Why it happens:** Using `state.matchedLocation` (path only) instead of `state.uri.toString()` (full URI)
**How to avoid:** Always use `state.uri.toString()` to capture full URL including query params
**Warning signs:** URLs with query params don't preserve after login

### Pitfall 3: ReturnUrl Reused Across Sessions
**What goes wrong:** User logs out, logs back in directly, goes to old destination instead of /home
**Why it happens:** Using SharedPreferences or localStorage instead of sessionStorage; or not clearing after use
**How to avoid:**
- Use sessionStorage (cleared when tab closes)
- Always clear returnUrl after successful navigation
**Warning signs:** Old destinations appear unexpectedly

### Pitfall 4: Invalid returnUrl Causes Crash
**What goes wrong:** Malformed or malicious returnUrl causes navigation error or security issue
**Why it happens:** Not validating returnUrl before navigation
**How to avoid:**
- Validate returnUrl starts with `/` (relative path only)
- Reject external URLs (potential open redirect vulnerability)
- Handle invalid returnUrl gracefully (fall back to /home)
**Warning signs:** Console errors on navigation, security scan flags

### Pitfall 5: OAuth Callback Ignores returnUrl
**What goes wrong:** Even with returnUrl stored, user always lands on /home after OAuth
**Why it happens:** CallbackScreen navigates to /home before reading storage, or relies on GoRouter redirect which doesn't have access to sessionStorage
**How to avoid:**
- Read returnUrl from sessionStorage in CallbackScreen BEFORE calling context.go()
- Don't rely on GoRouter redirect for final destination - handle in CallbackScreen
**Warning signs:** returnUrl visible in login URL, but post-login always goes to /home

## Code Examples

Verified patterns from official sources:

### Complete Redirect Logic (main.dart)
```dart
// Source: GoRouter documentation + existing codebase pattern
redirect: (context, state) {
  final isAuthenticated = authProvider.isAuthenticated;
  final isLoading = authProvider.isLoading;
  final currentPath = state.matchedLocation;
  final currentUri = state.uri;
  final isSplash = currentPath == '/splash';
  final isLogin = currentPath == '/login';
  final isCallback = currentPath == '/auth/callback';

  // Extract returnUrl from query params
  final returnUrl = currentUri.queryParameters['returnUrl'];

  // Callback: let CallbackScreen handle navigation (it reads from sessionStorage)
  if (isCallback) {
    return isAuthenticated ? null : null; // Stay on callback, it handles navigation
  }

  // Authenticated user on splash/login: go to returnUrl or /home
  if (isAuthenticated && (isSplash || isLogin)) {
    if (returnUrl != null) {
      return Uri.decodeComponent(returnUrl);
    }
    return '/home';
  }

  // Loading: redirect to splash, preserve returnUrl
  if (isLoading && !isSplash && !isLogin && !isCallback) {
    final intendedUrl = currentUri.toString();
    return '/splash?returnUrl=${Uri.encodeComponent(intendedUrl)}';
  }

  // Splash done loading, not authenticated: go to login with returnUrl
  if (isSplash && !isLoading && !isAuthenticated) {
    if (returnUrl != null) {
      return '/login?returnUrl=$returnUrl'; // Already encoded
    }
    return '/login';
  }

  // Unauthenticated on protected route: redirect to login with returnUrl
  if (!isAuthenticated && !isLoading && !isSplash && !isLogin && !isCallback) {
    final intendedUrl = currentUri.toString();
    return '/login?returnUrl=${Uri.encodeComponent(intendedUrl)}';
  }

  return null;
}
```

### Session Storage Service (Platform-Conditional)
```dart
// Source: dart:html sessionStorage + conditional import pattern
// file: lib/services/url_storage_service.dart

// For web platform
import 'dart:html' as html;

class UrlStorageService {
  static const String _key = 'auth_return_url';

  void storeReturnUrl(String url) {
    html.window.sessionStorage[_key] = url;
  }

  String? getReturnUrl() {
    return html.window.sessionStorage[_key];
  }

  void clearReturnUrl() {
    html.window.sessionStorage.remove(_key);
  }
}

// For non-web platforms (mobile), use in-memory with timeout
// Or SharedPreferences with explicit TTL clearing
```

### Callback Screen with Return URL
```dart
// Source: Existing callback_screen.dart pattern + returnUrl enhancement
Future<void> _processCallback() async {
  if (!mounted) return;

  try {
    final uri = GoRouterState.of(context).uri;
    final token = uri.queryParameters['token'];

    if (token == null || token.isEmpty) {
      setState(() {
        _error = 'No authentication token received';
        _isProcessing = false;
      });
      return;
    }

    final authProvider = context.read<AuthProvider>();
    await authProvider.handleCallback(token);

    if (mounted && authProvider.isAuthenticated) {
      // Get stored return URL
      final urlStorage = UrlStorageService();
      final returnUrl = urlStorage.getReturnUrl();
      urlStorage.clearReturnUrl(); // Clear after use

      // Validate returnUrl (security: prevent open redirect)
      String destination = '/home';
      if (returnUrl != null && returnUrl.startsWith('/')) {
        destination = returnUrl;
      }

      context.go(destination);
    } else if (mounted) {
      setState(() {
        _error = authProvider.errorMessage ?? 'Authentication failed';
        _isProcessing = false;
      });
    }
  } catch (e) {
    if (mounted) {
      setState(() {
        _error = 'Failed to process authentication: ${e.toString()}';
        _isProcessing = false;
      });
    }
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| localStorage for returnUrl | sessionStorage | Best practice | sessionStorage auto-clears on tab close |
| redirect hardcoded to /home | returnUrl query parameter | GoRouter 6.0+ | Standard pattern for auth flows |
| dart:html | package:web | Flutter 3.35+ Wasm prep | dart:html still works, package:web is future |

**Deprecated/outdated:**
- `dart:js` for JavaScript interop: Use `dart:js_interop` for future Wasm compatibility
- `window.localStorage` for session data: Use `sessionStorage` for ephemeral data

## Open Questions

Things that couldn't be fully resolved:

1. **Mobile platform returnUrl storage**
   - What we know: sessionStorage is web-only; mobile OAuth redirects differently
   - What's unclear: Does mobile OAuth flow need returnUrl preservation? (Deep links work differently)
   - Recommendation: Implement web-only for now; mobile can use in-memory or SharedPreferences with TTL if needed

2. **Wasm compatibility of dart:html**
   - What we know: dart:html won't work with WebAssembly; package:web is the future
   - What's unclear: When Wasm becomes default for Flutter web
   - Recommendation: Use dart:html now (works, simpler); migrate to package:web in future phase if needed

3. **CallbackScreen vs GoRouter redirect for final navigation**
   - What we know: GoRouter redirect doesn't have access to sessionStorage directly
   - What's unclear: Whether to read sessionStorage in redirect (requires service injection) or in CallbackScreen
   - Recommendation: Handle in CallbackScreen - simpler, already handles token extraction

## Sources

### Primary (HIGH confidence)
- [GoRouter pub.dev](https://pub.dev/packages/go_router) - Version 17.0.1, redirect patterns
- [GoRouter Redirection docs](https://pub.dev/documentation/go_router/latest/topics/Redirection-topic.html) - Official redirect patterns
- [dart:html sessionStorage](https://api.flutter.dev/flutter/dart-html/Window/sessionStorage.html) - Browser storage API
- Existing codebase: `frontend/lib/main.dart`, `frontend/lib/providers/auth_provider.dart`, `frontend/lib/screens/auth/callback_screen.dart`

### Secondary (MEDIUM confidence)
- [GitHub Issue #137602](https://github.com/flutter/flutter/issues/137602) - Query parameters lost during redirect
- [GitHub Issue #137721](https://github.com/flutter/flutter/issues/137721) - Query params in redirection
- [Local & Session Storage in flutter web - GitHub Gist](https://gist.github.com/sky1095/f2689ce58ba1c4957342aed3b7387971) - sessionStorage code example
- Prior v1.7 research: `.planning/research/ARCHITECTURE-v1.7-deep-linking.md`, `.planning/research/PITFALLS-v1.7-deep-linking.md`

### Tertiary (LOW confidence)
- [Flutter Go Router: The Crucial Guide](https://medium.com/@vimehraa29/flutter-go-router-the-crucial-guide-41dc615045bb) - Community patterns
- [JavaScript interoperability - Dart](https://dart.dev/interop/js-interop) - Future dart:js_interop patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing packages, well-documented APIs
- Architecture: HIGH - Follows established GoRouter patterns from prior research
- Pitfalls: HIGH - Identified in prior v1.7 research, verified with GitHub issues

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (GoRouter is "feature-complete", stable patterns)

---

## Implementation Checklist (For Planner)

Phase 16 should implement:

1. **Create UrlStorageService** - sessionStorage wrapper for returnUrl
2. **Extend GoRouter redirect logic** - Capture and forward returnUrl through splash/login
3. **Update LoginScreen** - Store returnUrl to sessionStorage before OAuth redirect
4. **Update CallbackScreen** - Retrieve returnUrl from sessionStorage, navigate there
5. **Clear returnUrl after navigation** - Prevent stale redirects
6. **Validate returnUrl** - Security: reject external URLs, malformed paths
7. **Handle edge cases** - Direct login (no returnUrl), invalid returnUrl, expired session

**No package installations needed.**
**Backend: No changes required** - Frontend-only feature.

---

## Requirements Traceability

| Requirement | Implementation |
|-------------|----------------|
| URL-01: Page refresh preserves current URL for authenticated users | Redirect captures URL, passes through splash as returnUrl |
| URL-02: URL preserved through OAuth redirect via session storage | UrlStorageService stores/retrieves from sessionStorage |
| URL-03: Settings page refresh returns to `/settings` | Redirect logic captures `/settings`, preserves through auth check |
| URL-04: Project detail refresh returns to `/projects/:id` | Redirect logic captures full URI including path params |
| AUTH-01: Auth redirect captures intended destination as `returnUrl` query parameter | Redirect appends `?returnUrl=` to login URL |
| AUTH-02: Login completes to stored `returnUrl` instead of `/home` | CallbackScreen reads from sessionStorage, navigates there |
| AUTH-03: Direct login (no returnUrl) goes to `/home` | CallbackScreen defaults to `/home` when no returnUrl |
| AUTH-04: `returnUrl` cleared from session storage after successful navigation | UrlStorageService.clearReturnUrl() called in CallbackScreen |
