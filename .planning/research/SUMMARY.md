# Project Research Summary

**Project:** Business Analyst Assistant
**Domain:** AI-powered conversational platform with document context management
**Researched:** 2026-01-17
**Confidence:** MEDIUM-HIGH

## Executive Summary

The Business Analyst Assistant is an AI-powered conversational platform that helps business analysts discover requirements through guided dialogue, contextual document search, and automated artifact generation. Research validates that the proposed technology stack (Flutter, FastAPI, Claude Agent SDK, SQLite→PostgreSQL) aligns exceptionally well with 2025-2026 best practices for AI-heavy cross-platform applications, scoring 94/100 for stack alignment.

The recommended approach follows a **layered architecture** with clear separation between presentation (Flutter), business logic (FastAPI), AI orchestration (Claude Agent SDK), and data persistence. The critical architectural pattern is **agentic tool orchestration** where the AI autonomously decides when to search documents, generate artifacts, or respond conversationally. This approach maximizes development velocity for a solo developer while maintaining professional-grade scalability through MVP validation and beyond.

Key risks center on **AI token cost management** (Agent SDK multiplies API calls 3-5x per user request), **document context quality** (shallow RAG implementation destroys value proposition), and **cross-platform UI consistency** (Flutter's "write once" can mask platform-specific issues). All three risks are mitigable through early implementation of token budgets, semantic chunking with metadata enrichment, and platform-aware testing from day one. The MVP feature scope is well-balanced between table stakes (authentication, project management, conversation threading) and core differentiators (AI edge case discovery, contextual document search, structured artifact generation).

## Key Findings

### Recommended Stack

The proposed stack is production-ready and optimized for solo developer velocity. Flutter 3.38.6 (January 2026 release) explicitly highlights AI-powered app development as a cutting-edge focus, making it ideal for this use case. FastAPI with Anthropic Python SDK v0.76.0 provides native async support perfect for SSE streaming, and the SDK's built-in agent patterns eliminate months of manual tool loop development.

**Core technologies:**
- **Flutter 3.38.6** — Cross-platform UI (web/Android/iOS) from single codebase, leveraging existing experience from AI Rhythm Coach project
- **FastAPI 0.115+** — Async Python backend optimal for SSE streaming and AI integration
- **Anthropic Python SDK 0.76.0** — Native async support, streaming helpers, @beta_tool decorator for function-based tools, eliminates manual agent loop complexity
- **SQLite 3.45+ → PostgreSQL 18.1** — Zero-config MVP database with FTS5 full-text search, clear migration path via SQLAlchemy ORM abstraction
- **OAuth 2.0 (Google + Microsoft)** — Enterprise authentication standard, free tier, eliminates password management burden
- **Server-Sent Events (SSE)** — Unidirectional streaming for AI responses, simpler than WebSockets, PaaS-friendly
- **Railway/Render PaaS** — Git-based deployment, automatic HTTPS, zero-config infrastructure for $5-20/month

**Version verification:** Flutter, Anthropic SDK, and PostgreSQL versions verified against official sources (January 2026). Supporting library versions based on training data (late 2024/early 2025) with MEDIUM confidence—should be validated during implementation.

**Critical synergy:** Python ecosystem dominates AI tooling, FastAPI's async matches both Claude SDK and SSE streaming patterns, SQLAlchemy provides database-agnostic abstraction for SQLite→PostgreSQL migration.

### Expected Features

MVP feature set scores **well-scoped** — includes all critical table stakes and the core differentiators that define product value proposition. The deferrals (search, editing, deletion, PDF parsing) are appropriate for validation phase.

**Must have (table stakes):**
- **User authentication (OAuth)** — Security baseline, enterprise users expect SSO
- **Project organization** — BAs manage multiple initiatives simultaneously
- **Document storage** — Text-only MVP acceptable, BAs reference specs/notes during discovery
- **Conversation history** — Multiple threads per project for different features/initiatives
- **Export to common formats** — Markdown, PDF, Word—stakeholders need documentation deliverables
- **Cross-device sync** — Server-stored data provides automatic sync for office (desktop) and meetings (mobile)
- **Artifact templates** — AI generates structured user stories/acceptance criteria automatically

**Should have (competitive differentiators):**
- **AI-powered edge case discovery** — CORE VALUE PROP: proactively identifies missing requirements BAs overlook
- **Contextual document search** — AI autonomously references uploaded documents during conversation (most AI tools require manual context)
- **Structured artifact generation** — Convert conversations to user stories, acceptance criteria automatically
- **Guided discovery questions** — AI asks clarifying questions like experienced BA mentor
- **Conversation threading** — Separate conversations for different features within project (organizational advantage vs single-thread chat)
- **Real-time streaming responses** — SSE shows AI response as it generates, reduces perceived latency
- **Multi-format export** — Word/PDF/Markdown without manual formatting

**Defer (Beta/V1.0+):**
- **Voice input for meetings** — HIGH VALUE for meeting use case, consider for Beta if mobile adoption strong
- **JIRA/Azure DevOps integration** — Critical for V1.0 enterprise adoption
- **Requirement completeness scoring** — Reinforces AI value proposition, good Beta candidate
- **PDF/Word document parsing** — Text-only sufficient for MVP validation
- **Search functionality** — Acceptable with <10 projects, becomes critical in Beta
- **Editing/deletion capabilities** — Minimal UX issue for MVP, must address for Beta

**Anti-features (deliberately avoid):**
- Built-in diagramming tools (BAs use Miro/Lucidchart, competing adds massive scope)
- Real-time collaboration in MVP/Beta (requires WebSockets, CRDTs, massive complexity)
- Gantt charts/project planning (not BA's primary responsibility, dilutes focus)
- Built-in approval workflows (low ROI for MVP validation)
- Customizable AI personalities (complexity without proven user demand)

### Architecture Approach

The recommended architecture follows a **layered separation of concerns** with stateless API design enabling horizontal scaling and natural cross-device synchronization. The critical innovation is using Claude Agent SDK as the orchestration layer—the SDK handles tool invocation timing, multi-turn conversation management, streaming assembly, and error recovery, eliminating weeks of manual implementation.

**Major components:**
1. **Flutter Client** — UI rendering, user input, state management (Provider), SSE consumption via Dio + sse_client
2. **FastAPI Server** — Request routing, authentication (JWT validation), business logic (project/thread/document CRUD), response streaming (EventSourceResponse)
3. **AI Service** — Agent session management, tool orchestration, streaming coordination via Claude Agent SDK
4. **Claude Agent SDK** — Tool execution loop, AI reasoning, response generation, communicates with Anthropic API and custom tools
5. **Custom Tools** — DocumentSearch (FTS5 query), ArtifactGenerator (structured formatting), ThreadSummarizer (UI summaries)
6. **SQLite Database** — Data persistence, full-text search (FTS5), encrypted storage (Fernet), clear PostgreSQL migration path

**Key patterns to follow:**
- **Agentic tool orchestration** — AI decides when to use tools based on context, not explicit user commands or keyword matching
- **Streaming-first response design** — Yield chunks from Agent SDK immediately via SSE, update Flutter UI progressively for better UX
- **Conversation context management** — Limit to last 20 messages + project metadata to avoid token explosion while maintaining coherent responses
- **Stateless API with centralized state** — Backend doesn't hold session state in memory (all state in database), enables horizontal scaling and cross-device sync
- **Layered separation** — Presentation (Flutter) → Business Logic (FastAPI) → Orchestration (Agent SDK) → Data (SQLite + Claude API), each layer single responsibility

**Critical dependency chain:** Database → Auth → Projects → Documents → AI Service → Streaming → Artifacts. This ordering is non-negotiable—each phase depends on the previous being functional.

### Critical Pitfalls

Research identified 13 pitfalls across critical/moderate/minor severity. The top 5 require prevention from Phase 1:

1. **Uncontrolled AI token costs** — Agent SDK multiplies API calls 3-5x per user request; without budgets, costs spiral to $500-2000/month before revenue. **Prevention:** Implement token budgets BEFORE launch (8K per request, 50K per conversation, 200K per user per day), monitor from day one, use prompt caching (70% discount), smart context windowing (last 5 messages + summary, not all 50 messages). Phase 1 must include analytics table logging tokens per request.

2. **Shallow document context (useless RAG problem)** — Document search ships but doesn't help users; AI references documents superficially without deep understanding. **Prevention:** Semantic chunking (split on document structure, not character limits), metadata enrichment (document type, section headers, date), relevance filtering (top 3-5 chunks with confidence scores, not 20), hybrid search (semantic + keyword matching). Phase 2 must implement semantic chunking before document search ships.

3. **Cross-platform UI/UX inconsistency** — Flutter app behaves differently on web vs mobile; desktop users expect keyboard shortcuts, mobile users expect gestures. **Prevention:** Responsive design from day one, platform-aware widgets (Platform.isAndroid/isIOS/isWeb), adaptive navigation (drawer on mobile, sidebar on web), test matrix (Chrome web + Android emulator + iOS simulator per PR). Phase 1 establishes responsive patterns, all subsequent phases test on all platforms.

4. **Conversation state explosion (lost context)** — As conversations grow (50+ messages), AI forgets earlier context, contradicts previous statements, repeats questions. **Prevention:** Conversation summarization (every 10 messages create rolling summary), explicit state tracking (artifacts created, stakeholders identified, decisions made), context prioritization (recent 5 messages + summary + relevant artifacts, not all 50 messages), state hydration in system prompt. Phase 2 adds summarization before long conversations become common.

5. **Authentication/security debt** — MVP ships with basic auth; adding OAuth, encryption, or compliance features later requires database migrations and breaking changes. **Prevention:** OAuth from day one (Google/Microsoft SSO for BA users), encryption at rest (Fernet for documents), row-level security (user_id foreign keys), audit logging for compliance. Phase 1 must include production-ready auth—cannot defer.

**Moderate pitfalls** (address by Beta): Generic AI responses (not BA-specific), no offline capability for mobile meetings, poor artifact export formatting for enterprise tools, SQLite scalability limits ignored (no migration plan).

**Minor pitfalls** (fixable post-launch): No loading states, missing search across conversations, no keyboard shortcuts for desktop power users.

## Implications for Roadmap

Based on research, the roadmap should follow a **7-phase structure** aligned with critical dependency chain and risk mitigation priorities. Total MVP timeline: 8-10 weeks for solo developer.

### Phase 1: Foundation & Authentication (Weeks 1-3)
**Rationale:** Database and auth are blockers for all user-specific features. OAuth must be production-ready from day one to avoid security debt. Token tracking analytics must exist before AI service ships to prevent cost explosion.

**Delivers:**
- SQLite database with Postgres-compatible schema + SQLAlchemy ORM + Alembic migrations
- FastAPI server with health check + CORS + basic routing
- OAuth 2.0 integration (Google + Microsoft) with JWT generation/validation
- Flutter app shell with navigation + OAuth flow + secure token storage
- Analytics table for token usage tracking

**Addresses:** Table stakes authentication, avoids authentication/security debt pitfall (PITFALL #5)

**Avoids:** Designing SQLite-specific schema that breaks PostgreSQL migration (PITFALL #10)

**Research flag:** Standard patterns (OAuth, FastAPI setup), skip /gsd:research-phase

---

### Phase 2: Project & Document Management (Weeks 3-4)
**Rationale:** AI needs projects and documents to search. Document upload with encryption and FTS5 indexing must be functional before AI service can use DocumentSearch tool.

**Delivers:**
- Project CRUD endpoints + ownership validation
- Thread CRUD endpoints + multiple threads per project
- Document upload + Fernet encryption + FTS5 indexing
- Flutter project/thread/document UI

**Addresses:** Table stakes (project organization, document storage)

**Avoids:** Plaintext document storage security risk (PITFALL #5)

**Research flag:** Standard CRUD patterns, skip /gsd:research-phase

---

### Phase 3: AI Service Core (Weeks 4-6)
**Rationale:** Core value proposition. Agent SDK integration with custom tools is the highest complexity phase—allow extra time. Must implement semantic chunking and token budgets BEFORE shipping to avoid shallow RAG (PITFALL #2) and cost explosion (PITFALL #1).

**Delivers:**
- Claude Agent SDK integration with AsyncAnthropic client
- Custom tools: DocumentSearch (FTS5 + semantic chunking), ArtifactGenerator (structured formatting)
- Message persistence + conversation history assembly (last 20 messages)
- Token budget implementation (8K/request, 50K/conversation, 200K/user/day)
- Prompt caching setup (system prompt caching for 70% cost reduction)
- BA-specific system prompt with few-shot examples

**Addresses:** Core differentiators (AI edge case discovery, contextual document search, guided questions)

**Avoids:** Uncontrolled token costs (PITFALL #1), shallow document context (PITFALL #2), generic AI responses (PITFALL #7)

**Research flag:** HIGH—Agent SDK tool integration is new technology, consider /gsd:research-phase for tool implementation patterns

---

### Phase 4: Streaming Interface (Weeks 6-7)
**Rationale:** Users expect real-time AI responses. SSE streaming is critical for UX—without it, feels slow/broken. Must handle connection failures to avoid half-written message problems.

**Delivers:**
- SSE endpoint in FastAPI (EventSourceResponse)
- Flutter SSE client integration (sse_client package)
- Real-time UI updates (progressive text rendering)
- Tool call indicators ("Searching documents...")
- Connection error handling + heartbeat + completion markers
- Graceful degradation (fallback on stream failure)

**Addresses:** Differentiator (real-time streaming responses), table stakes (conversation history)

**Avoids:** Streaming response failures (PITFALL #6)

**Research flag:** MEDIUM—SSE on Flutter may need debugging, consider /gsd:research-phase if issues arise

---

### Phase 5: Artifacts & Export (Weeks 7-8)
**Rationale:** Key differentiator for BAs—structured artifact generation saves hours of documentation time. Export formats critical for stakeholder delivery.

**Delivers:**
- Artifact storage (database model + foreign key to message)
- ArtifactGenerator tool integration
- Export endpoints: Markdown (trivial), PDF (WeasyPrint), Word (python-docx)
- Flutter artifact display + export UI
- ThreadSummarizer tool for conversation summaries

**Addresses:** Core differentiators (structured artifact generation, multi-format export)

**Avoids:** Poor artifact export formatting (PITFALL #9)

**Research flag:** LOW—Export libraries well-documented, skip /gsd:research-phase unless PDF layout issues emerge

---

### Phase 6: Cross-Platform Polish (Weeks 8-9)
**Rationale:** Must test on all platforms before MVP launch to catch platform-specific issues. Responsive design prevents web/mobile inconsistency.

**Delivers:**
- Responsive design refinements (drawer on mobile, sidebar on web)
- Platform-specific adaptations (Cupertino widgets on iOS, Material on Android)
- Loading states + skeleton loaders + progress indicators
- Error handling + user feedback + Sentry integration
- Cross-device testing (Chrome web + Android + iOS)
- Performance optimization (async queries, lazy loading)

**Addresses:** Table stakes (cross-device sync), UX quality

**Avoids:** Cross-platform UI/UX inconsistency (PITFALL #3)

**Research flag:** Standard Flutter patterns, skip /gsd:research-phase

---

### Phase 7: MVP Validation & Launch (Week 10)
**Rationale:** Final testing, deployment, and user validation before Beta features.

**Delivers:**
- PaaS deployment (Railway $5/month starter tier)
- Environment variables + secrets management
- OAuth app credentials configured (Google/Microsoft consoles)
- End-to-end testing on all platforms
- Documentation (setup instructions, user guide basics)
- Monitoring dashboard (token usage, error rates, user activity)

**Addresses:** Operational readiness

**Avoids:** No new feature development, focus on validation

**Research flag:** PaaS deployment well-documented, skip /gsd:research-phase

---

### Phase Ordering Rationale

**Dependency-driven:** Database → Auth → Projects → Documents → AI Service → Streaming → Artifacts is the only viable order. Each phase is blocked by previous phases completing.

**Risk-driven:** Token budgets and analytics in Phase 1 (before AI ships), semantic chunking in Phase 3 (before document search ships), cross-platform testing in Phase 6 (before launch) prevent critical pitfalls.

**Value-driven:** AI Service (Phase 3) is the longest/hardest phase but delivers core value proposition. Artifacts (Phase 5) complete the value loop (conversation → AI insights → deliverable documents).

### Research Flags

**Phases likely needing deeper research during planning:**

- **Phase 3 (AI Service Core):** Agent SDK tool integration is new technology with limited production examples. Consider /gsd:research-phase for:
  - Custom tool implementation patterns
  - Prompt caching setup for cost optimization
  - Semantic chunking strategies for BA documents
  - Token budget enforcement patterns

- **Phase 4 (Streaming Interface):** Flutter SSE client may have platform-specific quirks. Consider /gsd:research-phase if:
  - SSE connection stability issues on mobile
  - EventSource API behaves differently on web vs mobile
  - Connection failure/retry patterns unclear

**Phases with standard patterns (skip research-phase):**

- **Phase 1 (Foundation & Auth):** OAuth 2.0, FastAPI setup, SQLAlchemy ORM—all well-documented standard patterns
- **Phase 2 (Project & Document Management):** Standard CRUD operations, file upload, database encryption
- **Phase 5 (Artifacts & Export):** python-docx, WeasyPrint, ReportLab—mature libraries with extensive documentation
- **Phase 6 (Cross-Platform Polish):** Flutter responsive design and Material 3 patterns are established
- **Phase 7 (MVP Launch):** Railway/Render deployment well-documented

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Flutter 3.38.6, Anthropic SDK 0.76.0, PostgreSQL 18.1 verified via official sources (Jan 2026). Supporting libraries based on training data (late 2024/early 2025). |
| Features | MEDIUM-HIGH | Table stakes and differentiators identified based on BA tool patterns and AI assistant landscape. Anti-features validated against solo developer constraints. Not verified with current 2026 market research. |
| Architecture | HIGH | Layered architecture, Agent SDK orchestration, SSE streaming—all verified against official documentation and technical specification alignment. Build order validated against dependency graph. |
| Pitfalls | MEDIUM-HIGH | Critical pitfalls (token costs, RAG quality, cross-platform) based on established AI assistant patterns. BA-specific pitfalls inferred from domain knowledge but not verified with current case studies. |

**Overall confidence:** MEDIUM-HIGH

Research is production-ready for roadmap creation. Stack recommendations are verified and current. Architecture patterns align with technical specification. Feature scope is well-balanced. Pitfall prevention strategies are actionable.

### Gaps to Address

**AI token cost monitoring:** Research recommends specific budgets (8K/request, 50K/conversation) but actual costs depend on prompt complexity and Agent SDK behavior. **Mitigation:** Implement monitoring in Phase 1, adjust budgets during Phase 3 based on actual usage patterns.

**Agent SDK tool examples:** Official documentation provides patterns but limited production examples for complex multi-tool scenarios. **Mitigation:** Plan extra time in Phase 3 for tool integration experimentation, consider /gsd:research-phase if complexity exceeds expectations.

**Semantic chunking strategies:** Research identifies semantic chunking as critical but doesn't specify algorithm (sentence-based? paragraph-based? document structure-based?). **Mitigation:** Research during Phase 3 planning, evaluate libraries (LangChain splitters, semantic-text-splitter) with BA document samples.

**Flutter SSE performance:** sse_client package confidence is MEDIUM—limited information on production stability across platforms. **Mitigation:** Prototype SSE streaming early in Phase 4, have fallback plan (polling or complete response) if streaming proves unstable.

**PostgreSQL migration trigger:** Research recommends "migrate at 1000 users" but doesn't define precise metrics (write latency? concurrent connections? database size?). **Mitigation:** Define specific metrics during Phase 1 implementation (e.g., "migrate when p95 write latency > 100ms OR concurrent users > 500").

**BA-specific prompt quality:** Generic system prompt may not produce professional BA artifacts without domain-tuned examples. **Mitigation:** User (developer) has BA experience—leverage domain knowledge during Phase 3 prompt engineering, iterate with real BA document samples.

## Sources

### Primary (HIGH confidence)
- **STACK.md** — Technology stack recommendations with version verification (Flutter 3.38.6, Anthropic SDK 0.76.0, PostgreSQL 18.1 verified via official sources Jan 2026)
- **ARCHITECTURE.md** — Layered architecture patterns, Agent SDK integration, SSE streaming, verified against official Claude SDK and Flutter documentation
- **Claude Agent SDK documentation** — Tool orchestration patterns, streaming setup, async patterns
- **Flutter official documentation** — Cross-platform patterns, SSE client libraries, Material 3 responsive design

### Secondary (MEDIUM confidence)
- **FEATURES.md** — Feature landscape analysis based on training knowledge of BA tools (JIRA, Confluence, Azure DevOps, Notion, Miro), AI assistants (ChatGPT, Claude, specialized tools), not verified with current 2026 market data
- **PITFALLS.md** — Domain pitfalls based on training knowledge of AI assistant patterns, conversational platform development, Flutter cross-platform development, not verified with recent case studies
- **User-provided context** — Implementation Roadmap, Technical Specification, Technology Stack documents (HIGH confidence for project-specific decisions)

### Tertiary (LOW confidence)
- Library versions for supporting tools (SQLAlchemy 2.0+, Provider 6.1+, python-jose 3.3+) based on training data late 2024/early 2025, should be validated via PyPI/pub.dev during implementation

---
*Research completed: 2026-01-17*
*Ready for roadmap: yes*
