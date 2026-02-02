# Technology Stack: Unit Testing for FastAPI + Flutter

**Project:** BA Assistant - Unit Testing Initiative (v1.9.1)
**Researched:** 2026-02-02
**Confidence:** HIGH (verified against official documentation and existing codebase)

---

## Executive Summary

BA Assistant already has a solid testing foundation with pytest (backend) and flutter_test + mockito (frontend). This stack recommendation focuses on **enhancing coverage reporting, improving test isolation, and adding CI/CD integration** rather than replacing existing tools.

**Key additions:**
- pytest-cov for backend coverage
- pytest-mock for cleaner mocking syntax
- lcov/genhtml for Flutter coverage reporting
- GitHub Actions enhancements for coverage badges

---

## Current State Analysis

### Backend (Existing)
| Tool | Version | Status |
|------|---------|--------|
| pytest | >=8.3.0 | Installed |
| pytest-asyncio | >=0.24.0 | Installed |
| httpx | >=0.27.0 | Installed (for AsyncClient) |

### Frontend (Existing)
| Tool | Version | Status |
|------|---------|--------|
| flutter_test | SDK | Installed |
| mockito | ^5.6.3 | Installed |
| build_runner | ^2.10.5 | Installed |

---

## Recommended Stack: Backend (Python)

### Core Testing Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pytest | >=8.3.0 | Test runner and framework | Already in use. Industry standard for Python testing. Rich plugin ecosystem. |
| pytest-asyncio | >=0.24.0 | Async test support | Already in use. Required for FastAPI async endpoints. |
| httpx | >=0.27.0 | Async HTTP client for tests | Already in use via FastAPI's TestClient. ASGITransport for testing. |

### Coverage Tools (NEW)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest-cov** | >=4.1.0 | Coverage reporting | Integrates coverage.py with pytest. Automatic cleanup, multiple output formats (terminal, HTML, XML, JSON). Required for CI coverage badges. |
| coverage | >=7.4.0 | Coverage engine | Underlying engine for pytest-cov. Supports branch coverage, HTML reports. |

**Rationale:** pytest-cov is the standard for Python coverage. It handles parallel test runs, subprocess coverage, and generates reports compatible with all major CI services (Codecov, Coveralls, GitHub Actions).

### Mocking Tools (ENHANCEMENT)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest-mock** | >=3.12.0 | Enhanced mocking | Provides `mocker` fixture. Cleaner syntax than raw unittest.mock. Automatic cleanup after tests. Better pytest integration. |
| unittest.mock | stdlib | Core mocking | Part of Python stdlib. pytest-mock wraps this. |

**Rationale:** The project currently uses raw unittest.mock patterns. pytest-mock provides a `mocker` fixture that simplifies patching with automatic cleanup. Example benefit:

```python
# Current approach (more verbose)
from unittest.mock import patch

async def test_example():
    with patch('app.services.llm.call_api') as mock:
        mock.return_value = {...}
        # test code

# With pytest-mock (cleaner)
async def test_example(mocker):
    mock = mocker.patch('app.services.llm.call_api', return_value={...})
    # test code - automatic cleanup
```

### HTTP Mocking for External APIs (NEW)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **respx** | >=0.21.0 | Mock httpx requests | Native httpx mocking. Required for testing LLM adapters (Anthropic, Google GenAI, OpenAI) without hitting real APIs. pytest fixture included (`respx_mock`). |

**Rationale:** BA Assistant has multi-LLM adapters that make external HTTP calls. respx is the standard library for mocking httpx in async contexts. It's specifically designed for httpx (unlike `responses` which is for `requests`).

```python
# Example: mocking Anthropic API call
import respx
from httpx import Response

@respx.mock
async def test_anthropic_adapter():
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(200, json={"content": [{"text": "response"}]})
    )
    # Test adapter code
```

### Model Factories (NEW)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **factory-boy** | >=3.3.0 | Test data factories | Creates realistic test data. Reduces boilerplate for creating User, Project, Thread, Document models. Integrates with SQLAlchemy. |
| **pytest-factoryboy** | >=2.5.0 | pytest integration | Registers factories as fixtures. Enables `user`, `project` fixtures automatically. |
| faker | >=22.0.0 | Fake data generation | Used by factory-boy for realistic names, emails, text. Already a dependency of factory-boy. |

**Rationale:** Current tests manually create model instances (see `test_projects.py`). Factory-boy reduces this boilerplate and ensures consistent test data across all tests.

```python
# Current approach (verbose, repeated)
user = User(
    id=str(uuid4()),
    email="test@example.com",
    oauth_provider=OAuthProvider.GOOGLE,
    oauth_id="google_123",
)

# With factory-boy (cleaner, reusable)
@register
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.Faker('email')
    oauth_provider = OAuthProvider.GOOGLE
    oauth_id = factory.Sequence(lambda n: f'google_{n}')

# In tests - just use the fixture
async def test_create_project(client, user):  # user fixture auto-created
    token = create_access_token(user.id, user.email)
    # test code
```

### NOT Recommended

| Technology | Why NOT |
|------------|---------|
| pytest-bdd | Overkill for this project. BDD syntax adds complexity without clear benefit for a single-developer project. |
| hypothesis | Property-based testing is valuable but should be Phase 2. Start with basic coverage first. |
| locust | Load testing is out of scope for unit testing milestone. |
| pytest-docker | Project uses SQLite in-memory for tests. No need for containerized databases. |

---

## Recommended Stack: Frontend (Flutter/Dart)

### Core Testing Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| flutter_test | SDK | Widget and unit testing | Already in use. Official Flutter testing framework. |
| mockito | ^5.6.3 | Mocking framework | Already in use. Type-safe mocks with code generation. Well-established. |
| build_runner | ^2.10.5 | Code generation | Already in use. Required for mockito mock generation. |

### Coverage Tools (ENHANCEMENT)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| lcov | system | Coverage report processing | Convert Flutter's lcov.info to HTML. Standard tool, works with all CI services. |
| genhtml | system | HTML report generation | Part of lcov package. Generates browsable HTML coverage reports. |

**Flutter coverage command:**
```bash
# Generate coverage
flutter test --coverage

# Convert to HTML (requires lcov installed)
genhtml coverage/lcov.info -o coverage/html

# Exclude generated files
lcov -r coverage/lcov.info "lib/*.g.dart" "lib/*.freezed.dart" -o coverage/lcov.info
```

### Alternatives Considered

| Technology | Verdict | Reason |
|------------|---------|--------|
| **mocktail** | Not switching | Project already uses mockito with established patterns. Mocktail eliminates code generation but would require rewriting all existing tests. |
| **very_good_cli** | Optional | Provides `very_good test --coverage --min-coverage 80` convenience. Nice-to-have but not essential. The raw Flutter commands work fine. |

**Why stick with mockito:**
1. Already have 11 test files using mockito patterns
2. Generated mocks are already committed
3. Code generation is a one-time cost
4. Mockito is the official Flutter documentation recommendation

### NOT Recommended

| Technology | Why NOT |
|------------|---------|
| mocktail | Would require rewriting all existing tests. No compelling benefit over current mockito setup. |
| patrol | E2E testing framework. Out of scope for unit testing milestone. |
| golden_toolkit | Screenshot testing. Different category than unit testing. |

---

## CI/CD Integration

### Current CI State

The project has `.github/workflows/flutter-ci.yml` with:
- Backend: pytest tests/test_backend_integration.py
- Frontend: flutter test (widget + integration)
- No coverage reporting

### Recommended CI Enhancements

| Enhancement | Tool | Why |
|-------------|------|-----|
| Backend coverage | pytest-cov + Codecov | Industry standard. Free for open source. PR annotations. |
| Frontend coverage | lcov + Codecov | Same dashboard for both stacks. |
| Coverage badge | Codecov badge or coverage-badge-action | Visual indicator in README. |
| Coverage threshold | pytest-cov --fail-under=80 | Prevent coverage regression. |

### Recommended Workflow Updates

```yaml
# Backend test job enhancement
- name: Run backend tests with coverage
  run: |
    pytest tests/ -v --cov=app --cov-report=xml --cov-report=term
  env:
    ANTHROPIC_API_KEY: test-key-for-ci

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    files: ./backend/coverage.xml
    flags: backend

# Frontend test job enhancement
- name: Run Flutter tests with coverage
  run: flutter test --coverage

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    files: ./frontend/coverage/lcov.info
    flags: frontend
```

---

## Installation Commands

### Backend

```bash
cd backend

# Add to requirements.txt (or install directly)
pip install pytest-cov>=4.1.0 pytest-mock>=3.12.0 respx>=0.21.0 factory-boy>=3.3.0 pytest-factoryboy>=2.5.0
```

**Updated requirements.txt additions:**
```
# Testing (existing)
pytest>=8.3.0
pytest-asyncio>=0.24.0
httpx>=0.27.0

# Testing (new)
pytest-cov>=4.1.0
pytest-mock>=3.12.0
respx>=0.21.0
factory-boy>=3.3.0
pytest-factoryboy>=2.5.0
```

### Frontend

No new pub dependencies needed. Coverage tooling is external:

```bash
# macOS
brew install lcov

# Ubuntu/Debian
sudo apt-get install lcov

# Windows (via Chocolatey)
choco install lcov
```

---

## Configuration Files

### pytest.ini or pyproject.toml (NEW)

Create `backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

Or add to `backend/pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = ["ignore::DeprecationWarning"]

[tool.coverage.run]
source = ["app"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80
show_missing = true
```

### .coveragerc (Alternative)

If not using pyproject.toml:
```ini
[run]
source = app
branch = true
omit =
    */tests/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
fail_under = 80
show_missing = true
```

---

## Version Compatibility Matrix

| Component | Minimum Version | Tested With | Notes |
|-----------|-----------------|-------------|-------|
| Python | 3.10 | 3.11 | CI uses 3.11 |
| pytest | 8.0.0 | 8.3.0 | Current in requirements.txt |
| pytest-asyncio | 0.23.0 | 0.24.0 | Current in requirements.txt |
| pytest-cov | 4.0.0 | 4.1.0 | Requires coverage >= 7.0 |
| coverage | 7.0.0 | 7.4.0 | Bundled with pytest-cov |
| respx | 0.20.0 | 0.21.0 | Requires httpx >= 0.25 |
| factory-boy | 3.2.0 | 3.3.0 | SQLAlchemy 2.0 support |
| Flutter | 3.x | 3.x | CI uses stable channel |
| mockito | 5.4.0 | 5.6.3 | Current in pubspec.yaml |

---

## Migration Path

### Phase 1: Add Coverage Reporting
1. Add pytest-cov to requirements.txt
2. Add coverage config (pytest.ini or pyproject.toml)
3. Update CI to run `pytest --cov=app`
4. Add Codecov integration

### Phase 2: Add pytest-mock
1. Add pytest-mock to requirements.txt
2. Refactor existing tests to use `mocker` fixture (optional, gradual)
3. Use for all new tests

### Phase 3: Add External API Mocking
1. Add respx to requirements.txt
2. Create fixtures in conftest.py for LLM API mocks
3. Add tests for LLM adapters

### Phase 4: Add Model Factories
1. Add factory-boy and pytest-factoryboy to requirements.txt
2. Create factories for User, Project, Thread, Document, Message
3. Refactor existing tests to use factories (optional, gradual)
4. Use factories for all new tests

---

## Sources

**Official Documentation:**
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov PyPI](https://pypi.org/project/pytest-cov/)
- [pytest-mock DataCamp Tutorial](https://www.datacamp.com/tutorial/pytest-mock)
- [respx Documentation](https://lundberg.github.io/respx/)
- [factory-boy Documentation](https://factoryboy.readthedocs.io/)
- [pytest-factoryboy PyPI](https://pypi.org/project/pytest-factoryboy/)
- [Flutter Mock Dependencies](https://docs.flutter.dev/cookbook/testing/unit/mocking)
- [Flutter Test Coverage Guide](https://codewithandrea.com/articles/flutter-test-coverage/)

**Best Practices:**
- [pytest-mock vs unittest.mock](https://codecut.ai/pytest-mock-vs-unittest-mock-simplifying-mocking-in-python-tests/)
- [FastAPI Testing Best Practices](https://pytest-with-eric.com/pytest-advanced/pytest-fastapi-testing/)
- [Async Testing with pytest-asyncio](https://pytest-with-eric.com/pytest-advanced/pytest-asyncio/)
- [respx for httpx mocking](https://rogulski.it/blog/pytest-httpx-vcr-respx-remote-service-tests/)

**CI/CD:**
- [GitHub Actions Coverage Badge](https://medium.com/@nunocarvalhodossantos/how-i-generate-and-display-coverage-badges-in-github-for-a-fastapi-project-f71861d620bb)
- [Codecov Action](https://github.com/codecov/codecov-action)
- [Pytest Coverage Comment Action](https://github.com/marketplace/actions/pytest-coverage-comment)

---

## Summary: What to Install

### Backend (add to requirements.txt)
```
pytest-cov>=4.1.0
pytest-mock>=3.12.0
respx>=0.21.0
factory-boy>=3.3.0
pytest-factoryboy>=2.5.0
```

### Frontend
No new Dart dependencies. Install lcov system-wide for coverage HTML generation.

### CI
Add Codecov action to GitHub workflow for unified coverage dashboard.
