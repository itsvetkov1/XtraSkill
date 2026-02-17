# Technology Stack: Claude Code Backend Integration

**Project:** BA Assistant Claude Code Integration
**Researched:** 2026-02-13
**Current SDK Version:** 0.1.35 (2026-02-10)
**Current CLI Version:** 2.1.39 (2026-02-10)

---

## Executive Summary

Two integration approaches available:

1. **Agent SDK (Python Package)** — Currently used, requires upgrade from v0.1.22 → v0.1.35
2. **CLI Subprocess (Non-Interactive)** — New experimental approach, requires Claude Code CLI binary

**Recommendation:** Start with Agent SDK upgrade (known integration path), evaluate CLI subprocess as future enhancement.

---

## Approach 1: Agent SDK (Python Package) — RECOMMENDED

### Current State

**Already installed:** `claude-agent-sdk>=0.1.0` in requirements.txt
**Current version in use:** v0.1.22 (based on imports in agent_service.py)
**Latest version:** v0.1.35 (2026-02-10)

### Required Stack Additions

| Package | Version | Purpose | Why |
|---------|---------|---------|-----|
| `claude-agent-sdk` | `==0.1.35` | Core Agent SDK library | Pin to latest stable version with large agent definition fix (#468) |

### Breaking Changes from v0.1.22 → v0.1.35

**CRITICAL FIX (v0.1.31):**
- Large agent definitions no longer silently fail due to ARG_MAX limits
- Agent payloads now sent via stdin instead of CLI args
- **Impact:** Your existing `skill_prompt` (loaded in agent_service.py) will work reliably with large prompts

**Type Renaming:**
- `ClaudeCodeOptions` → `ClaudeAgentOptions` (already using correct name in agent_service.py ✓)

**New Features (v0.1.31+):**
- MCP tool annotations via `@tool` decorator's `annotations` parameter
- Bundled CLI updated from v2.x → v2.1.39

**Confidence:** HIGH — Official Anthropic SDK with comprehensive documentation

### Installation

```bash
# Upgrade existing SDK
pip install claude-agent-sdk==0.1.35
```

### Integration Points with Existing Backend

**✓ Already Compatible:**
- `query()` function with async iterator → works with FastAPI async endpoints
- `ClaudeAgentOptions` → already used in agent_service.py:295
- `@tool` decorator → already used for search_documents and save_artifact (agent_service.py:40, 123)
- `create_sdk_mcp_server()` → already used (agent_service.py:211)
- SSE streaming via `AsyncGenerator[Dict[str, Any], None]` → compatible with sse-starlette

**New Capabilities with v0.1.35:**
- `include_partial_messages=True` → Already enabled (agent_service.py:307)
- `StreamEvent` type → Already imported (agent_service.py:23)
- Sandbox configuration via `sandbox` parameter in `ClaudeAgentOptions`

### Dependencies (Bundled)

The SDK bundles its own Claude Code CLI binary internally — **no separate Node.js or CLI installation required for SDK usage.**

**Python version:** 3.10+ (currently using 3.11 ✓)

### Deployment Considerations

**No infrastructure changes required:**
- Runs in existing Python venv
- No Node.js dependency (CLI bundled with SDK package)
- No Docker requirement for basic usage
- Sandbox mode available but optional (see Approach 2 for Docker-based sandboxing)

**API Key:**
- Already configured: `ANTHROPIC_API_KEY` in .env
- SDK uses same authentication as direct Anthropic API

---

## Approach 2: CLI Subprocess (Non-Interactive) — EXPERIMENTAL

### Use Case

Evaluate if `claude -p` (CLI subprocess) produces higher-quality document generation than `query()` function.

### Required Stack Additions

| Component | Version | Purpose | Why |
|-----------|---------|---------|-----|
| Claude Code CLI | v2.1.39+ | Non-interactive agent execution | Native binary, no Node.js required |

### Installation Requirements

**Native Binary (Recommended):**
```bash
# macOS/Linux installation
curl -fsSL https://claude.ai/install.sh | sh
```

**Verification:**
```bash
which claude        # Should show: ~/.local/bin/claude (or similar)
claude --version    # Should show: 2.1.39+
```

**No Node.js Required:**
- As of 2026, native installers are recommended over npm
- Native binary is self-contained with automatic updater
- **Exception:** If using MCP servers (Context7, Playwright, etc.), install Node.js 18+ for `npx` support

### CLI Subprocess Pattern

**Input/Output Formats:**
- `--output-format json` → Structured response with `result`, `session_id`, `usage`
- `--output-format stream-json` → Newline-delimited JSON events (compatible with SSE)
- `--output-format text` → Plain text (default)

**Integration with FastAPI:**

```python
import subprocess
import json
import asyncio

async def stream_from_cli(prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream from Claude CLI subprocess."""
    process = await asyncio.create_subprocess_exec(
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--allowed-tools", "Read,Write,Bash",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async for line in process.stdout:
        if line:
            event = json.loads(line.decode())
            # Parse event and yield SSE format
            if event.get("type") == "stream_event":
                yield {"event": "text_delta", "data": json.dumps(event)}

    await process.wait()
```

**Advantages over SDK `query()`:**
- Uses Claude Code's full system prompt and tooling optimizations
- May produce different (potentially higher-quality) document generation
- Supports same SSE streaming pattern as SDK

**Disadvantages:**
- Process spawn overhead (200-500ms startup)
- No session continuity (each call is fresh session unless using `--resume`)
- More complex error handling (process exit codes vs Python exceptions)
- No direct Python API for tool registration (must use MCP servers)

### Tool Integration

**Custom Tools via MCP Servers:**

CLI requires tools to be MCP servers on stdio/SSE/HTTP. Cannot use Python `@tool` decorator directly.

**Options:**
1. **Convert existing tools to MCP stdio server** (Python script Claude CLI launches)
2. **Use Agent SDK for tool integration** (recommended — stick with Approach 1)

### Deployment Considerations

**Binary Requirements:**
- Install Claude Code CLI on deployment VPS
- Binary path: `~/.local/bin/claude` (or custom via `--cli-path`)
- Update mechanism: `claude update` (manual or scheduled)

**No Docker Required for Basic Usage:**
- CLI runs as subprocess in existing environment
- Sandboxing available via `--sandbox` flag (requires Docker on VPS if enabled)

---

## Approach Comparison

| Criterion | Agent SDK (Recommended) | CLI Subprocess (Experimental) |
|-----------|------------------------|-------------------------------|
| **Integration complexity** | LOW — already integrated | MEDIUM — subprocess + output parsing |
| **Tool registration** | Python `@tool` decorator ✓ | MCP server required |
| **Session continuity** | `ClaudeSDKClient` with multi-turn | `--resume` with session ID (stateless) |
| **Startup latency** | ~50ms (in-process) | ~300ms (process spawn) |
| **Output quality** | Standard Agent SDK | **Unknown — needs testing** |
| **Error handling** | Python exceptions | Process exit codes + stderr parsing |
| **Existing codebase fit** | HIGH — drop-in upgrade | MEDIUM — new abstraction layer |
| **Node.js dependency** | None (CLI bundled) | None (native binary) |
| **Docker dependency** | None (optional sandbox) | None (optional sandbox) |
| **Deployment complexity** | LOW — pip upgrade | MEDIUM — CLI binary installation |

---

## Sandbox Configuration (Both Approaches)

### When Sandboxing is Needed

**Not needed for BA Assistant use case:**
- No untrusted code execution
- Tools are controlled (search_documents, save_artifact)
- No arbitrary bash commands from user input

**Sandboxing is for:**
- Running untrusted code from user prompts
- Isolating file system access beyond permission rules
- Network request isolation

### Docker-Based Sandboxing (Optional)

**If sandbox mode is needed:**

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | 20.10+ | Container isolation for agent execution |
| gVisor (optional) | Latest | Enhanced syscall interception for stronger isolation |

**SDK Configuration:**
```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    sandbox={
        "enabled": True,
        "autoAllowBashIfSandboxed": True,
        "network": {"allowLocalBinding": True},
    }
)
```

**CLI Configuration:**
```bash
claude -p "Build my project" --sandbox
```

**Deployment (VPS):**
```bash
# Install Docker on VPS
curl -fsSL https://get.docker.com | sh

# Verify
docker --version
```

**Resource Limits (Recommended):**
- Memory: 2GB per container
- CPU: 2 cores
- PID limit: 100
- Read-only filesystem where possible

---

## What NOT to Add

### ❌ Node.js Runtime
**Reason:** Neither approach requires Node.js unless using MCP servers. Native CLI is standalone binary.

**Exception:** If adding Context7, Playwright, or other npx-based MCP servers.

### ❌ TypeScript SDK
**Reason:** Python-only backend. TypeScript SDK is for Node.js environments.

### ❌ `@anthropic-ai/claude-code` npm package
**Reason:** Deprecated. Native binary installer is recommended path.

### ❌ Additional LLM SDKs
**Reason:** Already have `anthropic==0.76.0` for direct API. Agent SDK uses same authentication.

### ❌ Docker (for now)
**Reason:** Not needed for basic integration. Add only if sandboxing becomes a requirement.

---

## Recommended Upgrade Path

### Phase 1: Agent SDK Upgrade (Low Risk)

**Changes:**
1. Update requirements.txt: `claude-agent-sdk==0.1.35`
2. Run: `pip install -r requirements.txt`
3. Test existing agent_service.py flows
4. Verify large skill prompts work (v0.1.31 fix)

**Expected outcome:** Better reliability, no functional changes.

### Phase 2: Evaluate CLI Subprocess (Experimental)

**Prerequisites:**
- Phase 1 complete and validated
- CLI installed on development machine

**Implementation:**
1. Create new `ClaudeCodeCLIAdapter` class implementing `LLMAdapter` ABC
2. Use subprocess with `--output-format stream-json`
3. Parse events and convert to existing `StreamChunk` format
4. A/B test document generation quality vs Agent SDK

**Decision point:** If CLI produces measurably better output, promote to production. Otherwise, stick with Agent SDK.

---

## Version Pinning Strategy

**Pin exactly:**
```txt
claude-agent-sdk==0.1.35
```

**Rationale:**
- SDK is pre-1.0 (breaking changes possible)
- Recent fixes critical for large payloads (v0.1.31)
- Bundled CLI updated automatically with SDK version

**Upgrade cadence:** Check releases monthly, upgrade when:
- Critical bug fixes announced
- New features needed (e.g., structured outputs enhancements)
- Security advisories

---

## Sources

### Official Documentation
- [Claude Agent SDK Python API Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [Agent SDK Releases](https://github.com/anthropics/claude-agent-sdk-python/releases)
- [Claude Code CLI Headless Mode](https://code.claude.com/docs/en/headless)
- [Agent SDK Hosting Guide](https://platform.claude.com/docs/en/agent-sdk/hosting)
- [Streaming Output Documentation](https://platform.claude.com/docs/en/agent-sdk/streaming-output)

### Installation Guides
- [Claude Code Setup](https://code.claude.com/docs/en/setup)
- [Native vs npm Installation](https://www.eesel.ai/blog/npm-install-claude-code)
- [Ubuntu Installation Guide 2026](https://itecsonline.com/post/how-to-install-claude-code-on-ubuntu-linux-complete-guide-2025)

### Community Resources
- [Agent SDK vs CLI Comparison](https://drlee.io/claude-code-vs-claude-agent-sdk-whats-the-difference-177971c442a9)
- [Docker Sandbox Configuration](https://docs.docker.com/ai/sandboxes/claude-code/)
- [Secure Deployment Guide](https://platform.claude.com/docs/en/agent-sdk/secure-deployment)

### Package Repositories
- [claude-agent-sdk on PyPI](https://pypi.org/project/claude-agent-sdk/)
- [@anthropic-ai/claude-code on npm](https://www.npmjs.com/package/@anthropic-ai/claude-code) (deprecated)

---

## Confidence Assessment

| Component | Confidence | Basis |
|-----------|-----------|-------|
| Agent SDK version | HIGH | Official PyPI, GitHub releases with dates |
| CLI version | HIGH | Official Anthropic changelog, release notes |
| API compatibility | HIGH | Existing code review + official API docs |
| Breaking changes | MEDIUM | Release notes reviewed, but no exhaustive testing |
| CLI subprocess pattern | MEDIUM | Official docs exist, but no production examples found |
| Docker requirements | HIGH | Official hosting guide, Docker docs |
| Node.js requirements | HIGH | Multiple sources confirm native binary is standalone |

**Overall Confidence:** HIGH for Agent SDK approach, MEDIUM for CLI subprocess approach.

---

## Next Steps for Roadmap

**Phase structure recommendation:**

1. **Dependency Upgrade** — Update claude-agent-sdk to v0.1.35, verify existing flows
2. **CLI Evaluation** — Install CLI, implement subprocess adapter, A/B test quality
3. **Production Decision** — Choose SDK vs CLI based on output quality testing
4. **Deployment** — Update VPS with chosen approach (pip upgrade or CLI binary)

**No deeper research needed** unless:
- Sandbox mode becomes a requirement (investigate Docker security hardening)
- MCP server integration needed (investigate stdio server patterns)
- Multi-session continuity required for CLI approach (investigate --resume patterns)
