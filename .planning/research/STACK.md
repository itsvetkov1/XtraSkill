# Technology Stack

**Project:** BA Assistant — v3.2 Assistant File Generation & CLI Permissions
**Researched:** 2026-02-23
**Confidence:** HIGH — verified against live CLI binary (v2.1.50), existing codebase, and in-repo source files

---

## Scope

This document covers only **new additions or changes** for v3.2. The following
are already validated and in production — do not re-research:

- Flutter web + FastAPI + SQLite
- SSE streaming (sse-starlette, flutter_client_sse)
- Claude CLI subprocess adapter (ClaudeCLIAdapter, ClaudeProcessPool)
- BA artifact generation pipeline (save_artifact tool, export_service, ArtifactCard widget)
- AssistantConversationProvider, AssistantChatInput

---

## Recommended Stack

### Core Technologies (Unchanged — no new packages)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Claude CLI | 2.1.50 (installed) | AI subprocess for Assistant | `--dangerously-skip-permissions` confirmed present in this version |
| FastAPI | 0.115.x (existing) | Backend HTTP + SSE | No change; artifact routes already exist |
| Flutter | SDK ^3.9.2 (existing) | Frontend | ArtifactCard and dialog patterns already established |
| SQLite + SQLAlchemy | 2.0.x (existing) | Artifact persistence | No schema change beyond new enum value |
| python-docx | 1.2.0 (pinned) | Word export | Already used in export_service; reuse as-is |
| weasyprint | >=62,<68 (existing) | PDF export | Already used in export_service; reuse as-is |

### Supporting Libraries (Already in Project — No New Installs)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sse-starlette | 2.0.x | SSE streaming backend | Already streams artifact_created events in BA flow |
| flutter_client_sse | 2.0.0 | SSE client Flutter | Already handles artifact_created events; add handler in AssistantConversationProvider |
| file_saver | 0.2.14 | Browser download trigger | Already downloads MD/PDF/docx in ArtifactService |
| markdown (backend) | 3.5.x | Markdown → HTML for PDF | Already used in export_pdf() |
| flutter_markdown | 0.7.7+1 | Markdown rendering in chat | Already used in MarkdownMessage widget |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Alembic | Database migration | Required for new ArtifactType enum value; pattern already established in Phase 62 |

---

## Installation

**No new packages to install.** All required libraries are in `requirements.txt` and `pubspec.yaml` already.

```bash
# Backend — NO NEW PACKAGES

# Migration only (for new ArtifactType enum value):
cd /Users/a1testingmac/projects/XtraSkill/backend
venv/bin/alembic revision --autogenerate -m "add_generated_file_artifact_type"
venv/bin/alembic upgrade head

# Frontend — NO NEW PACKAGES
```

---

## Feature 1: `--dangerously-skip-permissions` CLI Flag

### What the Flag Does

Verified against Claude CLI v2.1.50 `--help` output:

```
--dangerously-skip-permissions    Bypass all permission checks.
                                  Recommended only for sandboxes with no internet access.
```

Without this flag, the CLI in `-p` (print/non-interactive) mode may pause to
request interactive permission to use filesystem tools (Bash, Edit, file writes).
That pause causes the subprocess to block on stdin input that never arrives,
hanging the entire SSE stream indefinitely for the end user.

A second related flag exists but is NOT what we want:

```
--allow-dangerously-skip-permissions   Enable bypassing as an *option*, without
                                       it being enabled by default.
```

The `--allow-*` variant only makes the option available; it does not activate it.
For a headless subprocess, the unconditional form is correct.

### Safety Profile

| Factor | Assessment |
|--------|------------|
| Network access | No change — flag does not grant network access |
| Filesystem access | Subprocess already runs in the backend venv directory with no elevated OS permissions |
| Risk equivalence | Same risk as the Anthropic API calls already made for BA threads |
| Scope | Only affects CLI-internal permission dialogs, not OS-level permissions |

The subprocess runs under the same user and directory as the FastAPI server. The
backend already executes arbitrary Claude API calls. Adding this flag is equivalent
to the existing `permission_mode="acceptEdits"` used in the BA flow via agent SDK.

### Change Location — `claude_cli_adapter.py`

Three command lists in the file require the new flag:

```python
# 1. ClaudeProcessPool._spawn_warm_process()
return await asyncio.create_subprocess_exec(
    self._cli_path,
    '-p',
    '--output-format', 'stream-json',
    '--verbose',
    '--dangerously-skip-permissions',   # ADD
    '--model', self._model,
    ...
)

# 2. ClaudeProcessPool._cold_spawn()
return await asyncio.create_subprocess_exec(
    self._cli_path,
    '-p',
    '--output-format', 'stream-json',
    '--verbose',
    '--dangerously-skip-permissions',   # ADD
    '--model', self._model,
    ...
)

# 3. ClaudeCLIAdapter.stream_chat() cold-spawn fallback path
cmd = [
    self.cli_path,
    "-p",
    "--output-format", "stream-json",
    "--verbose",
    "--dangerously-skip-permissions",   # ADD
    "--model", self.model,
]
```

**No new Python packages. No migration. No schema change.**

---

## Feature 2: Generic File Generation in Assistant

### Backend Changes

#### 2.1 New ArtifactType Enum Value (`models.py`)

The existing `ArtifactType` enum requires one new value:

```python
class ArtifactType(str, PyEnum):
    USER_STORIES = "user_stories"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    REQUIREMENTS_DOC = "requirements_doc"
    BRD = "brd"
    GENERATED_FILE = "generated_file"   # NEW — v3.2
```

This requires an Alembic migration to update the Enum column constraint. SQLite
handles this as a table recreation (existing Alembic migrations already use this
pattern). No other schema changes needed.

#### 2.2 PDF Template Fallback (export_service.py)

The existing `export_pdf()` already handles unknown artifact types:

```python
try:
    template = env.get_template(template_name)
except Exception:
    template = env.get_template("user_stories.html")  # Fallback
```

`generated_file` will use the `user_stories.html` fallback. **No new Jinja2 template needed.**

#### 2.3 Reuse Existing Backend Components

| Component | File | Action |
|-----------|------|--------|
| Artifact routes (GET, export) | `backend/app/routes/artifacts.py` | Reuse as-is |
| Export service | `backend/app/services/export_service.py` | Reuse as-is |
| save_artifact MCP tool | `backend/app/services/mcp_tools.py` | Reuse as-is |
| Artifact model | `backend/app/models.py` | Add enum value only |

#### 2.4 Assistant System Prompt

The Assistant thread system prompt is currently `""` (empty string in `ai_service.py`
line 931: `system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""`).

A lightweight system prompt must be added for `thread_type == "assistant"` to instruct
the CLI to call `save_artifact` when the user requests file generation. Without this,
the CLI has no instruction about when or how to generate files.

**No new service. The existing `_stream_agent_chat()` path in `ai_service.py` already
delivers the system prompt to `ClaudeCLIAdapter.stream_chat()`.**

#### 2.5 Generation Flow (No New Endpoint)

```
1. User opens GenerateFileDialog, types description
2. AssistantConversationProvider.generateFile(description) calls sendMessage()
   with prompt: "Generate a file: <description>"
3. POST /api/threads/{id}/chat → ai_service._stream_agent_chat()
4. ClaudeCLIAdapter.stream_chat() with --dangerously-skip-permissions
5. CLI calls save_artifact MCP tool with artifact_type="generated_file"
6. mcp_tools.save_artifact() stores Artifact in DB, yields artifact_created SSE event
7. AssistantConversationProvider handles ArtifactCreatedEvent
8. ArtifactCard rendered in chat message list
```

**No new API endpoint. Reuses existing POST /api/threads/{id}/chat.**

### Frontend Changes

#### 2.6 GenerateFileDialog (New Widget)

A modal dialog with multi-line `TextField` for free-text description. Pattern mirrors
existing `ModeChangeDialog` and `ArtifactTypePicker`:

```dart
class GenerateFileDialog extends StatefulWidget {
  static Future<String?> show(BuildContext context) {
    return showDialog<String>(
      context: context,
      builder: (context) => const GenerateFileDialog(),
    );
  }
  // ... TextField + Confirm/Cancel buttons
}
```

**No new Flutter packages. Uses `showDialog`, `TextField`, `TextButton`.**

#### 2.7 Generate File Button in AssistantChatInput

Add `IconButton` to the existing input row in
`frontend/lib/screens/assistant/widgets/assistant_chat_input.dart`:

```dart
// Between SkillSelector and send button
IconButton(
  icon: const Icon(Icons.file_present_outlined),
  tooltip: 'Generate file',
  onPressed: widget.enabled ? _handleGenerateFile : null,
),
```

Add `onGenerateFile` callback to `AssistantChatInput` constructor parallel to
`onSend`. The screen passes `provider.generateFile` as the callback.

**No new Flutter packages.**

#### 2.8 ArtifactCreatedEvent in AssistantConversationProvider

The provider currently has no `artifact_created` SSE handler. Three additions:

```dart
// State
List<Artifact> _artifacts = [];
Artifact? _pendingArtifact;

// SSE handler in sendMessage()
} else if (event is ArtifactCreatedEvent) {
    final artifact = await _artifactService.getArtifact(event.id);
    _pendingArtifact = artifact;
    _artifacts.add(artifact);
    notifyListeners();
}

// Clear on MessageComplete
_pendingArtifact = null;
```

**Reuse `ArtifactService` from `frontend/lib/services/artifact_service.dart` (already used by BA flow).**

#### 2.9 ArtifactCard in AssistantMessageBubble

The existing `ArtifactCard` widget at
`frontend/lib/screens/conversation/widgets/artifact_card.dart`
handles collapse/expand and MD/PDF/Word export.

`AssistantMessageBubble` renders the card conditionally when an artifact is
associated with the assistant message turn:

```dart
if (artifact != null)
  ArtifactCard(artifact: artifact, threadId: widget.threadId),
```

**No new widget. Reuse existing `ArtifactCard`.**

#### 2.10 ArtifactType Dart Enum

The existing `frontend/lib/models/artifact.dart` `ArtifactType` enum must gain:

```dart
generatedFile('generated_file', 'Generated File', Icons.file_present_outlined),
```

**No new Flutter packages.**

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| CLI permissions | `--dangerously-skip-permissions` flag | `--permission-mode bypassPermissions` | Both work; flag form is one command-line argument vs two; documented CLI pattern |
| CLI permissions | `--dangerously-skip-permissions` | `--allow-dangerously-skip-permissions` | `--allow-*` only enables the option, does not activate it — wrong for headless |
| File generation trigger | Dialog → regular chat POST | Separate `/generate-file` API endpoint | Avoids a second code path; dialog description becomes user message naturally |
| Artifact type | New `generated_file` enum value | Reuse `requirements_doc` | Semantically misleading; new value enables correct icon/display in UI |
| File gen UI in Assistant | Reuse existing `ArtifactCard` | New `AssistantArtifactCard` | Identical export needs; duplication would diverge over time |
| PDF template for generated_file | Use existing fallback | New Jinja2 template | Existing fallback works; template would only add CSS complexity |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `--allow-dangerously-skip-permissions` | Only enables as an option, does not bypass | `--dangerously-skip-permissions` |
| Separate `/generate-file` API endpoint | Maintenance burden; duplicates chat flow | POST to `/api/threads/{id}/chat` |
| New ArtifactCard widget for Assistant | Would duplicate and diverge | Reuse `conversation/widgets/artifact_card.dart` |
| New PDF Jinja2 template for generated_file | export_service already falls back to user_stories.html | No new template needed |
| New Flutter dialog package | Inconsistent with existing pattern | `showDialog` + custom StatefulWidget |

---

## Version Compatibility

| Package | Version in Use | Compatibility Notes |
|---------|---------------|---------------------|
| claude (CLI) | 2.1.50 | `--dangerously-skip-permissions` confirmed present and documented |
| python-docx | 1.2.0 (pinned) | Upgrade requires testing docx export; do not upgrade in this milestone |
| weasyprint | >=62,<68 | Upper bound for GTK API stability; keep |
| Alembic | >=1.13.0 | SQLite enum changes use table recreation; existing migrations prove pattern works |

---

## Sources

- Claude CLI `--help` output (version 2.1.50, verified 2026-02-23 on this machine) — HIGH confidence
- `/Users/a1testingmac/projects/XtraSkill/backend/app/services/llm/claude_cli_adapter.py` — existing command list construction (lines 604-609, 179-193, 203-214)
- `/Users/a1testingmac/projects/XtraSkill/backend/app/services/export_service.py` — confirmed fallback template behavior (lines 75-79)
- `/Users/a1testingmac/projects/XtraSkill/backend/app/models.py` — ArtifactType enum (lines 436-442) and Artifact model (lines 444-494)
- `/Users/a1testingmac/projects/XtraSkill/backend/app/routes/artifacts.py` — artifact routes, confirmed reusable without modification
- `/Users/a1testingmac/projects/XtraSkill/backend/app/services/ai_service.py` — system_prompt logic (line 931), _stream_agent_chat() flow
- `/Users/a1testingmac/projects/XtraSkill/frontend/lib/screens/conversation/widgets/artifact_card.dart` — confirmed reusable ArtifactCard
- `/Users/a1testingmac/projects/XtraSkill/frontend/lib/providers/assistant_conversation_provider.dart` — confirmed no artifact handling yet
- `/Users/a1testingmac/projects/XtraSkill/frontend/lib/screens/assistant/widgets/assistant_chat_input.dart` — existing input row layout
- `/Users/a1testingmac/projects/XtraSkill/frontend/pubspec.yaml` — confirmed all needed Flutter packages present
- `/Users/a1testingmac/projects/XtraSkill/backend/requirements.txt` — confirmed all needed Python packages present

---

*Stack research for: v3.2 Assistant File Generation & CLI Permissions*
*Researched: 2026-02-23*
