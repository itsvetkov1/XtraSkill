# Research Task: claude-agent-sdk Standalone Usage Investigation

## Context
The `claude-agent-sdk` Python package (v0.1.22) fails when used in a backend application with error: "Claude Code not found at: [path]/claude.exe". The package description states "Python SDK for Claude Code", suggesting it's a wrapper for the Claude Code CLI rather than a standalone API client.

**Current situation:**
- Building a FastAPI backend that needs Claude AI integration
- Installed `claude-agent-sdk` expecting direct Anthropic API access
- SDK fails at runtime requiring `claude.exe` binary
- Currently using direct `anthropic` package as workaround

## Objective
Research and document:
1. Whether this is intended behavior or a bug/misconfiguration
2. Official documentation on SDK requirements and usage
3. Workarounds to use the SDK without Claude Code CLI
4. Alternative packages for building Claude-powered Python applications
5. Community reports of similar issues

## Search Queries to Execute
1. `claude-agent-sdk python requires claude code cli`
2. `claude-agent-sdk standalone usage without claude.exe`
3. `anthropic claude agent sdk python documentation`
4. `github anthropics claude-agent-sdk-python issues`
5. `claude-agent-sdk vs anthropic python sdk difference`
6. `"Claude Code not found" claude-agent-sdk error`

## Sources to Check
- GitHub: `anthropics/claude-agent-sdk-python` (issues, README, discussions)
- PyPI: `claude-agent-sdk` package page and description
- Anthropic official documentation (docs.anthropic.com)
- Stack Overflow questions tagged with claude/anthropic
- Reddit r/anthropic or r/ClaudeAI discussions

## Expected Output Format

**Summary:** [2-3 sentence overview of findings]

**Is this intended behavior?** [Yes/No/Unclear + evidence]

**Official Documentation Says:** [Quote or paraphrase from docs]

**Known Issues/Reports:**
- [Link 1]: [Summary]
- [Link 2]: [Summary]

**Workarounds Found:**
1. [Workaround + feasibility assessment]

**Alternative Packages:**
| Package | Purpose | Standalone? | Notes |
|---------|---------|-------------|-------|
| anthropic | Direct API | Yes | Currently using |
| [other] | [purpose] | [yes/no] | [notes] |

**Recommendation:** [Which approach to use for the BA Assistant project]

## Constraints
- Focus on Python packages only
- Prioritize official Anthropic sources
- Note dates of information (SDK is evolving rapidly)
- Flag if information is speculative vs confirmed

---

## Research Findings

*(To be filled in after executing the research)*

---

*Created: 2026-01-25*
*Related to: Phase 4.1 - Agent SDK & Skill Integration*
