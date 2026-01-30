# Technology Stack: Deep Linking for BA Assistant

**Project:** BA Assistant v1.7 - Deep Linking & URL Preservation
**Researched:** 2026-01-31
**Overall Confidence:** HIGH

---

## Executive Summary

The existing stack (GoRouter 17.0.1, Flutter 3.9+, path URL strategy) already provides everything needed for deep linking. **No additional packages required.** The work is primarily configuration and pattern implementation, not technology adoption.

---

## Current Stack Assessment

### Already In Place (No Changes Needed)

| Technology | Version | Status | Notes |
|------------|---------|--------|-------|
| go_router | ^17.0.1 | KEEP | Full deep linking support built-in |
| flutter_web_plugins | SDK | KEEP | `usePathUrlStrategy()` already configured in main.dart |
| provider | ^6.1.5+1 | KEEP | `refreshListenable` pattern already working |

### Key Observations from Codebase

1. **Path URL strategy already enabled** - `usePathUrlStrategy()` called in `main.dart` line 74
2. **Router created correctly** - Instance created outside build(), stored in `_routerInstance` (lines 96-97)
3. **Auth redirect pattern exists** - Using `refreshListenable: authProvider` (line 265)
4. **StatefulShellRoute configured** - Branch-based navigation already working
5. **Android deep link configured** - Custom scheme `com.baassistant://auth/callback` exists
6. **iOS URL scheme configured** - `com.baassistant` scheme in Info.plist

---

## Recommended Stack (What to Add)

### No New Packages Needed

**Recommendation:** Do NOT add `app_links` package.

**Rationale:**
- GoRouter handles deep linking automatically for web
- The app already uses GoRouter's redirect system for auth
- `app_links` is only needed when you want to preserve navigation stack on deep link - this app starts fresh on deep link (acceptable for URL sharing use case)
- Adding `app_links` requires disabling Flutter's default deep link handler, adding complexity

### Configuration Changes Only

| Change | Location | Purpose |
|--------|----------|---------|
| Add thread routes | `main.dart` | Enable `/projects/:projectId/threads/:threadId` URLs |
| Add errorBuilder | `main.dart` | Handle 404/invalid routes gracefully |
| Extend redirect logic | `main.dart` | Preserve return URL for auth redirects |
| Server config | Deployment | Support path-based URLs on refresh |

---

## Platform-Specific Setup

### Web (Primary Platform)

**Status:** Mostly configured, needs server setup for production.

**Current State:**
- `usePathUrlStrategy()` already enabled
- `<base href="$FLUTTER_BASE_HREF">` in index.html (correct)

**Required for Production:**
```
Server must rewrite all paths to index.html for SPA routing.

For Firebase Hosting (firebase.json):
{
  "hosting": {
    "rewrites": [
      { "source": "**", "destination": "/index.html" }
    ]
  }
}

For Nginx:
location / {
  try_files $uri $uri/ /index.html;
}
```

**Why:** PathUrlStrategy uses the History API. On page refresh, the browser requests the full path from the server (e.g., `/projects/123/threads/456`). Without rewrite rules, the server returns 404 because that file doesn't exist.

### Android

**Current State:** Custom scheme configured for OAuth only.

**For HTTP/HTTPS Deep Links (Optional):**

If you want `https://yourapp.com/projects/123` to open the app:

1. **AndroidManifest.xml** - Add intent filter:
```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data
        android:scheme="https"
        android:host="yourapp.com"
        android:pathPrefix="/projects" />
</intent-filter>
```

2. **Digital Asset Links** - Host `/.well-known/assetlinks.json` on your domain:
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.baassistant.app",
    "sha256_cert_fingerprints": ["YOUR_SHA256_FINGERPRINT"]
  }
}]
```

**Recommendation:** Defer to post-v1.7. Current custom scheme (`com.baassistant://`) works for OAuth. Web URL sharing is the primary use case.

### iOS

**Current State:** Custom scheme configured for OAuth only.

**For Universal Links (Optional):**

If you want `https://yourapp.com/projects/123` to open the app:

1. **Xcode** - Add Associated Domains capability:
```
applinks:yourapp.com
```

2. **Info.plist** - No changes needed (Flutter handles via Associated Domains)

3. **AASA File** - Host at `https://yourapp.com/.well-known/apple-app-site-association`:
```json
{
  "applinks": {
    "apps": [],
    "details": [{
      "appIDs": ["TEAMID.com.baassistant.app"],
      "paths": ["/projects/*", "/projects/*/threads/*"]
    }]
  }
}
```

**Recommendation:** Defer to post-v1.7. Same rationale as Android.

---

## GoRouter Configuration Patterns

### Pattern 1: Nested Routes for Thread URLs

**Goal:** `/projects/:projectId/threads/:threadId`

```dart
StatefulShellBranch(
  routes: [
    GoRoute(
      path: '/projects',
      builder: (context, state) => const ProjectListScreen(),
      routes: [
        GoRoute(
          path: ':projectId',
          builder: (context, state) {
            final id = state.pathParameters['projectId']!;
            return ProjectDetailScreen(projectId: id);
          },
          routes: [
            GoRoute(
              path: 'threads/:threadId',
              builder: (context, state) {
                final projectId = state.pathParameters['projectId']!;
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

**Confidence:** HIGH - This is standard GoRouter nested routing.

### Pattern 2: Auth Redirect with Return URL

**Goal:** Preserve intended destination through login flow.

```dart
redirect: (context, state) {
  final isAuthenticated = authProvider.isAuthenticated;
  final isLoading = authProvider.isLoading;
  final path = state.matchedLocation;

  // Public routes
  final publicRoutes = ['/splash', '/login', '/auth/callback'];
  final isPublic = publicRoutes.contains(path);

  // If not authenticated and trying to access protected route
  if (!isAuthenticated && !isLoading && !isPublic) {
    // Encode the intended destination as query parameter
    final returnUrl = Uri.encodeComponent(state.uri.toString());
    return '/login?returnUrl=$returnUrl';
  }

  // If authenticated and on login with returnUrl, go to that URL
  if (isAuthenticated && path == '/login') {
    final returnUrl = state.uri.queryParameters['returnUrl'];
    if (returnUrl != null) {
      return Uri.decodeComponent(returnUrl);
    }
    return '/home';
  }

  // ... rest of existing redirect logic
  return null;
},
```

**Confidence:** HIGH - Standard pattern documented in GoRouter guides.

### Pattern 3: Error Handling (404 Pages)

**Goal:** Graceful handling of invalid routes.

```dart
GoRouter(
  // ... routes ...
  errorBuilder: (context, state) {
    return Scaffold(
      appBar: AppBar(title: const Text('Page Not Found')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64),
            const SizedBox(height: 16),
            Text('Route not found: ${state.uri.path}'),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go('/home'),
              child: const Text('Go Home'),
            ),
          ],
        ),
      ),
    );
  },
);
```

**Confidence:** HIGH - GoRouter provides this API explicitly for 404 handling.

### Pattern 4: URL Preservation on Refresh

**Goal:** Browser refresh maintains current route.

**Current State:** Already working IF router instance is stable.

**Critical Implementation Detail:**
The router instance MUST be created once and reused. Current code does this correctly:

```dart
class _MyAppState extends State<MyApp> {
  late final GoRouter _routerInstance;  // Created once
  bool _isRouterInitialized = false;

  @override
  Widget build(BuildContext context) {
    // ...
    if (!_isRouterInitialized) {
      _routerInstance = _createRouter(context);  // Only runs once
      _isRouterInitialized = true;
    }
    // ...
  }
}
```

**Confidence:** HIGH - Code already follows the correct pattern per GitHub issue #172026.

---

## What NOT to Use

### Do NOT Add: app_links Package

**Why not:**
- Adds complexity (requires disabling Flutter's default deep link handler)
- Only benefit is preserving navigation stack on deep link
- For URL sharing use case, starting fresh at the deep linked screen is acceptable
- GoRouter already handles the routing

### Do NOT Add: uni_links Package

**Why not:**
- Deprecated in favor of app_links
- Same concerns as app_links

### Do NOT Use: Hash URL Strategy

**Why not:**
- Already using path strategy (correct choice)
- Hash URLs (`/#/projects/123`) look unprofessional
- Path URLs are better for SEO and sharing

### Do NOT Use: GoRouter.onException

**Why not:**
- `errorBuilder` is simpler and sufficient for 404 handling
- `onException` supersedes other error handling, adding complexity
- Only needed for advanced exception handling scenarios

---

## Version Compatibility

| Package | Current | Minimum for Deep Linking | Notes |
|---------|---------|--------------------------|-------|
| go_router | 17.0.1 | 6.0.0+ | Full deep linking support |
| flutter | 3.9+ | 3.0+ | PathUrlStrategy stable |
| flutter_web_plugins | SDK | SDK | Already included |

**No version upgrades needed.**

---

## Sources

### HIGH Confidence (Official Documentation)
- [go_router package](https://pub.dev/packages/go_router) - Version 17.0.1, "feature-complete"
- [Flutter Deep Linking Docs](https://docs.flutter.dev/ui/navigation/deep-linking) - Official Flutter documentation
- [Flutter URL Strategies](https://docs.flutter.dev/ui/navigation/url-strategies) - PathUrlStrategy configuration
- [GoRouter Error Handling](https://pub.dev/documentation/go_router/latest/topics/Error%20handling-topic.html) - errorBuilder API

### MEDIUM Confidence (Verified Community Sources)
- [GitHub Issue #172026](https://github.com/flutter/flutter/issues/172026) - Router recreation URL preservation issue
- [Flutter App Links Setup](https://docs.flutter.dev/cookbook/navigation/set-up-app-links) - Android App Links configuration
- [Flutter Universal Links Setup](https://docs.flutter.dev/cookbook/navigation/set-up-universal-links) - iOS Universal Links configuration

### LOW Confidence (Community Articles - Patterns Only)
- [CodeWithAndrea Deep Links Guide](https://codewithandrea.com/articles/flutter-deep-links/) - Pattern examples
- [Medium: app_links vs go_router](https://medium.com/@pinky.hlaing173/handling-deep-links-in-flutter-without-losing-navigation-using-app-links-over-go-router-45845bc07373) - Tradeoff analysis

---

## Summary: Implementation Checklist

For v1.7 deep linking, implement in this order:

1. **Add thread routes** - Nested GoRoute for `/projects/:id/threads/:threadId`
2. **Add errorBuilder** - 404 page for invalid routes
3. **Extend redirect logic** - `returnUrl` query parameter preservation
4. **Test URL preservation** - Verify browser refresh maintains route
5. **Configure deployment server** - SPA rewrite rules for production

**No new dependencies. No package upgrades. Configuration and patterns only.**

---

## Roadmap Implications

### Phase Structure Recommendation

Based on this research, the v1.7 milestone should be structured as:

**Phase 1: Route Configuration**
- Add nested thread routes to GoRouter
- Update ConversationScreen to accept both projectId and threadId
- Standard GoRouter patterns, low risk

**Phase 2: Error Handling**
- Add errorBuilder for 404 states
- Create NotFoundScreen widget
- Standard pattern, low risk

**Phase 3: Auth Flow Enhancement**
- Extend redirect logic with returnUrl parameter
- Modify login screen to read and use returnUrl
- Medium complexity, requires testing edge cases

**Phase 4: Testing & Validation**
- URL preservation on refresh
- Deep link navigation from external sources
- Auth redirect with return URL
- Invalid route handling

**No phases need deeper research** - all patterns are well-documented in official GoRouter documentation.
