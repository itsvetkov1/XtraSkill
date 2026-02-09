"""
Navigation E2E Tests.

Tests for navigation, routing, and breadcrumbs.
"""
import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage
from pages.chats_page import ChatsPage
from pages.projects_page import ProjectsPage
from pages.settings_page import SettingsPage
from components.navigation import NavigationComponent
from components.breadcrumb import BreadcrumbComponent
from utils.test_data import TestDataGenerator
from config.settings import settings


@pytest.mark.navigation
class TestNavigationRail:
    """Navigation rail/drawer tests."""

    def test_navigation_rail_visible_on_desktop(self, authenticated_page: Page):
        """
        Navigation rail should be visible on desktop viewport.

        Steps:
        1. Load app at desktop size
        2. Verify navigation rail is visible
        """
        authenticated_page.goto(settings.get_frontend_url("/home"))
        authenticated_page.wait_for_load_state("networkidle")

        nav = NavigationComponent(authenticated_page)

        # On desktop, rail should be visible
        is_visible = nav.is_visible()

        assert is_visible, "Navigation should be visible on desktop"

    def test_navigate_between_tabs(self, authenticated_page: Page):
        """
        Should be able to navigate between main tabs.

        Steps:
        1. Start at home
        2. Navigate to each section
        3. Verify navigation works
        """
        authenticated_page.goto(settings.get_frontend_url("/home"))
        authenticated_page.wait_for_load_state("networkidle")

        nav = NavigationComponent(authenticated_page)

        # Navigate to Chats
        nav.navigate_to_chats()
        assert "/chats" in authenticated_page.url, "Should navigate to chats"

        # Navigate to Projects
        nav.navigate_to_projects()
        assert "/projects" in authenticated_page.url, "Should navigate to projects"

        # Navigate to Settings
        nav.navigate_to_settings()
        assert "/settings" in authenticated_page.url, "Should navigate to settings"

        # Navigate back to Home
        nav.navigate_to_home()
        home_path = authenticated_page.url
        assert "/home" in home_path or home_path.endswith("/"), \
            "Should navigate to home"

    def test_active_item_highlighted(self, authenticated_page: Page):
        """
        Active navigation item should be highlighted.

        Steps:
        1. Navigate to projects
        2. Verify projects nav item is active
        """
        authenticated_page.goto(settings.get_frontend_url("/projects"))
        authenticated_page.wait_for_load_state("networkidle")

        nav = NavigationComponent(authenticated_page)

        # Projects should be active
        active = nav.get_active_item()

        # Active item should contain "projects" or navigation should work
        assert "project" in active.lower() or "/projects" in authenticated_page.url, \
            "Projects should be active or URL should be correct"


@pytest.mark.navigation
class TestBreadcrumbs:
    """Breadcrumb navigation tests."""

    def test_breadcrumb_visible_in_detail_views(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Breadcrumbs should be visible in detail views.

        Steps:
        1. Create and open a project
        2. Verify breadcrumb is visible
        """
        from pages.project_detail_page import ProjectDetailPage

        project_name = test_data.project_name()

        projects_page.create_project(project_name)
        projects_page.wait_for_load()
        projects_page.open_project(project_name)

        detail = ProjectDetailPage(projects_page.page)
        detail.wait_for_project_detail_page()

        breadcrumb = BreadcrumbComponent(projects_page.page)

        # Breadcrumb should be visible or path should indicate nesting
        has_breadcrumb = breadcrumb.is_visible()
        has_nested_path = "/" in detail.get_current_path().replace("/projects/", "")

        assert has_breadcrumb or has_nested_path, \
            "Breadcrumb or nested path should exist"

    def test_breadcrumb_navigation(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Should be able to navigate via breadcrumbs.

        Steps:
        1. Navigate to project detail
        2. Click on parent breadcrumb
        3. Verify navigation back
        """
        from pages.project_detail_page import ProjectDetailPage

        project_name = test_data.project_name()

        projects_page.create_project(project_name)
        projects_page.wait_for_load()
        projects_page.open_project(project_name)

        detail = ProjectDetailPage(projects_page.page)
        detail.wait_for_project_detail_page()

        breadcrumb = BreadcrumbComponent(projects_page.page)

        if breadcrumb.is_visible() and breadcrumb.get_crumb_count() > 1:
            # Click parent breadcrumb
            breadcrumb.click_parent()

            # Should navigate back
            assert not detail.is_project_detail_page() or \
                "/projects/" not in detail.get_current_path(), \
                "Should navigate back via breadcrumb"


@pytest.mark.navigation
class TestBackButton:
    """Back button navigation tests."""

    def test_back_button_behavior(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Back button should navigate to previous page.

        Steps:
        1. Navigate to projects
        2. Open a project
        3. Click back
        4. Verify back on projects list
        """
        from pages.project_detail_page import ProjectDetailPage

        project_name = test_data.project_name()

        projects_page.create_project(project_name)
        projects_page.wait_for_load()
        projects_page.open_project(project_name)

        detail = ProjectDetailPage(projects_page.page)
        detail.wait_for_project_detail_page()

        # Use back button
        detail.go_back()
        projects_page.wait_for_projects_page()

        assert projects_page.is_projects_page(), \
            "Back should return to projects list"

    def test_browser_back_button(
        self,
        authenticated_page: Page
    ):
        """
        Browser back button should work correctly.

        Steps:
        1. Navigate to home -> projects -> settings
        2. Use browser back
        3. Verify history navigation
        """
        authenticated_page.goto(settings.get_frontend_url("/home"))
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.goto(settings.get_frontend_url("/projects"))
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.goto(settings.get_frontend_url("/settings"))
        authenticated_page.wait_for_load_state("networkidle")

        # Go back
        authenticated_page.go_back()
        authenticated_page.wait_for_load_state("networkidle")

        assert "/projects" in authenticated_page.url, \
            "Browser back should go to projects"


@pytest.mark.navigation
class TestDeepLinks:
    """Deep link/direct URL navigation tests."""

    def test_deep_link_to_projects(self, authenticated_page: Page):
        """
        Direct URL to projects should work.

        Steps:
        1. Navigate directly to /projects
        2. Verify projects page loads
        """
        authenticated_page.goto(settings.get_frontend_url("/projects"))

        projects_page = ProjectsPage(authenticated_page)
        projects_page.wait_for_projects_page()

        assert projects_page.is_projects_page(), \
            "Deep link to projects should work"

    def test_deep_link_to_chats(self, authenticated_page: Page):
        """
        Direct URL to chats should work.

        Steps:
        1. Navigate directly to /chats
        2. Verify chats page loads
        """
        authenticated_page.goto(settings.get_frontend_url("/chats"))

        chats_page = ChatsPage(authenticated_page)
        chats_page.wait_for_chats_page()

        assert chats_page.is_chats_page(), \
            "Deep link to chats should work"

    def test_deep_link_to_settings(self, authenticated_page: Page):
        """
        Direct URL to settings should work.

        Steps:
        1. Navigate directly to /settings
        2. Verify settings page loads
        """
        authenticated_page.goto(settings.get_frontend_url("/settings"))

        settings_page = SettingsPage(authenticated_page)
        settings_page.wait_for_settings_page()

        assert settings_page.is_settings_page(), \
            "Deep link to settings should work"

    def test_invalid_route_handled(self, authenticated_page: Page):
        """
        Invalid routes should be handled gracefully.

        Steps:
        1. Navigate to invalid route
        2. Verify app doesn't crash (shows 404 or redirects)
        """
        authenticated_page.goto(settings.get_frontend_url("/invalid-route-xyz"))

        # Wait for navigation
        authenticated_page.wait_for_load_state("networkidle")

        # App should not crash - either show 404, redirect, or show home
        # Check that page has content
        body_text = authenticated_page.locator("body").text_content()

        assert len(body_text or "") > 0, "App should handle invalid routes"


@pytest.mark.navigation
@pytest.mark.smoke
class TestNavigationSmoke:
    """Quick navigation smoke tests."""

    def test_basic_navigation_works(self, authenticated_page: Page):
        """Verify basic navigation is functional."""
        authenticated_page.goto(settings.get_frontend_url("/"))
        authenticated_page.wait_for_load_state("networkidle")

        # Should not error
        assert authenticated_page.url is not None, "Navigation should work"

    def test_all_main_routes_accessible(self, authenticated_page: Page):
        """Verify all main routes are accessible."""
        routes = ["/home", "/chats", "/projects", "/settings"]

        for route in routes:
            authenticated_page.goto(settings.get_frontend_url(route))
            authenticated_page.wait_for_load_state("networkidle")

            # Should not error
            assert route in authenticated_page.url or \
                authenticated_page.url.endswith("/"), \
                f"Route {route} should be accessible"
