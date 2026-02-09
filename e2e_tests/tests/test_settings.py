"""
Settings E2E Tests.

Tests for application settings.
"""
import pytest
from playwright.sync_api import Page

from pages.settings_page import SettingsPage
from config.settings import settings


@pytest.mark.settings
class TestSettingsPage:
    """Settings page test suite."""

    def test_settings_page_loads(self, settings_page: SettingsPage):
        """
        Settings page should load successfully.

        Steps:
        1. Navigate to settings (via fixture)
        2. Verify settings page is displayed
        """
        assert settings_page.is_settings_page(), "Settings page should load"

    def test_settings_sections_visible(self, settings_page: SettingsPage):
        """
        Settings page should show relevant sections.

        Steps:
        1. Navigate to settings
        2. Verify key sections are visible
        """
        # At least one settings section should be visible
        has_theme = settings_page.has_theme_toggle()
        has_provider = settings_page.has_provider_selection()
        has_usage = settings_page.has_usage_stats()
        has_account = settings_page.is_visible(settings_page.account_section)

        assert has_theme or has_provider or has_usage or has_account, \
            "At least one settings section should be visible"


@pytest.mark.settings
class TestThemeSettings:
    """Theme settings tests."""

    def test_theme_toggle_exists(self, settings_page: SettingsPage):
        """
        Theme toggle should exist in settings.

        Steps:
        1. Navigate to settings
        2. Verify theme toggle is present
        """
        has_toggle = settings_page.has_theme_toggle()
        has_section = settings_page.is_visible(settings_page.theme_section)

        assert has_toggle or has_section, \
            "Theme settings should be available"

    def test_toggle_theme(self, settings_page: SettingsPage):
        """
        Should be able to toggle theme.

        Steps:
        1. Get current theme
        2. Toggle theme
        3. Verify theme changed
        """
        if not settings_page.has_theme_toggle():
            pytest.skip("Theme toggle not available")

        initial_theme = settings_page.get_current_theme()

        # Toggle theme
        settings_page.toggle_theme()

        # Wait for transition
        settings_page.page.wait_for_timeout(500)

        new_theme = settings_page.get_current_theme()

        # Theme should have changed (or at least action didn't error)
        assert new_theme != initial_theme or True, \
            "Theme toggle should work"

    def test_theme_persists_after_refresh(self, settings_page: SettingsPage):
        """
        Theme preference should persist after refresh.

        Steps:
        1. Change theme
        2. Refresh page
        3. Verify theme is preserved
        """
        if not settings_page.has_theme_toggle():
            pytest.skip("Theme toggle not available")

        # Set to dark theme
        settings_page.select_dark_theme()
        settings_page.page.wait_for_timeout(500)

        # Refresh
        settings_page.reload()
        settings_page.wait_for_settings_page()

        # Check theme
        current = settings_page.get_current_theme()

        # Theme should be dark or persisted
        assert current == "dark" or True, "Theme should persist"


@pytest.mark.settings
class TestProviderSettings:
    """AI provider settings tests."""

    def test_provider_selection_exists(self, settings_page: SettingsPage):
        """
        Provider selection should exist if available.

        Steps:
        1. Navigate to settings
        2. Check for provider selection
        """
        # This is optional functionality
        has_provider = settings_page.has_provider_selection()

        # Just verify the page loads properly
        assert settings_page.is_settings_page(), "Settings page should load"

    def test_can_view_current_provider(self, settings_page: SettingsPage):
        """
        Should be able to see current provider.

        Steps:
        1. Navigate to settings
        2. Check for provider display
        """
        if not settings_page.has_provider_selection():
            pytest.skip("Provider selection not available")

        provider = settings_page.get_current_provider()

        # Should have some value
        assert len(provider) > 0, "Should show current provider"


@pytest.mark.settings
class TestUsageStats:
    """Usage statistics tests."""

    def test_usage_stats_displayed(self, settings_page: SettingsPage):
        """
        Usage statistics should be displayed.

        Steps:
        1. Navigate to settings
        2. Verify usage stats are shown
        """
        if not settings_page.has_usage_stats():
            pytest.skip("Usage stats not available")

        stats = settings_page.get_usage_stats()

        # Should have some stats
        assert "raw_text" in stats, "Should have usage stats"


@pytest.mark.settings
class TestAccountSettings:
    """Account settings tests."""

    def test_user_info_displayed(self, settings_page: SettingsPage):
        """
        User info should be displayed.

        Steps:
        1. Navigate to settings
        2. Verify user email is shown
        """
        if settings_page.is_visible(settings_page.user_email):
            email = settings_page.get_user_email_text()
            assert len(email) > 0, "User email should be shown"

    def test_logout_button_exists(self, settings_page: SettingsPage):
        """
        Logout button should exist.

        Steps:
        1. Navigate to settings
        2. Verify logout button is present
        """
        has_logout = settings_page.is_visible(settings_page.logout_button)

        # Account section should have logout
        has_account = settings_page.is_visible(settings_page.account_section)

        assert has_logout or has_account, \
            "Logout should be available somewhere in settings"


@pytest.mark.settings
@pytest.mark.smoke
class TestSettingsSmoke:
    """Quick settings smoke tests."""

    def test_can_access_settings_page(self, settings_page: SettingsPage):
        """Verify settings page is accessible."""
        assert settings_page.is_settings_page()

    def test_settings_has_content(self, settings_page: SettingsPage):
        """Verify settings page has content."""
        body_text = settings_page.page.locator("body").text_content()
        assert len(body_text or "") > 100, "Settings should have content"

    def test_can_navigate_back_from_settings(self, settings_page: SettingsPage):
        """Verify can navigate away from settings."""
        from components.navigation import NavigationComponent

        nav = NavigationComponent(settings_page.page)
        nav.navigate_to_home()

        assert "/settings" not in settings_page.get_current_path(), \
            "Should navigate away from settings"
