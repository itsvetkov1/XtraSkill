# Business Analyst Assistant

## What This Is

A hybrid mobile and web application that augments business analysts during feature discovery meetings. The system provides AI-powered conversational assistance to explore requirements, proactively identify edge cases, and generate structured business documentation (user stories, acceptance criteria, requirements documents) on demand. Users upload project context documents, conduct multiple conversation threads per project, and export professional artifacts in multiple formats.

## Core Value

Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## Current State

**Shipped:** v1.7 URL & Deep Links (2026-01-31)

The application now supports full deep linking and URL preservation:
- Unique conversation URLs (`/projects/:projectId/threads/:threadId`)
- URL preserved on page refresh (authenticated users stay on same page)
- OAuth redirect preserves intended destination via sessionStorage
- Custom 404 error page with navigation options
- Graceful "not found" states for deleted projects/threads

Previous features (v1.6):
- One-tap copy for AI responses with cross-platform clipboard support
- Retry failed AI requests without retyping messages
- Thread rename via AppBar edit icon or popup menu
- Auth provider indicator showing "Signed in with Google/Microsoft"

Previous features (v1.5):
- Persistent responsive sidebar navigation (desktop rail, mobile drawer)
- Theme management with instant persistence (no white flash)
- Settings page with profile, token usage, logout
- Deletion with 10-second undo for all resources
- Professional empty states across all list screens
- Mode selector chips for AI conversations
- Consistent date formatting and visual polish

**Codebase:** ~13,000 lines of Dart/Python across Flutter frontend and FastAPI backend.

## Current Milestone: v1.8 LLM Provider Switching

**Goal:** Enable cost optimization and model testing by allowing users to switch between AI providers.

**Target features:**
- Settings page LLM provider selector (Claude / Gemini / DeepSeek)
- Per-conversation model binding (conversations remember their model)
- Model indicator below chat window showing current provider
- Backend adapter pattern for multiple LLM APIs
- Support for Gemini 3 Flash Preview (`gemini-3-flash-preview`)
- Support for DeepSeek V3.2 thinking mode (`deepseek-reasoner`)

**Previous:** v1.7 URL & Deep Links (complete)

## Future Milestone Goals

**v2.0 — Search, Previews & Integrations** (planned)

- Global search across projects and threads
- Thread preview text in list view
- Thread mode indicator badges
- JIRA integration for artifact export
- Voice input for mobile meetings

## Requirements

### Validated

- ✓ User can authenticate with Google or Microsoft work account via OAuth 2.0 — MVP v1.0
- ✓ User can create and manage multiple projects with isolated contexts — MVP v1.0
- ✓ User can upload text documents to projects for AI context — MVP v1.0
- ✓ User can create multiple conversation threads per project — MVP v1.0
- ✓ AI provides real-time streaming guidance during feature discovery with proactive edge case identification — MVP v1.0
- ✓ AI autonomously searches project documents when conversation requires context — MVP v1.0
- ✓ User can request structured artifacts (user stories, acceptance criteria, requirements docs) from conversations — MVP v1.0
- ✓ User can export artifacts in Markdown, PDF, and Word formats — MVP v1.0
- ✓ Threads display AI-generated summaries for quick identification — MVP v1.0
- ✓ All data persists and syncs across devices (web, Android, iOS) — MVP v1.0
- ✓ Professional loading states with skeleton loaders — MVP v1.0
- ✓ Global error handling with user-friendly recovery — MVP v1.0
- ✓ Persistent sidebar navigation visible on all screens (responsive: desktop always-visible, mobile hamburger) — Beta v1.5
- ✓ Home screen features primary action buttons ("Start Conversation", "Browse Projects") — Beta v1.5
- ✓ Empty states provide clear guidance when projects/threads/documents lists are empty — Beta v1.5
- ✓ User can delete projects with confirmation dialog — Beta v1.5
- ✓ User can delete threads with confirmation dialog — Beta v1.5
- ✓ User can delete documents with confirmation dialog — Beta v1.5
- ✓ User can delete individual messages with confirmation dialog — Beta v1.5
- ✓ Settings page displays user profile information — Beta v1.5
- ✓ Settings page provides logout functionality — Beta v1.5
- ✓ Settings page includes light/dark theme toggle — Beta v1.5
- ✓ Settings page shows current token budget usage — Beta v1.5
- ✓ AI mode selection presents as clickable buttons instead of typed responses — Beta v1.5
- ✓ Date/time formatting is consistent (relative <7 days, absolute >7 days) — Beta v1.5
- ✓ Project headers are consolidated to reduce wasted vertical space — Beta v1.5
- ✓ Breadcrumb navigation or contextual back arrows show navigation context — Beta v1.5
- ✓ Message pills have improved readability (padding, font size) — Beta v1.5
- ✓ Project cards display metadata badges (thread count, document count) — Beta v1.5
- ✓ User can retry a failed AI request without retyping message — v1.6
- ✓ User can copy AI-generated content with one tap — v1.6
- ✓ User can rename conversation thread after creation — v1.6
- ✓ User can see which OAuth provider they're signed in with — v1.6
- ✓ Conversations have unique URLs (`/projects/:projectId/threads/:threadId`) — v1.7
- ✓ URL preserved on page refresh (authenticated user stays on same page) — v1.7
- ✓ Auth redirect stores return URL and completes to intended destination — v1.7
- ✓ Invalid routes handled gracefully (404 error states with navigation options) — v1.7
- ✓ Deleted project/thread URLs show "not found" state instead of crash — v1.7

### Active

- [ ] User can select default LLM provider in Settings (Claude, Gemini, DeepSeek)
- [ ] New conversations use the currently selected default provider
- [ ] Existing conversations continue with their original model regardless of default
- [ ] Model indicator displays below chat window showing current provider name
- [ ] Backend supports multiple LLM provider APIs via adapter pattern

### Deferred

- [ ] Thread list items show preview of last message (deferred from Beta v1.5 - requires backend API)
- [ ] Thread list items display mode indicator (deferred from Beta v1.5 - requires backend tracking)

### Out of Scope

- **Search functionality** — Deferred to v2.0; users browse manually (acceptable for <20 projects per user)
- **PDF/Word document parsing** — Accepts text-only uploads; users must copy-paste content from PDFs/Word docs (reduces complexity, validates document usefulness first)
- **Message editing** — Users can delete but not edit individual messages; editing introduces conversation coherence complexity
- **Multi-user collaboration** — Single-user per account; no project sharing or team workspaces until v2.0+
- **Notifications** — No push or email notifications; not needed for single-user workflow
- **Offline mode** — Requires network connection; offline capability deferred to v2.0+
- **Custom AI personalities** — Single consistent AI behavior; customization deferred unless strong user demand
- **Integration with Jira/Confluence** — External integrations deferred to v2.0+ based on enterprise adoption
- **Advanced thread features** — Thread archiving, starring, categorization deferred to v2.0
- **Bulk operations** — Multi-select delete, bulk export deferred to v2.0

## Context

**User Profile:**
Target users are business analysts working in product development, requirements gathering, and stakeholder management roles. They typically have Google Workspace or Microsoft 365 work accounts, conduct client meetings both in-office (desktop) and on-site (mobile), and need to capture rough feature ideas then convert them into structured documentation.

**Workflow Pattern:**
BAs prepare for meetings by uploading existing requirements or stakeholder notes to project context. During discovery conversations (meetings or solo work), they describe features and ask the AI to explore edge cases, clarify ambiguities, and identify gaps. After exploration, they request artifacts (user stories, acceptance criteria) and export them for stakeholder review or ticketing systems.

**Technical Environment:**
- Solo developer with 20-30 hours/week capacity (part-time development)
- Developer has Flutter experience (AI Rhythm Coach project) and QA background
- Comprehensive technical specification and roadmap documents
- Cost-conscious approach: monitoring AI API costs, SQLite for simplicity

**Market Validation Goals:**
- Prove AI-assisted discovery genuinely helps BAs capture better requirements faster
- Validate conversation-based interface is preferable to form-based requirement capture
- Test that generated artifacts are high enough quality to use directly
- Confirm cross-device access (desktop planning → mobile meetings) is essential workflow
- Learn which artifact types BAs request most frequently and usage patterns

## Constraints

- **Solo Developer Capacity**: 20-30 hours/week part-time development, must maintain velocity through simplicity choices
- **Technology Stack**: Flutter (web/Android/iOS), FastAPI (Python), SQLite, Multi-LLM APIs (Anthropic/Google/DeepSeek), OAuth 2.0, PaaS hosting (Railway/Render)
- **AI API Costs**: Monitor token usage closely; estimated $50-100/month, must not exceed budget without user validation
- **Cross-Platform**: Single codebase must support web, Android, and iOS simultaneously
- **PaaS Hosting**: Deployment limited to Railway/Render capabilities; no custom infrastructure or Kubernetes
- **Text-Only Documents**: Accepts plain text uploads only (no PDF/Word parsing) to reduce complexity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Flutter for frontend | Leverages existing experience from AI Rhythm Coach; single codebase for web/Android/iOS; zero learning curve maximizes velocity | ✓ Implemented |
| Direct Anthropic API (not Agent SDK) | Agent SDK requires Claude Code CLI runtime (not suitable for web backends); Direct API with XML system prompt achieves same behavioral goals with standard PaaS deployment; business-analyst skill transformed to 7,437-token system prompt | ✓ Implemented (Phase 04.1) |
| SQLite for MVP database | Zero-configuration simplicity, file-based deployment, built-in FTS5 for document search; clear migration path to PostgreSQL when scale demands (via SQLAlchemy ORM) | ✓ Implemented |
| OAuth-only authentication | No password management burden (reset flows, strength validation); enterprise-friendly for BA users with work accounts; delegates security to Google/Microsoft | ✓ Implemented |
| Text-only document upload | Defers PDF/Word parsing complexity to validate document usefulness first; users copy-paste content (acceptable friction for MVP) | ✓ Implemented |
| PaaS hosting (Railway/Render) | Git-based deployment, automatic HTTPS, managed infrastructure; operational simplicity critical for solo developer focusing on product | — Ready for deployment |
| SSE for AI streaming | Unidirectional server→client streaming perfect for AI responses; simpler than WebSockets, PaaS-friendly, automatic reconnection | ✓ Implemented |
| Immediate persistence pattern | Theme/sidebar state saved to SharedPreferences BEFORE notifyListeners() to survive crashes | ✓ Implemented (Phase 06) |
| Static load() factory pattern | Async provider initialization before MaterialApp prevents white flash on dark mode | ✓ Implemented (Phase 06) |
| Hard delete with CASCADE | Database handles child record cleanup; simplifies backend code | ✓ Implemented (Phase 09) |
| 10-second undo window | Timer-based deferred deletion with optimistic UI; industry-standard pattern | ✓ Implemented (Phase 09) |
| ActionChip for mode selection | Tap-action semantics (not toggle), immediate response initiation | ✓ Implemented (Phase 10) |
| Synchronous clipboard for Safari | Safari requires clipboard in sync user gesture handler; no async/await | ✓ Implemented (Phase 11) |
| PATCH for thread rename (not PUT) | Semantically correct for single-field updates | ✓ Implemented (Phase 14) |
| Return 404 for non-owner | Security: don't leak thread existence to non-owners | ✓ Implemented (Phase 14) |
| sessionStorage for returnUrl | Auto-clears on tab close; ephemeral by design for security | ✓ Implemented (Phase 16) |
| dart:html for sessionStorage | Simpler API than package:web; migrate to package:web when Wasm becomes default | ✓ Implemented (Phase 16) |
| GoRouter.optionURLReflectsImperativeAPIs | Enables browser back/forward to work correctly with imperative navigation | ✓ Implemented (Phase 17) |
| ResourceNotFoundState widget | Reusable widget for deleted project/thread states; consistent UX | ✓ Implemented (Phase 17) |

---
*Last updated: 2026-01-31 after v1.8 milestone start*
