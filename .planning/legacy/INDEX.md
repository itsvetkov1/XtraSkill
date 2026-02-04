# Legacy Documentation Index

This directory contains documentation for **scrapped approaches**, **abandoned features**, and **historical decisions** that are no longer active in the codebase but preserved for reference.

---

## Why Keep Legacy Documentation?

1. **Decision Context** — Understand why certain approaches were rejected
2. **Avoid Repetition** — Don't re-investigate already-explored dead ends
3. **Historical Reference** — Trace the evolution of architectural decisions

---

## Contents

### Claude Agent SDK (Scrapped Approach)

The initial plan was to use Anthropic's Claude Agent SDK for skill integration. Research revealed the SDK requires Claude Code CLI as a runtime dependency, making it unsuitable for web backend deployment. The approach was scrapped in favor of direct Anthropic API with hardcoded system prompt.

| File | Description | Date |
|------|-------------|------|
| `ANALYSIS-claude-agent-sdk-workaround.md` | Analysis of why SDK was scrapped and recommendation to use direct API | 2026-01-25 |
| `claude-agent-sdk-web-backend-plan.md` | Proposed workaround plan (Docker + nginx + Redis) — **never implemented** | 2026-01-25 |
| `research-claude-agent-sdk-issue.md` | Research task that discovered the CLI dependency | 2026-01-25 |
| `compass_artifact_wf-*.md` | External research output confirming SDK limitations | 2026-01-25 |
| `SYSTEM-PROMPT-business-analyst.md` | Documentation of skill → system prompt transformation | 2026-01-26 |
| `04.1-agent-sdk-skill-integration/` | Complete phase directory with plans, research, and completion summary | 2026-01-25 to 2026-01-26 |

### Key Decision Summary

**Original Plan:**
- Use `claude-agent-sdk` Python package
- Load business-analyst skill via filesystem discovery
- Deploy to PaaS (Railway/Render)

**Problem Discovered:**
- SDK requires Claude Code CLI (`claude.exe`) as runtime dependency
- CLI is a Node.js application meant for local development
- Workaround would require Docker, nginx, Redis — violates PaaS constraint

**Final Decision:**
- Use direct `anthropic` package (already in use)
- Transform SKILL.md content into XML system prompt
- Hardcode system prompt in `ai_service.py`

**Dead Code Created (still in repo):**
- `backend/app/services/agent_service.py` — SDK-based service, never wired to routes
- `backend/app/services/skill_loader.py` — Loads SKILL.md, only used by agent_service
- `.claude/business-analyst/SKILL.md` — Not loaded at runtime

---

## Related Active Documentation

For current architecture, see:
- `.planning/PROJECT.md` — Main project documentation
- `backend/app/services/ai_service.py` — Active AI service with hardcoded system prompt
- `backend/tests/test_service_architecture.py` — Tests verifying active approach

---

## Adding New Legacy Items

When deprecating an approach or feature:

1. Move documentation to this directory
2. Update this INDEX.md with summary
3. Note the date and reason for deprecation
4. Reference any dead code that remains in the repo

---

*Last Updated: 2026-02-04*
*Created during BUG-016 investigation*
