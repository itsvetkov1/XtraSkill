---
phase: 04-artifact-generation-export
plan: 02
subsystem: artifact-export
tags: [pdf-export, word-export, markdown-export, weasyprint, python-docx, jinja2]

dependency-graph:
  requires:
    - 04-01: Artifact model and API endpoints
    - 02: Thread and database models
  provides:
    - Export service with PDF, Word, Markdown converters
    - HTML templates for professional PDF styling
    - Export API endpoint with file download
  affects:
    - Frontend artifact display (export buttons)

tech-stack:
  added:
    - python-docx==1.2.0 (Word document generation)
    - weasyprint==68.0 (PDF generation, requires GTK on Windows)
    - markdown>=3.5 (Markdown to HTML conversion)
    - jinja2>=3.1.0 (HTML template rendering)
  patterns:
    - BytesIO buffer for streaming file responses
    - Jinja2 template inheritance for PDF styling
    - StreamingResponse with Content-Disposition headers

key-files:
  created:
    - backend/app/services/export_service.py
    - backend/app/templates/artifacts/base.html
    - backend/app/templates/artifacts/user_stories.html
    - backend/app/templates/artifacts/acceptance_criteria.html
    - backend/app/templates/artifacts/requirements_doc.html
  modified:
    - backend/requirements.txt
    - backend/app/routes/artifacts.py

decisions:
  - id: weasyprint-for-pdf
    choice: "WeasyPrint with Jinja2 templates for PDF generation"
    why: "Professional styling, HTML-based templating, consistent rendering"
  - id: python-docx-for-word
    choice: "python-docx with markdown parsing for Word export"
    why: "Native .docx format, no external dependencies, works on all platforms"
  - id: graceful-gtk-handling
    choice: "ImportError catch for WeasyPrint on Windows"
    why: "PDF export requires GTK; provide clear error message rather than crash"
  - id: streaming-response
    choice: "StreamingResponse with BytesIO buffers"
    why: "Efficient memory usage for large documents, browser download support"

metrics:
  duration: "3 min"
  completed: "2026-01-24"
  tasks: "3/3"
---

# Phase 04 Plan 02: Export Service Summary

**One-liner:** Backend export service with PDF (WeasyPrint), Word (python-docx), and Markdown converters plus API endpoint for file downloads.

## What Was Built

### 1. Export Dependencies and HTML Templates (Task 1)

**Files:** `backend/requirements.txt`, `backend/app/templates/artifacts/`

Added dependencies:
- `python-docx==1.2.0` - Word document generation
- `weasyprint==68.0` - PDF generation (requires GTK on Windows)
- `markdown>=3.5` - Markdown to HTML conversion
- `jinja2>=3.1.0` - Template rendering

Created HTML templates with professional styling:

```html
<!-- base.html - Professional A4 styling -->
@page { margin: 2cm; size: A4; }
body { font-family: 'Segoe UI', Tahoma, sans-serif; }
h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; }
h2 { color: #34a853; }
.user-story { background: #f8f9fa; border-left: 4px solid #1a73e8; }
```

Template files:
- `base.html` - Base template with full CSS styling
- `user_stories.html` - Extends base for user story artifacts
- `acceptance_criteria.html` - Extends base for AC artifacts
- `requirements_doc.html` - Extends base for requirements

### 2. Export Service with Format Converters (Task 2)

**File:** `backend/app/services/export_service.py`

Three export functions returning BytesIO buffers:

```python
def export_markdown(artifact: Artifact) -> BytesIO:
    """UTF-8 encoded markdown with title header."""

def export_pdf(artifact: Artifact) -> BytesIO:
    """HTML-to-PDF via WeasyPrint with Jinja2 templates."""
    # Graceful ImportError for Windows without GTK

def export_docx(artifact: Artifact) -> BytesIO:
    """Word document with heading/list parsing from markdown."""
```

DOCX converter handles:
- H1/H2/H3 headings
- Bullet lists (`- ` or `* `)
- Numbered lists (`1. `)
- Checkbox items (`- [ ]` and `- [x]`)
- Bold text (`**text**`)
- Regular paragraphs
- Metadata footer with timestamp

### 3. Export API Endpoint (Task 3)

**File:** `backend/app/routes/artifacts.py`

```
GET /api/artifacts/{artifact_id}/export/{format}
```

Parameters:
- `artifact_id`: UUID of artifact to export
- `format`: Export format (`md`, `pdf`, `docx`)

Response:
- `StreamingResponse` with file content
- `Content-Type`: Format-specific MIME type
- `Content-Disposition`: `attachment; filename="Title.format"`

Security:
- JWT authentication required
- Ownership validation (user owns artifact's thread's project)
- Returns 404 for unauthorized access (no information leakage)

Error handling:
- 404: Artifact not found or not owned
- 400: Unsupported format
- 500: PDF export failed (GTK not available)

## Technical Details

### MIME Types

| Format | MIME Type |
|--------|-----------|
| md | `text/markdown` |
| pdf | `application/pdf` |
| docx | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |

### PDF Export Requirements

WeasyPrint requires GTK3/Pango native libraries:
- **Linux**: Works out of box (GTK typically installed)
- **macOS**: `brew install pango`
- **Windows**: Install GTK3 or use Docker
- **Docker**: Works with Python base images

The export service catches `ImportError` and returns a helpful message if GTK is missing.

### Word Document Structure

```
[Title - Heading 0, centered]

[Content parsed from markdown:]
- Headings (H1, H2, H3)
- Bullet lists (List Bullet style)
- Numbered lists (List Number style)
- Paragraphs

[Footer - 9pt italic]
Generated by BA Assistant | 2026-01-24 21:35
```

## Commits

| Hash | Message |
|------|---------|
| b571369 | feat(04-02): add export dependencies and HTML templates |
| 2429d20 | feat(04-02): create export service with PDF, Word, Markdown converters |
| d18b386 | feat(04-02): add export endpoint for Markdown, PDF, and Word formats |

## Deviations from Plan

None - plan executed exactly as written.

**Note:** WeasyPrint confirmed to require GTK on Windows (expected per plan). The service handles this gracefully with ImportError catch and user-friendly error message.

## Testing

Manual verification completed:
1. Dependencies in requirements.txt: OK
2. Templates exist in backend/app/templates/artifacts/: OK
3. Export service functions importable: OK
4. Export endpoint registered at /artifacts/{id}/export/{format}: OK
5. Content types return correct MIME types: OK

## Phase 4 Completion

With 04-02 complete, Phase 4 (Artifact Generation & Export) is now finished:

**04-01 (Backend Artifact Generation):**
- Artifact database model
- save_artifact Claude tool
- artifact_created SSE event
- GET endpoints for list/detail

**04-02 (Export Service):**
- PDF export with WeasyPrint
- Word export with python-docx
- Markdown export
- Export API endpoint

**Remaining for full MVP:**
- Frontend artifact display (list view, detail view)
- Frontend export buttons triggering downloads
- End-to-end testing of artifact generation flow
