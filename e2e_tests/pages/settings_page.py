"""
Settings Page Object for application settings.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from typing import Optional


class SettingsPage(BasePage):
    """
    Page Object for the Settings screen.

    Handles settings interactions including theme,
    AI provider selection, and usage statistics.
    """

    # ==================== Locators ====================

    @property
    def page_title(self) -> Locator:
        """Page title/header."""
        return self.page.get_by_role("heading", name="Settings")

    @property
    def back_button(self) -> Locator:
        """Back navigation button."""
        return self.page.get_by_role("button", name="Back")

    # ==================== Theme Settings ====================

    @property
    def theme_section(self) -> Locator:
        """Theme settings section."""
        return self.page.locator("[data-testid='theme-section'], .theme-section")

    @property
    def theme_toggle(self) -> Locator:
        """Theme toggle switch (light/dark)."""
        return self.page.locator(
            "[data-testid='theme-toggle'], "
            "[role='switch'][aria-label*='theme' i], "
            "button[aria-label*='theme' i]"
        )

    @property
    def light_theme_option(self) -> Locator:
        """Light theme option."""
        return self.page.get_by_role("radio", name="Light")

    @property
    def dark_theme_option(self) -> Locator:
        """Dark theme option."""
        return self.page.get_by_role("radio", name="Dark")

    @property
    def system_theme_option(self) -> Locator:
        """System theme option."""
        return self.page.get_by_role("radio", name="System")

    # ==================== AI Provider Settings ====================

    @property
    def provider_section(self) -> Locator:
        """AI provider settings section."""
        return self.page.locator("[data-testid='provider-section'], .provider-section")

    @property
    def provider_dropdown(self) -> Locator:
        """AI provider dropdown/selector."""
        return self.page.locator(
            "[data-testid='provider-dropdown'], "
            "[role='combobox'][aria-label*='provider' i]"
        )

    @property
    def api_key_input(self) -> Locator:
        """API key input field."""
        return self.page.locator(
            "[data-testid='api-key-input'], "
            "input[type='password'][placeholder*='API' i]"
        )

    @property
    def save_api_key_button(self) -> Locator:
        """Save API key button."""
        return self.page.get_by_role("button", name="Save")

    # ==================== Usage Statistics ====================

    @property
    def usage_section(self) -> Locator:
        """Usage statistics section."""
        return self.page.locator("[data-testid='usage-section'], .usage-section")

    @property
    def token_usage_display(self) -> Locator:
        """Token usage display."""
        return self.page.locator("[data-testid='token-usage'], .token-usage")

    @property
    def usage_reset_button(self) -> Locator:
        """Reset usage statistics button."""
        return self.page.get_by_role("button", name="Reset")

    # ==================== Account Settings ====================

    @property
    def account_section(self) -> Locator:
        """Account settings section."""
        return self.page.locator("[data-testid='account-section'], .account-section")

    @property
    def user_email(self) -> Locator:
        """User email display."""
        return self.page.locator("[data-testid='user-email'], .user-email")

    @property
    def logout_button(self) -> Locator:
        """Logout button."""
        return self.page.get_by_role("button", name="Logout")

    @property
    def delete_account_button(self) -> Locator:
        """Delete account button."""
        return self.page.get_by_role("button", name="Delete Account")

    # ==================== Theme Actions ====================

    def toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        self.click(self.theme_toggle)

    def select_light_theme(self) -> None:
        """Select light theme."""
        if self.is_visible(self.light_theme_option):
            self.click(self.light_theme_option)
        else:
            # Toggle if currently dark
            if self.get_current_theme() == "dark":
                self.toggle_theme()

    def select_dark_theme(self) -> None:
        """Select dark theme."""
        if self.is_visible(self.dark_theme_option):
            self.click(self.dark_theme_option)
        else:
            # Toggle if currently light
            if self.get_current_theme() == "light":
                self.toggle_theme()

    def select_system_theme(self) -> None:
        """Select system theme."""
        self.click(self.system_theme_option)

    def get_current_theme(self) -> str:
        """
        Get the currently active theme.

        Returns:
            "light", "dark", or "system"
        """
        # Check for theme attribute on body or html
        theme = self.evaluate("""
            () => {
                const html = document.documentElement;
                const body = document.body;
                return html.getAttribute('data-theme') ||
                       body.getAttribute('data-theme') ||
                       (body.classList.contains('dark') ? 'dark' : 'light');
            }
        """)
        return theme or "light"

    # ==================== Provider Actions ====================

    def select_provider(self, provider_name: str) -> None:
        """
        Select an AI provider.

        Args:
            provider_name: Provider name (e.g., "OpenAI", "Anthropic")
        """
        self.click(self.provider_dropdown)
        option = self.page.get_by_role("option", name=provider_name)
        self.click(option)

    def get_current_provider(self) -> str:
        """Get the currently selected provider."""
        return self.get_text(self.provider_dropdown)

    def set_api_key(self, api_key: str) -> None:
        """
        Set the API key.

        Args:
            api_key: API key value
        """
        self.fill(self.api_key_input, api_key)
        self.click(self.save_api_key_button)

    # ==================== Usage Actions ====================

    def get_usage_stats(self) -> dict:
        """
        Get usage statistics.

        Returns:
            Dictionary with usage info
        """
        text = self.get_text(self.token_usage_display)
        return {"raw_text": text}

    def reset_usage(self) -> None:
        """Reset usage statistics."""
        self.click(self.usage_reset_button)

        # Confirm in dialog if present
        dialog = self.page.locator("[role='dialog']")
        if self.is_visible(dialog, timeout=1000):
            confirm = dialog.get_by_role("button", name="Reset")
            self.click(confirm)

    # ==================== Account Actions ====================

    def get_user_email_text(self) -> str:
        """Get the displayed user email."""
        return self.get_text(self.user_email)

    def logout(self) -> None:
        """Log out of the application."""
        self.click(self.logout_button)

        # Confirm in dialog if present
        dialog = self.page.locator("[role='dialog']")
        if self.is_visible(dialog, timeout=1000):
            confirm = dialog.get_by_role("button", name="Logout")
            self.click(confirm)

    def delete_account(self) -> None:
        """Delete the user account (use with caution)."""
        self.click(self.delete_account_button)

        # Confirm in dialog
        dialog = self.page.locator("[role='dialog']")
        self.wait_for_element(dialog)
        confirm = dialog.get_by_role("button", name="Delete")
        self.click(confirm)

    # ==================== Navigation ====================

    def go_back(self) -> None:
        """Navigate back to previous screen."""
        self.click(self.back_button)

    # ==================== Verification ====================

    def is_settings_page(self) -> bool:
        """
        Verify we are on the settings page.

        Returns:
            True if on settings page, False otherwise
        """
        return (
            "/settings" in self.get_current_path() or
            self.is_visible(self.page_title)
        )

    def wait_for_settings_page(self) -> None:
        """Wait for settings page to be fully loaded."""
        self.wait_for_load()
        try:
            self.wait_for_element(self.page_title, timeout=5000)
        except Exception:
            pass

    def has_theme_toggle(self) -> bool:
        """Check if theme toggle is available."""
        return self.is_visible(self.theme_toggle)

    def has_provider_selection(self) -> bool:
        """Check if provider selection is available."""
        return self.is_visible(self.provider_dropdown)

    def has_usage_stats(self) -> bool:
        """Check if usage statistics are displayed."""
        return self.is_visible(self.token_usage_display)
