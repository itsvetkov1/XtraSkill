# Technology Stack: v1.9.2 Resilience & AI Transparency

**Project:** BA Assistant v1.9.2
**Researched:** 2026-02-02
**Research Mode:** Stack dimension for subsequent milestone

---

## Executive Summary

The v1.9.2 features (error resilience, token budget tracking, mode indicators, artifact UI, document attribution, file validation) can be implemented **primarily with existing packages** in the stack. Only two new packages are recommended: `connectivity_plus` for network detection and `eventflux` to replace `flutter_client_sse` for better reconnection handling. All other features use native Flutter widgets or minor extensions to existing code.

---

## Current Stack (For Reference)

### Frontend (Flutter)
| Package | Version | Purpose |
|---------|---------|---------|
| provider | ^6.1.5+1 | State management |
| dio | ^5.9.0 | HTTP requests |
| flutter_client_sse | ^2.0.0 | SSE streaming |
| go_router | ^17.0.1 | Navigation |
| shared_preferences | ^2.5.4 | Local persistence |
| file_picker | ^10.3.8 | File selection |
| flutter_secure_storage | ^10.0.0 | Secure token storage |

### Backend (FastAPI)
| Package | Version | Purpose |
|---------|---------|---------|
| sse-starlette | >=2.0.0 | SSE streaming |
| httpx | >=0.27.0 | HTTP client |
| anthropic | ==0.76.0 | Claude API |

---

## Recommended Additions

### Frontend: New Packages

| Package | Version | Purpose | Why Needed |
|---------|---------|---------|------------|
| **connectivity_plus** | ^7.0.0 | Network state detection | Detect offline state to show appropriate UI before attempting SSE reconnection |
| **eventflux** | ^2.2.1 | SSE with auto-reconnect | Replaces flutter_client_sse; provides built-in exponential backoff reconnection |

### Frontend: Existing Packages (No Changes)

| Feature | Package | Notes |
|---------|---------|-------|
| Token budget progress bar | Material (LinearProgressIndicator) | Built-in Flutter widget; dynamic color via percentage |
| Mode indicator | Material (Chip, Container) | Already implemented pattern in provider_indicator.dart |
| Artifact type picker | Material (DropdownButton) | Built-in; no need for dropdown_button2 for simple enum picker |
| File size validation | file_picker (existing) | PlatformFile.size property already available |
| Document attribution | Material (Text, InkWell) | Custom widget, no new packages |

### Backend: No New Packages Required

| Feature | Approach | Why No New Package |
|---------|----------|-------------------|
| Token threshold warnings | Extend token_tracking.py | Add threshold check functions (80%, 95%, 100%) |
| Heartbeat during streaming | Already implemented | stream_with_heartbeat() exists in ai_service.py |
| Connection resilience | SSE-starlette handles it | Headers already set; client-side reconnection is the gap |

---

## Feature-by-Feature Stack Decisions

### 1. Network Interruption Handling During SSE Streaming

**Problem:** Current `flutter_client_sse` has no built-in reconnection; connection drops are silent.

**Solution Stack:**

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Network detection | **connectivity_plus ^7.0.0** | Cross-platform network state monitoring; needed to differentiate "no network" from "server error" |
| SSE client | **eventflux ^2.2.1** | Auto-reconnect with exponential backoff; supports POST method (required for chat); actively maintained |
| State management | Provider (existing) | Add `ConnectionState` enum to ConversationProvider |
| Backend | sse-starlette (existing) | Already has heartbeat; add `X-Accel-Buffering: no` header |

**Why eventflux over alternatives:**
- `flutter_client_sse`: No auto-reconnect (current pain point)
- `flutter_http_sse`: Less mature, limited POST support documentation
- Native EventSource: Web-only, no POST support

**Migration effort:** Moderate - AIService.streamChat() needs rewrite, but same event structure.

**Confidence:** HIGH (eventflux docs verified, POST support confirmed)

---

### 2. Token Budget Tracking with Warning Thresholds

**Problem:** Backend enforces 100% budget limit (hard block); no warning before hitting limit.

**Solution Stack:**

| Layer | Technology | Rationale |
|-------|------------|-----------|
| UI Progress | LinearProgressIndicator (built-in) | Simple, matches existing UI; dynamic progressColor for thresholds |
| Threshold logic | Dart code in TokenUsage model | Add computed properties for threshold states |
| Backend API | Extend /auth/usage endpoint | Return threshold_warning field |
| Persistence | shared_preferences (existing) | Cache usage for offline display |

**Threshold color scheme:**
```dart
Color get budgetColor {
  if (costPercentage >= 1.0) return Colors.red;      // 100% - blocked
  if (costPercentage >= 0.95) return Colors.red;     // 95% - critical
  if (costPercentage >= 0.80) return Colors.orange;  // 80% - warning
  return Colors.green;                                // normal
}
```

**No new packages needed** - built-in LinearProgressIndicator supports:
- `value`: 0.0-1.0 percentage
- `backgroundColor`: track color
- `color`: progress color (dynamic based on threshold)

**Why NOT percent_indicator:**
- Adds dependency for feature achievable with built-in widget
- percent_indicator better suited for circular/decorative indicators

**Confidence:** HIGH (Flutter docs, existing codebase pattern)

---

### 3. Persistent Conversation Mode Indicator

**Problem:** Users need visual confirmation of which conversation mode is active.

**Solution Stack:**

| Layer | Technology | Rationale |
|-------|------------|-----------|
| UI Widget | Material Chip or custom Container | Matches existing ProviderIndicator pattern |
| State | Provider + SharedPreferences (existing) | Mode already tracked; just needs UI exposure |
| Persistence | shared_preferences (existing) | Already used for theme; same pattern |

**Implementation approach:**
- Extend existing `ProviderIndicator` widget or create sibling `ModeIndicator`
- Display near chat input (same area as provider badge)
- Use distinctive colors: Meeting Mode (blue), Document Refinement (green)

**No new packages needed.**

**Confidence:** HIGH (existing pattern in provider_indicator.dart)

---

### 4. Artifact Generation UI with Type Picker

**Problem:** Users need to explicitly request specific artifact types (BRD, user story, etc.).

**Solution Stack:**

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Picker UI | DropdownButton (built-in) | Simple enum selection; no complex features needed |
| State | Provider (existing) | Track selected artifact type |
| Backend | ArtifactType enum (existing) | Already defined in models.py |

**Why NOT dropdown_button2:**
- Overkill for simple enum picker (5-6 options max)
- Built-in DropdownButton + DropdownMenuItem sufficient
- dropdown_button2 better for searchable/multiselect scenarios

**Artifact types (from existing backend):**
```python
class ArtifactType(str, Enum):
    BRD = "brd"
    USER_STORY = "user_story"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    # etc.
```

**No new packages needed.**

**Confidence:** HIGH (existing enum in app/models.py)

---

### 5. Document Source Attribution in AI Responses

**Problem:** When AI cites uploaded documents, users need to see which document was referenced.

**Solution Stack:**

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Message parsing | Dart RegExp | Parse citation markers like `[Source: doc_name]` |
| UI | InkWell + Text widgets | Tappable citation links |
| Navigation | GoRouter (existing) | Deep link to document viewer |
| Backend | Modify AI prompt + tool response | Include document metadata in responses |

**Implementation approach:**
1. Backend: Modify `search_documents` tool to return document IDs and names
2. Backend: AI system prompt updated to include citations in format `[[doc:UUID:name]]`
3. Frontend: Parse message content for citation patterns
4. Frontend: Render citations as tappable chips that navigate to document viewer

**No new packages needed.**

**Confidence:** MEDIUM (requires AI prompt engineering; parsing logic straightforward)

---

### 6. File Size Validation UX

**Problem:** Current upload shows generic error after user selects oversized file.

**Solution Stack:**

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Size check | file_picker PlatformFile.size (existing) | Already returns bytes; just need validation logic |
| UI feedback | SnackBar + AlertDialog (built-in) | Show friendly error before upload attempt |
| Constants | Frontend config | Define MAX_FILE_SIZE_BYTES |

**Validation flow:**
```dart
FilePickerResult? result = await FilePicker.platform.pickFiles(...);
if (result != null) {
  final file = result.files.single;
  const maxSize = 1 * 1024 * 1024; // 1MB

  if (file.size > maxSize) {
    // Show dialog: "File too large (X MB). Maximum allowed: 1 MB"
    return;
  }
  // Proceed with upload
}
```

**No new packages needed** - file_picker already provides size property.

**Confidence:** HIGH (verified in file_picker docs and existing code)

---

## Installation Commands

### Frontend (pubspec.yaml additions)

```yaml
dependencies:
  # NEW: Network connectivity detection
  connectivity_plus: ^7.0.0

  # NEW: SSE with auto-reconnect (replaces flutter_client_sse)
  eventflux: ^2.2.1
```

```bash
# Run in frontend directory
flutter pub add connectivity_plus
flutter pub add eventflux
flutter pub remove flutter_client_sse
```

### Backend (requirements.txt)

**No changes required** - all features use existing packages.

---

## Packages Explicitly NOT Recommended

| Package | Why Not |
|---------|---------|
| flutter_http_sse | Less mature than eventflux; POST support unclear |
| internet_connection_checker_plus | Overkill - connectivity_plus sufficient for UI feedback; actual connectivity verified by SSE attempt |
| percent_indicator | Built-in LinearProgressIndicator sufficient for budget bar |
| dropdown_button2 | Built-in DropdownButton sufficient for artifact type picker |
| retry | Manual retry logic in eventflux sufficient; no need for generic retry package |

---

## Risk Assessment

| Package | Risk | Mitigation |
|---------|------|------------|
| eventflux | Platform support: Web marked as "experimental" | Test thoroughly on web; fall back to existing flutter_client_sse if issues |
| connectivity_plus | iOS may report multiple values on reconnect | Use debouncing; verify with actual network request |

---

## Migration Notes

### Replacing flutter_client_sse with eventflux

**Before (current):**
```dart
final stream = SSEClient.subscribeToSSE(
  method: SSERequestType.POST,
  url: url,
  header: headers,
  body: {'content': message},
);
```

**After (eventflux):**
```dart
EventFlux.instance.connect(
  EventFluxConnectionType.post,
  url,
  header: headers,
  body: {'content': message},
  onSuccessCallback: (response) {
    response.stream?.listen((event) {
      // Handle events
    });
  },
  autoReconnect: true,
  reconnectConfig: ReconnectConfig(
    mode: ReconnectMode.exponential,
    interval: Duration(seconds: 1),
    maxAttempts: 5,
  ),
  onError: (error) {
    // Handle connection error
  },
);
```

---

## Sources

### Official Documentation
- [connectivity_plus pub.dev](https://pub.dev/packages/connectivity_plus) - v7.0.0, platform support verified
- [eventflux pub.dev](https://pub.dev/packages/eventflux) - v2.2.1, POST support and reconnect config verified
- [Flutter LinearProgressIndicator](https://api.flutter.dev/flutter/material/LinearProgressIndicator-class.html)
- [file_picker pub.dev](https://pub.dev/packages/file_picker) - size property verification

### Community Resources
- [Flutter SSE packages comparison - Flutter Gems](https://fluttergems.dev/server-sent-events/)
- [Network connectivity handling in Flutter - Medium](https://medium.com/@mksl/making-a-connection-handling-network-issues-in-flutter-217e7cfd30e9)

### Existing Codebase (Verified)
- `frontend/lib/services/ai_service.dart` - Current SSE implementation
- `frontend/lib/providers/conversation_provider.dart` - State management pattern
- `frontend/lib/screens/conversation/widgets/provider_indicator.dart` - Indicator widget pattern
- `backend/app/services/token_tracking.py` - Budget tracking exists
- `backend/app/services/ai_service.py` - Heartbeat already implemented

---

## Confidence Summary

| Area | Confidence | Notes |
|------|------------|-------|
| SSE Reconnection (eventflux) | HIGH | POST support verified, auto-reconnect documented |
| Network Detection (connectivity_plus) | HIGH | Mature package, platform limitations understood |
| Token Budget UI | HIGH | Built-in Flutter widgets, existing pattern |
| Mode Indicator | HIGH | Existing pattern in codebase |
| Artifact Type Picker | HIGH | Built-in DropdownButton |
| Document Attribution | MEDIUM | Requires AI prompt changes; parsing straightforward |
| File Size Validation | HIGH | file_picker already provides size property |

---

*Stack research complete. Ready for roadmap phase structure.*
