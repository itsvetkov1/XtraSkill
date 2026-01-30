# US-004: Unique Conversation URLs

**Priority:** High
**Status:** Ready for Development
**Related Bug:** BUG-001

---

## User Story

As a user,
I want each conversation to have a unique URL,
So that I can bookmark, share, and refresh specific conversations.

---

## Acceptance Criteria

### AC-1: Conversations have unique URLs
- **Given** I open a conversation thread
- **When** the conversation screen loads
- **Then** the browser URL updates to `/projects/:projectId/threads/:threadId`

### AC-2: Conversation URL is shareable
- **Given** I'm viewing conversation at `/projects/123/threads/456`
- **When** I copy the URL and share it with a colleague
- **Then** they can open the URL and see the same conversation (if authorized)

### AC-3: Conversation URL is bookmarkable
- **Given** I bookmark `/projects/123/threads/456`
- **When** I open the bookmark later
- **Then** I navigate directly to that conversation

### AC-4: Refresh preserves conversation
- **Given** I'm viewing `/projects/123/threads/456`
- **When** I refresh the page
- **Then** I remain on the same conversation (per US-001)

### AC-5: Back navigation works correctly
- **Given** I'm at `/projects/123/threads/456`
- **When** I tap the back button
- **Then** I return to `/projects/123` (Threads tab)
- **And** browser history is correct (back/forward works)

### AC-6: Invalid thread URL shows error
- **Given** I navigate to `/projects/123/threads/999` (non-existent)
- **When** the page loads
- **Then** I see "Thread not found" error
- **And** I have option to return to project

---

## Current Implementation

Per `thread_list_screen.dart:47-54`:
```dart
void _onThreadTap(String threadId) {
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => ConversationScreen(threadId: threadId),
    ),
  );
}
```

**Problems:**
- Uses `Navigator.push` (imperative) instead of `context.go` (declarative)
- URL stays at `/projects/:id` when viewing conversation
- No route defined in GoRouter for conversations
- Cannot bookmark, share, or refresh conversations

---

## Technical Notes

### Required Changes

**1. Add route to GoRouter (`main.dart`):**
```dart
GoRoute(
  path: '/projects/:projectId/threads/:threadId',
  builder: (context, state) {
    final projectId = state.pathParameters['projectId']!;
    final threadId = state.pathParameters['threadId']!;
    return ConversationScreen(
      projectId: projectId,
      threadId: threadId,
    );
  },
),
```

**2. Update navigation (`thread_list_screen.dart`):**
```dart
void _onThreadTap(String threadId) {
  context.go('/projects/${widget.projectId}/threads/$threadId');
}
```

**3. Update ConversationScreen:**
- Accept `projectId` parameter (for breadcrumbs, back navigation)
- Handle case where thread doesn't exist (404)

**4. Update breadcrumbs:**
- Show: `Projects > Project Name > Thread Title`

### Considerations

- Thread belongs to a project - URL should reflect hierarchy
- ConversationScreen may need projectId for context (back navigation, breadcrumbs)
- Mobile deep links: `baassistant://projects/123/threads/456`
