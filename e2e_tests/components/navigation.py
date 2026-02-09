"""
Navigation Component for handling navigation rail/drawer.
"""
from playwright.sync_api import Page, Locator
from config.settings import settings
from typing import List


class NavigationComponent:
    """
    Component for the navigation rail/drawer.

    Handles navigation between main sections of the app.
    """

    def __init__(self, page: Page):
        """
        Initialize navigation component.

        Args:
            page: Playwright Page instance
        """
        self.page = page

    # ==================== Locators ====================

    @property
    def navigation_rail(self) -> Locator:
        """Navigation rail (desktop sidebar)."""
        return self.page.locator(
            "[data-testid='navigation-rail'], "
            "nav[role='navigation'], "
            ".navigation-rail"
        )

    @property
    def navigation_drawer(self) -> Locator:
        """Navigation drawer (mobile/tablet)."""
        return self.page.locator(
            "[data-testid='navigation-drawer'], "
            "[role='dialog'] nav, "
            ".navigation-drawer"
        )

    @property
    def menu_button(self) -> Locator:
        """Hamburger menu button (mobile)."""
        return self.page.get_by_role("button", name="Menu")

    @property
    def close_drawer_button(self) -> Locator:
        """Close drawer button."""
        return self.page.get_by_role("button", name="Close")

    # ==================== Navigation Items ====================

    @property
    def home_link(self) -> Locator:
        """Home navigation item."""
        return self.page.locator(
            "[data-testid='nav-home'], "
            "a[href*='/home'], "
            "button:has-text('Home')"
        ).first

    @property
    def chats_link(self) -> Locator:
        """Chats navigation item."""
        return self.page.locator(
            "[data-testid='nav-chats'], "
            "a[href*='/chats'], "
            "button:has-text('Chats')"
        ).first

    @property
    def projects_link(self) -> Locator:
        """Projects navigation item."""
        return self.page.locator(
            "[data-testid='nav-projects'], "
            "a[href*='/projects'], "
            "button:has-text('Projects')"
        ).first

    @property
    def documents_link(self) -> Locator:
        """Documents navigation item."""
        return self.page.locator(
            "[data-testid='nav-documents'], "
            "a[href*='/documents'], "
            "button:has-text('Documents')"
        ).first

    @property
    def settings_link(self) -> Locator:
        """Settings navigation item."""
        return self.page.locator(
            "[data-testid='nav-settings'], "
            "a[href*='/settings'], "
            "button:has-text('Settings')"
        ).first

    @property
    def all_nav_items(self) -> Locator:
        """All navigation items."""
        return self.page.locator(
            "[data-testid^='nav-'], "
            ".nav-item, "
            "nav button"
        )

    # ==================== Actions ====================

    def navigate_to_home(self) -> None:
        """Navigate to Home screen."""
        self._ensure_nav_visible()
        self.home_link.click()
        self._wait_for_navigation()

    def navigate_to_chats(self) -> None:
        """Navigate to Chats screen."""
        self._ensure_nav_visible()
        self.chats_link.click()
        self._wait_for_navigation()

    def navigate_to_projects(self) -> None:
        """Navigate to Projects screen."""
        self._ensure_nav_visible()
        self.projects_link.click()
        self._wait_for_navigation()

    def navigate_to_documents(self) -> None:
        """Navigate to Documents screen."""
        self._ensure_nav_visible()
        self.documents_link.click()
        self._wait_for_navigation()

    def navigate_to_settings(self) -> None:
        """Navigate to Settings screen."""
        self._ensure_nav_visible()
        self.settings_link.click()
        self._wait_for_navigation()

    def open_drawer(self) -> None:
        """Open navigation drawer (mobile)."""
        if not self._is_drawer_visible():
            self.menu_button.click()
            self.navigation_drawer.wait_for(state="visible", timeout=settings.TIMEOUT_SHORT)

    def close_drawer(self) -> None:
        """Close navigation drawer (mobile)."""
        if self._is_drawer_visible():
            self.close_drawer_button.click()
            self.navigation_drawer.wait_for(state="hidden", timeout=settings.TIMEOUT_SHORT)

    # ==================== Queries ====================

    def get_active_item(self) -> str:
        """
        Get the currently active navigation item.

        Returns:
            Name of active item or empty string
        """
        active = self.page.locator(
            "[data-testid^='nav-'][aria-current='page'], "
            ".nav-item.active, "
            "[data-testid^='nav-'].selected"
        ).first

        if active.is_visible():
            return active.text_content() or ""
        return ""

    def get_nav_items(self) -> List[str]:
        """Get list of all navigation item labels."""
        return self.all_nav_items.all_text_contents()

    # ==================== Verification ====================

    def is_visible(self) -> bool:
        """Check if navigation is visible."""
        return (
            self._is_rail_visible() or
            self._is_drawer_visible()
        )

    def is_rail_visible(self) -> bool:
        """Check if navigation rail (desktop) is visible."""
        return self._is_rail_visible()

    def is_drawer_visible(self) -> bool:
        """Check if navigation drawer (mobile) is visible."""
        return self._is_drawer_visible()

    def is_home_active(self) -> bool:
        """Check if Home is the active item."""
        return "home" in self.get_active_item().lower()

    def is_chats_active(self) -> bool:
        """Check if Chats is the active item."""
        return "chats" in self.get_active_item().lower()

    def is_projects_active(self) -> bool:
        """Check if Projects is the active item."""
        return "projects" in self.get_active_item().lower()

    def is_settings_active(self) -> bool:
        """Check if Settings is the active item."""
        return "settings" in self.get_active_item().lower()

    # ==================== Private Methods ====================

    def _is_rail_visible(self) -> bool:
        """Check if navigation rail is visible."""
        try:
            return self.navigation_rail.is_visible()
        except Exception:
            return False

    def _is_drawer_visible(self) -> bool:
        """Check if navigation drawer is visible."""
        try:
            return self.navigation_drawer.is_visible()
        except Exception:
            return False

    def _ensure_nav_visible(self) -> None:
        """Ensure navigation is visible (open drawer on mobile)."""
        if not self.is_visible():
            try:
                self.open_drawer()
            except Exception:
                pass  # Navigation may already be visible in rail mode

    def _wait_for_navigation(self) -> None:
        """Wait for navigation to complete."""
        self.page.wait_for_load_state("networkidle", timeout=settings.TIMEOUT_DEFAULT)
