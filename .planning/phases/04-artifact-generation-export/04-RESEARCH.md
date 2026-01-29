# Phase 4: Artifact Generation & Export - Research

**Researched:** 2026-01-24
**Domain:** Document generation (PDF, Word, Markdown) and artifact management
**Confidence:** HIGH

## Summary

This phase implements the core value proposition of the BA Assistant: converting AI conversations into professional business analysis deliverables. The implementation involves three key areas: (1) artifact generation via Claude Agent SDK with autonomous tool use, (2) document export using python-docx for Word and WeasyPrint for PDF, and (3) a new Artifact data model with associated API endpoints and Flutter UI components.

The Agent SDK approach extends the existing ai_service.py tool execution pattern from Phase 3. Claude receives a `save_artifact` tool that allows it to autonomously create artifacts during conversations. This enables Claude to search documents for context first, then generate artifacts with full project awareness. Users can request artifacts naturally in chat ("generate user stories for login") and Claude decides when and how to use the tool.

**Primary recommendation:** Extend ai_service.py with `save_artifact` tool following existing `search_documents` pattern. Claude autonomously generates and saves artifacts during conversation flow. Backend stores artifacts in database, converts to PDF/Word on-demand via export endpoints.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-docx | 1.2.0 | Word document generation | De-facto Python library for .docx, no external deps, pure Python |
| WeasyPrint | 68.0 | PDF generation from HTML/CSS | Modern CSS support, no browser required, BSD license |
| Jinja2 | (bundled with FastAPI) | HTML templating for PDF | Already in stack, familiar template syntax |
| file_saver | 0.3.1 | Flutter file downloads | Cross-platform (Android, iOS, Web, Windows, macOS, Linux) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| markdown | 3.x | Convert markdown to HTML | For PDF generation pipeline |
| Pydantic | (existing) | Artifact data validation | Request/response models |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| WeasyPrint | ReportLab | ReportLab is lower-level (canvas-based), harder to style, but more precise control |
| WeasyPrint | fpdf2 | Simpler but less CSS support, good for basic PDFs only |
| python-docx | docx-template | Template-based approach, better for complex fixed templates |
| file_saver | url_launcher | url_launcher works but file_saver has better cross-platform download UX |

**Installation:**
```bash
# Backend
pip install python-docx==1.2.0 weasyprint==68.0 markdown

# Frontend (pubspec.yaml)
file_saver: ^0.3.1
```

**WeasyPrint Windows Note:** WeasyPrint requires GTK3 runtime on Windows. Install via MSYS2 or include in deployment instructions.

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── models.py              # Add Artifact model
│   ├── routes/
│   │   └── artifacts.py       # New: artifact CRUD + export endpoints
│   ├── services/
│   │   ├── artifact_generation.py  # New: Claude prompts for artifacts
│   │   └── export_service.py       # New: PDF/Word generation
│   └── templates/
│       └── artifacts/         # New: HTML templates for PDF export
│           ├── user_stories.html
│           ├── acceptance_criteria.html
│           └── requirements_doc.html

frontend/lib/
├── models/
│   └── artifact.dart          # New: Artifact model
├── providers/
│   └── artifact_provider.dart # New: Artifact state management
├── services/
│   └── artifact_service.dart  # New: API calls for artifacts
├── screens/
│   └── conversation/
│       └── widgets/
│           ├── quick_actions_bar.dart    # New: Generation buttons
│           └── artifact_message.dart     # New: Inline artifact display
```

### Pattern 1: Artifact Data Model
**What:** Store artifacts as JSON with type, markdown content, and metadata
**When to use:** For all generated artifacts
**Example:**
```python
# Source: Custom design based on existing models.py patterns
class ArtifactType(str, PyEnum):
    USER_STORIES = "user_stories"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    REQUIREMENTS_DOC = "requirements_doc"

class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType, native_enum=False, length=30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)  # Generated markdown
    content_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Structured data for programmatic access
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    thread: Mapped["Thread"] = relationship(back_populates="artifacts")
```

### Pattern 2: Claude Agent SDK with save_artifact Tool
**What:** Extend existing tool execution pattern with artifact generation capability
**When to use:** For all artifact generation - Claude autonomously decides when to create artifacts
**Example:**
```python
# Source: Extension of existing ai_service.py tool pattern
SAVE_ARTIFACT_TOOL = {
    "name": "save_artifact",
    "description": """Save a business analysis artifact to the current conversation thread.

USE THIS TOOL WHEN:
- User requests user stories, acceptance criteria, or requirements documents
- You have gathered enough context from conversation and documents to generate a complete artifact
- User asks to "create", "generate", "write", or "document" requirements

BEFORE USING:
- Consider using search_documents first to gather project context
- Review the full conversation history for all requirements discussed
- Ensure you capture ALL discussed requirements, not just recent ones

You may call this tool multiple times to save multiple artifacts (e.g., user stories AND acceptance criteria).""",
    "input_schema": {
        "type": "object",
        "properties": {
            "artifact_type": {
                "type": "string",
                "enum": ["user_stories", "acceptance_criteria", "requirements_doc"],
                "description": "Type of artifact: user_stories (Given/When/Then format), acceptance_criteria (testable checklist), requirements_doc (formal IEEE 830-style document)"
            },
            "title": {
                "type": "string",
                "description": "Descriptive title for the artifact, e.g., 'Login Feature - User Stories'"
            },
            "content_markdown": {
                "type": "string",
                "description": "Full artifact content in markdown format. Use proper headers, lists, and formatting."
            }
        },
        "required": ["artifact_type", "title", "content_markdown"]
    }
}

# Tool execution in ai_service.py
async def execute_tool(self, tool_name: str, tool_input: dict, project_id: str, thread_id: str, db) -> str:
    if tool_name == "save_artifact":
        artifact = Artifact(
            thread_id=thread_id,
            artifact_type=ArtifactType(tool_input["artifact_type"]),
            title=tool_input["title"],
            content_markdown=tool_input["content_markdown"]
        )
        db.add(artifact)
        await db.commit()
        return f"Artifact saved: {artifact.title} (ID: {artifact.id}). User can export as PDF, Word, or Markdown."

    elif tool_name == "search_documents":
        # Existing search logic...
```

**Key benefits over simple prompt approach:**
1. Claude can search documents first for better context
2. Claude can create multiple artifacts in one conversation turn
3. Consistent with Phase 3 tool execution pattern
4. More autonomous - Claude decides artifact structure based on conversation

### Pattern 3: Export Service with FastAPI FileResponse
**What:** Generate documents server-side and stream to client
**When to use:** For all export operations
**Example:**
```python
# Source: FastAPI official docs + WeasyPrint docs
from fastapi.responses import StreamingResponse
from weasyprint import HTML
from docx import Document
from io import BytesIO

async def export_pdf(artifact: Artifact) -> BytesIO:
    """Convert artifact to PDF using WeasyPrint."""
    html_content = render_artifact_html(artifact)
    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

async def export_docx(artifact: Artifact) -> BytesIO:
    """Convert artifact to Word document using python-docx."""
    doc = Document()
    doc.add_heading(artifact.title, level=0)

    # Parse markdown and add content
    for section in parse_markdown_sections(artifact.content_markdown):
        if section.type == "heading":
            doc.add_heading(section.text, level=section.level)
        elif section.type == "paragraph":
            doc.add_paragraph(section.text)
        elif section.type == "bullet":
            doc.add_paragraph(section.text, style='List Bullet')

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# FastAPI endpoint
@router.get("/artifacts/{artifact_id}/export/{format}")
async def export_artifact(
    artifact_id: str,
    format: Literal["pdf", "docx", "md"],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    artifact = await get_artifact_with_auth(artifact_id, current_user, db)

    if format == "md":
        return StreamingResponse(
            iter([artifact.content_markdown.encode()]),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{artifact.title}.md"'}
        )
    elif format == "pdf":
        pdf_buffer = await export_pdf(artifact)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{artifact.title}.pdf"'}
        )
    elif format == "docx":
        docx_buffer = await export_docx(artifact)
        return StreamingResponse(
            docx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{artifact.title}.docx"'}
        )
```

### Pattern 4: Flutter File Download
**What:** Download file bytes from API and save locally
**When to use:** For export button actions
**Example:**
```dart
// Source: file_saver package docs + Flutter patterns
import 'package:file_saver/file_saver.dart';
import 'package:dio/dio.dart';

Future<void> exportArtifact(String artifactId, String format, String title) async {
  final dio = Dio();
  final response = await dio.get(
    '$baseUrl/artifacts/$artifactId/export/$format',
    options: Options(
      responseType: ResponseType.bytes,
      headers: {'Authorization': 'Bearer $token'},
    ),
  );

  final extension = format == 'docx' ? 'docx' : format;
  final mimeType = _getMimeType(format);

  await FileSaver.instance.saveFile(
    name: title,
    bytes: Uint8List.fromList(response.data),
    ext: extension,
    mimeType: mimeType,
  );
}

MimeType _getMimeType(String format) {
  switch (format) {
    case 'pdf': return MimeType.pdf;
    case 'docx': return MimeType.microsoftWord;
    case 'md': return MimeType.text;
    default: return MimeType.other;
  }
}
```

### Pattern 5: Quick Actions Bar (Chat-based)
**What:** Row of buttons above chat input that send predefined messages to trigger artifact generation
**When to use:** Always visible in conversation screen for quick access
**Example:**
```dart
// Source: Custom design based on existing chat_input.dart patterns
class QuickActionsBar extends StatelessWidget {
  final void Function(String message) onSendMessage;  // Sends as chat message
  final bool enabled;

  const QuickActionsBar({
    required this.onSendMessage,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Row(
        children: [
          _ActionChip(
            icon: Icons.list_alt,
            label: 'User Stories',
            // Sends chat message that triggers Claude to use save_artifact tool
            onPressed: enabled ? () => onSendMessage('Generate user stories from our conversation') : null,
          ),
          const SizedBox(width: 8),
          _ActionChip(
            icon: Icons.check_circle_outline,
            label: 'Acceptance Criteria',
            onPressed: enabled ? () => onSendMessage('Generate acceptance criteria from our conversation') : null,
          ),
          const SizedBox(width: 8),
          _ActionChip(
            icon: Icons.description,
            label: 'Requirements Doc',
            onPressed: enabled ? () => onSendMessage('Generate a requirements document from our conversation') : null,
          ),
        ],
      ),
    );
  }
}
```

**Key insight:** Quick action buttons simply send chat messages. Claude autonomously decides to use the `save_artifact` tool based on the message content. This keeps all generation flowing through the same Agent SDK pipeline.

### Anti-Patterns to Avoid
- **Client-side PDF generation:** Avoid generating PDFs in Flutter; server-side is more reliable and consistent
- **Storing rendered HTML/PDF in database:** Store markdown source, render on-demand for flexibility
- **Separate generation endpoint:** Don't create a separate `/generate-artifact` endpoint; use existing chat flow with tool execution for consistency
- **Bypassing Agent SDK:** Don't call Claude directly for generation; use the tool execution pattern so Claude can search documents first
- **Hardcoded artifact templates in code:** Use Jinja2 templates for HTML export; easier to update styling

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF generation | Custom PDF writer | WeasyPrint | PDF spec is complex; CSS rendering handles layout |
| Word documents | XML manipulation | python-docx | OOXML format has many edge cases |
| Markdown parsing | Regex patterns | markdown library | Handles edge cases, extensions, proper escaping |
| File downloads | Manual blob/anchor | file_saver | Cross-platform handling, MIME types, permissions |
| Structured AI output | Free-form parsing | System prompts with format | Claude follows instructions; parsing is fragile |

**Key insight:** Document formats (PDF, DOCX) have decades of complexity. Libraries abstract this; custom solutions will miss edge cases around fonts, encoding, pagination, and platform differences.

## Common Pitfalls

### Pitfall 1: Large Context Truncation
**What goes wrong:** Generating artifacts from long conversations exceeds token limits
**Why it happens:** Conversation history grows; 150k budget fills up
**How to avoid:** Summarize older messages before generation; include only recent detailed context
**Warning signs:** API errors mentioning context length; truncated artifacts missing early requirements

### Pitfall 2: Inconsistent Artifact Formatting
**What goes wrong:** Claude produces varying formats for same artifact type
**Why it happens:** Vague prompts allow interpretation; different conversation flows
**How to avoid:** Use explicit format templates in system prompts with examples
**Warning signs:** User complaints about inconsistent output; difficulty parsing artifacts

### Pitfall 3: WeasyPrint Font Issues on Windows
**What goes wrong:** PDFs have missing characters or wrong fonts
**Why it happens:** WeasyPrint requires GTK3 and system fonts; Windows doesn't include these
**How to avoid:** Bundle web fonts in CSS; document GTK3 installation requirement
**Warning signs:** Boxes instead of characters; different fonts than expected

### Pitfall 4: File Download Fails on Web Platform
**What goes wrong:** file_saver works on mobile but fails on web
**Why it happens:** Web has different file system APIs; dart:html deprecation
**How to avoid:** file_saver 0.3.1 handles this; test on web explicitly
**Warning signs:** "Platform not supported" errors; download button does nothing on web

### Pitfall 5: Artifact Generation via Agent SDK
**What goes wrong:** User doesn't realize artifact was created; no visual confirmation
**Why it happens:** Tool execution happens mid-stream; artifact saved silently
**How to avoid:**
- Emit `artifact_created` SSE event when save_artifact tool executes
- Frontend displays artifact card inline in chat
- Claude confirms artifact creation in its response text
**Warning signs:** Users asking "did it save?"; artifacts created but not visible in UI

## Code Examples

Verified patterns from official sources:

### WeasyPrint HTML to PDF
```python
# Source: https://doc.courtbouillon.org/weasyprint/stable/
from weasyprint import HTML, CSS

html_content = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 2cm; }
        h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 0.5em; }
        h2 { color: #34a853; margin-top: 1.5em; }
        .user-story { background: #f8f9fa; padding: 1em; margin: 1em 0; border-radius: 8px; }
        .criteria { margin-left: 1.5em; }
        .criteria li { margin: 0.5em 0; }
    </style>
</head>
<body>
    <h1>User Stories</h1>
    {{ content }}
</body>
</html>
"""

def generate_pdf(markdown_content: str) -> bytes:
    # Convert markdown to HTML
    import markdown
    html_body = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])

    # Render with template
    from jinja2 import Template
    template = Template(html_content)
    full_html = template.render(content=html_body)

    # Generate PDF
    return HTML(string=full_html).write_pdf()
```

### python-docx Document Creation
```python
# Source: https://python-docx.readthedocs.io/en/latest/user/quickstart.html
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_requirements_doc(title: str, sections: list) -> bytes:
    doc = Document()

    # Title
    heading = doc.add_heading(title, level=0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for section in sections:
        # Section heading
        doc.add_heading(section['title'], level=1)

        # Description paragraph
        if section.get('description'):
            doc.add_paragraph(section['description'])

        # Bullet points
        for item in section.get('items', []):
            doc.add_paragraph(item, style='List Bullet')

        # Table if present
        if section.get('table'):
            table_data = section['table']
            table = doc.add_table(rows=1, cols=len(table_data['headers']))
            table.style = 'Table Grid'

            # Headers
            for i, header in enumerate(table_data['headers']):
                table.rows[0].cells[i].text = header

            # Rows
            for row_data in table_data['rows']:
                row = table.add_row()
                for i, cell in enumerate(row_data):
                    row.cells[i].text = str(cell)

    # Save to buffer
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
```

### Flutter File Download with file_saver
```dart
// Source: https://pub.dev/packages/file_saver
import 'dart:typed_data';
import 'package:file_saver/file_saver.dart';

Future<void> downloadArtifact({
  required Uint8List bytes,
  required String fileName,
  required String extension,
}) async {
  MimeType mimeType;
  switch (extension) {
    case 'pdf':
      mimeType = MimeType.pdf;
      break;
    case 'docx':
      mimeType = MimeType.microsoftWord;
      break;
    case 'md':
      mimeType = MimeType.text;
      break;
    default:
      mimeType = MimeType.other;
  }

  await FileSaver.instance.saveFile(
    name: fileName,
    bytes: bytes,
    ext: extension,
    mimeType: mimeType,
  );
}
```

## Artifact Templates

### User Story Format (Given/When/Then - Gherkin)
```markdown
## User Story 1: [Descriptive Title]

**As a** [user role/persona]
**I want** [feature/capability]
**So that** [business value/benefit]

### Acceptance Criteria

**Scenario 1: [Happy path description]**
- **Given** [initial context/precondition]
- **When** [action taken]
- **Then** [expected outcome]

**Scenario 2: [Edge case or alternate flow]**
- **Given** [initial context]
- **When** [action taken]
- **Then** [expected outcome]

### Notes
- [Edge case discussed in conversation]
- [Assumption made]
- [Dependency or constraint]

---
```

### Acceptance Criteria Format
```markdown
# Acceptance Criteria: [Feature Name]

## Overview
[Brief description of feature from conversation context]

## Criteria

### Functional Requirements
- [ ] [Criterion 1 - specific, testable]
- [ ] [Criterion 2 - specific, testable]

### Business Rules
- [ ] [Rule 1]
- [ ] [Rule 2]

### Edge Cases
- [ ] [Edge case 1: condition and expected behavior]
- [ ] [Edge case 2: condition and expected behavior]

### Non-Functional Requirements
- [ ] [Performance criterion if discussed]
- [ ] [Security criterion if discussed]

## Verification
[How to test/verify each criterion]
```

### Requirements Document Format (Based on IEEE 830)
```markdown
# Software Requirements Specification
## [Project/Feature Name]

### 1. Introduction
#### 1.1 Purpose
[Purpose of this document and the software being specified]

#### 1.2 Scope
[Scope of the software, what it will and won't do]

#### 1.3 Definitions
[Key terms from conversation]

### 2. Overall Description
#### 2.1 Product Perspective
[How this fits into larger system]

#### 2.2 User Classes and Characteristics
[User personas discussed]

#### 2.3 Operating Environment
[Technical constraints discussed]

#### 2.4 Assumptions and Dependencies
[Assumptions made during conversation]

### 3. Specific Requirements
#### 3.1 Functional Requirements
| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-01 | [Requirement text] | High/Medium/Low | [Notes] |

#### 3.2 Non-Functional Requirements
| ID | Requirement | Category | Notes |
|----|-------------|----------|-------|
| NFR-01 | [Requirement text] | Performance/Security/etc | [Notes] |

### 4. Appendices
#### 4.1 Conversation Reference
[Thread ID and date for traceability]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ReportLab canvas | WeasyPrint HTML/CSS | ~2020 | Much easier to style PDFs with CSS knowledge |
| dart:html for web downloads | web package + file_saver | 2024 | dart:html deprecated; new approach is future-proof |
| Free-form AI responses | Structured prompts | 2024 | Claude follows format instructions reliably |

**Deprecated/outdated:**
- dart:html: Deprecated by Flutter team; use `web` package or `file_saver` instead
- PyPDF2: Largely replaced by pypdf for PDF manipulation (though not relevant for generation)

## Open Questions

Things that couldn't be fully resolved:

1. **Artifact versioning**
   - What we know: Artifacts should persist and be editable
   - What's unclear: Should we track versions or just allow regeneration?
   - Recommendation: Start without versioning; regeneration creates new artifact. Versioning is Phase 5+ enhancement.

2. **WeasyPrint on Windows deployment**
   - What we know: Requires GTK3 runtime
   - What's unclear: Best approach for production Windows deployment
   - Recommendation: Document MSYS2 installation; consider Docker for production if Windows is deployment target.

3. **Artifact editing post-generation**
   - What we know: Users might want to tweak generated content
   - What's unclear: Should editing happen in-app or export-edit-reimport?
   - Recommendation: Start with view-only in Phase 4; editing is Phase 5+ enhancement. Export to Word for editing workflow.

## Sources

### Primary (HIGH confidence)
- python-docx 1.2.0 documentation: https://python-docx.readthedocs.io/en/latest/
- WeasyPrint 68.0 documentation: https://doc.courtbouillon.org/weasyprint/stable/
- FastAPI Custom Responses: https://fastapi.tiangolo.com/advanced/custom-response/
- file_saver pub.dev: https://pub.dev/packages/file_saver

### Secondary (MEDIUM confidence)
- Gherkin syntax best practices: https://cucumber.io/docs/terms/user-story/
- IEEE 830 SRS template: https://press.rebus.community/requirementsengineering/back-matter/appendix-c-ieee-830-template/
- WeasyPrint vs ReportLab comparison: https://dev.to/claudeprime/generate-pdfs-in-python-weasyprint-vs-reportlab-ifi

### Tertiary (LOW confidence)
- Windows GTK3 installation varies by environment; verify during implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official docs verified for python-docx 1.2.0, WeasyPrint 68.0, file_saver 0.3.1
- Architecture: HIGH - Patterns based on existing codebase structure and official library examples
- Pitfalls: MEDIUM - Based on common issues reported in community; verify during implementation
- Artifact templates: MEDIUM - Based on industry standards (Gherkin, IEEE 830) but templates are customizable

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (stable libraries, 30-day validity)
