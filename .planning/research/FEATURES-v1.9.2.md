# Feature Landscape: BA Assistant v1.9.2 Resilience & AI Transparency

**Domain:** Business analyst assistant with AI conversations
**Researched:** 2026-02-02
**Confidence:** HIGH (verified against industry patterns and official sources)

---

## 1. Network Interruption Handling During Streaming

### Table Stakes (Must Have)

| Feature | Why Expected | Current State | Notes |
|---------|--------------|---------------|-------|
| Visual "thinking" indicator | Users need feedback that AI is processing | Implemented: CircularProgressIndicator + "Thinking..." | Basic implementation exists |
| Status messages during operations | Users need to know what's happening ("Searching documents...") | Implemented: `statusMessage` in StreamingMessage | Works well |
| Error message on failure | Users must know when something failed | Implemented: `_error` state in ConversationProvider | Generic error only |
| Retry capability | Users shouldn't have to retype messages | Implemented: `retryLastMessage()` | Exists but UX could improve |
| Preserve accumulated text on error | Partial responses shouldn't vanish | NOT implemented: `_streamingText = ''` on error | **GAP** |

**Industry Standard:** Reliable, resumable token streaming with WebSocket connections, server-side buffering, and message ordering (sequence identifiers). Source: [Ably Blog - Token Streaming for AI UX](https://ably.com/blog/token-streaming-for-ai-ux)

### Differentiators (Nice to Have)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Auto-reconnection with replay | Resume exactly where interrupted | High | Requires server-side buffering, unique sequence IDs |
| Multi-device/multi-tab sync | Start on laptop, continue on phone | High | Requires WebSocket with session tracking |
| Offline queuing | Send messages while offline, sync when back | Medium | Queue locally, send when connectivity returns |
| Connection health indicator | Show network status during streaming | Low | Simple UI element showing connection state |
| Exponential backoff retries | Transparent automatic recovery | Low | Backend-side implementation |

### Anti-Features (Do NOT Build)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Silent failure | Users think app is broken, lose trust | Always show error state with actionable message |
| Auto-retry without feedback | User doesn't know what's happening | Show "Reconnecting..." indicator during retries |
| Restart from scratch on error | Loses context, frustrating UX | Preserve partial response, show with error indicator |
| Aggressive retry loops | Hammers server, doesn't respect rate limits | Exponential backoff with jitter |

**Recommended Behavior:**
1. On network error during streaming: Preserve accumulated text, show error with retry button
2. On timeout: "Connection timed out. Tap to retry." with preserved context
3. On reconnection: Resume streaming or offer retry with preserved message

---

## 2. Token/Budget Exhaustion UX

### Table Stakes (Must Have)

| Feature | Why Expected | Current State | Notes |
|---------|--------------|---------------|-------|
| Budget progress bar | Users need visibility into usage | Implemented: LinearProgressIndicator in Settings | Good baseline |
| Dollar amount display | Concrete cost understanding | Implemented: "$X.XX / $Y.YY used" | Works well |
| Percentage display | Quick at-a-glance understanding | Implemented: `costPercentageDisplay` | Works well |
| Color change at threshold | Visual warning before hitting limit | Implemented: Orange color > 80% | Only in Settings screen |
| Clear limit exceeded message | User knows why they can't continue | NOT implemented | **GAP - Critical** |

**Industry Standard:** Multi-threshold alerts (50%, 80%, 100%), proactive warnings before exhaustion, clear blocked-state messaging with upgrade path. Source: [Skywork - AI API Cost Management](https://skywork.ai/blog/ai-api-cost-throughput-pricing-token-math-budgets-2025/)

### Differentiators (Nice to Have)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Persistent budget indicator in conversation | Always visible without going to Settings | Low | Small chip/badge showing usage |
| 50% threshold warning | Early awareness, can adjust behavior | Low | SnackBar or subtle indicator |
| Cost-per-message estimate | Understand impact of each interaction | Medium | Show token count and estimated cost |
| Usage trend visualization | Understand consumption patterns | Medium | Spark line or daily usage chart |
| Budget reset countdown | Know when limit resets | Low | "Resets in 5 days" |

### Anti-Features (Do NOT Build)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Hard block without warning | Surprises user mid-workflow | Warn at 80%, block at 100% with clear message |
| Truncating responses silently | User gets incomplete information | Show warning, let user choose shorter responses |
| Hidden budget information | User can't plan usage | Make budget visible and accessible |
| Vague "rate limit exceeded" | User doesn't know what to do | "Monthly budget reached. Resets on [date]." |
| Per-message cost anxiety | Discourages usage | Show budget, not per-message cost prominently |

**Recommended UX Copy for Blocked State:**
- Title: "Monthly Budget Reached"
- Body: "You've used your full $X.XX monthly budget. Your budget resets on [date]."
- Action: "View Usage Details" (link to Settings)

**Industry Standard Messages (Source: OpenAI, Azure, Google AI):**
- Warning (80%): "You're approaching your monthly limit (80% used)"
- Warning (95%): "Almost at your monthly limit. Consider shorter responses."
- Blocked: "Monthly budget exhausted. Budget resets on [date]. Contact admin for adjustment."

---

## 3. Conversation Mode Indicators

### Table Stakes (Must Have)

| Feature | Why Expected | Current State | Notes |
|---------|--------------|---------------|-------|
| Mode selection before first message | Users must choose context for AI | Implemented: ModeSelector chips | Disappears after selection |
| Mode labels | Users must identify AI features | Partially implemented | Mode selector has descriptions |
| Visible "AI-powered" indicator | Users know they're talking to AI | NOT implemented | **GAP** |
| Current mode display after selection | Users should see what mode is active | NOT implemented | **GAP - Important** |

**Industry Standard:** Clear visual identification of AI features, mode indicators visible throughout conversation, typing/thinking states. Source: [PatternFly - Conversation Design](https://www.patternfly.org/patternfly-ai/conversation-design/)

### Differentiators (Nice to Have)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Persistent mode badge in conversation header | Always know which mode is active | Low | Chip showing "Meeting Mode" or "Document Refinement" |
| Mode-specific visual theming | Visual differentiation by mode | Medium | Different accent colors per mode |
| Mode switching mid-conversation | Flexibility for evolving needs | High | Complex, may confuse AI context |
| Mode descriptions on hover | Quick reference without leaving screen | Low | Tooltip on mode badge |
| "New conversation in different mode" shortcut | Easy mode switching | Low | Button to start fresh with different mode |

### Anti-Features (Do NOT Build)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Mode disappears after selection | User forgets context, confusion | Show persistent indicator |
| Too many modes | Decision paralysis, complexity | Keep to 2-3 primary modes |
| Automatic mode detection | AI may guess wrong, confusing | Let user explicitly choose |
| Mode change mid-stream | Disrupts AI context, unexpected behavior | Start new conversation for new mode |
| Hidden mode information | User doesn't understand AI behavior differences | Clear descriptions and visual indicators |

**Recommended Implementation:**
1. After mode selection, show badge in conversation header: `[Meeting Mode]` or `[Document Refinement]`
2. Badge should be subtle but always visible
3. Optional: Different accent color per mode (e.g., blue for Meeting, green for Document)

---

## 4. Artifact Generation UI Patterns

### Table Stakes (Must Have)

| Feature | Why Expected | Current State | Notes |
|---------|--------------|---------------|-------|
| Streaming display of generated content | Users see progress in real-time | Implemented: StreamingMessage | Text streaming works |
| Copy to clipboard | Export generated content | NOT explicitly implemented for artifacts | **GAP** |
| Clear content boundaries | Distinguish generated content from chat | NOT implemented | **GAP** |
| Error state for generation failure | Users know if generation failed | Implemented: ErrorEvent handling | Basic error shown |

**Industry Standard:** Split-pane UI with chat on left, artifact preview on right. Real-time streaming with visual indicators. Source: [Anthropic Claude Artifacts](https://support.claude.com/en/articles/11649427-use-artifacts-to-visualize-and-create-ai-apps-without-ever-writing-a-line-of-code), [LibreChat Artifacts](https://www.librechat.ai/docs/features/artifacts)

### Differentiators (Nice to Have)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dedicated artifact panel (split view) | Clear separation of chat vs output | High | Major UI change |
| Syntax highlighting for code | Better readability for technical content | Medium | Markdown code block rendering |
| Download as file | Export artifacts directly | Low | Download button for generated content |
| Version history | Track iterations on an artifact | High | Complex state management |
| Edit-in-place | Refine without new message | Medium | Inline editing of generated content |
| Artifact type detection | Auto-format based on content | Medium | Detect code, markdown, diagrams |

### Anti-Features (Do NOT Build)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Auto-execute generated code | Security risk | Always require explicit user action |
| Replace chat with artifact view | Loses conversation context | Split view or modal, not replacement |
| No way to copy/export | Trapped content, frustrating | Always provide copy/download options |
| Complex artifact management | Scope creep, BA assistant focus | Keep simple: display, copy, download |
| Automatic file creation | Unexpected side effects | User must explicitly save/export |

**Recommended Implementation for BA Assistant:**
Given the app's focus (business analysts, not developers), a lightweight approach is recommended:
1. Render artifacts in expandable blocks within the chat
2. Add "Copy" and "Download as .txt/.md" buttons
3. Optional: Syntax highlighting for any code blocks
4. Defer complex split-pane UI to future version

---

## 5. Source Attribution in AI Responses

### Table Stakes (Must Have)

| Feature | Why Expected | Current State | Notes |
|---------|--------------|---------------|-------|
| List of documents used | Users need to know what informed the response | NOT implemented | **GAP - Critical for RAG app** |
| Link to source documents | Verify and explore sources | NOT implemented | **GAP** |
| Clear attribution placement | Not buried or hidden | NOT implemented | **GAP** |

**Industry Standard:** Inline citations with clickable links, hover previews for quick verification, explicit "no sources found" when applicable. Source: [Shape of AI - Citations](https://www.shapeof.ai/patterns/citations)

### Differentiators (Nice to Have)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Inline citations with document names | Know exactly which claim comes from where | High | Requires backend changes |
| Hover preview of source passage | Quick verification without navigation | Medium | Tooltip showing relevant excerpt |
| Source confidence indicators | Understand reliability of attribution | Medium | "3 sources support this" |
| "View in document" jump link | Go directly to relevant passage | Medium | Deep linking within documents |
| Source filtering | "Only use these documents" | Medium | Pre-select which docs to consult |
| Explicit "no sources" indicator | Transparency when AI doesn't use documents | Low | "This response is from general knowledge" |

### Anti-Features (Do NOT Build)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Hidden sources | Users can't verify, reduces trust | Always show what documents were consulted |
| Fabricated citations | Destroys trust if discovered | Verify all citations exist before displaying |
| Sources only on demand | Too much friction to check | Show sources inline or immediately below response |
| Overwhelming citation detail | Clutters the response | Collapsible or summary format |
| Citation without verification | May cite wrong document | Backend must verify document exists and was actually used |

**Recommended Implementation:**

```
AI Response text here...

---
Sources:
- [Document Name 1] (3 passages)
- [Document Name 2] (1 passage)
```

Or expandable format:
```
AI Response text here... [Show Sources v]
```

**Critical Warning from Research:**
"Citation presence is not the same as citation correctness." Source: [Emergent Mind - Citation Behavior](https://www.emergentmind.com/topics/ai-answer-engine-citation-behavior)

Always verify citations are accurate - a fabricated citation is worse than no citation.

---

## 6. File Size Validation UX

### Table Stakes (Must Have)

| Feature | Why Expected | Current State | Notes |
|---------|--------------|---------------|-------|
| File size limit displayed | Users know constraints before uploading | Implemented: "Maximum file size: 1MB" text | Good |
| File type restrictions clear | Users know what's accepted | Implemented: ".txt and .md files supported" | Good |
| Error message on violation | Users know why upload failed | Partially: Generic error shown | **Could be more specific** |
| Real-time validation | Don't wait for server to reject | NOT implemented | **GAP** |

**Industry Standard:** Client-side validation before upload, specific error messages explaining the violation, easy recovery path. Source: [Uploadcare - File Uploader UX](https://uploadcare.com/blog/file-uploader-ux-best-practices/), [UX Patterns Dev - File Input](https://uxpatterns.dev/patterns/forms/file-input)

### Differentiators (Nice to Have)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| File size shown before upload | User sees what they selected | Low | "selected-file.txt (450 KB)" |
| Progress with percentage | Clear upload status | Implemented | Already exists |
| Drag-and-drop support | Easier upload experience | Low | Flutter file_picker may support |
| Multi-file upload | Batch document uploads | Medium | One-by-one currently |
| File preview before upload | Verify correct file selected | Low | Show first few lines |

### Anti-Features (Do NOT Build)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Silent rejection | User thinks upload worked | Clear error with reason |
| Server-only validation | Wastes time and bandwidth | Validate client-side first |
| "Upload failed" without reason | User doesn't know how to fix | "File too large (2.3 MB). Maximum size is 1 MB." |
| No way to recover | User must start over | Keep file selected, show error, let user try different file |
| Hidden size limits | User discovers limits through failure | Show limits prominently before upload |

**Recommended Error Messages:**

| Violation | Current | Recommended |
|-----------|---------|-------------|
| File too large | "Upload failed: [error]" | "File too large (2.3 MB). Maximum allowed is 1 MB." |
| Wrong file type | "Upload failed: [error]" | "Unsupported file type (.pdf). Only .txt and .md files are supported." |
| Empty file | "Upload failed: [error]" | "File is empty. Please select a file with content." |
| Network error | "Upload failed: [error]" | "Upload interrupted. Check your connection and try again." |

**Recommended Implementation:**
1. Validate file size client-side immediately after selection
2. Show file details: name, size, type
3. If validation fails, show specific error and keep upload UI ready for another selection
4. If validation passes, proceed with upload showing progress

---

## Summary: Priority Matrix

### Critical Gaps (Address in v1.9.2)

| Feature | Area | Impact | Complexity |
|---------|------|--------|------------|
| Source attribution display | RAG Citations | High - Core value proposition | Medium |
| Budget exhaustion blocked state | Token/Budget | High - Prevents surprise failures | Low |
| Preserve partial response on error | Streaming | Medium - Better error recovery | Low |
| Client-side file size validation | Upload | Medium - Better UX | Low |
| Persistent mode indicator | Conversation | Medium - Context clarity | Low |

### Good-to-Have (Post v1.9.2)

| Feature | Area | Impact | Complexity |
|---------|------|--------|------------|
| Persistent budget indicator in conversation | Token/Budget | Medium | Low |
| Connection health indicator | Streaming | Low | Low |
| Artifact copy/download buttons | Artifacts | Medium | Low |
| File preview before upload | Upload | Low | Low |
| Hover preview for sources | RAG Citations | Medium | Medium |

### Future Considerations

| Feature | Area | Impact | Complexity |
|---------|------|--------|------------|
| Split-pane artifact view | Artifacts | High | High |
| Auto-reconnection with replay | Streaming | High | High |
| Inline citations with highlighting | RAG Citations | High | High |
| Multi-device sync | Streaming | Medium | High |

---

## Sources

### Network Interruption Handling
- [Ably Blog - AI UX: Reliable, Resumable Token Streaming](https://ably.com/blog/token-streaming-for-ai-ux) - HIGH confidence
- [AI SDK - useChat Reference](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat) - HIGH confidence
- [Parallel HQ - UX for AI Chatbots 2025](https://www.parallelhq.com/blog/ux-ai-chatbots) - MEDIUM confidence

### Token/Budget UX
- [Skywork - Best Practices for AI API Cost & Throughput Management 2025](https://skywork.ai/blog/ai-api-cost-throughput-pricing-token-math-budgets-2025/) - HIGH confidence
- [TrueFoundry - Rate Limiting in AI Gateway](https://www.truefoundry.com/blog/rate-limiting-in-llm-gateway) - MEDIUM confidence
- [Medium - Token & Latency Budgets for Real-Time AI UX](https://medium.com/coinmonks/token-latency-budgets-for-real-time-ai-ux-dac56901eaa7) - MEDIUM confidence

### Conversation Mode Indicators
- [PatternFly - Conversation Design](https://www.patternfly.org/patternfly-ai/conversation-design/) - HIGH confidence
- [MultitaskAI - Chat UI Design Trends 2025](https://multitaskai.com/blog/chat-ui-design/) - MEDIUM confidence
- [Shape of AI - UX Patterns](https://www.shapeof.ai/) - HIGH confidence

### Artifact Generation
- [Anthropic - Claude Artifacts](https://support.claude.com/en/articles/11649427-use-artifacts-to-visualize-and-create-ai-apps-without-ever-writing-a-line-of-code) - HIGH confidence
- [LibreChat - Artifacts Documentation](https://www.librechat.ai/docs/features/artifacts) - HIGH confidence
- [LogRocket - Implementing Claude's Artifacts Feature](https://blog.logrocket.com/implementing-claudes-artifacts-feature-ui-visualization/) - MEDIUM confidence

### Source Attribution
- [Shape of AI - Citations Pattern](https://www.shapeof.ai/patterns/citations) - HIGH confidence
- [Emergent Mind - Citation Behavior in AI Answer Engines](https://www.emergentmind.com/topics/ai-answer-engine-citation-behavior) - MEDIUM confidence
- [Arxiv - Attribution Gradients](https://arxiv.org/html/2510.00361v1) - HIGH confidence

### File Upload UX
- [Uploadcare - File Uploader UX Best Practices](https://uploadcare.com/blog/file-uploader-ux-best-practices/) - HIGH confidence
- [UX Patterns Dev - File Input Pattern](https://uxpatterns.dev/patterns/forms/file-input) - HIGH confidence
- [Vista Design - File Upload Pattern](https://vista.design/swan/patterns/file-upload/) - MEDIUM confidence
