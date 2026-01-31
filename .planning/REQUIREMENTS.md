# Requirements: v1.8 LLM Provider Switching

**Defined:** 2026-01-31
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v1.8 Requirements

Requirements for LLM provider switching. Each maps to roadmap phases.

### Settings

- [ ] **SET-01**: User can select default LLM provider in Settings (Claude/Gemini/DeepSeek)
- [ ] **SET-02**: Provider selection persists across sessions via SharedPreferences

### Conversation Binding

- [ ] **CONV-01**: New conversations use the currently selected default provider
- [ ] **CONV-02**: Thread database stores `model_provider` column
- [ ] **CONV-03**: Returning to existing conversation uses its stored model (not current default)

### UI Indicators

- [ ] **UI-01**: Model indicator displays below chat window showing provider name
- [ ] **UI-02**: Indicator uses provider-specific color accent (visual differentiation)

### Backend Integration

- [x] **BACK-01**: Adapter pattern abstracts provider API differences
- [x] **BACK-02**: Anthropic adapter extracted from current implementation
- [ ] **BACK-03**: Gemini adapter using `google-genai` SDK with streaming
- [ ] **BACK-04**: DeepSeek adapter using OpenAI SDK with `base_url` override
- [ ] **BACK-05**: SSE heartbeats prevent timeout during extended thinking (5+ min)
- [x] **BACK-06**: StreamChunk normalizes response format across providers

## v2.0 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Provider Enhancements

- **PROV-01**: Cost indicator showing relative pricing per provider
- **PROV-02**: Capability tags showing what each provider supports
- **PROV-03**: Auto-fallback when primary provider fails or rate-limits
- **PROV-04**: User-configurable API keys in Settings UI

### Advanced Features

- **ADV-01**: DeepSeek reasoning content displayed in expandable UI section
- **ADV-02**: Per-project default provider (override global setting)
- **ADV-03**: Provider usage analytics and cost tracking

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Mid-conversation provider switching | Breaks conversation context and coherence |
| Custom model parameters per provider | Complexity; use sensible defaults |
| Local/self-hosted LLM support | Infrastructure complexity, defer to v2.0+ |
| Provider-specific prompt optimization | Maintain single BA skill prompt for now |
| Real-time pricing API integration | Overkill for cost optimization goal |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SET-01 | Phase 22 | Pending |
| SET-02 | Phase 22 | Pending |
| CONV-01 | Phase 22 | Pending |
| CONV-02 | Phase 20 | Pending |
| CONV-03 | Phase 22 | Pending |
| UI-01 | Phase 22 | Pending |
| UI-02 | Phase 22 | Pending |
| BACK-01 | Phase 19 | Complete |
| BACK-02 | Phase 19 | Complete |
| BACK-03 | Phase 21 | Pending |
| BACK-04 | Phase 21 | Pending |
| BACK-05 | Phase 20 | Pending |
| BACK-06 | Phase 19 | Complete |

**Coverage:**
- v1.8 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0

---
*Requirements defined: 2026-01-31*
*Last updated: 2026-01-31 after Phase 19 completion*
