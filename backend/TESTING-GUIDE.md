# System Prompt Testing Guide

Quick manual testing guide for the new Business Analyst system prompt.

## Prerequisites

1. Backend running: `python -m uvicorn app.main:app --reload`
2. Frontend running (optional): `flutter run -d chrome`
3. Or use API client (Postman, Thunder Client, curl)

---

## Automated Tests

```bash
cd backend
python test_system_prompt.py
```

This will test all 6 critical behaviors automatically.

---

## Manual Testing (via Frontend or API)

### Test 1: Mode Detection ✓
**User Message:** "Help me gather requirements for a customer"

**Expected Response:**
- Should ask: "Which mode: (A) Meeting Mode ... or (B) Document Refinement Mode..."
- Must have (A) and (B) options
- Should NOT start asking business questions immediately

**Pass Criteria:**
- ✓ Asks for mode selection
- ✓ Provides two clear options
- ✓ Waits for user response

---

### Test 2: One-Question-at-a-Time ✓
**User Message:** "Meeting Mode"

**Expected Response:**
- ONE question only (check for single "?" mark)
- Question includes rationale (why it matters)
- Three options provided: (A), (B), (C)
- Example: "What is the primary business objective...? This ensures... For example: (A)..., (B)..., or (C)..."

**Pass Criteria:**
- ✓ Exactly one question
- ✓ Has rationale sentence
- ✓ Has three labeled options

---

### Test 3: Zero-Assumption Protocol ✓
**User Message:** "We need a seamless experience"

**Expected Response:**
- Should say "I want to ensure I understand correctly" or similar
- Should ask: "when you say 'seamless experience,' do you mean..."
- Should provide 2-3 specific interpretations with (A), (B), (C) options
- Should NOT assume meaning and move on

**Pass Criteria:**
- ✓ Asks for clarification of "seamless"
- ✓ Provides multiple concrete interpretations
- ✓ Does not assume meaning

---

### Test 4: Technical Boundary Enforcement ✓
**User Message:** "Should we use React or Vue for the frontend?"

**Expected Response:**
- Should acknowledge: "That's an important consideration for our technical team"
- Should redirect: "For now, let's focus on what the product needs to accomplish from a business perspective"
- Should ask a BUSINESS question (NOT engage in React vs Vue discussion)
- Should NOT say "React is better because..." or compare technologies

**Pass Criteria:**
- ✓ Acknowledges but doesn't engage technically
- ✓ Redirects to business focus
- ✓ Asks business-focused follow-up question

---

### Test 5: Tool Usage - search_documents ✓
**User Message:** "The customer mentioned compliance requirements in their documents"

**Expected Response:**
- Should automatically use search_documents tool
- Look for loading indicator: "Searching project documents..."
- Response should reference document findings (if any documents exist)

**Pass Criteria:**
- ✓ Calls search_documents tool automatically
- ✓ References results in response (or notes no documents found)

**Note:** If no documents uploaded to test project, tool may return "No documents found" - this is correct behavior.

---

### Test 6: BRD Generation with Validation ✓

**Setup:** Answer a few discovery questions first:
1. User: "The objective is to improve sales efficiency"
2. User: "Sales teams will use it"
3. User: "They need to capture customer requirements faster"

**User Message:** "Generate the BRD"

**Expected Response (Option A - Has enough info):**
- Should generate comprehensive BRD using save_artifact tool
- Look for loading indicator: "Generating artifact..."
- Should receive notification: "Artifact saved successfully"
- BRD should have all 13 sections (check in Artifacts list)

**Expected Response (Option B - Missing info):**
- Should flag gaps: "Before generating the BRD, I need to clarify these essential points..."
- Should list missing information (personas, flows, metrics, etc.)
- Should ask 2-3 targeted questions to fill gaps
- Should NOT generate incomplete BRD

**Pass Criteria:**
- ✓ Either generates complete BRD OR flags missing information
- ✓ Does not generate BRD with placeholder sections
- ✓ Pre-flight validation executed

---

## Quick Smoke Test (5 minutes)

Run through this sequence to verify all behaviors:

```
1. User: "Help me gather requirements"
   → Should ask for mode

2. User: "Meeting Mode"
   → Should ask ONE question with 3 options

3. User: "We need it to be user-friendly"
   → Should clarify what "user-friendly" means

4. User: "Should we use React?"
   → Should redirect to business focus

5. User: "Generate the BRD"
   → Should flag missing info or generate BRD
```

---

## Regression Checks

### Things that SHOULD STILL WORK:
- ✓ Streaming responses (text appears incrementally)
- ✓ Multi-turn conversation (maintains context)
- ✓ Database persistence (messages saved)
- ✓ OAuth authentication
- ✓ Document upload and search
- ✓ Artifact export (PDF, Word, Markdown)

### Things that CHANGED (expected):
- ✗ No longer asks about edge cases unprompted (new focus is business requirements)
- ✗ Asks for mode selection at conversation start (new behavior)
- ✗ Strictly one question at a time (stricter than before)
- ✗ Always clarifies ambiguous terms (zero-assumption protocol)

---

## API Testing with curl

```bash
# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'

# Create thread (use project_id from above)
curl -X POST http://localhost:8000/api/projects/{project_id}/threads \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Thread"}'

# Send message (use project_id and thread_id)
curl -X POST http://localhost:8000/api/projects/{project_id}/threads/{thread_id}/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Help me gather requirements"}' \
  --no-buffer

# Watch streaming response
```

---

## Troubleshooting

### Issue: Backend returns 500 error
**Solution:** Check backend logs for Anthropic API errors. Verify API key is set in `.env`

### Issue: Response is generic, doesn't follow new prompt
**Solution:** Verify system prompt was updated in `ai_service.py` lines 17+. Restart backend server.

### Issue: Test script fails to connect
**Solution:** Ensure backend running on port 8000. Check `API_BASE_URL` in test script.

### Issue: Tools not being called
**Solution:** Check that DOCUMENT_SEARCH_TOOL and SAVE_ARTIFACT_TOOL are still defined correctly in `ai_service.py` and passed to `self.tools`

---

## Success Criteria Summary

| Test | Behavior | Pass? |
|------|----------|-------|
| Mode Detection | Asks for Meeting vs Document Refinement mode | ☐ |
| One-Question-at-a-Time | Single question with rationale and 3 options | ☐ |
| Zero-Assumption | Clarifies ambiguous terms with interpretations | ☐ |
| Technical Boundary | Redirects technical talk to business focus | ☐ |
| Tool: search_documents | Autonomously searches when mentioned | ☐ |
| Tool: save_artifact | Validates info before generating BRD | ☐ |

**All 6 tests must pass** for the system prompt to be considered production-ready.

---

## Next Steps After Testing

If all tests pass:
1. Update PROJECT.md with new system prompt details
2. Update phase 04.1 documentation (Agent SDK conclusion)
3. Update ROADMAP.md to reflect completed Phase 4.1
4. Consider adding system prompt testing to CI/CD pipeline

If tests fail:
1. Review test output and identify specific failure
2. Check SYSTEM-PROMPT-business-analyst.md for guidance
3. Adjust system prompt XML if needed
4. Re-test until all pass
