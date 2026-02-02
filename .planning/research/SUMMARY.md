# Research Summary: BA Assistant v1.9.2

**Milestone:** v1.9.2 - Resilience & AI Transparency
**Synthesized:** 2026-02-02
**Research Files:** STACK_v1.9.2.md, FEATURES-v1.9.2.md, ARCHITECTURE_v1.9.2.md, PITFALLS-v1.9.2.md

---

## Executive Summary

BA Assistant v1.9.2 focuses on six features spanning error resilience, transparency indicators, and UX improvements. The research reveals that **all features can be implemented using the existing architecture** with only two new frontend packages (`connectivity_plus` for network detection, `eventflux` to replace `flutter_client_sse` for auto-reconnect SSE). The backend requires no new dependencies.

The most critical findings center on **SSE streaming resilience** and **source attribution accuracy**. Current implementation discards partial responses on network errors (losing user-visible content), and source attribution for RAG responses is a known hallucination vector requiring careful implementation. Industry patterns strongly recommend preserving partial content, implementing exponential backoff retry, and verifying citations before display.

The recommended approach is a **three-phase structure** organized by architectural dependencies: (1) Client-side resilience features requiring no backend changes, (2) Transparency indicators surfacing existing data, (3) AI interaction enhancements requiring new SSE events and database schema changes. This ordering minimizes deployment coordination and delivers user-visible improvements early.

---

## Key Findings

### From STACK_v1.9.2.md

**Core Stack Decisions:**

| Feature | Technology | Rationale |
|---------|------------|-----------|
| Network detection | connectivity_plus ^7.0.0 | Cross-platform network state; distinguish "no network" from "server error" |
| SSE with auto-reconnect | eventflux ^2.2.1 | Replaces flutter_client_sse; built-in exponential backoff, POST support |
| Budget progress bar | LinearProgressIndicator (built-in) | Dynamic color thresholds, no new dependency needed |
| Mode indicator | Material Chip (built-in) | Matches existing ProviderIndicator pattern |
| Artifact type picker | DropdownButton (built-in) | Simple enum selection, overkill to use dropdown_button2 |
| File validation | file_picker (existing) | PlatformFile.size already available |

**Migration Required:** Replace `flutter_client_sse` with `eventflux` in AIService - moderate effort, same event structure.

**Packages Explicitly NOT Recommended:**
- `internet_connection_checker_plus` - connectivity_plus sufficient
- `percent_indicator` - built-in LinearProgressIndicator sufficient
- `dropdown_button2` - built-in DropdownButton sufficient
- `flutter_http_sse` - less mature than eventflux

---

### From FEATURES-v1.9.2.md

**Critical Gaps to Address:**

| Gap | Feature Area | Impact |
|-----|--------------|--------|
| Source attribution display | RAG Citations | HIGH - Core value proposition of document-aware AI |
| Budget exhaustion blocked state | Token/Budget | HIGH - Users blocked without understanding why |
| Preserve partial response on error | Streaming | MEDIUM - Loses valuable content on network drop |
| Client-side file validation | Upload | MEDIUM - Error after user already committed |
| Persistent mode indicator | Conversation | MEDIUM - Context lost after mode selection |

**Table Stakes (Must Have for v1.9.2):**
- Visual error state with retry capability (exists, needs enhancement)
- Budget progress with threshold color changes (exists in Settings, needs conversation exposure)
- Mode indicator visible throughout conversation (GAP)
- Source attribution for document-informed responses (GAP)
- Client-side file size validation before upload (GAP)

**Industry-Standard UX Copy:**
- Warning (80%): "You're approaching your monthly limit (80% used)"
- Warning (95%): "Almost at your monthly limit. Consider shorter responses."
- Blocked (100%): "Monthly budget exhausted. Budget resets on [date]."

**Anti-Features to Avoid:**
- Silent failure on network drop
- Auto-retry without user feedback
- Discarding partial responses
- Aggressive reconnect loops
- Fabricated source citations

---

### From ARCHITECTURE_v1.9.2.md

**Component Changes Summary:**

**New Files to Create (Frontend):**
- `lib/models/artifact.dart` - Artifact model
- `lib/models/validation_result.dart` - File validation result
- `lib/services/artifact_service.dart` - Artifact API calls
- `lib/providers/budget_provider.dart` - Budget status tracking (or extend AuthProvider)
- `lib/widgets/budget_warning_banner.dart` - Budget warning UI
- `lib/widgets/mode_indicator.dart` - Conversation mode display
- `lib/widgets/artifact_card.dart` - Artifact display card
- `lib/widgets/artifact_preview_dialog.dart` - Full artifact view
- `lib/widgets/source_attribution.dart` - Document sources list
- `lib/widgets/file_validation_card.dart` - Upload validation UI

**Files to Modify (Frontend):**
- `ai_service.dart` - Add ConnectionStateEvent, retry logic, DocumentSourcesEvent
- `conversation_provider.dart` - Connection state, artifact tracking, sources
- `thread.dart` - Add conversationMode property
- `message.dart` - Add sources property
- `token_usage.dart` - Add threshold helpers

**Backend Changes:**
- `models.py` - Add conversation_mode to Thread
- `auth.py` - Add /budget-status lightweight endpoint
- `ai_service.py` - Add document_sources SSE event
- `conversation_service.py` - Detect mode on first message
- `token_tracking.py` - Add get_budget_status()

**Cross-Feature Dependencies:**
```
Independent (No dependencies):
  - Network Resilience (frontend only)
  - File Validation (frontend only)
  - Token Budget Tracking (minor backend)
  - Artifact Generation UI (backend already complete)

Dependent on backend changes:
  - Mode Indicator (requires Thread model migration)
  - Source Attribution (requires new SSE event)
```

---

### From PITFALLS-v1.9.2.md

**Critical Pitfalls (Must Prevent):**

| ID | Pitfall | Feature | Prevention |
|----|---------|---------|------------|
| PITFALL-01 | Network drop discards partial content | THREAD-004 | Do NOT clear _streamingText on error; create error-with-partial state |
| PITFALL-02 | Flutter Web SSE buffering | THREAD-004 | Use platform-specific implementations; test on web |
| PITFALL-03 | Server continues after client disconnect | THREAD-004 | Check request.is_disconnected() in stream generator |
| PITFALL-04 | Token counting fails during streaming | BUDGET-001 | Use API-provided usage from message_complete event |
| PITFALL-05 | RAG source attribution hallucination | THREAD-008 | Track chunk-to-document mapping; verify citations exist |

**Moderate Pitfalls (Avoid):**

| ID | Pitfall | Feature | Prevention |
|----|---------|---------|------------|
| PITFALL-06 | Budget warning race condition | BUDGET-001 | Estimate response tokens; pessimistic warnings |
| PITFALL-07 | Mode persistence scope confusion | THREAD-005 | Mode is thread property, not global preference |
| PITFALL-08 | Artifact UI overloads message list | THREAD-007 | Collapsed cards with expand; lazy render |
| PITFALL-09 | File validation after upload starts | DOC-005 | Validate immediately after picker returns |
| PITFALL-10 | Reconnect loop without backoff | THREAD-004 | Exponential backoff: 1s, 2s, 4s, 8s, max 30s |

---

## Implications for Roadmap

Based on architectural analysis and pitfall mapping, the recommended phase structure is:

### Phase 1: Client-Side Resilience
**Features:** THREAD-004 (Network Interruption), DOC-005 (File Size Validation)
**Rationale:** Both are frontend-focused, deliver immediate UX improvements, no deployment coordination needed with backend. Foundation for later features.

**Key Deliverables:**
- Replace flutter_client_sse with eventflux
- Add connectivity_plus for network state
- Implement exponential backoff retry (1s, 2s, 4s, 8s max)
- Preserve partial streaming content on error
- Client-side file size/type validation before upload

**Pitfalls to Prevent:**
- PITFALL-01: Preserve partial content
- PITFALL-02: Test web streaming behavior
- PITFALL-09: Validate before upload
- PITFALL-10: Exponential backoff with max retries

**Needs Phase Research:** NO - Patterns well-documented (eventflux, connectivity_plus)

---

### Phase 2: Transparency Indicators
**Features:** BUDGET-001 (Token Budget Exhaustion), THREAD-005 (Conversation Mode Indicator)
**Rationale:** Both surface existing data with better UI. Mode indicator requires simple migration, budget tracking extends existing token_usage infrastructure.

**Key Deliverables:**
- Budget warning banner at 80%, 90%, 100% thresholds
- Clear "budget exhausted" blocked state with reset date
- Lightweight /budget-status backend endpoint
- Mode indicator badge in conversation header
- Thread model migration for conversation_mode column

**Pitfalls to Prevent:**
- PITFALL-04: Use API-provided token counts
- PITFALL-06: Pessimistic budget warnings
- PITFALL-07: Mode as thread property, not global
- PITFALL-11: 48x48 minimum touch target for badge

**Needs Phase Research:** NO - Extends existing patterns

---

### Phase 3: AI Interaction Enhancement
**Features:** THREAD-007 (Artifact Generation UI), THREAD-008 (Document Source Attribution)
**Rationale:** Both enhance core AI chat experience. Source attribution requires new SSE event (document_sources). Artifact UI is frontend-only but benefits from source attribution context.

**Key Deliverables:**
- Artifact notification on creation during chat
- Collapsible artifact cards with preview
- Artifact view/export actions (copy, download as .md/.txt)
- document_sources SSE event from backend
- Source attribution widget below assistant messages
- Expandable sources list with document links

**Pitfalls to Prevent:**
- PITFALL-05: Verify citations match actual documents
- PITFALL-08: Collapsed cards, lazy render
- PITFALL-12: Meaningful export filenames
- PITFALL-13: Wrap chips, limit visible sources

**Needs Phase Research:** YES - Source attribution accuracy testing recommended

---

## Research Flags

| Phase | Research Needed | Reason |
|-------|-----------------|--------|
| Phase 1 | NO | eventflux and connectivity_plus well-documented; patterns clear |
| Phase 2 | NO | Extends existing token_usage and provider_indicator patterns |
| Phase 3 | YES | Source attribution accuracy is critical; need test suite of query-document pairs |

**Specific Research for Phase 3:**
- Build 20-30 test queries with known correct source documents
- Verify citation accuracy rate (target: 95%+)
- Test hallucination scenarios (generic queries, no relevant docs)

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified package docs, existing codebase patterns, migration path clear |
| Features | HIGH | Industry patterns well-documented, gaps clearly identified |
| Architecture | HIGH | Direct codebase analysis, component boundaries defined |
| Pitfalls | HIGH | Community-verified issues, specific prevention strategies |

**Overall Confidence:** HIGH

**Gaps Identified:**
1. Flutter Web SSE behavior - needs verification during Phase 1
2. Source attribution accuracy - needs test suite during Phase 3
3. eventflux web support marked "experimental" - fallback plan to retain flutter_client_sse

---

## Sources (Aggregated)

### Official Documentation
- [connectivity_plus pub.dev](https://pub.dev/packages/connectivity_plus) - v7.0.0
- [eventflux pub.dev](https://pub.dev/packages/eventflux) - v2.2.1, POST support verified
- [Flutter LinearProgressIndicator](https://api.flutter.dev/flutter/material/LinearProgressIndicator-class.html)
- [file_picker pub.dev](https://pub.dev/packages/file_picker)
- [sse-starlette Package](https://pypi.org/project/sse-starlette/)

### Industry Patterns
- [Ably Blog - AI UX: Reliable, Resumable Token Streaming](https://ably.com/blog/token-streaming-for-ai-ux)
- [Skywork - Best Practices for AI API Cost Management](https://skywork.ai/blog/ai-api-cost-throughput-pricing-token-math-budgets-2025/)
- [PatternFly - Conversation Design](https://www.patternfly.org/patternfly-ai/conversation-design/)
- [Anthropic - Claude Artifacts](https://support.claude.com/en/articles/11649427-use-artifacts-to-visualize-and-create-ai-apps-without-ever-writing-a-line-of-code)
- [Shape of AI - Citations Pattern](https://www.shapeof.ai/patterns/citations)
- [Uploadcare - File Uploader UX Best Practices](https://uploadcare.com/blog/file-uploader-ux-best-practices/)

### Pitfall Sources
- [FastAPI Client Disconnection Discussion](https://github.com/fastapi/fastapi/discussions/7572)
- [How to Fix RAG Citations](https://particula.tech/blog/fix-rag-citations)
- [23 RAG Pitfalls](https://www.nb-data.com/p/23-rag-pitfalls-and-how-to-fix-them)
- [LLM Token Counting Guide](https://winder.ai/calculating-token-counts-llm-context-windows-practical-guide/)

### Existing Codebase
- `frontend/lib/services/ai_service.dart` - Current SSE implementation
- `frontend/lib/providers/conversation_provider.dart` - State management pattern
- `frontend/lib/screens/conversation/widgets/provider_indicator.dart` - Indicator pattern
- `backend/app/services/token_tracking.py` - Budget tracking exists
- `backend/app/services/ai_service.py` - Heartbeat implemented
- `backend/app/models.py` - Database models

---

*Research synthesis complete. Ready for roadmap creation.*
