"""
Base Page Object with common methods for all page objects.
"""
from playwright.sync_api import Page, Locator, expect
from config.settings import settings
from utils.wait_helpers import WaitHelpers
from typing import Optional, List
import re


class BasePage:
    """
    Base class for all page objects.

    Provides common methods for navigation, element interaction, and waits.
    All page objects should inherit from this class.
    """

    def __init__(self, page: Page):
        """
        Initialize base page.

        Args:
            page: Playwright Page instance
        """
        self.page = page
        self.waits = WaitHelpers()

    # ==================== Navigation ====================

    def navigate_to(self, path: str = "") -> None:
        """
        Navigate to a specific path.

        Args:
            path: URL path (e.g., "/projects", "/chats")
        """
        url = settings.get_frontend_url(path)
        self.page.goto(url)
        self.wait_for_load()

    def get_current_url(self) -> str:
        """Get the current page URL."""
        return self.page.url

    def get_current_path(self) -> str:
        """Get the current URL path (without base URL)."""
        url = self.page.url
        base = settings.FRONTEND_URL.rstrip("/")
        return url.replace(base, "") or "/"

    def reload(self) -> None:
        """Reload the current page."""
        self.page.reload()
        self.wait_for_load()

    def go_back(self) -> None:
        """Navigate back in browser history."""
        self.page.go_back()
        self.wait_for_load()

    def go_forward(self) -> None:
        """Navigate forward in browser history."""
        self.page.go_forward()
        self.wait_for_load()

    # ==================== Wait Methods ====================

    def wait_for_load(self, timeout: int = None) -> None:
        """Wait for page to fully load."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        # Additional wait for Flutter animations
        self.page.wait_for_timeout(500)
        # Enable Flutter accessibility for better element detection
        self._enable_flutter_accessibility()

    def _enable_flutter_accessibility(self) -> None:
        """
        Enable Flutter's accessibility mode for better element detection.

        Flutter web renders to canvas by default. Pressing Tab then Enter
        activates the accessibility tree, making elements findable.
        """
        try:
            # Check if accessibility button exists and click it
            accessibility_btn = self.page.locator("text=Enable accessibility")
            if accessibility_btn.count() > 0:
                self.page.keyboard.press("Tab")
                self.page.wait_for_timeout(200)
                self.page.keyboard.press("Enter")
                self.page.wait_for_timeout(300)
        except Exception:
            pass  # Accessibility may already be enabled or not needed

    def wait_for_navigation(self, url_pattern: str = None, timeout: int = None) -> None:
        """
        Wait for navigation to complete.

        Args:
            url_pattern: Optional URL pattern to wait for
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        if url_pattern:
            self.page.wait_for_url(url_pattern, timeout=timeout)
        else:
            self.page.wait_for_load_state("networkidle", timeout=timeout)

    def wait_for_element(
        self,
        locator: Locator,
        state: str = "visible",
        timeout: int = None
    ) -> None:
        """
        Wait for element to reach a specific state.

        Args:
            locator: Element locator
            state: "visible", "hidden", "attached", "detached"
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        locator.wait_for(state=state, timeout=timeout)

    # ==================== Element Interaction ====================

    def click(
        self,
        locator: Locator,
        timeout: int = None,
        force: bool = False
    ) -> None:
        """
        Click an element with auto-wait.

        Args:
            locator: Element to click
            timeout: Timeout in ms
            force: Force click even if element is not visible
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        locator.click(timeout=timeout, force=force)

    def fill(
        self,
        locator: Locator,
        text: str,
        timeout: int = None
    ) -> None:
        """
        Fill a text input with value.

        Args:
            locator: Input element
            text: Text to enter
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        locator.fill(text, timeout=timeout)

    def clear_and_fill(
        self,
        locator: Locator,
        text: str,
        timeout: int = None
    ) -> None:
        """Clear an input and fill with new value."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        locator.clear(timeout=timeout)
        locator.fill(text, timeout=timeout)

    def type_text(
        self,
        locator: Locator,
        text: str,
        delay: int = 50
    ) -> None:
        """
        Type text character by character (simulates real typing).

        Args:
            locator: Input element
            text: Text to type
            delay: Delay between keystrokes in ms
        """
        locator.type(text, delay=delay)

    def select_option(
        self,
        locator: Locator,
        value: str = None,
        label: str = None,
        index: int = None
    ) -> None:
        """
        Select an option from a dropdown.

        Args:
            locator: Select element
            value: Option value
            label: Option label text
            index: Option index
        """
        if value:
            locator.select_option(value=value)
        elif label:
            locator.select_option(label=label)
        elif index is not None:
            locator.select_option(index=index)

    def check(self, locator: Locator) -> None:
        """Check a checkbox or radio button."""
        locator.check()

    def uncheck(self, locator: Locator) -> None:
        """Uncheck a checkbox."""
        locator.uncheck()

    def hover(self, locator: Locator) -> None:
        """Hover over an element."""
        locator.hover()

    def scroll_into_view(self, locator: Locator) -> None:
        """Scroll element into view."""
        locator.scroll_into_view_if_needed()

    # ==================== Element Query ====================

    def get_text(self, locator: Locator, timeout: int = None) -> str:
        """
        Get text content of an element.

        Args:
            locator: Element locator
            timeout: Timeout in ms

        Returns:
            Element text content
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        locator.wait_for(state="visible", timeout=timeout)
        return locator.text_content() or ""

    def get_inner_text(self, locator: Locator) -> str:
        """Get inner text of an element (visible text only)."""
        return locator.inner_text()

    def get_attribute(self, locator: Locator, name: str) -> Optional[str]:
        """Get an attribute value from an element."""
        return locator.get_attribute(name)

    def get_input_value(self, locator: Locator) -> str:
        """Get the current value of an input element."""
        return locator.input_value()

    def is_visible(self, locator: Locator, timeout: int = None) -> bool:
        """
        Check if an element is visible.

        Args:
            locator: Element locator
            timeout: Time to wait for visibility check

        Returns:
            True if visible, False otherwise
        """
        try:
            timeout = timeout or settings.TIMEOUT_SHORT
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_hidden(self, locator: Locator) -> bool:
        """Check if an element is hidden."""
        return not locator.is_visible()

    def is_enabled(self, locator: Locator) -> bool:
        """Check if an element is enabled."""
        return locator.is_enabled()

    def is_checked(self, locator: Locator) -> bool:
        """Check if a checkbox/radio is checked."""
        return locator.is_checked()

    def count(self, locator: Locator) -> int:
        """Count elements matching a locator."""
        return locator.count()

    def get_all_texts(self, locator: Locator) -> List[str]:
        """Get text content of all matching elements."""
        return locator.all_text_contents()

    # ==================== Locator Helpers ====================

    def locator(self, selector: str) -> Locator:
        """Create a locator from a selector."""
        return self.page.locator(selector)

    def get_by_role(
        self,
        role: str,
        name: str = None,
        exact: bool = False
    ) -> Locator:
        """
        Get element by ARIA role.

        Args:
            role: ARIA role (button, link, textbox, etc.)
            name: Accessible name
            exact: Exact name match
        """
        if name:
            return self.page.get_by_role(role, name=name, exact=exact)
        return self.page.get_by_role(role)

    def get_by_text(self, text: str, exact: bool = False) -> Locator:
        """Get element by text content."""
        return self.page.get_by_text(text, exact=exact)

    def get_by_label(self, label: str, exact: bool = False) -> Locator:
        """Get element by label text."""
        return self.page.get_by_label(label, exact=exact)

    def get_by_placeholder(self, placeholder: str, exact: bool = False) -> Locator:
        """Get element by placeholder text."""
        return self.page.get_by_placeholder(placeholder, exact=exact)

    def get_by_test_id(self, test_id: str) -> Locator:
        """Get element by data-testid attribute."""
        return self.page.get_by_test_id(test_id)

    # ==================== Assertions ====================

    def assert_visible(self, locator: Locator, timeout: int = None) -> None:
        """Assert that an element is visible."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_be_visible(timeout=timeout)

    def assert_hidden(self, locator: Locator, timeout: int = None) -> None:
        """Assert that an element is hidden."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_be_hidden(timeout=timeout)

    def assert_text(
        self,
        locator: Locator,
        expected: str,
        timeout: int = None
    ) -> None:
        """Assert element contains expected text."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_contain_text(expected, timeout=timeout)

    def assert_url_contains(self, expected: str, timeout: int = None) -> None:
        """Assert current URL contains expected string."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(self.page).to_have_url(re.compile(f".*{expected}.*"), timeout=timeout)

    def assert_title(self, expected: str, timeout: int = None) -> None:
        """Assert page title matches."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(self.page).to_have_title(expected, timeout=timeout)

    # ==================== Screenshots ====================

    def take_screenshot(self, name: str = None, full_page: bool = False) -> bytes:
        """
        Take a screenshot.

        Args:
            name: Screenshot filename (without extension)
            full_page: Capture full scrollable page

        Returns:
            Screenshot bytes
        """
        return self.page.screenshot(full_page=full_page)

    def screenshot_element(self, locator: Locator) -> bytes:
        """Take a screenshot of a specific element."""
        return locator.screenshot()

    # ==================== Keyboard ====================

    def press_key(self, key: str) -> None:
        """
        Press a keyboard key.

        Args:
            key: Key name (Enter, Escape, Tab, etc.)
        """
        self.page.keyboard.press(key)

    def press_enter(self) -> None:
        """Press Enter key."""
        self.press_key("Enter")

    def press_escape(self) -> None:
        """Press Escape key."""
        self.press_key("Escape")

    def press_tab(self) -> None:
        """Press Tab key."""
        self.press_key("Tab")

    # ==================== JavaScript Execution ====================

    def evaluate(self, expression: str):
        """
        Evaluate JavaScript expression.

        Args:
            expression: JavaScript code

        Returns:
            Result of evaluation
        """
        return self.page.evaluate(expression)

    def evaluate_on_element(self, locator: Locator, expression: str):
        """
        Evaluate JavaScript on an element.

        Args:
            locator: Element locator
            expression: JavaScript function (element) => ...

        Returns:
            Result of evaluation
        """
        return locator.evaluate(expression)
