# US-001: URL Preservation on Refresh

**Priority:** High
**Status:** Ready for Development
**Related Bug:** BUG-001

---

## User Story

As a user,
I want the app to remember my current page when I refresh,
So that I don't lose my navigation context.

---

## Acceptance Criteria

### AC-1: Refresh preserves current route
- **Given** I'm on `/projects/123`
- **When** I refresh the page (F5 or browser refresh)
- **And** auth check completes successfully
- **Then** I'm redirected back to `/projects/123`

### AC-2: Nested routes preserved
- **Given** I'm viewing a conversation at `/projects/456/threads/789`
- **When** I refresh the page
- **And** auth check completes successfully
- **Then** I remain on `/projects/456/threads/789`

### AC-3: Settings page preserved
- **Given** I'm on `/settings`
- **When** I refresh the page
- **And** auth check completes successfully
- **Then** I remain on `/settings`

### AC-4: Invalid routes handled gracefully
- **Given** I'm on a route that no longer exists (e.g., deleted project)
- **When** I refresh the page
- **Then** I see an appropriate error state or redirect to `/projects`

---

## Technical Notes

**Current Flow:**
```
Refresh → initialLocation: '/splash' → auth loading → /splash → authenticated → /home
```

**Target Flow:**
```
Refresh → store current URL → initialLocation: '/splash' → auth loading → /splash → authenticated → restore stored URL
```

**Implementation Considerations:**
- Store intended URL before redirect to splash
- Use `state.uri` or browser URL to capture destination
- After auth complete, redirect to stored URL instead of `/home`
- Clear stored URL after successful navigation
