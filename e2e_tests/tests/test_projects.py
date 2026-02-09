"""
Projects E2E Tests.

Tests for project CRUD operations.
"""
import pytest
from playwright.sync_api import Page

from pages.projects_page import ProjectsPage
from pages.project_detail_page import ProjectDetailPage
from utils.test_data import TestDataGenerator
from config.settings import settings


@pytest.mark.projects
class TestProjectsCRUD:
    """Project CRUD test suite."""

    def test_projects_page_loads(self, projects_page: ProjectsPage):
        """
        Projects page should load successfully.

        Steps:
        1. Navigate to projects (via fixture)
        2. Verify projects page is displayed
        """
        assert projects_page.is_projects_page(), "Projects page should load"

    def test_create_project(self, projects_page: ProjectsPage, test_data: TestDataGenerator):
        """
        Should be able to create a new project.

        Steps:
        1. Navigate to projects
        2. Click create project
        3. Fill project details
        4. Verify project appears in list
        """
        project_name = test_data.project_name()
        project_description = test_data.project_description()

        # Create project
        projects_page.create_project(project_name, project_description)

        # Wait for list to update
        projects_page.wait_for_load()

        # Verify project exists
        assert projects_page.project_exists(project_name), \
            f"Project '{project_name}' should appear in list"

    def test_list_projects(self, projects_page: ProjectsPage):
        """
        Projects page should list existing projects.

        Steps:
        1. Navigate to projects
        2. Verify project list is displayed
        """
        # Page should either have projects or show empty state
        has_projects = projects_page.has_projects()
        has_empty = projects_page.is_empty()

        assert has_projects or has_empty, \
            "Should show projects or empty state"

    def test_open_project_detail(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Should be able to open project detail.

        Steps:
        1. Create a project
        2. Click on the project
        3. Verify project detail page opens
        """
        project_name = test_data.project_name()

        # Create project first
        projects_page.create_project(project_name)
        projects_page.wait_for_load()

        # Open project
        projects_page.open_project(project_name)

        # Verify on detail page
        detail_page = ProjectDetailPage(projects_page.page)
        detail_page.wait_for_project_detail_page()

        assert detail_page.is_project_detail_page(), \
            "Should navigate to project detail"

    def test_delete_project(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Should be able to delete a project.

        Steps:
        1. Create a project
        2. Delete the project
        3. Verify project no longer exists
        """
        project_name = test_data.project_name()

        # Create project
        projects_page.create_project(project_name)
        projects_page.wait_for_load()
        assert projects_page.project_exists(project_name), "Project should exist"

        # Delete project
        projects_page.delete_project(project_name)
        projects_page.wait_for_load()

        # Verify deleted
        assert not projects_page.project_exists(project_name), \
            "Project should be deleted"

    def test_project_persists_after_refresh(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Created project should persist after page refresh.

        Steps:
        1. Create a project
        2. Refresh the page
        3. Verify project still exists
        """
        project_name = test_data.project_name()

        # Create project
        projects_page.create_project(project_name)
        projects_page.wait_for_load()

        # Refresh page
        projects_page.reload()
        projects_page.wait_for_projects_page()

        # Verify project still exists
        assert projects_page.project_exists(project_name), \
            "Project should persist after refresh"


@pytest.mark.projects
class TestProjectDetail:
    """Project detail page tests."""

    def test_project_detail_shows_title(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Project detail should show project title.

        Steps:
        1. Create and open a project
        2. Verify title is displayed
        """
        project_name = test_data.project_name()

        projects_page.create_project(project_name)
        projects_page.wait_for_load()
        projects_page.open_project(project_name)

        detail_page = ProjectDetailPage(projects_page.page)
        detail_page.wait_for_project_detail_page()

        title = detail_page.get_project_name()
        assert project_name in title, "Project title should be displayed"

    def test_create_thread_in_project(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator
    ):
        """
        Should be able to create a thread in a project.

        Steps:
        1. Create and open a project
        2. Create a new thread
        3. Verify thread appears
        """
        project_name = test_data.project_name()
        thread_title = test_data.thread_title()

        # Create and open project
        projects_page.create_project(project_name)
        projects_page.wait_for_load()
        projects_page.open_project(project_name)

        detail_page = ProjectDetailPage(projects_page.page)
        detail_page.wait_for_project_detail_page()

        # Create thread
        detail_page.create_thread(thread_title)
        detail_page.wait_for_load()

        assert detail_page.thread_exists(thread_title), \
            "Thread should appear in project"


@pytest.mark.projects
@pytest.mark.smoke
class TestProjectsSmoke:
    """Quick project smoke tests."""

    def test_can_access_projects_page(self, projects_page: ProjectsPage):
        """Verify projects page is accessible."""
        assert projects_page.is_projects_page()

    def test_create_button_visible(self, projects_page: ProjectsPage):
        """Verify create project button is visible."""
        assert projects_page.is_visible(projects_page.create_project_button)
