# BUG-020: DeepSeek Reasoner Cannot Read Uploaded Documents

**Priority:** Critical
**Status:** Open
**Component:** Backend / AI Service / LLM Adapters
**Discovered:** 2026-02-08

---

## User Story

As a user, I want the AI to read documents I've attached to a project, so that I can use Document Refinement Mode to modify existing BRDs.

---

## Problem

When a thread uses `deepseek-reasoner` as the model provider, the AI cannot access uploaded project documents. The AI responds with *"I don't see any documents in the system - the document search returned no results, and there appear to be some technical issues with tool calls."*

The document upload itself succeeds (201, stored in DB with FTS index), but the AI never retrieves it because:

1. Documents are **only** accessible via the `search_documents` tool — they are never injected into the system prompt or conversation context automatically.
2. `deepseek-reasoner` has **unstable tool calling support** (acknowledged in `deepseek_adapter.py:104`). The model either never invokes the tool or the tool call fails silently.
3. This creates a complete blind spot: the user uploads a document, the system confirms success, but the AI cannot see it.

### Design Gap

The architecture depends entirely on the LLM choosing to call `search_documents`. When a provider doesn't support tools reliably, documents become invisible. There is no fallback mechanism.

---

## Steps to Reproduce

1. Create a project and upload a document (e.g., `BRD.md`)
2. Open a thread in that project using DeepSeek Reasoner
3. Select "Document Refinement Mode"
4. Ask the AI to read or reference the uploaded document
5. AI responds that it cannot find any documents

---

## Evidence

Log timestamps (2026-02-08 UTC):
- `20:00:30` — `POST /api/projects/.../documents` **201** (upload success)
- `20:00:55` — AI stream starts, model: `deepseek-reasoner`, 3 messages
- `20:01:16` — AI responds: no documents found, tool call issues

---

## Acceptance Criteria

- [ ] AI can access uploaded project documents regardless of LLM provider
- [ ] If a provider does not support tool calling, documents are included in context via an alternative mechanism (e.g., injected into system prompt or first user message)
- [ ] Document Refinement Mode works with all supported providers (Anthropic, DeepSeek, Gemini)

---

## Technical References

- `backend/app/services/ai_service.py` — `stream_chat()` passes tools but never injects document content
- `backend/app/services/llm/deepseek_adapter.py:104` — comment acknowledging unstable tool support
- `backend/app/services/document_search.py` — `search_documents()` function (works correctly)
- `backend/app/routes/conversations.py:160-164` — passes `thread.project_id` to AI service

## Possible Approaches

1. **Inject document summaries into system prompt** when project has documents (provider-agnostic)
2. **Auto-switch to `deepseek-chat`** instead of `deepseek-reasoner` when tools are needed
3. **Pre-fetch and inject** document content into the conversation context before calling the LLM
