---
phase: 65-backend-skill-metadata
plan: 02
subsystem: api
tags: [python-frontmatter, yaml, skills, metadata, fallback]

requires:
  - phase: 65
    plan: 01
    provides: "YAML frontmatter in 10 personal SKILL.md files"
provides:
  - "Enhanced GET /api/skills endpoint with frontmatter parsing and structured metadata"
  - "Three-tier fallback system for skills without frontmatter"
  - "Home directory (~/.claude/) skill scanning instead of project directory"
affects: [66, 67]

tech-stack:
  added: ["python-frontmatter>=1.0.0"]
  patterns: ["Three-tier fallback pattern for missing metadata", "Environment variable override pattern (SKILLS_DIR)"]

key-files:
  created: []
  modified:
    - "backend/requirements.txt"
    - "backend/app/routes/skills.py"

key-decisions:
  - "Scan ~/.claude/ instead of project .claude/ for user-specific skills"
  - "Use SKIP_DIRS set to exclude plugins, get-shit-done, and 15+ utility directories"
  - "Implement three-tier fallback: frontmatter → transformed/extracted → default"
  - "Support SKILLS_DIR environment variable for deployment flexibility"
  - "skill_path relative to home directory (.claude/skill-name/SKILL.md)"

patterns-established:
  - "Frontmatter parsing with python-frontmatter library"
  - "Graceful fallback for missing metadata fields"
  - "Directory name transformation (kebab-case → Title Case)"
  - "First content line extraction for description fallback"

requirements-completed: [API-01, API-02]

duration: 4min
completed: 2026-02-18
---

# Plan 65-02: Enhanced Skills API with Frontmatter Parsing

**GET /api/skills now parses YAML frontmatter from ~/.claude/ skills and returns structured metadata with three-tier fallback system**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-18
- **Completed:** 2026-02-18
- **Tasks:** 2 (2 auto)
- **Files modified:** 2
- **Commits:** 1

## Accomplishments

- Added python-frontmatter>=1.0.0 dependency to requirements.txt
- Rewrote skills.py to scan ~/.claude/ instead of project .claude/
- Implemented YAML frontmatter parsing with python-frontmatter library
- Three-tier fallback system ensures all skills return valid metadata
- Excluded 17+ utility directories (plugins, get-shit-done, agents, etc.)
- Supports SKILLS_DIR environment variable for deployment override
- Returns structured metadata: name, description, features[], skill_path
- API verified with 10 skills from ~/.claude/ with frontmatter-sourced data

## Files Created/Modified

**Modified:**
- `/Users/a1testingmac/projects/XtraSkill/backend/requirements.txt` - Added python-frontmatter>=1.0.0
- `/Users/a1testingmac/projects/XtraSkill/backend/app/routes/skills.py` - Complete rewrite with frontmatter parsing

## Decisions Made

1. **Home directory scanning:** Changed from project `.claude/` to `~/.claude/` to access user's personal skills collection
2. **Skip directory set:** Defined SKIP_DIRS with 17 utility directories to exclude non-skill directories
3. **Three-tier fallback pattern:**
   - `name`: frontmatter.name → directory-name.replace('-', ' ').title() → raw directory name
   - `description`: frontmatter.description → first non-header content line → "No description available"
   - `features`: frontmatter.features (validated as list[str]) → empty array []
4. **Environment variable support:** Added SKILLS_DIR override for deployment flexibility
5. **skill_path format:** Relative to home directory (`.claude/skill-name/SKILL.md`)

## Task Completion Details

### Task 1: Install python-frontmatter and rewrite skills API

**Commit:** `7ee015f` - feat(65-02): add python-frontmatter parsing to skills API

**Changes:**
- Added `python-frontmatter>=1.0.0` to requirements.txt
- Installed dependency via pip
- Completely rewrote skills.py with new implementation:
  - `_get_skills_dir()`: Returns ~/.claude/ or SKILLS_DIR env var
  - `_extract_frontmatter()`: Parses YAML frontmatter with error handling
  - `_get_skill_name()`: Three-tier fallback for name field
  - `_get_skill_description()`: Three-tier fallback for description field
  - `_get_skill_features()`: Validates and returns features array
  - `list_skills()`: Main endpoint with sorted iteration and skip logic
- SKIP_DIRS set includes: plugins, get-shit-done, agents, commands, hooks, projects, tasks, todos, cache, downloads, debug, file-history, paste-cache, plans, session-env, shell-snapshots, telemetry

**Verification:**
- ✓ python-frontmatter installed successfully (v1.1.0)
- ✓ Python import successful
- ✓ GET /api/skills returns 10 skills
- ✓ All skills have name, description, features, skill_path fields
- ✓ All features are arrays of strings
- ✓ Names are human-readable (not slug format)
- ✓ Sample: Business Analyst with 5 features, description starts "Helps you systematically..."

### Task 2: Verify fallback behavior and edge cases

**No commit** (verification only)

**Verification Steps:**
1. ✓ Confirmed 10 skills with frontmatter-sourced metadata (all have 4-5 features)
2. ✓ Created test-fallback-skill without frontmatter
3. ✓ Verified fallback behavior:
   - Name: "Test Fallback Skill" (directory name transformed correctly)
   - Description: "This is a test description." (first content line extracted)
   - Features: [] (empty array as expected)
4. ✓ Cleaned up test skill successfully
5. ✓ Final count: exactly 10 skills (no test artifact)
6. ✓ Skip logic verified: 17 utility directories excluded from results

**Skip Logic Confirmation:**
- Directories in ~/.claude/: agents, cache, commands, debug, downloads, file-history, get-shit-done, hooks, paste-cache, plans, plugins, projects, session-env (and 5+ more)
- Skills in API: Only the 10 actual skill directories
- Utility directories correctly excluded

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## API Response Structure

```json
[
  {
    "name": "Business Analyst",
    "description": "Helps you systematically gather business requirements...",
    "features": [
      "Structured requirements discovery sessions",
      "Generates comprehensive BRDs",
      "Proactive edge case exploration",
      "Creates acceptance criteria and user stories",
      "Automatic mode detection (meeting vs document refinement)"
    ],
    "skill_path": ".claude/business-analyst/SKILL.md"
  }
]
```

**Field Details:**
- `name`: Human-readable skill name (from frontmatter or transformed directory name)
- `description`: Action-oriented description (from frontmatter or first content line)
- `features`: Array of 3-5 feature strings (from frontmatter or empty array)
- `skill_path`: Relative path from home directory (for frontend prepend logic)

## Fallback Behavior Verified

**Scenario 1: All frontmatter present** (normal case)
- 10 skills returned
- All have frontmatter-sourced name, description, features
- Features arrays contain 4-5 strings each

**Scenario 2: No frontmatter** (edge case)
- Test skill without frontmatter correctly returned:
  - name: Directory name transformed from `test-fallback-skill` → `Test Fallback Skill`
  - description: First content line after headers extracted
  - features: Empty array []
- Proves graceful degradation works as designed

**Scenario 3: Skip directories** (utility directory handling)
- 17+ utility directories in ~/.claude/ excluded from results
- Only 10 actual skill directories returned
- plugins, get-shit-done, agents, commands, hooks, etc. all properly skipped

## Next Phase Readiness

- ✓ GET /api/skills returns structured metadata ready for Phase 66 skill browser UI
- ✓ Frontmatter parsing tested with real user skills (10 skills)
- ✓ Fallback behavior verified with test skill
- ✓ Skip logic confirmed with 17+ utility directories excluded
- ✓ API response format matches Phase 66 expectations (name, description, features, skill_path)
- ✓ Frontend can now consume rich metadata for browsable skill cards

## Self-Check: PASSED

**Files verified:**
- ✓ FOUND: /Users/a1testingmac/projects/XtraSkill/backend/requirements.txt
- ✓ FOUND: /Users/a1testingmac/projects/XtraSkill/backend/app/routes/skills.py

**Commits verified:**
- ✓ FOUND: 7ee015f

**API verified:**
- ✓ 10 skills returned from GET /api/skills
- ✓ All fields present and correctly formatted
- ✓ Fallback behavior working as designed
- ✓ Skip logic excluding utility directories

---
*Phase: 65-backend-skill-metadata*
*Completed: 2026-02-18*
