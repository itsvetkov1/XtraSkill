# User Stories Index

**Project:** Business Analyst Assistant
**Last Updated:** 2026-02-25

---

## Status Legend

| Status | Description |
|--------|-------------|
| Open | Not started |
| In Progress | Currently being worked on |
| Done | Completed and verified |
| Wont Do | Rejected or out of scope |

---

## Summary

| Priority | Total | Open | Done | Wont Do |
|----------|-------|------|------|---------|
| Critical | 20 | 7 | 13 | 0 |
| High | 25 | 18 | 6 | 1 |
| Medium | 14 | 11 | 1 | 2 |
| Low | 4 | 3 | 1 | 0 |
| **Total** | **63** | **39** | **21** | **3** |

---

## Open Items Only

### Critical Priority (Open)

| ID | Title | Component | Notes |
|----|-------|-----------|-------|
| [BUG-016](BUG-016_artifact-generation-multiplies.md) | Artifact generation multiplies on repeated requests | Backend / AI Service | Parent issue — accumulates from conversation history |
| [BUG-017](BUG-017_prompt-deduplication-rule.md) | System prompt deduplication rule | Backend / AI Service | BUG-016 fix layer 1 — prompt engineering |
| [BUG-018](BUG-018_tool-description-single-call.md) | Tool description single-call enforcement | Backend / AI Service | BUG-016 fix layer 2 — tool description |
| [BUG-019](BUG-019_history-filtering-fulfilled-requests.md) | History filtering for fulfilled requests | Backend / Conversation Service | BUG-016 fix layer 3 — structural fix |
| [BUG-020](BUG-020_deepseek-cannot-read-documents.md) | DeepSeek Reasoner cannot read uploaded documents | Backend / AI Service / LLM Adapters | Documents invisible when provider lacks tool support |
| [SKILL-001](SKILL-001_bind-skill-to-thread.md) | Bind selected skill to thread at runtime | Backend / Thread Model / Skill System | Prerequisite for skill prompt injection |
| [SKILL-002](SKILL-002_inject-skill-prompt.md) | Inject skill system prompt into assistant threads | Backend / AI Service / Skill System | **Most critical gap** — skills are cosmetic without this |

### High Priority (Open)

| ID | Title | Component | Notes |
|----|-------|-----------|-------|
| [UX-004](UX-004_question-card-ui.md) | Question Card UI (Epic) | Frontend + Backend | AI questions as interactive cards |
| [UX-005](UX-005_question-card-backend.md) | Backend Structured Question Output | Backend | SSE event with question metadata |
| [UX-006](UX-006_question-card-rendering.md) | Frontend Question Card Rendering | Frontend | Card widget and styling |
| [UX-007](UX-007_question-card-interaction.md) | Question Card Interaction | Frontend | Tap, type, collapse behaviors |
| [THREAD-004](THREAD-004_network-interruption-streaming.md) | Handle network interruption | Streaming | Data loss prevention |
| [DELETE-001](DELETE-001_undo-behavior.md) | Consistent undo behavior | Deletion | UX consistency |
| [BUDGET-001](BUDGET-001_token-budget-ux.md) | Token budget exhaustion UX | Settings | Prevents cryptic errors |
| [THREAD-005](THREAD-005_mode-persistence.md) | Show conversation mode | Conversation | User clarity on AI behavior |
| [NAV-001](NAV-001_breadcrumb-thread-context.md) | Breadcrumb for threads | Navigation | Thread-level breadcrumbs |
| [DOC-001](DOC-001_document-preview-upload.md) | Document preview before upload | Documents | Error prevention |
| [THREAD-011](THREAD-011_silent-artifact-generation.md) | Silent artifact generation from buttons | Frontend + Backend | BUG-016 fix layer 4 — UX change |
| [BUG-021](BUG-021_pdf-export-500.md) | PDF export returns 500 error | Backend / Export Service | DOCX works, PDF fails + connection leak |
| [SKILL-003](SKILL-003_backend-skill-enforcement.md) | Backend enforcement of skill selection | Backend / Skills API / Chat Route | API contract for skill-to-runtime wiring |
| [BUG-024](BUG-024_dead-code-agent-service.md) | Dead code — AgentService not wired into production | Backend / Services | Maintenance burden, developer confusion |
| [ENH-012](ENH-012_assistant-direct-api.md) | Evaluate Direct API vs CLI for assistant threads | Backend / LLM Adapters | 120-400ms latency overhead for simple chats |
| [ENH-011](ENH-011_backend-request-logging.md) | Comprehensive backend request logging | Backend / Observability | Debugging visibility |

### Medium Priority (Open)

| ID | Title | Component | Notes |
|----|-------|-----------|-------|
| [THREAD-007](THREAD-007_artifact-generation-ui.md) | Artifact generation UI | Conversation | Feature discoverability |
| [THREAD-008](THREAD-008_document-sources.md) | Show AI document sources | Conversation | Transparency |
| [DOC-002](DOC-002_download-document.md) | Download document option | Documents | Convenience |
| [DOC-004](DOC-004_conversation-export.md) | Conversation export docs | Documentation | Feature clarity |
| [DOC-003](DOC-003_token-refresh-docs.md) | Token refresh docs | Documentation | Documentation |
| [DOC-005](DOC-005_file-size-error.md) | File size error UX | Documents | Error handling |
| [BUG-022](BUG-022_token-usage-model-mismatch.md) | Token usage records wrong model name | Backend / Token Tracking | Hardcoded AGENT_MODEL — affects all providers |
| [BUG-026](BUG-026_datetime-utcnow-deprecation.md) | datetime.utcnow() deprecation across codebase | Backend / Multiple Files | Python 3.12 deprecation warning |
| [BUG-028](BUG-028_artifact-correlation-timestamp-fragile.md) | Artifact correlation uses fragile timestamp window | Backend / Conversation Service | 5s window insufficient under load |
| [DOC-006](DOC-006_thread-scoped-document-search.md) | Thread-scoped document search for assistant threads | Backend / Document Search | Search misses thread-scoped docs |

### Low Priority (Open)

| ID | Title | Component | Notes |
|----|-------|-----------|-------|
| [RESPONSIVE-001](RESPONSIVE-001_tablet-breakpoint.md) | Tablet breakpoint review | Layout | Polish |
| [AUTH-001](AUTH-001_session-duration.md) | Session duration docs | Documentation | Documentation |
| [STATE-001](STATE-001_usage-provider.md) | UsageProvider docs | Documentation | Documentation |
| [BUG-025](BUG-025_summarization-print-not-logger.md) | Summarization uses print() instead of logger | Backend / Summarization Service | Errors invisible to logging |
| [BUG-027](BUG-027_process-pool-refill-no-backoff.md) | Process pool refill loop has no backoff | Backend / LLM Adapters / Claude CLI | Floods logs on spawn failure |

---

## Completed Items

### Critical (Done)

| ID | Title | Version |
|----|-------|---------|
| [BUG-001](BUG-001_page-refresh-loses-url.md) | Page refresh loses URL | v1.7 |
| [US-004](US-004_unique-conversation-urls.md) | Unique conversation URLs | v1.7 |
| [US-001](US-001_url-preservation-on-refresh.md) | URL preservation on refresh | v1.7 |
| [US-003](US-003_auth-redirect-with-return-url.md) | Auth redirect with return URL | v1.7 |
| [THREAD-001](THREAD-001_retry-failed-messages.md) | Retry failed AI messages | v1.6 |
| [THREAD-002](THREAD-002_copy-ai-responses.md) | Copy AI responses | v1.6 |
| [BUG-010](BUG-010_fts5-empty-query.md) | FTS5 empty query crash | v1.9 |
| [BUG-011](BUG-011_chats-missing-projectless.md) | Chats missing project-less threads | v1.9 |
| [BUG-012](BUG-012_chats-loading-state.md) | Chats stuck loading state | v1.9 |
| [BUG-013](BUG-013_global-threads-missing-created-at.md) | Global threads missing created_at | v1.9 |
| [BUG-014](BUG-014_project-threads-missing-last-activity.md) | Project threads missing last_activity | v1.9 |
| [BUG-015](BUG-015_shift-enter-newline.md) | Shift+Enter not creating new line | v1.9 |
| [BUG-023](BUG-023_cli-adapter-drops-conversation-history.md) | Claude CLI adapter drops conversation history | v3.1.1 |

### High (Done)

| ID | Title | Version |
|----|-------|---------|
| [THREAD-003](THREAD-003_rename-thread.md) | Rename thread after creation | v1.6 |
| [UX-001](UX-001_enter-to-send.md) | Enter key sends message | v1.9 |
| [UX-002](UX-002_threads-primary-documents-column.md) | Threads primary, documents column | v1.9 |
| [UX-003](UX-003_project-less-chats.md) | Project-less chats with global menu | v1.9 |
| [US-002](US-002_deep-link-support.md) | Deep link support | v1.7 |
| [THREAD-006](THREAD-006_search-filter-threads.md) | Search/filter threads | v1.9 |

### Medium (Done)

| ID | Title | Version |
|----|-------|---------|
| [SETTINGS-001](SETTINGS-001_auth-provider-display.md) | Show auth provider | v1.6 |

### Low (Done)

| ID | Title | Version |
|----|-------|---------|
| [THREAD-010](THREAD-010_chat-input-lines.md) | Increase chat input lines | v1.9 |

### Wont Do

| ID | Title | Reason |
|----|-------|--------|
| [HOME-001](HOME-001_button-differentiation.md) | Differentiate home buttons | Obsolete after UX-003 |
| [PROJECT-001](PROJECT-001_tab-persistence.md) | Tab state persistence | Obsolete after UX-002 |
| [THREAD-009](THREAD-009_message-count-definition.md) | Message count definition | Low value |

---

## Future Enhancements (Parking Lot)

Ideas beyond current scope. See [BACKLOG.md](BACKLOG.md) for details.

| ID | Enhancement |
|----|-------------|
| ENH-001 | Thread templates |
| ENH-002 | Pin important threads |
| ENH-003 | Thread archiving |
| ENH-004 | Conversation bookmarks |
| ENH-005 | AI response ratings |
| ENH-006 | Quick artifact actions |
| ENH-007 | Thread sharing |
| ENH-008 | Keyboard shortcuts |
| ENH-009 | Offline mode |
| ENH-010 | Accessibility audit |

---

## Story ID Prefixes

| Prefix | Component Area |
|--------|----------------|
| BUG- | Bug reports |
| US- | URL/Navigation user stories |
| UX- | User experience improvements |
| THREAD- | Conversation/Thread features |
| NAV- | Navigation/Breadcrumbs |
| DOC- | Documents or Documentation |
| DELETE- | Deletion behavior |
| BUDGET- | Token budget/Usage |
| HOME- | Home screen |
| SETTINGS- | Settings screen |
| PROJECT- | Project management |
| RESPONSIVE- | Responsive layout |
| AUTH- | Authentication |
| STATE- | State management |
| ENH- | Future enhancements |
| SKILL- | Skill system (assistant flow) |

---

*Last updated: 2026-02-25 — added 10 stories from assistant flow review, moved BUG-023 to Done, added SKILL- prefix*

## Infra (Infrastructure)

| ID | Title | Status |
|----|-------|--------|
| [INFRA-001](INFRA-001_docker-backend-setup.md) | Docker Backend Setup | Done |
| [INFRA-002](INFRA-002_openclaw-llm-provider.md) | OpenClaw as LLM Provider | Done |
| [INFRA-003](INFRA-003_openclaw-tools-integration.md) | OpenClaw Tools Integration | Done |

---

*Last updated: 2026-03-01 — added INFRA prefix for Docker and OpenClaw integration*

| [INFRA-004](INFRA-004_openclaw-tools-frontend.md) | OpenClaw Tools Frontend UI | Done |
