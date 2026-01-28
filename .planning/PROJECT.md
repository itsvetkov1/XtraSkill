# Business Analyst Assistant

## What This Is

A hybrid mobile and web application that augments business analysts during feature discovery meetings. The system provides AI-powered conversational assistance to explore requirements, proactively identify edge cases, and generate structured business documentation (user stories, acceptance criteria, requirements documents) on demand. Users upload project context documents, conduct multiple conversation threads per project, and export professional artifacts in multiple formats.

## Core Value

Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## Current Milestone: Beta v1.5 - UI/UX Excellence

**Goal:** Transform the application into a polished, intuitive experience ready for executive demos and wider user testing through comprehensive navigation improvements, professional empty states, and essential user management features.

**Target features:**
- Persistent responsive sidebar navigation across all screens
- Professional empty states with clear guidance for new users
- Deletion capabilities with confirmation dialogs for projects, threads, and documents
- Enhanced Home screen with primary CTAs (remove development phase information)
- Settings page with profile, logout, theme toggle, and token budget display
- Clickable mode selection buttons in AI conversations
- Improved visual consistency (date formatting, header layouts, message readability)
- Breadcrumb navigation and contextual back arrows
- Thread preview indicators and project metadata badges

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

### Active

- [ ] Persistent sidebar navigation visible on all screens (responsive: desktop always-visible, mobile hamburger)
- [ ] Home screen features primary action buttons ("Start Conversation", "Browse Projects")
- [ ] Empty states provide clear guidance when projects/threads/documents lists are empty
- [ ] User can delete projects with confirmation dialog
- [ ] User can delete threads with confirmation dialog
- [ ] User can delete documents with confirmation dialog
- [ ] User can delete individual messages with confirmation dialog
- [ ] Settings page displays user profile information
- [ ] Settings page provides logout functionality
- [ ] Settings page includes light/dark theme toggle
- [ ] Settings page shows current token budget usage
- [ ] AI mode selection presents as clickable buttons instead of typed responses
- [ ] Date/time formatting is consistent (relative <7 days, absolute >7 days)
- [ ] Project headers are consolidated to reduce wasted vertical space
- [ ] Breadcrumb navigation or contextual back arrows show navigation context
- [ ] Message pills have improved readability (padding, font size)
- [ ] Thread list items show preview of last message
- [ ] Project cards display metadata badges (thread count, document count)

### Out of Scope

- **Search functionality** — Deferred to Beta v2.0 phase; users browse manually (acceptable for <20 projects per user)
- **PDF/Word document parsing** — Accepts text-only uploads; users must copy-paste content from PDFs/Word docs (reduces complexity, validates document usefulness first)
- **Message editing** — Users can delete but not edit individual messages; editing introduces conversation coherence complexity
- **Multi-user collaboration** — Single-user per account; no project sharing or team workspaces until V2.0+
- **Notifications** — No push or email notifications; not needed for single-user workflow
- **Offline mode** — Requires network connection; offline capability deferred to V2.0+
- **Custom AI personalities** — Single consistent AI behavior; customization deferred unless strong user demand
- **Integration with Jira/Confluence** — External integrations deferred to V2.0+ based on enterprise adoption
- **Advanced thread features** — Thread archiving, starring, categorization deferred to V2.0
- **Bulk operations** — Multi-select delete, bulk export deferred to V2.0

## Context

**User Profile:**
Target users are business analysts working in product development, requirements gathering, and stakeholder management roles. They typically have Google Workspace or Microsoft 365 work accounts, conduct client meetings both in-office (desktop) and on-site (mobile), and need to capture rough feature ideas then convert them into structured documentation.

**Workflow Pattern:**
BAs prepare for meetings by uploading existing requirements or stakeholder notes to project context. During discovery conversations (meetings or solo work), they describe features and ask the AI to explore edge cases, clarify ambiguities, and identify gaps. After exploration, they request artifacts (user stories, acceptance criteria) and export them for stakeholder review or ticketing systems.

**Technical Environment:**
- Solo developer with 20-30 hours/week capacity (part-time development)
- Developer has Flutter experience (AI Rhythm Coach project) and QA background
- Existing comprehensive technical specification and roadmap documents
- Cost-conscious approach: monitoring AI API costs, starting with SQLite for simplicity

**Market Validation Goals:**
- Prove AI-assisted discovery genuinely helps BAs capture better requirements faster
- Validate conversation-based interface is preferable to form-based requirement capture
- Test that generated artifacts are high enough quality to use directly
- Confirm cross-device access (desktop planning → mobile meetings) is essential workflow
- Learn which artifact types BAs request most frequently and usage patterns

## Constraints

- **Solo Developer Capacity**: 20-30 hours/week part-time development, must maintain velocity through simplicity choices
- **Timeline**: 8-10 weeks MVP development window; features must fit this constraint or be descoped
- **Technology Stack**: Flutter (web/Android/iOS), FastAPI (Python), SQLite, Anthropic Messages API (direct), OAuth 2.0, PaaS hosting (Railway/Render)
- **AI API Costs**: Monitor token usage closely; estimated $50-100/month MVP phase, must not exceed budget without user validation
- **Cross-Platform**: Single codebase must support web, Android, and iOS simultaneously
- **PaaS Hosting**: Deployment limited to Railway/Render capabilities; no custom infrastructure or Kubernetes
- **Text-Only Documents**: MVP accepts plain text uploads only (no PDF/Word parsing) to reduce complexity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Flutter for frontend | Leverages existing experience from AI Rhythm Coach; single codebase for web/Android/iOS; zero learning curve maximizes velocity | ✓ Implemented |
| Direct Anthropic API (not Agent SDK) | Agent SDK requires Claude Code CLI runtime (not suitable for web backends); Direct API with XML system prompt achieves same behavioral goals with standard PaaS deployment; business-analyst skill transformed to 7,437-token system prompt | ✓ Implemented (Phase 04.1) |
| SQLite for MVP database | Zero-configuration simplicity, file-based deployment, built-in FTS5 for document search; clear migration path to PostgreSQL when scale demands (via SQLAlchemy ORM) | ✓ Implemented |
| OAuth-only authentication | No password management burden (reset flows, strength validation); enterprise-friendly for BA users with work accounts; delegates security to Google/Microsoft | ✓ Implemented |
| Text-only document upload | Defers PDF/Word parsing complexity to validate document usefulness first; users copy-paste content (acceptable friction for MVP) | ✓ Implemented |
| No deletion in MVP | Maintains velocity by deferring cascade delete logic, confirmation flows, and edge cases; database grows but no data loss risk | ✓ Implemented |
| PaaS hosting (Railway/Render) | Git-based deployment, automatic HTTPS, managed infrastructure; operational simplicity critical for solo developer focusing on product | — Ready for deployment |
| SSE for AI streaming | Unidirectional server→client streaming perfect for AI responses; simpler than WebSockets, PaaS-friendly, automatic reconnection | ✓ Implemented |

---
*Last updated: 2026-01-29 after MVP v1.0 completion - starting Beta v1.5 (UI/UX Excellence)*
