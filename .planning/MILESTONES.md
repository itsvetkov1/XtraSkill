# Project Milestones: Business Analyst Assistant

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

*Last updated: 2026-02-04 (v1.9.3 complete)*
