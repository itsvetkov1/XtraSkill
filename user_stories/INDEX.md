# User Stories Index

**Project:** Business Analyst Assistant
**Last Updated:** 2026-01-30

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

| Priority | Total | Open | In Progress | Done |
|----------|-------|------|-------------|------|
| Critical | 6 | 4 | 0 | 2 |
| High | 10 | 9 | 0 | 1 |
| Medium | 9 | 9 | 0 | 0 |
| Low | 4 | 4 | 0 | 0 |
| **Total** | **29** | **26** | **0** | **3** |

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
| 8 | [THREAD-004](THREAD-004_network-interruption-streaming.md) | Handle network interruption | High | Data loss prevention |
| 9 | [US-002](US-002_deep-link-support.md) | Deep link support | High | Sharing/bookmarking; depends on US-004 |
| 10 | [DELETE-001](DELETE-001_undo-behavior.md) | Consistent undo behavior | High | UX consistency across resources |
| 11 | [BUDGET-001](BUDGET-001_token-budget-ux.md) | Token budget exhaustion UX | High | Prevents cryptic errors at limit |
| 12 | [THREAD-005](THREAD-005_mode-persistence.md) | Show conversation mode | High | User clarity on AI behavior |
| 13 | [NAV-001](NAV-001_breadcrumb-thread-context.md) | Breadcrumb for threads | High | Navigation; depends on US-004 |
| 14 | [DOC-001](DOC-001_document-preview-upload.md) | Document preview before upload | High | Error prevention |
| 15 | [THREAD-006](THREAD-006_search-filter-threads.md) | Search/filter threads | High | Scalability for large projects |
| 16 | [THREAD-007](THREAD-007_artifact-generation-ui.md) | Artifact generation UI | High | Feature discoverability |
| 17 | [THREAD-008](THREAD-008_document-sources.md) | Show AI document sources | Medium | Transparency; trust building |
| 18 | [HOME-001](HOME-001_button-differentiation.md) | Differentiate home buttons | Medium | Reduces confusion |
| 19 | [SETTINGS-001](SETTINGS-001_auth-provider-display.md) | Show auth provider | Medium | Minor UX improvement |
| 20 | [DOC-002](DOC-002_download-document.md) | Download document option | Medium | Convenience feature |
| 21 | [PROJECT-001](PROJECT-001_tab-persistence.md) | Tab state persistence | Medium | Navigation polish |
| 22 | [DOC-004](DOC-004_conversation-export.md) | Conversation export docs | Medium | Feature clarity |
| 23 | [DOC-003](DOC-003_token-refresh-docs.md) | Token refresh docs | Medium | Documentation |
| 24 | [DOC-005](DOC-005_file-size-error.md) | File size error UX | Medium | Error handling |
| 25 | [THREAD-009](THREAD-009_message-count-definition.md) | Message count definition | Medium | Documentation |
| 26 | [THREAD-010](THREAD-010_chat-input-lines.md) | Increase chat input lines | Low | Minor UX |
| 27 | [RESPONSIVE-001](RESPONSIVE-001_tablet-breakpoint.md) | Tablet breakpoint review | Low | Layout polish |
| 28 | [AUTH-001](AUTH-001_session-duration.md) | Session duration docs | Low | Documentation |
| 29 | [STATE-001](STATE-001_usage-provider.md) | UsageProvider docs | Low | Documentation |

---

## Critical Priority (Rank 1-6)

Blocking issues and core workflow problems. Address first.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 1 | [BUG-001](BUG-001_page-refresh-loses-url.md) | Page refresh loses URL | Open | Router |
| 2 | [US-004](US-004_unique-conversation-urls.md) | Unique conversation URLs | Open | Router |
| 3 | [US-001](US-001_url-preservation-on-refresh.md) | URL preservation on refresh | Open | Router |
| 4 | [US-003](US-003_auth-redirect-with-return-url.md) | Auth redirect with return URL | Open | Auth |
| 5 | [THREAD-001](THREAD-001_retry-failed-messages.md) | Retry failed AI messages | **Done** | Conversation |
| 6 | [THREAD-002](THREAD-002_copy-ai-responses.md) | Copy AI responses | **Done** | Message Bubble |

---

## High Priority (Rank 7-16)

High-value features and UX improvements.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 7 | [THREAD-003](THREAD-003_rename-thread.md) | Rename thread after creation | **Done** | Thread List |
| 8 | [THREAD-004](THREAD-004_network-interruption-streaming.md) | Handle network interruption | Open | Streaming |
| 9 | [US-002](US-002_deep-link-support.md) | Deep link support | Open | Router |
| 10 | [DELETE-001](DELETE-001_undo-behavior.md) | Consistent undo behavior | Open | Deletion |
| 11 | [BUDGET-001](BUDGET-001_token-budget-ux.md) | Token budget exhaustion UX | Open | Settings |
| 12 | [THREAD-005](THREAD-005_mode-persistence.md) | Show conversation mode | Open | Conversation |
| 13 | [NAV-001](NAV-001_breadcrumb-thread-context.md) | Breadcrumb for threads | Open | Navigation |
| 14 | [DOC-001](DOC-001_document-preview-upload.md) | Document preview before upload | Open | Documents |
| 15 | [THREAD-006](THREAD-006_search-filter-threads.md) | Search/filter threads | Open | Thread List |
| 16 | [THREAD-007](THREAD-007_artifact-generation-ui.md) | Artifact generation UI | Open | Conversation |

---

## Medium Priority (Rank 17-25)

Polish and documentation improvements.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 17 | [THREAD-008](THREAD-008_document-sources.md) | Show AI document sources | Open | Conversation |
| 18 | [HOME-001](HOME-001_button-differentiation.md) | Differentiate home buttons | Open | Home |
| 19 | [SETTINGS-001](SETTINGS-001_auth-provider-display.md) | Show auth provider | Open | Settings |
| 20 | [DOC-002](DOC-002_download-document.md) | Download document option | Open | Documents |
| 21 | [PROJECT-001](PROJECT-001_tab-persistence.md) | Tab state persistence | Open | Projects |
| 22 | [DOC-004](DOC-004_conversation-export.md) | Conversation export docs | Open | Documentation |
| 23 | [DOC-003](DOC-003_token-refresh-docs.md) | Token refresh docs | Open | Documentation |
| 24 | [DOC-005](DOC-005_file-size-error.md) | File size error UX | Open | Documents |
| 25 | [THREAD-009](THREAD-009_message-count-definition.md) | Message count definition | Open | Thread List |

---

## Low Priority (Rank 26-29)

Minor improvements and polish.

| Rank | ID | Title | Status | Component |
|------|-----|-------|--------|-----------|
| 26 | [THREAD-010](THREAD-010_chat-input-lines.md) | Increase chat input lines | Open | Conversation |
| 27 | [RESPONSIVE-001](RESPONSIVE-001_tablet-breakpoint.md) | Tablet breakpoint review | Open | Layout |
| 28 | [AUTH-001](AUTH-001_session-duration.md) | Session duration docs | Open | Documentation |
| 29 | [STATE-001](STATE-001_usage-provider.md) | UsageProvider docs | Open | Documentation |

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
