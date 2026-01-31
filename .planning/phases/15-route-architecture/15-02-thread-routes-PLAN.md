---
phase: 15-route-architecture
plan: 02
type: execute
wave: 2
depends_on: ["15-01"]
files_modified:
  - frontend/lib/screens/conversation/conversation_screen.dart
  - frontend/lib/main.dart
  - frontend/lib/screens/threads/thread_list_screen.dart
  - frontend/lib/widgets/breadcrumb_bar.dart
autonomous: false
checkpoint_reason: "Visual verification of thread URL in browser and breadcrumb display"

must_haves:
  truths:
    - "User navigates to thread and URL shows /projects/:id/threads/:threadId"
    - "User clicks thread in list and navigates via GoRouter (not Navigator.push)"
    - "Breadcrumbs show Projects > ProjectName > Conversation hierarchy"
  artifacts:
    - path: "frontend/lib/screens/conversation/conversation_screen.dart"
      provides: "ConversationScreen with projectId parameter"
      contains: "required this.projectId"
    - path: "frontend/lib/main.dart"
      provides: "Nested thread route under project"
      contains: "threads/:threadId"
    - path: "frontend/lib/screens/threads/thread_list_screen.dart"
      provides: "URL-based thread navigation"
      contains: "context.go"
    - path: "frontend/lib/widgets/breadcrumb_bar.dart"
      provides: "Thread route breadcrumb parsing"
      contains: "threads"
  key_links:
    - from: "frontend/lib/screens/threads/thread_list_screen.dart"
      to: "frontend/lib/main.dart"
      via: "context.go('/projects/$projectId/threads/$threadId')"
      pattern: "context\\.go.*threads"
    - from: "frontend/lib/main.dart"
      to: "frontend/lib/screens/conversation/conversation_screen.dart"
      via: "Route builder creates ConversationScreen with params"
      pattern: "ConversationScreen\\(.*projectId.*threadId"
---

<objective>
Implement nested thread routes so conversations have unique, bookmarkable URLs.

Purpose: Users can share, bookmark, and directly navigate to specific conversations via URL (ROUTE-01). Browser URL bar reflects current thread location.

Output: Working `/projects/:id/threads/:threadId` route with proper navigation and breadcrumbs.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/15-route-architecture/15-RESEARCH.md
@.planning/phases/15-route-architecture/15-01-SUMMARY.md

@frontend/lib/main.dart
@frontend/lib/screens/conversation/conversation_screen.dart
@frontend/lib/screens/threads/thread_list_screen.dart
@frontend/lib/widgets/breadcrumb_bar.dart
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update ConversationScreen to accept projectId</name>
  <files>frontend/lib/screens/conversation/conversation_screen.dart</files>
  <action>
Modify ConversationScreen to accept both projectId and threadId parameters.

1. Update class definition:
   ```dart
   class ConversationScreen extends StatefulWidget {
     /// Project ID this thread belongs to
     final String projectId;

     /// Thread ID to display
     final String threadId;

     const ConversationScreen({
       super.key,
       required this.projectId,
       required this.threadId,
     });

     @override
     State<ConversationScreen> createState() => _ConversationScreenState();
   }
   ```

2. No other changes needed - projectId is stored for future use (back navigation in Phase 17).

Note: The threadId usage throughout the file remains unchanged. We're only adding projectId as a required parameter that will be used for URL-based navigation context.
  </action>
  <verify>
File compiles: `cd frontend && flutter analyze lib/screens/conversation/conversation_screen.dart`
  </verify>
  <done>ConversationScreen accepts both projectId and threadId as required parameters.</done>
</task>

<task type="auto">
  <name>Task 2: Add nested thread route and update navigation</name>
  <files>frontend/lib/main.dart, frontend/lib/screens/threads/thread_list_screen.dart</files>
  <action>
**In main.dart:**

1. Add import for ConversationScreen (if not already present):
   ```dart
   import 'screens/conversation/conversation_screen.dart';
   ```

2. Add nested thread route inside the existing project :id route (around line 243-248). Find this block:
   ```dart
   GoRoute(
     path: ':id',
     builder: (context, state) {
       final id = state.pathParameters['id']!;
       return ProjectDetailScreen(projectId: id);
     },
   ),
   ```

   Replace with:
   ```dart
   GoRoute(
     path: ':id',
     builder: (context, state) {
       final id = state.pathParameters['id']!;
       return ProjectDetailScreen(projectId: id);
     },
     routes: [
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
   ```

**In thread_list_screen.dart:**

1. Add import for go_router:
   ```dart
   import 'package:go_router/go_router.dart';
   ```

2. Update _onThreadTap method (around line 47-54). Change from:
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

   To:
   ```dart
   void _onThreadTap(String threadId) {
     context.go('/projects/${widget.projectId}/threads/$threadId');
   }
   ```

3. Remove the import for ConversationScreen (no longer needed):
   ```dart
   // DELETE: import '../conversation/conversation_screen.dart';
   ```

IMPORTANT: Use `context.go()` not `context.push()`. The go() method replaces the URL entirely, which is correct for deep linking. Push would add to the stack but not update the URL properly for our use case.
  </action>
  <verify>
1. App compiles: `cd frontend && flutter build web --no-tree-shake-icons 2>&1 | head -20`
2. Navigate to a project, click a thread, verify URL shows /projects/[id]/threads/[threadId]
  </verify>
  <done>Thread navigation uses GoRouter and URL reflects /projects/:id/threads/:threadId path.</done>
</task>

<task type="auto">
  <name>Task 3: Update BreadcrumbBar for thread routes</name>
  <files>frontend/lib/widgets/breadcrumb_bar.dart</files>
  <action>
Update _buildBreadcrumbs method to handle /projects/:id/threads/:threadId paths.

1. Add import for ConversationProvider:
   ```dart
   import '../providers/conversation_provider.dart';
   ```

2. Modify the /projects route handling section (around line 86-103). Replace the existing logic with:

   ```dart
   // /projects routes
   if (segments.isNotEmpty && segments[0] == 'projects') {
     // /projects -> Projects (just the list, no parent link)
     if (segments.length == 1) {
       return [const Breadcrumb('Projects')];
     }

     // /projects/:id or /projects/:id/threads/:threadId
     breadcrumbs.add(const Breadcrumb('Projects', '/projects'));

     // Add project name (segments[1] is the project ID)
     if (segments.length >= 2) {
       final projectProvider = context.read<ProjectProvider>();
       final projectName =
           projectProvider.selectedProject?.name ?? 'Project';

       // If we have threads segment, project name links to project detail
       if (segments.length >= 4 && segments[2] == 'threads') {
         final projectId = segments[1];
         breadcrumbs.add(Breadcrumb(projectName, '/projects/$projectId'));

         // Add thread/conversation name
         final conversationProvider = context.read<ConversationProvider>();
         final threadTitle = conversationProvider.thread?.title ?? 'Conversation';
         breadcrumbs.add(Breadcrumb(threadTitle));
       } else {
         // Just /projects/:id - project name is current page (no link)
         breadcrumbs.add(Breadcrumb(projectName));
       }
     }

     return breadcrumbs;
   }
   ```

This creates breadcrumb hierarchies:
- /projects -> "Projects"
- /projects/:id -> "Projects > ProjectName"
- /projects/:id/threads/:threadId -> "Projects > ProjectName > ConversationTitle"

The conversation title comes from ConversationProvider which is loaded when ConversationScreen mounts.
  </action>
  <verify>
1. File compiles: `cd frontend && flutter analyze lib/widgets/breadcrumb_bar.dart`
2. Navigate to thread, verify breadcrumbs show "Projects > [ProjectName] > [ThreadTitle]"
  </verify>
  <done>Breadcrumbs correctly display hierarchy for thread routes.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
Thread URL routing with nested /projects/:id/threads/:threadId paths, URL-based navigation from thread list, and updated breadcrumbs.
  </what-built>
  <how-to-verify>
1. Start the app: `cd frontend && flutter run -d chrome`
2. Log in and navigate to Projects
3. Click on a project to open it
4. Click on a thread/conversation
5. **Check URL bar**: Should show `/projects/[project-id]/threads/[thread-id]`
6. **Check breadcrumbs**: Should show "Projects > [Project Name] > [Thread Title]"
7. Click "Projects" in breadcrumb - should navigate to /projects
8. Navigate back to a thread
9. Press F5 to refresh - page should reload (may require login, but URL structure should be visible)
  </how-to-verify>
  <resume-signal>Type "approved" if URL shows correct path and breadcrumbs display hierarchy, or describe issues found.</resume-signal>
</task>

</tasks>

<verification>
After all tasks including checkpoint:
1. `flutter analyze` passes
2. URL bar shows `/projects/abc/threads/xyz` format when viewing conversation
3. Breadcrumbs show clickable "Projects" > clickable "[ProjectName]" > bold "[ThreadTitle]"
4. Invalid routes still show 404 (from Plan 01)
</verification>

<success_criteria>
- ROUTE-01: Conversations have unique URLs (`/projects/:projectId/threads/:threadId`)
- Thread navigation uses context.go() for proper URL sync
- Breadcrumbs reflect URL hierarchy with clickable segments
</success_criteria>

<output>
After completion, create `.planning/phases/15-route-architecture/15-02-SUMMARY.md`
</output>
