# ENH-012: Assistant Direct API Evaluation

## Decision: Claude Code CLI (Locked)

**Status:** Implemented

### Summary

Assistant threads (`thread_type = "assistant"`) use **Claude Code CLI** as the LLM provider.

### Provider Options Evaluated

| Option | Pros | Cons |
|--------|------|------|
| Claude Code CLI | Fast, MCP tools, local | Requires CLI install |
| Claude Agent SDK | Full control, async | More complex |
| Direct API | Cheapest | No tool handling |
| Anthropic API | Simple | No MCP tools |

### Decision Rationale

Claude Code CLI chosen because:
1. MCP tool integration (search_documents, save_artifact)
2. Streaming support
3. Agentic behavior for complex tasks
4. Already deployed and tested

### Code Reference

`ai_service.py:823`:
```python
# LOGIC-03: Override provider for Assistant threads
# (per locked decision: hardcoded to claude-code-cli)
if thread_type == "assistant":
    provider = "claude-code-cli"
```

### Alternative

If latency becomes an issue, consider DeepSeek adapter (cheaper, fast) but would need manual tool handling implementation.
