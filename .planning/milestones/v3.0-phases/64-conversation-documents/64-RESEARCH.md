# Phase 64: Conversation & Documents - Research

**Researched:** 2026-02-17
**Domain:** Flutter UI + FastAPI streaming + file upload + markdown rendering
**Confidence:** HIGH

## Summary

This phase implements end-to-end chat and document upload for Assistant threads, completing the Assistant workflow started in Phases 62-63. Users can send messages to Claude Code CLI, receive streaming responses with markdown formatting, upload documents for AI context, and select Claude Code skills without the BA-specific UX.

The implementation leverages existing patterns from BA ChatScreen (SSE streaming, thinking indicators, retry controls) but creates a new dedicated AssistantChatScreen with a cleaner UI. Document upload uses existing backend infrastructure (encryption, FTS5 indexing, project_id nullable pattern) extended to Assistant threads. Skills are discovered from `.claude/` directory and prepended to prompts transparently.

**Primary recommendation:** Reuse proven streaming/markdown/upload patterns from BA chat while building a minimal Assistant-specific UI layer. Use `flutter_markdown` with `flutter_highlight` for syntax-highlighted code blocks, `file_picker` for button-based upload, `flutter_dropzone` for drag-and-drop on web, and `super_clipboard` for image paste.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Chat screen design
- New dedicated AssistantChatScreen (not reusing BA ChatScreen)
- Clean chat view — no BA-specific buttons, no artifact viewer, no project context
- Attachment button for files
- Skills button — rugged-looking plus-in-a-square icon that opens a list of available Claude Code skills from .claude/
- When a skill is selected, it silently prepends to the prompt (user doesn't see "/skillname" in the chat — it behaves as if the prompt started with the skill context)
- Skills appear as a selectable element below the chat, not in the message stream

#### Document upload flow
- Three upload methods: button in input area, drag-and-drop onto chat area, and paste image
- Broad file type support: documents (PDF, DOCX, TXT, MD), images (PNG, JPG, GIF), spreadsheets (CSV, XLSX), code files — anything Claude can process
- While composing: removable chip/pill above the text field showing filename
- After sending: inline card/thumbnail in the user's message bubble
- Documents persist for the entire thread — once uploaded, available as context for all future messages in that thread

#### Streaming & indicators
- Thinking indicator with elapsed time — same pattern as existing BA chat
- Copy + retry controls on each AI response message
- Error handling: clear partial response on streaming error, show error message, auto-retry once
- Full markdown rendering — formatted output (like Ctrl+Shift+V in VS Code): headers, code blocks with syntax highlighting, tables, lists

#### Input area controls
- Layout: attachment button on the left, skills button + send button grouped on the right
- Multi-line text input by default (3-4 lines tall)
- Enter sends the message, Shift+Enter for newline
- Skill indicator: small colored chip above the text field showing selected skill name, with X to remove

### Claude's Discretion
- Exact styling and spacing of the chat screen
- Skills list UI (popup menu, bottom sheet, etc.)
- Drag-and-drop visual feedback design
- Image paste detection implementation
- Auto-retry timing and backoff on streaming errors

### Specific Ideas
- Skills come from Claude Code skills in the .claude/ directory — same skills available in Claude Code CLI
- Markdown should be rendered formatted, not as raw markdown — "like Ctrl+Shift+V in VS Code" (paste without formatting shows rendered markdown)
- The skill selection should feel integrated, not like a command — user picks skill, sees chip, types their message naturally

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-03 | Assistant conversation screen works end-to-end (send message, streaming response) | SSE streaming patterns (flutter_http_sse), ConversationProvider patterns, claude_cli_adapter integration |
| UI-04 | User can upload documents for context within Assistant threads | Document model (project_id nullable), file_picker + flutter_dropzone + super_clipboard, backend document routes reusable |

</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flutter_markdown | Latest (0.7.x) | Markdown rendering in Flutter | Official Flutter package, widely used, supports CommonMark/GFM |
| flutter_highlight | Latest (0.7.x) | Syntax highlighting for code blocks | De facto standard for code highlighting in Flutter Markdown |
| file_picker | 10.3.8+ | Native file picker dialog | Cross-platform, already in project, supports web/mobile/desktop |
| flutter_dropzone | Latest (4.x) | Web-only drag-and-drop | Web-specific drag-and-drop handling, federated plugin pattern |
| super_clipboard | Latest (0.9.x) | Cross-platform clipboard with image support | Most comprehensive clipboard package for image paste on web |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| markdown_widget | Alternative to flutter_markdown | Built-in syntax highlighting | Only if flutter_markdown + flutter_highlight proves insufficient |
| provider | Already in project | State management | Reuse existing ConversationProvider patterns |
| sse_starlette | Already in backend | SSE streaming (Python) | Backend streaming endpoint (already implemented) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| flutter_markdown | markdown_widget | Heavier, more features (TOC, LaTeX) but unnecessary for Assistant chat |
| flutter_dropzone | desktop_drop | Desktop-only, doesn't work on web (Flutter Web is primary platform) |
| super_clipboard | pasteboard | Less robust on web, requires more platform-specific code |

**Installation:**
```bash
# Frontend (Flutter)
cd frontend
flutter pub add flutter_markdown flutter_highlight
flutter pub add flutter_dropzone  # Web-only, conditional use
flutter pub add super_clipboard

# Backend (Python) - No new dependencies needed
# Document upload routes, encryption, FTS5 indexing already implemented
```

---

## Architecture Patterns

### Recommended Project Structure

**Frontend:**
```
frontend/lib/
├── screens/
│   ├── assistant/
│   │   ├── assistant_chat_screen.dart        # NEW: Main chat UI (clean, no BA elements)
│   │   ├── assistant_thread_list_screen.dart # EXISTING: From Phase 63
│   │   └── widgets/
│   │       ├── assistant_chat_input.dart      # NEW: Input with attachment + skills buttons
│   │       ├── skill_selector.dart            # NEW: Skill picker UI
│   │       ├── document_attachment_chip.dart  # NEW: Removable file chip
│   │       └── markdown_message.dart          # NEW: Markdown renderer with syntax highlighting
│   └── conversation/
│       └── widgets/
│           ├── chat_input.dart                # EXISTING: BA chat input (reference pattern)
│           └── message_bubble.dart            # EXISTING: BA message bubble (reference pattern)
├── providers/
│   └── assistant_conversation_provider.dart   # NEW: Chat state for Assistant threads
└── services/
    ├── ai_service.dart                        # EXISTING: SSE streaming (reuse)
    └── skill_service.dart                     # NEW: Discover skills from .claude/
```

**Backend:**
```
backend/app/
├── routes/
│   ├── conversations.py                       # EXISTING: SSE streaming endpoint (reuse)
│   └── documents.py                           # EXISTING: Upload routes (extend for Assistant)
├── services/
│   ├── llm/
│   │   └── claude_cli_adapter.py             # EXISTING: Claude Code CLI integration
│   └── document_search.py                     # EXISTING: FTS5 search (reuse)
└── models.py                                  # EXISTING: Document model has nullable project_id
```

---

### Pattern 1: SSE Streaming with Heartbeat

**What:** Server-Sent Events (SSE) with heartbeat comments to keep connection alive during long thinking periods.

**When to use:** AI streaming responses where thinking time can exceed proxy/browser timeouts (30-60s).

**Example:**
```dart
// Source: Existing ConversationProvider pattern (frontend/lib/providers/conversation_provider.dart)
Future<void> sendMessage(String content) async {
  _isStreaming = true;
  _streamingText = '';
  notifyListeners();

  try {
    await for (final event in _aiService.streamChat(_thread!.id, content)) {
      if (event is TextDeltaEvent) {
        _streamingText += event.text;
        notifyListeners();
      } else if (event is ToolExecutingEvent) {
        _statusMessage = event.status;
        notifyListeners();
      } else if (event is MessageCompleteEvent) {
        // Add complete message to list
        final assistantMessage = Message(
          id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
          role: MessageRole.assistant,
          content: _streamingText.isNotEmpty ? _streamingText : event.content,
          createdAt: DateTime.now(),
        );
        _messages.add(assistantMessage);
      }
    }
  } catch (e) {
    _error = e.toString();
    _hasPartialContent = _streamingText.isNotEmpty;
  } finally {
    _isStreaming = false;
    notifyListeners();
  }
}
```

**Backend heartbeat wrapper:**
```python
# Source: backend/app/services/ai_service.py (stream_with_heartbeat)
async def stream_with_heartbeat(
    data_gen: AsyncGenerator[Dict[str, Any], None],
    initial_delay: float = 5.0,
    heartbeat_interval: float = 15.0,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Wrap async generator with heartbeat comments during silence."""
    # SSE comments (format: ': heartbeat\\n\\n') keep connection alive
    # through proxies without visible output to client
```

---

### Pattern 2: Markdown Rendering with Syntax Highlighting

**What:** Render AI responses as formatted markdown with syntax-highlighted code blocks.

**When to use:** AI chat responses containing code, documentation, or structured text.

**Example:**
```dart
// NEW widget: frontend/lib/screens/assistant/widgets/markdown_message.dart
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/github.dart';

class MarkdownMessage extends StatelessWidget {
  final String content;

  const MarkdownMessage({required this.content});

  @override
  Widget build(BuildContext context) {
    return MarkdownBody(
      data: content,
      selectable: true,
      builders: {
        'code': CodeBlockBuilder(),  // Custom code block with syntax highlighting
      },
      styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
        codeblockDecoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }
}

class CodeBlockBuilder extends MarkdownElementBuilder {
  @override
  Widget visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    final language = element.attributes['class']?.split('-').last ?? 'plaintext';
    final code = element.textContent;

    return HighlightView(
      code,
      language: language,
      theme: githubTheme,
      padding: EdgeInsets.all(12),
      textStyle: TextStyle(fontFamily: 'monospace', fontSize: 14),
    );
  }
}
```

**Sources:**
- [flutter_markdown](https://pub.dev/packages/flutter_markdown)
- [flutter_highlight](https://pub.dev/packages/flutter_highlight)
- [Syntax highlighting GitHub Gist](https://gist.github.com/X-Wei/7370ec7823f9be40a91feb127627586d)

---

### Pattern 3: Multi-Method Document Upload

**What:** Support three upload methods (button, drag-drop, paste) with unified handling.

**When to use:** File attachment UI where users expect flexible input methods.

**Example:**
```dart
// NEW widget: frontend/lib/screens/assistant/widgets/assistant_chat_input.dart
import 'package:file_picker/file_picker.dart';
import 'package:flutter_dropzone/flutter_dropzone.dart';
import 'package:super_clipboard/super_clipboard.dart';

class AssistantChatInput extends StatefulWidget {
  final Function(String text, List<PlatformFile>? files) onSend;

  @override
  State<AssistantChatInput> createState() => _AssistantChatInputState();
}

class _AssistantChatInputState extends State<AssistantChatInput> {
  List<PlatformFile> _attachedFiles = [];
  late DropzoneViewController _dropzoneController;

  // Method 1: Button picker
  Future<void> _pickFiles() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      type: FileType.any,
    );
    if (result != null) {
      setState(() => _attachedFiles.addAll(result.files));
    }
  }

  // Method 2: Drag-and-drop (web only)
  Future<void> _onDrop(dynamic event) async {
    final files = await _dropzoneController.getFilesData(event);
    // Convert to PlatformFile and add to _attachedFiles
  }

  // Method 3: Paste from clipboard
  Future<void> _handlePaste() async {
    final clipboard = SystemClipboard.instance;
    if (clipboard == null) return;

    final reader = await clipboard.read();
    if (reader.canProvide(Formats.png)) {
      final pngData = await reader.readFile(Formats.png);
      // Create PlatformFile from bytes, add to _attachedFiles
    }
  }

  @override
  Widget build(BuildContext context) {
    return DropzoneView(
      onCreated: (ctrl) => _dropzoneController = ctrl,
      onDrop: _onDrop,
      child: Column(
        children: [
          // Attachment chips
          if (_attachedFiles.isNotEmpty)
            Wrap(
              children: _attachedFiles.map((file) =>
                DocumentAttachmentChip(
                  filename: file.name,
                  onRemove: () => setState(() => _attachedFiles.remove(file)),
                ),
              ).toList(),
            ),
          // Input row
          Row(
            children: [
              IconButton(
                icon: Icon(Icons.attach_file),
                onPressed: _pickFiles,
              ),
              Expanded(
                child: TextField(
                  // ... text input config
                  onSubmitted: (text) => widget.onSend(text, _attachedFiles),
                ),
              ),
              IconButton(
                icon: Icon(Icons.add_box_outlined),  // "rugged plus-in-square" for skills
                onPressed: _showSkillSelector,
              ),
              IconButton(
                icon: Icon(Icons.send),
                onPressed: () => widget.onSend(_controller.text, _attachedFiles),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
```

**Sources:**
- [file_picker package](https://pub.dev/packages/file_picker)
- [flutter_dropzone for web drag-and-drop](https://pub.dev/packages/flutter_dropzone)
- [super_clipboard for image paste](https://pub.dev/packages/super_clipboard)

---

### Pattern 4: Skill Discovery and Prepending

**What:** Discover Claude Code skills from `.claude/` directory and prepend selected skill to user's prompt.

**When to use:** Assistant threads where users want to leverage Claude Code's built-in skills.

**Example:**
```dart
// NEW service: frontend/lib/services/skill_service.dart
class SkillService {
  Future<List<Skill>> discoverSkills() async {
    // Read .claude/ directory (via backend API endpoint)
    // Parse SKILL.md files for skill metadata
    final response = await http.get('/api/skills');
    final skillsJson = jsonDecode(response.body);
    return skillsJson.map((s) => Skill.fromJson(s)).toList();
  }
}

class Skill {
  final String name;
  final String description;
  final String skillPath;  // e.g., ".claude/business-analyst/SKILL.md"
}

// In AssistantConversationProvider:
String _prependSkillToPrompt(String prompt, Skill? skill) {
  if (skill == null) return prompt;
  // Silently prepend skill context (user doesn't see this in UI)
  return "/skill ${skill.name}\n\n$prompt";
}
```

**Backend endpoint:**
```python
# NEW: backend/app/routes/skills.py
@router.get("/skills")
async def list_skills():
    """Discover skills from .claude/ directory."""
    skills_dir = Path(".claude")
    skills = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                # Parse skill metadata from SKILL.md frontmatter
                skills.append({
                    "name": skill_dir.name,
                    "description": extract_description(skill_file),
                    "skill_path": str(skill_file),
                })
    return skills
```

**Note:** Skills are prepended to the prompt transparently — user sees only their original message in the chat, but the backend sends the skill-prefixed version to Claude Code CLI.

---

### Anti-Patterns to Avoid

- **Don't render raw markdown text in chat bubbles:** Use `MarkdownBody` or `Markdown` widget, not `Text()` — users expect formatted output, not raw syntax.
- **Don't block UI during file upload:** Upload asynchronously, show progress indicator, keep input enabled for cancellation.
- **Don't duplicate ConversationProvider logic:** Reuse SSE streaming patterns, error handling, retry logic from existing BA chat — only create Assistant-specific provider for Assistant-only state (skills, thread_type filter).
- **Don't hardcode skill paths:** Discover skills dynamically from `.claude/` — skills may be added/removed by user.
- **Don't show skill syntax in chat:** Prepend skills transparently to prompt before sending to backend — user should see natural conversation, not command syntax.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown parsing and rendering | Custom markdown parser | `flutter_markdown` | Handles edge cases: nested lists, tables, inline code, link parsing, image rendering. CommonMark/GFM compliance is complex. |
| Code syntax highlighting | Regex-based highlighting | `flutter_highlight` | Supports 100+ languages, handles multi-line, nested scopes, theme support. Regex fails on edge cases (strings containing delimiters, comments). |
| File picker dialog | Custom file input | `file_picker` | Cross-platform (web/mobile/desktop), handles permissions, MIME type filtering, multi-select, file size validation. Web requires different APIs than mobile. |
| Drag-and-drop on web | `dart:html` manual handling | `flutter_dropzone` | Handles browser compatibility, drop zones, file extraction from DataTransfer, CORS issues, multi-file drops. |
| Clipboard image paste | Manual clipboard API | `super_clipboard` | Cross-platform clipboard access, image format detection (PNG/JPEG), permission handling, fallback for unsupported browsers. |
| SSE connection management | Raw HTTP with manual parsing | Existing AIService SSE client | Handles reconnection, Last-Event-ID tracking, backoff, heartbeat detection, error recovery. Already implemented and tested. |

**Key insight:** File handling, markdown rendering, and clipboard access have significant cross-platform differences (web vs mobile vs desktop) and edge cases (CORS, permissions, browser quirks, format support). Use battle-tested packages instead of reinventing.

---

## Common Pitfalls

### Pitfall 1: Web-Only Packages Breaking Mobile Builds

**What goes wrong:** Adding `flutter_dropzone` (web-only) breaks Android/iOS builds with "dart:html not found" errors.

**Why it happens:** Dart's conditional imports (`dart:html` vs `dart:io`) require federated plugin architecture. Direct `dart:html` imports fail on mobile.

**How to avoid:** Use `if (kIsWeb)` guards from `package:flutter/foundation.dart`. Wrap web-only code in conditional blocks:
```dart
import 'package:flutter/foundation.dart' show kIsWeb;

Widget _buildUploadArea() {
  if (kIsWeb) {
    return DropzoneView(
      onDrop: _handleDrop,
      child: _buildInputField(),
    );
  } else {
    // Mobile: no drag-drop, just button picker
    return _buildInputField();
  }
}
```

**Warning signs:** Build errors mentioning `dart:html`, `XMLHttpRequest`, `EventSource` on mobile platforms.

---

### Pitfall 2: Markdown Not Rendering Code Blocks with Syntax Highlighting

**What goes wrong:** Code blocks appear as plain text without syntax highlighting, or highlighting theme doesn't match app theme.

**Why it happens:** `flutter_markdown` doesn't include syntax highlighting by default. You must provide a custom `SyntaxHighlighter` or use `builders` to integrate `flutter_highlight`.

**How to avoid:** Create a custom `MarkdownElementBuilder` for code blocks:
```dart
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/github.dart';
import 'package:markdown/markdown.dart' as md;

class CodeElementBuilder extends MarkdownElementBuilder {
  @override
  Widget? visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    var language = '';
    if (element.attributes['class'] != null) {
      String lg = element.attributes['class'] as String;
      language = lg.substring(9);  // Remove 'language-' prefix
    }
    return HighlightView(
      element.textContent,
      language: language,
      theme: githubTheme,
      padding: EdgeInsets.all(12),
      textStyle: TextStyle(fontFamily: 'Courier', fontSize: 14),
    );
  }
}

// In MarkdownBody:
MarkdownBody(
  data: messageContent,
  builders: {
    'code': CodeElementBuilder(),
  },
)
```

**Warning signs:** Code blocks render as plain text, no color highlighting, monospace font missing.

---

### Pitfall 3: SSE Connection Dropping During Long Thinking Periods

**What goes wrong:** SSE connection times out (30-60s) during Claude's thinking phase, stream cuts off mid-response.

**Why it happens:** Proxies (Nginx, Cloudflare) and browsers close idle connections. Claude Code CLI can think for 30+ seconds without emitting events.

**How to avoid:** Backend already implements heartbeat comments (`: heartbeat\n\n`) every 15s during silence. Frontend should ignore comments:
```dart
// In SSE parsing:
if (event.startsWith(':')) {
  // Heartbeat comment — ignore, keeps connection alive
  continue;
}
```

Ensure backend uses `stream_with_heartbeat()` wrapper (already implemented in `ai_service.py`).

**Warning signs:** Streams cut off after 30-60s of thinking, "EventSource failed" errors in console, partial responses.

---

### Pitfall 4: Document Upload Creating Orphaned Files on Error

**What goes wrong:** User uploads file, backend saves to disk/DB, then parsing/encryption fails — file remains in storage but unusable.

**Why it happens:** Non-transactional file operations. If `encrypt()` or `index_document()` fails after DB insert, rollback doesn't delete file bytes.

**How to avoid:** Backend already uses transactional pattern — encrypt/parse BEFORE DB insert:
```python
# GOOD: Validate, parse, encrypt BEFORE DB insert
content_bytes = await file.read()
validate_file_security(content_bytes, file.content_type)
parsed = parser.parse(content_bytes)  # May raise exception
encrypted = encrypt_service.encrypt_binary(content_bytes)

# Only after all validation passes:
doc = Document(content_encrypted=encrypted, ...)
db.add(doc)
await db.commit()  # If this fails, no orphaned file
```

**Warning signs:** Growing storage usage, documents table has fewer rows than expected, users report "file uploaded but can't be accessed."

---

### Pitfall 5: Skill Selector Blocking Main Thread on Large Skill Directory

**What goes wrong:** Opening skill selector freezes UI for 1-2 seconds when `.claude/` has many skills.

**Why it happens:** Synchronous file I/O on main thread — reading all SKILL.md files blocks rendering.

**How to avoid:** Fetch skills via backend API (I/O on server), cache in provider:
```dart
class AssistantConversationProvider extends ChangeNotifier {
  List<Skill>? _cachedSkills;

  Future<List<Skill>> getSkills() async {
    if (_cachedSkills != null) return _cachedSkills!;

    // Fetch from backend asynchronously
    final skills = await _skillService.discoverSkills();
    _cachedSkills = skills;
    return skills;
  }
}

// In skill selector widget:
FutureBuilder<List<Skill>>(
  future: provider.getSkills(),
  builder: (context, snapshot) {
    if (snapshot.connectionState == ConnectionState.waiting) {
      return CircularProgressIndicator();
    }
    return ListView(children: snapshot.data!.map(...));
  },
)
```

**Warning signs:** UI freezes when opening skill selector, jank during rendering, ANR (Application Not Responding) on mobile.

---

## Code Examples

Verified patterns from official sources and existing codebase:

### Existing SSE Streaming Pattern (Reuse for Assistant)

```dart
// Source: frontend/lib/providers/conversation_provider.dart (lines 162-200)
// REUSE THIS PATTERN for AssistantConversationProvider
Future<void> sendMessage(String content) async {
  if (_thread == null || _isStreaming) return;

  _error = null;
  _lastFailedMessage = content;

  // Add user message optimistically
  final userMessage = Message(
    id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
    role: MessageRole.user,
    content: content,
    createdAt: DateTime.now(),
  );
  _messages.add(userMessage);

  // Start streaming
  _isStreaming = true;
  _streamingText = '';
  _statusMessage = null;
  notifyListeners();

  try {
    await for (final event in _aiService.streamChat(_thread!.id, content)) {
      if (event is TextDeltaEvent) {
        _streamingText += event.text;
        notifyListeners();
      } else if (event is ToolExecutingEvent) {
        _statusMessage = event.status;
        notifyListeners();
      } else if (event is MessageCompleteEvent) {
        final assistantMessage = Message(
          id: 'temp-assistant-${DateTime.now().millisecondsSinceEpoch}',
          role: MessageRole.assistant,
          content: _streamingText.isNotEmpty ? _streamingText : event.content,
          createdAt: DateTime.now(),
        );
        _messages.add(assistantMessage);
        _streamingText = '';
        _statusMessage = null;
        _lastFailedMessage = null;  // Success — clear retry state
      }
    }
  } catch (e) {
    _error = e.toString();
    _hasPartialContent = _streamingText.isNotEmpty;
  } finally {
    _isStreaming = false;
    notifyListeners();
  }
}
```

---

### Existing Document Upload Pattern (Extend for Assistant)

```python
# Source: backend/app/routes/documents.py (lines 37-100)
# EXTEND THIS to support Assistant threads (thread_id instead of project_id)
@router.post("/threads/{thread_id}/documents", status_code=201)
async def upload_document_to_thread(
    thread_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload document to Assistant thread."""
    # Validate thread access and ownership
    thread = await validate_thread_access(db, thread_id, current_user["user_id"])

    # Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Read and validate
    content_bytes = await file.read()
    validate_file_security(content_bytes, file.content_type)

    # Parse
    parser = ParserFactory.get_parser(file.content_type)
    parser.validate_security(content_bytes)
    parsed = parser.parse(content_bytes)

    # Encrypt
    if ParserFactory.is_rich_format(file.content_type):
        encrypted = get_encryption_service().encrypt_binary(content_bytes)
    else:
        encrypted = get_encryption_service().encrypt_document(parsed["text"])

    # Create document with project_id=None for Assistant threads
    doc = Document(
        project_id=None,  # Assistant threads have no project
        filename=file.filename or "untitled",
        content_type=file.content_type,
        content_encrypted=encrypted,
        content_text=parsed["text"],
        metadata_json=json.dumps(parsed.get("metadata", {})),
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Index for search
    await index_document(db, doc.id)

    return {"id": doc.id, "filename": doc.filename}
```

---

### Web-Only Drag-and-Drop Integration

```dart
// Source: Research — flutter_dropzone package example
// NEW widget for AssistantChatInput
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_dropzone/flutter_dropzone.dart';

Widget _buildChatInputArea() {
  if (kIsWeb) {
    // Web: wrap with drag-drop zone
    return Stack(
      children: [
        DropzoneView(
          operation: DragOperation.copy,
          cursor: CursorType.grab,
          onCreated: (ctrl) => _dropzoneController = ctrl,
          onDrop: (event) async {
            final files = await _dropzoneController.getFilesData(event);
            setState(() {
              for (var file in files) {
                _attachedFiles.add(PlatformFile(
                  name: file.name,
                  size: file.size,
                  bytes: file.bytes,
                ));
              }
            });
          },
          onHover: () => setState(() => _isDragging = true),
          onLeave: () => setState(() => _isDragging = false),
          child: _buildInputField(),
        ),
        if (_isDragging)
          Container(
            color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
            child: Center(
              child: Text('Drop files here', style: TextStyle(fontSize: 18)),
            ),
          ),
      ],
    );
  } else {
    // Mobile: no drag-drop, just input field
    return _buildInputField();
  }
}
```

---

### Clipboard Image Paste (Cross-Platform)

```dart
// Source: super_clipboard package documentation
// NEW: Handle paste events in AssistantChatInput
import 'package:super_clipboard/super_clipboard.dart';

Future<void> _handlePaste() async {
  final clipboard = SystemClipboard.instance;
  if (clipboard == null) {
    // Clipboard not available on this platform
    return;
  }

  final reader = await clipboard.read();

  // Check for image formats (PNG prioritized)
  if (reader.canProvide(Formats.png)) {
    final pngData = await reader.readFile(Formats.png);
    if (pngData != null) {
      final bytes = await pngData.readAll();
      setState(() {
        _attachedFiles.add(PlatformFile(
          name: 'pasted_image_${DateTime.now().millisecondsSinceEpoch}.png',
          size: bytes.length,
          bytes: bytes,
        ));
      });
    }
  } else if (reader.canProvide(Formats.jpeg)) {
    final jpegData = await reader.readFile(Formats.jpeg);
    if (jpegData != null) {
      final bytes = await jpegData.readAll();
      setState(() {
        _attachedFiles.add(PlatformFile(
          name: 'pasted_image_${DateTime.now().millisecondsSinceEpoch}.jpg',
          size: bytes.length,
          bytes: bytes,
        ));
      });
    }
  }
}

// Attach paste listener to text field
TextField(
  onSubmitted: (text) => _sendMessage(text),
  // Flutter doesn't expose onPaste directly, use FocusNode key handler
  focusNode: _focusNode,
  // ... or use Actions/Shortcuts for Ctrl+V detection
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `markdown` package only | `flutter_markdown` + `flutter_highlight` | 2024+ | Built-in syntax highlighting for code blocks, better rendering quality |
| Manual `dart:html` for drag-drop | `flutter_dropzone` federated plugin | 2023+ | Cross-platform compatibility, no build errors on mobile |
| `flutter_clipboard_manager` | `super_clipboard` | 2024+ | Image paste support on web, unified API across platforms |
| Manual SSE reconnection logic | `EventSource` with Last-Event-ID | Standard | Automatic reconnection with event deduplication |
| Text-only clipboard | Rich clipboard with image support | 2024+ | Users can paste screenshots directly into chat |

**Deprecated/outdated:**
- **`pasteboard` for web:** Poor web support, use `super_clipboard` instead (research: [Flutter Clipboard Image Picker Guide](https://medium.com/@julienjthomas/flutter-clipboard-image-picker-a-complete-guide-c30cd4925dfc))
- **`markdown_widget` for basic chat:** Overkill for Assistant chat (includes LaTeX, TOC) — use lighter `flutter_markdown` + `flutter_highlight`
- **Manual `XMLHttpRequest` SSE parsing in Flutter Web:** Use `http` package with `StreamedResponse` or EventSource wrapper packages

---

## Open Questions

1. **Should document thumbnails in message bubbles be interactive (tap to preview) or static images?**
   - What we know: BA chat has inline source chips (tap to navigate), document cards in artifact viewer
   - What's unclear: UX for document attachments in user messages — preview modal vs navigation vs inline expansion
   - Recommendation: Static thumbnail + filename chip (tap to preview in bottom sheet) — keeps message bubbles compact, consistent with existing patterns

2. **Should skills persist across messages (sticky) or reset after each send?**
   - What we know: User decision specifies "selected skill silently prepends to the prompt"
   - What's unclear: If user selects a skill once, does it apply to all subsequent messages in the thread or just the next one?
   - Recommendation: One-time use with visual indicator (chip) — user selects skill, sends message, chip clears. For persistent skill, user can re-select. Prevents accidental skill pollution of conversation.

3. **How should Assistant threads handle document context from project-scoped documents?**
   - What we know: Assistant threads have no project association (API-03: validation prevents project_id)
   - What's unclear: If user uploads a document to a BA project, can they reference it in an Assistant thread?
   - Recommendation: Deferred to future (XMOD-01: "User can reference BA project documents from Assistant threads"). For v3.0, Assistant documents are thread-scoped only.

---

## Sources

### Primary (HIGH confidence)

**Markdown Rendering:**
- [flutter_markdown package](https://pub.dev/packages/flutter_markdown) — Official Flutter markdown rendering
- [flutter_highlight package](https://pub.dev/packages/flutter_highlight) — Syntax highlighting for code blocks
- [Syntax highlighter for flutter_markdown (GitHub Gist)](https://gist.github.com/X-Wei/7370ec7823f9be40a91feb127627586d) — Integration pattern

**File Handling:**
- [file_picker package](https://pub.dev/packages/file_picker) — Already in project (v10.3.8)
- [flutter_dropzone package](https://pub.dev/packages/flutter_dropzone) — Web-only drag-and-drop
- [super_clipboard package](https://pub.dev/packages/super_clipboard) — Cross-platform clipboard with image support
- [Flutter Clipboard Image Picker Guide (Medium)](https://medium.com/@julienjthomas/flutter-clipboard-image-picker-a-complete-guide-c30cd4925dfc) — Image paste implementation

**SSE Streaming:**
- [flutter_http_sse GitHub](https://github.com/ElshiatyTube/flutter_http_sse) — SSE with exponential backoff (max 5 retries)
- [Server-Sent Events with Flutter (Medium)](https://medium.com/flutter-community/server-sent-events-sse-with-flutter-cf331f978b4f) — Error handling patterns
- Existing codebase: `backend/app/services/ai_service.py` — `stream_with_heartbeat()` implementation

**Backend Patterns:**
- Existing codebase: `backend/app/routes/documents.py` — Document upload with encryption and FTS5 indexing
- Existing codebase: `backend/app/routes/conversations.py` — SSE streaming endpoint with AIService integration
- Existing codebase: `backend/app/services/llm/claude_cli_adapter.py` — Claude Code CLI subprocess integration

### Secondary (MEDIUM confidence)

- [Top Flutter File Picker packages (Flutter Gems)](https://fluttergems.dev/file-picker/) — Comparison of file picker packages
- [Mastering Clipboard Operations in Flutter Web (Medium)](https://wingch-apps.medium.com/mastering-clipboard-operations-in-flutter-web-a-step-by-step-guide-to-copying-widgets-as-images-e911d395c621) — Web-specific clipboard patterns

### Tertiary (LOW confidence)

- None — All findings verified against official package documentation or existing codebase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All packages are official/widely-used, already in project (file_picker) or standard for use case
- Architecture: HIGH — Reusing proven patterns from existing ConversationProvider, document upload, SSE streaming
- Pitfalls: HIGH — Based on existing codebase patterns and official package documentation warnings

**Research date:** 2026-02-17
**Valid until:** 60 days (stable Flutter ecosystem, packages mature)
