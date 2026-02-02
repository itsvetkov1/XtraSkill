# Phase 33: CI Integration - Research

**Researched:** 2026-02-02
**Domain:** GitHub Actions CI/CD with coverage tracking via Codecov
**Confidence:** HIGH

## Summary

This phase configures GitHub Actions to run tests with coverage tracking, enforces quality gates, and displays coverage via Codecov badges. The project already has an existing CI workflow (`flutter-ci.yml`) that runs basic tests on push/PR but lacks coverage reporting. Research confirms the standard approach:

1. **Codecov** is the industry-standard for coverage tracking with GitHub - it provides history, PR comments, badges, and configurable thresholds
2. **GitHub Actions** triggers support the user's requirements: `issue_comment` for /test commands, `schedule` for weekly runs, plus `workflow_dispatch` for manual triggers
3. **Flags** in Codecov allow separate tracking of backend (Python/pytest-cov) and frontend (Flutter/lcov) coverage

**Primary recommendation:** Modify the existing `flutter-ci.yml` workflow to add coverage generation and Codecov upload, change triggers to manual/scheduled only, and add a new workflow for slash command dispatch.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| codecov/codecov-action | v5 | Upload coverage to Codecov | Official Codecov GitHub Action with integrity checks |
| pytest-cov | 4.1.0+ | Python coverage generation | Already in requirements.txt, generates XML reports |
| lcov | system | Flutter coverage processing | Standard for Dart/Flutter coverage |
| peter-evans/slash-command-dispatch | v5 | /test command handling | Industry-standard ChatOps action |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| actions/cache | v4 | Dependency caching | Reduce CI time for pip/flutter pub |
| subosito/flutter-action | v2 | Flutter SDK setup | Already in use, has built-in caching |
| actions/setup-python | v5 | Python setup | Already in use, has pip caching |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Codecov | Coveralls | Codecov has better GitHub integration and flag support |
| Codecov | shields.io + manual upload | Loses history, PR comments, and trend tracking |
| slash-command-dispatch | Custom issue_comment parsing | More maintenance, less robust |

**Installation:**
```bash
# No new dependencies needed - pytest-cov already in requirements.txt
# Codecov uses GitHub Action, no package installation
```

## Architecture Patterns

### Recommended Workflow Structure
```
.github/
├── workflows/
│   ├── ci.yml               # Main test workflow (manual/scheduled triggers)
│   └── slash-command.yml    # Dispatch /test commands from PR comments
└── codecov.yml              # (optional) Root-level Codecov config
codecov.yml                  # Alternative location in repo root
```

### Pattern 1: Dual-Trigger Workflow
**What:** Single workflow file with multiple trigger types
**When to use:** When the same jobs run for different triggers
**Example:**
```yaml
# Source: GitHub Docs - Events that trigger workflows
name: CI Tests

on:
  # Manual trigger via Actions tab
  workflow_dispatch:

  # Scheduled weekly run (Monday 9 AM UTC)
  schedule:
    - cron: '0 9 * * 1'

  # Triggered by slash-command-dispatch
  repository_dispatch:
    types: [test-command]

  # Triggered on PR comment /test (via commit message)
  push:
    branches: [master, main]

jobs:
  test:
    # Only run on push if commit message contains /test
    if: |
      github.event_name != 'push' ||
      contains(github.event.head_commit.message, '/test')
    runs-on: ubuntu-latest
    steps:
      # ... test steps
```

### Pattern 2: Codecov Flags for Backend/Frontend
**What:** Separate coverage tracking for different parts of codebase
**When to use:** Multi-language projects, monorepos
**Example:**
```yaml
# Source: Codecov Docs - Flags
# codecov.yml
coverage:
  status:
    project:
      default:
        informational: true  # Warn only, don't fail
      backend:
        flags:
          - backend
        informational: true
      frontend:
        flags:
          - frontend
        informational: true

flags:
  backend:
    paths:
      - app/
    carryforward: true
  frontend:
    paths:
      - lib/
    carryforward: true
```

### Pattern 3: Slash Command Dispatch
**What:** Parse /test from PR comments and trigger workflows
**When to use:** ChatOps-style CI triggers
**Example:**
```yaml
# Source: peter-evans/slash-command-dispatch
name: Slash Command Dispatch
on:
  issue_comment:
    types: [created]

jobs:
  dispatch:
    runs-on: ubuntu-latest
    # Only on PR comments (not issues)
    if: github.event.issue.pull_request && startsWith(github.event.comment.body, '/test')
    steps:
      - uses: peter-evans/slash-command-dispatch@v5
        with:
          token: ${{ secrets.PAT }}
          commands: test
          dispatch-type: repository
```

### Anti-Patterns to Avoid
- **Running tests on every push:** User explicitly wants manual/scheduled triggers only
- **Blocking merges on coverage drops:** User wants warn-only for coverage thresholds
- **Single coverage report:** Backend and frontend should be tracked separately with flags
- **Hardcoded thresholds in workflow:** Use Codecov's codecov.yml for configurability

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Coverage history tracking | Custom database/file storage | Codecov | Provides trends, comparisons, PR annotations |
| Badge generation | Manual shields.io updates | Codecov badges | Auto-updates with each coverage upload |
| Slash command parsing | Manual regex in issue_comment | slash-command-dispatch | Handles edge cases, branch targeting, permissions |
| Coverage merging | Custom scripts to combine XML/lcov | Codecov flags | Handles carryforward, parallel uploads |

**Key insight:** Codecov's value is in the ecosystem integration (PR comments, badges, history) - not just the coverage number.

## Common Pitfalls

### Pitfall 1: issue_comment Runs on Default Branch
**What goes wrong:** Workflow triggered by PR comment runs from master, not PR branch
**Why it happens:** `issue_comment` event always checks out default branch
**How to avoid:** Use `slash-command-dispatch` which properly handles PR branch targeting, or manually checkout the PR's head ref
**Warning signs:** Tests pass in CI but fail locally on the PR branch

### Pitfall 2: CODECOV_TOKEN Required for Private Repos
**What goes wrong:** Coverage upload fails with authentication error
**Why it happens:** Private repos need the token, public repos can use tokenless
**How to avoid:** Always configure CODECOV_TOKEN secret, even if optional for public repos
**Warning signs:** "Unable to upload coverage" in CI logs

### Pitfall 3: Scheduled Workflows Only Run on Default Branch
**What goes wrong:** Scheduled workflow doesn't pick up workflow file changes until merged
**Why it happens:** GitHub Actions limitation - schedule event only runs from default branch
**How to avoid:** Test workflow changes via workflow_dispatch first, then merge
**Warning signs:** Workflow changes don't take effect on scheduled runs

### Pitfall 4: Coverage Threshold Blocking Merges
**What goes wrong:** Legitimate changes blocked because coverage dropped slightly
**Why it happens:** `fail_ci_if_error: true` or strict codecov.yml status checks
**How to avoid:** Use `informational: true` in Codecov config for warn-only
**Warning signs:** PRs failing CI despite all tests passing

### Pitfall 5: Flutter Coverage Path Mismatch
**What goes wrong:** Codecov can't find Flutter coverage file
**Why it happens:** `flutter test --coverage` outputs to `coverage/lcov.info`, not XML
**How to avoid:** Explicitly specify `files: ./frontend/coverage/lcov.info` in Codecov action
**Warning signs:** Zero coverage reported for frontend

## Code Examples

Verified patterns from official sources:

### Generate and Upload Python Coverage
```yaml
# Source: https://github.com/codecov/codecov-action
- name: Run backend tests with coverage
  working-directory: ./backend
  run: |
    pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing
  env:
    ANTHROPIC_API_KEY: test-key-for-ci

- name: Upload backend coverage to Codecov
  uses: codecov/codecov-action@v5
  with:
    files: ./backend/coverage.xml
    flags: backend
    token: ${{ secrets.CODECOV_TOKEN }}
    fail_ci_if_error: false
```

### Generate and Upload Flutter Coverage
```yaml
# Source: https://damienaicheh.github.io/flutter/github/actions/2021/05/06/flutter-tests-github-actions-codecov-en.html
- name: Run Flutter tests with coverage
  working-directory: ./frontend
  run: flutter test --coverage

- name: Upload frontend coverage to Codecov
  uses: codecov/codecov-action@v5
  with:
    files: ./frontend/coverage/lcov.info
    flags: frontend
    token: ${{ secrets.CODECOV_TOKEN }}
    fail_ci_if_error: false
```

### Codecov Configuration with Flags and Thresholds
```yaml
# Source: https://docs.codecov.com/docs/codecovyml-reference
# codecov.yml in repository root
codecov:
  require_ci_to_pass: yes

coverage:
  precision: 2
  round: down
  status:
    project:
      default:
        target: auto  # Compare to base commit
        threshold: 5%  # Allow 5% drop without warning
        informational: true  # Warn only, don't fail
      backend:
        flags:
          - backend
        informational: true
      frontend:
        flags:
          - frontend
        informational: true
    patch:
      default:
        target: 50%  # New code should have some coverage
        informational: true

flags:
  backend:
    paths:
      - app/
    carryforward: true
  frontend:
    paths:
      - lib/
    carryforward: true

comment:
  layout: "reach,diff,flags,files"
  behavior: default
  require_changes: true
```

### Commit Message Trigger Condition
```yaml
# Source: https://dev.to/mliakos/conditional-github-action-based-on-commit-message-2l02
jobs:
  test:
    # Run if: manual dispatch, scheduled, repository_dispatch,
    # OR push with /test in commit message
    if: |
      github.event_name == 'workflow_dispatch' ||
      github.event_name == 'schedule' ||
      github.event_name == 'repository_dispatch' ||
      (github.event_name == 'push' && contains(github.event.head_commit.message, '/test'))
    runs-on: ubuntu-latest
```

### Codecov Badge Markdown
```markdown
# Source: https://docs.codecov.com/docs/status-badges
[![codecov](https://codecov.io/github/itsvetkov1/XtraSkill/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/github/itsvetkov1/XtraSkill)
```

### Weekly Schedule (Monday Morning UTC)
```yaml
# Source: GitHub Docs - Events that trigger workflows
on:
  schedule:
    # Monday at 9:00 AM UTC
    - cron: '0 9 * * 1'
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Coveralls | Codecov | 2020+ | Better GitHub integration, flag support |
| codecov-action v3/v4 | codecov-action v5 | 2024 | OIDC support, tokenless for public repos |
| Manual badge URLs | Codecov auto-badges | N/A | Badges auto-update |
| Run on every push | Manual/scheduled triggers | User preference | Saves CI minutes, reduces noise |

**Deprecated/outdated:**
- codecov-action v1-v3: Upgrade to v5 for latest features
- Coveralls: Still works but Codecov has better ecosystem

## Open Questions

Things that couldn't be fully resolved:

1. **Current coverage percentages**
   - What we know: Backend is ~67% (from test run), frontend count is 627 tests
   - What's unclear: Exact frontend coverage percentage
   - Recommendation: Run `flutter test --coverage` locally to determine baseline, set thresholds accordingly (suggest 60% backend, 50% frontend as starting points)

2. **PAT for slash-command-dispatch**
   - What we know: Action requires repo-scoped PAT, not GITHUB_TOKEN
   - What's unclear: Does user have a PAT configured, or need to create one?
   - Recommendation: Document PAT creation in plan if not already available

3. **Branch protection configuration**
   - What we know: User wants CI to pass before merge, admin bypass available
   - What's unclear: Is branch protection already configured on master?
   - Recommendation: Include branch protection setup in plan tasks

## Sources

### Primary (HIGH confidence)
- [codecov/codecov-action GitHub](https://github.com/codecov/codecov-action) - v5 usage, inputs, OIDC
- [Codecov Quick Start](https://docs.codecov.com/docs/quick-start) - Setup process, token configuration
- [Codecov YAML Reference](https://docs.codecov.com/docs/codecovyml-reference) - Full configuration options
- [Codecov Flags](https://docs.codecov.com/docs/flags) - Backend/frontend separation
- [Codecov Status Badges](https://docs.codecov.com/docs/status-badges) - Badge URL format
- [GitHub Docs - Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows) - Schedule, issue_comment, workflow_dispatch
- [GitHub Docs - Workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions) - Job conditions, matrix
- [GitHub Docs - Branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) - Status checks, admin bypass

### Secondary (MEDIUM confidence)
- [peter-evans/slash-command-dispatch](https://github.com/marketplace/actions/slash-command-dispatch) - ChatOps /test command handling
- [Conditional GitHub Action based on commit message](https://dev.to/mliakos/conditional-github-action-based-on-commit-message-2l02) - contains() pattern
- [Flutter tests with GitHub Actions and Codecov](https://damienaicheh.github.io/flutter/github/actions/2021/05/06/flutter-tests-github-actions-codecov-en.html) - Flutter lcov + Codecov
- [pytest documentation](https://docs.pytest.org/en/stable/how-to/failures.html) - Test failure handling

### Tertiary (LOW confidence)
- Community discussions on admin bypass for status checks - Feature limitations confirmed but workarounds unclear

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools verified via official docs
- Architecture: HIGH - Patterns from official GitHub and Codecov docs
- Pitfalls: HIGH - Common issues documented in official troubleshooting

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (30 days - stable domain)

## Existing Infrastructure Analysis

### Current CI Workflow (flutter-ci.yml)
The existing workflow:
- Triggers: push to main/master/develop, PR to main/master
- Backend job: Python 3.11, runs only `tests/test_backend_integration.py`
- Frontend job: Flutter 3.x stable, runs widget/ and integration/ tests separately
- Web build job: Depends on flutter-test, builds release web
- Caching: pip cache enabled, Flutter cache enabled

**Needed changes:**
1. Remove push/commit triggers (keep PR trigger for /test in commit message check)
2. Add workflow_dispatch, schedule, and repository_dispatch triggers
3. Add coverage generation (`--cov` for pytest, `--coverage` for flutter)
4. Add Codecov upload steps with flags
5. Run ALL tests, not just test_backend_integration.py

### Current Coverage Configuration (pyproject.toml)
```toml
[tool.coverage.run]
source = ["app"]
branch = true
fail_under = 0  # Currently no enforcement

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "def __repr__", ...]
```
**Note:** fail_under = 0 means no local enforcement - Codecov will handle threshold warnings

### Test Counts
- Backend: 471 tests total (448 passed, 18 failed, 4 errors in last run)
- Frontend: 627 tests (all passed)
- Current backend coverage: ~67%
- Current frontend coverage: Unknown (needs measurement)

### Repository
- GitHub: `itsvetkov1/XtraSkill`
- No README at repo root (only frontend/README.md)
- Badge will need to go in a new root README or frontend README
