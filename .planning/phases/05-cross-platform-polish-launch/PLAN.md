# Business-Analyst Skill Integration Plan

## Phase Goal

Integrate the `/business-analyst` skill into the BA Assistant backend, enabling the AI to conduct structured one-question-at-a-time discovery and generate comprehensive Business Requirements Documents (BRDs).

## Approach

**Selected: Approach A - Expanded System Prompt**

Transform the 2,143 lines of skill instructions into an optimized ~2,300 token system prompt that preserves core methodology. No new dependencies, minimal code changes, works with existing architecture.

---

## Tasks

### Task 1: Create Condensed Skill Prompt Module

**File:** `backend/app/prompts/business_analyst_skill.py`

**Content:**
- `MODE_DETECTION_PROMPT` - Meeting vs Document Refinement mode detection
- `CORE_BA_BEHAVIOR_PROMPT` - One-question protocol, zero-assumption, cumulative understanding
- `DISCOVERY_FRAMEWORK_PROMPT` - Priority sequence (objective → personas → flows → etc.)
- `TONE_GUIDELINES_PROMPT` - DO/DON'T examples, consultative language
- `ERROR_PROTOCOLS_PROMPT` - Handling unclear answers, technical redirects
- `TOOL_INSTRUCTIONS_PROMPT` - When to search documents, when to generate BRD
- `BRD_TEMPLATE_PROMPT` - Section structure for generated BRDs

**Deliverable:** Python module with string constants that can be combined into final system prompt.

**Acceptance Criteria:**
- [ ] Total combined prompt is under 3,000 tokens
- [ ] All critical behaviors from SKILL.md are captured
- [ ] Format supports easy editing and iteration

---

### Task 2: Add `generate_brd` Tool Definition

**File:** `backend/app/services/ai_service.py`

**Add tool:**
```python
GENERATE_BRD_TOOL = {
    "name": "generate_brd",
    "description": """Generate comprehensive Business Requirements Document.

USE THIS TOOL WHEN:
- User says "create the documentation", "generate the BRD", "ready for deliverables"
- Sufficient discovery has occurred (objectives, personas, flows, metrics captured)

BEFORE USING:
- Run pre-flight validation (check critical info captured)
- Use search_documents to gather any additional project context
- Review full conversation for ALL requirements discussed

OUTPUT FORMAT:
- Follow BRD template structure exactly
- Include all sections even if minimal info available
- Note assumptions clearly in Assumptions section
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "executive_summary": {"type": "string"},
            "business_context": {"type": "string"},
            "primary_objective": {"type": "string"},
            "secondary_objectives": {"type": "array", "items": {"type": "string"}},
            "user_personas": {"type": "array", "items": {"type": "object"}},
            "user_flows": {"type": "array", "items": {"type": "object"}},
            "functional_requirements": {"type": "object"},
            "business_processes": {"type": "array", "items": {"type": "object"}},
            "stakeholders": {"type": "array", "items": {"type": "object"}},
            "success_metrics": {"type": "array", "items": {"type": "object"}},
            "regulatory_requirements": {"type": "string"},
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "object"}},
            "next_steps": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["executive_summary", "primary_objective", "user_personas"]
    }
}
```

**Acceptance Criteria:**
- [ ] Tool schema matches BRD template structure
- [ ] Required fields reflect minimum viable BRD
- [ ] Tool description includes pre-flight validation reminder

---

### Task 3: Implement BRD Generation Logic

**File:** `backend/app/services/ai_service.py`

**Modify `execute_tool` method:**

```python
elif tool_name == "generate_brd":
    # Convert structured input to markdown BRD
    brd_markdown = self._format_brd_markdown(tool_input)

    # Save as artifact with type "requirements_doc"
    artifact = Artifact(
        thread_id=thread_id,
        artifact_type=ArtifactType.requirements_doc,
        title=f"Business Requirements Document - {tool_input.get('title', 'Untitled')}",
        content_markdown=brd_markdown
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    return (
        f"BRD generated successfully: '{artifact.title}' (ID: {artifact.id}). "
        "Document is ready for export as PDF, Word, or Markdown.",
        {"id": artifact.id, "artifact_type": "requirements_doc", "title": artifact.title}
    )
```

**Add helper method:**
```python
def _format_brd_markdown(self, data: dict) -> str:
    """Format structured BRD data into markdown document."""
    # Implementation follows brd-template.md structure
```

**Acceptance Criteria:**
- [ ] Generated BRD follows template structure from `brd-template.md`
- [ ] All sections properly formatted with headers
- [ ] Stakeholder table renders correctly
- [ ] Success metrics table renders correctly

---

### Task 4: Update System Prompt in AI Service

**File:** `backend/app/services/ai_service.py`

**Replace current `SYSTEM_PROMPT` with skill-enhanced version:**

```python
from app.prompts.business_analyst_skill import (
    MODE_DETECTION_PROMPT,
    CORE_BA_BEHAVIOR_PROMPT,
    DISCOVERY_FRAMEWORK_PROMPT,
    TONE_GUIDELINES_PROMPT,
    ERROR_PROTOCOLS_PROMPT,
    TOOL_INSTRUCTIONS_PROMPT,
    BRD_TEMPLATE_PROMPT
)

SYSTEM_PROMPT = f"""You are a Business Analyst AI assistant specializing in systematic requirements discovery and BRD generation.

{MODE_DETECTION_PROMPT}

{CORE_BA_BEHAVIOR_PROMPT}

{DISCOVERY_FRAMEWORK_PROMPT}

{TONE_GUIDELINES_PROMPT}

{ERROR_PROTOCOLS_PROMPT}

{TOOL_INSTRUCTIONS_PROMPT}

{BRD_TEMPLATE_PROMPT}
"""
```

**Acceptance Criteria:**
- [ ] System prompt includes all skill components
- [ ] Total token count verified under budget
- [ ] Import paths correct and modules load

---

### Task 5: Add Session Mode Detection

**At conversation start, Claude should ask:**

> "Which mode: (A) Meeting Mode for conducting live discovery with a customer, or (B) Document Refinement Mode for modifying an existing Business Requirements Document?"

**Implementation:** Include in `MODE_DETECTION_PROMPT`:

```python
MODE_DETECTION_PROMPT = """
## Session Initialization

At the START of every new conversation (first message), ask:

"Which mode would you like to use?
(A) Meeting Mode - Conduct live discovery with a customer using one-question-at-a-time methodology
(B) Document Refinement Mode - Modify or enhance an existing Business Requirements Document"

Wait for user selection before proceeding.

If Meeting Mode: Use one-question discovery protocol
If Document Refinement Mode: Request existing BRD content, ask what needs modification
"""
```

**Acceptance Criteria:**
- [ ] Claude asks mode question on first message
- [ ] Claude adapts behavior based on mode selection
- [ ] Mode persists throughout conversation

---

### Task 6: Create Integration Tests

**File:** `backend/tests/test_ba_skill_integration.py`

**Test cases:**

1. **Mode Detection Test**
   - Send empty thread, verify mode question asked
   - Select Meeting Mode, verify one-question response
   - Select Document Mode, verify BRD request

2. **One-Question Protocol Test**
   - After mode selection, verify response contains exactly one question
   - Verify question includes rationale
   - Verify question includes 3 options

3. **Zero-Assumption Test**
   - Send message with ambiguous term ("seamless experience")
   - Verify Claude asks for clarification with specific interpretations

4. **Technical Redirect Test**
   - Send message asking "Should we use React or Vue?"
   - Verify Claude redirects to business focus

5. **BRD Generation Test**
   - Simulate discovery conversation
   - Send "generate the BRD"
   - Verify artifact_created event
   - Verify BRD includes all required sections

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Tests cover critical skill behaviors
- [ ] Tests use mock Claude responses where needed

---

### Task 7: Manual Validation

**Validation scenarios:**

1. **Complete Discovery Session**
   - Start Meeting Mode
   - Answer 8-10 questions
   - Request BRD generation
   - Verify BRD completeness

2. **Document Refinement Session**
   - Start Document Mode
   - Provide existing BRD
   - Request modifications
   - Verify changes applied

3. **Edge Cases**
   - Vague customer answers (should clarify)
   - Technical tangents (should redirect)
   - Early BRD request (should flag incomplete areas)

**Acceptance Criteria:**
- [ ] Discovery feels systematic and thorough
- [ ] One question at a time is maintained
- [ ] Generated BRD matches template structure

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/prompts/business_analyst_skill.py` | NEW | Skill prompt components |
| `backend/app/services/ai_service.py` | MODIFY | Add generate_brd tool, update system prompt |
| `backend/tests/test_ba_skill_integration.py` | NEW | Integration tests |

---

## Execution Order

1. Task 1: Create prompt module (foundation)
2. Task 2: Add tool definition (enables Task 3)
3. Task 3: Implement BRD generation (uses Task 2)
4. Task 4: Update system prompt (uses Task 1)
5. Task 5: Mode detection (part of Task 4)
6. Task 6: Integration tests (validates all above)
7. Task 7: Manual validation (final verification)

---

## Rollback Plan

If skill integration causes issues:

1. Revert `ai_service.py` to previous SYSTEM_PROMPT
2. Remove `generate_brd` tool from tools list
3. Keep `business_analyst_skill.py` for future iteration

---

## Success Criteria

- [ ] Claude asks mode question at session start
- [ ] Claude maintains one-question-at-a-time protocol
- [ ] Claude clarifies ambiguous terms before proceeding
- [ ] Claude redirects technical discussions to business focus
- [ ] Generated BRDs follow template structure with all sections
- [ ] All integration tests pass
- [ ] Manual validation scenarios complete successfully
