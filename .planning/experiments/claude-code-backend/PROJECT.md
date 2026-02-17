# Claude Code as AI Backend — Experiment

## What This Is

An experimental branch investigating whether Claude Code (via Agent SDK Python API or CLI subprocess model) can serve as a superior AI backend provider for BA Assistant's document generation and conversational AI capabilities. This replaces the direct Anthropic API approach for potentially higher-quality BRDs, user stories, and acceptance criteria through agent-level capabilities like multi-turn self-review and file-based validation.

## Core Value

Determine if Claude Code's agent capabilities produce measurably better business analysis artifacts than the current direct API approach, and if so, build a production-viable adapter.

## Previous Evaluation (Jan 2026)

The Claude Agent SDK was evaluated in Phase 4.1 and **rejected** for these reasons:
- SDK requires Claude Code CLI as runtime dependency
- PaaS constraint (Railway/Render) violated by Docker/Redis requirements
- Use-case mismatch: SDK designed for filesystem agents, BA Assistant only needs chat + DB tools
- Direct API already handled everything in ~30 lines

**Decision documented in:** `.planning/legacy/ANALYSIS-claude-agent-sdk-workaround.md`

## What Changed

- Agent SDK has matured (new versions, hosting patterns, possibly lighter deployment)
- Infrastructure constraint removed — VPS/Docker now acceptable for this experiment
- Quality expectations increased — need better document generation
- `agent_service.py` exists as starting point (430 lines, unused but functional structure)
- Known quality gaps identified in current direct API approach

## Known Quality Gaps (Current Direct API)

- Document generation is single-pass (no self-review/iteration loop)
- No file-based artifact validation (write → read-back → fix cycle)
- Limited to whatever the model produces in one tool call
- No ability to use extended thinking + tool use in combination effectively
- Artifacts sometimes have structural inconsistencies (missing sections, uneven depth)

## Approaches to Investigate

### Approach A: Agent SDK Python API
- Use `claude-agent-sdk` package directly in FastAPI
- Structured tool loops, MCP servers, skill integration
- Question: Does it STILL require Claude Code CLI binary?

### Approach B: CLI Subprocess Model
- Spawn Claude Code CLI as subprocess per request
- Full agent capabilities including file operations
- JSON/structured output modes for server integration

## Constraints

- **Branch isolation**: All work on `feature/claude-code-backend`, never modify master
- **No infrastructure limits**: VPS/Docker/bare metal all acceptable
- **Must fit existing adapter pattern**: New adapter must conform to `LLMAdapter` ABC
- **Quality must be measurable**: Side-by-side comparison with direct API required
- **Time-boxed**: Research in 1 session, PoC in 1 session

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Separate experiment branch | Isolates risk from production codebase | — Pending |
| Separate planning directory | Avoids conflicts with master's .planning/ state | — Pending |
| v0.1-claude-code versioning | Clean slate for experiment, doesn't interfere with v2.x track | — Pending |
| Research both approaches | User wants full comparison before committing to one | — Pending |

---
*Last updated: 2026-02-13 after milestone initialization*
