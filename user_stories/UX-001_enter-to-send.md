# UX-001: Enter Key Sends Message

**Priority:** High
**Status:** Open
**Component:** Chat Input
**Created:** 2026-01-31

---

## User Story

As a user composing a chat message,
I want pressing Enter to send my message immediately,
So that I can communicate quickly without reaching for a button.

---

## Current Behavior

- Pressing Enter creates a new line in the input field
- User must click "Send" button or use no keyboard shortcut
- This differs from standard chat app conventions (Slack, Discord, Teams)

---

## Desired Behavior

| Action | Result |
|--------|--------|
| Enter | Send message (if input not empty) |
| Enter (empty input) | Nothing happens (ignored) |
| Shift+Enter | Insert new line |

---

## Acceptance Criteria

- [ ] Pressing Enter in chat input sends the message
- [ ] Pressing Enter with empty input does nothing (no error, no empty send)
- [ ] Pressing Shift+Enter inserts a new line
- [ ] Multi-line messages can still be composed using Shift+Enter
- [ ] Send button remains functional as alternative
- [ ] Behavior works on web (Chrome, Firefox, Safari)
- [ ] Behavior works on mobile (if applicable - may need different handling)

---

## Technical Notes

**Files likely affected:**
- `frontend/lib/screens/conversation/widgets/chat_input.dart`

**Implementation approach:**
- Add `onKey` or `onKeyEvent` handler to TextField
- Check for Enter key without Shift modifier
- Call send function if input is not empty
- Allow default behavior (new line) only when Shift is held

**Edge cases:**
- IME composition (Chinese, Japanese input) - Enter may confirm character, not send
- Mobile keyboards - Enter behavior may differ

---

## Dependencies

None - standalone UX improvement

---

## Design Reference

Standard chat application behavior:
- Slack: Enter sends, Shift+Enter for newline
- Discord: Enter sends, Shift+Enter for newline
- Microsoft Teams: Enter sends, Shift+Enter for newline

---

*Created: 2026-01-31*
