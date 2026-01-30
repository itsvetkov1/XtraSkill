# Requirements: Business Analyst Assistant v1.6

**Defined:** 2026-01-30
**Core Value:** Reduce friction in the core conversation workflow — users can recover from errors, copy content easily, organize threads, and identify their account.

## v1 Requirements

Requirements for v1.6 UX Quick Wins release. Each maps to roadmap phases.

### Error Recovery

- [ ] **RETRY-01**: Error banner shows "Dismiss | Retry" actions when AI request fails
- [ ] **RETRY-02**: Retry resends the last user message without retyping
- [ ] **RETRY-03**: Failed message state tracked in ConversationProvider
- [ ] **RETRY-04**: Works for both network errors and API errors

### Content Copying

- [ ] **COPY-01**: Copy icon button visible on all assistant messages
- [ ] **COPY-02**: Copy action copies full message content to clipboard
- [ ] **COPY-03**: Snackbar confirms "Copied to clipboard"
- [ ] **COPY-04**: Copy works cross-platform (web, Android, iOS) with error handling

### Thread Management

- [ ] **THREAD-01**: Edit icon in ConversationScreen AppBar opens rename dialog
- [ ] **THREAD-02**: "Rename" option in Thread List PopupMenu
- [ ] **THREAD-03**: Dialog pre-fills current thread title
- [ ] **THREAD-04**: Backend PATCH endpoint for thread rename

### Settings Enhancement

- [ ] **SETTINGS-01**: Auth provider indicator shown in Settings profile section
- [ ] **SETTINGS-02**: Display format: "Signed in with Google" or "Signed in with Microsoft"

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Error Recovery Enhancements

- **RETRY-05**: Partial response preserved on network interruption during streaming
- **RETRY-06**: "Regenerate" option for alternative AI response

### Content Copying Enhancements

- **COPY-05**: Long-press menu includes "Copy" option alongside Delete
- **COPY-06**: Copy code blocks individually (separate from full message)

### Thread Management Enhancements

- **THREAD-05**: Inline rename (tap title to edit without dialog)
- **THREAD-06**: Thread list search and filter

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Brand icons for OAuth providers | Adds package dependency (font_awesome_flutter ~2MB), text indicator sufficient |
| Inline thread rename | Dialog pattern matches existing codebase (ThreadCreateDialog), simpler to maintain |
| Long-press copy menu | One-tap copy button provides sufficient convenience |
| Retry with regenerate option | Simple resend is MVP; regenerate adds AI cost implications |
| Partial streaming response preservation | Complex state management; deferred to v2 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| RETRY-01 | TBD | Pending |
| RETRY-02 | TBD | Pending |
| RETRY-03 | TBD | Pending |
| RETRY-04 | TBD | Pending |
| COPY-01 | TBD | Pending |
| COPY-02 | TBD | Pending |
| COPY-03 | TBD | Pending |
| COPY-04 | TBD | Pending |
| THREAD-01 | TBD | Pending |
| THREAD-02 | TBD | Pending |
| THREAD-03 | TBD | Pending |
| THREAD-04 | TBD | Pending |
| SETTINGS-01 | TBD | Pending |
| SETTINGS-02 | TBD | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 0
- Unmapped: 14

---
*Requirements defined: 2026-01-30*
*Last updated: 2026-01-30 after initial definition*
