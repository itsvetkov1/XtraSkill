# Domain Pitfalls: v1.6 UX Quick Wins

**Domain:** Flutter UX improvements (retry, clipboard, inline editing, OAuth display)
**Researched:** 2026-01-30
**Confidence:** HIGH (verified against official Flutter documentation, platform guidelines, and codebase patterns)

---

## Critical Pitfalls

Mistakes that cause rewrites, broken cross-platform behavior, or major UX failures.

### Pitfall 1: Message Retry Without State Management (The "Duplicate Message" Problem)

**What goes wrong:** Retry button sends the message again without cleaning up the failed state. User ends up with:
- Duplicate user messages in the conversation
- Multiple retry buttons visible for the same failed message
- Race conditions if user taps retry while previous retry is still processing

**Why it happens:**
- Optimistic UI already added user message to `_messages` list
- Retry naively calls `sendMessage()` again instead of retrying the failed request
- No explicit "failed message" state tracked in `Message` model
- Current `Message` model lacks `status` field (only `id`, `role`, `content`, `createdAt`)

**Consequences:**
- Conversation history becomes inconsistent
- User sees same message twice
- Backend may process duplicate requests (cost, confusion)
- Poor UX destroys trust in the app

**Warning signs:**
- User messages appear twice after retry
- Multiple loading indicators visible
- Users complain about "ghost messages"
- Conversation length doesn't match expected count

**Prevention strategy:**
1. **Add message status to model:** Extend `Message` with `status` field (`pending`, `sent`, `failed`)
2. **Track failed messages explicitly:** Store failed user message content and position
3. **Retry replaces, not appends:** Remove failed message before retrying
4. **Disable retry during processing:** Use `isStreaming` to prevent double-taps
5. **Clear error state on retry:** Call `clearError()` at start of retry

**Implementation pattern:**
```dart
// In Message model - add status
enum MessageStatus { pending, sent, failed }

// In ConversationProvider - track last failed message
String? _failedMessageContent;
String? _failedMessageId;

Future<void> retryFailedMessage() async {
  if (_failedMessageContent == null || _isStreaming) return;

  // Remove the failed message from list
  _messages.removeWhere((m) => m.id == _failedMessageId);

  // Clear error and failed state
  _error = null;
  final content = _failedMessageContent!;
  _failedMessageContent = null;
  _failedMessageId = null;

  // Now send as fresh message
  await sendMessage(content);
}
```

**Phase relevance:** Message retry phase must address this FIRST before implementing UI.

**Sources:**
- [Flutter Mastery Library - Error Handling and Retry Strategies](https://fluttermasterylibrary.com/6/9/2/3/)
- [DEV Community - Streamlining Async Operations with Retry](https://dev.to/iamsirmike/streamlining-asynchronous-operations-in-flutter-with-error-handling-and-retry-mechanism-3od7)

---

### Pitfall 2: Clipboard API Cross-Platform Inconsistencies

**What goes wrong:** Clipboard copy works on one platform but fails silently or throws on another. Common failures:
- Web: Permission denied errors in secure contexts
- iOS: Clipboard access requires explicit permission in some scenarios
- Android: Works but no feedback if copy fails

**Why it happens:**
- Flutter's `Clipboard` class is text-only (no rich content)
- Web requires HTTPS or localhost for clipboard access
- Browser clipboard API requires user gesture context
- WebView environments have additional restrictions

**Consequences:**
- User taps copy button, nothing happens
- No error feedback, user tries repeatedly
- Works in development (localhost), fails in production (permissions)
- Platform-specific bug reports that are hard to reproduce

**Warning signs:**
- Copy button works on Android, fails on web
- Works in debug mode, fails in release
- Works on Chrome, fails on Safari/Firefox
- "NotAllowedError: Write permission denied" in console (web)

**Prevention strategy:**
1. **Use try-catch with platform feedback:** Always wrap clipboard operations
2. **Show confirmation snackbar:** User needs visual feedback that copy worked
3. **Test on all platforms before merge:** Web Chrome, Android, iOS minimum
4. **Handle failure gracefully:** Show "Copy failed" message, not silent failure
5. **Use correct Flutter API:** `Clipboard.setData(ClipboardData(text: content))`

**Implementation pattern:**
```dart
Future<void> copyToClipboard(BuildContext context, String content) async {
  try {
    await Clipboard.setData(ClipboardData(text: content));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Copied to clipboard'),
          duration: Duration(seconds: 2),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to copy: ${e.toString()}'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }
}
```

**Phase relevance:** Clipboard copy phase - test cross-platform before considering complete.

**Sources:**
- [LogRocket - Implementing Copy to Clipboard in Flutter](https://blog.logrocket.com/implementing-copy-clipboard-flutter/)
- [Flutter GitHub Issue #111388 - WebView clipboard restrictions](https://github.com/flutter/flutter/issues/111388)
- [GeeksforGeeks - Flutter Copy to Clipboard](https://www.geeksforgeeks.org/flutter/flutter-add-copy-to-clipboard-without-package/)

---

### Pitfall 3: TextEditingController Memory Leak in Dialogs

**What goes wrong:** Creating `TextEditingController` inside dialog without proper disposal causes memory leaks. Symptoms:
- Memory usage grows with each dialog open/close cycle
- "A TextEditingController was used after being disposed" errors
- App becomes sluggish over time
- DevTools shows increasing TextEditingController instances

**Why it happens:**
- `TextEditingController` allocates native resources not automatically garbage collected
- Dialog widgets rebuilt on state changes, creating new controllers
- Disposing in dialog's `dispose()` can race with dialog close
- Existing `ThreadCreateDialog` does this correctly, but pattern easy to break

**Consequences:**
- Memory leaks accumulate, especially on mobile
- Crashes due to out-of-memory errors
- Runtime errors when accessing disposed controller
- Performance degradation over time

**Warning signs:**
- DevTools Memory Tab shows TextEditingController count increasing
- "was used after being disposed" errors in console
- App slows down after opening/closing dialogs many times
- Memory never decreases after closing dialogs

**Prevention strategy:**
1. **Follow existing pattern:** `ThreadCreateDialog` already does this correctly - replicate it
2. **Create in initState, dispose in dispose:** Never create controller in `build()`
3. **Check mounted before using:** Always `if (mounted)` before setState after async
4. **Test with DevTools:** Run memory profiler, open/close dialog 10 times, verify no leak

**Correct pattern (from existing codebase):**
```dart
class _ThreadRenameDialogState extends State<ThreadRenameDialog> {
  final _titleController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _titleController.text = widget.initialTitle ?? '';
  }

  @override
  void dispose() {
    _titleController.dispose();  // CRITICAL: Must dispose
    super.dispose();
  }

  // ... rest of dialog
}
```

**Phase relevance:** Thread rename dialog phase - must follow disposal pattern.

**Sources:**
- [DCM Blog - 15 Common Flutter Mistakes 2025](https://dcm.dev/blog/2025/03/24/fifteen-common-mistakes-flutter-dart-development)
- [Medium - Memory Leaks in Flutter](https://medium.com/@avniprajapati21101/memory-management-memory-leaks-in-flutter-6936bdba2b71)
- [Flutter GitHub Issue #61249 - TextEditingController used after disposed](https://github.com/flutter/flutter/issues/61249)

---

## Moderate Pitfalls

Mistakes that cause delays, inconsistent UX, or technical debt.

### Pitfall 4: Dialog Build Context Timing Issues

**What goes wrong:** Showing dialog or snackbar from wrong context causes crashes or misbehavior:
- "setState() called during build" errors
- Dialog appears behind other widgets
- Snackbar shows on wrong screen
- Navigator operations fail

**Why it happens:**
- Calling `showDialog` from `build()` method
- Using context before widget is fully mounted
- Using stale context after navigation
- Not using `BuildContext` from `Builder` or `Consumer`

**Consequences:**
- Runtime exceptions crash the app
- Dialogs appear at wrong z-index
- Navigation state becomes corrupted
- Inconsistent behavior across platforms

**Warning signs:**
- "setState() called during build" in console
- Dialog appears but is not interactive
- "Looking up a deactivated widget's ancestor" errors
- Dialog dismissal breaks navigation

**Prevention strategy:**
1. **Never call showDialog in build():** Use button callbacks or initState with postFrameCallback
2. **Use context.mounted check:** Always verify before async operations
3. **Get fresh context from Builder:** Use `Builder(builder: (context) => ...)` when needed
4. **Use ScaffoldMessenger.of(context):** Not deprecated `Scaffold.of(context)`

**Implementation pattern:**
```dart
// WRONG - calling showDialog in build triggers on every rebuild
@override
Widget build(BuildContext context) {
  if (shouldShowDialog) {
    showDialog(...);  // BAD: causes setState during build
  }
}

// CORRECT - use postFrameCallback or callback
@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    if (shouldShowDialog) {
      showDialog(context: context, ...);
    }
  });
}

// CORRECT - triggered by user action
void _onRenamePressed() {
  showDialog(context: context, ...);  // GOOD: in callback, not build
}
```

**Phase relevance:** All dialog phases (rename, retry confirmation) must follow this pattern.

**Sources:**
- [Flutter Docs - Common Errors](https://docs.flutter.dev/testing/common-errors)
- [LogRocket - Creating Dialogs in Flutter](https://blog.logrocket.com/creating-dialogs-flutter/)

---

### Pitfall 5: OAuth Provider Icon Brand Guideline Violations

**What goes wrong:** Displaying Google/Microsoft icons incorrectly leads to:
- App rejection from app stores
- Legal cease-and-desist letters
- Unprofessional appearance
- User confusion about login options

**Why it happens:**
- Using generic icons instead of official brand assets
- Modifying official icons (color, proportion, effects)
- Placing icons without proper spacing/prominence
- Not matching the look of other social login buttons

**Consequences:**
- App store rejection (especially Apple)
- Brand guideline violation notices
- Legal liability
- Users don't recognize login options

**Warning signs:**
- Google icon looks different from other apps
- Icons are stretched, recolored, or have effects
- Sign-in button text doesn't match guidelines
- Icons are smaller/less prominent than other buttons

**Prevention strategy:**
1. **Use official packages:** `flutter_signin_button` or similar that includes correct assets
2. **Follow brand guidelines:**
   - Google: Must use official colors, Roboto font, proper aspect ratio
   - Microsoft: Must follow Microsoft identity branding
3. **Equal prominence:** OAuth buttons must be equally or more prominent than alternatives
4. **Don't modify icons:** No color changes, no stretching, no effects
5. **Use correct text:** "Sign in with Google" / "Continue with Microsoft"

**Implementation pattern:**
```dart
// Use package with official brand assets
import 'package:flutter_signin_button/flutter_signin_button.dart';

SignInButton(
  Buttons.Google,
  onPressed: () => _loginWithGoogle(),
)

// OR custom button following guidelines
ElevatedButton.icon(
  icon: Image.asset(
    'assets/google_logo.png',  // Official asset, not custom
    height: 24,
    width: 24,  // Preserve aspect ratio
  ),
  label: const Text('Sign in with Google'),  // Exact text from guidelines
  onPressed: () => _loginWithGoogle(),
)
```

**Phase relevance:** OAuth provider icon phase - verify against official guidelines before merge.

**Sources:**
- [Google Sign-In Branding Guidelines](https://developers.google.com/identity/branding-guidelines)
- [Flutter Gems - Authentication Packages](https://fluttergems.dev/authentication/)
- [pub.dev - flutter_signin_button](https://pub.dev/packages/flutter_signin_button)

---

### Pitfall 6: Snackbar Persistence Across Routes (2025 Breaking Change)

**What goes wrong:** Snackbars with action buttons now persist until dismissed by user (Flutter breaking change). This causes:
- Snackbar stays visible after navigating away
- Multiple snackbars stack up
- User confused why snackbar won't go away
- Inconsistent behavior between action/no-action snackbars

**Why it happens:**
- Flutter 2025 breaking change: SnackBars with actions default to `persist: true`
- Old code assumes snackbar will auto-dismiss
- Not clearing previous snackbars before showing new ones
- Not using `ScaffoldMessenger` correctly

**Consequences:**
- Snackbars pile up, cluttering UI
- User has to manually dismiss each snackbar
- Confusion when snackbar persists unexpectedly
- Accessibility issues (TalkBack/VoiceOver makes snackbars persist longer)

**Warning signs:**
- Snackbar stays visible indefinitely
- Multiple snackbars visible at once
- "Copied to clipboard" snackbar won't go away
- Different behavior on different Flutter versions

**Prevention strategy:**
1. **Clear previous snackbars:** `ScaffoldMessenger.of(context).clearSnackBars()`
2. **Explicit duration for no-action snackbars:** Use 2-4 second duration
3. **Set persist: false if action but want auto-dismiss:** Override new default
4. **Use floating behavior:** `behavior: SnackBarBehavior.floating`

**Implementation pattern:**
```dart
// For copy confirmation (no action, should auto-dismiss)
ScaffoldMessenger.of(context).clearSnackBars();
ScaffoldMessenger.of(context).showSnackBar(
  const SnackBar(
    content: Text('Copied to clipboard'),
    duration: Duration(seconds: 2),
    behavior: SnackBarBehavior.floating,
  ),
);

// For retry action (with action, may want to auto-dismiss)
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(
    content: const Text('Message failed to send'),
    action: SnackBarAction(
      label: 'Retry',
      onPressed: _retryMessage,
    ),
    duration: const Duration(seconds: 10),
    // persist: false,  // Uncomment if you want auto-dismiss despite action
  ),
);
```

**Phase relevance:** All phases using snackbars (copy, retry, rename) must consider this.

**Sources:**
- [Flutter Docs - SnackBar with Action Breaking Change](https://docs.flutter.dev/release/breaking-changes/snackbar-with-action-behavior-update)
- [Flutter Docs - Display a Snackbar](https://docs.flutter.dev/cookbook/design/snackbars)

---

## Minor Pitfalls

Mistakes that cause annoyance but are easily fixable.

### Pitfall 7: Copy Button on User Messages

**What goes wrong:** Adding copy button to user messages (not just AI responses) clutters UI and provides little value.

**Prevention:**
- Only show copy button on assistant messages
- User already has the text they typed
- Check `message.role == MessageRole.assistant` before showing copy

**Phase relevance:** Clipboard copy phase - filter to assistant messages only.

---

### Pitfall 8: Retry Button Visible During Streaming

**What goes wrong:** Retry button shown while AI is still streaming, confusing users.

**Prevention:**
- Hide retry button when `isStreaming == true`
- Show retry button only after error state
- Disable (not hide) if you want consistent layout

**Phase relevance:** Message retry phase - check isStreaming state.

---

### Pitfall 9: Empty Title After Rename

**What goes wrong:** User clears title field and saves, thread has no visible name.

**Prevention:**
- Validate that title is not empty or whitespace-only
- Or fallback to default name like "Untitled Conversation"
- Existing create dialog allows empty (different UX for create vs rename)

**Phase relevance:** Thread rename phase - decide on validation rules.

---

### Pitfall 10: OAuth Provider Info Not in Auth State

**What goes wrong:** Settings screen shows user email/name but not which provider they used (Google vs Microsoft). User forgets how they signed up.

**Prevention:**
- Add `oauthProvider` field to `AuthProvider` state
- Fetch from `/auth/me` endpoint (already returns `oauth_provider`)
- Display icon next to profile in settings

**Current state (from codebase):**
```dart
// In AuthProvider - already fetches from getCurrentUser()
_userId = user['id'] as String?;
_email = user['email'] as String?;
_displayName = user['display_name'] as String?;
// MISSING: _oauthProvider = user['oauth_provider'] as String?;
```

**Phase relevance:** OAuth provider icon phase - add to AuthProvider state.

---

## Phase-Specific Warnings

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|----------------|------------|
| Retry Logic | State management | Duplicate messages on retry | Track failed message separately, remove before retry |
| Retry Logic | UI timing | Retry during streaming | Check `isStreaming` before allowing retry |
| Clipboard Copy | Cross-platform | Silent failures on web | Wrap in try-catch, show error snackbar |
| Clipboard Copy | UX | No feedback on success | Show confirmation snackbar for 2 seconds |
| Thread Rename | Memory | TextEditingController leak | Follow `ThreadCreateDialog` disposal pattern |
| Thread Rename | Context | Dialog from wrong context | Use callback, not build() |
| Thread Rename | Validation | Empty title allowed | Decide on validation rules for rename vs create |
| OAuth Display | Brand | Icon guideline violations | Use official packages or exact brand assets |
| OAuth Display | State | Provider not tracked | Add `oauthProvider` to `AuthProvider` |
| All Phases | Snackbars | Unexpected persistence | Clear previous snackbars, set explicit duration |

---

## Codebase-Specific Observations

### Existing Good Patterns to Follow

1. **ThreadCreateDialog TextEditingController disposal** (line 28-31): Correct pattern for controller lifecycle
2. **SettingsScreen mounted check** (line 48, 56): Correct async safety pattern
3. **ConversationProvider error handling** (line 146-160): Good error state management
4. **Delete with undo SnackBar** (line 209-220): Good undo pattern for retry reference

### Current Gaps to Address

1. **Message model lacks status field:** Cannot distinguish pending/sent/failed messages
2. **No retry mechanism exists:** `sendMessage()` has no retry-on-error logic
3. **MessageBubble has no copy button:** Widget is simple, needs action buttons
4. **AuthProvider lacks oauthProvider field:** User info fetched but provider not stored
5. **No thread rename dialog exists:** Must create based on `ThreadCreateDialog` pattern

---

## Confidence Assessment

| Area | Confidence | Source |
|------|------------|--------|
| Retry state management | HIGH | Codebase analysis + official Flutter patterns |
| Clipboard cross-platform | HIGH | Official Flutter docs + GitHub issues |
| TextEditingController disposal | HIGH | Official docs + codebase pattern verification |
| Snackbar behavior change | HIGH | Official Flutter breaking change docs |
| OAuth brand guidelines | HIGH | Official Google/Microsoft docs |
| Dialog context issues | MEDIUM | Community patterns, not verified with current Flutter version |

---

## Sources

### Official Documentation
- [Flutter Docs - Common Errors](https://docs.flutter.dev/testing/common-errors)
- [Flutter Docs - Display a Snackbar](https://docs.flutter.dev/cookbook/design/snackbars)
- [Flutter Docs - SnackBar Breaking Change](https://docs.flutter.dev/release/breaking-changes/snackbar-with-action-behavior-update)
- [Google Sign-In Branding Guidelines](https://developers.google.com/identity/branding-guidelines)

### Community Resources
- [DCM Blog - 15 Common Flutter Mistakes 2025](https://dcm.dev/blog/2025/03/24/fifteen-common-mistakes-flutter-dart-development)
- [LogRocket - Implementing Copy to Clipboard](https://blog.logrocket.com/implementing-copy-clipboard-flutter/)
- [LogRocket - Creating Dialogs in Flutter](https://blog.logrocket.com/creating-dialogs-flutter/)
- [Flutter Mastery Library - Error Handling and Retry](https://fluttermasterylibrary.com/6/9/2/3/)

### GitHub Issues
- [flutter/flutter #111388 - WebView clipboard restrictions](https://github.com/flutter/flutter/issues/111388)
- [flutter/flutter #61249 - TextEditingController used after disposed](https://github.com/flutter/flutter/issues/61249)

### Package Documentation
- [pub.dev - flutter_signin_button](https://pub.dev/packages/flutter_signin_button)
- [Flutter Gems - Authentication Packages](https://fluttergems.dev/authentication/)
