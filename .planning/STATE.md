# Project State

**Project:** Business Analyst Assistant
**Last Updated:** 2026-01-24

## Project Reference

**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

**Current Focus:** MVP v1.0 - Validate that AI-assisted discovery genuinely helps BAs capture better requirements faster than traditional methods

## Current Position

**Phase:** 04 of 04 (Artifact Generation & Export)
**Plan:** 02 of 02 in phase - Completed
**Status:** Phase 4 COMPLETE - All backend plans finished
**Progress:** ████████████ 100% (12/12 total plans)

## Performance Metrics

### Development Velocity
- **Capacity:** 20-30 hours/week (solo developer, part-time)
- **Timeline:** 8-10 weeks MVP development window
- **Plans Completed:** 12 (01-01: 44 min, 01-02: 34 min, 01-03: 2 hours, 02-01: 33 min, 02-02: 75 min, 02-03: 82 min, 02-04: 15 min, 03-01: 18 min, 03-02: 3 min, 03-03: 2 min, 04-01: 4 min, 04-02: 3 min)
- **Requirements Delivered:** 40/40 (database, API health check, app shell, OAuth Google/Microsoft, JWT auth, secure token storage, protected endpoints, logout, responsive UI, integration tests, cross-platform verification, projects, documents, threads, AI streaming, token tracking, thread summaries, conversation UI, streaming display, artifact model, save_artifact tool, artifact API, PDF export, Word export, Markdown export)

### Quality Indicators
- **Test Coverage:** Backend integration tests (14 tests passing), Flutter integration tests (2 tests passing)
- **Bug Count:** 5 bugs auto-fixed total (2 in 01-03: flutter_web_plugins, OAuth callback URLs)
- **Tech Debt:** Minimal (state storage in-memory dict - acceptable for MVP, move to Redis in production)

### Cost Tracking
- **AI Token Usage:** Now tracked via TokenUsage table (03-02)
- **Monthly Budget:** $50/user default enforced at API level
- **Hosting Costs:** Not yet incurred
- **Target Budget:** $50-100/month AI costs during MVP phase

## Accumulated Context

### Key Decisions Made
1. **OAuth-only authentication** (2026-01-17): No password management; enterprise-friendly for BA users with work accounts
2. **Flutter for frontend** (2026-01-17): Leverages existing experience; single codebase for web/Android/iOS
3. **Claude Agent SDK** (2026-01-17): Autonomous tool execution; accepts higher token cost for development speed
4. **SQLite for MVP** (2026-01-17): Zero-configuration simplicity; clear PostgreSQL migration path via SQLAlchemy
5. **Text-only documents** (2026-01-17): Defers PDF/Word parsing to validate document usefulness first
6. **No deletion in MVP** (2026-01-17): Maintains velocity by deferring cascade delete logic
7. **PaaS hosting** (2026-01-17): Railway/Render for operational simplicity (solo developer)
8. **SSE for streaming** (2026-01-17): Simpler than WebSockets, PaaS-friendly
9. **UUID primary keys** (2026-01-17 - Plan 01-01): PostgreSQL compatibility from day one, avoids migration pain
10. **TokenUsage model in Phase 1** (2026-01-17 - Plan 01-01): Critical for cost monitoring before AI integration
11. **Async SQLAlchemy throughout** (2026-01-17 - Plan 01-01): Non-blocking database operations for FastAPI performance
12. **Material 3 with light/dark mode** (2026-01-17 - Plan 01-01): Modern Flutter theming with built-in accessibility
13. **WidgetsBinding.addPostFrameCallback** (2026-01-17 - Plan 01-01): Prevents setState during build for async initialization
14. **JWT expiration: 7 days** (2026-01-17 - Plan 01-02): Balances security with UX for solo developer workflow; users re-authenticate weekly
15. **State storage: in-memory dict** (2026-01-17 - Plan 01-02): Sufficient for MVP single-instance; move to Redis before horizontal scaling
16. **Mobile deep link: com.baassistant** (2026-01-17 - Plan 01-02): Consistent URL scheme for iOS/Android OAuth callbacks
17. **flutter_secure_storage for tokens** (2026-01-17 - Plan 01-02): Platform-specific secure storage (Keychain/KeyStore), NOT SharedPreferences
18. **Responsive breakpoints: mobile < 600px, tablet 600-900px, desktop >= 900px** (2026-01-18 - Plan 01-03): Standard Material Design breakpoints
19. **Navigation patterns: Drawer (mobile/tablet) vs NavigationRail (desktop)** (2026-01-18 - Plan 01-03): Platform-appropriate navigation patterns
20. **SQLite PRAGMA foreign_keys** (2026-01-18 - Plan 02-01): Event listener on Engine connect ensures foreign keys enforced; critical for cascade deletes
21. **LargeBinary for encrypted content** (2026-01-18 - Plan 02-01): Fernet encryption returns bytes; avoid base64 encoding overhead
22. **back_populates over backref** (2026-01-18 - Plan 02-01): Explicit bidirectional relationships for better type hints; SQLAlchemy 2.0 best practice
23. **Pydantic request validation** (2026-01-18 - Plan 02-02): Field constraints (min_length, max_length) for name validation; prevents invalid data at API boundary
24. **Project ownership via 404** (2026-01-18 - Plan 02-02): Return 404 for "not found OR not owned" to avoid leaking project existence to unauthorized users
25. **Projects ordered by updated_at DESC** (2026-01-18 - Plan 02-02): Most recently modified projects appear first in list; matches user mental model
26. **ResponsiveMasterDetail pattern** (2026-01-18 - Plan 02-02): Reusable widget switches between split view (desktop) and navigation (mobile) at 600px breakpoint
27. **Provider manages list + selected** (2026-01-18 - Plan 02-02): Single ProjectProvider tracks both projects list and selectedProject to avoid redundant API calls

28. **Fernet encryption for documents** (2026-01-18 - Plan 02-03): Symmetric encryption with environment-based key management; documents encrypted at rest
29. **FTS5 for document search** (2026-01-18 - Plan 02-03): SQLite FTS5 virtual table with porter tokenizer for full-text search; BM25 ranking with snippets
30. **File upload validation** (2026-01-18 - Plan 02-03): Three-layer validation (content_type, size limit 1MB, UTF-8 encoding); prevents binary/oversized files
31. **file_picker for cross-platform uploads** (2026-01-18 - Plan 02-03): Flutter file_picker package with allowedExtensions filter for .txt and .md only
32. **Upload progress tracking** (2026-01-18 - Plan 02-03): Dio onSendProgress callback updates DocumentProvider state during multipart upload
33. **Optional thread titles** (2026-01-18 - Plan 02-04): Threads can have null titles; AI will generate summaries in Phase 3; UI shows "New Conversation" placeholder
34. **Thread ordering strategy** (2026-01-18 - Plan 02-04): List endpoint created_at DESC (newest first), detail messages created_at ASC (chronological reading)
35. **Message count via selectinload** (2026-01-18 - Plan 02-04): Load thread.messages relationship and count in Python; avoids N+1 queries
36. **Tab listener for thread refresh** (2026-01-18 - Plan 02-04): ProjectDetailScreen refreshes threads when switching to Threads tab for fresh data

37. **Claude claude-sonnet-4-5-20250514 model** (2026-01-22 - Plan 03-01): Balance of capability and cost for BA assistant conversations
38. **Token context budget: 150k with 80/20 split** (2026-01-22 - Plan 03-01): 80% for messages, 20% buffer for response and system prompt
39. **Token estimation: 1 token ~= 4 characters** (2026-01-22 - Plan 03-01): Simple heuristic for budget tracking without tokenizer dependency
40. **SSE event types standardized** (2026-01-22 - Plan 03-01): text_delta, tool_executing, message_complete, error for frontend handling
41. **Tool execution loop pattern** (2026-01-22 - Plan 03-01): Stream until tool_use stop_reason, execute tools, continue conversation

42. **Claude pricing: $3/1M input, $15/1M output** (2026-01-22 - Plan 03-02): Official Jan 2026 pricing for cost calculation
43. **Monthly budget: $50/user default** (2026-01-22 - Plan 03-02): Prevents cost explosion; check before each chat request
44. **Summary interval: every 5 messages** (2026-01-22 - Plan 03-02): Balances title freshness vs API cost
45. **Budget enforcement via 429** (2026-01-22 - Plan 03-02): HTTP 429 Too Many Requests when budget exceeded

46. **Thread navigation via Navigator.push** (2026-01-22 - Plan 03-03): Simple push navigation for modal conversation flow
47. **Optimistic message display** (2026-01-22 - Plan 03-03): User message shows immediately, AI message built via streaming
48. **SelectableText for message content** (2026-01-22 - Plan 03-03): Allow users to copy AI-generated content for requirements docs

49. **Artifact model markdown-first** (2026-01-24 - Plan 04-01): content_markdown primary, content_json reserved for future structured access
50. **No artifact POST endpoint** (2026-01-24 - Plan 04-01): Artifacts created only via Claude tool execution during chat
51. **artifact_created SSE event** (2026-01-24 - Plan 04-01): Frontend notified with id, type, title when artifact generated

52. **WeasyPrint for PDF export** (2026-01-24 - Plan 04-02): HTML-to-PDF with Jinja2 templates; requires GTK on Windows
53. **python-docx for Word export** (2026-01-24 - Plan 04-02): Native .docx generation with markdown parsing
54. **Graceful GTK error handling** (2026-01-24 - Plan 04-02): ImportError catch for PDF export provides helpful message on Windows
55. **StreamingResponse for exports** (2026-01-24 - Plan 04-02): BytesIO buffers with Content-Disposition headers for browser downloads

### Open Questions
- None yet

### Active Blockers
- ANTHROPIC_API_KEY required for AI features (user setup)

### Deferred Issues
- Search functionality (deferred to Beta)
- Deletion capabilities (deferred to Beta)
- PDF/Word parsing (deferred to Beta)
- Conversation editing (deferred to Beta)
- Token refresh mechanism (users re-authenticate after 7 days; acceptable for MVP)
- Production OAuth redirect URIs (requires deployed backend; configure after Railway/Render deployment)
- E2E OAuth tests with mocking (manual verification sufficient for MVP; automated E2E useful for CI/CD)

### Technical Debt
- State storage in-memory dict (acceptable for MVP; move to Redis for production multi-instance)
- Hardcoded OAuth redirect URIs in auth_service.py (localhost only; make configurable per environment)
- Responsive breakpoints hardcoded (could be configurable in future if needed)

## Session Continuity

### What Just Happened
- **Plan 04-02 EXECUTED:** Export Service (3 minutes)
  - Added python-docx, weasyprint, markdown, jinja2 to requirements.txt
  - Created HTML templates for PDF styling (base.html + artifact type templates)
  - Created export_service.py with export_markdown, export_pdf, export_docx functions
  - Added GET /artifacts/{id}/export/{format} endpoint with StreamingResponse
  - Graceful error handling for WeasyPrint GTK requirement on Windows
  - SUMMARY.md created documenting export service

### MVP Backend Complete
**All 12 backend plans finished - 100% progress**

Phase 1 (Foundation): Database, API shell, OAuth, JWT, responsive UI
Phase 2 (Data Management): Projects, documents, threads
Phase 3 (AI Conversation): Streaming, tokens, summaries, conversation UI
Phase 4 (Artifacts): Generation tool, SSE events, export service

### Next Action
**MVP Backend Ready for Frontend Integration**

Available APIs:
- Auth: POST /auth/login/google, /auth/login/microsoft, /auth/callback
- Projects: GET/POST /projects, GET/PATCH /projects/{id}
- Documents: GET/POST /projects/{id}/documents, GET /documents/{id}
- Threads: GET/POST /projects/{id}/threads, GET /threads/{id}
- Chat: POST /threads/{id}/chat (SSE streaming)
- Artifacts: GET /threads/{id}/artifacts, GET /artifacts/{id}, GET /artifacts/{id}/export/{format}

Export Formats:
- Markdown (.md): Plain text download
- PDF (.pdf): Styled document (requires GTK on Windows)
- Word (.docx): Microsoft Word document

### Context for Next Agent
**Phase 4 Complete - Full Export Service:**

New Components:
- `backend/requirements.txt` - python-docx, weasyprint, markdown, jinja2
- `backend/app/templates/artifacts/` - HTML templates for PDF styling
- `backend/app/services/export_service.py` - Export functions for all formats
- `backend/app/routes/artifacts.py` - Export endpoint added

Export API:
- `GET /api/artifacts/{id}/export/md` - Markdown download
- `GET /api/artifacts/{id}/export/pdf` - PDF download (GTK required)
- `GET /api/artifacts/{id}/export/docx` - Word download

Frontend Integration Needed:
- Artifact list view in thread detail
- Artifact detail view with markdown rendering
- Export buttons triggering file downloads
- Toast notifications for artifact_created SSE events

---

*Last updated: 2026-01-24 after completing Plan 04-02 (Export Service)*
