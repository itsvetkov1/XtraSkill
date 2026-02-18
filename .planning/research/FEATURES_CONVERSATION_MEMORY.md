# Feature Landscape: Conversation Memory

**Domain:** Multi-turn AI conversation systems
**Researched:** 2026-02-18
**Confidence:** HIGH (based on official Anthropic docs, current research, and existing tools analysis)

## Table Stakes

Features users expect from conversation systems. Missing = product feels broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Full conversation history sent to LLM | Without this, AI can't reference prior turns | Low | **Critical**: This is the bug to fix. Anthropic Messages API requires full history in `messages` array |
| Immediate recall (within session) | AI must remember what was said 3 messages ago | Low | Natural consequence of sending full history |
| Role alternation (user/assistant) | Claude API requirement and conversation structure | Low | Already implemented in models; verify formatting |
| Multi-turn context preservation | Conversation should flow naturally across 10+ turns | Low | Database stores messages; need to pass all to LLM |
| Token-aware truncation | Prevent API errors when conversation exceeds context window | Medium | Already implemented (`build_conversation_context` with 150K token limit) |

## Differentiators

Features that set products apart. Not expected by default, but create competitive advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Artifact pair filtering | Hide "generate BRD" request pairs after artifact created | Medium | **Already implemented** via `_identify_fulfilled_pairs()` - improves context clarity |
| Sliding window for long conversations | Keep recent turns + summary of old ones | Medium | **Partially implemented** - truncates to recent 80% budget, adds summary note |
| Knowledge retention metrics | Track if AI re-asks for already-provided info | Medium | For testing/QA, not user-facing feature |
| Conversation restart suggestions | Detect when context is too polluted, suggest starting fresh | Low-Medium | Cursor's pattern: restart after feature completion |
| Context compaction API | Compress old history as session approaches limits | High | Anthropic beta feature (2026), not needed for current scale |

## Anti-Features

Features to explicitly NOT build for this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Complex summarization strategies | Over-engineering for current use case (BA sessions are focused, not infinite) | Use simple truncation with summary note (already implemented) |
| Multiple conversation branches | BA discovery is linear; branching adds UI/UX complexity | Keep single linear history per thread |
| Conversation search/indexing | Not needed for typical BA session length (10-30 turns) | Rely on database queries for thread history |
| Memory across threads | Each BA session is independent context | Thread isolation is correct behavior |
| User-editable history | Editing past messages complicates truth and storage | Messages are immutable once sent |

## Feature Dependencies

```
Full conversation history → Multi-turn context preservation
    ↓
Token-aware truncation (prevents API errors at scale)
    ↓
Sliding window (subset of truncation)

Artifact pair filtering (optional enhancement)
```

## Current Implementation Analysis

Based on code review (`agent_service.py` line 103-120, `conversation_service.py`):

### ✅ **What Works**
- Database correctly stores all messages (`save_message`)
- `build_conversation_context()` loads full history
- Token estimation and truncation implemented
- Artifact pair filtering reduces noise
- Role formatting follows Claude pattern

### ❌ **The Bug**
**Location:** `agent_service.py` lines 103-120

```python
# Build the prompt from messages
# Convert message history to single prompt for SDK
prompt_parts = []
for msg in messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if isinstance(content, str):
        prompt_parts.append(f"[{role.upper()}]: {content}")
    # ... (tool result handling)

full_prompt = "\n\n".join(prompt_parts)
```

**Problem:** Claude Code CLI (`query()` function with `-p` flag) receives:
```
[USER]: message 1
[ASSISTANT]: response 1
[USER]: message 2
```

**But the CLI subprocess doesn't maintain conversation state.** Each call to `query()` is independent. The formatted prompt is passed via `-p`, but **Claude Code CLI doesn't parse `[USER]:` / `[ASSISTANT]:` blocks as structured conversation history** — it treats them as a single user prompt with inline conversation text.

### 🔧 **The Fix**

**Option 1: Use Anthropic Messages API directly** (RECOMMENDED)
- Replace Claude Code CLI subprocess with direct Anthropic SDK
- Pass `messages` array with proper `{"role": "user", "content": "..."}` format
- This is what the API expects per official documentation
- Complexity: Medium (need to replace agent call, handle streaming)

**Option 2: Modify prompt formatting for CLI**
- Investigate if Claude Code CLI has a conversation history flag (unlikely)
- If not, keep current format but document as limitation
- Complexity: Low (just document), but doesn't solve problem

**Option 3: Build conversation context into system prompt**
- Move conversation history into system prompt as reference context
- Only pass current message as prompt
- Complexity: Low, but less clean than proper message format

**Recommendation:** Option 1 (direct API) aligns with table stakes expectations and official patterns.

## Expected Behaviors

### Immediate Recall (1-3 turns back)
**Test case:**
```
User: "My project is called SkillHub"
Assistant: "Great! What features does SkillHub need?"
User: "Show me a BRD for it"
```
**Expected:** Assistant remembers "SkillHub" and uses it in BRD title.

### Long-term Context (10+ turns)
**Test case:**
```
Turn 1-5: User describes authentication requirements
Turn 10: "What authentication did we discuss?"
```
**Expected:** Assistant recalls specific auth details from turns 1-5.

### Reference Resolution
**Test case:**
```
User: "I need user login, password reset, and 2FA"
Assistant: "Let's start with login. What auth provider?"
User: "Use the second one you mentioned"
```
**Expected:** Assistant knows "second one" = "password reset".

### Edge Cases

| Scenario | Expected Behavior | Current Status |
|----------|-------------------|----------------|
| Single turn conversation | Works normally | ✅ Works (no history needed) |
| Extremely long messages | Truncate gracefully with summary note | ✅ Implemented |
| Conversation exceeds 150K tokens | Keep recent 80% + summary | ✅ Implemented |
| Rapid successive messages | Maintain order, no race conditions | ⚠️ Needs verification |
| Assistant message with tool calls | Preserve tool execution in history | ✅ Handled via role format |
| Malformed history (consecutive user roles) | API rejects or auto-merges | ⚠️ Needs verification |

## Testing Patterns for Regression Coverage

Based on research from [Confident AI](https://www.confident-ai.com/blog/llm-chatbot-evaluation-explained-top-chatbot-evaluation-metrics-and-testing-techniques) and [arXiv conversation regression testing](https://ar5iv.labs.arxiv.org/html/2302.03154):

### Test Category 1: Knowledge Retention
**What it catches:** Memory loss between turns

```
TC-MEM-01: Name Retention (3 turns)
  Pre: Thread is empty
  1. User: "My name is John and I'm building a CRM"
  2. Assistant: [responds]
  3. User: "What was my name?"
  Expected: Assistant says "John"

TC-MEM-02: Multi-fact Retention (10 turns)
  Pre: Thread is empty
  1. User provides: project name, tech stack, target users
  5. User asks unrelated questions
  10. User: "What tech stack did I mention?"
  Expected: Assistant recalls the exact stack
```

**Scoring:** `turns_with_correct_recall ÷ total_test_turns`

### Test Category 2: Conversation Relevancy
**What it catches:** Off-topic responses due to context loss

```
TC-REL-01: Topic Continuity
  Pre: 5-turn conversation about authentication
  6. User: "What about the password requirements?"
  Expected: Response relates to auth context, not generic password advice

TC-REL-02: Pronoun Resolution
  Pre: Discussed three features (A, B, C)
  User: "Let's focus on the second one"
  Expected: Assistant knows "second one" = feature B
```

### Test Category 3: Role Adherence
**What it catches:** Persona drift across turns

```
TC-ROLE-01: Maintains BA Voice
  Pre: 10-turn BA discovery conversation
  11. User: "How should I implement this?"
  Expected: Assistant redirects to business focus, doesn't provide code

TC-ROLE-02: Consistent Questioning Style
  Pre: BA asking one question at a time
  User provides multi-part answer
  Expected: Assistant still asks one follow-up, not multiple
```

### Test Category 4: Conversation Completeness
**What it catches:** Unfulfilled user intentions

```
TC-COMP-01: Request Tracking
  Pre: User asks for BRD generation
  Expected: Artifact created OR explicit "need more info" response

TC-COMP-02: Follow-through on Promises
  Pre: "I'll generate that after you answer..."
  User provides answer
  Expected: Assistant actually generates promised artifact
```

### Edge Case Tests

```
TC-EDGE-01: Truncation Behavior
  Pre: Conversation at 140K tokens (near limit)
  User: Sends 5K token message
  Expected: Summary note appears, recent context preserved

TC-EDGE-02: Rapid Fire Messages
  1. Send message A
  2. Immediately send message B (before A response complete)
  Expected: B waits for A completion OR clear error

TC-EDGE-03: Empty Message Handling
  User: Sends whitespace-only message
  Expected: Validation error (min_length=1 in ChatRequest)

TC-EDGE-04: Very Long Single Message
  User: Sends 30K character message (near limit)
  Expected: Accepted, truncation only if context exceeded

TC-EDGE-05: Tool Call in History
  Pre: Previous turn used search_documents tool
  User: "What documents did you find?"
  Expected: Assistant recalls search results
```

## How Existing Tools Handle Context

### Cursor IDE
**Source:** [Cursor Context Management Course](https://stevekinney.com/courses/ai-development/cursor-context)

**Strategies:**
- **Partial file reading:** Agent reads first 250 lines, extends by 250 if needed
- **Search result caps:** Maximum 100 lines
- **Restart after milestones:** "Restart conversations after completing a feature or fixing a bug"
- **Documentation as context:** `README.md` helps re-establish context quickly

**Best practice:** Keep conversations "short and focused" to avoid context pollution.

### Aider (CLI Tool)
**Source:** [Best AI Coding Agents 2026](https://www.faros.ai/blog/best-ai-coding-agents-2026)

**Strategies:**
- Git-native: Diffs and commits as conversation markers
- Works with multiple models (not locked to one provider)
- CLI-based conversation state (persists across commands)

**Implication:** For CLI tools, conversation state must be explicitly managed (not automatic like web UI).

### Claude Code CLI
**Current project usage:** `query(prompt=full_prompt, options=...)` via subprocess

**Limitation discovered:** Treats formatted conversation as single prompt, not structured turns. This is why memory fails.

## Formatting Best Practices

### Anthropic Official Format (Messages API)
**Source:** [Anthropic Messages API Docs](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)

```python
messages = [
    {"role": "user", "content": "Hello, Claude"},
    {"role": "assistant", "content": "Hello!"},
    {"role": "user", "content": "Can you describe LLMs to me?"}
]
```

**Rules:**
- Must alternate `user` ↔ `assistant` (consecutive same roles auto-merge)
- Max 100,000 messages per request
- System prompts use separate `system` parameter (not a role in messages)
- Prefill deprecated on Claude 4.6/4.5 models (use structured outputs instead)

### Current BA Flow Format
```python
# In agent_service.py (lines 104-119)
prompt_parts.append(f"[{role.upper()}]: {content}")
full_prompt = "\n\n".join(prompt_parts)
```

**Problem:** This creates:
```
[USER]: message 1

[ASSISTANT]: response 1

[USER]: message 2
```

**This is NOT the Messages API format.** It's a single string prompt that *describes* a conversation, not structured conversation history.

### Recommended Fix
Replace subprocess call with direct Anthropic SDK:

```python
import anthropic

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# Pass structured messages array
response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=4096,
    system=self.skill_prompt,  # BA skill instructions
    messages=messages  # Already in correct format from build_conversation_context()
)
```

## Complexity Analysis

| Fix Approach | Effort | Risk | Benefits |
|--------------|--------|------|----------|
| Direct Anthropic API | Medium | Low | Proper conversation memory, official format, easier debugging |
| Keep CLI + hack format | Low | Medium | Quick but doesn't solve root cause |
| Hybrid (API for Assistant, CLI for BA) | High | Medium | Over-engineering |

**Recommendation:** Direct API (Medium effort, High value). This aligns with table stakes, fixes the bug properly, and uses official supported patterns.

## MVP Recommendation

**For memory bug fix milestone:**

1. ✅ **Replace Claude Code CLI with direct Anthropic Messages API** (table stakes)
   - Fixes conversation memory completely
   - Uses official supported format
   - Easier to test and debug

2. ✅ **Keep existing token-aware truncation** (already works)
   - 150K token limit with 80% budget
   - Summary note for truncated history

3. ✅ **Keep artifact pair filtering** (differentiator already implemented)
   - Reduces context noise
   - Improves readability

4. ✅ **Add regression tests** (quality gate)
   - Knowledge retention (TC-MEM-01, TC-MEM-02)
   - Conversation relevancy (TC-REL-01, TC-REL-02)
   - Edge cases (TC-EDGE-01 through TC-EDGE-05)

**Defer:**
- ❌ Context compaction API (beta feature, not needed yet)
- ❌ Conversation branching (unnecessary complexity)
- ❌ Advanced summarization (current truncation is sufficient)

## Sources

**HIGH Confidence (Official Documentation):**
- [Anthropic Messages API - Working with Messages](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)
- [Anthropic Messages API Reference](https://docs.claude.com/en/api/messages)
- [AWS Bedrock - Claude Messages API](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html)

**MEDIUM Confidence (Current Research & Tools):**
- [LLM Development in 2026: Hierarchical Memory](https://medium.com/@vforqa/llm-development-in-2026-transforming-ai-with-hierarchical-memory-for-deep-context-understanding-32605950fa47)
- [DataCamp - How LLM Memory Works](https://www.datacamp.com/blog/how-does-llm-memory-work)
- [Cursor Context Management Course](https://stevekinney.com/courses/ai-development/cursor-context)
- [Best AI Coding Agents 2026 - Faros AI](https://www.faros.ai/blog/best-ai-coding-agents-2026)

**MEDIUM Confidence (Testing Patterns):**
- [Confident AI - LLM Chatbot Evaluation](https://www.confident-ai.com/blog/llm-chatbot-evaluation-explained-top-chatbot-evaluation-metrics-and-testing-techniques)
- [arXiv - Conversation Regression Testing](https://ar5iv.labs.arxiv.org/html/2302.03154)
- [Chatbot Testing Guide - Cekura AI](https://www.cekura.ai/blogs/complete-chatbot-testing-guide-ai-agents)

**LOW Confidence (Training Data, 2025 knowledge):**
- General LLM conversation patterns (may be superseded by 2026 developments)
