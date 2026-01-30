# Research Summary: v1.7 URL & Deep Links

**Milestone:** v1.7 - URL & Deep Linking
**Synthesized:** 2026-01-31
**Overall Confidence:** HIGH

---

## Executive Summary

The BA Assistant v1.7 deep linking milestone is a **configuration and pattern implementation project**, not a technology adoption project. The existing stack (GoRouter 17.0.1, Flutter 3.9+, path URL strategy via `usePathUrlStrategy()`) already provides everything needed. No new packages are required. The primary work involves extending the GoRouter redirect logic to preserve URLs through the OAuth authentication flow, adding nested thread routes (`/projects/:id/threads/:threadId`), and implementing proper 404 error handling.

The current codebase has a solid foundation but contains **one critical gap**: the redirect logic discards the user's intended destination when redirecting to login, causing all authenticated users to land on `/home` regardless of their original deep link target. The fix is well-documented in GoRouter patterns: capture `state.matchedLocation` (or `state.uri.toString()` for query params) into a `returnUrl` query parameter, preserve it through the OAuth flow via session storage, and redirect to it after authentication completes.

The main risks are **router recreation destroying URL state on refresh** (already mitigated by the `_routerInstance` pattern but needs verification), **infinite redirect loops** when extending the redirect logic (add defensive null returns), and **production server configuration** (path-based URLs require SPA rewrite rules). All risks have documented prevention strategies with high confidence. Mobile-specific deep linking (Android App Links, iOS Universal Links) should be deferred to post-v1.7 as web is the primary platform.

---

## Key Findings

### From STACK-DEEP-LINKING.md

| Technology | Decision | Rationale |
|------------|----------|-----------|
| go_router 17.0.1 | KEEP | Full deep linking support built-in, no upgrade needed |
| flutter_web_plugins | KEEP | `usePathUrlStrategy()` already configured in main.dart:74 |
| provider 6.1.5 | KEEP | `refreshListenable` pattern already working for auth |
| app_links | DO NOT ADD | Only needed for navigation stack preservation; overkill for URL sharing use case |
| uni_links | DO NOT ADD | Deprecated in favor of app_links |

**Key insight:** Router instance already created correctly outside build() with `_isRouterInitialized` flag (main.dart:114-117). This pattern protects against rebuilds within widget lifecycle.

### From FEATURES-v1.7-deep-linking.md

**Table Stakes (Must Have v1.7):**
| Feature | Complexity | Notes |
|---------|------------|-------|
| URL reflects current page | Low | Basic GoRoute definition for threads |
| Refresh preserves location | Medium | Store/restore URL through auth flow |
| Bookmarkable URLs | Low | Follows from correct route structure |
| Auth redirect to intended destination | Medium | Query parameter pattern `?returnUrl=` |
| 404 handling for invalid routes | Medium | Custom error page with navigation options |
| Hierarchical URL structure | Low | `/projects/:id/threads/:threadId` nested routes |

**Differentiators (Nice to Have v1.7):**
- Copy current URL button (Low effort, high value)
- Tab state in URL via query params (Medium effort)

**Defer to v2.0:**
- Mobile deep links (Android App Links, iOS Universal Links)
- Link previews (Open Graph metadata)
- Smart redirect with scroll/state preservation

**Anti-Features (Do NOT Build):**
- Custom URL schemes (baassistant://) - insecure, unprofessional
- Sensitive data in URLs - use opaque IDs only
- Hash-based URLs - already using path strategy correctly

### From ARCHITECTURE-v1.7-deep-linking.md

**Core Components:**

| Component | Responsibility | Changes Needed |
|-----------|----------------|----------------|
| GoRouter redirect | URL parsing, redirect decisions, returnUrl preservation | Extend to capture/forward returnUrl |
| AuthProvider | Auth state, notifies router, holds returnUrl state | Add `_returnUrl` field and accessors |
| AuthService | Token storage, OAuth flow | Add session storage for returnUrl before OAuth |
| ConversationScreen | Display conversation | Accept both projectId and threadId params |
| ThreadListScreen | List threads | Replace Navigator.push() with context.go() |

**URL Storage Strategy:**
1. Query parameter for splash/login transitions (visible for debugging)
2. Session storage before OAuth redirect (survives external redirect)
3. Retrieve from session storage after callback, navigate to stored URL

**Breaking Changes:**
- `ConversationScreen(threadId)` becomes `ConversationScreen(projectId, threadId)`
- `Navigator.push()` calls in ThreadListScreen must become `context.go()` for URL sync

### From PITFALLS-v1.7-deep-linking.md

**Critical Pitfalls (Cause rewrites/bugs):**

| # | Pitfall | Prevention | Phase |
|---|---------|------------|-------|
| 1 | Router recreation destroys URL state | Create GoRouter outside widget tree, verify current pattern | Phase 1 |
| 2 | Missing return URL after OAuth | Capture `state.uri.toString()` into `returnUrl` query param | Phase 2 |
| 3 | StatefulShellRoute deep link branch conflict | Use parentNavigatorKey, test back navigation | Phase 1 |
| 4 | iOS cold start deep link race condition | Handle "/" -> actual path gracefully, test on real devices | Phase 4 |
| 5 | refreshListenable infinite redirect loop | Return null when already at target, never notify from redirect | Phase 2 |

**Moderate Pitfalls:**

| # | Pitfall | Prevention | Phase |
|---|---------|------------|-------|
| 6 | Path URL strategy needs server config | Document SPA rewrite rules, test production refresh | Phase 5 |
| 7 | No 404 handling for invalid deep links | Add errorBuilder to GoRouter, screen-level resource validation | Phase 3 |
| 8 | URL fragment loss with OAuth | Capture fragment before usePathUrlStrategy(), verify OAuth works | Phase 2 |
| 9 | Back navigation history corruption | Design decision: go() replaces stack, consider manual stack construction | Phase 3 |
| 10 | Query parameters lost in redirect | Use `state.uri.toString()` not `state.matchedLocation` | Phase 2 |

---

## Recommended Phase Structure

Based on combined research analysis, the v1.7 milestone should be structured into **4 phases** with dependencies flowing sequentially:

### Phase 1: Route Architecture Foundation

**Rationale:** All other features depend on stable URL state and correct route structure. Must be bulletproof before adding auth complexity.

**Delivers:**
- Nested thread routes: `/projects/:id/threads/:threadId`
- Verified router instance stability on refresh
- errorBuilder for 404 states (route-level)
- Debug logging enabled (`debugLogDiagnostics: kDebugMode`)

**Features from research:**
- Hierarchical URL structure (table stakes)
- 404 handling for invalid routes (partial - route-level)

**Pitfalls to avoid:**
- #1 Router Recreation Destroys URL State
- #3 StatefulShellRoute Deep Link Branch Conflict
- #11 Missing Debug Logging

**Research needed:** NO - well-documented GoRouter patterns

---

### Phase 2: Auth Flow with URL Preservation

**Rationale:** Depends on Phase 1 route stability. This is the highest-value change - makes deep links actually work for logged-out users.

**Delivers:**
- returnUrl capture in redirect logic
- Session storage integration for OAuth flow
- Full URL preservation including query parameters
- Login screen reads and uses returnUrl
- Callback screen restores returnUrl after OAuth

**Features from research:**
- Auth redirect to intended destination (table stakes)
- URL reflects current page through auth flow (table stakes)

**Pitfalls to avoid:**
- #2 Missing Return URL After OAuth
- #5 refreshListenable Infinite Redirect Loop
- #8 URL Fragment Loss with OAuth
- #10 Query Parameters Lost in Redirect

**Research needed:** NO - standard GoRouter redirect patterns

---

### Phase 3: Screen-Level URL Integration

**Rationale:** Depends on routes (Phase 1) and auth flow (Phase 2). This phase connects the URL structure to actual screen behavior.

**Delivers:**
- ConversationScreen accepts projectId + threadId from URL
- ThreadListScreen uses `context.go()` instead of Navigator.push()
- Resource-level 404 states (project not found, thread not found)
- Proper back navigation from deep-linked screens

**Features from research:**
- URL reflects current page (table stakes - completion)
- Bookmarkable URLs (table stakes - completion)
- 404 handling for invalid routes (table stakes - resource-level)

**Pitfalls to avoid:**
- #7 No 404 Handling for Invalid Deep Links
- #9 Back Navigation History Corruption
- #13 Missing URL Encoding for IDs

**Research needed:** NO - standard screen implementation patterns

---

### Phase 4: Testing & Validation

**Rationale:** Comprehensive testing after all features implemented. Includes platform-specific edge cases.

**Delivers:**
- Browser refresh preserves URL (all route types)
- Deep link from external source works
- Auth redirect with return URL (full flow)
- Invalid route/resource handling verified
- Documentation for production deployment (SPA rewrite rules)

**Features from research:**
- Refresh preserves location (table stakes - verification)
- All table stakes verified end-to-end

**Pitfalls to avoid:**
- #4 iOS Cold Start Deep Link Race Condition
- #6 Path URL Strategy Requires Server Configuration
- #12 Route Path Typos in Deep Link Configuration

**Research needed:** MAYBE - if iOS/Android native deep links added later

---

## Critical Pitfalls to Address (Top 5)

### 1. Router Recreation Destroys URL State (CRITICAL)
**Phase:** 1
**Risk:** After page refresh, app briefly loads correct URL then redirects to /home
**Prevention:** Verify `_routerInstance` pattern survives full page refresh; consider moving to top-level final variable
**Test:** Navigate to `/projects/abc/threads/xyz`, F5 refresh, verify URL maintained

### 2. Missing Return URL After OAuth (CRITICAL)
**Phase:** 2
**Risk:** Users always land on /home after OAuth, losing their deep link destination
**Prevention:** Capture `state.uri.toString()` into `returnUrl` param, store in session storage before OAuth, restore after callback
**Test:** Deep link while logged out, complete OAuth, verify landing on original URL

### 3. refreshListenable Infinite Redirect Loop (CRITICAL)
**Phase:** 2
**Risk:** App freezes, browser tab crashes due to redirect loop
**Prevention:** Always return null when already at correct location; never call notifyListeners() from redirect; add defensive checks
**Test:** Login/logout cycles with slow network simulation

### 4. Path URL Strategy Server Configuration (CRITICAL for Production)
**Phase:** 4 (document in Phase 1)
**Risk:** Production deployment returns 404 on any URL refresh
**Prevention:** Document SPA rewrite rules for common servers (Firebase, nginx, Apache); test staging deployment
**Test:** Deploy to staging, refresh on nested route

### 5. StatefulShellRoute Deep Link Branch Conflict (HIGH)
**Phase:** 1
**Risk:** Back button skips expected screens after deep link, navigation history corrupted
**Prevention:** Test back navigation explicitly; use parentNavigatorKey if needed; verify tab switching preserves state
**Test:** Deep link to thread, press back, verify you reach project detail (not home)

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new packages needed; GoRouter 17.0.1 is feature-complete for this use case |
| Features | HIGH | Table stakes are well-defined; official Flutter/GoRouter docs cover all patterns |
| Architecture | HIGH | Existing codebase has correct foundation; changes are incremental |
| Pitfalls | HIGH | GitHub issues document real bugs with verified solutions |

### Research Gaps

1. **Production server configuration** - Exact deployment target not confirmed (Firebase? nginx? Vercel?). Document multiple options, confirm during Phase 4.

2. **iOS cold start timing** - Testing only possible on real iOS devices. May need adjustment if flash of wrong screen occurs.

3. **Query parameter encoding edge cases** - If project/thread IDs ever contain special characters, additional encoding may be needed. Current UUIDs should be safe.

---

## Implications for Roadmap

### Phase Dependencies

```
Phase 1: Route Architecture  -->  Phase 2: Auth Flow  -->  Phase 3: Screen Integration  -->  Phase 4: Testing
   |                                    |
   +-- Must be stable first            +-- Highest user value
```

### Phase Research Flags

| Phase | Needs `/gsd:research-phase`? | Rationale |
|-------|------------------------------|-----------|
| Phase 1 | NO | Standard GoRouter nested routes |
| Phase 2 | NO | Standard redirect patterns |
| Phase 3 | NO | Standard screen implementation |
| Phase 4 | MAYBE | If iOS/Android native deep links added |

### Estimated Complexity

- **Phase 1:** Low complexity, high importance (foundation)
- **Phase 2:** Medium complexity (redirect logic, session storage)
- **Phase 3:** Low complexity (screen changes, navigation updates)
- **Phase 4:** Low complexity (testing, documentation)

### Key Decision Points

1. **Back navigation behavior:** When user deep links to thread, should back button:
   - Go to parent project detail? (Recommended - matches URL hierarchy)
   - Go nowhere/close? (Current go() behavior)

2. **Copy URL button:** Include in v1.7 (low effort) or defer?

3. **Query param state:** Include tab state in URL (`?tab=threads`) in v1.7 or defer?

---

## Sources (Aggregated)

### Official Documentation (HIGH Confidence)
- [go_router package](https://pub.dev/packages/go_router) - v17.0.1 reference
- [Flutter Deep Linking](https://docs.flutter.dev/ui/navigation/deep-linking)
- [Flutter URL Strategies](https://docs.flutter.dev/ui/navigation/url-strategies)
- [GoRouter Error Handling](https://pub.dev/documentation/go_router/latest/topics/Error%20handling-topic.html)
- [GoRouter Redirection](https://pub.dev/documentation/go_router/latest/topics/Redirection-topic.html)

### Verified GitHub Issues (HIGH Confidence)
- [Router recreation URL loss #172026](https://github.com/flutter/flutter/issues/172026)
- [Nested app refresh loses route #114597](https://github.com/flutter/flutter/issues/114597)
- [StatefulShellRoute deep link conflict #134373](https://github.com/flutter/flutter/issues/134373)
- [Infinite redirect loops #118061](https://github.com/flutter/flutter/issues/118061)
- [PathUrlStrategy 404 on refresh #107996](https://github.com/flutter/flutter/issues/107996)

### Community Resources (MEDIUM Confidence)
- [CodeWithAndrea Deep Links Guide](https://codewithandrea.com/articles/flutter-deep-links/)
- [Flutter Auth Flow with GoRouter](https://blog.ishangavidusha.com/flutter-authentication-flow-with-go-router-and-provider)

---

*Synthesized from: STACK-DEEP-LINKING.md, FEATURES-v1.7-deep-linking.md, ARCHITECTURE-v1.7-deep-linking.md, PITFALLS-v1.7-deep-linking.md*
