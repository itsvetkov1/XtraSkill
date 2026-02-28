# AUTH-001: Document Session Duration

**Priority:** Low
**Status:** Done
**Component:** Login Screen (Documentation)

---

## Description

Login screen doesn't indicate how long sessions last.

---

## Acceptance Criteria

- [ ] Document JWT session duration in spec
- [ ] If sessions are short (<24h), consider "Stay signed in" option
- [ ] Or document: "Sessions last 30 days unless user logs out"

---

## Technical References

- `frontend/lib/screens/auth/login_screen.dart`
- `backend/app/services/auth_service.py`
