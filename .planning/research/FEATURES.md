# Feature Landscape: Multi-LLM Provider Switching

**Domain:** AI Chat Application with LLM Provider Switching
**Researched:** 2026-01-31
**Confidence:** HIGH (verified with multiple sources and competitor analysis)

---

## Executive Summary

Multi-LLM provider switching is a well-established pattern in AI chat applications. The user's requirements align with industry best practices:
- Global default model in settings
- Per-conversation model binding
- Visual model indicator
- Conversation model persistence

This document categorizes features into table stakes (must have), differentiators (competitive advantage), and anti-features (deliberately NOT building in v1.8).

---

## Table Stakes

Features users expect from any multi-model AI chat application. Missing = product feels incomplete.

### TS-01: Global Default Model Setting

| Aspect | Details |
|--------|---------|
| **Feature** | User can set their preferred default model in Settings |
| **Why Expected** | [Open WebUI](https://docs.openwebui.com/features/chat-features/chat-params/), [TypingMind](https://docs.typingmind.com/feature-list), and all major multi-model interfaces provide this |
| **Complexity** | Low |
| **Notes** | Default model auto-selected when starting new conversations |

**Implementation pattern:**
- Settings page dropdown showing available providers/models
- Persisted to user preferences (SharedPreferences or backend)
- Applied automatically to new conversations

### TS-02: Per-Conversation Model Binding

| Aspect | Details |
|--------|---------|
| **Feature** | Each conversation remembers which model it uses |
| **Why Expected** | Core UX pattern in [Open WebUI](https://deepwiki.com/daw/open-webui/3.3-model-selection), [LibreChat](https://github.com/danny-avila/LibreChat/discussions/3999), TypingMind |
| **Complexity** | Medium |
| **Notes** | Stored in conversation/thread metadata in database |

**Why this matters:**
- Users may use different models for different tasks
- Switching models mid-conversation preserves context but may cause quality inconsistencies
- Existing conversations should "remember" their model when reopened

### TS-03: Model Selector at Conversation Start

| Aspect | Details |
|--------|---------|
| **Feature** | User can select model when starting a new conversation |
| **Why Expected** | Standard pattern in ChatGPT, Claude.ai, TypingMind, Open WebUI |
| **Complexity** | Low |
| **Notes** | Dropdown/selector above or beside chat input for new conversations |

**Implementation options:**
- Dropdown in chat header (Open WebUI style)
- Model picker in chat input area (ChatGPT style)
- Pre-defaults to global setting, can override per-conversation

### TS-04: Visual Model Indicator

| Aspect | Details |
|--------|---------|
| **Feature** | Display which model is active for current conversation |
| **Why Expected** | Users need to know which AI they're talking to for context and cost awareness |
| **Complexity** | Low |
| **Notes** | Badge, label, or icon showing current model |

**Common placements:**
- Below chat input (user's stated preference)
- In chat header beside conversation title
- As subtle badge on each AI response bubble

**Reference implementations:**
- [JetBrains AI Assistant](https://www.jetbrains.com/help/ai-assistant/ai-chat.html) shows model picker with current selection
- [ChatGPT](https://help.openai.com/en/articles/7864572-what-is-the-chatgpt-model-selector) shows model name in conversation header
- [Aethera](https://help.aethera.ai/chat-interface/model-selection) shows dropdown with current model visible

### TS-05: Model Persistence on Conversation Return

| Aspect | Details |
|--------|---------|
| **Feature** | Returning to existing conversation uses its bound model, not current default |
| **Why Expected** | Prevents confusion when users switch between conversations |
| **Complexity** | Low (once TS-02 implemented) |
| **Notes** | Critical for user's stated requirement |

**User's explicit requirement:** "Existing conversations keep their original model when returning to them"

### TS-06: API Key Management (BYOK)

| Aspect | Details |
|--------|---------|
| **Feature** | User provides their own API keys for each provider |
| **Why Expected** | Standard for cost-optimized multi-provider apps; see [Warp](https://docs.warp.dev/support-and-billing/plans-and-pricing/bring-your-own-api-key), [OpenRouter](https://openrouter.ai/announcements/bring-your-own-api-keys), [GitHub Copilot BYOK](https://github.blog/changelog/2025-11-20-enterprise-bring-your-own-key-byok-for-github-copilot-is-now-in-public-preview/) |
| **Complexity** | Medium |
| **Notes** | Keys stored securely (encrypted), never synced to cloud without user consent |

**Security requirements:**
- Keys stored locally on device OR encrypted at rest in backend
- Keys never logged or exposed in error messages
- Clear indication of which keys are configured

### TS-07: Provider Availability Indication

| Aspect | Details |
|--------|---------|
| **Feature** | Show which providers are available (have valid API keys) |
| **Why Expected** | Users need to know what's available before selecting |
| **Complexity** | Low |
| **Notes** | Visual indicator (checkmark, green dot) for configured providers |

---

## Differentiators

Features that set product apart. Not expected, but valued. Consider for v1.8 or later versions.

### DIF-01: Cost Indicator per Model

| Aspect | Details |
|--------|---------|
| **Feature** | Show relative cost ($/1M tokens or simple low/medium/high) per model |
| **Value Proposition** | User's stated goal is cost optimization; helps informed decisions |
| **Complexity** | Low |
| **Notes** | Can be static metadata, doesn't need real-time pricing |

**Why valuable:** User explicitly mentioned wanting to switch providers for cost optimization. Showing relative cost helps them make informed decisions.

### DIF-02: Model Capability Tags

| Aspect | Details |
|--------|---------|
| **Feature** | Tags showing model strengths (e.g., "Best for code", "Fast", "Creative writing") |
| **Value Proposition** | Helps users choose right model for their task |
| **Complexity** | Low |
| **Notes** | Static metadata per model |

### DIF-03: Quick Model Switcher in Active Conversation

| Aspect | Details |
|--------|---------|
| **Feature** | Allow switching model mid-conversation without losing context |
| **Value Proposition** | Flexibility when starting with cheap model, escalating for complex questions |
| **Complexity** | Medium |
| **Notes** | Requires clear UX for context warning |

**Pattern from [TypingMind](https://blog.typingmind.com/optimize-token-costs-for-chatgpt-and-llm-api/):** "When you finish all the tough questions, switch to a more budget-friendly model for easier tasks"

**Warning needed:** "Switching models mid-conversation: New model will receive full conversation history but may respond differently."

### DIF-04: Multi-Model Response Comparison

| Aspect | Details |
|--------|---------|
| **Feature** | Send same prompt to multiple models, compare responses side-by-side |
| **Value Proposition** | Helps evaluate model quality for specific use cases |
| **Complexity** | High |
| **Notes** | [TypingMind multi-model feature](https://docs.typingmind.com/manage-and-connect-ai-models/activate-multi-model-responses), [Open WebUI dual-model](https://docs.openwebui.com/features/chat-features/) |

**Defer to post-v1.8:** High complexity, nice-to-have rather than core need.

### DIF-05: Automatic Model Selection Based on Task

| Aspect | Details |
|--------|---------|
| **Feature** | "Smart Mode" that routes to appropriate model based on query complexity |
| **Value Proposition** | Cost optimization without manual selection |
| **Complexity** | High |
| **Notes** | Requires query classification, complex to implement well |

**Pattern from [MultipleChat](https://multiple.chat/):** "Smart Mode" uses collaborative AI processing to route to best model.

**Defer:** High complexity, needs sophisticated routing logic.

### DIF-06: Token/Cost Tracking per Model

| Aspect | Details |
|--------|---------|
| **Feature** | Show token usage and estimated cost breakdown by model |
| **Value Proposition** | Direct support for user's cost optimization goal |
| **Complexity** | Medium |
| **Notes** | Requires tracking usage per provider |

---

## Anti-Features

Features to explicitly NOT build for v1.8. Common mistakes in this domain.

### AF-01: Mid-Conversation Model Switching Without Warning

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Silent model switching | Confuses users; context may be interpreted differently | Always show clear indicator when model changes; warn about potential consistency issues |

**Source:** [How to fix AI chatbot that switches models mid-conversation](https://www.arsturn.com/blog/how-to-fix-an-ai-chatbot-that-switches-models-mid-conversation) - "The new model often doesn't have the context of the previous conversation. It's like a new person jumping into a conversation without being caught up."

### AF-02: Automatic Model Downgrade Without User Consent

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Auto-switching to cheaper model when budget exhausted | Unexpected behavior change; quality degradation | Show clear budget warning; let user explicitly choose to switch or stop |

### AF-03: Provider-Specific Feature Parity Assumptions

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Assuming all providers support same features | OpenAI has JSON mode, Claude has tool use differences, Gemini has different context windows | Abstract common interface; disable unsupported features per provider |

**Note for BA Assistant:** The current Business Analyst skill uses Claude-specific tool calling. Other providers may need adapted prompts or reduced functionality.

### AF-04: Complex Model Hierarchies/Routing in Settings

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Complex rules for model selection (if X then use Y) | Overwhelming for users; hard to debug | Keep it simple: one default, per-conversation override |

### AF-05: Real-Time Pricing API Integration

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Fetching live pricing from provider APIs | Adds complexity, failure points; pricing rarely changes | Use static cost tier metadata; update with app releases |

### AF-06: Cross-Provider Conversation Migration

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Ability to "migrate" conversation history between providers | Complex; formats differ; expectations mismatch | Per-conversation binding is simpler; user can start new conversation with different model |

### AF-07: Provider Account Linking (OAuth)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full OAuth integration with provider accounts | Overly complex; most users just want to paste API keys | Simple API key entry with validation |

---

## Feature Dependencies

```
Global Default Setting (TS-01)
    |
    v
Per-Conversation Model Binding (TS-02)
    |
    +---> Model Selector at Start (TS-03)
    |
    +---> Model Persistence on Return (TS-05)
    |
    v
Visual Model Indicator (TS-04)
    |
    v
[Optional] Quick Model Switcher (DIF-03)

API Key Management (TS-06)
    |
    v
Provider Availability Indication (TS-07)
    |
    +---> Cost Indicator (DIF-01)
    |
    +---> Capability Tags (DIF-02)
```

---

## MVP Recommendation for v1.8

### Must Include (Table Stakes)

1. **TS-01: Global Default Model Setting** - User's explicit requirement
2. **TS-02: Per-Conversation Model Binding** - User's explicit requirement
3. **TS-03: Model Selector at Conversation Start** - Natural extension of TS-02
4. **TS-04: Visual Model Indicator** - User's explicit requirement ("below chat window")
5. **TS-05: Model Persistence on Return** - User's explicit requirement
6. **TS-06: API Key Management** - Required for multi-provider to function
7. **TS-07: Provider Availability Indication** - Necessary UX for key management

### Consider Including (High-Value Differentiators)

1. **DIF-01: Cost Indicator** - Directly supports user's cost optimization goal
2. **DIF-02: Capability Tags** - Low effort, helps model selection

### Defer to Post-v1.8

- **DIF-03: Quick Model Switcher** - Nice to have, adds complexity
- **DIF-04: Multi-Model Comparison** - High complexity
- **DIF-05: Automatic Model Selection** - Very high complexity
- **DIF-06: Token/Cost Tracking per Model** - Medium complexity, post-MVP

---

## Provider-Specific Considerations

### Claude (Anthropic) - Currently Implemented

- Tool use (function calling) fully supported
- Current BA skill is Claude-optimized
- Context window: 200K tokens (Claude 3+)
- Streaming supported

### Gemini (Google)

- Tool use supported but different API shape
- Context window: Up to 1M tokens (Gemini 1.5)
- May need adapted system prompts
- Streaming supported

### DeepSeek

- OpenAI-compatible API format
- Very cost-effective for simpler tasks
- Limited tool use capabilities
- May not support all BA skill features

### Abstraction Requirement

The backend needs an abstraction layer that:
1. Normalizes request/response formats across providers
2. Handles tool calling differences gracefully
3. Degrades gracefully when provider doesn't support a feature
4. Maintains conversation history format compatibility

---

## UX Patterns from Competitors

### Open WebUI Pattern
- Model dropdown in conversation header
- Per-chat and per-model settings hierarchy
- "Set as default" one-click action
- Model hiding for deprecated options

### TypingMind Pattern
- Model selector prominently placed
- Multi-model responses (premium feature)
- Clear cost optimization guidance in docs
- AI character/persona system

### ChatGPT Pattern
- Minimal model selector (hidden in dropdown)
- Model capabilities explained on hover
- Conversation locked to model after first message (by design)

---

## Sources

### Primary Sources
- [Open WebUI Documentation - Chat Parameters](https://docs.openwebui.com/features/chat-features/chat-params/)
- [Open WebUI - Model Selection](https://deepwiki.com/daw/open-webui/3.3-model-selection)
- [TypingMind Feature List](https://docs.typingmind.com/feature-list)
- [TypingMind Multi-Model Responses](https://docs.typingmind.com/manage-and-connect-ai-models/activate-multi-model-responses)
- [ChatGPT Model Selector Help](https://help.openai.com/en/articles/7864572-what-is-the-chatgpt-model-selector)

### BYOK/API Key Management
- [Warp BYOK Documentation](https://docs.warp.dev/support-and-billing/plans-and-pricing/bring-your-own-api-key)
- [GitHub Copilot BYOK](https://github.blog/changelog/2025-11-20-enterprise-bring-your-own-key-byok-for-github-copilot-is-now-in-public-preview/)
- [OpenRouter BYOK](https://openrouter.ai/announcements/bring-your-own-api-keys)

### Cost Optimization Strategies
- [TypingMind - Optimize Token Costs](https://blog.typingmind.com/optimize-token-costs-for-chatgpt-and-llm-api/)
- [Eden AI - Control Token Usage](https://www.edenai.co/post/how-to-control-token-usage-and-cut-costs-on-ai-apis)

### Multi-Model Architecture
- [Stream - Multi-Model AI Chat](https://getstream.io/blog/multi-model-ai-chat/)
- [Medium - Multi-Provider Chat App](https://medium.com/@richardhightower/multi-provider-chat-app-litellm-streamlit-ollama-gemini-claude-perplexity-and-modern-llm-afd5218c7eab)
- [Building Multi-AI Chat Platform](https://medium.com/@reactjsbd/building-a-complete-multi-ai-chat-platform-chatgpt-claude-gemini-grok-in-one-interface-4295d10e3174)

### Context/Model Switching Pitfalls
- [Fix AI Chatbot Model Switching Issues](https://www.arsturn.com/blog/how-to-fix-an-ai-chatbot-that-switches-models-mid-conversation)
- [LibreChat Model Switching Discussion](https://github.com/danny-avila/LibreChat/discussions/3999)
- [Cursor Forum - Model Context](https://forum.cursor.com/t/if-i-change-a-model-will-the-new-model-know-the-previous-context/43939)

---

*Research completed 2026-01-31. Ready for requirements definition.*
