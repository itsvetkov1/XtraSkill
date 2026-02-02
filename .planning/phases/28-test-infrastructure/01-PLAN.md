---
phase: 28-test-infrastructure
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/requirements.txt
  - backend/pyproject.toml
  - backend/.coveragerc
autonomous: true

must_haves:
  truths:
    - "Running pytest --cov=app generates coverage data"
    - "Coverage HTML report is generated in htmlcov/"
    - "pytest-mock is available for cleaner mocking syntax"
    - "factory-boy and pytest-factoryboy are installed"
  artifacts:
    - path: "backend/requirements.txt"
      provides: "Test dependencies"
      contains: "pytest-cov"
    - path: "backend/pyproject.toml"
      provides: "Coverage configuration"
      contains: "[tool.coverage"
    - path: "backend/.coveragerc"
      provides: "Coverage source exclusions"
      contains: "omit"
  key_links:
    - from: "pytest"
      to: "pytest-cov plugin"
      via: "automatic plugin discovery"
      pattern: "pytest-cov"
---

<objective>
Install and configure pytest-cov and related testing dependencies for backend coverage reporting.

Purpose: Enable coverage measurement for all subsequent test phases. Without coverage tooling, we cannot verify test completeness.

Output: Backend has pytest-cov configured; running `pytest --cov=app --cov-report=html` generates coverage report.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@backend/requirements.txt
@backend/tests/conftest.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add testing dependencies to requirements.txt</name>
  <files>backend/requirements.txt</files>
  <action>
Add the following test dependencies to backend/requirements.txt after existing test dependencies (pytest, pytest-asyncio):

```
# Test coverage and utilities
pytest-cov>=4.1.0
pytest-mock>=3.12.0
factory-boy>=3.3.0
pytest-factoryboy>=2.5.0
```

These dependencies enable:
- pytest-cov: Coverage measurement and reporting
- pytest-mock: Cleaner mocking with mocker fixture
- factory-boy: Test data factories for SQLAlchemy models
- pytest-factoryboy: Auto-registers factories as pytest fixtures
  </action>
  <verify>Run `pip install -r backend/requirements.txt` and verify no errors</verify>
  <done>All four new packages listed in requirements.txt and installable</done>
</task>

<task type="auto">
  <name>Task 2: Create pyproject.toml with coverage configuration</name>
  <files>backend/pyproject.toml</files>
  <action>
Create backend/pyproject.toml with pytest and coverage configuration:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["app"]
branch = true
omit = [
    "app/__init__.py",
    "app/config.py",
    "**/migrations/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 0
show_missing = true

[tool.coverage.html]
directory = "htmlcov"
```

This configures:
- pytest: Auto async mode (matches existing conftest.py), verbose output
- coverage.run: Source is app/, measure branches, omit init/config/migrations
- coverage.report: Exclude boilerplate, show missing lines, no minimum (will increase later)
- coverage.html: Output to htmlcov/ directory
  </action>
  <verify>Run `cd backend && pytest --cov=app --cov-report=html tests/test_projects.py -v` and check htmlcov/ directory created</verify>
  <done>pyproject.toml exists with [tool.coverage.*] sections, coverage report generates to htmlcov/</done>
</task>

<task type="auto">
  <name>Task 3: Create .coveragerc for additional exclusions</name>
  <files>backend/.coveragerc</files>
  <action>
Create backend/.coveragerc with additional coverage configuration (some tools read this file):

```ini
[run]
source = app
branch = true
omit =
    app/__init__.py
    app/config.py
    **/migrations/*
    tests/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
fail_under = 0
show_missing = true

[html]
directory = htmlcov
```

Note: This mirrors pyproject.toml settings but adds @abstractmethod exclusion and tests/* omit.
Some coverage invocations use .coveragerc, some use pyproject.toml - having both ensures consistency.
  </action>
  <verify>File exists at backend/.coveragerc with [run], [report], [html] sections</verify>
  <done>.coveragerc exists with coverage configuration matching pyproject.toml</done>
</task>

</tasks>

<verification>
1. Dependencies installed: `cd backend && pip install -r requirements.txt` succeeds
2. Coverage works: `cd backend && pytest --cov=app --cov-report=html tests/test_projects.py` produces htmlcov/index.html
3. Config files exist: backend/pyproject.toml and backend/.coveragerc both present
</verification>

<success_criteria>
- pytest-cov>=4.1.0, pytest-mock>=3.12.0, factory-boy>=3.3.0, pytest-factoryboy>=2.5.0 in requirements.txt
- Running `pytest --cov=app --cov-report=html` generates htmlcov/index.html
- Coverage configuration excludes appropriate files (init, config, migrations, abstract methods)
</success_criteria>

<output>
After completion, create `.planning/phases/28-test-infrastructure/28-01-SUMMARY.md`
</output>
