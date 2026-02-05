# Phase 42: Silent Artifact Generation - Research

**Researched:** 2026-02-05
**Domain:** SSE streaming control, Flutter state management, FastAPI conditional streaming
**Confidence:** HIGH

## Summary

Phase 42 implements silent artifact generation where button-triggered requests produce only an artifact card with a loading indicator, completely bypassing conversation history accumulation. This is Layer 4 of the artifact deduplication defense-in-depth strategy (Phases 40-42).

The implementation requires zero new dependencies. The entire solution uses existing patterns: (1) FastAPI Pydantic optional field for request flag, (2) SSE event filtering in the existing event generator, (3) Flutter Provider separate state variable for generation tracking, and (4) a new `GeneratingIndicator` widget following established loading state patterns. The critical architectural decision is that `generateArtifact()` MUST be a completely separate code path from `sendMessage()` to avoid frontend state machine conflicts.

User decisions from CONTEXT.md are prescriptive: progress bar replaces preset buttons during generation, shows typed artifact label ("Generating User Stories..."), friendly error messages without technical details, unlimited retries, and cancel button. The frontend uses a disabled chat input during generation to prevent concurrent requests.

**Primary recommendation:** Build backend first (ChatRequest extension + event filtering), then frontend Provider method (separate from sendMessage), then UI components (GeneratingIndicator widget + screen integration). Test error paths thoroughly since silent failures are harder to debug than conversational errors.

## Standard Stack

The phase uses the existing tech stack with no additions.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | Backend framework | Already powering SSE streaming endpoints |
| sse-starlette | 2.1+ | Server-Sent Events | Already providing EventSourceResponse for chat streaming |
| Pydantic | 2.x | Request validation | Already used for ChatRequest model |
| flutter_client_sse | 1.1+ | SSE client | Already consuming chat stream on frontend |
| Provider | 6.x | State management | Already managing conversation state |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Dio | 5.x | HTTP client | Already used in AIService for SSE header management |
| Material Design 3 | Flutter 3.x | UI components | Already used for LinearProgressIndicator |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Optional Pydantic field | New endpoint `/artifact/generate` | Cleaner separation but requires duplicating SSE logic and conversation context building |
| Separate state variable | Reuse `_isStreaming` | Simpler but causes frontend state conflicts per PITFALL-06 |
| Event filtering | Model instruction only | Fragile reliance on model compliance without guaranteed suppression |

**Installation:**
No new packages needed. All components already present in stack.

## Architecture Patterns

### Recommended Project Structure

Silent generation follows the existing request flow with conditional branching:

```
Backend flow:
1. ChatRequest with artifact_generation: true
2. Skip save_message() for user message
3. Build conversation context (history needed)
4. Append silent instruction (in-memory only)
5. Stream with text_delta suppression
6. Skip save_message() for assistant response
7. Artifact saved via save_artifact tool (unchanged)

Frontend flow:
1. User clicks preset/custom button
2. Call provider.generateArtifact() (NOT sendMessage)
3. Set _isGeneratingArtifact = true
4. Disable chat input
5. Show GeneratingIndicator widget
6. Listen for artifact_created event
7. Clear generating state, add artifact to list
```

### Pattern 1: Conditional Message Persistence

**What:** Skip database writes for ephemeral requests while preserving context building.
**When to use:** Silent operations that need historical context but should not contribute to history.

**Backend example:**
```python
# conversations.py - stream_chat endpoint

# Before streaming starts
if not body.artifact_generation:  # Normal chat
    await save_message(db, thread_id, "user", body.content)

# Build context (always needed)
conversation = await build_conversation_context(db, thread_id)

# Append ephemeral instruction for silent mode
if body.artifact_generation:
    conversation.append({
        "role": "user",
        "content": f"{body.content}\n\nIMPORTANT: Generate the artifact silently..."
    })

# After streaming completes
if accumulated_text and not body.artifact_generation:  # Only save for normal chat
    await save_message(db, thread_id, "assistant", accumulated_text)
```

Source: Existing pattern from `conversations.py:126-183` adapted for conditional persistence.

### Pattern 2: SSE Event Filtering

**What:** Suppress specific event types conditionally during streaming without breaking client state machine.
**When to use:** When different request types need different event subsets from the same stream generator.

**Backend example:**
```python
# conversations.py - event_generator within stream_chat

async for event in heartbeat_stream:
    # Check for client disconnect
    if await request.is_disconnected():
        break

    # Heartbeat events pass through (no accumulation)
    if "comment" in event:
        yield event
        continue

    # Suppress text_delta for silent generation
    if body.artifact_generation and event.get("event") == "text_delta":
        continue  # Skip yielding

    # All other events (tool_executing, artifact_created, message_complete)
    yield event
```

Source: Existing pattern from `conversations.py:158-179` with filtering added.

**Critical:** Do NOT suppress `message_complete` event. Frontend uses it for stream-end signaling regardless of mode.

### Pattern 3: Separate Frontend Code Paths

**What:** Independent methods for different request types with dedicated state variables to avoid state machine conflicts.
**When to use:** When UI flow differs significantly between operation types (e.g., conversational vs silent).

**Frontend example:**
```dart
// conversation_provider.dart

// Separate state variable (not reusing _isStreaming)
bool _isGeneratingArtifact = false;
String? _generatingArtifactType;  // For typed label

Future<void> generateArtifact(String prompt, String artifactType) async {
  if (_thread == null || _isGeneratingArtifact) return;

  _error = null;
  _isGeneratingArtifact = true;
  _generatingArtifactType = artifactType;
  notifyListeners();

  try {
    await for (final event in _aiService.streamChat(
      _thread!.id,
      prompt,
      artifactGeneration: true  // Flag for backend
    )) {
      if (event is ArtifactCreatedEvent) {
        _artifacts.add(Artifact.fromEvent(...));
      } else if (event is MessageCompleteEvent) {
        // Clear generating state on completion
        break;
      } else if (event is ErrorEvent) {
        _error = event.message;
        break;
      }
      // No TextDeltaEvent handling - suppressed by backend
    }
  } catch (e) {
    _error = e.toString();
  } finally {
    _isGeneratingArtifact = false;
    _generatingArtifactType = null;
    notifyListeners();
  }
}
```

Source: Adapted from existing `sendMessage()` pattern in `conversation_provider.dart:135-210`.

**CRITICAL:** Do NOT add messages to `_messages` list. Do NOT accumulate text in `_streamingText`. Silent generation only modifies `_artifacts` list.

### Pattern 4: Indeterminate Progress with Typed Label

**What:** LinearProgressIndicator with value: null plus context-specific text label showing operation type.
**When to use:** Long-running operations (>5 seconds typical) where progress is unknown but user needs reassurance.

**Frontend example:**
```dart
// generating_indicator.dart (new widget)

class GeneratingIndicator extends StatelessWidget {
  final String artifactType;  // "User Stories", "Acceptance Criteria", etc.
  final VoidCallback? onCancel;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          LinearProgressIndicator(value: null),  // Indeterminate
          SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Generating $artifactType...',
                style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
              ),
              if (onCancel != null)
                TextButton(
                  onPressed: onCancel,
                  child: Text('Cancel'),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
```

Sources:
- [Flutter LinearProgressIndicator docs](https://api.flutter.dev/flutter/material/LinearProgressIndicator-class.html) - indeterminate progress (value: null)
- Existing loading pattern in `streaming_message.dart` for label placement

### Pattern 5: Transform-Based Button Area Swap

**What:** Replace preset button area with progress indicator in same location using conditional rendering, not layout shifts.
**When to use:** When UI states are mutually exclusive and should occupy identical space.

**Frontend example:**
```dart
// conversation_screen.dart integration

Widget _buildInputArea(ConversationProvider provider) {
  return Column(
    children: [
      // Button area transforms into progress during generation
      if (provider.isGeneratingArtifact)
        GeneratingIndicator(
          artifactType: provider.generatingArtifactType,
          onCancel: provider.cancelGeneration,
        )
      else
        // Normal preset buttons (only when not generating)
        ChatInput(
          onSend: (msg) => provider.sendMessage(msg),
          onGenerateArtifact: _showArtifactTypePicker,
          enabled: !provider.isStreaming && budgetOk,
        ),
    ],
  );
}
```

Source: Material Design 3 guideline - in-place state transformations avoid jarring layout shifts.

### Anti-Patterns to Avoid

- **Reusing sendMessage() with SSE filtering:** Frontend state machine expects text accumulation and message bubbles. Silent mode breaks these expectations. Use separate `generateArtifact()` method.
- **Suppressing message_complete event:** Frontend relies on this for stream-end detection regardless of mode. Suppressing breaks cleanup logic.
- **Showing technical error details to users:** Backend errors like "Network timeout" or "API rate limit" should map to generic "Something went wrong. Please try again." per CONTEXT.md decisions.
- **Auto-scrolling on artifact appearance:** User may have scrolled up to review earlier content. Let artifact appear naturally at bottom without forcing scroll.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP request cancellation | Custom abort logic | Dio CancelToken | Handles streaming cleanup, connection termination, error propagation |
| Progress indicator with label | Custom animated widget | LinearProgressIndicator + Column layout | Material Design 3 compliant, accessibility support built-in |
| Friendly error message mapping | Per-error custom text | Generic fallback + error logging | Technical details leak implementation, generic message suffices per CONTEXT.md |
| SSE event type detection | String parsing event.event | Type checking (event is ArtifactCreatedEvent) | Type-safe, catches typos at compile time |

**Key insight:** SSE event suppression is straightforward (conditional `continue` in generator loop) but must preserve message_complete for cleanup. Dio already handles HTTP cancellation complexities.

## Common Pitfalls

### Pitfall 1: Frontend State Machine Conflicts

**What goes wrong:** Reusing `sendMessage()` flow with backend SSE filtering causes blank message bubbles. Frontend state machine expects text accumulation when `_isStreaming = true` and adds assistant message on MessageCompleteEvent. With text_delta suppressed, accumulated text is empty but message still added.

**Why it happens:** `sendMessage()` was designed for conversational flow with guarantees: text always streams, message always added. Silent mode breaks these invariants.

**How to avoid:** Create separate `generateArtifact()` method with dedicated state variable (`_isGeneratingArtifact`). This method:
- Does NOT set `_isStreaming = true`
- Does NOT accumulate text in `_streamingText`
- Does NOT add messages to `_messages` list
- ONLY updates `_artifacts` list on artifact_created event

**Warning signs:**
- Empty assistant message bubbles appearing after generation
- StreamingMessage widget flickering during silent generation
- Error messages showing in chat instead of error banner

Source: PITFALL-06 from `.planning/research/SUMMARY.md` - documented as CRITICAL.

### Pitfall 2: message_complete Event Suppression

**What goes wrong:** If backend suppresses message_complete event alongside text_delta, frontend never detects stream end. Loading state persists forever, cleanup never runs, UI stuck.

**Why it happens:** message_complete signals "stream finished" for all modes. It's not text-specific.

**How to avoid:** Only suppress text_delta events. Allow tool_executing, artifact_created, and message_complete to pass through:

```python
# CORRECT
if body.artifact_generation and event.get("event") == "text_delta":
    continue  # Only block text

# WRONG
if body.artifact_generation and event.get("event") in ["text_delta", "message_complete"]:
    continue  # Breaks stream-end detection
```

**Warning signs:**
- Progress indicator never clears after generation
- Backend shows successful artifact save but frontend stuck
- No error shown despite generation completing

### Pitfall 3: Chat Input Not Disabled During Generation

**What goes wrong:** User can type and send message while artifact is generating. This creates concurrent requests to same thread, potential race conditions on database (message order), and confusing UX (which operation's error is shown?).

**Why it happens:** Generation state (`_isGeneratingArtifact`) is separate from streaming state. Input enable/disable logic only checks `!_isStreaming`.

**How to avoid:** Update ChatInput enabled condition to include generation state:

```dart
// conversation_screen.dart
final inputEnabled = !provider.isStreaming &&
                     !provider.isGeneratingArtifact &&
                     budgetProvider.status != BudgetStatus.exhausted;
```

And update placeholder text when generating:
```dart
hintText: widget.enabled
    ? 'Type a message...'
    : (generatingArtifact ? 'Generating artifact...' : 'Waiting for response...')
```

**Warning signs:**
- Users report "sent message but nothing happened" during generation
- Error banner shows while progress indicator visible (concurrent operation)
- Database shows interleaved assistant messages when shouldn't exist

### Pitfall 4: Error State Doesn't Clear Progress Indicator

**What goes wrong:** Generation fails (network timeout, API error, model refusal) but progress indicator remains visible. Error shown in banner but loading animation still present. Confusing UX.

**Why it happens:** Error handling only sets `_error` but doesn't clear `_isGeneratingArtifact`.

**How to avoid:** Ensure finally block in generateArtifact() always clears state:

```dart
Future<void> generateArtifact(...) async {
  _isGeneratingArtifact = true;
  notifyListeners();

  try {
    // ... streaming logic
  } catch (e) {
    _error = e.toString();
  } finally {
    // CRITICAL: Always clear, even on error
    _isGeneratingArtifact = false;
    _generatingArtifactType = null;
    notifyListeners();
  }
}
```

And transform progress indicator to error state per CONTEXT.md:
```dart
// In conversation_screen.dart message list
if (provider.isGeneratingArtifact)
  GeneratingIndicator(...)
else if (provider.error != null && provider.lastOperationWasGeneration)
  GenerationErrorState(
    onRetry: () => provider.retryLastGeneration(),
    onDismiss: () => provider.clearError(),
  )
```

**Warning signs:**
- Progress bar stuck after error banner appears
- User can't retry because input still disabled (generating state stuck)
- Error banner + progress indicator both visible simultaneously

### Pitfall 5: Artifact Appears Before Loading Clears

**What goes wrong:** Race condition where artifact_created event adds artifact to list but `_isGeneratingArtifact` still true. UI shows both progress indicator AND artifact card momentarily.

**Why it happens:** artifact_created fires before message_complete. State cleared on message_complete but artifact added on artifact_created.

**How to avoid:** Clear generating state on artifact_created event, not message_complete:

```dart
if (event is ArtifactCreatedEvent) {
  _artifacts.add(Artifact.fromEvent(...));
  // Clear immediately when artifact appears
  _isGeneratingArtifact = false;
  _generatingArtifactType = null;
  notifyListeners();
} else if (event is MessageCompleteEvent) {
  // Cleanup only, state already cleared
  break;
}
```

**Warning signs:**
- Brief flicker showing progress bar above artifact card
- Smooth transition doesn't occur (progress -> artifact appears jarring)

## Code Examples

Verified patterns from codebase and standards.

### Backend: ChatRequest Extension

```python
# backend/app/routes/conversations.py

class ChatRequest(BaseModel):
    """Request model for chat message."""
    content: str = Field(..., min_length=1, max_length=32000)
    artifact_generation: bool = Field(default=False)  # NEW
```

Source: Existing ChatRequest at `conversations.py:34-36` plus Pydantic optional field pattern.

### Backend: Conditional Persistence and Event Filtering

```python
# backend/app/routes/conversations.py - stream_chat endpoint

# Save user message (skip for silent generation)
if not body.artifact_generation:
    await save_message(db, thread_id, "user", body.content)

# Build conversation context (always needed)
conversation = await build_conversation_context(db, thread_id)

# Append ephemeral instruction for silent mode
if body.artifact_generation:
    conversation.append({
        "role": "user",
        "content": f"{body.content}\n\n"
                   "IMPORTANT: Generate the artifact silently. "
                   "Do not include any conversational text. "
                   "Only call the save_artifact tool and stop."
    })

async def event_generator():
    accumulated_text = ""
    usage_data = None

    try:
        raw_stream = ai_service.stream_chat(conversation, project_id, thread_id, db)
        heartbeat_stream = stream_with_heartbeat(raw_stream)

        async for event in heartbeat_stream:
            if await request.is_disconnected():
                break

            # Heartbeat passes through
            if "comment" in event:
                yield event
                continue

            # Suppress text_delta for silent generation
            if body.artifact_generation and event.get("event") == "text_delta":
                continue  # Skip yielding

            # Track text (for normal mode only)
            if event.get("event") == "text_delta":
                data = json.loads(event["data"])
                accumulated_text += data.get("text", "")

            # Track usage (always needed)
            if event.get("event") == "message_complete":
                data = json.loads(event["data"])
                usage_data = data.get("usage", {})

            yield event

        # Save assistant message (skip for silent generation)
        if accumulated_text and not body.artifact_generation:
            await save_message(db, thread_id, "assistant", accumulated_text)

        # Track token usage (always)
        if usage_data:
            await track_token_usage(
                db, current_user["user_id"], AGENT_MODEL,
                usage_data.get("input_tokens", 0),
                usage_data.get("output_tokens", 0),
                f"/threads/{thread_id}/chat"
            )

        # Update summary (skip for silent - no new messages)
        if not body.artifact_generation:
            await maybe_update_summary(db, thread_id, current_user["user_id"])
```

Source: Adapted from existing `stream_chat` at `conversations.py:85-211`.

### Frontend: AIService Extension

```dart
// frontend/lib/services/ai_service.dart

Stream<ChatEvent> streamChat(
  String threadId,
  String message,
  {bool artifactGeneration = false}  // NEW parameter
) async* {
  final token = await _storage.read(key: _tokenKey);
  if (token == null) {
    yield ErrorEvent(message: 'Not authenticated');
    return;
  }

  final url = '$apiBaseUrl/api/threads/$threadId/chat';

  try {
    final stream = SSEClient.subscribeToSSE(
      method: SSERequestType.POST,
      url: url,
      header: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: {
        'content': message,
        'artifact_generation': artifactGeneration,  // NEW field
      },
    );

    // Rest unchanged - event parsing remains same
    await for (final event in stream) {
      // ... existing event handling
    }
  } catch (e) {
    yield ErrorEvent(message: 'Connection error: $e');
  }
}
```

Source: Adapted from existing streamChat at `ai_service.dart:111-179`.

### Frontend: Separate Generation Method

```dart
// frontend/lib/providers/conversation_provider.dart

bool _isGeneratingArtifact = false;
String? _generatingArtifactType;
String? _lastGenerationPrompt;  // For retry

bool get isGeneratingArtifact => _isGeneratingArtifact;
String? get generatingArtifactType => _generatingArtifactType;
bool get canRetryGeneration => _lastGenerationPrompt != null && _error != null;

Future<void> generateArtifact(String prompt, String artifactType) async {
  if (_thread == null || _isGeneratingArtifact) return;

  _error = null;
  _lastGenerationPrompt = prompt;
  _isGeneratingArtifact = true;
  _generatingArtifactType = artifactType;
  notifyListeners();

  try {
    await for (final event in _aiService.streamChat(
      _thread!.id,
      prompt,
      artifactGeneration: true,
    )) {
      if (event is ArtifactCreatedEvent) {
        _artifacts.add(Artifact.fromEvent(
          id: event.id,
          artifactType: event.artifactType,
          title: event.title,
          threadId: _thread!.id,
        ));
        // Clear state immediately when artifact appears
        _isGeneratingArtifact = false;
        _generatingArtifactType = null;
        _lastGenerationPrompt = null;  // Success - clear retry
        notifyListeners();
      } else if (event is ErrorEvent) {
        _error = event.message;
        break;
      } else if (event is MessageCompleteEvent) {
        // Stream ended normally (after artifact_created)
        break;
      }
      // Note: No TextDeltaEvent or ToolExecutingEvent handling - not yielded by backend
    }
  } catch (e) {
    _error = e.toString();
  } finally {
    // Ensure state cleared even if error before artifact_created
    _isGeneratingArtifact = false;
    _generatingArtifactType = null;
    notifyListeners();
  }
}

void retryLastGeneration() {
  if (_lastGenerationPrompt == null) return;
  final prompt = _lastGenerationPrompt!;
  final type = _generatingArtifactType ?? 'Artifact';  // Fallback
  _error = null;
  generateArtifact(prompt, type);
}
```

Source: Pattern adapted from existing `sendMessage()` at `conversation_provider.dart:135-210`.

### Frontend: GeneratingIndicator Widget

```dart
// frontend/lib/screens/conversation/widgets/generating_indicator.dart (NEW FILE)

import 'package:flutter/material.dart';

/// Progress indicator for silent artifact generation
class GeneratingIndicator extends StatefulWidget {
  /// Type of artifact being generated (for label)
  final String artifactType;

  /// Callback when user cancels
  final VoidCallback? onCancel;

  /// Show reassurance text after delay
  final Duration reassuranceDelay;

  const GeneratingIndicator({
    super.key,
    required this.artifactType,
    this.onCancel,
    this.reassuranceDelay = const Duration(seconds: 15),
  });

  @override
  State<GeneratingIndicator> createState() => _GeneratingIndicatorState();
}

class _GeneratingIndicatorState extends State<GeneratingIndicator> {
  bool _showReassurance = false;

  @override
  void initState() {
    super.initState();
    // Show reassurance text after delay
    Future.delayed(widget.reassuranceDelay, () {
      if (mounted) {
        setState(() => _showReassurance = true);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Indeterminate progress bar
          LinearProgressIndicator(
            value: null,  // Indeterminate
            backgroundColor: theme.colorScheme.surfaceContainerHighest,
          ),
          const SizedBox(height: 12),

          // Label row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Typed label
              Text(
                'Generating ${widget.artifactType}...',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),

              // Cancel button
              if (widget.onCancel != null)
                TextButton(
                  onPressed: widget.onCancel,
                  child: const Text('Cancel'),
                ),
            ],
          ),

          // Reassurance text (after delay)
          if (_showReassurance) ...[
            const SizedBox(height: 8),
            Text(
              'This may take a moment...',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
```

Source: Pattern from `streaming_message.dart` status display plus Material Design 3 LinearProgressIndicator guidelines.

### Frontend: Error State for Generation

```dart
// frontend/lib/screens/conversation/widgets/generation_error_state.dart (NEW FILE)

import 'package:flutter/material.dart';

/// Error state shown when artifact generation fails
class GenerationErrorState extends StatelessWidget {
  final VoidCallback onRetry;
  final VoidCallback onDismiss;

  const GenerationErrorState({
    super.key,
    required this.onRetry,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Generic error message
          Row(
            children: [
              Icon(
                Icons.error_outline,
                color: theme.colorScheme.onErrorContainer,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Something went wrong. Please try again.',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onErrorContainer,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Action buttons
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: onDismiss,
                child: const Text('Dismiss'),
              ),
              const SizedBox(width: 8),
              FilledButton.tonal(
                onPressed: onRetry,
                child: const Text('Retry'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
```

Source: Pattern from `error_state_message.dart` adapted for generation failures per CONTEXT.md friendly error requirement.

### Frontend: Screen Integration

```dart
// frontend/lib/screens/conversation/conversation_screen.dart

// Update _showArtifactTypePicker method (line ~198)
Future<void> _showArtifactTypePicker() async {
  final selection = await ArtifactTypePicker.show(context);

  if (selection != null && mounted) {
    final provider = context.read<ConversationProvider>();

    // Build prompt and artifact type for label
    String prompt;
    String artifactType;

    if (selection.isCustom) {
      prompt = selection.customPrompt!;
      artifactType = 'Artifact';  // Generic for custom
    } else {
      prompt = 'Generate ${selection.presetType!.displayName} from this conversation.';
      artifactType = selection.presetType!.displayName;
    }

    // Call generateArtifact (not sendMessage)
    provider.generateArtifact(prompt, artifactType);
  }
}

// Update _buildMessageList to include generating indicator (line ~371)
Widget _buildMessageList(ConversationProvider provider) {
  final messages = provider.messages;

  // Empty state unchanged...
  if (messages.isEmpty && !provider.isStreaming && !provider.isGeneratingArtifact) {
    return /* ... existing empty state ... */;
  }

  // Calculate extra items
  final hasStreamingItem = provider.isStreaming;
  final hasGeneratingItem = provider.isGeneratingArtifact;
  final hasErrorItem = provider.hasPartialContent && !provider.isStreaming;
  final hasGenerationError = provider.error != null &&
                              provider.canRetryGeneration;

  final artifactCount = provider.artifacts.length;
  final extraItems = (hasStreamingItem ? 1 : 0) +
                     (hasGeneratingItem ? 1 : 0) +
                     (hasErrorItem ? 1 : 0) +
                     (hasGenerationError ? 1 : 0);

  return ListView.builder(
    controller: _scrollController,
    padding: const EdgeInsets.symmetric(vertical: 16),
    itemCount: messages.length + artifactCount + extraItems,
    itemBuilder: (context, index) {
      // Messages
      if (index < messages.length) {
        final message = messages[index];
        return GestureDetector(
          onLongPress: () => _showMessageOptions(context, message),
          child: MessageBubble(message: message, projectId: widget.projectId),
        );
      }

      // Artifacts
      if (index < messages.length + artifactCount) {
        final artifactIndex = index - messages.length;
        final artifact = provider.artifacts[artifactIndex];
        return ArtifactCard(artifact: artifact, threadId: widget.threadId);
      }

      // Special states (after artifacts)
      final specialIndex = index - messages.length - artifactCount;

      // Generating indicator
      if (hasGeneratingItem && specialIndex == 0) {
        return GeneratingIndicator(
          artifactType: provider.generatingArtifactType ?? 'Artifact',
          onCancel: () {
            // TODO: Implement cancellation with CancelToken
          },
        );
      }

      // Generation error
      if (hasGenerationError && specialIndex == (hasGeneratingItem ? 1 : 0)) {
        return GenerationErrorState(
          onRetry: provider.retryLastGeneration,
          onDismiss: provider.clearError,
        );
      }

      // Streaming message (existing)
      if (hasStreamingItem) {
        return StreamingMessage(
          text: provider.streamingText,
          statusMessage: provider.statusMessage,
        );
      }

      // Error state message (existing)
      if (hasErrorItem) {
        return ErrorStateMessage(partialText: provider.streamingText);
      }

      return const SizedBox.shrink();
    },
  );
}

// Update ChatInput enabled logic (line ~259)
final inputEnabled = !provider.isStreaming &&
                     !provider.isGeneratingArtifact &&  // NEW
                     budgetProvider.status != BudgetStatus.exhausted;
```

Source: Existing conversation_screen.dart patterns with conditional rendering additions.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All requests save messages | Conditional persistence with ephemeral requests | v1.9.4 (Phase 42) | Cleaner UX, eliminates accumulation for button path |
| Single sendMessage() path | Separate generateArtifact() path | v1.9.4 (Phase 42) | Avoids state machine conflicts, dedicated UI flow |
| Technical error messages | Generic friendly errors | v1.9.4 (Phase 42) | Better UX per CONTEXT.md, logs retain details |
| Disabled input shows generic "Waiting..." | Context-aware placeholder text | v1.9.4 (Phase 42) | User knows whether streaming or generating |

**Deprecated/outdated:**
- None - this is new functionality. No prior silent generation pattern existed.

## Open Questions

Things that couldn't be fully resolved:

1. **Cancel Implementation Approach**
   - What we know: Dio supports CancelToken for HTTP request abortion. SSE streams can be cancelled by aborting underlying Dio request.
   - What's unclear: Whether backend needs explicit cancellation handling or if connection close suffices. Does partial artifact (mid-generation) need cleanup?
   - Recommendation: Start without cancel button. Add in Phase 42-02 after testing backend behavior on connection close. If orphaned artifacts appear, add cleanup logic.

2. **Reassurance Text Threshold**
   - What we know: CONTEXT.md specifies "after ~15 seconds" show "This may take a moment..."
   - What's unclear: Should threshold vary by artifact type? User Stories typically faster (~5-8s) than BRDs (~15-25s).
   - Recommendation: Use fixed 15s threshold for v1.9.4. Collect telemetry on actual generation times. Consider typed thresholds in v1.9.5 if wide variance observed.

3. **Error Logging Scope**
   - What we know: ERR-02 requires "silent generation failures logged to backend for debugging"
   - What's unclear: Log to console only or persist to database? Include conversation context? PII concerns?
   - Recommendation: Console logging sufficient for v1.9.4 (FastAPI logs to stdout, captured by hosting). Add structured error tracking (database table) in v2.0 if failure rates warrant investigation.

## Sources

### Primary (HIGH confidence)
- **Codebase analysis (direct inspection):**
  - `/backend/app/routes/conversations.py` - ChatRequest model, stream_chat endpoint, event_generator pattern
  - `/backend/app/services/ai_service.py` - SSE streaming, event yielding, tool execution
  - `/frontend/lib/providers/conversation_provider.dart` - sendMessage pattern, state management
  - `/frontend/lib/services/ai_service.dart` - SSE client usage, event parsing
  - `/frontend/lib/screens/conversation/conversation_screen.dart` - UI integration, artifact picker flow
  - `/frontend/lib/screens/conversation/widgets/streaming_message.dart` - Loading state pattern
  - `/frontend/lib/screens/conversation/widgets/error_state_message.dart` - Error display pattern
- **Project documentation:**
  - `.planning/research/SUMMARY.md` - PITFALL-06 (separate code paths), architecture decisions
  - `user_stories/THREAD-011_silent-artifact-generation.md` - Requirements, acceptance criteria
  - `.planning/phases/42-silent-artifact-generation/42-CONTEXT.md` - User decisions on UX
- **Official documentation:**
  - [FastAPI Pydantic models](https://fastapi.tiangolo.com/tutorial/body-fields/) - Optional field patterns
  - [Flutter LinearProgressIndicator](https://api.flutter.dev/flutter/material/LinearProgressIndicator-class.html) - Indeterminate progress (value: null)
  - [Flutter Provider patterns](https://docs.flutter.dev/data-and-backend/state-mgmt/simple) - State management best practices

### Secondary (MEDIUM confidence)
- [Dio HTTP cancellation](https://pub.dev/packages/dio) - CancelToken usage from package docs
- [Code with Andrea: Cancel HTTP requests with Riverpod](https://codewithandrea.com/tips/dio-cancel-token-riverpod/) - Pattern for cleanup on dispose
- [Flutter SSE packages](https://pub.dev/packages/flutter_client_sse) - SSEClient usage examples
- [Mastering Progress Indicators in Flutter](https://medium.com/@punithsuppar7795/mastering-progress-indicators-in-flutter-build-a-custom-reusable-linearprogressindicator-68d73abf12f0) - Custom progress patterns
- [FastAPI SSE implementation patterns](https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154) - Conditional streaming examples

### Tertiary (LOW confidence)
- None - all patterns verified against codebase or official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Zero new dependencies, all components present and analyzed
- Architecture: HIGH - All patterns adapted from existing codebase with line references
- Pitfalls: HIGH - PITFALL-06 documented as CRITICAL in research, others derived from codebase analysis
- User decisions: HIGH - All locked in CONTEXT.md with specific choices (progress bar type, error messages, button behavior)

**Research date:** 2026-02-05
**Valid until:** 30 days (stable domain - SSE patterns and state management unlikely to change)

**Ready for planning:** YES

**Key takeaways for planner:**
1. Separate code paths (generateArtifact vs sendMessage) is non-negotiable architecture decision
2. Event filtering must preserve message_complete for cleanup
3. User decisions in CONTEXT.md are prescriptive (not suggestions) - progress bar, error text, cancel button all specified
4. Two new widgets needed: GeneratingIndicator and GenerationErrorState
5. No new packages required - use existing stack components
