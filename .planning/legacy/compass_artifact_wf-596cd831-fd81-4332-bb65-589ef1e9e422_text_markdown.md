# Claude-Agent-SDK: CLI dependency is by design

The `claude-agent-sdk` package **requires the Claude Code CLI as intended behavior**, not a bug. It is architecturally designed as a Python wrapper that spawns the CLI as a subprocess—the CLI handles all API communication while the SDK provides a Pythonic interface. Your current workaround using the direct `anthropic` package is the **correct solution** for backend applications.

## The package serves a different purpose than you expected

The naming is somewhat misleading. While `claude-agent-sdk` sounds like a generic API client, it's specifically designed to build **autonomous agents** that interact with local environments—reading files, running commands, editing code. Anthropic's official documentation states: "The SDK gives you the same tools, agent loop, and context management that power Claude Code, programmable in Python."

The architecture works as follows: your Python application calls the SDK, which spawns a Claude Code CLI subprocess, which then communicates with Anthropic's API. This design enables powerful local automation capabilities but makes the package unsuitable for traditional web backends without the CLI runtime.

**Key documentation quote** from the GitHub README: "The Claude Code CLI is automatically bundled with the package - no separate installation required! The SDK will use the bundled CLI by default."

## Multiple users have hit this exact error

The "Claude Code not found" error appears in **eight documented GitHub issues** across Anthropic's repositories, with the earliest dated September 2025. The most relevant include:

- **Issue #7238** (anthropics/claude-code): "SDK unable to find executable" - closed as not planned, 8 upvotes
- **Issue #978** (Auto-Claude): Detailed root cause analysis showing PATH inheritance problems between GUI applications and Python backends
- **Issue #529** (Auto-Claude): Windows-specific bundled CLI detection failures

The bundled CLI approach—while convenient for CLI applications—frequently fails in containerized, GUI-launched, or non-standard PATH environments. Maintainers have closed some issues as "not planned," indicating this architecture is intentional.

## Workarounds require the CLI to exist somewhere

All documented workarounds assume you have or can install the CLI:

1. **Specify custom path**: `ClaudeAgentOptions(cli_path='/path/to/claude')`
2. **Install globally**: `npm install -g @anthropic-ai/claude-code` or `curl -fsSL https://claude.ai/install.sh | bash`
3. **Create symlink**: `sudo ln -s /opt/homebrew/bin/claude /usr/local/bin/claude`
4. **Modify PATH**: `export PATH="$HOME/node_modules/.bin:$PATH"`

**No workaround exists for truly standalone usage.** The SDK cannot function without the CLI runtime—this is fundamental to its design, not a configuration issue.

## Package comparison for your use case

| Package | Purpose | Standalone | Best for |
|---------|---------|------------|----------|
| **`anthropic`** | Direct API client | **Yes** | Backend services, FastAPI, web apps |
| **`claude-agent-sdk`** | Autonomous agents with local tools | No | CLI apps, file automation, coding tools |
| `claude-code-sdk` | Deprecated predecessor | No | Don't use—migrate away |

The fundamental distinction: `anthropic` is a **pure HTTP API client** while `claude-agent-sdk` is an **agent framework** that wraps local infrastructure. They serve completely different use cases despite both enabling Claude integration.

## Your current approach is the recommended one

For a FastAPI backend, Anthropic officially recommends the `anthropic` package. From their documentation at docs.anthropic.com:

```python
from fastapi import FastAPI
from anthropic import AsyncAnthropic

app = FastAPI()
client = AsyncAnthropic()  # Uses ANTHROPIC_API_KEY env var

@app.post("/chat")
async def chat(prompt: str):
    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return {"response": message.content[0].text}
```

The `anthropic` package provides **full type safety**, **async/await support**, **automatic retries**, **streaming**, and **tool use/function calling**—everything needed for production backend services without any CLI dependency.

## When you would actually need claude-agent-sdk

The agent SDK becomes valuable only when you need Claude to autonomously:
- Read and write files on a local system
- Execute bash commands
- Edit code with file system access
- Use MCP (Model Context Protocol) tools
- Operate with the same capabilities as Claude Code itself

For a typical backend API serving chat completions, document analysis, or structured outputs, these capabilities aren't needed—and the complexity isn't justified.

## Conclusion

**This is intended behavior**: The `claude-agent-sdk` is a CLI wrapper by design, documented clearly in official sources. **Your workaround is actually the correct solution**: The `anthropic` package is what Anthropic recommends for backend services. Continue with your current implementation—you've already found the right tool for the job.

If you later need agent capabilities with local file access, you would install Claude Code CLI separately (`npm install -g @anthropic-ai/claude-code`) and use `claude-agent-sdk`. But for standard backend AI integration, stick with the direct `anthropic` SDK.