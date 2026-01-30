# Technology Stack: v1.6 UX Quick Wins

**Project:** BA Assistant - UX Improvements
**Researched:** 2026-01-30
**Scope:** Retry mechanism, clipboard access, inline editing, auth provider icons

## Executive Summary

All target features can be implemented using **Flutter SDK built-in APIs only**. No additional packages are required. This keeps the dependency footprint minimal and leverages well-documented, stable APIs.

---

## Recommended Stack

### No New Packages Required

| Feature | API/Class | Source | Notes |
|---------|-----------|--------|-------|
| Clipboard copy | `Clipboard.setData()` | `flutter/services.dart` | Built-in, async, cross-platform |
| Inline editing dialog | `showDialog()` + `TextFormField` | `flutter/material.dart` | Built-in Material dialog |
| Retry mechanism | Provider state + UI buttons | Existing Provider setup | State already has error handling |
| Auth provider icons | Material Icons | Built-in | Generic icons recommended |

**Rationale:** The existing stack (Flutter 3.9+, Provider, Dio) already has all the capabilities needed. Adding packages for these simple features would increase bundle size and maintenance burden without meaningful benefit.

---

## Feature Implementation Details

### 1. Clipboard Access

**API:** `Clipboard` class from `package:flutter/services.dart`

**Methods:**
```dart
// Copy text to clipboard
await Clipboard.setData(ClipboardData(text: 'content to copy'));

// Read from clipboard (if needed later)
ClipboardData? data = await Clipboard.getData(Clipboard.kTextPlain);
```

**Key Points:**
- Already available - no import changes needed (services.dart is Flutter SDK)
- Async operation - returns `Future<void>`
- Cross-platform: works on Web, Android, iOS, Desktop
- Breaking change note (Flutter 3.10+): Use empty string `''` to clear, not `null`

**User Feedback Pattern:**
```dart
await Clipboard.setData(ClipboardData(text: message.content));
if (context.mounted) {
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content: Text('Copied to clipboard')),
  );
}
```

**Confidence:** HIGH (Official Flutter API documentation verified)

**Source:** [Flutter Clipboard API](https://api.flutter.dev/flutter/services/Clipboard-class.html)

---

### 2. Inline Text Editing Dialog (Thread Rename)

**API:** `showDialog()` + `AlertDialog` + `TextFormField`

**Pattern:**
```dart
Future<String?> showRenameDialog({
  required BuildContext context,
  required String currentTitle,
}) async {
  final controller = TextEditingController(text: currentTitle);

  return showDialog<String>(
    context: context,
    barrierDismissible: false,
    builder: (dialogContext) => AlertDialog(
      title: const Text('Rename Thread'),
      content: TextFormField(
        controller: controller,
        autofocus: true,
        decoration: const InputDecoration(
          labelText: 'Title',
          hintText: 'Enter thread title',
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(dialogContext).pop(null),
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: () => Navigator.of(dialogContext).pop(controller.text),
          child: const Text('Save'),
        ),
      ],
    ),
  );
}
```

**Key Points:**
- Use `TextEditingController` for pre-filling current value
- `autofocus: true` for immediate keyboard input
- Return value via `Navigator.pop(value)` - `null` means cancelled
- `barrierDismissible: false` prevents accidental dismissal
- Existing `delete_confirmation_dialog.dart` follows this pattern - reuse structure

**Note:** The backend API may need a new endpoint for thread rename (`PATCH /api/threads/{id}` with `{ "title": "new title" }`). This is a backend consideration, not a Flutter stack issue.

**Confidence:** HIGH (Pattern matches existing codebase dialogs)

**Source:** [Flutter showDialog API](https://api.flutter.dev/flutter/material/showDialog.html)

---

### 3. Retry Mechanism UI

**API:** Existing Provider state management + conditional UI

**Current State:**
The codebase already has error handling infrastructure:
- `ConversationProvider` has `_error` field and `error` getter
- `ErrorEvent` class exists in `ai_service.dart`
- `ThreadListScreen` shows retry via SnackBar action (line 92-98)

**Implementation Pattern:**
```dart
// In ConversationProvider - store failed message for retry
String? _failedMessageContent;
String? get failedMessageContent => _failedMessageContent;

// On error during sendMessage:
_failedMessageContent = content;
_error = e.toString();

// Retry method:
Future<void> retryLastMessage() async {
  if (_failedMessageContent != null) {
    final content = _failedMessageContent!;
    _failedMessageContent = null;
    _error = null;
    await sendMessage(content);
  }
}
```

**UI Options:**
1. **Inline retry button** on the failed message bubble (RECOMMENDED)
2. **SnackBar with retry action** (matches existing delete pattern)
3. **Error banner** above input field with retry button

**Recommended:** Inline retry button on message bubble - most discoverable for users.

**Confidence:** HIGH (Uses existing patterns from codebase)

---

### 4. Auth Provider Icons

**API:** Material Icons (built-in) or simple text indicator

**Reality Check:** Material Icons does NOT include official brand logos (Google, Microsoft). Options:

| Option | Pros | Cons |
|--------|------|------|
| **A. Use generic icons** | No new deps, immediate | Less recognizable |
| **B. font_awesome_flutter** | Has brand icons | Adds ~2MB to bundle |
| **C. Custom SVG assets** | Exact logos, small | Manual asset management |
| **D. Text indicator** | Simplest, no icons needed | Less visual |

**Recommendation:** Option D (text indicator) or Option A (generic icons)

**Option D (Text Indicator - Simplest):**
```dart
// Settings screen - show auth method as text
Text('Signed in with Google')
Text('Signed in with Microsoft')
```

**Option A (Generic Icons):**
```dart
// Use cloud/account icons
Icon(Icons.account_circle) // Generic authenticated user
Icon(Icons.cloud) // Generic cloud/OAuth indicator
```

**Backend Consideration:** The auth provider type is not currently returned by `/api/users/me`. Backend would need to include `auth_provider: "google"` or `auth_provider: "microsoft"` in the response.

**Recommendation:** Start with text indicator ("Signed in with Google") - simple and clear. Defer brand icons to future enhancement if requested by users.

**Confidence:** MEDIUM (Depends on backend API changes)

---

## What NOT to Use

| Package | Why Not |
|---------|---------|
| `clipboard` package | Flutter's built-in `Clipboard` is sufficient for text |
| `retry` package | Simple UI retry doesn't need automatic exponential backoff |
| `font_awesome_flutter` | 2MB+ bundle addition for one or two brand icons - overkill |
| `fluttericon` | Custom icon packs unnecessary for this scope |
| Any "dialog" packages | Built-in `showDialog` covers all needs |
| `simple_icons` | SVG icon package - unnecessary complexity |

---

## Backend API Considerations

Features that may need backend changes:

| Feature | Backend Endpoint | Status | Priority |
|---------|------------------|--------|----------|
| Thread rename | `PATCH /api/threads/{id}` | Likely needs adding | HIGH |
| Auth provider type | `GET /api/users/me` response | Needs `auth_provider` field | LOW |

**Note:** Thread rename is essential for the feature. Auth provider display can start with what's available (email domain inference) before backend changes.

---

## Implementation Checklist

### Clipboard (Copy AI Response)
- [ ] Import `package:flutter/services.dart` in `message_bubble.dart`
- [ ] Add copy button to assistant message bubbles
- [ ] Show "Copied" SnackBar feedback
- [ ] Test on Web, Android

### Inline Editing (Thread Rename)
- [ ] Create `thread_rename_dialog.dart` (follow `delete_confirmation_dialog.dart` pattern)
- [ ] Add "Rename" option to thread PopupMenuButton
- [ ] Add `updateThread(id, title)` method to `ThreadService`
- [ ] Backend: Add `PATCH /api/threads/{id}` endpoint

### Retry Mechanism
- [ ] Add `_failedMessageContent` field to `ConversationProvider`
- [ ] Add `retryLastMessage()` method
- [ ] Show retry button inline on failed message
- [ ] Test error recovery flow

### Auth Provider Display
- [ ] Add text indicator to settings screen profile section
- [ ] (Optional) Backend: Add `auth_provider` to `/api/users/me` response

---

## Installation Summary

```yaml
# NO changes to pubspec.yaml required for core features
# Existing dependencies are sufficient:

dependencies:
  flutter:
    sdk: flutter
  provider: ^6.1.5+1    # Already installed - state management
  dio: ^5.9.0           # Already installed - HTTP requests
  # All other existing deps unchanged
```

**Total new dependencies: 0**

---

## Sources

- [Flutter Clipboard API Documentation](https://api.flutter.dev/flutter/services/Clipboard-class.html) - HIGH confidence
- [Flutter showDialog Documentation](https://api.flutter.dev/flutter/material/showDialog.html) - HIGH confidence
- [GeeksforGeeks - Flutter Copy to Clipboard](https://www.geeksforgeeks.org/flutter/flutter-add-copy-to-clipboard-without-package/) - MEDIUM confidence
- [LogRocket - Implementing copy to clipboard](https://blog.logrocket.com/implementing-copy-clipboard-flutter/) - MEDIUM confidence
- [font_awesome_flutter package](https://pub.dev/packages/font_awesome_flutter) - Reference only (not recommended)

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Clipboard | HIGH | Official Flutter SDK, well-documented, verified |
| Edit dialog | HIGH | Pattern already exists in codebase (`delete_confirmation_dialog.dart`) |
| Retry UI | HIGH | Uses existing Provider state patterns |
| Auth icons | MEDIUM | Depends on backend API changes; text indicator as fallback |
| No new deps | HIGH | All features achievable with Flutter SDK |

---

## Roadmap Implications

### Phase Structure Recommendation

Based on this research, features have no external dependencies blocking implementation:

1. **Clipboard copy** - Can start immediately (frontend only)
2. **Retry mechanism** - Can start immediately (frontend only)
3. **Thread rename** - Requires backend endpoint first, then frontend
4. **Auth provider icon** - Lowest priority, backend changes needed

**Suggested order:**
1. Clipboard + Retry (frontend-only, parallel)
2. Thread rename (backend then frontend, sequential)
3. Auth provider display (deferred or text-only MVP)

### No Additional Research Needed

All stack questions answered. Implementation can proceed directly.

---

*Research complete. All UX features achievable with existing Flutter SDK - zero new packages required.*
