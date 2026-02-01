# Project Milestones: Business Analyst Assistant

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

*Last updated: 2026-02-01 (v1.8 complete)*
