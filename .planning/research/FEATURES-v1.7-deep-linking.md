# Feature Landscape: Deep Linking & URL Preservation

**Domain:** Flutter web/mobile SaaS application deep linking
**Researched:** 2026-01-31
**Confidence:** HIGH (verified with official Flutter docs, go_router documentation, and industry patterns)

---

## Table Stakes

Features users expect from a professional web application. Missing any of these makes the app feel incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **URL reflects current page** | Users see URL in browser; it must match what they're viewing | Low | Basic go_router route definition |
| **Refresh preserves location** | Web users instinctively refresh; losing context is unacceptable | Medium | Requires storing/restoring intended URL through auth flow |
| **Bookmarkable URLs** | Users bookmark pages in all web apps | Low | Follows from correct route structure |
| **Back/forward navigation** | Browser buttons must work; violating this breaks mental model | Low | go_router handles via History API |
| **Auth redirect to intended destination** | Standard SaaS pattern; users expect to land where they tried to go | Medium | Query parameter pattern (`?returnUrl=`) |
| **404 handling for invalid routes** | Users manually edit URLs, follow stale links, access deleted resources | Medium | Custom error page with navigation options |
| **Hierarchical URL structure** | URLs should reflect app hierarchy (`/projects/:id/threads/:id`) | Low | Nested routes in go_router |
| **Clean URLs (no hash)** | Hash-based URLs (`/#/`) look unprofessional; path-based is standard | Low | Already using `usePathUrlStrategy()` |

### Table Stakes Detail

#### 1. URL Reflects Current Page

**What users expect:** When viewing a conversation, the URL shows `/projects/123/threads/456`, not `/projects/123` or `/home`.

**Current gap:** Thread navigation uses `Navigator.push()` which doesn't update the URL.

**Standard pattern:**
```
/projects              - Project list
/projects/:id          - Project detail (with tabs)
/projects/:id/threads/:id  - Conversation view
/settings              - Settings page
```

#### 2. Refresh Preserves Location

**What users expect:** F5 or browser refresh returns to the same page.

**Current gap:** App uses `initialLocation: '/splash'` which redirects all refreshes to `/home`.

**Standard pattern:** Store intended URL, restore after auth check completes.

#### 3. Auth Redirect with Return URL

**What users expect:** If session expires while deep in the app, login returns them to where they were.

**Standard pattern:**
```
/login?returnUrl=%2Fprojects%2F123%2Fthreads%2F456
```

After successful OAuth, decode and redirect to the return URL.

#### 4. 404 Handling

**What users expect:** Invalid URLs show a clear error with navigation options, not a crash or blank screen.

**Types of 404s:**
- Route doesn't exist in router (e.g., `/foo/bar`)
- Route exists but resource doesn't (e.g., `/projects/999` for deleted project)
- Route exists but user lacks access (show 404, not 403, for security)

**Standard pattern:** Custom 404 page with:
- Clear "Not Found" message
- Explanation of what might have happened
- Button to go home or back

---

## Differentiators

Features that set the product apart. Not strictly expected, but create competitive advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Copy current URL button** | One-tap sharing of exact location | Low | Clipboard API, shown in AppBar |
| **Smart redirect after login** | Remember scroll position, tab state, not just URL | High | Requires state serialization |
| **URL-based state (query params)** | Tab selection, filters in URL (`?tab=threads`) | Medium | Enables sharing specific views |
| **Loading skeletons during navigation** | Perceived performance during deep link resolution | Medium | Already have skeleton patterns |
| **Mobile deep links** | Native app opens from shared URLs | High | Requires app_links, platform config |
| **Thread preview in shared links** | Link previews show conversation context (Open Graph) | Medium | Backend metadata endpoint |

### Differentiator Detail

#### Copy Current URL Button

**Value:** Users can share their exact location with one tap without manually copying from address bar (especially useful on mobile web).

**Implementation:** Add share/copy icon to AppBar that copies current URL to clipboard.

#### URL-Based State (Query Parameters)

**Value:** Shareable links to specific views within a page.

**Examples:**
```
/projects/123?tab=documents   - Opens Documents tab
/projects/123?tab=threads     - Opens Threads tab
/settings?section=appearance  - Opens appearance section
```

**When to use:** Only for user-shareable state. Internal UI state (drawer open/closed) stays out of URL.

#### Mobile Deep Links (Future)

**Value:** Shared URLs open directly in native app if installed.

**Requirements:**
- HTTPS links (not custom schemes)
- `assetlinks.json` for Android
- `apple-app-site-association` for iOS
- `app_links` package (replaces deprecated `uni_links`)

**Note:** Deferred to post-v1.7. Web-first app; native deep linking is enhancement.

---

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Custom URL scheme (baassistant://)** | Insecure, unprofessional, any app can steal it | Use HTTPS links only |
| **URL contains sensitive data** | Exposes info in browser history, logs | Use IDs, not names/content |
| **Route guessing from URL** | Users try `/admin`, `/api`, etc. | Explicit 404 for undefined routes |
| **Silent redirect on 404** | Users confused about what happened | Show clear error state |
| **Auth state in URL** | Token in URL is security risk | Use HTTP-only cookies, session |
| **Deep linking without auth check** | Direct URL access bypasses security | Auth check on every route |
| **Exposing entity existence** | 403 reveals resource exists | Return 404 for unauthorized |
| **Hash-based URLs for new apps** | Legacy pattern, looks unprofessional | Path-based (`usePathUrlStrategy`) |
| **Over-engineering URL structure** | `/app/v1/user/projects/...` | Clean hierarchy matching user mental model |

### Anti-Feature Detail

#### Custom URL Scheme (baassistant://)

**Why it's tempting:** Easy to set up, works without a web server.

**Why it's wrong:**
- Any app can register the same scheme and intercept your links
- Looks unprofessional to users
- Doesn't fall back to website if app not installed
- Search engines can't index

**Right approach:** HTTPS links (`https://app.example.com/projects/123`)

#### URL Contains Sensitive Data

**Bad patterns:**
```
/search?query=confidential%20salary%20data
/projects/my-secret-project-name
/threads/full-thread-title-with-client-names
```

**Right approach:**
```
/projects/abc123           - UUIDs or opaque IDs
/threads/def456            - No semantic meaning in URL
```

#### Exposing Entity Existence (403 vs 404)

**Security issue:** If `/projects/999` returns 403 but `/projects/998` returns 404, an attacker learns project 999 exists.

**Right approach:** Return 404 for both "doesn't exist" and "you can't access it". Already implemented in backend (`Return 404 for non-owner` key decision).

---

## Feature Dependencies

```
URL Reflects Current Page
    |
    v
Refresh Preserves Location
    |
    +--> Auth Redirect with Return URL
    |
    v
Bookmarkable URLs
    |
    +--> Copy Current URL Button (differentiator)
    |
    v
404 Handling
    |
    v
[Mobile Deep Links - future]
```

**Critical path:** Without correct route structure, nothing else works. Route structure is the foundation.

---

## MVP Recommendation (v1.7)

For this milestone, prioritize all table stakes:

### Must Have (v1.7)
1. **Unique conversation URLs** - `/projects/:id/threads/:id` route
2. **URL preservation on refresh** - Store/restore intended URL
3. **Auth redirect with return URL** - Query parameter pattern
4. **404 error states** - Custom page for invalid routes/resources

### Nice to Have (v1.7)
- **Copy URL button** - Low effort, high value
- **Tab state in URL** - Query params for project detail tabs

### Defer to v2.0
- **Mobile deep links** - Requires platform configuration, testing
- **Link previews (Open Graph)** - Backend work, low priority
- **Smart redirect (scroll/state)** - Complex, diminishing returns

---

## Implementation Patterns

### Pattern 1: Nested GoRoute Structure

```dart
// Correct: Hierarchical routes reflecting resource ownership
GoRoute(
  path: '/projects',
  builder: (_, __) => ProjectListScreen(),
  routes: [
    GoRoute(
      path: ':projectId',
      builder: (_, state) => ProjectDetailScreen(
        projectId: state.pathParameters['projectId']!,
      ),
      routes: [
        GoRoute(
          path: 'threads/:threadId',
          builder: (_, state) => ConversationScreen(
            projectId: state.pathParameters['projectId']!,
            threadId: state.pathParameters['threadId']!,
          ),
        ),
      ],
    ),
  ],
),
```

### Pattern 2: Return URL via Query Parameter

```dart
// Redirect to login with return URL
redirect: (context, state) {
  if (!isAuthenticated && !isLogin && !isCallback) {
    final returnUrl = Uri.encodeComponent(state.matchedLocation);
    return '/login?returnUrl=$returnUrl';
  }

  // After auth, redirect to return URL
  if (isAuthenticated && isLogin) {
    final returnUrl = state.uri.queryParameters['returnUrl'];
    return returnUrl != null ? Uri.decodeComponent(returnUrl) : '/home';
  }
  return null;
}
```

### Pattern 3: 404 Error Page

```dart
// In GoRouter config
errorBuilder: (context, state) => NotFoundScreen(
  attemptedPath: state.uri.path,
),

// NotFoundScreen widget
class NotFoundScreen extends StatelessWidget {
  final String attemptedPath;

  Widget build(context) {
    return Scaffold(
      body: Center(
        child: Column(
          children: [
            Icon(Icons.error_outline, size: 64),
            Text('Page not found'),
            Text('Could not find: $attemptedPath'),
            ElevatedButton(
              onPressed: () => context.go('/home'),
              child: Text('Go Home'),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Pattern 4: Resource Not Found Handling

```dart
// In screen that loads resource
class ConversationScreen extends StatefulWidget {
  Future<void> _loadThread() async {
    try {
      final thread = await threadService.getThread(widget.threadId);
      setState(() => _thread = thread);
    } on NotFoundException {
      setState(() => _notFound = true);
    }
  }

  Widget build(context) {
    if (_notFound) {
      return ResourceNotFoundWidget(
        resourceType: 'Thread',
        onBack: () => context.go('/projects/${widget.projectId}'),
      );
    }
    // ... normal build
  }
}
```

---

## Sources

### Official Documentation (HIGH confidence)
- [Flutter Deep Linking](https://docs.flutter.dev/ui/navigation/deep-linking)
- [go_router Package](https://pub.dev/packages/go_router)
- [Flutter URL Strategies](https://docs.flutter.dev/ui/navigation/url-strategies)
- [Set up App Links for Android](https://docs.flutter.dev/cookbook/navigation/set-up-app-links)
- [Set up Universal Links for iOS](https://docs.flutter.dev/cookbook/navigation/set-up-universal-links)

### Community Best Practices (MEDIUM confidence)
- [Flutter Authentication Flow with Go Router](https://blog.ishangavidusha.com/flutter-authentication-flow-with-go-router-and-provider)
- [Advanced Navigation in Flutter Web with Go Router](https://geekyants.com/blog/advanced-navigation-in-flutter-web-a-deep-dive-with-go-router)
- [Best Practices for Flutter Routing 2025](https://teachmeidea.com/flutter-routing-deep-linking-best-practices-2025/)

### SaaS UX Standards (MEDIUM confidence)
- [Navigation UX Best Practices for SaaS](https://www.pencilandpaper.io/articles/ux-pattern-analysis-navigation)
- [SaaS UX Design Best Practices 2025](https://mouseflow.com/blog/saas-ux-design-best-practices/)

### Industry Examples (MEDIUM confidence)
- [Slack Deep Linking Documentation](https://docs.slack.dev/interactivity/deep-linking/)
- [Handling 404 in Flutter](https://medium.com/flutter/handling-404-page-not-found-error-in-flutter-731f5a9fba29)

---

*Researched for BA Assistant v1.7 milestone*
