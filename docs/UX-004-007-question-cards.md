# UX-004-007: Question Cards Epic

## Status: PARTIAL (Backend Complete, Frontend Pending)

### What's Implemented (Backend)

1. **SSE Events for Questions** — AI questions stream via `text_delta` events
2. **Question Metadata in System Prompt** — Each question includes:
   - Clear, specific question
   - One-sentence rationale  
   - Three suggested answer options
3. **Discovery Protocol** — One-question-at-a-time flow enforced

### What's Needed (Frontend)

1. **Question Card Widget** — Parse question from text, render as card
2. **Tap-to-Answer** — Click option → sends as user message
3. **Progress Indicator** — Show question number (e.g., "Question 3 of 7")

### Technical Notes

Backend already delivers questions with this structure:
```
**Question:** [question text]
**Why:** [rationale]
1. [option A]
2. [option B]  
3. [option C]
```

Frontend needs to:
1. Detect question pattern in incoming text
2. Render as interactive card
3. Send selected option as chat message

### Related Code

- `ai_service.py` — Question generation rules
- `conversations.py` — SSE streaming endpoint
