# Project Milestones: Business Analyst Assistant

## v0.1-claude-code: Claude Code as AI Backend (Shipped: 2026-02-17)

**Delivered:** Claude Code CLI adapter integrated as a new LLM provider, enabling agent-based conversations with MCP tool access. Experiment concluded with CLI adapter adopted; formal quality comparison skipped.

**Phases completed:** 57-61 (11 plans, 1 skipped)

**Key accomplishments:**

- Shared MCP tool infrastructure (search_documents, save_artifact) extracted to reusable module
- Claude Agent SDK adapter with event stream translation to StreamChunk format
- Claude CLI subprocess adapter with JSON stream parsing, lifecycle management, and zombie process prevention
- Frontend provider integration with experimental badges and thread info panel
- Evaluation framework with test scenarios, quality rubric, and BRD generation (5 CLI BRDs produced)
- 3 bugs fixed during manual testing (broken pipe, projectless chat, text selection)

**Stats:**

- 96 files changed, +24,573 / -568 lines
- 5 phases, 11 plans executed (1 skipped)
- Branch: `feature/claude-code-backend` → merged to master
- 5 days from start to ship (2026-02-13 → 2026-02-17)

**Git range:** `a1c9c70` → `76d689b`

**What's next:** v3.0 — Assistant Foundation

---

## v2.1 Rich Document Support (Shipped: 2026-02-12)

**Delivered:** Full document parsing pipeline replacing text-only uploads with Excel, CSV, PDF, and Word support — including security validation, format-aware rendering, AI context integration, and round-trip export capabilities.

**Phases completed:** 54-56 (8 plans total)

**Key accomplishments:**

- Document parser infrastructure with 5 format-specific parsers (Excel, CSV, PDF, Word, Text) and factory routing
- Upload security validation pipeline: magic number verification, XXE protection (defusedxml), zip bomb detection, 10MB file size limit
- Dual-column storage (encrypted binary + extracted text) with FTS5 unicode61 full-text search
- Rich upload UI with table preview for Excel/CSV, sheet selector for multi-sheet workbooks
- Format-aware Document Viewer: PlutoGrid for Excel/CSV with virtualization, text viewers for PDF/Word
- AI document search with metadata, token budget limiting (3 chunks max), and format-specific source attribution chips
- Excel/CSV export endpoints with memory-efficient openpyxl write_only mode and UTF-8 BOM CSV encoding
- Frontend export UI with PopupMenuButton, FileSaver download, and loading/success/error feedback

**Stats:**

- 45 files modified, +6,973 / -193 lines
- 3 phases, 8 plans
- 24/24 requirements satisfied
- 1 day from start to ship (2026-02-12)

**Git range:** `7705f78` → `b5a3547`

**What's next:** v2.0 — Security Audit & Deployment

---

## v1.9.5 Pilot Logging Infrastructure (Shipped: 2026-02-08)

**Delivered:** Comprehensive logging infrastructure for AI-powered debugging during pilot testing — structured JSON logging with correlation IDs linking frontend and backend, admin API for log access, settings toggle for privacy control, and lifecycle-aware flush to centralized storage.

**Phases completed:** 43-48 (8 plans total)

**Key accomplishments:**

- Backend LoggingService with async-safe QueueHandler pattern, structlog JSON formatting, and 7-day rolling retention
- Admin API endpoints for log listing, download, and frontend log ingestion with role-based access control
- Frontend LoggingService with 1000-entry buffer, session ID grouping, and NavigatorObserver for route tracking
- ApiClient singleton with X-Correlation-ID header injection linking frontend requests to backend logs
- Settings toggle for logging enable/disable with SharedPreferences persistence and privacy-first buffer clearing
- Lifecycle-aware flush with 5-minute Timer.periodic, AppLifecycleListener (pause/detach), and pre-logout capture

**Stats:**

- 65 files modified, +9,525 / -288 lines
- ~88,000 LOC (75,852 Python + 12,220 Dart)
- 6 phases, 8 plans
- 29/29 requirements satisfied
- 2 days from start to ship (2026-02-07 → 2026-02-08)

**Git range:** `67c582d` → `01e5360`

**What's next:** v2.0 — Search, Previews & Integrations

---

## v1.9.4 Artifact Generation Deduplication (Shipped: 2026-02-05)

**Delivered:** 4-layer defense-in-depth fix for artifact multiplication bug (BUG-016) — prompt engineering deduplication rule, tool description single-call enforcement, structural history filtering via timestamp correlation, and silent artifact generation that bypasses chat history entirely.

**Phases completed:** 40-42 (5 plans total)

**Key accomplishments:**

- Added ARTIFACT DEDUPLICATION rule at priority 2 in SYSTEM_PROMPT with "ONLY act on MOST RECENT user message" and escape hatch for regenerate/revise
- Enforced single-call behavior in SAVE_ARTIFACT_TOOL description — "Call this tool ONCE per user request"
- Built _identify_fulfilled_pairs() with 5-second timestamp correlation to detect completed artifact requests
- Implemented structural history filtering in build_conversation_context() — fulfilled pairs removed before model sees them
- Created silent artifact generation backend mode — ChatRequest.artifact_generation flag gates conditional persistence and SSE suppression
- Built separate generateArtifact() frontend code path with GeneratingIndicator and GenerationErrorState UI widgets

**Stats:**

- 67 files modified, +8,725 / -1,188 lines
- ~86,400 LOC (74,766 Python + 11,652 Dart)
- 3 phases, 5 plans
- 35/35 requirements satisfied
- 1 day from start to ship (2026-02-05)

**Git range:** `7b6aca4` → `1451be1`

**What's next:** v2.0 — Search, Previews & Integrations

---

## v1.9.3 Document & Navigation Polish (Shipped: 2026-02-04)

**Delivered:** Document workflow improvements with download capability and upload preview confirmation, plus full breadcrumb navigation context for threads and documents with proper URL routing.

**Phases completed:** 37-39 (3 plans total)

**Key accomplishments:**

- Document download from Document Viewer AppBar and list context menu using file_saver pattern
- Document preview dialog before upload showing filename, size, and first 20 lines in monospace
- Extended breadcrumb navigation for threads (Projects > Project > Threads > Thread)
- Project-less thread breadcrumbs (Chats > Thread)
- Document Viewer URL routing via GoRouter (/projects/:id/documents/:docId) with browser back button support
- Full breadcrumb hierarchy for documents (Projects > Project > Documents > Document)

**Stats:**

- 24 files modified, +3,038 lines
- ~11,300 lines Dart frontend
- 3 phases, 3 plans
- 17/17 requirements satisfied
- 1 day from start to ship (2026-02-04)

**Git range:** `a867836` → `419980c`

**What's next:** v2.0 — Search, Previews & Integrations

---

## v1.9.2 Resilience & AI Transparency (Shipped: 2026-02-04)

**Delivered:** Error resilience with partial content preservation, budget transparency with threshold warnings, conversation mode persistence, artifact generation UI, and source attribution display.

**Phases completed:** 34-36 (9 plans total)

**Key accomplishments:**

- Network error resilience: partial AI responses preserved on drop with "Connection lost" banner and retry
- Client-side file validation: size checked before upload with clear error dialog and immediate retry
- Budget transparency: warning banners at 80%/95%/100% with input blocking when exhausted
- Conversation mode persistence: AppBar badge with tap-to-change dialog and database storage
- Artifact generation UI: type picker with 4 presets + custom, collapsible cards with MD/PDF/Word export
- Source attribution: collapsible chips showing documents used with navigation to Document Viewer

**Stats:**

- 24 files modified, +1,762 lines
- ~17,700 lines of code (10,985 Dart + 6,696 Python)
- 3 phases, 9 plans
- 24/24 requirements satisfied
- 2 days from start to ship (2026-02-03 → 2026-02-04)

**Git range:** `ce1b01d` → `0ea6e40`

**What's next:** v2.0 — Search, Previews & Integrations

---

## v1.9.1 Unit Test Coverage (Shipped: 2026-02-02)

**Delivered:** Comprehensive unit test coverage across backend services, LLM adapters, API routes, frontend providers, widgets, and models with CI-ready test suite and Codecov integration.

**Phases completed:** 28-33 (24 plans total)

**Key accomplishments:**

- Test infrastructure with MockLLMAdapter, Factory-boy factories, pytest-cov, and Flutter lcov
- Backend service tests (97 tests) covering auth, AI service, token tracking, document search
- Backend LLM adapter tests (53 tests) for Anthropic, Gemini, and DeepSeek with mocked HTTP
- Backend API contract tests (142 tests) for all routes with error consistency verification
- Frontend provider and service tests (429 tests) with Mockito mocks
- Frontend widget and model tests (198 tests) with conditional imports for dart:html
- GitHub Actions CI with coverage generation, Codecov upload, and README badge

**Stats:**

- 1,098 total tests (471 backend + 627 frontend)
- ~83,500 lines of code (74,431 Python + 9,132 Dart)
- 6 phases, 24 plans
- 43/43 requirements satisfied
- 1 day from start to ship (2026-02-02)

**Git range:** `feat(28-01)` → `docs(33-01)`

**What's next:** v2.0 — Search, Previews & Integrations

---

## v1.9 UX Improvements (Shipped: 2026-02-02)

**Delivered:** Standard chat UX patterns with Enter to send, threads-first project layout, project-less chats with global Chats menu, and search/sort for thread lists.

**Phases completed:** 23-27 (9 plans total)

**Key accomplishments:**

- Enter to send messages, Shift+Enter for newline (FocusNode.onKeyEvent keyboard handling)
- Threads-first project layout with collapsible documents column (48px collapsed, 280px expanded)
- Project-less chats with global Chats navigation section and dual ownership model
- One-way chat-to-project association via "Add to Project" button and confirmation flow
- Real-time search and sort in thread lists (Newest/Oldest/Alphabetical, case-insensitive)
- Three bug fixes during testing (GlobalThreadListResponse fields, last_activity_at, Shift+Enter web)

**Stats:**

- ~9,100 lines Dart, ~66,600 lines Python
- 5 phases, 9 plans
- 27/27 requirements satisfied
- 15 days from start to ship (2026-01-18 → 2026-02-02)

**Git range:** `feat(23-01)` → `docs(27)`

**What's next:** v2.0 — Search, Previews & Integrations

---

## v1.8 LLM Provider Switching (Shipped: 2026-01-31)

**Delivered:** Multi-provider support enabling users to select Claude, Gemini, or DeepSeek for conversations with per-conversation model binding.

**Phases completed:** 19-22 (8 plans total)

**Key accomplishments:**

- Provider-agnostic adapter pattern with StreamChunk normalization (backend treats all providers identically)
- AnthropicAdapter extracted from existing code, GeminiAdapter (google-genai), DeepSeekAdapter (OpenAI SDK)
- Thread database stores model_provider column with full API support
- SSE heartbeat mechanism prevents timeout during extended thinking (5+ min)
- Settings page provider dropdown with SharedPreferences persistence
- Model indicator below chat with provider-specific colors (Claude=orange, Gemini=blue, DeepSeek=green)

**Stats:**

- ~14,000 lines of Dart/Python
- 4 phases, 8 plans
- 13/13 requirements satisfied
- 1 day from start to ship (2026-01-31)

**Git range:** `feat(19-01)` → `feat(22-02)`

**What's next:** v1.9 — UX Improvements

---

## v1.7 URL & Deep Links (Shipped: 2026-01-31)

**Delivered:** Full deep linking support with URL preservation on refresh and OAuth redirect handling.

**Phases completed:** 15-18 (8 plans total)

**Key accomplishments:**

- Unique conversation URLs (`/projects/:projectId/threads/:threadId`)
- URL preserved on page refresh (authenticated users stay on same page)
- OAuth redirect stores return URL via sessionStorage
- Custom 404 error page with navigation options
- Graceful "not found" states for deleted projects/threads
- GoRouter configuration with optionURLReflectsImperativeAPIs

**Stats:**

- ~13,000 lines of Dart/Python
- 4 phases, 8 plans
- 5/5 requirements satisfied
- 1 day from start to ship (2026-01-31)

**Git range:** `feat(15-01)` → `feat(18-02)`

**What's next:** v1.8 — LLM Provider Switching ✅

---

## v1.6 UX Quick Wins (Shipped: 2026-01-30)

**Delivered:** Four friction-reduction features for the conversation workflow — copy responses, retry failures, auth provider display, and thread rename.

**Phases completed:** 11-14 (5 plans total)

**Key accomplishments:**

- One-tap copy for AI responses with synchronous clipboard integration (Safari compatible)
- Retry failed messages without retyping with smart duplicate prevention
- Auth provider indicator in Settings ("Signed in with Google/Microsoft")
- Thread rename via AppBar edit icon or popup menu with full-stack implementation

**Stats:**

- ~12,000 lines of Dart/Python
- 4 phases, 5 plans
- 14/14 requirements satisfied
- 1 day from start to ship (2026-01-30)

**Git range:** `feat(11-01)` → `feat(14-02)`

**What's next:** v1.7 — URL & Deep Links ✅

---

## v1.5 Beta - UI/UX Excellence (Shipped: 2026-01-30)

**Delivered:** Executive-demo-ready application with persistent navigation, professional empty states, deletion with undo, and visual polish.

**Phases completed:** 6-10 (15 plans total)

**Key accomplishments:**

- Theme management with instant persistence (no white flash on dark mode startup)
- Responsive navigation infrastructure (sidebar on desktop, drawer on mobile, breadcrumbs everywhere)
- Complete Settings page with OAuth profile display, token budget visualization, logout confirmation
- Deletion flows for all resources with 10-second undo window and optimistic UI
- Professional empty states across all list screens with clear CTAs
- Mode selector chips for AI conversation mode selection
- Consistent date formatting (relative <7 days, absolute >=7 days)

**Stats:**

- 11,778 lines of Dart/Python
- 5 phases, 15 plans
- 30/32 requirements satisfied (2 LOW priority deferred to v2.0)
- 2 days from start to ship (2026-01-29 → 2026-01-30)

**Git range:** `feat(06-01)` → `feat(10-05)`

**What's next:** v1.6 — UX Quick Wins ✅

---

## v1.0 MVP (Shipped: 2026-01-28)

**Delivered:** Fully functional AI-assisted business analyst tool with OAuth authentication, project/document management, streaming AI conversations with document search, and artifact export.

**Phases completed:** 1-5 + 4.1 (20 plans total)

**Key accomplishments:**

- Google and Microsoft OAuth 2.0 authentication with JWT session management
- Project, document, and thread CRUD with full-text search (FTS5)
- AI-powered discovery conversations with Claude API (SSE streaming, tool use for document search)
- Business analyst skill behaviors via 7,437-token XML system prompt
- Artifact generation (user stories, acceptance criteria, requirements docs) with Markdown/PDF/Word export
- Cross-platform Flutter app (web, Android, iOS) with responsive layouts
- Skeleton loaders and global error handling

**Stats:**

- ~9,500 lines of Dart/Python
- 6 phases, 20 plans
- 41/41 requirements delivered
- 11 days from start to ship (2026-01-17 → 2026-01-28)

**Git range:** `feat(01-01)` → `feat(05-05)`

**What's next:** Beta v1.5 - UI/UX Excellence ✅

---

*Last updated: 2026-02-12 (v2.1 complete)*
