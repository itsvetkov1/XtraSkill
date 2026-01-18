# Domain Pitfalls

**Domain:** AI-powered conversational assistant for business analysts
**Researched:** 2026-01-17
**Confidence:** MEDIUM (based on training knowledge of AI assistants, conversational platforms, BA tools, Flutter development patterns)

## Critical Pitfalls

Mistakes that cause rewrites, user abandonment, or major technical issues.

### Pitfall 1: Uncontrolled AI Token Costs
**What goes wrong:** Token usage spirals out of control, making the product financially unsustainable. Common causes:
- Sending entire conversation history on every request
- Including all document context regardless of relevance
- Not implementing token limits or budget controls
- Agent SDK overhead (multiple model calls per user interaction)

**Why it happens:**
- Initial prototype works fine with small conversations
- No monitoring until first expensive bill arrives
- Agent SDK abstraction hides token multiplication (one user message → many API calls)
- Document context grows unbounded

**Consequences:**
- $500-2000+ monthly costs before revenue
- Need to rewrite context management
- Emergency feature freezes to control costs
- User limits that hurt growth

**Prevention:**
- **Implement token budgets BEFORE launch:** Max tokens per request (8K), per conversation (50K), per user per day (200K)
- **Monitor from day one:** Track tokens-per-request, cost-per-user, daily burn rate
- **Smart context windowing:** Only send last N messages + relevant docs (not entire history)
- **Agent SDK mitigation:** Cache system prompts, use prompt caching (Claude 70% discount), limit tool calls per request
- **SQLite cost tracking:** Log token usage per request in `conversation_analytics` table

**Detection:**
- Average tokens per request > 5000 (red flag)
- Cost per user per month > $5 (unsustainable at scale)
- 90th percentile request cost > $0.15
- Month-over-month token growth > 50%

**Phase mapping:** Phase 1 (Foundation) must include token tracking. Phase 2 (Intelligence) must include context optimization before document features ship.

---

### Pitfall 2: Shallow Document Context (The "Useless RAG" Problem)
**What goes wrong:** Document context feature ships but doesn't actually help users. AI responses reference documents superficially ("As mentioned in your document...") without deep understanding.

**Why it happens:**
- Treating documents as pure text without structure
- No semantic chunking (splitting on character count, not meaning)
- Poor embedding quality (generic embeddings, not domain-tuned)
- Returning too many irrelevant chunks (20 chunks → AI confused)
- No metadata enrichment (document type, section headers, creation date)

**Consequences:**
- Users upload docs, see no value, abandon feature
- "It's just keyword search, not intelligence"
- BA artifacts lack document insights
- Competitive disadvantage vs tools with good context

**Prevention:**
- **Semantic chunking:** Split on document structure (sections, paragraphs), not character limits
- **Quality embeddings:** Use Claude embeddings or domain-specific models, not generic word2vec
- **Relevance filtering:** Return top 3-5 chunks (not 20), with confidence scores
- **Metadata enrichment:** Track document type (requirements doc, process map, stakeholder list), creation date, author
- **Structured extraction:** For BA documents, extract entities (stakeholders, requirements, processes) at upload
- **Hybrid search:** Combine semantic search with keyword matching for precision

**Detection:**
- Users upload docs but don't ask doc-related questions
- "Document uploaded" feature usage high, but "documents cited in responses" low
- User feedback: "It doesn't understand my documents"
- Low engagement time after doc upload spike

**Phase mapping:** Phase 2 (Intelligence) must include semantic chunking and metadata before document search ships. Phase 3 can add advanced features like structured extraction.

---

### Pitfall 3: Cross-Platform UI/UX Inconsistency
**What goes wrong:** Flutter app behaves differently on web vs mobile. Desktop users expect keyboard shortcuts, mobile users expect gestures. Web users confused by mobile-first navigation.

**Why it happens:**
- Designing for one platform first (usually mobile)
- Not testing on target platforms until late
- Flutter's "write once, run everywhere" promise creates false confidence
- Platform-specific patterns ignored (back button on Android, swipe on iOS, mouse hover on web)

**Consequences:**
- Web users complain about poor desktop experience
- Mobile users encounter broken gestures
- Platform-specific bugs discovered post-launch
- Rewrite UI components per platform

**Prevention:**
- **Responsive design from day one:** Test on phone, tablet, desktop simultaneously
- **Platform-aware widgets:** Use Flutter's `Platform.isAndroid/isIOS/isWeb` for conditional UI
- **Adaptive navigation:** Drawer on mobile, sidebar on web/tablet
- **Input method awareness:** Keyboard shortcuts on desktop, touch gestures on mobile
- **Test matrix:** Every PR tested on Chrome (web), Android emulator, iOS simulator minimum
- **Design system:** Material 3 base with platform adaptations (Cupertino widgets on iOS for native feel)

**Detection:**
- User agent distribution doesn't match usage patterns (80% web users, but only 20% active)
- Platform-specific bug reports spike
- High bounce rate on one platform
- User feedback: "Works great on mobile, terrible on web" (or vice versa)

**Phase mapping:** Phase 1 (Foundation) must establish responsive design patterns. Each subsequent phase tests on all platforms before completion.

---

### Pitfall 4: Conversation State Explosion (The "Lost Context" Problem)
**What goes wrong:** As conversations grow (50+ messages), the AI:
- Forgets earlier context despite having conversation history
- Contradicts previous statements
- Repeats questions already answered
- Loses track of artifacts in progress

**Why it happens:**
- Sending raw conversation history without summarization
- No explicit state tracking (what's been decided, what artifacts exist)
- Context window limits hit (even 200K tokens have practical limits)
- Agent SDK doesn't maintain cross-request memory

**Consequences:**
- Users frustrated by repetitive AI
- "It doesn't remember what we discussed"
- Artifacts lack continuity (user tracking diagram references requirements doc that doesn't exist)
- Need conversation "reset" feature (admission of failure)

**Prevention:**
- **Conversation summarization:** Every 10 messages, create rolling summary of key decisions
- **Explicit state tracking:** Store structured state (artifacts created, stakeholders identified, decisions made)
- **Context prioritization:** Recent messages (last 5) + summary + relevant artifacts (not all 50 messages)
- **Artifact registry:** Track all generated artifacts in conversation metadata
- **State hydration:** When loading conversation, inject state summary at start of context
- **Agent SDK prompt engineering:** Include conversation state in system prompt

**Detection:**
- User messages contain "as I mentioned earlier" or "you already asked that"
- Conversation length negatively correlates with user satisfaction
- Users start new threads instead of continuing (workaround for lost context)
- Average messages per conversation plateaus at ~15 (users give up)

**Phase mapping:** Phase 1 (Foundation) includes basic conversation history. Phase 2 (Intelligence) must add summarization before long conversations become common.

---

### Pitfall 5: Authentication/Security Debt
**What goes wrong:** MVP ships with basic auth, but adding OAuth, encryption, or compliance features later requires database migrations, schema changes, and breaking changes.

**Why it happens:**
- "We'll add proper auth later"
- Starting with API keys or simple passwords
- Not planning for encryption at rest
- SQLite chosen without considering multi-user isolation

**Consequences:**
- Major refactor to add OAuth
- Can't encrypt existing documents without migration
- Compliance requirements block enterprise sales
- User data at risk during transition

**Prevention:**
- **OAuth from day one:** Supabase auth with Google/Microsoft providers (BA users expect SSO)
- **Encryption at rest:** SQLite with SQLCipher or Supabase encryption
- **Row-level security:** Even in SQLite, design schema with user_id foreign keys
- **Audit logging:** Track document access, AI interactions for compliance
- **Token security:** Never log full API responses (may contain sensitive data)

**Detection:**
- Enterprise users ask about SOC2/GDPR compliance
- Security audit reveals plaintext document storage
- No way to prove "who accessed what document when"
- Password reset flow doesn't exist

**Phase mapping:** Phase 1 (Foundation) must include production-ready auth (OAuth, encryption). Cannot defer to Phase 3+.

---

### Pitfall 6: Streaming Response Failures (The "Half-Written Message" Problem)
**What goes wrong:** SSE connections drop mid-response. User sees partial AI message, doesn't know if it's complete. Retrying duplicates content.

**Why it happens:**
- No connection error handling
- Network timeouts on mobile (switching WiFi to cellular)
- Long responses exceed default timeouts
- No resume/retry mechanism
- Assuming streaming always succeeds

**Consequences:**
- Users see incomplete artifacts (half a user story)
- No indication of failure vs completion
- Retry sends entire prompt again (double token cost)
- Mobile users suffer most (unstable connections)

**Prevention:**
- **Connection heartbeat:** Send keepalive events every 15 seconds
- **Chunk boundaries:** Mark semantic boundaries (JSON objects, paragraphs) so partial content is useful
- **Completion markers:** Explicit `[DONE]` event at end
- **Graceful degradation:** If streaming fails, fall back to polling or complete response
- **Client-side buffering:** Store partial response, resume from last complete chunk
- **Timeout configuration:** 120+ second timeout for long artifact generation
- **Network awareness:** Detect connection type (Flutter's connectivity_plus), warn on cellular for large operations

**Detection:**
- User reports of "stuck" messages
- Analytics: streaming_started events without streaming_completed
- High retry rate (> 10% of requests)
- Platform-specific failure patterns (iOS > Android > web)

**Phase mapping:** Phase 1 (Foundation) must handle basic streaming errors. Phase 2 adds resume/retry for long artifacts.

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or suboptimal UX.

### Pitfall 7: Generic AI Responses (Chatbot, Not Assistant)
**What goes wrong:** AI responses are generic, not BA-specific. "Have you considered stakeholder needs?" instead of "Based on your process map, have you identified approval authorities for each decision point?"

**Why it happens:**
- Generic system prompt (not domain-tuned)
- Not using document context effectively
- Agent SDK with generic tools (not BA-specific)
- No examples in prompt (few-shot learning)

**Prevention:**
- **BA-specific system prompt:** Include BA terminology, artifact templates, analysis frameworks
- **Few-shot examples:** Show example BA conversations → high-quality outputs
- **Structured prompts:** Use XML tags for context sections (<documents>, <conversation_state>, <current_artifact>)
- **Domain tools:** Agent SDK tools like `create_user_story`, `analyze_stakeholders` (not generic `search` or `summarize`)

**Detection:**
- User feedback: "It's just like ChatGPT"
- Low artifact quality ratings
- Users copy AI output to other tools for refinement
- Competitor comparison shows weaker BA insights

**Phase mapping:** Phase 2 (Intelligence) focuses on BA-specific prompt engineering. Must happen before public launch.

---

### Pitfall 8: No Offline Capability
**What goes wrong:** Mobile users in meetings (elevator, basement conference rooms) can't access documents or conversation history.

**Why it happens:**
- Assuming always-online
- Supabase requires network connection
- No local caching strategy
- Real-time sync dependency

**Prevention:**
- **Local-first architecture:** SQLite as source of truth, sync to Supabase
- **Offline document access:** Cache uploaded documents locally
- **Read-only offline mode:** Can view conversations/documents, queue AI requests
- **Sync queue:** Store outbound requests, send when online
- **Flutter offline packages:** drift (offline SQLite ORM), connectivity_plus (network detection)

**Detection:**
- Mobile usage drops during business hours (meeting times)
- User feedback: "Can't use in meetings"
- Network error rate > 5% on mobile
- iOS offline usage analytics (if implemented)

**Phase mapping:** Phase 3 (Cross-platform Polish) adds offline-first features. Not critical for MVP.

---

### Pitfall 9: Poor Artifact Export/Formatting
**What goes wrong:** Generated artifacts look unprofessional when exported. Markdown renders poorly in Word/Confluence. No templates for enterprise BA tools.

**Why it happens:**
- Focusing on AI generation, not output formatting
- Markdown-first without considering target platforms
- No export testing with real BA tools (JIRA, Confluence, Azure DevOps)

**Prevention:**
- **Multi-format export:** Markdown, HTML, PDF, docx, JSON
- **Template-based generation:** Use professional templates for user stories, requirements docs
- **Platform-specific formatting:** JIRA-flavored markdown, Confluence macros, ADO work item format
- **Copy-paste optimization:** Rich text clipboard support
- **Preview before export:** Show how artifact will look in target format

**Detection:**
- Users manually reformat AI output
- Low export feature usage
- Feature requests for specific formats
- "Looks great here, terrible in [tool]"

**Phase mapping:** Phase 4 (Artifacts & Export) focused specifically on this. Not critical for MVP.

---

### Pitfall 10: SQLite Scalability Ignored
**What goes wrong:** SQLite chosen for MVP, but no migration plan to PostgreSQL. Schema design assumes single-user, breaking multi-user features later.

**Why it happens:**
- "We'll migrate later" without concrete plan
- SQLite-specific features used (without PostgreSQL equivalents)
- No abstraction layer between app and database

**Prevention:**
- **Postgres-compatible schema:** Avoid SQLite-specific types/features
- **ORM abstraction:** Use drift or sqflite with migration path to PostgreSQL
- **Design for multi-tenant:** user_id on all tables, even in MVP
- **Document migration plan:** Clear criteria for when to migrate (1000 users? 10K documents?)
- **Test with Supabase local:** Develop against Postgres locally, even if using SQLite in prod initially

**Detection:**
- Schema uses SQLite-specific features (loosely-typed columns)
- No foreign key constraints (will break on Postgres)
- Queries use SQLite-specific syntax
- No clear definition of "migrate when X"

**Phase mapping:** Phase 1 schema design must be Postgres-compatible. Migration occurs in Phase 5-6 based on traction.

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

### Pitfall 11: No Loading States/Progress Indicators
**What goes wrong:** User clicks "Generate artifact", sees blank screen for 10 seconds, assumes crash.

**Prevention:**
- Skeleton loaders for loading content
- Progress indicators for AI generation ("Analyzing documents...", "Drafting user stories...", "Finalizing...")
- Streaming shows progress naturally (text appears incrementally)

**Detection:**
- Users click multiple times (thinking first click didn't work)
- Support tickets: "Is it working?"

---

### Pitfall 12: Search Over Multiple Conversations Missing
**What goes wrong:** User asks "What did we decide about the authentication flow?" but it was in a different conversation thread.

**Prevention:**
- Global search across all conversations
- Search within document content
- Filter by date, document, conversation
- Recent documents/conversations shortcuts

**Detection:**
- Users recreate conversations to find information
- "I can't find what we discussed last week"

---

### Pitfall 13: No Keyboard Shortcuts (Desktop Users)
**What goes wrong:** Desktop users forced to use mouse for everything. New conversation, search, send message all require clicking.

**Prevention:**
- Cmd/Ctrl+N: New conversation
- Cmd/Ctrl+K: Search
- Cmd/Ctrl+Enter: Send message
- Cmd/Ctrl+/: Show shortcuts help
- Escape: Close modals

**Detection:**
- Power users complain about slow workflow
- Desktop time-to-complete-task higher than expected

---

## Phase-Specific Warnings

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|---------------|------------|
| Phase 1 | Foundation | Not implementing token tracking from day one | Add analytics table, log tokens per request |
| Phase 1 | Auth | Starting with simple auth, planning to "add OAuth later" | Use Supabase auth with OAuth from start |
| Phase 1 | Streaming | Not handling connection failures | Implement error boundaries, retry logic |
| Phase 2 | Document Context | Shipping text-only without semantic chunking | Implement semantic splitter, metadata extraction |
| Phase 2 | AI Quality | Generic responses, not BA-specific | BA-focused system prompt, few-shot examples |
| Phase 2 | Cost Control | No token limits, costs spiral | Implement per-request, per-conversation, per-user limits |
| Phase 3 | Cross-platform | Mobile-first design breaks desktop UX | Test on all platforms per PR, responsive design |
| Phase 3 | Offline | No offline capability for mobile users | Local-first architecture with sync queue |
| Phase 4 | Artifacts | Poor export formatting for enterprise tools | Multi-format export, template-based generation |
| Phase 5-6 | Scale | SQLite hits limits, no migration path | Postgres-compatible schema from day one |

---

## Assessment of Conscious Trade-offs

### Trade-off 1: SQLite for MVP (migrate to PostgreSQL later)
**Assessment:** REASONABLE with caveats

**Pros:**
- Faster initial development
- No server infrastructure for MVP
- Local-first aligns with offline use case

**Risks:**
- Must design Postgres-compatible schema NOW
- Migration becomes urgent at ~1000 users
- Multi-device sync awkward with SQLite

**Mitigation:**
- Use Postgres-compatible types and constraints
- Test schema against Supabase local Postgres
- Define clear migration trigger (1000 users OR multi-device OR team features)

---

### Trade-off 2: Text-only document upload (no PDF/Word parsing)
**Assessment:** REASONABLE for MVP

**Pros:**
- Avoids parsing complexity (PyPDF2, python-docx dependencies)
- Users can copy-paste from any source
- Faster time-to-market

**Risks:**
- BA users have documents in Word/PDF
- Copy-paste loses formatting, structure
- Competitive disadvantage if competitors support native formats

**Mitigation:**
- Support .txt and .md natively (markdown preserves structure)
- Provide clear instructions: "Copy-paste content or save as .txt"
- Add PDF/Word in Phase 3-4 after validating text-only demand
- Consider server-side parsing (not in Flutter) to avoid binary bloat

---

### Trade-off 3: No deletion/editing in MVP
**Assessment:** RISKY — reconsider for documents

**Pros:**
- Faster MVP development
- Simplifies sync logic
- Immutable audit trail

**Risks:**
- Users WILL upload wrong document
- Typo in conversation needs fixing
- Document contains sensitive info → must delete
- "Can't delete" feels broken to users

**Mitigation:**
- **Conversations:** No edit/delete is OK (users can start new thread)
- **Documents:** MUST support delete (wrong file, sensitive data scenarios)
- **Messages:** No edit is OK, but consider soft delete (mark deleted, hide from UI)
- Add edit/delete in Phase 2-3, not Phase 5+

---

### Trade-off 4: Agent SDK approach (higher token cost for simpler implementation)
**Assessment:** REASONABLE with strict cost controls

**Pros:**
- Faster development (no manual prompt engineering per feature)
- Built-in tool calling, streaming, error handling
- Easier to add new capabilities

**Risks:**
- Token multiplication (one user request → 3-5 API calls)
- Harder to optimize prompts (abstracted by SDK)
- Cost can spiral before noticing

**Mitigation:**
- Implement token budgets BEFORE Phase 1 completion
- Monitor agent calls per user request (alert if > 5)
- Use prompt caching aggressively (70% cost reduction on system prompt)
- Consider hybrid: Agent SDK for complex flows, direct API for simple Q&A
- Budget cap: $200/month in Phase 1-2, $500/month in Phase 3+

---

## Cost Management Strategies

Given solo developer budget constraints and Agent SDK approach:

### 1. Token Budgets (CRITICAL)
```
Per request: 8,000 tokens max
Per conversation: 50,000 tokens max
Per user per day: 200,000 tokens max
Global daily: 500,000 tokens max (Phase 1-2)
```

### 2. Prompt Caching
- Cache system prompt (5,000+ tokens) → 70% cost reduction
- Cache document embeddings → no re-embedding on every request
- Cache conversation summaries → no re-summarizing

### 3. Context Optimization
- Send last 5 messages + summary (not all 50 messages)
- Send top 3 document chunks (not 20)
- Structured context with XML (Claude processes more efficiently)

### 4. Smart Routing
- Simple queries: Direct API call (1 call)
- Complex queries: Agent SDK (3-5 calls)
- Detect intent early to avoid unnecessary agent routing

### 5. Monitoring & Alerts
- Daily cost dashboard
- Alert if daily cost > $20
- Alert if per-request average > $0.10
- Weekly cost trend report

### 6. Free Tier Considerations
- Use Supabase free tier (500MB, 50K rows)
- Use Claude free tier if available (rate limits acceptable for MVP)
- Use Vercel/Netlify free tier for hosting

---

## Sources

**Confidence note:** This research is based on my training knowledge (as of January 2025) of:
- AI assistant development patterns (ChatGPT, Copilot, Cursor architecture)
- Flutter cross-platform development (Material Design docs, Flutter.dev patterns)
- Document context/RAG systems (LangChain patterns, vector DB best practices)
- Claude API specifics (Anthropic docs on prompt caching, token costs, Agent SDK)
- BA tool requirements (JIRA, Confluence, Azure DevOps integration patterns)

**Confidence level: MEDIUM** — Core architectural pitfalls (token costs, cross-platform, streaming) are well-established patterns. BA-specific pitfalls (artifact quality, document context) are inferred from domain knowledge but not verified with current sources.

**Recommended validation:**
- Verify current Claude API pricing and prompt caching discount rates
- Check latest Flutter web/mobile best practices (Material 3 patterns)
- Review recent RAG/document context failure case studies
- Consult BA community for artifact quality expectations

**No web search sources available** — research conducted using training knowledge only.
