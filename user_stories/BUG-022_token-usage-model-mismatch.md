# BUG-022: Token Usage Records Wrong Model Name

**Priority:** Medium
**Status:** Done
**Component:** Backend / Token Tracking
**Discovered:** 2026-02-08

---

## User Story

As a user, I want accurate token usage tracking per provider, so that I can understand my actual costs across different AI models.

---

## Problem

When a chat uses DeepSeek Reasoner, the token usage is recorded with model `claude-sonnet-4-5-20250514` instead of `deepseek-reasoner`. This means:

1. Cost calculations are wrong (Claude pricing applied to DeepSeek tokens)
2. Per-provider usage breakdowns are inaccurate
3. Budget tracking may be misleading

The issue is in the conversations route, which uses a hardcoded `AGENT_MODEL` constant for token tracking rather than reading the actual model from the thread or AI service response.

**Additional finding (2026-02-25):** This also affects assistant threads. The `AGENT_MODEL` constant is set to `claude-sonnet-4-5-20250514` but assistant threads actually use `claude-sonnet-4-5-20250929` (DEFAULT_MODEL in `claude_cli_adapter.py`). All assistant thread cost reporting is inaccurate.

---

## Steps to Reproduce

1. Create a thread using DeepSeek Reasoner as the provider
2. Send a message and receive a response
3. Check token_usage table — model column shows `claude-sonnet-4-5-20250514` instead of `deepseek-reasoner`

---

## Evidence

Log (2026-02-08 UTC):
- `20:00:55` — AI stream starts with `model: "deepseek-reasoner"`
- `20:01:16` — Token usage INSERT records `model: "claude-sonnet-4-5-20250514"`

---

## Acceptance Criteria

- [ ] Token usage records reflect the actual model used for the request
- [ ] Cost calculation uses the correct provider's pricing
- [ ] Usage dashboard shows accurate per-provider breakdowns

---

## Technical References

- `backend/app/routes/conversations.py:203-209` — `track_token_usage()` call uses `AGENT_MODEL` constant
- Should use `thread.model_provider` or the model returned in the AI stream's usage data
