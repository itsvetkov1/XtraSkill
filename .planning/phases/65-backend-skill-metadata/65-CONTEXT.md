# Phase 65: Backend Skill Metadata - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance GET /api/skills to parse YAML frontmatter from SKILL.md files and return structured metadata (name, description, features). Add YAML frontmatter to all 11 personal skills. Change scan path from project .claude/ to user home ~/.claude/. Frontend changes are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Frontmatter format
- YAML frontmatter with three fields only: `name`, `description`, `features`
- `name` is the human-readable display name (e.g., "Business Analyst")
- `description` is a 1-2 sentence action-oriented summary
- `features` is a simple string array of 3-5 key capabilities
- Example:
  ```yaml
  ---
  name: Business Analyst
  description: Helps you systematically gather business requirements and generate professional documentation.
  features:
    - Generates BRDs and user stories
    - Explores edge cases proactively
    - Creates acceptance criteria
  ---
  ```

### Skill descriptions
- Claude drafts all 11 skill frontmatters, presents batch for user approval
- Action-oriented tone ("Helps you...", "Enables you to...")
- Skip all GSD (get-shit-done) skills — they are workflow commands, not user-facing
- Skip all plugin marketplace skills (~/.claude/plugins/)

### Skills to include (11 personal skills)
1. business-analyst
2. software-architect
3. judge
4. ralph-prd-generator
5. qa-bff
6. task-delegation
7. skill-transformer
8. instructions-creator
9. tl-assistant
10. prompt-enhancer
11. evaluator-ba-docs

### API scan path
- Change from scanning project `.claude/` to scanning user home `~/.claude/`
- Skip directories that don't contain SKILL.md
- Skip `plugins/` subdirectory (marketplace skills excluded)
- Skip GSD-related directories (get-shit-done/)

### API response shape
- Add `features` field to existing response: `[{name, description, features: [...], skill_path}]`
- `name` sourced from frontmatter (human-readable), falls back to directory name if no frontmatter
- `description` sourced from frontmatter, falls back to first content line (current behavior)
- `features` sourced from frontmatter, empty array if not present
- Keep `skill_path` field — frontend uses it for prepend logic

### Fallback behavior (Claude's Discretion)
- Skills without frontmatter: use directory name for name, first content line for description, empty features
- Partially complete frontmatter: use what's present, fall back for missing fields
- Malformed YAML: log warning, fall back to current parsing behavior

</decisions>

<specifics>
## Specific Ideas

- User wants to see the drafted frontmatters in a batch before they're written to SKILL.md files
- The home ~/.claude/ path needs to work on the deployment server too (consider environment variable)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 65-backend-skill-metadata*
*Context gathered: 2026-02-18*
