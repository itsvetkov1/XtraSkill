# UX-005: Backend Structured Question Output

**Priority:** High
**Status:** Open
**Component:** Backend / AI Service
**Related:** UX-004 (Parent), UX-006 (Rendering), UX-007 (Interaction)
**Implementation Order:** 1 of 3 (backend first, then frontend rendering, then interaction)

---

## User Story

As the frontend application,
I need to receive structured question data via SSE events,
so that I can render interactive question cards instead of parsing plain text.

---

## Problem

The AI currently outputs questions with options as plain text formatted like:

```
What is the primary business objective?

Understanding your main goal ensures all features align with business priorities.

For example:
(A) Increase revenue through new customer acquisition
(B) Improve operational efficiency and reduce costs
(C) Enhance customer retention and lifetime value
```

This format requires fragile frontend parsing to detect and extract questions, options, and context. Any variation in AI output breaks the detection.

---

## Solution

### New SSE Event Type: `question_card`

When the AI is in Discovery or Clarification mode and outputs a structured question, emit a dedicated SSE event instead of plain `text_delta` events.

**Event Structure:**

```json
{
  "event": "question_card",
  "data": {
    "question_id": "q_abc123",
    "question_text": "What is the primary business objective?",
    "rationale": "Understanding your main goal ensures all features align with business priorities.",
    "category": "discovery",
    "options": [
      {
        "id": "opt_1",
        "label": "Increase revenue through new customer acquisition",
        "description": "Focus on growing customer base and market share",
        "is_default": false
      },
      {
        "id": "opt_2",
        "label": "Improve operational efficiency and reduce costs",
        "description": "Streamline processes and eliminate waste",
        "is_default": true
      },
      {
        "id": "opt_3",
        "label": "Enhance customer retention and lifetime value",
        "description": "Keep existing customers engaged and spending",
        "is_default": false
      }
    ],
    "allow_free_text": true,
    "free_text_placeholder": "Or type your own answer...",
    "max_selections": 1,
    "metadata": {
      "discovery_phase": "business_objectives",
      "question_sequence": 1
    }
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_id` | string | Yes | Unique identifier for tracking/analytics |
| `question_text` | string | Yes | The main question to display |
| `rationale` | string | No | One-sentence explanation of why this matters |
| `category` | enum | Yes | `discovery` \| `clarification` \| `mode_selection` |
| `options` | array | Yes | List of selectable options (min 2, max 6) |
| `options[].id` | string | Yes | Unique option identifier for tracking |
| `options[].label` | string | Yes | Display text for the option button |
| `options[].description` | string | No | Tooltip/subtitle explaining the option |
| `options[].is_default` | boolean | No | Whether this is the suggested/recommended option |
| `allow_free_text` | boolean | Yes | Whether to show embedded text input (always `true` per requirements) |
| `free_text_placeholder` | string | No | Placeholder text for free-text input |
| `max_selections` | integer | No | Maximum options selectable (1 for single-select, >1 for multi-select) |
| `metadata` | object | No | Additional tracking data (phase, sequence, etc.) |

### Detection Strategy

Modify the AI service to detect question+options patterns in the model output:

**File:** `backend/app/services/ai_service.py`

**Option A: Post-processing detection (recommended for v1)**

After receiving complete model output, scan for question patterns:
1. Sentence ending with `?`
2. Followed by options formatted as `(A)`, `(B)`, `(C)` or numbered list
3. Extract question, rationale (sentence before question), and options

```python
def detect_question_card(text: str) -> Optional[QuestionCardEvent]:
    """Detect question+options pattern and return structured event."""
    # Regex pattern for question with lettered options
    pattern = r'(.+\?)\s*\n\n(.+?)\n\n(?:For example:|Options:)?\s*\n((?:\([A-Z]\).+\n?)+)'
    match = re.search(pattern, text, re.MULTILINE)
    if match:
        question = match.group(1).strip()
        rationale = match.group(2).strip()
        options_text = match.group(3)
        options = parse_options(options_text)
        return QuestionCardEvent(
            question_id=generate_id(),
            question_text=question,
            rationale=rationale,
            category=detect_category(),  # Based on current mode
            options=options,
            allow_free_text=True,
            max_selections=1
        )
    return None
```

**Option B: Structured tool output (recommended for v2)**

Define a `present_question` tool that the AI calls when asking questions:

```python
PRESENT_QUESTION_TOOL = {
    "name": "present_question",
    "description": "Present a question to the user with selectable options. Use this instead of plain text when asking discovery or clarification questions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "rationale": {"type": "string"},
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
        },
        "required": ["question", "options"]
    }
}
```

### Event Emission

**File:** `backend/app/routes/conversations.py`

In the SSE event generator, when a question card is detected:

```python
async def event_generator():
    accumulated_text = ""

    async for event in ai_stream:
        if event["event"] == "text_delta":
            accumulated_text += event["data"]["text"]
            # Don't yield text_delta yet - buffer it

        elif event["event"] == "message_complete":
            # Check if accumulated text contains a question card
            question_card = detect_question_card(accumulated_text)

            if question_card:
                # Yield question card event instead of text
                yield {
                    "event": "question_card",
                    "data": question_card.dict()
                }
            else:
                # Yield buffered text as normal
                yield {
                    "event": "text_delta",
                    "data": {"text": accumulated_text}
                }

            yield event  # message_complete
```

### Triggering Conditions

Question cards are emitted ONLY when:
1. AI is in **Discovery** or **Clarification** mode (check thread mode)
2. Output contains structured question+options pattern
3. Streaming has completed (card appears at end of response)

Regular chat messages, artifact generation, and other modes continue using `text_delta` events.

---

## Acceptance Criteria

### Event Structure
- [ ] New SSE event type `question_card` is defined and documented
- [ ] Event includes all required fields: `question_id`, `question_text`, `category`, `options`, `allow_free_text`
- [ ] Options array includes `id`, `label` for each option
- [ ] Optional fields supported: `rationale`, `description`, `is_default`, `max_selections`, `metadata`

### Detection
- [ ] Questions with `(A)/(B)/(C)` format are detected and converted to structured events
- [ ] Questions with numbered options `1. / 2. / 3.` are also detected
- [ ] Detection only triggers in Discovery or Clarification mode
- [ ] Regular chat messages (without options pattern) are unaffected

### Event Emission
- [ ] `question_card` event emitted after streaming completes (not mid-stream)
- [ ] When question card is detected, `text_delta` events for that content are suppressed
- [ ] `message_complete` event still emitted after `question_card`
- [ ] Multiple questions in one response each emit separate `question_card` events

### Edge Cases
- [ ] Malformed option patterns fall back to plain text rendering
- [ ] Empty options array is rejected (minimum 2 options required)
- [ ] Option labels exceeding 200 characters are truncated
- [ ] `question_id` is unique per question (UUID or similar)

---

## Technical References

**Backend:**
- `backend/app/routes/conversations.py:85-211` — SSE event generator
- `backend/app/services/ai_service.py:755-882` — AIService.stream_chat()
- `backend/app/models.py` — Thread model with mode field

**Existing Patterns:**
- `artifact_created` event structure for reference
- `tool_executing` event structure for reference

---

## Data Models

### QuestionCardEvent (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class QuestionCategory(str, Enum):
    DISCOVERY = "discovery"
    CLARIFICATION = "clarification"
    MODE_SELECTION = "mode_selection"

class QuestionOption(BaseModel):
    id: str = Field(..., description="Unique option identifier")
    label: str = Field(..., max_length=200, description="Display text")
    description: Optional[str] = Field(None, max_length=500, description="Tooltip text")
    is_default: bool = Field(False, description="Suggested option flag")

class QuestionCardEvent(BaseModel):
    question_id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., max_length=1000, description="The question")
    rationale: Optional[str] = Field(None, max_length=500, description="Why this matters")
    category: QuestionCategory
    options: List[QuestionOption] = Field(..., min_items=2, max_items=6)
    allow_free_text: bool = Field(True, description="Show embedded text input")
    free_text_placeholder: Optional[str] = Field("Or type your own answer...")
    max_selections: int = Field(1, ge=1, le=6, description="Max selectable options")
    metadata: Optional[dict] = Field(None, description="Additional tracking data")
```

---

## Testing Strategy

1. **Unit tests:** Pattern detection with various question formats
2. **Integration tests:** Full SSE stream with question card emission
3. **Edge case tests:** Malformed patterns, missing options, mode filtering

---

*Created: 2026-02-05*
*Part of UX-004 Question Card UI feature*
