"""
Breadcrumb Component for navigation trail.
"""
from playwright.sync_api import Page, Locator
from config.settings import settings
from typing import List


class BreadcrumbComponent:
    """
    Component for the breadcrumb navigation bar.

    Handles breadcrumb navigation and verification.
    """

    def __init__(self, page: Page):
        """
        Initialize breadcrumb component.

        Args:
            page: Playwright Page instance
        """
        self.page = page

    # ==================== Locators ====================

    @property
    def breadcrumb_bar(self) -> Locator:
        """Breadcrumb bar container."""
        return self.page.locator(
            "[data-testid='breadcrumb'], "
            "nav[aria-label='Breadcrumb'], "
            ".breadcrumb"
        )

    @property
    def breadcrumb_items(self) -> Locator:
        """All breadcrumb items."""
        return self.breadcrumb_bar.locator(
            "[data-testid='breadcrumb-item'], "
            "a, button, "
            ".breadcrumb-item"
        )

    @property
    def home_crumb(self) -> Locator:
        """Home breadcrumb item."""
        return self.breadcrumb_bar.locator("a[href*='/home'], button:has-text('Home')").first

    @property
    def current_crumb(self) -> Locator:
        """Current/last breadcrumb item."""
        return self.breadcrumb_items.last

    @property
    def separators(self) -> Locator:
        """Breadcrumb separators."""
        return self.breadcrumb_bar.locator(
            "[data-testid='breadcrumb-separator'], "
            ".separator, "
            "span:has-text('/')"
        )

    # ==================== Actions ====================

    def click_crumb(self, text: str) -> None:
        """
        Click a breadcrumb item by text.

        Args:
            text: Breadcrumb item text
        """
        crumb = self.breadcrumb_items.filter(has_text=text).first
        crumb.click()
        self._wait_for_navigation()

    def click_home(self) -> None:
        """Click the home breadcrumb."""
        self.home_crumb.click()
        self._wait_for_navigation()

    def click_crumb_at_index(self, index: int) -> None:
        """
        Click a breadcrumb at specific index.

        Args:
            index: 0-based index
        """
        self.breadcrumb_items.nth(index).click()
        self._wait_for_navigation()

    def click_parent(self) -> None:
        """Click the parent breadcrumb (second to last)."""
        count = self.breadcrumb_items.count()
        if count > 1:
            self.breadcrumb_items.nth(count - 2).click()
            self._wait_for_navigation()

    # ==================== Queries ====================

    def get_crumb_texts(self) -> List[str]:
        """
        Get text of all breadcrumb items.

        Returns:
            List of breadcrumb texts
        """
        return self.breadcrumb_items.all_text_contents()

    def get_current_text(self) -> str:
        """
        Get text of current (last) breadcrumb.

        Returns:
            Current breadcrumb text
        """
        if self.current_crumb.is_visible():
            return self.current_crumb.text_content() or ""
        return ""

    def get_crumb_count(self) -> int:
        """Get number of breadcrumb items."""
        return self.breadcrumb_items.count()

    def get_full_path(self) -> str:
        """
        Get the full breadcrumb path as a string.

        Returns:
            Path like "Home > Projects > My Project"
        """
        texts = self.get_crumb_texts()
        return " > ".join(texts)

    # ==================== Verification ====================

    def is_visible(self) -> bool:
        """Check if breadcrumb bar is visible."""
        try:
            return self.breadcrumb_bar.is_visible()
        except Exception:
            return False

    def has_crumb(self, text: str) -> bool:
        """
        Check if a breadcrumb with given text exists.

        Args:
            text: Breadcrumb text to find

        Returns:
            True if found
        """
        crumb = self.breadcrumb_items.filter(has_text=text)
        return crumb.count() > 0

    def is_at_root(self) -> bool:
        """Check if at root level (only home crumb)."""
        return self.get_crumb_count() <= 1

    def verify_path(self, expected_path: List[str]) -> bool:
        """
        Verify the breadcrumb path matches expected.

        Args:
            expected_path: Expected list of breadcrumb texts

        Returns:
            True if matches
        """
        actual = self.get_crumb_texts()
        return actual == expected_path

    def current_is(self, expected: str) -> bool:
        """
        Check if current breadcrumb matches expected.

        Args:
            expected: Expected current breadcrumb text

        Returns:
            True if matches
        """
        return expected.lower() in self.get_current_text().lower()

    # ==================== Private Methods ====================

    def _wait_for_navigation(self) -> None:
        """Wait for navigation to complete."""
        self.page.wait_for_load_state("networkidle", timeout=settings.TIMEOUT_DEFAULT)
