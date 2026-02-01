# User Stories Index

**Project:** Business Analyst Assistant
**Last Updated:** 2026-01-31

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

| Priority | Total | Open | In Progress | Done | Wont Do |
|----------|-------|------|-------------|------|---------|
| Critical | 9 | 3 | 4 | 2 | 0 |
| High | 13 | 12 | 0 | 1 | 0 |
| Medium | 9 | 7 | 0 | 0 | 2 |
| Low | 4 | 4 | 0 | 0 | 0 |
| **Total** | **35** | **30** | **0** | **3** | **2** |

---

## Priority Ranking (Recommended Order)

Work items ranked by impact, dependencies, and user value.

| Rank | ID | Title | Priority | Rationale |
|------|-----|-------|----------|-----------|
| 1 | [BUG-001](BUG-001_page-refresh-loses-url.md) | Page refresh loses URL | Critical | Blocks basic navigation; root cause of URL issues |
| 2 | [US-004](US-004_unique-conversation-urls.md) | Unique conversation URLs | Critical | **Prerequisite** for US-001, US-002, NAV-001 |
| 3 | [US-001](US-001_url-preservation-on-refresh.md) | URL preservation on refresh | Critical | Core navigation fix; depends on US-004 |
| 4 | [US-003](US-003_auth-redirect-with-return-url.md) | Auth redirect with return URL | Critical | Login UX; prevents user frustration |
| 5 | [THREAD-001](THREAD-001_retry-failed-messages.md) | Retry failed AI messages | Critical | ~~Error recovery; prevents lost work~~ **DONE** |
| 6 | [THREAD-002](THREAD-002_copy-ai-responses.md) | Copy AI responses | Critical | ~~Core workflow; daily pain point~~ **DONE** |
| 7 | [THREAD-003](THREAD-003_rename-thread.md) | Rename thread after creation | High | ~~Usability; many "Untitled" threads~~ **DONE** |
| 8 | [UX-001](UX-001_enter-to-send.md) | Enter key sends message | High | Standard chat UX; daily friction point |
| 9 | [UX-002](UX-002_threads-primary-documents-column.md) | Threads primary, documents column | High | Layout improvement; conversations are primary workflow |
| 10 | [UX-003](UX-003_project-less-chats.md) | Project-less chats with global menu | High | Reduces friction; enables quick conversations |
| 11 | [THREAD-004](THREAD-004_network-interruption-streaming.md) | Handle network interruption | High | Data loss prevention |
| 12 | [US-002](US-002_deep-link-support.md) | Deep link support | High | Sharing/bookmarking; depends on US-004 |
| 13 | [DELETE-001](DELETE-001_undo-behavior.md) | Consistent undo behavior | High | UX consistency across resources |
| 14 | [BUDGET-001](BUDGET-001_token-budget-ux.md) | Token budget exhaustion UX | High | Prevents cryptic errors at limit |
| 15 | [THREAD-005](THREAD-005_mode-persistence.md) | Show conversation mode | High | User clarity on AI behavior |
| 16 | [NAV-001](NAV-001_breadcrumb-thread-context.md) | Breadcrumb for threads | High | Navigation; depends on US-004 |
| 17 | [DOC-001](DOC-001_document-preview-upload.md) | Document preview before upload | High | Error prevention |
| 18 | [THREAD-006](THREAD-006_search-filter-threads.md) | Search/filter threads | High | Scalability for large projects |
| 19 | [THREAD-007](THREAD-007_artifact-generation-ui.md) | Artifact generation UI | High | Feature discoverability |
| 20 | [THREAD-008](THREAD-008_document-sources.md) | Show AI document sources | Medium | Transparency; trust building |
| ~21~ | ~~[HOME-001](HOME-001_button-differentiation.md)~~ | ~~Differentiate home buttons~~ | ~~Medium~~ | **Wont Do** - Obsolete after UX-003 |
| 22 | [SETTINGS-001](SETTINGS-001_auth-provider-display.md) | Show auth provider | Medium | Minor UX improvement |
| 23 | [DOC-002](DOC-002_download-document.md) | Download document option | Medium | Convenience feature |
| ~24~ | ~~[PROJECT-001](PROJECT-001_tab-persistence.md)~~ | ~~Tab state persistence~~ | ~~Medium~~ | **Wont Do** - Obsolete after UX-002 |
| 25 | [DOC-004](DOC-004_conversation-export.md) | Conversation export docs | Medium | Feature clarity |
| 26 | [DOC-003](DOC-003_token-refresh-docs.md) | Token refresh docs | Medium | Documentation |
| 27 | [DOC-005](DOC-005_file-size-error.md) | File size error UX | Medium | Error handling |
| 28 | [THREAD-009](THREAD-009_message-count-definition.md) | Message count definition | Medium | Documentation |
| 29 | [THREAD-010](THREAD-010_chat-input-lines.md) | Increase chat input lines | Low | Minor UX |
| 30 | [RESPONSIVE-001](RESPONSIVE-001_tablet-breakpoint.md) | Tablet breakpoint review | Low | Layout polish |
| 31 | [AUTH-001](AUTH-001_session-duration.md) | Session duration docs | Low | Documentation |
| 32 | [STATE-001](STATE-001_usage-provider.md) | UsageProvider docs | Low | Documentation |

---

## Critical Priority (Rank 1-9)

Blocking issues and core workflow problems. Address first.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 1 | [BUG-001](BUG-001_page-refresh-loses-url.md) | Page refresh loses URL | **v1.7** | Router |
| 2 | [US-004](US-004_unique-conversation-urls.md) | Unique conversation URLs | **v1.7** | Router |
| 3 | [US-001](US-001_url-preservation-on-refresh.md) | URL preservation on refresh | **v1.7** | Router |
| 4 | [US-003](US-003_auth-redirect-with-return-url.md) | Auth redirect with return URL | **v1.7** | Auth |
| 5 | [THREAD-001](THREAD-001_retry-failed-messages.md) | Retry failed AI messages | **Done** | Conversation |
| 6 | [THREAD-002](THREAD-002_copy-ai-responses.md) | Copy AI responses | **Done** | Message Bubble |
| 7 | [BUG-010](BUG-010_fts5-empty-query.md) | FTS5 empty query crash | **Open** | Document Search |
| 8 | [BUG-011](BUG-011_chats-missing-projectless.md) | Chats missing project-less threads | **Open** | ChatsScreen |
| 9 | [BUG-012](BUG-012_chats-loading-state.md) | Chats stuck loading state | **Open** | ChatsScreen |

---

## High Priority (Rank 7-19)

High-value features and UX improvements.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 7 | [THREAD-003](THREAD-003_rename-thread.md) | Rename thread after creation | **Done** | Thread List |
| 8 | [UX-001](UX-001_enter-to-send.md) | Enter key sends message | Open | Chat Input |
| 9 | [UX-002](UX-002_threads-primary-documents-column.md) | Threads primary, documents column | Open | Project Layout |
| 10 | [UX-003](UX-003_project-less-chats.md) | Project-less chats with global menu | Open | Navigation |
| 11 | [THREAD-004](THREAD-004_network-interruption-streaming.md) | Handle network interruption | Open | Streaming |
| 12 | [US-002](US-002_deep-link-support.md) | Deep link support | Open | Router |
| 13 | [DELETE-001](DELETE-001_undo-behavior.md) | Consistent undo behavior | Open | Deletion |
| 14 | [BUDGET-001](BUDGET-001_token-budget-ux.md) | Token budget exhaustion UX | Open | Settings |
| 15 | [THREAD-005](THREAD-005_mode-persistence.md) | Show conversation mode | Open | Conversation |
| 16 | [NAV-001](NAV-001_breadcrumb-thread-context.md) | Breadcrumb for threads | Open | Navigation |
| 17 | [DOC-001](DOC-001_document-preview-upload.md) | Document preview before upload | Open | Documents |
| 18 | [THREAD-006](THREAD-006_search-filter-threads.md) | Search/filter threads | Open | Thread List |
| 19 | [THREAD-007](THREAD-007_artifact-generation-ui.md) | Artifact generation UI | Open | Conversation |

---

## Medium Priority (Rank 20-28)

Polish and documentation improvements.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 20 | [THREAD-008](THREAD-008_document-sources.md) | Show AI document sources | Open | Conversation |
| ~21~ | ~~[HOME-001](HOME-001_button-differentiation.md)~~ | ~~Differentiate home buttons~~ | **Wont Do** | ~~Home~~ |
| 22 | [SETTINGS-001](SETTINGS-001_auth-provider-display.md) | Show auth provider | Open | Settings |
| 23 | [DOC-002](DOC-002_download-document.md) | Download document option | Open | Documents |
| ~24~ | ~~[PROJECT-001](PROJECT-001_tab-persistence.md)~~ | ~~Tab state persistence~~ | **Wont Do** | ~~Projects~~ |
| 25 | [DOC-004](DOC-004_conversation-export.md) | Conversation export docs | Open | Documentation |
| 26 | [DOC-003](DOC-003_token-refresh-docs.md) | Token refresh docs | Open | Documentation |
| 27 | [DOC-005](DOC-005_file-size-error.md) | File size error UX | Open | Documents |
| 28 | [THREAD-009](THREAD-009_message-count-definition.md) | Message count definition | Open | Thread List |

---

## Low Priority (Rank 29-32)

Minor improvements and polish.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 29 | [THREAD-010](THREAD-010_chat-input-lines.md) | Increase chat input lines | Open | Conversation |
| 30 | [RESPONSIVE-001](RESPONSIVE-001_tablet-breakpoint.md) | Tablet breakpoint review | Open | Layout |
| 31 | [AUTH-001](AUTH-001_session-duration.md) | Session duration docs | Open | Documentation |
| 32 | [STATE-001](STATE-001_usage-provider.md) | UsageProvider docs | Open | Documentation |

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

---

*Generated from backlog analysis*
