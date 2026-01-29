# Business-Analyst Skill Integration Analysis

## Executive Summary

This document analyzes how to integrate the `/business-analyst` skill into the BA Assistant backend. The skill currently exists as a Claude Code skill in `.claude/business-analyst/` and needs to be adapted for the production backend AI service.

## Current State Analysis

### 1. Existing Business-Analyst Skill Structure

Located at `.claude/business-analyst/`:

```
business-analyst/
├── SKILL.md                    # Main skill definition (273 lines)
├── references/
│   ├── discovery-framework.md  # Discovery question sequences (374 lines)
│   ├── brd-template.md         # BRD output structure (489 lines)
│   ├── tone-guidelines.md      # Professional communication (513 lines)
│   └── error-protocols.md      # Error handling scenarios (494 lines)
└── scripts/
    ├── validate_brd.py         # BRD quality validation
    ├── validate_preflight.py   # Pre-generation checks
    └── validate_structure.py   # Markdown structure checks
```

**Total skill content: ~2,143 lines of detailed instructions**

### 2. Current Backend AI Service

Located at `backend/app/services/ai_service.py`:

- Uses direct `anthropic.AsyncAnthropic` client
- Simple system prompt (~30 lines) with basic BA guidance
- Two tools: `search_documents` and `save_artifact`
- SSE streaming for real-time responses
- Tool execution loop for document search and artifact creation

### 3. Claude Agent SDK vs Direct API

| Aspect | Direct API (Current) | Agent SDK |
|--------|---------------------|-----------|
| Tool execution | Manual loop in `stream_chat` | SDK manages agentic loop |
| System prompt | Static string | Can load from files |
| Skill support | Not native | Native `.claude/skills/` |
| Streaming | Manual SSE handling | Built-in streaming mode |
| Error handling | Try/catch in service | SDK catches and flags |
| Complexity | Lower | Higher learning curve |

**Recommendation:** Stay with direct API for MVP. The Agent SDK adds complexity without significant benefits for our use case. The skill content can be integrated by expanding the system prompt.

## Two Approaches for Skill Integration

### Approach A: Expanded System Prompt (Recommended for MVP)

Transform the skill's markdown content into an optimized system prompt that captures the core methodology without exceeding token limits.

**Pros:**
- Minimal code changes
- Works with existing architecture
- Fast to implement
- No new dependencies

**Cons:**
- Large system prompt uses tokens
- Can't dynamically load reference files
- Must manually sync skill updates

**Token estimate:** ~3,000-4,000 tokens for condensed skill prompt

### Approach B: Dynamic Skill Loading

Create a skill loader that reads skill files at runtime and constructs the system prompt dynamically.

**Pros:**
- Skill updates automatically apply
- Reference files loaded on demand
- Closer to Claude Code skill system

**Cons:**
- More complex implementation
- File I/O on every request (cacheable)
- Need to decide which files to load when

### Approach C: Full Agent SDK Migration

Replace direct Anthropic API with Claude Agent SDK.

**Pros:**
- Native skill support
- Automatic tool loop management
- Future-proof for advanced features

**Cons:**
- Major refactor
- Learning curve
- Overkill for current needs
- SDK still maturing

## Critical Skill Behaviors to Preserve

### 1. One-Question-at-a-Time Protocol
The skill's core differentiator: never batch multiple questions. Each response asks exactly ONE question with:
- Clear question
- Brief rationale
- Three suggested answer options

### 2. Mode Detection
At session start, detect:
- **Meeting Mode**: Live customer discovery, concise responses
- **Document Refinement Mode**: Modifying existing BRD

### 3. Zero-Assumption Protocol
Never assume meanings. When encountering ambiguous terms ("seamless", "scalable"), immediately clarify with specific interpretation options.

### 4. Technical Boundary Enforcement
Redirect technical implementation discussions (React vs Vue, microservices, etc.) back to business requirements.

### 5. Discovery Priority Sequence
Cover in order:
1. Primary business objective
2. Target user personas
3. Key user flows
4. Current state challenges
5. Success metrics and KPIs
6. Regulatory/compliance requirements
7. Stakeholder perspectives
8. Business processes impacted

### 6. BRD Generation Triggers
Only generate when user explicitly requests: "create the documentation", "generate the BRD", "ready for deliverables"

### 7. Pre-Flight Validation
Before generating BRD, verify critical information is captured:
- Primary objective defined
- User personas identified
- Key user flows documented
- Success metrics specified
- Core requirements captured

## Integration Architecture

### Proposed System Prompt Structure

```python
SYSTEM_PROMPT = f"""
{CORE_BA_BEHAVIOR}      # ~500 tokens - Role, one-question protocol
{MODE_DETECTION}        # ~200 tokens - Meeting vs Document mode
{DISCOVERY_FRAMEWORK}   # ~800 tokens - Condensed question sequences
{TONE_GUIDELINES}       # ~300 tokens - Key DO/DON'T examples
{ERROR_PROTOCOLS}       # ~200 tokens - Critical error handling
{TOOL_INSTRUCTIONS}     # ~300 tokens - When to search/generate

Total: ~2,300 tokens system prompt
"""
```

### Tool Changes

**Current tools (keep):**
- `search_documents` - Already implemented
- `save_artifact` - Already implemented

**New tool to add:**
- `generate_brd` - Full BRD generation with template structure

### State Management

**Session state to track:**
```python
@dataclass
class DiscoveryState:
    mode: Literal["meeting", "document_refinement", "unset"]
    questions_asked: int
    understanding_verified: bool
    areas_covered: List[str]  # e.g., ["objective", "personas", "flows"]
    pending_clarifications: List[str]
    ready_for_brd: bool
```

**Implementation options:**
1. Store in thread metadata (DB)
2. Pass as context in messages
3. Let Claude maintain implicitly (current approach)

**Recommendation:** Let Claude maintain state implicitly for MVP. The system prompt instructs Claude to track progress and verify understanding every 5-7 questions.

## Token Budget Analysis

| Component | Tokens | Notes |
|-----------|--------|-------|
| System prompt (skill) | ~2,300 | Condensed from 2,143 lines |
| Conversation context | ~120,000 max | 80% of 150k budget |
| Response buffer | ~4,096 | max_tokens setting |
| Tool definitions | ~500 | Two existing + BRD tool |

**Impact:** Adding the skill increases system prompt from ~300 tokens to ~2,300 tokens (~2,000 token increase per request). At $3/1M input tokens, this adds ~$0.006 per request - negligible.

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| System prompt too long | Medium | Low | Compress to essential behaviors |
| Claude ignores skill instructions | High | Medium | Test thoroughly, iterate on prompt |
| Performance degradation | Low | Low | Minimal token increase |
| Skill behavior drift | Medium | Medium | Regular testing against skill goals |
| BRD quality issues | High | Medium | Include template structure in prompt |

## Success Metrics

1. **Question Quality**: Claude asks one question at a time with rationale and options
2. **Mode Detection**: Claude correctly identifies Meeting vs Document mode
3. **Boundary Enforcement**: Technical questions are redirected to business focus
4. **BRD Completeness**: Generated BRDs include all template sections
5. **User Satisfaction**: BAs find the assistant helpful (post-MVP validation)

## Dependencies

- Existing AI service (`ai_service.py`)
- Existing tools (search_documents, save_artifact)
- Skill markdown files (already in repo)

## Out of Scope

- Claude Agent SDK migration
- Real-time skill file reloading
- Multi-skill support
- Validation script integration (Python scripts in skill)
