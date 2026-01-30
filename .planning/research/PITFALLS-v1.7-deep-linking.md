# Domain Pitfalls: Deep Linking with GoRouter

**Domain:** Flutter deep linking and URL preservation
**Milestone:** v1.7 Deep Linking & URL Preservation
**Researched:** 2026-01-31
**Overall Confidence:** HIGH (verified with official docs and GitHub issues)

---

## Critical Pitfalls

Mistakes that cause rewrites, user-facing bugs, or fundamental architecture problems.

---

### Pitfall 1: Router Recreation Destroys URL State on Refresh

**What goes wrong:** After navigating to a deep URL (e.g., `/projects/abc123/threads/xyz789`) and refreshing the browser, the app initially loads the correct URL but then redirects to the initial location (`/home`) within 1-2 seconds.

**Why it happens:** The `GoRouter` instance is created inside a widget that rebuilds. When the widget tree rebuilds (e.g., due to theme change, provider update, or hot reload), a new `GoRouter` is instantiated with its `initialLocation`, discarding the current browser URL.

**Your current code is affected:**
```dart
// main.dart lines 114-117
if (!_isRouterInitialized) {
  _routerInstance = _createRouter(context);
  _isRouterInitialized = true;
}
```
This pattern protects against rebuilds but only within the same `_MyAppState` lifecycle. Full page refresh creates a new widget tree entirely.

**Consequences:**
- Deep links work initially but fail after refresh
- Users bookmark URLs that don't work reliably
- OAuth callback returns to wrong page after auth completes
- Conversation URLs cannot be shared (they redirect to home)

**Prevention:**
1. Create `GoRouter` as a top-level `final` variable outside any class
2. Or use a singleton pattern that survives widget rebuilds
3. Never create `GoRouter` inside `build()` methods
4. Test URL refresh explicitly in every PR that touches navigation

**Detection (warning signs):**
- Manual testing: Navigate to nested route, F5 refresh, observe redirect
- Automated: E2E test that loads `/projects/:id` directly and verifies no redirect

**Phase to address:** Phase 1 (Router Architecture) - Must be first, all other features depend on stable URL state

**Sources:**
- [GoRouter does not preserve browser URL if app widget rebuilds](https://github.com/flutter/flutter/issues/172026)
- [Refreshing on nested app loses current route](https://github.com/flutter/flutter/issues/114597)

---

### Pitfall 2: Missing Return URL After OAuth Authentication

**What goes wrong:** User clicks a deep link to `/projects/abc/threads/xyz`, gets redirected to login (correct), authenticates successfully, but lands on `/home` instead of the original intended URL.

**Why it happens:** The redirect logic sends unauthenticated users to `/login` but doesn't preserve the original destination. After authentication, the router only knows the user is authenticated, not where they originally wanted to go.

**Your current code vulnerability:**
```dart
// main.dart lines 184-186
if (!isAuthenticated && !isLoading && !isSplash && !isLogin && !isCallback) {
  return '/login';  // Original URL is lost here!
}
```

**Consequences:**
- Users lose their intended destination after login
- Shared conversation URLs don't work for logged-out users
- OAuth flow disrupts deep link experience
- User frustration when bookmarks require re-navigation after auth

**Prevention:**
1. Store intended location in query parameter: `return '/login?returnUrl=${state.matchedLocation}'`
2. Or use `state.uri.toString()` to capture full path with query params
3. On successful auth, extract `returnUrl` and navigate there instead of hardcoded `/home`
4. Handle URL encoding/decoding for complex paths

**Implementation pattern:**
```dart
// In redirect:
if (!isAuthenticated) {
  final returnUrl = Uri.encodeComponent(state.uri.toString());
  return '/login?returnUrl=$returnUrl';
}

// After auth success:
final returnUrl = state.uri.queryParameters['returnUrl'];
if (returnUrl != null) {
  return Uri.decodeComponent(returnUrl);
}
return '/home';
```

**Detection:**
- Test flow: Copy deep link, open in incognito, login, verify landing page
- Check: Is `returnUrl` parameter present in login URL after redirect?

**Phase to address:** Phase 2 (Auth Flow Integration) - Requires router architecture to be stable first

**Sources:**
- [Redirection topic - Dart API](https://pub.dev/documentation/go_router/latest/topics/Redirection-topic.html)
- [Flutter Authentication Flow with Go Router](https://blog.ishangavidusha.com/flutter-authentication-flow-with-go-router-and-provider)

---

### Pitfall 3: StatefulShellRoute Deep Link Branch Conflict

**What goes wrong:** Deep linking to `/projects/abc123` works, but the navigation stack gets corrupted. User cannot navigate back properly, or switching tabs resets navigation history unexpectedly.

**Why it happens:** `StatefulShellRoute.indexedStack` preserves branch state, but deep links can conflict with this preservation. When a deep link arrives, GoRouter uses `context.go()` semantics which replaces the navigation stack rather than pushing onto it.

**Your current architecture risk:**
```dart
// main.dart lines 207-262
StatefulShellRoute.indexedStack(
  branches: [
    StatefulShellBranch(routes: [/* /home */]),
    StatefulShellBranch(routes: [/* /projects, /projects/:id */]),  // Nested routes
    StatefulShellBranch(routes: [/* /settings */]),
  ],
)
```
Deep linking to `/projects/abc123/threads/xyz789` may not properly establish the back navigation to `/projects/abc123` then `/projects`.

**Consequences:**
- Back button behavior unpredictable after deep link
- Tab switching loses expected navigation history
- User confusion about navigation state
- Potential for getting "stuck" on screens

**Prevention:**
1. Use `parentNavigatorKey` to control which navigator handles routes
2. Test deep link back navigation explicitly
3. Consider `app_links` package for finer control over deep link behavior
4. Ensure nested routes properly chain back navigation

**Detection:**
- Deep link to `/projects/:id/threads/:tid`, press back, verify you go to `/projects/:id` not home
- Switch tabs after deep link, switch back, verify state

**Phase to address:** Phase 1 (Router Architecture) - Must design correct before adding features

**Sources:**
- [Deep Linking Behavior Conflicts with StatefulShellRoute](https://github.com/flutter/flutter/issues/134373)
- [Navigate to StatefulShellBranch while preserving navigation stack](https://github.com/flutter/flutter/issues/142226)

---

### Pitfall 4: iOS Cold Start Deep Link Race Condition

**What goes wrong:** On iOS, deep links opened from a terminated (cold) state first trigger the `initialLocation` ("/") in the redirect method, then the actual deep link path. This causes a flash of wrong content or incorrect redirect behavior.

**Why it happens:** iOS and Android have different deep link delivery timing. On iOS, the app lifecycle means the initial route fires before the platform delivers the deep link intent. GoRouter's redirect sees "/" first, may redirect (e.g., to "/splash"), then receives the actual deep link.

**Consequences:**
- Flash of splash/home screen before correct deep link content
- If redirect logic handles "/" specially, may cause incorrect state
- Different behavior between Android and iOS confuses testing
- Auth redirects may fire prematurely

**Prevention:**
1. Never assume redirect is called only once per navigation
2. Handle the "/" -> actual path transition gracefully
3. Add short delay or loading state to absorb the race
4. Test on actual iOS devices, not just simulator

**Detection:**
- iOS device: Kill app completely, tap deep link, observe initial route handling
- Log redirect calls: `debugLogDiagnostics: true`

**Phase to address:** Phase 4 (Platform Testing) - Requires routes to be implemented first

**Sources:**
- [Deep links route to "/" before expected path on iOS](https://github.com/flutter/flutter/issues/142988)
- [Flutter Deep Linking: The Ultimate Guide](https://codewithandrea.com/articles/flutter-deep-links/)

---

### Pitfall 5: refreshListenable Infinite Redirect Loop

**What goes wrong:** App freezes on splash screen, browser tab becomes unresponsive, or stack overflow errors in console. The redirect callback is being called infinitely.

**Why it happens:** When `refreshListenable` (like `AuthProvider`) notifies listeners, it triggers a redirect evaluation. If the redirect logic has a bug where it returns a path that also triggers a state change (which notifies listeners again), an infinite loop occurs.

**Your current risk:**
```dart
// main.dart line 265
refreshListenable: authProvider,
```
AuthProvider calls `notifyListeners()` in multiple places. If redirect logic isn't perfectly idempotent, loops can occur.

**Common trigger patterns:**
- Redirect returns `/splash` which loads data, which notifies, which redirects to `/splash`...
- Auth check sets loading state, redirect sees loading, sends to splash, auth check runs again...
- Browser extensions (on Flutter Web) can trigger phantom refreshes

**Consequences:**
- App completely unusable
- Browser tab crash
- Users see frozen splash screen
- Hard to reproduce, intermittent in production

**Prevention:**
1. Ensure redirect returns `null` when already at correct location
2. Never trigger `notifyListeners()` from within redirect logic
3. Use `Future.microtask()` for notifications (you already do this - good!)
4. Set `redirectLimit` explicitly and handle the exception gracefully
5. Add defensive checks: `if (state.matchedLocation == targetLocation) return null;`

**Detection:**
- Console shows repeated redirect logs
- Browser DevTools shows CPU spike
- `debugLogDiagnostics: true` shows redirect loop

**Phase to address:** Phase 2 (Auth Flow Integration) - Must be bulletproof before adding more auth complexity

**Sources:**
- [Infinite redirect loops causing stack overflows](https://github.com/flutter/flutter/issues/118061)
- [Push does not correctly update state with refreshListenable](https://github.com/flutter/flutter/issues/162735)

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or degraded experience but are recoverable.

---

### Pitfall 6: Path URL Strategy Requires Server Configuration

**What goes wrong:** App works in development, but in production, refreshing any page except root returns 404 from the server.

**Why it happens:** `usePathUrlStrategy()` creates clean URLs (`/projects/123`) instead of hash URLs (`/#/projects/123`). But the web server sees `/projects/123` as a real server path. When the server doesn't find a file at that path, it returns 404 instead of serving `index.html`.

**Your current usage:**
```dart
// main.dart line 74
usePathUrlStrategy();
```

**Consequences:**
- Production deployment appears broken
- Users cannot share or bookmark URLs
- Refresh breaks the entire app
- SEO benefits of clean URLs lost

**Prevention:**
1. Configure web server to rewrite all paths to `index.html`
2. For Firebase Hosting: set "Configure as single-page app" during init
3. For nginx: `try_files $uri $uri/ /index.html;`
4. For Apache: `.htaccess` with `FallbackResource /index.html`
5. Test production deployment with URL refresh before release

**Detection:**
- Deploy to staging, navigate to nested route, refresh
- Check server response headers for 404

**Phase to address:** Phase 5 (Deployment) - But document requirement in Phase 1

**Sources:**
- [Configuring the URL strategy on the web](https://docs.flutter.dev/ui/navigation/url-strategies)
- [Use of UrlPathStrategy causes 404 on browser refresh](https://github.com/flutter/flutter/issues/107996)

---

### Pitfall 7: No 404 Handling for Invalid Deep Links

**What goes wrong:** User visits `/conversations/invalid-id-12345`, app shows default GoRouter error page or crashes.

**Why it happens:** GoRouter can route to `/conversations/:id`, but the ID doesn't exist in the database. The route matches, but the screen fails to load data. Without proper handling, this shows ugly error states.

**Consequences:**
- Unprofessional error screens shown to users
- No way for users to recover (back to safe state)
- Shared links to deleted content break permanently
- Security: May expose internal error details

**Prevention:**
1. Use `onException` or `errorBuilder` in GoRouter constructor
2. Create a custom 404 screen with navigation back to home
3. Handle "resource not found" at the screen level (not just router level)
4. Distinguish between "route doesn't exist" and "resource doesn't exist"

**Implementation:**
```dart
GoRouter(
  errorBuilder: (context, state) => NotFoundScreen(
    message: 'Page not found: ${state.uri.path}',
    onGoHome: () => context.go('/home'),
  ),
  onException: (context, state, router) {
    // Log the error
    router.go('/404', extra: state.error);
  },
)
```

**Detection:**
- Navigate to `/gibberish/path/that/doesnt/exist`
- Navigate to valid route pattern with invalid ID

**Phase to address:** Phase 3 (URL Implementation for Features) - Part of each feature's error handling

**Sources:**
- [Error handling topic - Dart API](https://pub.dev/documentation/go_router/latest/topics/Error%20handling-topic.html)
- [Navigate to specific route when 404 found](https://github.com/flutter/flutter/issues/108517)

---

### Pitfall 8: URL Fragment/Hash Loss with OAuth

**What goes wrong:** OAuth providers (especially Supabase, Firebase) return tokens in URL fragments (`#access_token=...`). When using `PathUrlStrategy`, the fragment is stripped before Flutter can read it.

**Why it happens:** `PathUrlStrategy` uses the History API which can modify the URL. Somewhere in Navigator 2.0 routing, the fragment gets removed before your app code can access it.

**Your current OAuth flow:**
```dart
// screens/auth/callback_screen.dart handles OAuth callback
// Token extraction happens in this screen
```

**Consequences:**
- OAuth login silently fails (no token received)
- Users stuck in auth loop
- Different behavior between hash and path strategies
- Hard to debug (URL looks normal by the time you check)

**Prevention:**
1. Capture URL fragment immediately in `main()` before router initializes
2. Or use `app_links` package which handles fragments correctly
3. Test OAuth callback with actual provider (not mocked)
4. Store fragment in memory before `usePathUrlStrategy()` runs

**Detection:**
- Complete OAuth flow with real Google/Microsoft accounts
- Log the full URL in callback screen including fragment
- Check if token is present

**Phase to address:** Phase 2 (Auth Flow Integration) - Must verify existing OAuth still works

**Sources:**
- [PathUrlStrategy ignores fragments](https://github.com/flutter/flutter/issues/98933)
- [Deep linking doesn't handle url fragments](https://github.com/flutter/flutter/issues/86292)

---

### Pitfall 9: Back Navigation History Corruption with `go()` vs `push()`

**What goes wrong:** Deep links work, but the browser back button doesn't behave as expected. Pressing back skips pages or goes to unexpected locations.

**Why it happens:** Deep links use `context.go()` semantics which replaces the navigation stack. This is fundamentally different from `context.push()` which adds to the stack. After a deep link, there's no history to go "back" to.

**Consequences:**
- Users expect back button to work like a browser
- Deep link -> back = nothing happens or goes to wrong place
- Breaks mental model of navigation
- Back button may close app entirely instead of navigating

**Prevention:**
1. Use `app_links` package for `push()`-based deep link handling
2. Manually reconstruct navigation stack for deep links (push parent routes first)
3. Handle back gesture at screen level with `WillPopScope`
4. Consider if "back" from deep link should go to parent route or close

**Implementation consideration:**
```dart
// For deep link to /projects/abc/threads/xyz
// Consider pushing: /projects -> /projects/abc -> /projects/abc/threads/xyz
// So back navigation works naturally
```

**Detection:**
- Deep link to nested route, press back, observe behavior
- Check browser history entries after deep link

**Phase to address:** Phase 3 (URL Implementation) - Design decision needed per feature

**Sources:**
- [Flutter Deep Linking: The Ultimate Guide](https://codewithandrea.com/articles/flutter-deep-links/)

---

### Pitfall 10: Query Parameters Lost in Redirect Chain

**What goes wrong:** URL `/projects?filter=active&sort=date` redirects to login, user logs in, lands on `/projects` without the filter and sort parameters.

**Why it happens:** The redirect logic captures `state.matchedLocation` which is just the path, not `state.uri` which includes query parameters. When reconstructing the return URL, only the path is preserved.

**Your current redirect captures only path:**
```dart
// state.matchedLocation = '/projects' (no query params)
// state.uri.toString() = '/projects?filter=active&sort=date'
```

**Consequences:**
- Users lose applied filters after login
- Shared URLs with parameters don't work for logged-out users
- Search URLs, paginated URLs all affected
- Feature appears broken for complex URLs

**Prevention:**
1. Use `state.uri.toString()` instead of `state.matchedLocation` for return URL
2. Properly encode/decode the full URI including query params
3. Test with URLs containing special characters in query params
4. Validate the returnUrl before navigation (security: prevent open redirect)

**Detection:**
- Add `?test=value` to any protected URL, force login, check if preserved
- Check redirect URL in browser address bar

**Phase to address:** Phase 2 (Auth Flow Integration) - Part of return URL implementation

---

## Minor Pitfalls

Annoyances that are easily fixed but good to know about.

---

### Pitfall 11: debugLogDiagnostics Missing in Development

**What goes wrong:** Debugging routing issues is difficult because you can't see what GoRouter is doing.

**Prevention:** Always enable in development:
```dart
GoRouter(
  debugLogDiagnostics: kDebugMode,  // Only in debug builds
  ...
)
```

**Phase to address:** Phase 1 (Router Architecture) - Add immediately

---

### Pitfall 12: Route Path Typos in Deep Link Configuration

**What goes wrong:** Android intent filter says `/projects/:projectId` but GoRouter route says `/projects/:id`. Deep links arrive but don't match.

**Prevention:**
1. Define route paths as constants, use everywhere
2. Generate Android/iOS config from Dart code if possible
3. Integration tests that test deep link -> screen mapping

**Phase to address:** Phase 4 (Platform Configuration) - Part of Android/iOS setup

---

### Pitfall 13: Missing URL Encoding for IDs

**What goes wrong:** Project ID contains special characters (some UUID formats, user-generated IDs), URL breaks or routes incorrectly.

**Prevention:**
1. Always URL-encode path parameters when constructing URLs
2. Always URL-decode when extracting from `state.pathParameters`
3. Validate ID format before database queries

**Phase to address:** Phase 3 (URL Implementation) - Per-feature implementation

---

## Phase-Specific Warnings Summary

| Phase | Topic | Likely Pitfall | Priority |
|-------|-------|----------------|----------|
| Phase 1 | Router Architecture | #1 Router Recreation, #3 StatefulShellRoute Conflict | CRITICAL |
| Phase 1 | Router Architecture | #11 Debug Logging | LOW |
| Phase 2 | Auth Flow | #2 Missing Return URL, #5 Infinite Redirect Loop | CRITICAL |
| Phase 2 | Auth Flow | #8 Fragment Loss, #10 Query Param Loss | HIGH |
| Phase 3 | Feature URLs | #7 No 404 Handling, #9 Back Navigation | MEDIUM |
| Phase 3 | Feature URLs | #13 URL Encoding | LOW |
| Phase 4 | Platform Config | #4 iOS Cold Start, #12 Path Typos | MEDIUM |
| Phase 5 | Deployment | #6 Server Configuration | CRITICAL |

---

## Testing Checklist by Phase

### Phase 1: Router Architecture
- [ ] Create GoRouter outside widget tree (singleton or top-level)
- [ ] Navigate to nested route, refresh browser, verify URL preserved
- [ ] Deep link to branch route, verify back navigation works
- [ ] Enable `debugLogDiagnostics` for development

### Phase 2: Auth Flow Integration
- [ ] Deep link when logged out captures return URL
- [ ] After OAuth callback, verify landing on return URL (not /home)
- [ ] Query parameters preserved through auth redirect
- [ ] No infinite redirect loops (test with slow network)
- [ ] OAuth fragment tokens still work with PathUrlStrategy

### Phase 3: Feature URL Implementation
- [ ] Each feature has working error/404 state
- [ ] Invalid IDs show friendly error, not crash
- [ ] Back navigation from deep link works as expected
- [ ] Special characters in IDs handled correctly

### Phase 4: Platform Configuration
- [ ] Android: Deep links open app, route correctly
- [ ] iOS: Cold start deep links work (no flash of wrong screen)
- [ ] Path patterns match between platform config and router

### Phase 5: Deployment
- [ ] Production server rewrites configured
- [ ] Browser refresh works on all routes
- [ ] Shared links work for new users

---

## Sources Summary

**Official Documentation (HIGH confidence):**
- [Redirection topic - Dart API](https://pub.dev/documentation/go_router/latest/topics/Redirection-topic.html)
- [Error handling topic - Dart API](https://pub.dev/documentation/go_router/latest/topics/Error%20handling-topic.html)
- [Configuring URL strategy - Flutter](https://docs.flutter.dev/ui/navigation/url-strategies)
- [Deep linking - Flutter](https://docs.flutter.dev/ui/navigation/deep-linking)

**GitHub Issues (HIGH confidence - verified bugs):**
- [Router recreation URL loss #172026](https://github.com/flutter/flutter/issues/172026)
- [Nested app refresh loses route #114597](https://github.com/flutter/flutter/issues/114597)
- [StatefulShellRoute deep link conflict #134373](https://github.com/flutter/flutter/issues/134373)
- [iOS cold start race condition #142988](https://github.com/flutter/flutter/issues/142988)
- [Infinite redirect loops #118061](https://github.com/flutter/flutter/issues/118061)
- [PathUrlStrategy 404 on refresh #107996](https://github.com/flutter/flutter/issues/107996)
- [PathUrlStrategy ignores fragments #98933](https://github.com/flutter/flutter/issues/98933)

**Community Resources (MEDIUM confidence):**
- [Flutter Deep Linking: Ultimate Guide - CodeWithAndrea](https://codewithandrea.com/articles/flutter-deep-links/)
- [Flutter Authentication Flow with GoRouter](https://blog.ishangavidusha.com/flutter-authentication-flow-with-go-router-and-provider)
- [Bottom Navigation with Nested Routes - CodeWithAndrea](https://codewithandrea.com/articles/flutter-bottom-navigation-bar-nested-routes-gorouter/)
