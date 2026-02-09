# UX-006: Frontend Question Card Rendering

**Priority:** High
**Status:** Open
**Component:** Frontend / Conversation UI
**Related:** UX-004 (Parent), UX-005 (Backend), UX-007 (Interaction)
**Implementation Order:** 2 of 3 (after backend, before interaction polish)

---

## User Story

As a user viewing the conversation,
I want AI discovery questions to appear as visually distinct cards,
so that I can immediately recognize when input is needed and see my available options clearly.

---

## Problem

When `question_card` SSE events arrive from the backend (see UX-005), the frontend needs to:

1. Recognize the event type and not render it as plain text
2. Display a visually distinct card that stands out from regular messages
3. Present options as tappable buttons in a clean layout
4. Include an embedded text input for free-text responses
5. Fit naturally into the existing message list without jarring transitions

---

## Solution

### New Widget: QuestionCard

**File:** `frontend/lib/screens/conversation/widgets/question_card.dart`

A StatefulWidget that renders the structured question data as an interactive card.

### Visual Design Specifications

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   [Question Icon]  Discovery Question                   │  ← Header with category badge
│                                                         │
│   What is the primary business objective?               │  ← Question text (bold, larger)
│                                                         │
│   Understanding your main goal ensures all features     │  ← Rationale (smaller, muted)
│   align with business priorities.                       │
│                                                         │
│   ┌─────────────────────────────────────────────────┐  │
│   │  ⭐ Increase revenue through acquisition        │  │  ← Default option (star icon)
│   │     Focus on growing customer base              │  │  ← Description (if present)
│   └─────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────┐  │
│   │  Improve operational efficiency                 │  │
│   │     Streamline processes and eliminate waste    │  │
│   └─────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────┐  │
│   │  Enhance customer retention                     │  │
│   └─────────────────────────────────────────────────┘  │
│                                                         │
│   ┌───────────────────────────────────────┐  ┌─────┐  │
│   │  Or type your own answer...           │  │  ➤  │  │  ← Embedded text input
│   └───────────────────────────────────────┘  └─────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Styling

| Element | Style |
|---------|-------|
| Card container | `surfaceContainerHighest` background, 12px border radius, subtle elevation |
| Category badge | Chip with icon (💬 discovery, ❓ clarification, ⚙️ mode_selection) |
| Question text | `titleMedium`, bold weight |
| Rationale | `bodySmall`, `onSurfaceVariant` color |
| Option buttons | `OutlinedButton` or `Card` with `InkWell`, full width |
| Default option | Leading star icon, slightly highlighted border |
| Option description | `bodySmall` below label, muted color |
| Text input | `TextField` with send `IconButton`, matches chat input styling |

### Card States

**1. Active State (awaiting response)**
- All options tappable
- Text input enabled
- Full visual presentation as shown above

**2. Collapsed State (after response)**
- Shows only question text and selected answer
- Options and text input hidden
- Checkmark icon indicates completion
- Reduced height, subtle styling

```
┌─────────────────────────────────────────────────────────┐
│  ✓  What is the primary business objective?             │
│     → Improve operational efficiency                    │
└─────────────────────────────────────────────────────────┘
```

**3. Custom Response Collapsed State**
```
┌─────────────────────────────────────────────────────────┐
│  ✓  What is the primary business objective?             │
│     → "Reduce time-to-market for new features"          │
└─────────────────────────────────────────────────────────┘
```

### Widget Structure

```dart
class QuestionCard extends StatefulWidget {
  final QuestionCardData data;
  final bool isCollapsed;
  final String? selectedOptionId;
  final String? customResponse;
  final Function(String optionId) onOptionSelected;
  final Function(String text) onCustomSubmit;

  const QuestionCard({
    required this.data,
    required this.onOptionSelected,
    required this.onCustomSubmit,
    this.isCollapsed = false,
    this.selectedOptionId,
    this.customResponse,
    super.key,
  });

  @override
  State<QuestionCard> createState() => _QuestionCardState();
}

class _QuestionCardState extends State<QuestionCard> {
  final TextEditingController _textController = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  @override
  Widget build(BuildContext context) {
    if (widget.isCollapsed) {
      return _buildCollapsedCard();
    }
    return _buildActiveCard();
  }

  Widget _buildActiveCard() {
    return Card(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 12),
            _buildQuestionText(),
            if (widget.data.rationale != null) ...[
              const SizedBox(height: 8),
              _buildRationale(),
            ],
            const SizedBox(height: 16),
            _buildOptions(),
            if (widget.data.allowFreeText) ...[
              const SizedBox(height: 12),
              _buildFreeTextInput(),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildCollapsedCard() {
    final response = widget.customResponse ??
        widget.data.options
            .firstWhere((o) => o.id == widget.selectedOptionId)
            .label;

    return Card(
      color: Theme.of(context).colorScheme.surfaceContainerLow,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.data.questionText,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '→ ${widget.customResponse != null ? '"$response"' : response}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ... additional builder methods
}
```

### Data Model

**File:** `frontend/lib/models/question_card.dart`

```dart
enum QuestionCategory {
  discovery,
  clarification,
  modeSelection;

  String get displayName {
    switch (this) {
      case QuestionCategory.discovery:
        return 'Discovery Question';
      case QuestionCategory.clarification:
        return 'Clarification';
      case QuestionCategory.modeSelection:
        return 'Select Mode';
    }
  }

  IconData get icon {
    switch (this) {
      case QuestionCategory.discovery:
        return Icons.explore;
      case QuestionCategory.clarification:
        return Icons.help_outline;
      case QuestionCategory.modeSelection:
        return Icons.settings;
    }
  }
}

class QuestionOption {
  final String id;
  final String label;
  final String? description;
  final bool isDefault;

  const QuestionOption({
    required this.id,
    required this.label,
    this.description,
    this.isDefault = false,
  });

  factory QuestionOption.fromJson(Map<String, dynamic> json) {
    return QuestionOption(
      id: json['id'] as String,
      label: json['label'] as String,
      description: json['description'] as String?,
      isDefault: json['is_default'] as bool? ?? false,
    );
  }
}

class QuestionCardData {
  final String questionId;
  final String questionText;
  final String? rationale;
  final QuestionCategory category;
  final List<QuestionOption> options;
  final bool allowFreeText;
  final String freeTextPlaceholder;
  final int maxSelections;

  const QuestionCardData({
    required this.questionId,
    required this.questionText,
    required this.category,
    required this.options,
    this.rationale,
    this.allowFreeText = true,
    this.freeTextPlaceholder = 'Or type your own answer...',
    this.maxSelections = 1,
  });

  factory QuestionCardData.fromJson(Map<String, dynamic> json) {
    return QuestionCardData(
      questionId: json['question_id'] as String,
      questionText: json['question_text'] as String,
      rationale: json['rationale'] as String?,
      category: QuestionCategory.values.firstWhere(
        (c) => c.name == json['category'],
        orElse: () => QuestionCategory.discovery,
      ),
      options: (json['options'] as List)
          .map((o) => QuestionOption.fromJson(o as Map<String, dynamic>))
          .toList(),
      allowFreeText: json['allow_free_text'] as bool? ?? true,
      freeTextPlaceholder: json['free_text_placeholder'] as String? ?? 'Or type your own answer...',
      maxSelections: json['max_selections'] as int? ?? 1,
    );
  }
}
```

### Integration with Message List

**File:** `frontend/lib/screens/conversation/conversation_screen.dart`

In `_buildMessageList()`, add handling for question card items:

```dart
Widget _buildMessageList() {
  // ... existing logic

  return ListView.builder(
    itemCount: itemCount,
    itemBuilder: (context, index) {
      final item = items[index];

      if (item is QuestionCardItem) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: QuestionCard(
            data: item.data,
            isCollapsed: item.isAnswered,
            selectedOptionId: item.selectedOptionId,
            customResponse: item.customResponse,
            onOptionSelected: (optionId) => _handleOptionSelected(item, optionId),
            onCustomSubmit: (text) => _handleCustomSubmit(item, text),
          ),
        );
      }

      // ... existing message handling
    },
  );
}
```

---

## Acceptance Criteria

### Widget Structure
- [ ] `QuestionCard` widget created at `frontend/lib/screens/conversation/widgets/question_card.dart`
- [ ] `QuestionCardData` model created at `frontend/lib/models/question_card.dart`
- [ ] Widget accepts all required props: data, callbacks, state flags

### Active State Rendering
- [ ] Card displays with distinct background color (surfaceContainerHighest)
- [ ] Category badge with icon shown in header
- [ ] Question text rendered in bold, larger font
- [ ] Rationale text rendered below question (when present)
- [ ] Options rendered as full-width tappable buttons
- [ ] Default option (is_default: true) shows star indicator
- [ ] Option descriptions shown as subtitle text (when present)
- [ ] Embedded text input shown at bottom with placeholder
- [ ] Send button visible next to text input

### Collapsed State Rendering
- [ ] Card shrinks to compact size after response
- [ ] Shows checkmark icon, question text, and selected answer
- [ ] Custom responses shown in quotes
- [ ] Options and text input hidden

### Visual Integration
- [ ] Card fits naturally in conversation message list
- [ ] Padding and spacing consistent with other message types
- [ ] Dark mode support (colors adapt to theme)
- [ ] Responsive width (works on mobile and desktop)

### SSE Event Handling
- [ ] `question_card` event type recognized in SSE stream parser
- [ ] Event data correctly deserialized to `QuestionCardData`
- [ ] Card rendered in message list at correct position (end of AI response)

---

## Technical References

**Frontend:**
- `frontend/lib/screens/conversation/conversation_screen.dart` — message list builder
- `frontend/lib/screens/conversation/widgets/` — existing widget patterns
- `frontend/lib/models/` — existing model patterns
- `frontend/lib/services/ai_service.dart` — SSE event parsing

**Design Patterns:**
- `ArtifactCard` widget for card styling reference
- `StreamingMessage` widget for inline content reference
- `ChatInput` widget for text input styling reference

---

*Created: 2026-02-05*
*Part of UX-004 Question Card UI feature*
