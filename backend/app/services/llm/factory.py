"""
LLM Provider Factory.

Factory class for creating LLM provider adapters based on provider name.
Handles API key retrieval from settings and adapter instantiation.

This module enables provider selection at runtime without the calling
code needing to know about specific adapter implementations.
"""
from typing import Optional

from .base import LLMAdapter, LLMProvider
from .anthropic_adapter import AnthropicAdapter
from .gemini_adapter import GeminiAdapter
from .deepseek_adapter import DeepSeekAdapter
from .claude_agent_adapter import ClaudeAgentAdapter
from .claude_cli_adapter import ClaudeCLIAdapter
from app.config import settings


class LLMFactory:
    """
    Factory for creating LLM provider adapters.

    Provides a single entry point for adapter creation, handling:
    - Provider name validation
    - API key retrieval from settings
    - Adapter instantiation with correct configuration

    Usage:
        adapter = LLMFactory.create("anthropic")
        async for chunk in adapter.stream_chat(messages, system_prompt):
            process(chunk)
    """

    # Registry of provider adapters
    _adapters = {
        LLMProvider.ANTHROPIC: AnthropicAdapter,
        LLMProvider.GOOGLE: GeminiAdapter,
        LLMProvider.DEEPSEEK: DeepSeekAdapter,
        LLMProvider.CLAUDE_CODE_SDK: ClaudeAgentAdapter,
        LLMProvider.CLAUDE_CODE_CLI: ClaudeCLIAdapter,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        model: Optional[str] = None,
    ) -> LLMAdapter:
        """
        Create adapter for specified provider.

        Args:
            provider: Provider name string (e.g., "anthropic")
            model: Optional model override (uses provider default if not specified)

        Returns:
            LLMAdapter instance configured for the specified provider

        Raises:
            ValueError: If provider is not supported or no API key is configured
        """
        # Validate provider name
        try:
            provider_enum = LLMProvider(provider)
        except ValueError:
            supported = ", ".join(cls.list_providers())
            raise ValueError(
                f"Unsupported provider: {provider}. Supported: {supported}"
            )

        # Get adapter class
        adapter_class = cls._adapters.get(provider_enum)
        if not adapter_class:
            raise ValueError(f"No adapter registered for provider: {provider}")

        # Get API key and determine model
        api_key = cls._get_api_key(provider_enum)

        # Use provider-specific model from settings if not specified
        if model is None:
            if provider_enum == LLMProvider.GOOGLE:
                model = settings.gemini_model
            elif provider_enum == LLMProvider.DEEPSEEK:
                model = settings.deepseek_model

        return adapter_class(api_key=api_key, model=model)

    @classmethod
    def _get_api_key(cls, provider: LLMProvider) -> str:
        """
        Get API key from settings for provider.

        Args:
            provider: LLMProvider enum value

        Returns:
            API key string

        Raises:
            ValueError: If API key is not configured
        """
        if provider == LLMProvider.ANTHROPIC:
            key = settings.anthropic_api_key
            if not key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not configured. "
                    "Set the environment variable or add to .env file."
                )
            return key

        if provider == LLMProvider.GOOGLE:
            key = settings.google_api_key
            if not key:
                raise ValueError(
                    "GOOGLE_API_KEY not configured. "
                    "Get API key from https://aistudio.google.com/app/apikey"
                )
            return key

        if provider == LLMProvider.DEEPSEEK:
            key = settings.deepseek_api_key
            if not key:
                raise ValueError(
                    "DEEPSEEK_API_KEY not configured. "
                    "Get API key from https://platform.deepseek.com/api_keys"
                )
            return key

        if provider in (LLMProvider.CLAUDE_CODE_SDK, LLMProvider.CLAUDE_CODE_CLI):
            key = settings.anthropic_api_key
            if not key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not configured. "
                    "Claude Code providers require an Anthropic API key."
                )
            return key

        raise ValueError(f"No API key configuration for provider: {provider.value}")

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        Return list of supported provider names.

        Returns:
            List of provider name strings (e.g., ["anthropic"])
        """
        return [p.value for p in cls._adapters.keys()]
