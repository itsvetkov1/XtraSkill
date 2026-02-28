# THREAD-004: Handle Network Interruption During Streaming

**Priority:** Critical
**Status:** Done
**Component:** Streaming Message, Conversation Provider

---

## User Story

As a user,
I want partial AI responses preserved if my connection drops,
So that I don't lose valuable content.

---

## Problem

No specification for behavior on connection loss mid-stream. Partial responses may be discarded.

---

## Acceptance Criteria

- [ ] On network loss during streaming, partial content is preserved
- [ ] Error banner shows "Connection lost - response incomplete"
- [ ] Retry option attempts to continue/regenerate response
- [ ] User can copy partial content even in error state

---

## Technical References

- `frontend/lib/screens/conversation/widgets/streaming_message.dart`
- `frontend/lib/providers/conversation_provider.dart`
