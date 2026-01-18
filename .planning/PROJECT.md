# Business Analyst Assistant

## What This Is

A hybrid mobile and web application that augments business analysts during feature discovery meetings. The system provides AI-powered conversational assistance to explore requirements, proactively identify edge cases, and generate structured business documentation (user stories, acceptance criteria, requirements documents) on demand. Users upload project context documents, conduct multiple conversation threads per project, and export professional artifacts in multiple formats.

## Core Value

Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can authenticate with Google or Microsoft work account via OAuth 2.0
- [ ] User can create and manage multiple projects with isolated contexts
- [ ] User can upload text documents to projects for AI context
- [ ] User can create multiple conversation threads per project
- [ ] AI provides real-time streaming guidance during feature discovery with proactive edge case identification
- [ ] AI autonomously searches project documents when conversation requires context
- [ ] User can request structured artifacts (user stories, acceptance criteria, requirements docs) from conversations
- [ ] User can export artifacts in Markdown, PDF, and Word formats
- [ ] Threads display AI-generated summaries for quick identification
- [ ] All data persists and syncs across devices (web, Android, iOS)

### Out of Scope

- **Deletion capabilities** — Deferred to Beta phase to maintain MVP velocity; users cannot delete projects/threads/documents in MVP
- **Search functionality** — Deferred to Beta phase; users browse manually (acceptable for 1-5 projects per user in MVP)
- **PDF/Word document parsing** — MVP accepts text-only uploads; users must copy-paste content from PDFs/Word docs (reduces complexity, validates document usefulness first)
- **Conversation editing** — Users cannot edit or delete individual messages in MVP; threads are append-only
- **Multi-user collaboration** — Single-user per account; no project sharing or team workspaces until V1.0+
- **Notifications** — No push or email notifications; not needed for single-user MVP workflow
- **Offline mode** — Requires network connection; offline capability deferred to V1.0+
- **Custom AI personalities** — Single consistent AI behavior; customization deferred unless strong user demand
- **Integration with Jira/Confluence** — External integrations deferred to V1.0+ based on enterprise adoption

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
- **Technology Stack**: Flutter (web/Android/iOS), FastAPI (Python), SQLite, Claude Agent SDK, OAuth 2.0, PaaS hosting (Railway/Render)
- **AI API Costs**: Monitor token usage closely; estimated $50-100/month MVP phase, must not exceed budget without user validation
- **Cross-Platform**: Single codebase must support web, Android, and iOS simultaneously
- **PaaS Hosting**: Deployment limited to Railway/Render capabilities; no custom infrastructure or Kubernetes
- **Text-Only Documents**: MVP accepts plain text uploads only (no PDF/Word parsing) to reduce complexity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Flutter for frontend | Leverages existing experience from AI Rhythm Coach; single codebase for web/Android/iOS; zero learning curve maximizes velocity | — Pending |
| Claude Agent SDK (Approach 2) | Autonomous tool execution without manual loops; mirrors /business-analyst skill concept; accepts higher token cost for development speed and behavioral consistency | — Pending |
| SQLite for MVP database | Zero-configuration simplicity, file-based deployment, built-in FTS5 for document search; clear migration path to PostgreSQL when scale demands (via SQLAlchemy ORM) | — Pending |
| OAuth-only authentication | No password management burden (reset flows, strength validation); enterprise-friendly for BA users with work accounts; delegates security to Google/Microsoft | — Pending |
| Text-only document upload | Defers PDF/Word parsing complexity to validate document usefulness first; users copy-paste content (acceptable friction for MVP) | — Pending |
| No deletion in MVP | Maintains velocity by deferring cascade delete logic, confirmation flows, and edge cases; database grows but no data loss risk | — Pending |
| PaaS hosting (Railway/Render) | Git-based deployment, automatic HTTPS, managed infrastructure; operational simplicity critical for solo developer focusing on product | — Pending |
| SSE for AI streaming | Unidirectional server→client streaming perfect for AI responses; simpler than WebSockets, PaaS-friendly, automatic reconnection | — Pending |

---
*Last updated: 2026-01-17 after initialization from existing technical documentation*
