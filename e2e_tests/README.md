# BA Assistant E2E Tests

Python Playwright testing framework for the BA Assistant Flutter web application.

## Overview

This framework provides end-to-end testing for the BA Assistant application using:

- **Playwright** for browser automation
- **pytest** for test execution
- **Page Object Model (POM)** for maintainable test code
- **Mock OAuth** for authentication testing

## Directory Structure

```
e2e_tests/
├── conftest.py              # Pytest fixtures & configuration
├── pytest.ini               # Pytest settings
├── requirements.txt         # Python dependencies
├── README.md                # This file
│
├── config/
│   ├── settings.py          # Environment config (URLs, timeouts)
│   └── test_users.py        # Test user credentials/tokens
│
├── pages/
│   ├── base_page.py         # Base page class with common methods
│   ├── login_page.py        # Login screen page object
│   ├── home_page.py         # Home screen page object
│   ├── chats_page.py        # Chats screen page object
│   ├── projects_page.py     # Projects list page object
│   ├── project_detail_page.py  # Project detail page object
│   ├── documents_page.py    # Documents page object
│   ├── conversation_page.py # Chat conversation page object
│   └── settings_page.py     # Settings screen page object
│
├── components/
│   ├── navigation.py        # Navigation rail/drawer component
│   ├── breadcrumb.py        # Breadcrumb bar component
│   ├── message_input.py     # Message input component
│   └── dialogs.py           # Dialog components
│
├── utils/
│   ├── auth_helper.py       # Token injection & auth mocking
│   ├── wait_helpers.py      # Custom wait conditions
│   └── test_data.py         # Test data generators
│
└── tests/
    ├── test_auth.py         # Authentication tests
    ├── test_home.py         # Home screen tests
    ├── test_chats.py        # Chats functionality tests
    ├── test_projects.py     # Project CRUD tests
    ├── test_documents.py    # Document upload/view tests
    ├── test_conversation.py # Chat conversation tests
    ├── test_settings.py     # Settings tests
    └── test_navigation.py   # Navigation & routing tests
```

## Setup

### Prerequisites

- Python 3.9+
- Backend running at `http://localhost:8001`
- Frontend running at `http://localhost:5000` (or Flutter web build)

### Installation

```bash
# Navigate to e2e_tests directory
cd e2e_tests

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with browser visible (not headless)
pytest --headed

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_login_page_shows_oauth_buttons

# Run tests by marker
pytest -m smoke          # Quick smoke tests
pytest -m auth           # Authentication tests
pytest -m projects       # Project tests
pytest -m "not slow"     # Skip slow tests
```

### Test Markers

| Marker | Description |
|--------|-------------|
| `smoke` | Quick smoke tests for basic functionality |
| `auth` | Authentication related tests |
| `projects` | Project CRUD tests |
| `documents` | Document upload/view tests |
| `chats` | Chat/conversation tests |
| `navigation` | Navigation and routing tests |
| `settings` | Settings page tests |
| `slow` | Tests that take longer to run |

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

### Reports

```bash
# Generate HTML report
pytest --html=report.html

# Open report
open report.html  # Mac
start report.html # Windows
```

## Configuration

### Environment Variables

Create a `.env` file in the `e2e_tests` directory:

```bash
# URLs
E2E_BASE_URL=http://localhost:8001
E2E_FRONTEND_URL=http://localhost:5000

# Timeouts (milliseconds)
E2E_TIMEOUT_DEFAULT=10000
E2E_TIMEOUT_LONG=30000

# Browser settings
E2E_HEADLESS=true
E2E_SLOW_MO=0

# Viewport
E2E_VIEWPORT_WIDTH=1280
E2E_VIEWPORT_HEIGHT=720
```

### Overriding Settings

```bash
# Run with visible browser
E2E_HEADLESS=false pytest

# Run against different URLs
E2E_FRONTEND_URL=https://staging.example.com pytest
```

## Writing Tests

### Page Object Pattern

Tests use page objects to encapsulate UI interactions:

```python
from pages.projects_page import ProjectsPage

def test_create_project(projects_page: ProjectsPage, test_data):
    """Create a new project."""
    project_name = test_data.project_name()

    projects_page.create_project(project_name)
    projects_page.wait_for_load()

    assert projects_page.project_exists(project_name)
```

### Fixtures

Common fixtures are available in `conftest.py`:

```python
# Unauthenticated page
def test_login_required(page: Page):
    page.goto("/protected")
    # ...

# Authenticated page (auto-injected auth)
def test_home_access(authenticated_page: Page):
    authenticated_page.goto("/home")
    # ...

# Pre-configured page objects
def test_projects(projects_page: ProjectsPage):
    projects_page.create_project("Test")
    # ...

# Test data generators
def test_with_data(test_data: TestDataGenerator):
    name = test_data.project_name()
    # ...
```

### Test Data

Use the `TestDataGenerator` for unique test data:

```python
from utils.test_data import TestDataGenerator

def test_example(test_data: TestDataGenerator):
    project_name = test_data.project_name()       # "Test Project abc123"
    thread_title = test_data.thread_title()       # "Test Thread def456"
    message = test_data.chat_message()            # Random message
    email = test_data.email()                     # "test_ghi789@example.com"
```

### Authentication Mocking

Auth is handled via token injection:

```python
from utils.auth_helper import AuthHelper
from config.test_users import TestUsers

# Inject auth for default user
AuthHelper.authenticate_page(page, TestUsers.DEFAULT)

# Inject auth for admin user
AuthHelper.authenticate_page(page, TestUsers.ADMIN)

# Clear auth
AuthHelper.clear_auth(page)
```

## Debugging

### View Browser

```bash
# Run with visible browser
pytest --headed tests/test_auth.py

# Slow down actions
E2E_SLOW_MO=100 pytest --headed
```

### Screenshots

Failed tests automatically capture screenshots to `e2e_tests/screenshots/`.

### Traces

```bash
# Run with tracing
pytest --tracing on

# View trace
playwright show-trace trace.zip
```

### Playwright Inspector

```bash
# Debug mode
PWDEBUG=1 pytest tests/test_auth.py::test_login -s
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd e2e_tests
          pip install -r requirements.txt
          playwright install chromium

      - name: Start services
        run: |
          # Start your backend and frontend
          docker-compose up -d

      - name: Run tests
        run: |
          cd e2e_tests
          pytest --html=report.html

      - name: Upload report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: e2e_tests/report.html
```

## Troubleshooting

### Browser Installation

```bash
# If browser is not installed
playwright install chromium

# Install all browsers
playwright install
```

### Timeout Issues

```bash
# Increase timeouts
E2E_TIMEOUT_DEFAULT=30000 pytest
```

### Flaky Tests

1. Check for proper waits after actions
2. Use `page.wait_for_load_state("networkidle")`
3. Add explicit waits: `page.wait_for_timeout(500)`

### Authentication Issues

1. Verify `AuthHelper.inject_full_auth()` is called
2. Check localStorage keys match Flutter's storage
3. Ensure API mock intercepts are set up

## Best Practices

1. **Use Page Objects** - Never interact with elements directly in tests
2. **Unique Test Data** - Use `TestDataGenerator` for unique names
3. **Proper Waits** - Always wait for UI updates after actions
4. **Cleanup** - Tests should not depend on each other
5. **Markers** - Tag tests appropriately for selective runs
6. **Assertions** - One clear assertion per test when possible
7. **Documentation** - Add docstrings explaining test steps

## License

Internal use only. Part of the BA Assistant project.
