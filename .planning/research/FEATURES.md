# Feature Research

**Domain:** Multi-mode AI chat application with specialized assistants
**Researched:** 2026-02-17
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Separate thread list per assistant | Standard pattern for multi-assistant apps (Slack workspaces, Discord servers) | LOW | Already have thread list screen; clone for Assistant section |
| Visual differentiation in UI | Users need to know which assistant context they're in | LOW | Sidebar entry + distinct UI treatment (icon, color, or label) |
| Thread persistence | Conversations must survive app restart | LOW | Already implemented; no new backend changes needed |
| Message history | Full conversation context retained across sessions | LOW | Already implemented via Thread.messages relationship |
| Streaming responses | Real-time token display standard for modern AI UX | LOW | Already implemented; CLI adapter supports streaming |
| Thread creation | Ability to start new conversations | LOW | Reuse existing thread_create_dialog with assistant context |
| Thread rename | Users expect to organize conversations with meaningful names | LOW | Already implemented; works for all thread types |
| Thread delete | Ability to remove unwanted conversations | LOW | Already implemented with undo behavior |
| Provider indicator | Show which AI backend is powering responses | LOW | Already implemented; provider_indicator widget exists |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Document upload per assistant | Context-aware file sharing unique to each mode | MEDIUM | Requires document-assistant association; BA uses project-scoped docs |
| Mode-specific system prompts | BA = business analysis focus, Assistant = general purpose | LOW | Backend already supports per-provider routing; add context flag |
| Seamless mode switching | Users can switch contexts without losing place | MEDIUM | Navigation state preservation + breadcrumb updates |
| Thread search across assistants | Find conversations regardless of mode | LOW | Extend existing FTS5 search with assistant_type filter |
| Persistent conversation memory | CLI sessions maintain context across requests | MEDIUM | CLI adapter manages session lifecycle; already implemented |
| Agentic tool execution | Assistant can search docs and save artifacts | LOW | MCP tools already integrated in CLI adapter |
| Thinking process visibility | Show reasoning steps (extended thinking mode) | LOW | StreamChunk already supports thinking events |
| Export conversations | Download thread history for external use | MEDIUM | Thread export feature not yet implemented for any mode |

### Anti-Features (Commonly Requested, Often Problematic)

Features to explicitly NOT build.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Universal thread list | "I want to see all threads in one view" | Context confusion — users lose track of which assistant mode a thread uses | Separate lists with global search for finding specific threads |
| Assistant switching mid-thread | "I want to change AI provider in existing conversation" | System prompt contamination — BA context bleeds into general chat | Create new thread in correct mode, reference previous conversation if needed |
| Shared document pool | "Upload once, use in both modes" | Context pollution — BA requirements docs appear in general chat results | Assistant-scoped documents; explicit copy between modes if needed |
| Real-time sync between assistants | "Assistant should know what BA discussed" | Privacy violation and context bloat | Manual cross-reference via thread URLs or explicit summaries |

## Feature Dependencies

```
[Separate Thread List]
    └──requires──> [Assistant Type Field] (thread.assistant_type: 'ba' | 'general')

[Document Upload per Assistant]
    └──requires──> [Document-Assistant Association]
                       └──requires──> [Assistant Type Field]

[Mode-Specific System Prompts]
    └──requires──> [Assistant Type Field]

[Thread Search Across Assistants] ──enhances──> [Separate Thread List]

[Seamless Mode Switching] ──requires──> [Navigation State Preservation]

[Export Conversations] ──independent──> [All other features]
```

### Dependency Notes

- **Separate Thread List requires Assistant Type Field:** Database schema needs `thread.assistant_type` (ENUM: 'ba', 'general') to filter threads by mode
- **Document Upload requires Document-Assistant Association:** Documents must be scoped to assistant type, not just project (project can be NULL for Assistant mode)
- **Thread Search enhances Separate Thread List:** Global search becomes more valuable when threads are separated by default
- **Seamless Mode Switching requires Navigation State:** Router must preserve scroll position, selected thread, and breadcrumb context when switching modes

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [x] **Assistant Type Field** — `thread.assistant_type` distinguishes BA vs Assistant threads
- [x] **Separate Sidebar Entry** — "Assistant" appears in navigation, distinct from "BA Assistant" sections
- [x] **Dedicated Thread List Screen** — Assistant threads shown separately from BA threads
- [x] **Thread Creation** — New threads created with `assistant_type='general'` and `model_provider='claude-code-cli'`
- [x] **CLI Backend Integration** — Claude Code CLI subprocess adapter already implemented
- [x] **Streaming Conversation** — Chat works end-to-end with CLI provider (already verified in Phase 60-61)
- [ ] **Document Upload for Assistant** — Upload files as context for Assistant conversations (project_id=NULL, assistant_type='general')
- [ ] **Mode-Specific System Prompts** — Backend routes requests based on assistant_type (no BA tools/prompts for Assistant)

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **Thread Search with Assistant Filter** — Extend FTS5 search to filter by assistant_type
- [ ] **Export Conversations** — Download thread history as Markdown or PDF (applies to both BA and Assistant)
- [ ] **Document Management UI** — Dedicated screen for viewing/deleting Assistant documents (similar to project documents)
- [ ] **Cross-Mode References** — Generate shareable URLs for threads to reference across modes

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Conversation Templates** — Pre-built thread starters for common Assistant use cases
- [ ] **Multi-Assistant Workflows** — Explicit handoffs between BA and Assistant (e.g., "Ask Assistant to write copy based on this BRD")
- [ ] **Assistant Customization** — User-defined system prompts or personas for Assistant mode
- [ ] **Voice Input** — Multimodal interaction for Assistant conversations

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Assistant Type Field | HIGH | LOW | P1 |
| Separate Sidebar Entry | HIGH | LOW | P1 |
| Dedicated Thread List Screen | HIGH | LOW | P1 |
| Thread Creation for Assistant | HIGH | LOW | P1 |
| Mode-Specific System Prompts | HIGH | LOW | P1 |
| Document Upload for Assistant | MEDIUM | MEDIUM | P1 |
| CLI Backend Integration | HIGH | LOW | P1 (done) |
| Streaming Conversation | HIGH | LOW | P1 (done) |
| Thread Search with Filter | MEDIUM | LOW | P2 |
| Export Conversations | MEDIUM | MEDIUM | P2 |
| Document Management UI | MEDIUM | MEDIUM | P2 |
| Cross-Mode References | LOW | MEDIUM | P3 |
| Conversation Templates | LOW | MEDIUM | P3 |
| Multi-Assistant Workflows | LOW | HIGH | P3 |
| Assistant Customization | MEDIUM | HIGH | P3 |
| Voice Input | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch (MVP)
- P2: Should have, add when possible (Post-validation)
- P3: Nice to have, future consideration

## Existing Features to Reuse

The app already has robust infrastructure that makes Assistant separation easier:

| Existing Feature | How Assistant Reuses It |
|------------------|-------------------------|
| Thread model | Add `assistant_type` ENUM field ('ba', 'general'); default 'ba' for backward compatibility |
| Thread list screen | Clone `thread_list_screen.dart` → `assistant_thread_list_screen.dart` with filtered query |
| Thread creation dialog | Extend with `assistant_type` parameter; hardcode `model_provider='claude-code-cli'` for Assistant |
| Conversation screen | No changes needed; works for any thread type |
| Message bubbles | Already supports streaming, thinking, and tool execution |
| Document model | Add `assistant_type` field; allow `project_id=NULL` for Assistant documents |
| Document upload | Clone for Assistant mode with `assistant_type='general'` and `project_id=NULL` |
| Provider routing | LLMFactory already routes by `model_provider`; add context for system prompt selection |
| FTS5 search | Extend `search_threads()` with optional `assistant_type` filter |
| Streaming SSE | Works for all providers; no changes needed |
| Token tracking | Already records usage per thread; works transparently |

## Competitor Feature Analysis

| Feature | ChatGPT (Projects) | Claude (Projects) | Perplexity (Spaces) | Our Approach |
|---------|-------------------|-------------------|---------------------|--------------|
| Mode Separation | Projects for context isolation | Projects with custom instructions | Spaces for different search contexts | Sidebar entries for BA vs Assistant |
| Thread Organization | Folders within projects | Projects as containers | Spaces as top-level containers | Assistant type as top-level navigation |
| Document Context | Per-project file uploads | Per-project knowledge | Per-space document library | Per-assistant document scoping |
| System Prompts | Custom instructions per project | Project-level prompts | Space-level search modes | Backend routing by assistant_type |
| Thread Search | Global search across projects | Search within project | Search within space | Global search with assistant filter |

## Sources

### Multi-Mode AI Chat Patterns
- [AI UI Patterns](https://www.patterns.dev/react/ai-ui-patterns/) — Multi-mode switching, agent cards, streaming output patterns
- [Innovative Chat UI Design Trends 2025 - MultitaskAI](https://multitaskai.com/blog/chat-ui-design/) — Persona differentiation, visual separation
- [AI UX patterns in 2026: from assistants to decisions](https://nurxmedov.substack.com/p/ai-ux-patterns-in-2026-from-assistants) — Agentic design, proactive assistance
- [AI UX Patterns | Modes | ShapeofAI.com](https://www.shapeof.ai/patterns/modes) — Modes as contracts, explicit entry/exit paths

### Conversation Type Separation
- [Conversational UI: 6 Best Practices in 2026](https://research.aimultiple.com/conversational-ui/) — Separate work vs personal, AI vs human disclosure
- [Group Chat App Comparison 2026](https://trueconf.com/blog/reviews-comparisons/group-chat-app) — Topic-based channels, structured collaboration
- [The Importance of Message Threads in Team Messaging Apps](https://dispatch.m.io/message-threads/) — Context preservation, transparency, clutter reduction

### CLI Chat Interfaces
- [The Best AI Coding CLI of 2026](https://www.xugj520.cn/en/archives/best-ai-coding-cli-2026-guide.html) — Agentic autonomy, persistent memory, natural language interaction
- [Command Line Interface Guidelines](https://clig.dev/) — Human-centered design, information balance
- [GitHub - sigoden/aichat](https://github.com/sigoden/aichat) — All-in-one LLM CLI with RAG and Shell Assistant features

### Document Upload & Context Management
- [GitHub - billy-enrizky/chat-with-documents](https://github.com/billy-enrizky/chat-with-documents) — RAG with vector store, streaming responses
- [LibreChat - Upload as Text](https://www.librechat.ai/docs/features/upload_as_text) — Full document content injection, OCR enhancement
- [How Do Our Chatbots Handle Uploaded Documents?](https://medium.com/@georgekar91/how-do-our-chatbots-handle-uploaded-documents-01483cb99948) — RAG vs full text injection, semantic search

### Standalone vs Domain-Specific Assistants
- [AI Agent vs. Chatbot — What's the Difference? | Salesforce US](https://www.salesforce.com/agentforce/ai-agent-vs-chatbot/) — Multi-turn vs single-turn, context retention
- [Smarter Than a Chatbot: Inside the New Era of Domain-Specific AI Assistants](https://www.cmswire.com/contact-center/smarter-than-a-chatbot-inside-the-new-era-of-domain-specific-ai-assistants/) — RAG integration, specialized vs general-purpose

---
*Feature research for: Multi-mode AI chat application (BA Assistant vs standalone Assistant)*
*Researched: 2026-02-17*
*Confidence: MEDIUM — Based on web search of current UX patterns + analysis of existing codebase architecture*
