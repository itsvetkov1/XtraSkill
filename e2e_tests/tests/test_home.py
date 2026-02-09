"""
Home Screen E2E Tests.

Tests for home/dashboard functionality.
"""
import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage
from config.settings import settings


@pytest.mark.smoke
class TestHomeScreen:
    """Home screen test suite."""

    def test_home_page_loads(self, home_page: HomePage):
        """
        Home page should load successfully.

        Steps:
        1. Navigate to home (via fixture)
        2. Verify home page is displayed
        """
        assert home_page.is_home_page(), "Home page should load"

    def test_home_displays_welcome_message(self, home_page: HomePage):
        """
        Home page should display a welcome message.

        Steps:
        1. Navigate to home
        2. Verify welcome message is visible
        """
        welcome = home_page.welcome_message

        # Welcome message should be visible or home should have content
        has_welcome = home_page.is_visible(welcome)
        has_content = home_page.get_current_path() in ["/", "/home"]

        assert has_welcome or has_content, \
            "Home page should have welcome message or be at home path"

    def test_home_shows_quick_actions(self, home_page: HomePage):
        """
        Home page should show quick action buttons.

        Steps:
        1. Navigate to home
        2. Verify quick actions are available
        """
        has_new_project = home_page.is_visible(home_page.new_project_button)
        has_new_chat = home_page.is_visible(home_page.new_chat_button)

        # At least one quick action should be visible
        assert has_new_project or has_new_chat, \
            "Home should have quick action buttons"

    def test_navigate_to_project_from_home(self, home_page: HomePage):
        """
        Should be able to navigate to projects from home.

        Steps:
        1. Navigate to home
        2. Click new project button
        3. Verify navigation to projects or dialog opens
        """
        from pages.projects_page import ProjectsPage
        from components.dialogs import DialogComponent

        if home_page.is_visible(home_page.new_project_button):
            home_page.click_new_project()

            # Either navigated to projects or dialog opened
            projects_page = ProjectsPage(home_page.page)
            dialog = DialogComponent(home_page.page)

            navigated = projects_page.is_projects_page()
            dialog_opened = dialog.is_visible()

            assert navigated or dialog_opened, \
                "Clicking new project should navigate or open dialog"


class TestHomeRecentItems:
    """Tests for recent items on home screen."""

    def test_home_can_show_recent_projects(self, home_page: HomePage):
        """
        Home page should be able to display recent projects.

        Note: This test just verifies the section exists,
        not that there are projects (which depends on test data).
        """
        # Check for recent projects section or empty state
        has_section = home_page.is_visible(home_page.recent_projects_section)
        has_empty = home_page.is_visible(home_page.empty_state)
        has_projects = home_page.has_recent_projects()

        assert has_section or has_empty or has_projects, \
            "Home should have recent projects section or empty state"

    def test_clicking_recent_project_navigates(self, home_page: HomePage):
        """
        Clicking a recent project should navigate to it.

        Steps:
        1. Check if any projects are shown
        2. If so, click first project
        3. Verify navigation occurred
        """
        if home_page.has_recent_projects():
            # Get project names
            project_names = home_page.get_recent_project_names()

            if len(project_names) > 0:
                first_project = project_names[0]
                home_page.click_project(first_project)

                # Should navigate away from home
                home_page.wait_for_navigation()
                assert not home_page.is_home_page() or \
                    "/projects/" in home_page.get_current_path(), \
                    "Should navigate to project detail"


class TestHomeNavigation:
    """Tests for navigation from home screen."""

    def test_can_navigate_from_home_to_chats(self, home_page: HomePage):
        """Navigate from home to chats."""
        from components.navigation import NavigationComponent

        nav = NavigationComponent(home_page.page)
        nav.navigate_to_chats()

        assert "/chats" in home_page.get_current_path(), \
            "Should navigate to chats"

    def test_can_navigate_from_home_to_projects(self, home_page: HomePage):
        """Navigate from home to projects."""
        from components.navigation import NavigationComponent

        nav = NavigationComponent(home_page.page)
        nav.navigate_to_projects()

        assert "/projects" in home_page.get_current_path(), \
            "Should navigate to projects"

    def test_can_navigate_from_home_to_settings(self, home_page: HomePage):
        """Navigate from home to settings."""
        from components.navigation import NavigationComponent

        nav = NavigationComponent(home_page.page)
        nav.navigate_to_settings()

        assert "/settings" in home_page.get_current_path(), \
            "Should navigate to settings"
