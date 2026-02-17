"""
LLM Provider Abstraction Package.

This package provides a provider-agnostic interface for LLM interactions,
enabling multi-provider support (Anthropic Claude, Google Gemini, DeepSeek,
Claude Code SDK, Claude Code CLI) while maintaining a consistent API for
the AI service layer.

Exports:
    LLMAdapter: Abstract base class for provider adapters
    LLMProvider: Enum of supported providers
    StreamChunk: Dataclass for normalized streaming responses
    LLMFactory: Factory for creating provider adapters
    AnthropicAdapter: Anthropic Claude adapter implementation
    GeminiAdapter: Google Gemini adapter implementation
    DeepSeekAdapter: DeepSeek adapter implementation
    ClaudeAgentAdapter: Claude Agent SDK adapter implementation (stub)
    ClaudeCLIAdapter: Claude Code CLI subprocess adapter implementation (stub)
"""
from .base import LLMAdapter, LLMProvider, StreamChunk
from .anthropic_adapter import AnthropicAdapter
from .gemini_adapter import GeminiAdapter
from .deepseek_adapter import DeepSeekAdapter
from .claude_agent_adapter import ClaudeAgentAdapter
from .claude_cli_adapter import ClaudeCLIAdapter
from .factory import LLMFactory

__all__ = [
    "LLMAdapter",
    "LLMProvider",
    "StreamChunk",
    "LLMFactory",
    "AnthropicAdapter",
    "GeminiAdapter",
    "DeepSeekAdapter",
    "ClaudeAgentAdapter",
    "ClaudeCLIAdapter",
]
