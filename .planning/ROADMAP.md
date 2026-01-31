# Roadmap: v1.8 LLM Provider Switching

**Milestone:** v1.8
**Created:** 2026-01-31
**Status:** In Progress

---

## Overview

Enable users to select from multiple LLM providers (Claude, Gemini, DeepSeek) for conversations. Each conversation binds to a specific provider at creation time and persists that binding. Backend adapter pattern normalizes response formats so frontend treats all providers identically.

---

## Phases

### Phase 19: backend-abstraction

**Goal:** Provider-agnostic adapter pattern established with Anthropic implementation extracted from existing code.

**Dependencies:** None (foundation phase)

**Requirements:**
- BACK-01: Adapter pattern abstracts provider API differences
- BACK-02: Anthropic adapter extracted from current implementation
- BACK-06: StreamChunk normalizes response format across providers

**Success Criteria:**
1. User can send a message and receive streaming response using new adapter architecture
2. Existing Anthropic functionality works identically through extracted adapter
3. StreamChunk dataclass provides unified format for content, thinking blocks, and errors
4. LLMFactory can instantiate adapters by provider name string

**Plans:** 2 plans
Plans:
- [x] 19-01-PLAN.md - Create LLM abstraction layer (base, adapter, factory)
- [x] 19-02-PLAN.md - Wire adapter into AIService

**Completed:** 2026-01-31

---

### Phase 20: database-api

**Goal:** Thread model stores provider information and backend handles extended thinking timeouts.

**Dependencies:** Phase 19 (adapter pattern must exist)

**Requirements:**
- CONV-02: Thread database stores `model_provider` column
- BACK-05: SSE heartbeats prevent timeout during extended thinking (5+ min)

**Success Criteria:**
1. Creating a thread with provider parameter stores provider in database
2. Fetching existing thread returns its stored provider
3. Chat endpoint selects correct adapter based on thread's provider
4. SSE stream sends heartbeat events every 15 seconds during extended thinking

**Plans:** 2 plans
Plans:
- [x] 20-01-PLAN.md - Add model_provider column to Thread and update API
- [x] 20-02-PLAN.md - Implement SSE heartbeat wrapper for extended thinking

**Completed:** 2026-01-31

---

### Phase 21: provider-adapters

**Goal:** Gemini and DeepSeek adapters implemented with provider-specific handling.

**Dependencies:** Phase 20 (database must support provider storage)

**Requirements:**
- BACK-03: Gemini adapter using `google-genai` SDK with streaming
- BACK-04: DeepSeek adapter using OpenAI SDK with `base_url` override

**Success Criteria:**
1. User can create conversation with Gemini provider and receive streaming responses
2. User can create conversation with DeepSeek provider and receive streaming responses
3. Gemini thinking output normalized to StreamChunk format
4. DeepSeek reasoning_content normalized to StreamChunk format

---

### Phase 22: frontend-provider-ui

**Goal:** Users can select and view provider information in the Flutter application.

**Dependencies:** Phase 21 (all backend providers must work)

**Requirements:**
- SET-01: User can select default LLM provider in Settings (Claude/Gemini/DeepSeek)
- SET-02: Provider selection persists across sessions via SharedPreferences
- CONV-01: New conversations use the currently selected default provider
- CONV-03: Returning to existing conversation uses its stored model (not current default)
- UI-01: Model indicator displays below chat window showing provider name
- UI-02: Indicator uses provider-specific color accent (visual differentiation)

**Success Criteria:**
1. User can change default provider in Settings and see change persist after app restart
2. Starting new conversation uses current default provider setting
3. Opening existing conversation shows its bound provider (not current default)
4. Model indicator below chat shows provider name with distinct color per provider

---

## Progress

| Phase | Name | Requirements | Status |
|-------|------|--------------|--------|
| 19 | backend-abstraction | BACK-01, BACK-02, BACK-06 | Complete |
| 20 | database-api | CONV-02, BACK-05 | Complete |
| 21 | provider-adapters | BACK-03, BACK-04 | Pending |
| 22 | frontend-provider-ui | SET-01, SET-02, CONV-01, CONV-03, UI-01, UI-02 | Pending |

**Coverage:** 13/13 requirements mapped

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Phase structure | 4 phases | Research recommended 5, compressed to 4 for quick depth |
| Adapter pattern | Abstract base class + factory | Well-documented pattern, enables future providers |
| StreamChunk normalization | Backend responsibility | Frontend treats all providers identically |
| SSE heartbeats | Every 15 seconds | Prevents timeout during 30+ second thinking delays |

---

*Roadmap created: 2026-01-31*
*Phase 19 planned: 2026-01-31*
*Phase 19 complete: 2026-01-31*
*Phase 20 planned: 2026-01-31*
*Phase 20 complete: 2026-01-31*
