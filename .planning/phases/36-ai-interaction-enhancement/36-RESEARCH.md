# Phase 36: AI Interaction Enhancement - Research

**Researched:** 2026-02-03
**Domain:** Artifact Generation UI, Source Attribution, Export Functionality
**Confidence:** HIGH

## Summary

This phase enhances AI interactions with two main features: (1) artifact generation UI with export capabilities, and (2) source document attribution showing which documents informed AI responses.

The backend already has artifact generation infrastructure via the `save_artifact` tool and `artifact_created` SSE events. The frontend needs to add: artifact type picker UI, collapsible artifact cards, export functionality, and source attribution chips. Export should download files from backend endpoints rather than generate locally (backend already supports MD, PDF, DOCX export).

Source attribution requires backend changes to track which documents were searched and return them in the response. Currently, `search_documents_tool` returns document IDs but this information is not surfaced to the frontend.

**Primary recommendation:** Leverage existing backend artifact/export infrastructure. Add a new `documents_used` SSE event or field in `message_complete` to enable source attribution.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already in Use)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flutter_client_sse | ^2.0.0 | SSE streaming | Already used for chat streaming |
| dio | ^5.9.0 | HTTP requests | Already used for API calls |
| file_picker | ^10.3.8 | File operations | Already in pubspec |

### New Required
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| file_saver | ^0.3.1 | Cross-platform file download | Supports Web, Android, iOS, Windows, macOS, Linux; handles downloads universally |
| url_launcher | ^6.3.2 | Open files (already present) | For 'Open' action after export |

### Backend (Already Present)
| Library | Purpose | Notes |
|---------|---------|-------|
| python-docx | Word export | In requirements.txt |
| weasyprint | PDF export | Requires GTK on Windows |
| markdown | HTML conversion | For PDF rendering |

### Not Needed - Backend Handles Export
| Don't Add | Why |
|-----------|-----|
| pdf (Flutter) | Backend already generates PDFs via `/artifacts/{id}/export/pdf` |
| docx_template | Backend already generates DOCX via `/artifacts/{id}/export/docx` |

**Installation:**
```bash
# Frontend
flutter pub add file_saver
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/
├── models/
│   └── artifact.dart              # Artifact model (NEW)
├── services/
│   └── artifact_service.dart      # Artifact API service (NEW)
├── providers/
│   └── conversation_provider.dart # Add artifact_created handling
├── screens/conversation/
│   └── widgets/
│       ├── artifact_card.dart       # Collapsible artifact display (NEW)
│       ├── artifact_type_picker.dart # Bottom sheet type picker (NEW)
│       ├── source_chips.dart        # Document source chips (NEW)
│       └── generate_artifact_button.dart # Input area button (NEW)
```

### Pattern 1: SSE Event-Driven Artifact Display

**What:** When `artifact_created` SSE event arrives, immediately display artifact card in message list without separate API call.

**When to use:** Real-time artifact display during chat streaming.

**Example:**
```dart
// In AIService - already exists but not handled in frontend
case 'artifact_created':
  yield ArtifactCreatedEvent(
    id: data['id'],
    artifactType: data['artifact_type'],
    title: data['title'],
  );
  break;

// In ConversationProvider
} else if (event is ArtifactCreatedEvent) {
  // Add artifact card to message list immediately
  _artifacts.add(Artifact.fromEvent(event));
  notifyListeners();
}
```

### Pattern 2: Download via Backend Export Endpoint

**What:** Frontend requests file from backend export endpoint, then triggers download.

**When to use:** All export operations (MD, PDF, DOCX).

**Example:**
```dart
// ArtifactService
Future<void> exportArtifact(String artifactId, String format) async {
  final url = '$apiBaseUrl/api/artifacts/$artifactId/export/$format';
  final response = await _dio.get(
    url,
    options: Options(
      responseType: ResponseType.bytes,
      headers: await _getHeaders(),
    ),
  );

  // Use file_saver for cross-platform download
  await FileSaver.instance.saveFile(
    name: 'artifact_$artifactId',
    bytes: response.data,
    ext: format,
    mimeType: _getMimeType(format),
  );
}
```

### Pattern 3: Source Attribution via SSE Event

**What:** Backend returns list of document IDs/filenames that were searched, frontend displays as chips.

**When to use:** Every AI response that used `search_documents` tool.

**Backend change needed:**
```python
# In agent_service.py search_documents_tool
# Track documents used and emit event or include in message_complete

# Option A: New SSE event
yield {
    "event": "documents_used",
    "data": json.dumps({
        "documents": [
            {"id": doc_id, "filename": filename}
            for doc_id, filename, _, _ in results[:5]
        ]
    })
}

# Option B: Include in message_complete
yield {
    "event": "message_complete",
    "data": json.dumps({
        "content": accumulated_text,
        "usage": usage_data,
        "documents_used": [...] # NEW
    })
}
```

### Anti-Patterns to Avoid
- **Generating PDFs client-side:** Backend already has export endpoints; don't duplicate.
- **Storing artifacts in local state only:** Artifacts are persisted server-side; use API.
- **Fetching full artifact content for display:** Use title/type from SSE event; fetch content only on expand.
- **Linear Row for source chips:** Use Wrap widget per PITFALL-13.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF generation | Flutter pdf package | Backend `/export/pdf` | Backend already has WeasyPrint with templates |
| Word generation | Flutter docx_template | Backend `/export/docx` | Backend already has python-docx |
| Cross-platform download | Platform-specific code | file_saver package | Handles Web, iOS, Android, Windows, macOS, Linux |
| Artifact persistence | Local storage | Backend API | Artifacts already stored in database |
| Document search tracking | Custom tracking | Extend search_documents_tool | Tool already has document IDs |

**Key insight:** The backend artifact infrastructure is complete. Frontend only needs UI for triggering generation (via chat prompts), displaying results (artifact cards), and downloading exports (via existing endpoints).

## Common Pitfalls

### Pitfall 1: RAG Source Attribution Hallucination (PITFALL-05)
**What goes wrong:** LLM cites documents it didn't actually use or misinterprets document content.
**Why it happens:** Chunk retrieval happens but LLM "fills in" from training data.
**How to avoid:**
- Track actual documents searched at backend level (not LLM-reported)
- Return document IDs from `search_documents_tool` results to frontend
- Source chips reflect backend tracking, not LLM claims
**Warning signs:** User clicks source and finds different content than expected.

### Pitfall 2: Artifact UI Overloads Message List (PITFALL-08)
**What goes wrong:** Full artifact content (50+ user stories) makes message list sluggish.
**Why it happens:** Rendering large markdown content in ListView.
**How to avoid:**
- Collapsed by default showing type + title only
- Full content fetched only on expand
- Use `ExpansionTile` or custom expand/collapse
- Consider separate full-screen view for very long artifacts
**Warning signs:** Scroll jank when artifact in view.

### Pitfall 3: Export Filename Meaningless (PITFALL-12)
**What goes wrong:** Downloads as `artifact.pdf` requiring manual rename.
**Why it happens:** Generic filename used.
**How to avoid:**
- Use pattern: `{artifact_type}_{title_slug}_{date}.{ext}`
- Example: `user_stories_login_flow_2026-02-03.md`
- Backend already sanitizes filename in export endpoint
**Warning signs:** User's Downloads folder full of `artifact (1).pdf` files.

### Pitfall 4: Source Chips Overflow (PITFALL-13)
**What goes wrong:** 10 document chips overflow horizontally.
**Why it happens:** Using Row instead of Wrap, no limit on visible chips.
**How to avoid:**
- Use `Wrap` widget with `spacing` and `runSpacing`
- Limit to 3-4 visible chips, show "+N more" expandable
- Truncate long filenames with tooltip
**Warning signs:** Horizontal scrollbar or cut-off chips.

### Pitfall 5: Artifact Type Mismatch
**What goes wrong:** User selects "User Stories" but backend creates "requirements_doc".
**Why it happens:** Frontend/backend use different type values.
**How to avoid:**
- Use exact enum values from backend: `user_stories`, `acceptance_criteria`, `requirements_doc`, `brd`
- Map display names to backend values explicitly
**Warning signs:** Artifact type shows wrong icon/label after creation.

## Code Examples

Verified patterns from existing codebase and official sources:

### Artifact Model
```dart
// frontend/lib/models/artifact.dart
enum ArtifactType {
  userStories('user_stories'),
  acceptanceCriteria('acceptance_criteria'),
  requirementsDoc('requirements_doc'),
  brd('brd');

  final String value;
  const ArtifactType(this.value);

  static ArtifactType fromJson(String json) {
    return ArtifactType.values.firstWhere(
      (t) => t.value == json,
      orElse: () => ArtifactType.requirementsDoc,
    );
  }

  String get displayName {
    switch (this) {
      case ArtifactType.userStories:
        return 'User Stories';
      case ArtifactType.acceptanceCriteria:
        return 'Acceptance Criteria';
      case ArtifactType.requirementsDoc:
        return 'Requirements Doc';
      case ArtifactType.brd:
        return 'BRD';
    }
  }

  IconData get icon {
    switch (this) {
      case ArtifactType.userStories:
        return Icons.list_alt;
      case ArtifactType.acceptanceCriteria:
        return Icons.checklist;
      case ArtifactType.requirementsDoc:
        return Icons.description;
      case ArtifactType.brd:
        return Icons.article;
    }
  }
}

class Artifact {
  final String id;
  final String threadId;
  final ArtifactType artifactType;
  final String title;
  final String? contentMarkdown; // Only loaded on expand
  final DateTime createdAt;

  Artifact({
    required this.id,
    required this.threadId,
    required this.artifactType,
    required this.title,
    this.contentMarkdown,
    required this.createdAt,
  });

  factory Artifact.fromJson(Map<String, dynamic> json) {
    return Artifact(
      id: json['id'],
      threadId: json['thread_id'],
      artifactType: ArtifactType.fromJson(json['artifact_type']),
      title: json['title'],
      contentMarkdown: json['content_markdown'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
```

### ArtifactCreatedEvent in AIService
```dart
// Add to frontend/lib/services/ai_service.dart

/// Artifact created event - generated artifact saved
class ArtifactCreatedEvent extends ChatEvent {
  final String id;
  final String artifactType;
  final String title;
  ArtifactCreatedEvent({
    required this.id,
    required this.artifactType,
    required this.title,
  });
}

// In streamChat switch statement:
case 'artifact_created':
  yield ArtifactCreatedEvent(
    id: data['id'] as String,
    artifactType: data['artifact_type'] as String,
    title: data['title'] as String,
  );
  break;
```

### Collapsible Artifact Card
```dart
// frontend/lib/screens/conversation/widgets/artifact_card.dart
class ArtifactCard extends StatefulWidget {
  final Artifact artifact;
  final VoidCallback? onExport;

  const ArtifactCard({
    super.key,
    required this.artifact,
    this.onExport,
  });

  @override
  State<ArtifactCard> createState() => _ArtifactCardState();
}

class _ArtifactCardState extends State<ArtifactCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = theme.colorScheme.primaryContainer;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: accent.withOpacity(0.1),
        border: Border(
          left: BorderSide(color: theme.colorScheme.primary, width: 4),
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header - always visible
          ListTile(
            leading: Icon(widget.artifact.artifactType.icon),
            title: Text(widget.artifact.title),
            subtitle: Text(widget.artifact.artifactType.displayName),
            trailing: IconButton(
              icon: Icon(_expanded ? Icons.expand_less : Icons.expand_more),
              onPressed: () => setState(() => _expanded = !_expanded),
            ),
            onTap: () => setState(() => _expanded = !_expanded),
          ),
          // Export buttons - always visible
          _buildExportRow(),
          // Content - only when expanded
          if (_expanded && widget.artifact.contentMarkdown != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: SelectableText(widget.artifact.contentMarkdown!),
            ),
        ],
      ),
    );
  }

  Widget _buildExportRow() {
    return Padding(
      padding: const EdgeInsets.only(left: 16, right: 16, bottom: 8),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            icon: const Icon(Icons.description_outlined, size: 20),
            tooltip: 'Export as Markdown',
            onPressed: () => _export('md'),
          ),
          IconButton(
            icon: const Icon(Icons.picture_as_pdf_outlined, size: 20),
            tooltip: 'Export as PDF',
            onPressed: () => _export('pdf'),
          ),
          IconButton(
            icon: const Icon(Icons.article_outlined, size: 20),
            tooltip: 'Export as Word',
            onPressed: () => _export('docx'),
          ),
        ],
      ),
    );
  }

  Future<void> _export(String format) async {
    // Implementation uses ArtifactService
  }
}
```

### Source Chips Widget
```dart
// frontend/lib/screens/conversation/widgets/source_chips.dart
class SourceChips extends StatefulWidget {
  final List<DocumentSource> sources;
  final void Function(String documentId)? onSourceTap;

  const SourceChips({
    super.key,
    required this.sources,
    this.onSourceTap,
  });

  @override
  State<SourceChips> createState() => _SourceChipsState();
}

class _SourceChipsState extends State<SourceChips> {
  bool _expanded = false;
  static const int _maxVisible = 3;

  @override
  Widget build(BuildContext context) {
    if (widget.sources.isEmpty) return const SizedBox.shrink();

    final visible = _expanded
        ? widget.sources
        : widget.sources.take(_maxVisible).toList();
    final overflow = widget.sources.length - _maxVisible;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.source, size: 16),
                const SizedBox(width: 4),
                Text(
                  _expanded
                      ? 'Hide sources'
                      : '${widget.sources.length} sources used',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ),
        if (_expanded)
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              for (final source in visible)
                ActionChip(
                  avatar: const Icon(Icons.description, size: 16),
                  label: Text(
                    _truncateFilename(source.filename),
                    style: const TextStyle(fontSize: 12),
                  ),
                  tooltip: source.filename, // Full name on hover
                  onPressed: () => widget.onSourceTap?.call(source.id),
                ),
              if (!_expanded && overflow > 0)
                ActionChip(
                  label: Text('+$overflow more'),
                  onPressed: () => setState(() => _expanded = true),
                ),
            ],
          ),
      ],
    );
  }

  String _truncateFilename(String filename) {
    if (filename.length <= 20) return filename;
    return '${filename.substring(0, 17)}...';
  }
}

class DocumentSource {
  final String id;
  final String filename;

  DocumentSource({required this.id, required this.filename});
}
```

### File Export with file_saver
```dart
// Source: https://pub.dev/packages/file_saver
import 'package:file_saver/file_saver.dart';

Future<void> exportArtifact(
  String artifactId,
  String format,
  String title,
) async {
  final url = '$apiBaseUrl/api/artifacts/$artifactId/export/$format';

  try {
    final response = await _dio.get<List<int>>(
      url,
      options: Options(
        responseType: ResponseType.bytes,
        headers: await _getHeaders(),
      ),
    );

    // Generate meaningful filename
    final safeName = title
        .replaceAll(RegExp(r'[^\w\s-]'), '')
        .replaceAll(RegExp(r'\s+'), '_')
        .toLowerCase();
    final date = DateTime.now().toIso8601String().split('T')[0];
    final filename = '${safeName}_$date';

    await FileSaver.instance.saveFile(
      name: filename,
      bytes: Uint8List.fromList(response.data!),
      ext: format,
      mimeType: _getMimeType(format),
    );

    // Show success snackbar
  } catch (e) {
    // Show error snackbar
  }
}

MimeType _getMimeType(String format) {
  switch (format) {
    case 'md':
      return MimeType.text;
    case 'pdf':
      return MimeType.pdf;
    case 'docx':
      return MimeType.microsoftWord;
    default:
      return MimeType.other;
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| dart:html for web download | package:web or file_saver | 2024+ | dart:html deprecated; use file_saver for cross-platform |
| Client-side PDF generation | Server-side generation | N/A | Backend already handles; no change needed |
| Message.sourceDocuments field | Separate SSE event/field | Phase 36 | Backend must emit documents_used data |

**Deprecated/outdated:**
- `dart:html`: Use `file_saver` or `package:web` instead
- Direct AnchorElement downloads: Use file_saver for platform abstraction

## Open Questions

Things that couldn't be fully resolved:

1. **Source Attribution Backend Change**
   - What we know: `search_documents_tool` has document IDs in results
   - What's unclear: Best way to surface to frontend (new SSE event vs field in message_complete)
   - Recommendation: Add `documents_used` array to `message_complete` event data

2. **Artifact Content Loading Strategy**
   - What we know: Collapsed cards don't need full content
   - What's unclear: Fetch on expand vs pre-fetch when scrolled near
   - Recommendation: Fetch on expand (lazy); keep it simple for v1

3. **Custom Artifact Type**
   - What we know: ART-02 mentions "Custom" option with free-form input
   - What's unclear: How backend handles custom type (not in ArtifactType enum)
   - Recommendation: Use `requirements_doc` as fallback for custom; or extend backend enum

## Sources

### Primary (HIGH confidence)
- Existing backend code: `backend/app/routes/artifacts.py` - Export endpoints verified
- Existing backend code: `backend/app/services/agent_service.py` - artifact_created event verified
- Existing backend code: `backend/app/services/export_service.py` - MD/PDF/DOCX export verified
- pub.dev/packages/file_saver - v0.3.1 documentation
- pub.dev/packages/pdf - v3.11.3 (not needed - backend handles)

### Secondary (MEDIUM confidence)
- PITFALLS-v1.9.2.md - Pitfall analysis verified against codebase
- ARCHITECTURE_v1.9.2.md - SSE event flow verified
- User story THREAD-008 - Source attribution requirements

### Tertiary (LOW confidence)
- WebSearch for Flutter PDF libraries - Used to verify not needed client-side

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified existing backend infrastructure
- Architecture: HIGH - Based on existing patterns in codebase
- Pitfalls: HIGH - From documented PITFALLS.md
- Source attribution backend: MEDIUM - Requires backend change, approach recommended but not implemented

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - stable domain)
