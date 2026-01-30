# Claude Development Rules

This document defines rules and conventions for Claude Code when working on this project.

---

## Git & Version Control

### Rule: Auto-Push After Every Change

**CRITICAL:** Push all code changes to remote repository immediately after committing.

**Why:** User tests on multiple machines. All changes must be available on remote for cross-platform testing.

**Implementation:**
```bash
# After every commit:
git commit -m "your commit message"
git push origin master

# OR combine:
git add <files> && git commit -m "message" && git push origin master
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

### Rule: Complete Phase Execution Commits

When executing GSD phases, ensure all commits are pushed:

1. **Per-task commits** (during execution)
2. **Plan completion commits** (SUMMARY.md)
3. **Phase completion commits** (ROADMAP.md, STATE.md, VERIFICATION.md)

**Never leave uncommitted phase work** - user needs to see progress on other machines.

---

## Bug Fixes

### Rule: Immediate Fix & Push

When user reports a bug (like the `/settings` logout issue):

1. **Acknowledge** the bug is real (don't assume user error first)
2. **Investigate** the root cause
3. **Fix** the issue with clear commit message
4. **Push** immediately: `git push origin master`
5. **Update documentation** if needed (testing guides, troubleshooting)
6. **Push documentation** immediately

**Example:**
```bash
# Fix the bug
git add frontend/lib/main.dart
git commit -m "fix(06-02): prevent router recreation causing logout"
git push origin master

# Update docs
git add THEME_TESTING_GUIDE.md
git commit -m "docs: update guide with bug fix info"
git push origin master
```

---

## Documentation

### Rule: Keep Testing Guides Current

When code changes affect testing:

1. Update relevant testing guides (TESTING_GUIDE.md, THEME_TESTING_GUIDE.md)
2. Add notes about bug fixes with commit hashes
3. Remove misleading troubleshooting sections after bugs are fixed
4. Push immediately

**Never leave documentation out of sync with code.**

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
4. **Commit and push** both files

### Rule: Keep INDEX.md Current

After any story change:

1. Update status in INDEX.md table
2. Update summary counts at top
3. Commit: `docs(stories): update INDEX with [story-id] status`

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

## Summary

**The Golden Rule:**
```
After every code/doc change: COMMIT + PUSH immediately
```

**Why this matters:**
1. User tests on multiple machines
2. Bugs need immediate fixes visible on all machines
3. Documentation must stay in sync with code
4. Other developers/testers need latest changes

**Quick checklist after any change:**
- [ ] Code committed with clear message
- [ ] Code pushed to remote
- [ ] Documentation updated if needed
- [ ] Documentation pushed to remote
- [ ] `git status --porcelain` shows only excluded files

---

*Last updated: 2026-01-30*
*Established during Phase 6 execution*
*User story management added during QA session*
