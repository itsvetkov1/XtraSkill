"""
Pytest configuration and fixtures for E2E tests.
"""
import pytest
import os
import sys
from datetime import datetime
from typing import Generator
from playwright.sync_api import (
    Page,
    Browser,
    BrowserContext,
    Playwright,
    sync_playwright,
)

# Add e2e_tests to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from config.test_users import TestUsers, TestUser
from utils.auth_helper import AuthHelper
from utils.test_data import TestDataGenerator


# ==================== Browser Fixtures ====================

@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    """Provide a Playwright instance for the test session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Generator[Browser, None, None]:
    """
    Provide a browser instance for the test session.

    Uses Chromium by default, configurable via settings.
    """
    browser = playwright_instance.chromium.launch(
        headless=settings.HEADLESS,
        slow_mo=settings.SLOW_MO,
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Provide a fresh browser context for each test.

    Each test gets an isolated context with its own cookies,
    localStorage, and session state.
    """
    context = browser.new_context(
        viewport={
            "width": settings.VIEWPORT_WIDTH,
            "height": settings.VIEWPORT_HEIGHT,
        },
        base_url=settings.FRONTEND_URL,
    )

    # Set default timeout
    context.set_default_timeout(settings.TIMEOUT_DEFAULT)

    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """
    Provide a fresh page for each test.

    This page is NOT authenticated - use `authenticated_page`
    for tests that require login.
    """
    page = context.new_page()
    yield page
    page.close()


# ==================== Authenticated Fixtures ====================

@pytest.fixture(scope="function")
def authenticated_context(
    browser: Browser
) -> Generator[BrowserContext, None, None]:
    """
    Provide an authenticated browser context.

    Sets up auth interception and token injection.
    """
    context = browser.new_context(
        viewport={
            "width": settings.VIEWPORT_WIDTH,
            "height": settings.VIEWPORT_HEIGHT,
        },
        base_url=settings.FRONTEND_URL,
    )
    context.set_default_timeout(settings.TIMEOUT_DEFAULT)

    # Set up auth mocking
    AuthHelper.setup_authenticated_context(context)

    yield context
    context.close()


@pytest.fixture(scope="function")
def authenticated_page(
    authenticated_context: BrowserContext
) -> Generator[Page, None, None]:
    """
    Provide an authenticated page.

    The page is pre-authenticated with the default test user.
    """
    page = authenticated_context.new_page()

    # Navigate and inject auth
    page.goto(settings.FRONTEND_URL)
    AuthHelper.inject_full_auth(page, TestUsers.DEFAULT)
    page.reload()

    yield page
    page.close()


@pytest.fixture(scope="function")
def auth_as_admin(
    authenticated_context: BrowserContext
) -> Generator[Page, None, None]:
    """
    Provide a page authenticated as admin user.
    """
    page = authenticated_context.new_page()
    page.goto(settings.FRONTEND_URL)
    AuthHelper.inject_full_auth(page, TestUsers.ADMIN)
    page.reload()
    yield page
    page.close()


# ==================== Page Object Fixtures ====================

@pytest.fixture
def login_page(page: Page):
    """Provide LoginPage instance."""
    from pages.login_page import LoginPage
    return LoginPage(page)


@pytest.fixture
def home_page(authenticated_page: Page):
    """Provide authenticated HomePage instance."""
    from pages.home_page import HomePage
    hp = HomePage(authenticated_page)
    hp.navigate_to("/home")
    return hp


@pytest.fixture
def chats_page(authenticated_page: Page):
    """Provide authenticated ChatsPage instance."""
    from pages.chats_page import ChatsPage
    cp = ChatsPage(authenticated_page)
    cp.navigate_to("/chats")
    return cp


@pytest.fixture
def projects_page(authenticated_page: Page):
    """Provide authenticated ProjectsPage instance."""
    from pages.projects_page import ProjectsPage
    pp = ProjectsPage(authenticated_page)
    pp.navigate_to("/projects")
    return pp


@pytest.fixture
def documents_page(authenticated_page: Page):
    """Provide authenticated DocumentsPage instance."""
    from pages.documents_page import DocumentsPage
    dp = DocumentsPage(authenticated_page)
    dp.navigate_to("/documents")
    return dp


@pytest.fixture
def settings_page(authenticated_page: Page):
    """Provide authenticated SettingsPage instance."""
    from pages.settings_page import SettingsPage
    sp = SettingsPage(authenticated_page)
    sp.navigate_to("/settings")
    return sp


# ==================== Component Fixtures ====================

@pytest.fixture
def navigation(authenticated_page: Page):
    """Provide NavigationComponent instance."""
    from components.navigation import NavigationComponent
    return NavigationComponent(authenticated_page)


@pytest.fixture
def dialog(authenticated_page: Page):
    """Provide DialogComponent instance."""
    from components.dialogs import DialogComponent
    return DialogComponent(authenticated_page)


@pytest.fixture
def breadcrumb(authenticated_page: Page):
    """Provide BreadcrumbComponent instance."""
    from components.breadcrumb import BreadcrumbComponent
    return BreadcrumbComponent(authenticated_page)


# ==================== Test Data Fixtures ====================

@pytest.fixture
def test_data() -> TestDataGenerator:
    """Provide TestDataGenerator instance."""
    return TestDataGenerator()


@pytest.fixture
def test_user() -> TestUser:
    """Provide default test user."""
    return TestUsers.DEFAULT


@pytest.fixture
def test_file(test_data: TestDataGenerator) -> Generator[str, None, None]:
    """
    Provide a temporary test file.

    The file is automatically cleaned up after the test.
    """
    file_path = test_data.create_test_file()
    yield file_path
    try:
        os.remove(file_path)
    except Exception:
        pass


@pytest.fixture
def test_pdf(test_data: TestDataGenerator) -> Generator[str, None, None]:
    """
    Provide a temporary test PDF file.
    """
    file_path = test_data.create_pdf_test_file()
    yield file_path
    try:
        os.remove(file_path)
    except Exception:
        pass


# ==================== Screenshot Fixtures ====================

@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page: Page):
    """
    Automatically take screenshot on test failure.

    This fixture runs after each test and captures a screenshot
    if the test failed.
    """
    yield

    # Check if test failed
    rep_call = getattr(request.node, 'rep_call', None)
    if rep_call and rep_call.failed:
        # Ensure screenshot directory exists
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)

        # Generate screenshot filename
        test_name = request.node.name.replace("/", "_").replace(":", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_name}_{timestamp}.png"
        filepath = os.path.join(settings.SCREENSHOT_DIR, filename)

        try:
            page.screenshot(path=filepath, full_page=True)
            print(f"\nScreenshot saved: {filepath}")
        except Exception as e:
            print(f"\nFailed to capture screenshot: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Make test result available in fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ==================== Cleanup Fixtures ====================

@pytest.fixture(autouse=True, scope="session")
def cleanup_test_files():
    """Clean up test files after all tests complete."""
    yield
    TestDataGenerator.cleanup_test_files()


# ==================== API Fixtures ====================

@pytest.fixture
def api_client():
    """
    Provide an API client for direct backend testing.

    Returns a requests session pre-configured with auth headers.
    """
    import requests

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TestUsers.generate_token(TestUsers.DEFAULT)}",
    })

    return session


# ==================== Markers ====================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "projects: Project CRUD tests")
    config.addinivalue_line("markers", "documents: Document tests")
    config.addinivalue_line("markers", "chats: Chat/conversation tests")
    config.addinivalue_line("markers", "navigation: Navigation tests")
    config.addinivalue_line("markers", "settings: Settings tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
