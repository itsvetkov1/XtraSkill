# Claude Development Rules

This document defines rules and conventions for Claude Code when working on this project.

---

## Git & Version Control

### Rule: Commit & Push on Completed Phases/Milestones Only

**CRITICAL:** Only commit and push when completing a phase or milestone, NOT on every individual change.

**Why:**
- Keeps git history clean with meaningful commits
- Each commit represents a complete unit of work
- User tests on multiple machines - all completed work must be available on remote

**When to Commit:**
- ✅ After completing a GSD phase (all tasks done, verification passed)
- ✅ After completing a milestone (all phases done)
- ✅ After completing a bug fix session (investigation + fix + testing)
- ✅ After completing documentation for a session
- ❌ NOT after every individual file change
- ❌ NOT after each small task within a phase

**Implementation:**
```bash
# After completing a phase or milestone:
git add <all-related-files>
git commit -m "feat(phase-XX): complete phase description"
git push origin master
```

**What to push:**
- ✅ All code changes (frontend, backend)
- ✅ All documentation updates
- ✅ All planning documents (.planning/)
- ✅ All configuration changes
- ✅ All test files

**What NOT to push:**
- ❌ `.claude/settings.local.json` (user-specific settings)
- ❌ `*.log` files (runtime logs)
- ❌ Temporary test scripts (`test_*.py`, `test_*.sh`)
- ❌ Local environment files (`.env.local`)
- ❌ `node_modules/`, `venv/`, build artifacts

**Verification:**
```bash
git status --porcelain  # Should be clean or only show excluded files
git log --oneline -5    # Verify commits pushed
```

---

## Phase Execution (GSD Workflow)

### Rule: Single Commit Per Phase Completion

When executing GSD phases, create ONE commit when the phase is complete:

1. **During execution:** Make changes to files but do NOT commit
2. **On phase completion:** Stage ALL phase-related files and commit together
3. **Commit includes:** Code changes, SUMMARY.md, ROADMAP.md updates, VERIFICATION.md

**Commit format:**
```bash
git add .planning/phases/XX-*/ backend/ frontend/  # All related files
git commit -m "feat(XX): complete phase - brief description"
git push origin master
```

**Never leave completed phase work unpushed** - user needs to see finished work on other machines.

---

## Bug Fixes

### Rule: Complete Bug Fix Session, Then Commit

When user reports a bug:

1. **Acknowledge** the bug is real (don't assume user error first)
2. **Investigate** the root cause thoroughly
3. **Fix** all related issues (may involve multiple files)
4. **Document** the session in `.planning/SESSION_*.md`
5. **Update** testing guides if affected
6. **Single commit** with all fix-related changes
7. **Push** when complete

**Example:**
```bash
# After completing entire bug fix session:
git add backend/app/services/agent_service.py \
        .claude/business-analyst/SKILL.md \
        .planning/SESSION_2026-02-03_BRD_FIX.md
git commit -m "fix(agent): prevent infinite artifact generation loop"
git push origin master
```

**Note:** Don't make separate commits for code fix and documentation - combine them into one meaningful commit.

---

## Documentation

### Rule: Keep Testing Guides Current

When code changes affect testing:

1. Update relevant testing guides (TESTING_GUIDE.md, THEME_TESTING_GUIDE.md)
2. Add notes about bug fixes with commit hashes
3. Remove misleading troubleshooting sections after bugs are fixed
4. Include documentation updates in the same commit as the code change

**Documentation should be bundled with its related code changes, not committed separately.**

---

## Multi-Machine Testing

### Rule: Assume User Tests on Different Machines

**Context:** User tests on multiple PCs, may not be on the same machine where changes were made.

**Implications:**
- All changes must be in remote repository
- Testing guides must be complete and self-contained
- Backend AND frontend must be documented for setup
- No assumptions about local state or cached dependencies

**Required in every testing guide:**
```markdown
## Quick Setup (Another PC)

1. Clone repository
2. Backend setup (venv, pip install, run.py)
3. Frontend setup (flutter pub get, flutter run)
4. Testing steps (numbered, specific)
```

---

## Commit Message Format

Use conventional commits format:

```
<type>(<scope>): <description>

[optional body]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

**Scopes:**
- Phase-plan format: `06-01`, `06-02`
- Component: `auth`, `theme`, `navigation`
- Area: `frontend`, `backend`, `planning`

**Examples:**
```bash
feat(06-01): create ThemeProvider with immediate persistence
fix(06-02): prevent router recreation causing logout
docs: update testing guide with bug fix info
chore(06-01): add shared_preferences dependency
```

---

## File Exclusions

Never commit these files (already in .gitignore, but worth noting):

```
# User-specific
.claude/settings.local.json

# Logs
*.log
backend.log
backend_*.log

# Temporary test files
test_*.py
test_*.sh
test_*.html
test_document.txt

# Dependencies
node_modules/
venv/
.venv/

# Build artifacts
build/
dist/
*.pyc

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db

# Planning temporary files
.planning/.claude/
.planning/temp_*.xml
.planning/*_artifact_*.md
```

---

## Log Files

**Location:** `G:\git_repos\BA_assistant\backend\logs`

When investigating issues, check logs here:
- `backend/logs/app.log` — current log file (backend + frontend logs)
- `backend/logs/app.log.YYYY-MM-DD` — rotated daily logs (7-day retention)

Do NOT look for logs in root directory or other locations.

---

## Deferred Testing Workflow

### Rule: Collect Testing Points, Continue Development

**Context:** User may not be able to test immediately during development sessions. Don't block on manual testing checkpoints.

**Workflow:**

1. **During execution:** When a plan has `autonomous: false` (checkpoint), complete all tasks normally
2. **At checkpoint:** Instead of waiting for user approval, document all test cases in `.planning/TESTING-QUEUE.md`
3. **Continue execution:** Proceed with phase verification and completion
4. **Later testing:** User requests testing points with "show me what needs testing" or similar

**TESTING-QUEUE.md structure:**
```markdown
## Phase X: Phase Name

**Status:** Pending user testing
**Collected:** YYYY-MM-DD

### Test Environment Setup
[Setup steps]

### Test Cases

#### TC-XX-01: Test Name
1. Step 1
2. Step 2
3. **Expected:** [expected result]

### Results
| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-XX-01 | Pending | |
```

**When user asks for testing:**
- Point them to `.planning/TESTING-QUEUE.md`
- After testing, user reports results
- Update Results table with outcomes
- Create fix plans if issues found

**Benefits:**
- Development velocity maintained
- Testing requirements captured systematically
- User tests when convenient
- Clear traceability of what was tested

---

## User Story Management

### Rule: Maintain Stories in `/user_stories/`

**Location:** All user stories, bugs, and feature requests live in `/user_stories/`

**Structure:**
```
user_stories/
├── INDEX.md              # Master catalog of all stories
├── BACKLOG.md            # Future enhancements (parking lot)
├── BUG-XXX_short-name.md # Bug reports
├── US-XXX_short-name.md  # User stories (URL/navigation)
├── THREAD-XXX_*.md       # Conversation/thread features
├── DOC-XXX_*.md          # Document features or documentation tasks
└── [PREFIX]-XXX_*.md     # Other categorized stories
```

### Rule: Auto-Create Stories from Bug Reports

When user reports a bug or requests a feature:

1. **Create story file** in `/user_stories/` with appropriate prefix
2. **Use standard format:**
   ```markdown
   # [ID]: [Title]

   **Priority:** Critical | High | Medium | Low
   **Status:** Open | In Progress | Done | Wont Do
   **Component:** [Affected component]

   ---

   ## User Story
   As a [user], I want [goal], So that [benefit].

   ---

   ## Problem
   [Description of current behavior/issue]

   ---

   ## Acceptance Criteria
   - [ ] Criterion 1
   - [ ] Criterion 2

   ---

   ## Technical References
   - `path/to/relevant/file.dart`
   ```

3. **Update INDEX.md** - Add story to appropriate priority table
4. **Include in phase commit** - Story files are committed with related code changes

### Rule: Keep INDEX.md Current

After any story change:

1. Update status in INDEX.md table
2. Update summary counts at top
3. Include INDEX.md update in the phase/milestone commit

### Story ID Prefixes

| Prefix | Use For |
|--------|---------|
| BUG- | Bug reports with root cause analysis |
| US- | URL/Navigation/Router user stories |
| THREAD- | Conversation and thread features |
| NAV- | Navigation and breadcrumb features |
| DOC- | Document upload/view features OR documentation tasks |
| DELETE- | Deletion behavior |
| BUDGET- | Token budget and usage features |
| HOME- | Home screen features |
| SETTINGS- | Settings screen features |
| PROJECT- | Project management features |
| RESPONSIVE- | Responsive layout features |
| AUTH- | Authentication features |
| STATE- | State management |
| ENH- | Future enhancements (in BACKLOG.md) |

### Workflow Integration

When starting work on a story:
1. Update status to "In Progress" in INDEX.md
2. Reference story ID in commit messages: `feat(THREAD-001): add retry button`
3. When complete, update status to "Done"
4. Check off acceptance criteria in story file

---

## Regression Testing

### Rule: Create Test Plans for New Features

**CRITICAL:** When a new feature is created, add essential test cases to `REGRESSION_TESTS.md`.

**Why:** Maintain a living test suite that covers essential user flows. Tests serve as both verification and documentation of expected behavior.

**Test Case Format:**
```markdown
### TC-[AREA]-[NUMBER]: [Title]

**Pre-conditions:**
- [Required state before testing]

**Steps:**
1. [Action]
2. [Action]
3. [Action]

**Expected Result:**
- [What should happen]
```

**Principles:**
- **Essential flows only** — Test the happy path and critical edge cases, not every permutation
- **User-centric** — Write steps as user actions, not technical operations
- **Observable results** — Expected results must be visually verifiable
- **Minimal pre-conditions** — Tests should be independent when possible

**When to Add Tests:**
- After completing a feature (before marking phase complete)
- After fixing a bug (regression test for the fix)
- When user reports an issue (capture the flow that should work)

**Test Areas (Prefixes):**
| Prefix | Area |
|--------|------|
| AUTH | Authentication and login |
| PROJ | Projects (create, list, delete) |
| DOC | Documents (upload, view, delete) |
| CHAT | Chats and conversations |
| MSG | Messages (send, copy, retry) |
| NAV | Navigation and routing |
| SET | Settings |

**Maintenance:**
- Update tests when feature behavior changes
- Remove tests for removed features
- Mark tests as `[DEPRECATED]` before removal

**Location:** `/REGRESSION_TESTS.md`

---

## Session Management

### Token Refresh Behavior

OAuth tokens are automatically refreshed before expiration. The access token expires after 7 days (configurable via `ACCESS_TOKEN_EXPIRE_DAYS` in `backend/app/utils/jwt.py`). Users remain authenticated without interruption under normal conditions.

### File Upload Validation

Files are validated client-side before upload to provide immediate feedback.

**Validation rules:**
- Maximum file size: 10MB (configurable via \`_maxFileSizeBytes\` in document_upload_screen.dart)
- Supported formats: txt, md, xlsx, csv, pdf, docx

**Error handling:**
- If file exceeds limit, dialog shows "File too large" with actual size and limit
- User can immediately select a different file
- No failed upload attempt hits the server

**Key behaviors:**
- JWT tokens include an expiration timestamp
- Backend silently refreshes tokens before they expire during API calls
- Users should never be interrupted for re-authentication during normal use

**Edge case handling:**
- If token refresh fails (e.g., revoked access, expired refresh token), the user receives a friendly re-authentication prompt
- Session data is cleared gracefully on logout

---

## Summary

**The Golden Rule:**
```
Commit & Push only when completing a phase, milestone, or bug fix session
```

**Why this matters:**
1. Clean git history with meaningful commits
2. Each commit represents a complete unit of work
3. User tests on multiple machines - completed work must be available
4. Documentation stays bundled with related code changes

**When to commit (checklist):**
- [ ] Phase/milestone/bug fix session is COMPLETE
- [ ] All related code changes are staged together
- [ ] Documentation is included in same commit
- [ ] Commit message describes the completed work
- [ ] Push to remote after commit

**What NOT to do:**
- ❌ Commit after every individual file change
- ❌ Separate commits for code and its documentation
- ❌ Commit incomplete work-in-progress

---

*Last updated: 2026-02-03*
*Established during Phase 6 execution*
*User story management added during QA session*
*Regression testing added during v1.9 QA*
*Commit policy updated: phases/milestones only (not every change)*
