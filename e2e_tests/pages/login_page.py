"""
Login Page Object for authentication testing.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class LoginPage(BasePage):
    """
    Page Object for the Login screen.

    Handles login UI interactions and verification.
    """

    # ==================== Locators ====================

    @property
    def google_login_button(self) -> Locator:
        """Google login button."""
        # Flutter web renders to canvas - try multiple selectors
        return self.page.locator("text=Sign in with Google, text=Google, flt-semantics:has-text('Google')").first

    @property
    def microsoft_login_button(self) -> Locator:
        """Microsoft login button."""
        return self.page.locator("text=Sign in with Microsoft, text=Microsoft, flt-semantics:has-text('Microsoft')").first

    @property
    def app_logo(self) -> Locator:
        """Application logo on login screen."""
        return self.page.locator("[data-testid='app-logo'], .app-logo, img[alt*='logo' i]")

    @property
    def login_title(self) -> Locator:
        """Login screen title - this text IS exposed in Flutter's accessibility tree."""
        return self.page.get_by_text("Business Analyst Assistant")

    @property
    def login_subtitle(self) -> Locator:
        """Login screen subtitle/description."""
        return self.page.get_by_text("AI-powered requirement discovery")

    @property
    def error_message(self) -> Locator:
        """Error message display."""
        return self.page.locator("[role='alert'], .error-message")

    # ==================== Actions ====================

    def login_with_google(self) -> None:
        """Click the Google login button."""
        self.click(self.google_login_button)

    def login_with_microsoft(self) -> None:
        """Click the Microsoft login button."""
        self.click(self.microsoft_login_button)

    # ==================== Verification ====================

    def is_login_page(self, timeout: int = 10000) -> bool:
        """
        Verify we are on the login page.

        Flutter web renders to canvas, so we primarily use URL-based checks
        and verify the title text that IS exposed in the accessibility tree.

        Args:
            timeout: Time to wait for elements

        Returns:
            True if on login page, False otherwise
        """
        # Check URL first (most reliable for Flutter)
        if "/login" in self.get_current_path():
            return True

        # Check for title text that Flutter DOES expose
        return self.is_visible(self.login_title, timeout=timeout)

    def wait_for_login_page(self, timeout: int = 15000) -> None:
        """Wait for login page to be fully loaded."""
        # Wait for Flutter to load
        self.page.wait_for_load_state("networkidle")

        # Check if already on login page
        if "/login" in self.page.url:
            self.page.wait_for_timeout(1000)
            # Enable accessibility for element detection
            self._enable_flutter_accessibility()
            self.page.wait_for_timeout(500)
            return

        # Wait for URL to contain /login (most reliable for Flutter)
        self.page.wait_for_url("**/login**", timeout=timeout)

        # Enable accessibility for element detection
        self._enable_flutter_accessibility()

        # Extra wait for Flutter render
        self.page.wait_for_timeout(500)

    def _enable_flutter_accessibility(self) -> None:
        """Enable Flutter's accessibility mode for better element detection."""
        try:
            # Press Tab to focus the accessibility button, then Enter to activate
            self.page.keyboard.press("Tab")
            self.page.wait_for_timeout(300)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(500)
        except Exception:
            pass  # Accessibility may already be enabled

    def get_error_message(self) -> str:
        """Get the current error message text."""
        if self.is_visible(self.error_message):
            return self.get_text(self.error_message)
        return ""

    def has_error(self) -> bool:
        """Check if an error message is displayed."""
        return self.is_visible(self.error_message)
