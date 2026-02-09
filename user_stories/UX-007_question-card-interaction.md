# UX-007: Question Card Interaction Behavior

**Priority:** High
**Status:** Open
**Component:** Frontend / Conversation Provider
**Related:** UX-004 (Parent), UX-005 (Backend), UX-006 (Rendering)
**Implementation Order:** 3 of 3 (after backend and rendering)

---

## User Story

As a user interacting with a question card,
I want to tap an option for immediate submission or type a custom answer,
so that I can respond quickly without extra confirmation steps.

---

## Problem

The question card widget (UX-006) needs defined interaction behaviors for:

1. What happens when user taps an option button
2. How the embedded text input submits responses
3. How the card transitions to collapsed state
4. How the response is sent to the AI
5. State management for tracking answered questions

---

## Solution

### Interaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER ACTIONS                              │
├──────────────────────┬──────────────────────────────────────┤
│  Tap Option Button   │  Type + Submit Custom Text           │
│         │            │         │                             │
│         ▼            │         ▼                             │
│  ┌──────────────┐    │  ┌──────────────────────────────┐    │
│  │ Immediate    │    │  │ Enter key OR tap send button │    │
│  │ Send         │    │  └──────────────────────────────┘    │
│  └──────────────┘    │         │                             │
│         │            │         │                             │
│         ▼            │         ▼                             │
│  ┌───────────────────────────────────────────────────┐      │
│  │           SEND TO AI (via ConversationProvider)    │      │
│  │   - Include question_id for tracking               │      │
│  │   - Include selected option_id OR custom text      │      │
│  └───────────────────────────────────────────────────┘      │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────┐      │
│  │           COLLAPSE CARD TO SUMMARY                 │      │
│  │   - Mark question as answered                      │      │
│  │   - Store selected option or custom text           │      │
│  │   - Re-render in collapsed state                   │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Option Button Tap Behavior

When user taps an option button:

1. **Immediate visual feedback** — button shows pressed state
2. **Disable all options** — prevent double-tap
3. **Send response to AI** — call `provider.sendMessage()` with option text
4. **Collapse card** — transition to collapsed state showing selection
5. **AI continues** — normal conversation flow resumes

```dart
void _handleOptionSelected(String optionId) {
  if (_isSubmitting) return;  // Prevent double-tap

  setState(() => _isSubmitting = true);

  final option = widget.data.options.firstWhere((o) => o.id == optionId);

  // Send to AI
  widget.onOptionSelected(optionId);

  // Provider handles:
  // 1. Sending message with option label as content
  // 2. Including metadata: { question_id, option_id }
  // 3. Marking question as answered in state
}
```

### Free Text Input Behavior

The embedded text input supports two submission methods:

**1. Enter Key (matches existing chat input pattern)**
```dart
TextField(
  controller: _textController,
  focusNode: _focusNode,
  onSubmitted: _handleCustomSubmit,
  textInputAction: TextInputAction.send,
  decoration: InputDecoration(
    hintText: widget.data.freeTextPlaceholder,
    border: OutlineInputBorder(),
    suffixIcon: IconButton(
      icon: Icon(Icons.send),
      onPressed: () => _handleCustomSubmit(_textController.text),
    ),
  ),
)
```

**2. Send Button Tap**
```dart
void _handleCustomSubmit(String text) {
  if (text.trim().isEmpty || _isSubmitting) return;

  setState(() => _isSubmitting = true);

  widget.onCustomSubmit(text.trim());

  // Provider handles:
  // 1. Sending message with custom text as content
  // 2. Including metadata: { question_id, custom_response: true }
  // 3. Marking question as answered in state
}
```

### State Management

**File:** `frontend/lib/providers/conversation_provider.dart`

Add state tracking for question cards:

```dart
class ConversationProvider extends ChangeNotifier {
  // ... existing fields

  // Question card state
  final Map<String, QuestionCardState> _questionStates = {};

  /// Get state for a specific question
  QuestionCardState? getQuestionState(String questionId) {
    return _questionStates[questionId];
  }

  /// Check if a question has been answered
  bool isQuestionAnswered(String questionId) {
    return _questionStates[questionId]?.isAnswered ?? false;
  }

  /// Handle option selection from question card
  Future<void> respondToQuestion({
    required String questionId,
    String? optionId,
    String? customText,
  }) async {
    // Mark as answered immediately (optimistic UI)
    _questionStates[questionId] = QuestionCardState(
      isAnswered: true,
      selectedOptionId: optionId,
      customResponse: customText,
      answeredAt: DateTime.now(),
    );
    notifyListeners();

    // Determine response text
    final responseText = customText ??
        _getOptionLabel(questionId, optionId!);

    // Send as regular message with metadata
    await sendMessage(
      responseText,
      metadata: {
        'question_response': true,
        'question_id': questionId,
        'option_id': optionId,
        'is_custom': customText != null,
      },
    );
  }

  /// Handle incoming question_card event
  void handleQuestionCardEvent(Map<String, dynamic> eventData) {
    final questionData = QuestionCardData.fromJson(eventData);
    final questionId = questionData.questionId;

    // Initialize state if new question
    _questionStates.putIfAbsent(
      questionId,
      () => QuestionCardState(isAnswered: false),
    );

    // Add to message list as special item type
    _items.add(QuestionCardItem(
      data: questionData,
      state: _questionStates[questionId]!,
    ));

    notifyListeners();
  }
}

class QuestionCardState {
  final bool isAnswered;
  final String? selectedOptionId;
  final String? customResponse;
  final DateTime? answeredAt;

  const QuestionCardState({
    required this.isAnswered,
    this.selectedOptionId,
    this.customResponse,
    this.answeredAt,
  });
}

class QuestionCardItem {
  final QuestionCardData data;
  final QuestionCardState state;

  bool get isAnswered => state.isAnswered;
  String? get selectedOptionId => state.selectedOptionId;
  String? get customResponse => state.customResponse;

  const QuestionCardItem({
    required this.data,
    required this.state,
  });
}
```

### Message Metadata

When responding to a question card, include metadata for analytics/tracking:

```dart
// In sendMessage or dedicated respondToQuestion method
final message = ChatMessage(
  content: responseText,
  role: 'user',
  metadata: {
    'question_response': true,
    'question_id': questionId,
    'option_id': optionId,  // null if custom
    'is_custom': customText != null,
  },
);
```

Backend can optionally log this for analytics on which options users select vs custom responses.

### Keyboard Handling

Match existing chat input behavior (UX-001):

```dart
KeyboardListener(
  focusNode: _keyboardFocusNode,
  onKeyEvent: (event) {
    if (event is KeyDownEvent) {
      if (event.logicalKey == LogicalKeyboardKey.enter) {
        if (HardwareKeyboard.instance.isShiftPressed) {
          // Shift+Enter: Insert newline (though unlikely needed for short answers)
          return;
        }
        // Enter alone: Submit
        _handleCustomSubmit(_textController.text);
      }
    }
  },
  child: TextField(...),
)
```

### Card Collapse Animation (Optional Enhancement)

For polish, animate the collapse transition:

```dart
AnimatedCrossFade(
  duration: const Duration(milliseconds: 200),
  firstChild: _buildActiveCard(),
  secondChild: _buildCollapsedCard(),
  crossFadeState: widget.isCollapsed
      ? CrossFadeState.showSecond
      : CrossFadeState.showFirst,
)
```

---

## Acceptance Criteria

### Option Selection
- [ ] Tapping option button immediately sends response to AI
- [ ] No confirmation dialog or extra tap required
- [ ] Button shows visual feedback on tap (ripple/press state)
- [ ] All options become disabled after one is selected (prevent double-tap)
- [ ] Card collapses to show selected option after send

### Free Text Submission
- [ ] Enter key sends custom text (matches existing chat input)
- [ ] Shift+Enter inserts newline (if supported in text field)
- [ ] Send button tap also sends custom text
- [ ] Empty text cannot be submitted (send button disabled)
- [ ] Placeholder text shows in empty field
- [ ] Card collapses to show custom response in quotes

### State Management
- [ ] Question answered state persists across widget rebuilds
- [ ] Provider tracks `questionId` → `QuestionCardState` mapping
- [ ] `isQuestionAnswered()` returns correct state
- [ ] Collapsed state survives conversation refresh

### Message Sending
- [ ] Response sent via `sendMessage()` or equivalent
- [ ] Message content is option label OR custom text
- [ ] Metadata includes `question_id` for tracking
- [ ] Metadata includes `option_id` when option selected
- [ ] Metadata includes `is_custom: true` for free text

### Edge Cases
- [ ] Rapid double-tap on option doesn't send twice
- [ ] Network error during send shows error state (not stuck collapsed)
- [ ] Very long custom text is handled gracefully (truncation or scroll)
- [ ] Card remains functional after conversation clear/reload

---

## Technical References

**Frontend:**
- `frontend/lib/providers/conversation_provider.dart` — state management
- `frontend/lib/screens/conversation/widgets/chat_input.dart` — keyboard handling reference
- `frontend/lib/screens/conversation/conversation_screen.dart` — message list integration

**Existing Patterns:**
- `sendMessage()` method for sending user messages
- `_handleRetry()` for optimistic UI patterns
- `StreamingMessage` for state transition patterns

---

## Testing Scenarios

1. **Happy path - option selection:** Tap option → card collapses → AI responds
2. **Happy path - custom text:** Type → Enter → card collapses → AI responds
3. **Double-tap prevention:** Tap option twice quickly → only one message sent
4. **Empty text rejection:** Try to submit empty field → nothing happens
5. **Network error:** Disconnect during send → error shown, card stays active for retry
6. **State persistence:** Answer question → scroll away → scroll back → still collapsed

---

*Created: 2026-02-05*
*Part of UX-004 Question Card UI feature*
