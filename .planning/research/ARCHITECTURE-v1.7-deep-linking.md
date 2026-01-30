# Architecture: Deep Linking Integration with GoRouter

**Milestone:** v1.7 - URL & Deep Linking
**Researched:** 2026-01-31
**Confidence:** HIGH (based on existing codebase analysis + official GoRouter patterns)

---

## Executive Summary

This document defines how URL preservation and deep linking should integrate with the existing GoRouter redirect logic and OAuth authentication flow. The current architecture already uses `refreshListenable` with `AuthProvider` for reactive routing, providing an excellent foundation for adding URL preservation.

**Key insight:** GoRouter's redirect function receives `state.matchedLocation`, which contains the intended URL. By passing this as a query parameter to the login route (`/login?returnUrl=/projects/123/threads/456`), the URL survives the authentication flow and can be restored after OAuth completes.

---

## Current Architecture Analysis

### Existing Router Configuration (main.dart:146-267)

```dart
GoRouter(
  initialLocation: '/splash',
  redirect: (context, state) {
    // Current flow:
    // 1. If loading auth → redirect to /splash
    // 2. If authenticated on splash/login → redirect to /home
    // 3. If not authenticated on protected route → redirect to /login
    // 4. Callback handling → redirect to /home when authenticated
  },
  refreshListenable: authProvider,  // Re-evaluates redirect on auth state change
)
```

**Current Problem:**
- Line 165: `if (isAuthenticated && (isSplash || isLogin)) { return '/home'; }`
- Line 184: `if (!isAuthenticated && !isLoading && !isSplash && !isLogin && !isCallback) { return '/login'; }`
- **No URL preservation** - original intended URL is lost

### Authentication Flow

```
User navigates to /projects/123/threads/456
         │
         ▼
┌─────────────────────────────┐
│  GoRouter redirect fires    │
│  isLoading=true             │
│  → redirect to /splash      │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SplashScreen calls         │
│  checkAuthStatus()          │
└─────────────────────────────┘
         │
         ├─────── Token valid ─────► AuthState.authenticated
         │                                    │
         │                                    ▼
         │                          /home (URL LOST!)
         │
         └─────── Token invalid ───► AuthState.unauthenticated
                                              │
                                              ▼
                                    /login (URL LOST!)
```

---

## Proposed Architecture

### Data Flow with URL Preservation

```
User navigates to /projects/123/threads/456
         │
         ▼
┌─────────────────────────────┐
│  GoRouter redirect fires    │
│  Store: returnUrl           │
│  → /splash?returnUrl=...    │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SplashScreen calls         │
│  checkAuthStatus()          │
│  Preserves returnUrl        │
└─────────────────────────────┘
         │
         ├─────── Token valid ────► Read returnUrl
         │                         Navigate to original URL
         │
         └─────── Token invalid ──► /login?returnUrl=...
                                              │
                                              ▼
                                   User completes OAuth
                                              │
                                              ▼
                                   /auth/callback?token=...
                                              │
                                              ▼
                                   Read returnUrl from storage
                                   Navigate to original URL
```

### URL Storage Strategy

**Recommended: Hybrid Approach (Query Parameter + Session Storage)**

| Storage Method | Pros | Cons | Use Case |
|----------------|------|------|----------|
| Query Parameter | Survives page refresh, shareable | Visible in URL, limited length | Short URLs, non-sensitive routes |
| Session Storage | Hidden, survives OAuth redirect | Lost on new tab/browser close | OAuth flow preservation |
| SharedPreferences | Persists across sessions | Overkill for short-term storage | Not recommended |

**Implementation Decision:**

1. **Query parameter for splash/login transitions** - Keeps URL visible for debugging
2. **Session storage for OAuth callback** - Required because OAuth redirects clear query params

```dart
// Pattern for splash/login
'/splash?returnUrl=${Uri.encodeComponent(state.matchedLocation)}'

// Pattern for OAuth callback
// Store in session storage before OAuth redirect
// Retrieve after callback
```

### Component Changes

#### 1. main.dart - Router Redirect Logic

**Location:** `_createRouter()` method (lines 146-267)

**Changes:**

```dart
redirect: (context, state) {
  final isAuthenticated = authProvider.isAuthenticated;
  final isLoading = authProvider.isLoading;
  final currentPath = state.matchedLocation;
  final queryParams = state.uri.queryParameters;

  // Extract existing returnUrl or use current protected route
  final returnUrl = queryParams['returnUrl'] ??
    (_isProtectedRoute(currentPath) ? currentPath : null);

  // Public routes that don't need returnUrl
  final isSplash = currentPath == '/splash';
  final isLogin = currentPath == '/login';
  final isCallback = currentPath == '/auth/callback';

  // Callback: redirect to returnUrl or /home when authenticated
  if (isCallback && isAuthenticated) {
    return returnUrl ?? '/home';
  }

  // Authenticated on splash/login: go to returnUrl or /home
  if (isAuthenticated && (isSplash || isLogin)) {
    return returnUrl ?? '/home';
  }

  // Loading: redirect to splash, preserving returnUrl
  if (isLoading && !isSplash && !isLogin && !isCallback) {
    return _buildUrlWithReturn('/splash', returnUrl);
  }

  // Not authenticated: redirect to login, preserving returnUrl
  if (!isAuthenticated && !isLoading && !isSplash && !isLogin && !isCallback) {
    return _buildUrlWithReturn('/login', returnUrl);
  }

  return null;
}

// Helper methods
bool _isProtectedRoute(String path) {
  return path.startsWith('/home') ||
         path.startsWith('/projects') ||
         path.startsWith('/settings');
}

String _buildUrlWithReturn(String base, String? returnUrl) {
  if (returnUrl == null) return base;
  return '$base?returnUrl=${Uri.encodeComponent(returnUrl)}';
}
```

#### 2. auth_provider.dart - Return URL State

**Location:** `AuthProvider` class

**Changes:**

```dart
class AuthProvider extends ChangeNotifier {
  // ... existing fields ...

  /// Stored return URL for post-auth navigation
  String? _returnUrl;

  /// Get/set return URL for post-authentication redirect
  String? get returnUrl => _returnUrl;

  void setReturnUrl(String? url) {
    _returnUrl = url;
  }

  void clearReturnUrl() {
    _returnUrl = null;
  }

  /// Handle OAuth callback with optional return URL
  Future<void> handleCallback(String token, {String? returnUrl}) async {
    _returnUrl = returnUrl;
    // ... existing handleCallback logic ...
  }
}
```

#### 3. callback_screen.dart - Return URL Handling

**Location:** `_processCallback()` method

**Changes:**

```dart
Future<void> _processCallback() async {
  final uri = GoRouterState.of(context).uri;
  final token = uri.queryParameters['token'];

  // Retrieve returnUrl from session storage (set before OAuth redirect)
  final returnUrl = await _getReturnUrlFromStorage();

  if (token != null && token.isNotEmpty) {
    await authProvider.handleCallback(token, returnUrl: returnUrl);
    // Clear stored returnUrl after use
    await _clearReturnUrlFromStorage();
  }
}
```

#### 4. auth_service.dart - Session Storage Integration

**New methods for web session storage:**

```dart
import 'dart:html' as html;

class AuthService {
  // ... existing code ...

  /// Store return URL in session storage before OAuth redirect
  void storeReturnUrl(String url) {
    html.window.sessionStorage['auth_return_url'] = url;
  }

  /// Retrieve return URL from session storage
  String? getReturnUrl() {
    return html.window.sessionStorage['auth_return_url'];
  }

  /// Clear return URL from session storage
  void clearReturnUrl() {
    html.window.sessionStorage.remove('auth_return_url');
  }
}
```

**Note:** For non-web platforms (mobile), use SharedPreferences with a short TTL or in-memory storage.

#### 5. New Routes for Threads

**Location:** `StatefulShellBranch` for Projects (main.dart)

```dart
StatefulShellBranch(
  routes: [
    GoRoute(
      path: '/projects',
      builder: (context, state) => const ProjectListScreen(),
      routes: [
        GoRoute(
          path: ':id',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return ProjectDetailScreen(projectId: id);
          },
          routes: [
            // NEW: Thread routes
            GoRoute(
              path: 'threads/:threadId',
              builder: (context, state) {
                final projectId = state.pathParameters['id']!;
                final threadId = state.pathParameters['threadId']!;
                return ConversationScreen(
                  projectId: projectId,
                  threadId: threadId,
                );
              },
            ),
          ],
        ),
      ],
    ),
  ],
),
```

---

## Build Order (Dependencies)

The following sequence ensures each change builds on stable foundations:

### Phase 1: Foundation (No UI Changes)

**1.1 Add URL preservation to redirect logic**
- Modify redirect function to capture and forward `returnUrl`
- Add helper methods `_isProtectedRoute()` and `_buildUrlWithReturn()`
- Test: Navigate to protected route while logged out → see `returnUrl` in login URL

**1.2 Add returnUrl state to AuthProvider**
- Add `_returnUrl` field and accessors
- No functional change yet - just state storage

### Phase 2: OAuth Flow Integration

**2.1 Add session storage utilities to AuthService**
- Platform-conditional: `dart:html` for web, SharedPreferences for mobile
- Methods: `storeReturnUrl()`, `getReturnUrl()`, `clearReturnUrl()`

**2.2 Update login screen to store returnUrl before OAuth**
- Extract `returnUrl` from query parameters
- Store in session storage before launching OAuth URL

**2.3 Update callback screen to restore returnUrl**
- Retrieve from session storage after OAuth
- Pass to AuthProvider.handleCallback()
- Navigate to returnUrl instead of /home

### Phase 3: New Thread Routes

**3.1 Define thread route structure**
- Add nested route: `/projects/:id/threads/:threadId`
- Update ConversationScreen to accept both projectId and threadId

**3.2 Update thread navigation**
- Replace `Navigator.push()` in ThreadListScreen with `context.go()`
- Ensure breadcrumbs work with new URL structure

### Phase 4: Edge Cases & Error Handling

**4.1 Invalid route handling (404)**
- Add error route in GoRouter
- Handle missing project/thread IDs gracefully

**4.2 Expired/invalid returnUrl**
- Validate returnUrl format before redirect
- Fall back to /home for malformed URLs
- Clear stale returnUrls after timeout

---

## Component Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                         GoRouter                                 │
│  - Central redirect logic                                        │
│  - URL parsing and preservation                                  │
│  - Route definitions                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  AuthProvider   │  │  AuthService    │  │  Screens        │
│  - Auth state   │  │  - Token mgmt   │  │  - Display      │
│  - returnUrl    │  │  - Session      │  │  - User input   │
│    state        │  │    storage      │  │  - Navigation   │
│  - Notifies     │  │  - OAuth flow   │  │    triggers     │
│    router       │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Responsibility Matrix

| Component | Owns | Does NOT Own |
|-----------|------|--------------|
| GoRouter redirect | URL parsing, redirect decisions | Token validation, auth state |
| AuthProvider | Auth state, user info, returnUrl | HTTP calls, token storage |
| AuthService | Token storage, session storage | Auth state notification |
| SplashScreen | Triggering auth check | Navigation decisions |
| LoginScreen | OAuth button clicks | returnUrl extraction |
| CallbackScreen | Token extraction from URL | Redirect decisions |

---

## Error Scenarios

### Invalid Route (404)

**Scenario:** User navigates to `/projects/invalid-uuid/threads/also-invalid`

**Handling:**
```dart
GoRouter(
  errorBuilder: (context, state) {
    return NotFoundScreen(attemptedPath: state.matchedLocation);
  },
)
```

**Plus screen-level validation:**
```dart
// In ProjectDetailScreen
if (provider.error?.contains('not found') ?? false) {
  return NotFoundState(
    message: 'Project not found',
    suggestion: 'Return to projects list',
    onAction: () => context.go('/projects'),
  );
}
```

### Stale returnUrl

**Scenario:** User bookmarks `/login?returnUrl=/projects/123` but project 123 was deleted

**Handling:**
- Navigate to returnUrl as normal
- ProjectDetailScreen shows error state with "Project not found"
- User can navigate away normally

### OAuth Callback Without returnUrl

**Scenario:** Session storage cleared during OAuth flow (user cleared browser data)

**Handling:**
```dart
final returnUrl = await _getReturnUrlFromStorage();
// Default to /home if no returnUrl stored
authProvider.handleCallback(token, returnUrl: returnUrl ?? '/home');
```

---

## Testing Scenarios

### Manual Test Cases

| Scenario | Steps | Expected |
|----------|-------|----------|
| Fresh login | Navigate to `/projects/abc/threads/xyz` while logged out | After login, land on `/projects/abc/threads/xyz` |
| Page refresh | Login, navigate to thread, press F5 | Return to same thread URL |
| Direct URL | Paste `/projects/abc/threads/xyz` into address bar | If logged in, see thread. If not, login then see thread |
| Invalid route | Navigate to `/projects/doesnotexist` | 404 or "Project not found" state |
| Logout and back | On thread, logout, login again | Default to /home (no returnUrl preserved across logout) |

### Automated Test Strategy

```dart
// Router redirect tests
testWidgets('preserves returnUrl on auth redirect', (tester) async {
  // Given: User not authenticated
  // When: Navigate to /projects/123
  // Then: URL becomes /login?returnUrl=%2Fprojects%2F123
});

testWidgets('restores returnUrl after authentication', (tester) async {
  // Given: User on /login?returnUrl=/projects/123
  // When: Authentication completes
  // Then: Navigate to /projects/123
});
```

---

## Migration Considerations

### Backward Compatibility

**Existing bookmarks:** Users may have bookmarked `/home` or `/projects`. These will continue to work.

**Shared links:** Current URLs like `/projects/abc` work. New URLs like `/projects/abc/threads/xyz` are additive.

### Breaking Changes

**ConversationScreen signature:** Currently takes only `threadId`. Will need `projectId` for URL structure.

```dart
// Before
ConversationScreen(threadId: threadId)

// After
ConversationScreen(projectId: projectId, threadId: threadId)
```

**ThreadListScreen navigation:** Currently uses `Navigator.push()`. Must change to `context.go()` for URL sync.

```dart
// Before (thread_list_screen.dart:47-54)
void _onThreadTap(String threadId) {
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => ConversationScreen(threadId: threadId),
    ),
  );
}

// After
void _onThreadTap(String threadId) {
  context.go('/projects/${widget.projectId}/threads/$threadId');
}
```

---

## Sources

- [go_router | Flutter package](https://pub.dev/packages/go_router) - Official GoRouter documentation
- [Flutter Authentication Flow with Go Router and Provider](https://blog.ishangavidusha.com/flutter-authentication-flow-with-go-router-and-provider) - Auth redirect patterns
- [Deep linking topic - Dart API](https://pub.dev/documentation/go_router/latest/topics/Deep%20linking-topic.html) - GoRouter deep linking reference
- [Flutter Deep Linking: The Ultimate Guide](https://codewithandrea.com/articles/flutter-deep-links/) - Comprehensive deep linking patterns
- Existing codebase: `frontend/lib/main.dart`, `frontend/lib/providers/auth_provider.dart`

---

## Summary

The existing GoRouter + AuthProvider architecture provides a solid foundation. URL preservation requires:

1. **Capture** intended URL in redirect logic via `state.matchedLocation`
2. **Preserve** URL through query parameter (`?returnUrl=...`)
3. **Store** URL in session storage before OAuth redirect
4. **Restore** URL after OAuth callback completes
5. **Navigate** to preserved URL instead of hardcoded `/home`

Build order ensures stable incremental changes: redirect logic first, then OAuth integration, then new routes.
