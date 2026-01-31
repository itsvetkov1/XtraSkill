# Architecture Patterns: Multi-LLM Provider Integration

**Domain:** Multi-LLM Provider Support for BA Assistant
**Researched:** 2026-01-31
**Confidence:** HIGH (based on codebase analysis + official documentation patterns)

---

## Current Architecture Overview

```
                         Current State

+------------------+     +------------------+     +------------------+
|   Flutter App    |     |   FastAPI        |     |   Anthropic      |
|                  |---->|   Backend        |---->|   Messages API   |
|  - AIService     | SSE |  - ai_service.py |     |                  |
|  - ConversationProvider|  - MODEL const   |     |  claude-sonnet-  |
|                  |<----|                  |<----|  4-5-20250929    |
+------------------+     +------------------+     +------------------+
                              |
                              v
                         +----------+
                         | SQLite   |
                         | - threads|
                         | - messages|
                         +----------+
```

### Current Coupling Points

1. **Backend `ai_service.py`**:
   - Hardcoded `MODEL = "claude-sonnet-4-5-20250929"`
   - Direct `anthropic.AsyncAnthropic` client instantiation
   - Anthropic-specific streaming via `client.messages.stream()`
   - Tool definitions tied to Anthropic schema format

2. **Frontend `Thread` model**:
   - No `model_provider` field
   - No provider indicator in UI

3. **Database `threads` table**:
   - No `model_provider` column
   - No `model_name` column

---

## Recommended Architecture

### Component Diagram

```
                         Target State (v1.8)

+------------------+     +------------------+     +------------------+
|   Flutter App    |     |   FastAPI        |     | LLM Providers    |
|                  |---->|   Backend        |     |                  |
|  - AIService     | SSE |                  |     | +-------------+  |
|  - ProviderSelector|  |  +-------------+ |---->| | Anthropic   |  |
|  - ModelIndicator|<----| | LLMAdapter  | |     | | Claude      |  |
|                  |     |  | (abstract) | |     | +-------------+  |
+------------------+     |  +------+------+ |     |                  |
        |                |         |        |     | +-------------+  |
        v                |         v        |---->| | Google      |  |
+------------------+     |  +------+------+ |     | | Gemini 3    |  |
| Settings Screen  |     |  | Provider   | |     | +-------------+  |
| - Default provider|    |  | Factory    | |     |                  |
| - API key config |     |  +-------------+ |     | +-------------+  |
+------------------+     |                  |---->| | DeepSeek    |  |
                         |  +-------------+ |     | | V3.2        |  |
                         |  | Normalizer  | |     | +-------------+  |
                         |  | (response)  | |     |                  |
                         |  +-------------+ |     +------------------+
                         |         |        |
                         +---------|--------+
                                   v
                         +------------------+
                         | SQLite/Postgres  |
                         | - threads        |
                         |   + model_provider|
                         |   + model_name   |
                         | - provider_configs|
                         +------------------+
```

### Adapter Pattern Design

```python
# backend/app/services/llm/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"

@dataclass
class StreamChunk:
    """Normalized streaming chunk from any provider."""
    text: str
    is_complete: bool = False
    reasoning_content: Optional[str] = None  # For DeepSeek thinking mode
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None

@dataclass
class ToolCall:
    """Normalized tool call request."""
    id: str
    name: str
    arguments: Dict[str, Any]

@dataclass
class ToolResult:
    """Normalized tool execution result."""
    tool_call_id: str
    content: str

class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Return the provider identifier."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this provider supports SSE streaming."""
        pass

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        pass

    @property
    @abstractmethod
    def supports_thinking_mode(self) -> bool:
        """Whether this provider has reasoning/thinking mode."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response from the LLM.

        Args:
            messages: Conversation history in normalized format
            system_prompt: System instructions
            tools: Tool definitions (provider adapts to native format)
            **kwargs: Provider-specific options (thinking_enabled, etc.)

        Yields:
            StreamChunk: Normalized response chunks
        """
        pass

    @abstractmethod
    def normalize_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert normalized messages to provider-specific format."""
        pass

    @abstractmethod
    def normalize_tools(
        self,
        tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert normalized tool schemas to provider-specific format."""
        pass
```

### Provider Implementations

```python
# backend/app/services/llm/anthropic_adapter.py
import anthropic
from .base import LLMAdapter, LLMProvider, StreamChunk

class AnthropicAdapter(LLMAdapter):
    """Anthropic Claude adapter."""

    MODELS = {
        "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
        "claude-opus-4-5": "claude-opus-4-5-20251101",
        "claude-haiku-4": "claude-4-haiku-latest",
    }

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = self.MODELS.get(model, model)

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        return True

    @property
    def supports_thinking_mode(self) -> bool:
        return False  # Claude uses extended thinking differently

    async def stream_chat(self, messages, system_prompt, tools=None, **kwargs):
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=self.normalize_messages(messages),
            tools=self.normalize_tools(tools) if tools else None,
            system=system_prompt
        ) as stream:
            async for text in stream.text_stream:
                yield StreamChunk(text=text)

            final = await stream.get_final_message()
            yield StreamChunk(
                text="",
                is_complete=True,
                usage={
                    "input_tokens": final.usage.input_tokens,
                    "output_tokens": final.usage.output_tokens
                }
            )

    def normalize_messages(self, messages):
        # Anthropic uses role: "user" | "assistant"
        # Already matches our normalized format
        return messages

    def normalize_tools(self, tools):
        # Anthropic tool format already used in current codebase
        return tools
```

```python
# backend/app/services/llm/gemini_adapter.py
from google import genai
from google.genai.types import Tool, FunctionDeclaration
from .base import LLMAdapter, LLMProvider, StreamChunk

class GeminiAdapter(LLMAdapter):
    """Google Gemini adapter."""

    MODELS = {
        "gemini-3-flash": "gemini-3-flash-preview",
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-pro": "gemini-2.5-pro",
    }

    def __init__(self, api_key: str, model: str = "gemini-3-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = self.MODELS.get(model, model)

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GOOGLE

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        return True

    @property
    def supports_thinking_mode(self) -> bool:
        return False

    async def stream_chat(self, messages, system_prompt, tools=None, **kwargs):
        # Gemini uses generate_content_stream with async
        config = {
            "system_instruction": system_prompt,
        }
        if tools:
            config["tools"] = self.normalize_tools(tools)

        async for chunk in self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=self.normalize_messages(messages),
            config=config
        ):
            if chunk.text:
                yield StreamChunk(text=chunk.text)

        yield StreamChunk(text="", is_complete=True)

    def normalize_messages(self, messages):
        # Convert to Gemini's Content format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        return contents

    def normalize_tools(self, tools):
        # Convert Anthropic-style tools to Gemini FunctionDeclarations
        gemini_tools = []
        for tool in tools:
            gemini_tools.append(FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["input_schema"]
            ))
        return [Tool(function_declarations=gemini_tools)]
```

```python
# backend/app/services/llm/deepseek_adapter.py
from openai import AsyncOpenAI  # DeepSeek uses OpenAI-compatible API
from .base import LLMAdapter, LLMProvider, StreamChunk

class DeepSeekAdapter(LLMAdapter):
    """DeepSeek V3.2 adapter with thinking mode support."""

    MODELS = {
        "deepseek-chat": "deepseek-chat",      # Non-thinking mode
        "deepseek-reasoner": "deepseek-reasoner",  # Thinking mode
    }

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = self.MODELS.get(model, model)

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.DEEPSEEK

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        return True  # DeepSeek V3.2 supports tool use

    @property
    def supports_thinking_mode(self) -> bool:
        return True

    async def stream_chat(self, messages, system_prompt, tools=None, **kwargs):
        thinking_enabled = kwargs.get("thinking_enabled", False)

        # Build request
        request_messages = [{"role": "system", "content": system_prompt}]
        request_messages.extend(self.normalize_messages(messages))

        extra_body = {}
        if thinking_enabled:
            extra_body["thinking"] = {"type": "enabled"}

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=request_messages,
            stream=True,
            tools=self.normalize_tools(tools) if tools else None,
            extra_body=extra_body if extra_body else None
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield StreamChunk(
                    text=chunk.choices[0].delta.content,
                    reasoning_content=getattr(
                        chunk.choices[0].delta,
                        'reasoning_content',
                        None
                    )
                )

        yield StreamChunk(text="", is_complete=True)

    def normalize_messages(self, messages):
        # DeepSeek uses OpenAI format
        return messages

    def normalize_tools(self, tools):
        # Convert to OpenAI function calling format
        return [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        } for tool in tools]
```

### Provider Factory

```python
# backend/app/services/llm/factory.py
from typing import Optional
from .base import LLMAdapter, LLMProvider
from .anthropic_adapter import AnthropicAdapter
from .gemini_adapter import GeminiAdapter
from .deepseek_adapter import DeepSeekAdapter
from app.config import settings

class LLMFactory:
    """Factory for creating LLM adapters."""

    _adapters = {
        LLMProvider.ANTHROPIC: AnthropicAdapter,
        LLMProvider.GOOGLE: GeminiAdapter,
        LLMProvider.DEEPSEEK: DeepSeekAdapter,
    }

    @classmethod
    def create(
        cls,
        provider: LLMProvider,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> LLMAdapter:
        """
        Create an LLM adapter for the specified provider.

        Args:
            provider: The LLM provider to use
            model: Optional model name override
            api_key: Optional API key override (uses settings if not provided)

        Returns:
            Configured LLM adapter instance
        """
        adapter_class = cls._adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unsupported provider: {provider}")

        # Get API key from settings if not provided
        if api_key is None:
            api_key = cls._get_api_key(provider)

        kwargs = {"api_key": api_key}
        if model:
            kwargs["model"] = model

        return adapter_class(**kwargs)

    @classmethod
    def _get_api_key(cls, provider: LLMProvider) -> str:
        """Get API key for provider from settings."""
        key_map = {
            LLMProvider.ANTHROPIC: settings.anthropic_api_key,
            LLMProvider.GOOGLE: settings.google_api_key,
            LLMProvider.DEEPSEEK: settings.deepseek_api_key,
        }
        key = key_map.get(provider)
        if not key:
            raise ValueError(f"No API key configured for {provider}")
        return key
```

---

## Database Schema Changes

### Migration: Add provider to threads

```python
# alembic/versions/xxxx_add_model_provider_to_threads.py
"""Add model_provider and model_name to threads table."""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add columns with defaults for existing data
    op.add_column('threads',
        sa.Column('model_provider', sa.String(20),
                  nullable=False, server_default='anthropic')
    )
    op.add_column('threads',
        sa.Column('model_name', sa.String(100),
                  nullable=False, server_default='claude-sonnet-4-5')
    )

    # Add index for filtering by provider
    op.create_index('ix_threads_model_provider', 'threads', ['model_provider'])

def downgrade():
    op.drop_index('ix_threads_model_provider')
    op.drop_column('threads', 'model_name')
    op.drop_column('threads', 'model_provider')
```

### Updated Thread Model

```python
# backend/app/models.py (additions)

class Thread(Base):
    # ... existing fields ...

    # LLM provider configuration
    model_provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="anthropic",
        index=True
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="claude-sonnet-4-5"
    )
```

### Optional: User Preferences Table

```python
# For storing user's default provider preference
class UserPreferences(Base):
    """User preferences including default LLM provider."""

    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    default_provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="anthropic"
    )
    default_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="claude-sonnet-4-5"
    )
```

---

## Frontend State Management

### Updated Thread Model

```dart
// frontend/lib/models/thread.dart

enum LLMProvider {
  anthropic('anthropic', 'Claude'),
  google('google', 'Gemini'),
  deepseek('deepseek', 'DeepSeek');

  final String value;
  final String displayName;
  const LLMProvider(this.value, this.displayName);

  static LLMProvider fromString(String value) {
    return LLMProvider.values.firstWhere(
      (e) => e.value == value,
      orElse: () => LLMProvider.anthropic,
    );
  }
}

class Thread {
  final String id;
  final String projectId;
  final String? title;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int? messageCount;
  final List<Message>? messages;

  // New fields for provider support
  final LLMProvider modelProvider;
  final String modelName;

  Thread({
    required this.id,
    required this.projectId,
    this.title,
    required this.createdAt,
    required this.updatedAt,
    this.messageCount,
    this.messages,
    this.modelProvider = LLMProvider.anthropic,
    this.modelName = 'claude-sonnet-4-5',
  });

  factory Thread.fromJson(Map<String, dynamic> json) {
    return Thread(
      id: json['id'],
      projectId: json['project_id'],
      title: json['title'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      messageCount: json['message_count'] as int?,
      messages: json['messages'] != null
          ? (json['messages'] as List)
              .map((m) => Message.fromJson(m as Map<String, dynamic>))
              .toList()
          : null,
      modelProvider: LLMProvider.fromString(
        json['model_provider'] ?? 'anthropic'
      ),
      modelName: json['model_name'] ?? 'claude-sonnet-4-5',
    );
  }
}
```

### Provider Selector Widget

```dart
// frontend/lib/widgets/provider_selector.dart

class ProviderSelector extends StatelessWidget {
  final LLMProvider selected;
  final ValueChanged<LLMProvider> onChanged;
  final bool showModelSelector;

  const ProviderSelector({
    super.key,
    required this.selected,
    required this.onChanged,
    this.showModelSelector = false,
  });

  @override
  Widget build(BuildContext context) {
    return DropdownButton<LLMProvider>(
      value: selected,
      items: LLMProvider.values.map((provider) {
        return DropdownMenuItem(
          value: provider,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _getProviderIcon(provider),
              const SizedBox(width: 8),
              Text(provider.displayName),
            ],
          ),
        );
      }).toList(),
      onChanged: (value) {
        if (value != null) onChanged(value);
      },
    );
  }

  Widget _getProviderIcon(LLMProvider provider) {
    // Provider-specific icons
    switch (provider) {
      case LLMProvider.anthropic:
        return const Icon(Icons.auto_awesome, size: 20);
      case LLMProvider.google:
        return const Icon(Icons.lightbulb_outline, size: 20);
      case LLMProvider.deepseek:
        return const Icon(Icons.psychology, size: 20);
    }
  }
}
```

### Model Indicator in Conversation

```dart
// In conversation_screen.dart AppBar

AppBar(
  title: Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(provider.thread?.title ?? 'New Conversation'),
      if (provider.thread != null)
        Text(
          '${provider.thread!.modelProvider.displayName} - ${provider.thread!.modelName}',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
    ],
  ),
  // ...
)
```

---

## Data Flow

### Thread Creation with Provider Selection

```
User clicks "New Thread" in ThreadListScreen
        |
        v
ThreadCreateDialog shows with:
  - Title field
  - Provider dropdown (Anthropic/Gemini/DeepSeek)
  - Model dropdown (filtered by provider)
        |
        v
POST /projects/{id}/threads
{
  "title": "Optional title",
  "model_provider": "anthropic",
  "model_name": "claude-sonnet-4-5"
}
        |
        v
Backend creates Thread with provider info
        |
        v
Returns ThreadResponse with provider fields
        |
        v
Frontend navigates to ConversationScreen
ConversationScreen shows model indicator
```

### Chat with Provider-Aware Routing

```
User sends message in ConversationScreen
        |
        v
POST /threads/{id}/chat {"content": "..."}
        |
        v
Backend loads Thread with model_provider, model_name
        |
        v
LLMFactory.create(thread.model_provider, thread.model_name)
        |
        v
Adapter-specific streaming (Anthropic/Gemini/DeepSeek)
        |
        v
Normalized StreamChunk events
        |
        v
SSE events to frontend (same format for all providers)
        |
        v
ConversationProvider handles events identically
```

---

## Suggested Build Order

### Phase 1: Backend Foundation (Days 1-2)

1. **Create adapter interface and base classes**
   - `backend/app/services/llm/base.py`
   - `backend/app/services/llm/__init__.py`

2. **Extract current Anthropic logic to adapter**
   - `backend/app/services/llm/anthropic_adapter.py`
   - Migrate from `ai_service.py` to adapter pattern

3. **Create factory with single provider**
   - `backend/app/services/llm/factory.py`
   - Wire into existing `conversations.py` route

4. **Verify no regression**
   - All existing functionality works unchanged

### Phase 2: Database & API Changes (Days 2-3)

5. **Add model_provider columns**
   - Alembic migration
   - Update Thread model

6. **Update thread creation API**
   - Accept `model_provider`, `model_name` in ThreadCreate
   - Update ThreadResponse schemas

7. **Wire provider into chat route**
   - Use Thread's provider to select adapter

### Phase 3: Additional Providers (Days 3-5)

8. **Add Gemini adapter**
   - `backend/app/services/llm/gemini_adapter.py`
   - Add `google-genai` to requirements.txt
   - Add `GOOGLE_API_KEY` to config

9. **Add DeepSeek adapter**
   - `backend/app/services/llm/deepseek_adapter.py`
   - Uses `openai` SDK with custom base_url
   - Add `DEEPSEEK_API_KEY` to config

10. **Test all providers streaming**
    - Verify SSE format consistency
    - Verify tool calling (if supported)

### Phase 4: Frontend Integration (Days 5-7)

11. **Update Thread model in Flutter**
    - Add `modelProvider`, `modelName` fields

12. **Update ThreadCreateDialog**
    - Add provider/model selector

13. **Add model indicator to ConversationScreen**
    - Show provider badge in AppBar

14. **Update Settings screen**
    - Default provider selection
    - Provider-specific API key management (optional)

### Phase 5: Polish & Testing (Days 7-8)

15. **Error handling per provider**
    - Normalize error messages
    - Handle rate limits, auth failures

16. **Token tracking per provider**
    - Update TokenUsage to include provider
    - Different pricing per provider

17. **End-to-end testing**
    - Create threads with each provider
    - Verify streaming works
    - Verify conversations remember their model

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `LLMAdapter` (abstract) | Define streaming interface | None (interface only) |
| `AnthropicAdapter` | Anthropic API calls, format conversion | Anthropic SDK |
| `GeminiAdapter` | Google API calls, format conversion | Google GenAI SDK |
| `DeepSeekAdapter` | DeepSeek API calls, thinking mode | OpenAI SDK (custom base) |
| `LLMFactory` | Adapter instantiation, API key lookup | Settings, Adapters |
| `conversations.py` | HTTP/SSE layer, thread validation | LLMFactory, Database |
| `Thread` model | Persist provider choice per conversation | Database |
| `ThreadService` (Flutter) | Create threads with provider | Backend API |
| `ProviderSelector` (Flutter) | UI for provider selection | Parent widget |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Direct Provider SDK Usage in Routes

**What:** Calling `anthropic.AsyncAnthropic()` directly in route handlers
**Why bad:** Locks you into one provider, makes switching impossible
**Instead:** Always use factory + adapter pattern

### Anti-Pattern 2: Provider-Specific Event Formats

**What:** Different SSE event structures per provider
**Why bad:** Frontend needs provider-specific handling
**Instead:** Normalize all events to single StreamChunk format

### Anti-Pattern 3: Storing Full API Responses

**What:** Persisting provider-specific response structures to database
**Why bad:** Database becomes provider-dependent
**Instead:** Normalize to our own Message schema before storing

### Anti-Pattern 4: UI Provider Logic Creep

**What:** Frontend has `if (provider == 'anthropic')` checks everywhere
**Why bad:** Adding providers requires frontend changes throughout
**Instead:** Backend normalizes everything; frontend treats all providers identically

---

## Scalability Considerations

| Concern | v1.8 (3 providers) | Future (10+ providers) |
|---------|-------------------|------------------------|
| API Keys | Environment variables | Secrets manager / vault |
| Rate Limits | Per-provider simple tracking | Redis-backed rate limiter |
| Fallback | Manual provider selection | Auto-fallback on errors |
| Caching | None | Response caching for repeated queries |
| Monitoring | Basic logging | OpenTelemetry per-provider spans |

---

## Sources

### Official Documentation
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Google Gemini API Reference](https://ai.google.dev/api)
- [DeepSeek API Docs - Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode)
- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/)

### Architecture Patterns
- [LiteLLM - Multi-Provider Interface](https://docs.litellm.ai/docs/)
- [Multi-LLM Systems with Abstract Classes](https://medium.com/algomart/multi-llm-systems-with-abstract-classes-in-python-038cd6ce78d5)
- [FastAPI LLM Streaming Best Practices](https://medium.com/@bhagyarana80/8-fastapi-tricks-for-low-latency-llm-backends-2831e3ee35d8)

### API Comparison
- [OpenAI API vs Anthropic API Comparison](https://www.eesel.ai/blog/openai-api-vs-anthropic-api)
- [Anthropic's /v1/messages Endpoint Parameters](https://scalablehuman.com/2025/09/03/anthropics-v1-messages-endpoint-parameters-openai-comparison-more/)
