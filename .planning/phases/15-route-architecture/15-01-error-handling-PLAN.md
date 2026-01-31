---
phase: 15-route-architecture
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/lib/screens/not_found_screen.dart
  - frontend/lib/main.dart
autonomous: true

must_haves:
  truths:
    - "User sees 404 page when entering invalid route"
    - "User can navigate to home from 404 page"
    - "404 page shows attempted path for debugging"
  artifacts:
    - path: "frontend/lib/screens/not_found_screen.dart"
      provides: "404 error page widget"
      min_lines: 40
      exports: ["NotFoundScreen"]
    - path: "frontend/lib/main.dart"
      provides: "GoRouter errorBuilder configuration"
      contains: "errorBuilder"
  key_links:
    - from: "frontend/lib/main.dart"
      to: "frontend/lib/screens/not_found_screen.dart"
      via: "errorBuilder callback imports and returns NotFoundScreen"
      pattern: "errorBuilder.*NotFoundScreen"
---

<objective>
Implement 404 error page for invalid routes using GoRouter's errorBuilder.

Purpose: Users entering invalid URLs see a helpful error page with navigation options instead of a blank screen or crash (ERR-01, ROUTE-03).

Output: NotFoundScreen widget and errorBuilder configuration in GoRouter.
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

@frontend/lib/main.dart
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create NotFoundScreen widget</name>
  <files>frontend/lib/screens/not_found_screen.dart</files>
  <action>
Create a new NotFoundScreen widget that displays:
- Error icon (Icons.error_outline, size 64, error color)
- "404 - Page Not Found" heading (headlineSmall)
- "The page [attemptedPath] does not exist." body text
- "Go to Home" FilledButton.icon with home icon that navigates to /home via context.go()

Required imports:
- flutter/material.dart
- go_router/go_router.dart

Constructor:
```dart
class NotFoundScreen extends StatelessWidget {
  final String attemptedPath;
  const NotFoundScreen({super.key, required this.attemptedPath});
}
```

Widget structure:
- Scaffold with AppBar (title: "Page Not Found")
- Center > Column (mainAxisAlignment: center)
- Icon, SizedBox(16), Text heading, SizedBox(8), Text body, SizedBox(24), FilledButton.icon

Use Theme.of(context) for colors (colorScheme.error for icon, textTheme for text styles).
  </action>
  <verify>
No syntax errors: `cd frontend && flutter analyze lib/screens/not_found_screen.dart`
  </verify>
  <done>NotFoundScreen widget exists with attemptedPath parameter and "Go to Home" button.</done>
</task>

<task type="auto">
  <name>Task 2: Add errorBuilder to GoRouter</name>
  <files>frontend/lib/main.dart</files>
  <action>
1. Add import for NotFoundScreen:
   ```dart
   import 'screens/not_found_screen.dart';
   ```

2. Add errorBuilder parameter to GoRouter constructor (after refreshListenable line ~265):
   ```dart
   return GoRouter(
     initialLocation: '/splash',
     redirect: (context, state) { ... },
     routes: [ ... ],
     refreshListenable: authProvider,
     errorBuilder: (context, state) {
       return NotFoundScreen(attemptedPath: state.uri.path);
     },
   );
   ```

The errorBuilder is called when GoRouter cannot match any route. Pass state.uri.path as attemptedPath so user sees which URL failed.

Do NOT modify anything else in main.dart - only add the import and errorBuilder parameter.
  </action>
  <verify>
1. App compiles: `cd frontend && flutter build web --no-tree-shake-icons 2>&1 | head -20`
2. Manual test: Navigate to http://localhost:PORT/invalid/random/path and verify 404 page appears
  </verify>
  <done>Invalid routes show NotFoundScreen with "Go to Home" button that works.</done>
</task>

</tasks>

<verification>
After both tasks:
1. `flutter analyze` passes with no errors
2. Navigate to `/asdf/gibberish` - should see 404 page
3. Click "Go to Home" - should navigate to /home
4. 404 page shows the attempted path in the message
</verification>

<success_criteria>
- ERR-01: Invalid route path shows 404 error page with navigation options
- ROUTE-03: GoRouter errorBuilder displays 404 page for invalid routes
- User can recover from 404 by clicking "Go to Home"
</success_criteria>

<output>
After completion, create `.planning/phases/15-route-architecture/15-01-SUMMARY.md`
</output>
