# OpenClaw Tools Integration

This document describes how OpenClaw skills are integrated as tools in XtraSkill.

## Overview

When using OpenClaw as the LLM provider, XtraSkill has access to additional tools beyond the standard document search and artifact generation.

## Available Tools

### Core XtraSkill Tools

| Tool | Description |
|------|-------------|
| `search_documents` | Search across project documents |
| `save_artifact` | Save generated content to project |

### OpenClaw Skill Tools

| Tool | Description | Requires |
|------|-------------|----------|
| `send_email` | Send email via configured account | Email skill |
| `check_calendar` | Check Google Calendar events | Calendar skill |
| `post_twitter` | Post to Twitter/X | Twitter skill |
| `spawn_subagent` | Spawn a specialized sub-agent | - |
| `web_search` | Search the web | - |

## Tool Configuration

Tools can be enabled/disabled in the settings:

```python
from app.services.openclaw_tools import OpenClawToolMapper

# Enable only specific tools
mapper = OpenClawToolMapper(enabled_tools=[
    "search_documents",
    "save_artifact", 
    "web_search",
])

tools = mapper.get_tools()
```

## Sub-Agent Types

| Agent | Purpose |
|-------|---------|
| `dev` | General development tasks |
| `debugger` | Bug diagnosis and fixing |
| `code-reviewer` | Code review |
| `architect` | Architecture planning |

## Integration with LLM

The tools are passed to the OpenClaw adapter:

```python
from app.services.openclaw_tools import OpenClawToolMapper

mapper = OpenClawToolMapper()
tools = mapper.get_tools()

async for chunk in adapter.stream_chat(
    messages=messages,
    system_prompt=system_prompt,
    tools=tools,
):
    # Handle chunks
```

## Error Handling

Tool errors are returned as `StreamChunk` with `chunk_type="error"`:

```python
if chunk.chunk_type == "error":
    logger.error(f"Tool error: {chunk.error}")
```

## Frontend UI

Users can configure which tools are available in Settings (AC-5).

## Dependencies

- INFRA-002: OpenClaw as LLM Provider
- OpenClaw Gateway running with required skills configured
