# Feature Landscape: Claude Code Agent SDK for Document Generation

**Domain:** Business analysis document generation (BRDs, user stories, acceptance criteria)
**Researched:** 2026-02-13
**Confidence:** HIGH (official docs + Agent SDK documentation)

## Executive Summary

Claude Code Agent SDK provides a structured agent loop architecture that adds **multi-turn reasoning**, **file-based validation**, and **specialized subagent delegation** beyond direct API calls. For document generation, this translates to critique-revise loops, schema validation through file operations, and quality improvement through specialized review subagents.

The key differentiator is not raw capabilities (direct API can also do tool use), but **architectural patterns** that make quality workflows easier to implement: subagents preserve context for independent review, Skills provide progressive content loading without context penalty, and extended thinking enables deeper reasoning at each generation step.

This is NOT a replacement for your existing direct API backend. It's an **additive experiment** to test if agent patterns improve document quality for specific artifact types.

---

## Table Stakes

Features users expect from any AI document generation backend. Missing these = experiment fails.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Streaming responses** | Real-time feedback, same UX as current backend | Low | SDK supports SSE streaming via `query()` generator pattern |
| **Multi-turn conversations** | Contextual refinement of documents | Low | Sessions API maintains conversation history automatically |
| **Tool integration** | Document search, artifact save, source attribution | Medium | Built-in tools (Read, Write, Bash) + custom MCP tools for existing backend integration |
| **Model selection** | User choice of Claude models (Sonnet/Opus/Haiku) | Low | `model` parameter in ClaudeAgentOptions |
| **Error handling** | Graceful degradation when generation fails | Medium | Hooks for PreToolUse/PostToolUse validation, error messages via tool results |
| **Token management** | Prevent runaway costs, respect budgets | Medium | `maxTurns` limit, token counting via usage metrics |
| **Concurrent requests** | Multiple users generating documents simultaneously | Low | Stateless SDK instances, session isolation |

**Implementation notes:**
- Streaming already working in your direct API backend, SDK uses same SSE pattern
- Tool integration means wrapping existing `document_search_tool` and `artifact_generation_tool` as MCP custom tools
- Sessions provide built-in conversation memory (no custom state management needed)

---

## Differentiators

Features that set agent-based generation apart from direct API. Not expected, but provide measurable value.

### 1. Multi-Turn Agent Loops (Critique → Revise)

**What:** Agent generates document, spawns review subagent, incorporates feedback, repeats until quality threshold met

**Value Proposition:** Addresses known quality gap in current single-pass generation (structural inconsistencies, missing sections)

**Complexity:** Medium-High
- Define review subagent with read-only tools and quality criteria prompt
- Implement exit conditions (max iterations, quality score threshold)
- Pass full conversation context to subagent for independent review

**Mechanism:**
```python
# Main agent generates BRD
response = query(
    prompt="Generate BRD for user request",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Task"],
        agents={
            "brd-reviewer": AgentDefinition(
                description="Reviews BRDs for completeness and consistency",
                prompt="Analyze BRD structure, check for missing sections...",
                tools=["Read"]  # Read-only reviewer
            )
        }
    )
)

# Agent automatically delegates to brd-reviewer subagent
# Incorporates feedback and revises
```

**Quality improvement:** Independent review subagent catches issues that generated content misses because it operates in separate context (fresh perspective)

**Dependencies:** Requires defining quality criteria in reviewer subagent prompt

**Sources:**
- [Building agents with critique loops](https://medium.com/flow-specialty/ai-assisted-coding-automating-plan-reviews-with-claude-code-and-codex-for-higher-quality-plans-c7e373a625ca)
- [Subagents documentation](https://code.claude.com/docs/en/sub-agents)

---

### 2. File-Based Validation Workflows

**What:** Write generated document to file, run validation scripts (schema checks, linting, consistency rules), surface errors for agent to fix

**Value Proposition:** Deterministic quality checks (your existing JSON schema validation, business rule enforcement) BEFORE returning to user

**Complexity:** Medium
- Custom MCP tool wraps existing `file_validator.py` logic
- PreToolUse hook runs validation before committing artifact to database
- Agent sees validation errors and self-corrects

**Mechanism:**
```python
# Custom validation tool
@tool("validate_brd", "Validate BRD structure and content", {"file_path": str})
async def validate_brd(args):
    result = subprocess.run(["python", "scripts/validate_brd.py", args["file_path"]])
    if result.returncode != 0:
        return {"content": [{"type": "text", "text": f"Validation failed: {result.stderr}"}]}
    return {"content": [{"type": "text", "text": "Valid BRD structure"}]}

# Agent loop
# 1. Generate BRD -> Write to temp file
# 2. Call validate_brd tool
# 3. If errors, revise and repeat
# 4. If valid, save to database
```

**Quality improvement:** Catches structural errors (missing required fields, invalid JSON, business rule violations) that direct API generation misses

**Dependencies:** Existing `file_validator.py` service logic

**Sources:**
- [Custom Tools documentation](https://platform.claude.com/docs/en/agent-sdk/custom-tools)
- [File-based validation workflows](https://github.com/Pimzino/claude-code-spec-workflow)

---

### 3. Extended Thinking for Document Planning

**What:** Enable extended thinking mode for initial document planning phase (structure, sections, content strategy) before generation

**Value Proposition:** Deeper reasoning about document requirements → better structure → fewer revisions

**Complexity:** Low-Medium
- Add `thinking: {type: "adaptive"}` parameter to initial planning request
- Opus 4.6 automatically determines thinking depth based on complexity
- Thinking blocks show reasoning (useful for debugging quality issues)

**Mechanism:**
```python
# Planning phase with extended thinking
planning_response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},  # Auto-determines thinking depth
    effort="high",  # Prioritize quality over speed
    messages=[{
        "role": "user",
        "content": "Analyze requirements and plan BRD structure for: <user_request>"
    }]
)

# Thinking blocks reveal reasoning about structure decisions
# Then generate document based on plan
```

**Quality improvement:** Structured planning phase reduces need for major revisions (better upfront structure)

**Dependencies:** Opus 4.6 model (Sonnet 4.5 also supports but manual budget tuning)

**Sources:**
- [Extended thinking documentation](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- [Adaptive thinking guide](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)

---

### 4. Progressive Content Loading via Skills

**What:** Package domain-specific templates, examples, and guidelines as Skills that load on-demand (not in initial context)

**Value Proposition:** Reusable document patterns without context penalty, better consistency across generated artifacts

**Complexity:** Medium
- Create `.claude/skills/brd-templates/SKILL.md` with frontmatter + templates
- Skill metadata loads at startup (low token cost)
- Full content loads only when triggered by user request

**Mechanism:**
```markdown
---
name: brd-templates
description: BRD templates and examples. Use when generating Business Requirements Documents.
---

# BRD Generation Guidelines

## Structure Template
1. Executive Summary
2. Business Objectives
3. Stakeholders
4. Requirements
   - Functional requirements
   - Non-functional requirements
5. Acceptance Criteria

## Example BRD
[Full example document...]

## Quality Checklist
- [ ] All sections present
- [ ] Requirements numbered
- [ ] Acceptance criteria measurable
```

**Quality improvement:** Consistent structure across all BRDs (follows template), reduces hallucination (examples guide output)

**Dependencies:** Skill authoring (one-time setup per artifact type)

**Sources:**
- [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Skills in Agent SDK](https://platform.claude.com/docs/en/agent-sdk/skills)

---

### 5. Specialized Document Review Subagents

**What:** Pre-configured subagents for each artifact type (BRD reviewer, user story reviewer, acceptance criteria reviewer) with focused quality prompts

**Value Proposition:** Domain-specific quality checks (not generic review), independent context prevents confirmation bias

**Complexity:** Medium-High
- Define subagent per artifact type with specialized review criteria
- Subagent operates in separate context (fresh perspective)
- Can run multiple reviewers in parallel (structure + content + compliance)

**Mechanism:**
```yaml
# .claude/agents/brd-reviewer.md
---
name: brd-reviewer
description: Reviews BRDs for completeness, consistency, and business value. Use after generating BRDs.
tools: Read, Grep, Glob
model: sonnet
permissionMode: dontAsk
---

You are a senior business analyst reviewing BRD quality.

Review checklist:
1. **Completeness:** All required sections present
2. **Consistency:** Requirements align with objectives
3. **Clarity:** Unambiguous language, no jargon
4. **Traceability:** Each requirement maps to business objective
5. **Testability:** Acceptance criteria measurable

For each issue found:
- Severity: Critical/High/Medium/Low
- Location: Section and line
- Fix: Specific suggestion
```

**Quality improvement:** Specialized reviewers catch domain-specific issues (requirements traceability, acceptance criteria clarity) that general-purpose review misses

**Dependencies:** Domain expertise to define review criteria per artifact type

**Sources:**
- [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Subagents in SDK](https://platform.claude.com/docs/en/agent-sdk/subagents)

---

### 6. Interleaved Thinking with Tool Use

**What:** Agent thinks BETWEEN tool calls (after document search results, after validation errors) to reason about next steps

**Value Proposition:** More sophisticated tool chaining (search → analyze → refine query → search again), better error recovery

**Complexity:** Low (automatic in Opus 4.6 with adaptive thinking)

**Mechanism:**
```
User: "Generate BRD based on these requirements"

Turn 1: [thinking] "Need to search for similar past BRDs..."
        [tool_use: document_search] { "query": "BRD authentication requirements" }
  ↓ tool result: [3 similar BRDs]

Turn 2: [thinking] "These examples show focus on OAuth flows. Should refine search for OAuth-specific patterns..."
        [tool_use: document_search] { "query": "OAuth implementation BRD" }
  ↓ tool result: [2 OAuth BRDs]

Turn 3: [thinking] "Now have enough context. Key patterns: scope definition, token lifecycle, error handling..."
        [text] "Based on similar BRDs, here's the structure..."
```

**Quality improvement:** Better source attribution (agent reasons about search results before generating), more targeted follow-up searches

**Dependencies:** Opus 4.6 for automatic interleaved thinking, or beta header for Opus 4.5/Sonnet 4.5

**Sources:**
- [Interleaved thinking documentation](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#interleaved-thinking)

---

### 7. Background Subagent Processing

**What:** Spawn long-running subagents (compliance check, template population, batch validation) that don't block main conversation

**Value Proposition:** User continues working while background agent handles time-consuming tasks

**Complexity:** Medium
- Define background-compatible subagents (pre-approve tool permissions)
- Handle subagent completion events asynchronously
- Not available for MCP tools (limitation)

**Mechanism:**
```python
# User continues conversation while background agent validates
# Agent automatically runs brd-compliance-checker in background if task is suitable
# When complete, results return to main conversation
```

**Quality improvement:** Enables more thorough validation without blocking user (can run expensive checks like duplicate detection, compliance analysis)

**Dependencies:** Subagent design for background execution (no clarifying questions, pre-approved tools)

**Sources:**
- [Background subagents](https://code.claude.com/docs/en/sub-agents#run-subagents-in-foreground-or-background)

---

## Anti-Features

Features to explicitly NOT build for this experiment.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Nested subagents** | Subagents cannot spawn other subagents (SDK limitation) | Chain subagents sequentially from main conversation: generate → review → compliance → finalize |
| **Custom package installation** | SDK cannot install packages at runtime (security) | Pre-install all dependencies in container, or use pre-built Skills with bundled scripts |
| **Real-time collaboration** | Agent SDK is request-response, not pub/sub | Keep existing WebSocket architecture for real-time updates, use SDK for generation only |
| **Network calls in Skills** | No network access in Skills via API (claude.ai has varying network access) | Use MCP tools for external API calls, Skills for templates/validation only |
| **Force tool use** | Extended thinking incompatible with forced tool use | Let agent autonomously decide when to call tools (better reasoning) |
| **Model fine-tuning** | SDK uses pre-trained models, no fine-tuning support | Achieve customization through Skills, custom system prompts, and few-shot examples |
| **Synchronous blocking** | Agent loops can be slow (extended thinking, multiple tool calls) | Always use async/streaming, set user expectations for quality-first workflows |

**Rationale for anti-features:**
- Work WITH SDK limitations, not against them
- Preserve existing real-time architecture (don't replace what works)
- Focus experiment on quality improvements, not infrastructure rewrite

---

## Feature Dependencies

```
Extended Thinking (Opus 4.6)
  ↓
Multi-Turn Agent Loops
  ↓ requires
Specialized Review Subagents
  ↓ uses
Skills (BRD templates, review criteria)
  ↓ validated by
File-Based Validation Workflows
  ↓ integrated via
Custom MCP Tools (wrap existing backend services)
```

**Critical path:**
1. **Foundation:** Custom MCP tools to integrate existing document_search and artifact_save services
2. **Core loop:** Multi-turn generation with basic review subagent
3. **Quality:** File-based validation + extended thinking for planning
4. **Refinement:** Skills for templates, interleaved thinking for better tool use
5. **Advanced:** Background processing for long-running validations

---

## MVP Recommendation

**Prioritize (Phase 1 - Experiment Core):**
1. **Custom MCP tools** — Wrap existing backend services (document search, artifact save)
2. **Basic review subagent** — Simple BRD reviewer with read-only tools
3. **File-based validation** — Run existing `file_validator.py` on generated documents
4. **Streaming responses** — Maintain current UX (SSE streaming)

**Defer (Phase 2 - Quality Enhancements):**
- **Extended thinking** — Test impact on quality vs latency tradeoff
- **Skills** — Create BRD template Skill (one-time authoring investment)
- **Interleaved thinking** — Requires Opus 4.6 or beta header

**Defer (Future):**
- **Background subagents** — Not critical for MVP, adds complexity
- **Multiple review subagents** — Start with single reviewer, add specialized reviewers based on quality metrics

**Success criteria for experiment:**
- Generated BRDs pass validation at higher rate than direct API (measured via `file_validator.py`)
- User-reported quality issues decrease (track via user stories in `/user_stories/`)
- Latency acceptable for quality-first workflow (< 60s for typical BRD)

---

## Comparison to Direct API Approach

| Capability | Direct API (Current) | Agent SDK (Experiment) | Advantage |
|------------|---------------------|----------------------|-----------|
| **Single-pass generation** | ✅ Fast, predictable | ⚠️ Slower, multi-turn | Direct API for speed |
| **Self-review loops** | ❌ Manual implementation | ✅ Built-in subagent pattern | Agent SDK for quality |
| **File validation** | ⚠️ Post-generation only | ✅ In-loop validation | Agent SDK for correctness |
| **Context management** | ⚠️ Manual session handling | ✅ Automatic session API | Agent SDK for simplicity |
| **Extended thinking** | ⚠️ Requires beta features | ✅ Native support (Opus 4.6) | Agent SDK for planning depth |
| **Real-time streaming** | ✅ SSE via FastAPI | ✅ SSE via SDK generator | Equal |
| **Tool integration** | ✅ Custom implementation | ✅ MCP standard | Equal (MCP more portable) |
| **Multi-provider support** | ✅ Anthropic, Google, DeepSeek | ⚠️ Anthropic only | Direct API for provider diversity |

**When to use each:**

**Direct API (keep for):**
- User stories, acceptance criteria (simpler artifacts, speed matters)
- Multi-provider support (Gemini, DeepSeek backends)
- Exploratory chat (no quality workflow needed)

**Agent SDK (experiment with):**
- BRDs, complex documents (benefit from review loops)
- Artifacts requiring validation (schema compliance, business rules)
- Quality-critical generation (worth latency tradeoff)

---

## Implementation Complexity Assessment

| Feature | Complexity | Effort Estimate | Risk |
|---------|------------|----------------|------|
| Custom MCP tools (wrap existing backend) | Medium | 1-2 days | Low (well-documented pattern) |
| Basic review subagent | Medium | 2-3 days | Medium (prompt engineering for quality criteria) |
| File-based validation integration | Low | 1 day | Low (reuse existing `file_validator.py`) |
| Streaming responses | Low | 0.5 day | Low (SDK provides generator pattern) |
| Extended thinking (planning phase) | Low | 0.5 day | Low (config change + prompt adjustment) |
| Skills (BRD templates) | Medium | 2-3 days | Medium (authoring + testing) |
| Interleaved thinking | Low | 0.5 day | Low (automatic in Opus 4.6) |
| Background subagents | High | 3-4 days | High (async handling, permission pre-approval) |

**Total MVP estimate:** 5-7 days (Custom MCP tools + review subagent + validation + streaming)

**Risk factors:**
- Prompt engineering for quality reviewers (iterative tuning needed)
- Latency management (extended thinking + multi-turn can be slow)
- Integration with existing FastAPI backend (subprocess vs in-process SDK)

---

## Sources

### Official Documentation
- [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Custom Tools Documentation](https://platform.claude.com/docs/en/agent-sdk/custom-tools)
- [Subagents in SDK](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Extended Thinking Documentation](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- [Interleaved Thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#interleaved-thinking)

### Community Resources
- [Building agents with critique loops](https://medium.com/flow-specialty/ai-assisted-coding-automating-plan-reviews-with-claude-code-and-codex-for-higher-quality-plans-c7e373a625ca)
- [Tracing Claude Code's agent loop](https://medium.com/@georgesung/tracing-claude-codes-llm-traffic-agentic-loop-sub-agents-tool-use-prompts-7796941806f5)
- [File-based validation workflows](https://github.com/Pimzino/claude-code-spec-workflow)
- [Claude Code workflows GitHub](https://github.com/shinpr/claude-code-workflows)

### Agent Loop Architecture
- [The Agent Loop Behind Claude Code](https://claudecn.com/en/docs/claude-code/advanced/agent-loop/)
- [Claude Code: A Simple Loop That Produces High Agency](https://medium.com/@aiforhuman/claude-code-a-simple-loop-that-produces-high-agency-814c071b455d)

---

**Confidence Assessment:**

| Area | Level | Reason |
|------|-------|--------|
| Core capabilities | HIGH | Official SDK docs, verified API references |
| Quality improvement mechanisms | MEDIUM | Theoretical (critique loops, extended thinking) but no BA-specific benchmarks |
| Implementation complexity | MEDIUM | Documented patterns exist, but integration with existing backend untested |
| Performance characteristics | MEDIUM | Latency concerns documented, but no BA document generation benchmarks |

**Gaps to address in experimentation phase:**
- Actual latency measurements for BRD generation with review loops
- Quality metrics comparison (direct API vs agent SDK) on real user requests
- Cost analysis (extended thinking tokens vs faster direct API iterations)
