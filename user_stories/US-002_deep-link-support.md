# US-002: Deep Link Support

**Priority:** Medium
**Status:** Ready for Development
**Related Bug:** BUG-001

---

## User Story

As a user,
I want to bookmark or share URLs to specific pages,
So that I can return directly to that content.

---

## Acceptance Criteria

### AC-1: Bookmarked URL works when authenticated
- **Given** I have bookmarked `/projects/456`
- **And** I'm already authenticated in another tab
- **When** I open the bookmark in a new tab
- **Then** I navigate directly to `/projects/456`

### AC-2: Bookmarked URL works after login
- **Given** I have bookmarked `/projects/456`
- **And** I'm not currently authenticated
- **When** I open the bookmark
- **Then** I'm redirected to login
- **And** after successful login, I arrive at `/projects/456`

### AC-3: Shared URL works for authenticated recipient
- **Given** another user shares URL `/projects/789` with me
- **And** I have access to that project
- **When** I paste the URL in my browser
- **Then** I navigate directly to `/projects/789`

### AC-4: Thread-level deep links work
- **Given** I paste URL `/projects/123/threads/456` in browser
- **When** I'm authenticated
- **Then** I navigate directly to that conversation thread

### AC-5: Invalid deep links show error
- **Given** I paste URL `/projects/999` (non-existent)
- **When** I'm authenticated
- **Then** I see "Project not found" or similar error
- **And** I have option to go to `/projects`

---

## Technical Notes

**Browser URL must be source of truth:**
- On app init, read `window.location` (web) or deep link (mobile)
- Store target URL before auth redirect
- Restore after auth completes

**Mobile considerations:**
- iOS: Universal Links
- Android: App Links
- Deferred until web works correctly
