# THREAD-005: Show Current Conversation Mode Persistently

**Priority:** High
**Status:** Done

**Resolution:** Already implemented. Mode badge in AppBar (`mode_badge.dart`) shows current mode as tappable chip. Mode change dialog (`mode_change_dialog.dart`) handles mode selection. Mode stored in thread.conversation_mode in database.
**Component:** Conversation Screen

---

## User Story

As a user,
I want to see which mode (Meeting/Document) my conversation is in,
So that I understand the AI's behavior.

---

## Problem

Mode selector disappears after first message. User can't see or change active mode.

---

## Acceptance Criteria

- [ ] Current mode shown as chip/badge in AppBar after selection
- [ ] Tapping mode badge opens menu to change mode
- [ ] Mode change shows warning about potential context shift
- [ ] Mode persists across app restarts for that thread

---

## Technical References

- `frontend/lib/screens/conversation/conversation_screen.dart`
- `frontend/lib/widgets/mode_selector.dart`
