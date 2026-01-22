# Project State

**Project:** Business Analyst Assistant
**Last Updated:** 2026-01-22

## Project Reference

**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

**Current Focus:** MVP v1.0 - Validate that AI-assisted discovery genuinely helps BAs capture better requirements faster than traditional methods

## Current Position

**Phase:** 03 of 04 (AI-Powered Conversations)
**Plan:** 01 of 03 in phase - Completed
**Status:** Phase 3 in progress - Backend AI service complete
**Progress:** ███████░░░ 70% (7/10 total plans estimated)

## Performance Metrics

### Development Velocity
- **Capacity:** 20-30 hours/week (solo developer, part-time)
- **Timeline:** 8-10 weeks MVP development window
- **Plans Completed:** 8 (01-01: 44 min, 01-02: 34 min, 01-03: 2 hours, 02-01: 33 min, 02-02: 75 min, 02-03: 82 min, 02-04: 15 min, 03-01: 18 min)
- **Requirements Delivered:** 28/40 (AI-01, AI-03 partially added) (database, API health check, app shell, OAuth Google/Microsoft, JWT auth, secure token storage, protected endpoints, logout, responsive UI, integration tests, cross-platform verification, projects, documents, threads, AI streaming)

### Quality Indicators
- **Test Coverage:** Backend integration tests (14 tests passing), Flutter integration tests (2 tests passing)
- **Bug Count:** 5 bugs auto-fixed total (2 in 01-03: flutter_web_plugins, OAuth callback URLs)
- **Tech Debt:** Minimal (state storage in-memory dict - acceptable for MVP, move to Redis in production)

### Cost Tracking
- **AI Token Usage:** Not yet measured (tracking infrastructure pending in 03-02)
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
- Token usage tracking to database (pending in 03-02)
- Thread title/summary generation (pending in 03-02)

### Technical Debt
- State storage in-memory dict (acceptable for MVP; move to Redis for production multi-instance)
- Hardcoded OAuth redirect URIs in auth_service.py (localhost only; make configurable per environment)
- Responsive breakpoints hardcoded (could be configurable in future if needed)

## Session Continuity

### What Just Happened
- **Plan 03-01 EXECUTED:** Backend AI Service with Claude Integration (18 minutes)
  - AIService class with AsyncAnthropic client and streaming
  - SYSTEM_PROMPT defining proactive BA assistant behavior
  - DOCUMENT_SEARCH_TOOL for autonomous document search
  - Conversation service with message persistence and token-aware truncation
  - SSE streaming chat endpoint POST /threads/{thread_id}/chat
  - Tool execution loop for multi-turn document search
  - SUMMARY.md created with all service components documented
  - **AI-01 (partial), AI-03 (partial):** Backend ready for AI conversations

### Next Action
**Phase 3 Plan 01 complete! Ready for Plan 03-02**

Phase 3 Status:
- Plan 01: Backend AI service - COMPLETE
- Plan 02: Frontend chat UI - PENDING
- Plan 03: Token tracking and artifacts - PENDING

**Ready for Plan 02 (Frontend Chat UI):**
- SSE endpoint streams text_delta events for real-time display
- message_complete event includes usage stats
- Thread ownership validation prevents unauthorized access
- Messages auto-saved to database

### Context for Next Agent
**Phase 3 Plan 01 Complete:**
- Backend API: POST /threads/{thread_id}/chat SSE endpoint
- AIService: AsyncAnthropic client with tool execution loop
- ConversationService: save_message, build_conversation_context, truncation
- SSE events: text_delta, tool_executing, message_complete, error
- Tool: search_documents available to Claude for project document search
- System prompt: Proactive BA assistant with edge case focus

**Key files created:**
- backend/app/services/ai_service.py - Claude integration
- backend/app/services/conversation_service.py - Message persistence
- backend/app/routes/conversations.py - SSE streaming endpoint

**Patterns established:**
- Tool execution loop: stream -> tool_use -> execute -> continue
- SSE event format: {event: string, data: JSON}
- validate_thread_access helper for ownership check
- Token budget management with truncation

---

*Last updated: 2026-01-22 after completing Plan 03-01 (Backend AI Service)*
