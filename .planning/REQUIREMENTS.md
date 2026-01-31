# Requirements: v1.7 URL & Deep Links

**Defined:** 2026-01-31
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v1.7 Requirements

Requirements for URL & Deep Links milestone. Each maps to roadmap phases.

### Route Architecture

- [x] **ROUTE-01**: Conversations have unique URLs (`/projects/:projectId/threads/:threadId`)
- [ ] **ROUTE-02**: Browser back/forward navigation works correctly from conversation screen
- [x] **ROUTE-03**: GoRouter errorBuilder displays 404 page for invalid routes
- [ ] **ROUTE-04**: ConversationScreen accepts projectId and threadId from URL parameters

### URL Preservation

- [ ] **URL-01**: Page refresh preserves current URL for authenticated users
- [ ] **URL-02**: URL preserved through OAuth redirect via session storage
- [ ] **URL-03**: Settings page refresh returns to `/settings` (not `/home`)
- [ ] **URL-04**: Project detail refresh returns to `/projects/:id` (not `/home`)

### Auth Flow

- [ ] **AUTH-01**: Auth redirect captures intended destination as `returnUrl` query parameter
- [ ] **AUTH-02**: Login completes to stored `returnUrl` instead of `/home`
- [ ] **AUTH-03**: Direct login (no returnUrl) goes to `/home`
- [ ] **AUTH-04**: `returnUrl` cleared from session storage after successful navigation

### Error Handling

- [x] **ERR-01**: Invalid route path shows 404 error page with navigation options
- [ ] **ERR-02**: Valid route with non-existent project shows "Project not found" state
- [ ] **ERR-03**: Valid route with non-existent thread shows "Thread not found" state
- [ ] **ERR-04**: Invalid `returnUrl` (deleted resource) handled gracefully after login

## v2.0 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Mobile Deep Links

- **MOBILE-01**: Android App Links configuration for native deep linking
- **MOBILE-02**: iOS Universal Links configuration for native deep linking
- **MOBILE-03**: Cold start deep link handling on both platforms

### Advanced URL Features

- **ADV-01**: Copy current URL button in AppBar
- **ADV-02**: Tab state in URL via query params (`?tab=threads`)
- **ADV-03**: Open Graph metadata for link previews

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Custom URL schemes (baassistant://) | Insecure, unprofessional - use platform deep links instead |
| Hash-based URLs | Already using path URL strategy correctly |
| Sensitive data in URLs | Security risk - use opaque IDs only (already implemented) |
| Smart redirect with scroll position | Complexity exceeds value for v1.7 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ROUTE-01 | Phase 15 | Complete |
| ROUTE-02 | Phase 17 | Pending |
| ROUTE-03 | Phase 15 | Complete |
| ROUTE-04 | Phase 17 | Pending |
| URL-01 | Phase 16 | Pending |
| URL-02 | Phase 16 | Pending |
| URL-03 | Phase 16 | Pending |
| URL-04 | Phase 16 | Pending |
| AUTH-01 | Phase 16 | Pending |
| AUTH-02 | Phase 16 | Pending |
| AUTH-03 | Phase 16 | Pending |
| AUTH-04 | Phase 16 | Pending |
| ERR-01 | Phase 15 | Complete |
| ERR-02 | Phase 17 | Pending |
| ERR-03 | Phase 17 | Pending |
| ERR-04 | Phase 18 | Pending |

**Coverage:**
- v1.7 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-01-31*
*Last updated: 2026-01-31 after phase 15 completion*
