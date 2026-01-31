"""
LLM Provider Abstraction Package.

This package provides a provider-agnostic interface for LLM interactions,
enabling multi-provider support (Anthropic Claude, Google Gemini, DeepSeek)
while maintaining a consistent API for the AI service layer.

Exports:
    LLMAdapter: Abstract base class for provider adapters
    LLMProvider: Enum of supported providers
    StreamChunk: Dataclass for normalized streaming responses

Future exports (added in subsequent tasks):
    LLMFactory: Factory for creating provider adapters
    AnthropicAdapter: Anthropic Claude adapter implementation
"""
from .base import LLMAdapter, LLMProvider, StreamChunk

__all__ = [
    "LLMAdapter",
    "LLMProvider",
    "StreamChunk",
]
