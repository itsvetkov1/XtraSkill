# UX-004: Question Card UI for AI Discovery Questions

**Priority:** High
**Status:** Open
**Component:** Frontend + Backend / Conversation UI
**Related:** UX-005 (Backend), UX-006 (Card Rendering), UX-007 (Interaction)
**Type:** Epic / Parent Story

---

## User Story

As a business analyst using the AI assistant,
I want AI discovery questions to appear in visually distinct cards with tappable option buttons,
so that I can quickly respond without typing and never miss important questions in the conversation flow.

---

## Problem

Currently, AI questions during discovery/clarification modes blend into the regular conversation stream as plain text. This causes three issues:

1. **Visibility:** Users miss or overlook AI questions because they look identical to regular AI messages
2. **Efficiency:** Users must type responses even when predefined options like "(A) Option one (B) Option two" would suffice
3. **Professionalism:** Text-based interaction feels less guided and polished for business analyst workflows

---

## Solution Overview

Introduce a **Question Card UI** that renders AI discovery/clarification questions as visually distinct inline cards with:

- Tappable option buttons for quick selection
- Embedded free-text input field as fallback
- Collapsed summary state after response
- Rich metadata for analytics and smart defaults

### Visual Design

```
┌─────────────────────────────────────────────────────┐
│  What is the primary business objective?            │
│                                                     │
│  Understanding your main goal ensures all features  │
│  align with business priorities.                    │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  Increase revenue through acquisition       │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │  Improve operational efficiency             │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │  Enhance customer retention                 │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────┐  ┌──────┐    │
│  │  Or type your own answer...     │  │  ➤  │    │
│  └─────────────────────────────────┘  └──────┘    │
└─────────────────────────────────────────────────────┘
```

### After Selection (Collapsed State)

```
┌─────────────────────────────────────────────────────┐
│  What is the primary business objective?            │
│  ✓ Improve operational efficiency                   │
└─────────────────────────────────────────────────────┘
```

---

## Scope

### In Scope

- Backend structured question output with rich metadata
- Frontend question card widget rendering
- Option button tap-to-send interaction
- Embedded free-text input with Enter and button send
- Card collapse to summary after response
- Question cards appear only in Discovery/Clarification mode
- Cards render at end of AI response (after streaming completes)

### Out of Scope

- Voice input for responses
- Question card animations/transitions (keep simple initially)
- Analytics dashboard for option selection patterns
- A/B testing of option orderings

---

## Child Stories

| ID | Title | Component | Description |
|----|-------|-----------|-------------|
| [UX-005](UX-005_question-card-backend.md) | Backend Structured Question Output | Backend | SSE event with question metadata |
| [UX-006](UX-006_question-card-rendering.md) | Frontend Question Card Rendering | Frontend | Card widget and styling |
| [UX-007](UX-007_question-card-interaction.md) | Question Card Interaction | Frontend | Tap, type, collapse behaviors |

---

## Success Metrics

- Users respond to AI questions 50%+ faster (tap vs type)
- Zero missed questions in discovery sessions (visibility)
- User satisfaction improvement in guided discovery feel

---

## Technical Approach

1. **Backend:** Modify AI service to detect question+options pattern and emit structured SSE event (`question_card`) with rich metadata instead of plain text
2. **Frontend:** New `QuestionCard` widget renders the structured event as an interactive card in the message list
3. **Interaction:** Option taps send immediately; free-text supports Enter or button; card collapses after response

---

*Created: 2026-02-05*
*Discovery completed with systematic requirements gathering*
