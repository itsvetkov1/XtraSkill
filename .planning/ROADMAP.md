# Roadmap: v1.7 URL & Deep Links

**Milestone:** v1.7
**Created:** 2026-01-31
**Depth:** Quick (4 phases)
**Status:** Complete

---

## Overview

Implement deep linking and URL preservation for the BA Assistant. Users can bookmark, share, and refresh URLs without losing their place. The OAuth authentication flow preserves intended destinations, and invalid routes show helpful error states.

---

## Phase 15: route-architecture

**Goal:** URL structure reflects application hierarchy with proper error handling for invalid routes.

**Dependencies:** None (foundation phase)

**Requirements:**
- ROUTE-01: Conversations have unique URLs (`/projects/:projectId/threads/:threadId`)
- ROUTE-03: GoRouter errorBuilder displays 404 page for invalid routes
- ERR-01: Invalid route path shows 404 error page with navigation options

**Plans:** 2 plans

Plans:
- [x] 15-01-error-handling-PLAN.md - 404 error page with errorBuilder
- [x] 15-02-thread-routes-PLAN.md - Nested thread routes and navigation

**Success Criteria:**
1. User navigates to `/projects/abc/threads/xyz` and URL bar shows this path
2. User enters invalid route `/invalid/path` and sees 404 page with "Go Home" button
3. User can navigate from 404 page to home without using browser back button

---

## Phase 16: auth-url-preservation

**Goal:** Users can refresh pages or return from OAuth login without losing their intended destination.

**Dependencies:** Phase 15 (routes must exist before preservation logic)

**Requirements:**
- URL-01: Page refresh preserves current URL for authenticated users
- URL-02: URL preserved through OAuth redirect via session storage
- URL-03: Settings page refresh returns to `/settings` (not `/home`)
- URL-04: Project detail refresh returns to `/projects/:id` (not `/home`)
- AUTH-01: Auth redirect captures intended destination as `returnUrl` query parameter
- AUTH-02: Login completes to stored `returnUrl` instead of `/home`
- AUTH-03: Direct login (no returnUrl) goes to `/home`
- AUTH-04: `returnUrl` cleared from session storage after successful navigation

**Plans:** 2 plans

Plans:
- [x] 16-01-PLAN.md - UrlStorageService and redirect logic foundation
- [x] 16-02-PLAN.md - Login/Callback screen returnUrl integration

**Success Criteria:**
1. User refreshes browser on `/settings` and returns to `/settings` after auth check
2. User deep links to `/projects/abc` while logged out, completes OAuth, lands on `/projects/abc`
3. User clicks login button directly (no deep link), completes OAuth, lands on `/home`
4. User completes login with returnUrl, navigates away, returnUrl is not reused on next login

---

## Phase 17: screen-url-integration

**Goal:** Screens read URL parameters correctly and show appropriate states for missing resources.

**Dependencies:** Phase 16 (URL preservation must work before screens consume params)

**Requirements:**
- ROUTE-02: Browser back/forward navigation works correctly from conversation screen
- ROUTE-04: ConversationScreen accepts projectId and threadId from URL parameters
- ERR-02: Valid route with non-existent project shows "Project not found" state
- ERR-03: Valid route with non-existent thread shows "Thread not found" state

**Plans:** 2 plans

Plans:
- [x] 17-01-PLAN.md - ResourceNotFoundState widget and project not-found handling
- [x] 17-02-PLAN.md - Thread not-found handling and browser history option

**Success Criteria:**
1. User opens conversation via URL `/projects/abc/threads/xyz`, screen loads correct thread
2. User clicks browser back button from conversation, returns to project detail (not home)
3. User navigates to valid route with deleted project ID, sees "Project not found" message
4. User navigates to valid route with deleted thread ID, sees "Thread not found" message

---

## Phase 18: validation

**Goal:** All deep linking features verified end-to-end with edge cases documented.

**Dependencies:** Phase 17 (all features must be implemented before validation)

**Requirements:**
- ERR-04: Invalid `returnUrl` (deleted resource) handled gracefully after login

**Plans:** 2 plans

Plans:
- [x] 18-01-PLAN.md - End-to-end validation test execution
- [x] 18-02-PLAN.md - Production deployment documentation

**Success Criteria:**
1. User logs in with returnUrl pointing to deleted project, sees graceful error (not crash)
2. Browser refresh works on all route types (home, settings, project detail, conversation)
3. Copy URL from browser, paste in new tab, loads same content (for authenticated user)

---

## Progress

| Phase | Name | Requirements | Status |
|-------|------|--------------|--------|
| 15 | route-architecture | ROUTE-01, ROUTE-03, ERR-01 | Complete |
| 16 | auth-url-preservation | URL-01-04, AUTH-01-04 | Complete |
| 17 | screen-url-integration | ROUTE-02, ROUTE-04, ERR-02, ERR-03 | Complete |
| 18 | validation | ERR-04 | Complete |

**Coverage:** 16/16 requirements mapped

---

## Key Decisions

Decisions made during roadmap creation:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Phase structure | 4 phases per research | Research identified natural boundaries; quick depth allows 3-5 |
| Back navigation | Go to parent route | Matches URL hierarchy (`/projects/:id/threads/:threadId` -> `/projects/:id`) |
| Defer copy URL button | v2.0 | Nice-to-have, not table stakes for this milestone |
| Defer tab state in URL | v2.0 | Medium effort, not critical for bookmark/share use case |

---

*Roadmap created: 2026-01-31*
*Last updated: 2026-01-31 (phase 18 complete, milestone complete)*
