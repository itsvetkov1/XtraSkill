"""
Projects Page Object for project list management.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from typing import List


class ProjectsPage(BasePage):
    """
    Page Object for the Projects list screen.

    Handles project CRUD operations including creation,
    listing, and deletion from the projects list view.
    """

    # ==================== Locators ====================

    @property
    def page_title(self) -> Locator:
        """Page title/header."""
        return self.page.get_by_role("heading", name="Projects")

    @property
    def create_project_button(self) -> Locator:
        """Create project button."""
        return self.page.get_by_role("button", name="New Project")

    @property
    def project_list(self) -> Locator:
        """Project list container."""
        return self.page.locator("[data-testid='project-list'], .project-list")

    @property
    def project_cards(self) -> Locator:
        """All project cards."""
        return self.page.locator("[data-testid='project-card'], .project-card")

    @property
    def empty_state(self) -> Locator:
        """Empty state when no projects exist."""
        return self.page.locator("[data-testid='empty-state'], .empty-state")

    @property
    def search_input(self) -> Locator:
        """Search/filter input for projects."""
        return self.page.get_by_placeholder("Search projects")

    @property
    def loading_indicator(self) -> Locator:
        """Loading indicator."""
        return self.page.locator("[role='progressbar'], .loading")

    @property
    def sort_dropdown(self) -> Locator:
        """Sort order dropdown."""
        return self.page.locator("[data-testid='sort-dropdown'], .sort-dropdown")

    # ==================== Project Card Locators ====================

    def get_project_card(self, name: str) -> Locator:
        """Get a specific project card by name."""
        return self.project_cards.filter(has_text=name).first

    def get_project_menu_button(self, name: str) -> Locator:
        """Get the menu button for a specific project."""
        card = self.get_project_card(name)
        return card.locator("[data-testid='project-menu'], button[aria-label*='menu' i]")

    def get_project_description(self, name: str) -> Locator:
        """Get the description element of a project."""
        card = self.get_project_card(name)
        return card.locator(".project-description, [data-testid='project-description']")

    # ==================== Actions ====================

    def create_project(self, name: str, description: str = "") -> None:
        """
        Create a new project.

        Args:
            name: Project name
            description: Optional project description
        """
        self.click(self.create_project_button)

        # Wait for dialog
        dialog = self.page.locator("[role='dialog']")
        self.wait_for_element(dialog)

        # Fill project details
        name_input = dialog.get_by_label("Name")
        self.fill(name_input, name)

        if description:
            desc_input = dialog.get_by_label("Description")
            self.fill(desc_input, description)

        # Confirm creation
        create_button = dialog.get_by_role("button", name="Create")
        self.click(create_button)

        # Wait for dialog to close
        self.wait_for_element(dialog, state="hidden")

    def open_project(self, name: str) -> None:
        """
        Open a specific project.

        Args:
            name: Project name to open
        """
        card = self.get_project_card(name)
        self.click(card)

    def delete_project(self, name: str) -> None:
        """
        Delete a project.

        Args:
            name: Project name to delete
        """
        # Open context menu
        menu_button = self.get_project_menu_button(name)
        self.click(menu_button)

        # Click delete option
        delete_option = self.page.get_by_role("menuitem", name="Delete")
        self.click(delete_option)

        # Confirm deletion in dialog
        dialog = self.page.locator("[role='dialog'], [role='alertdialog']")
        self.wait_for_element(dialog)
        confirm_button = dialog.get_by_role("button", name="Delete")
        self.click(confirm_button)

        # Wait for dialog to close
        self.wait_for_element(dialog, state="hidden")

    def rename_project(self, old_name: str, new_name: str) -> None:
        """
        Rename a project.

        Args:
            old_name: Current project name
            new_name: New project name
        """
        # Open context menu
        menu_button = self.get_project_menu_button(old_name)
        self.click(menu_button)

        # Click rename option
        rename_option = self.page.get_by_role("menuitem", name="Rename")
        self.click(rename_option)

        # Enter new name
        dialog = self.page.locator("[role='dialog']")
        self.wait_for_element(dialog)
        name_input = dialog.get_by_label("Name")
        self.clear_and_fill(name_input, new_name)

        # Confirm
        save_button = dialog.get_by_role("button", name="Save")
        self.click(save_button)

        # Wait for dialog to close
        self.wait_for_element(dialog, state="hidden")

    def search_projects(self, query: str) -> None:
        """
        Search/filter projects.

        Args:
            query: Search query
        """
        self.fill(self.search_input, query)

    def clear_search(self) -> None:
        """Clear the search filter."""
        self.fill(self.search_input, "")

    # ==================== Queries ====================

    def get_project_names(self) -> List[str]:
        """Get list of all project names."""
        return self.get_all_texts(self.project_cards)

    def get_project_count(self) -> int:
        """Get number of projects displayed."""
        return self.count(self.project_cards)

    def get_project_description_text(self, name: str) -> str:
        """Get the description of a project."""
        desc = self.get_project_description(name)
        if self.is_visible(desc):
            return self.get_text(desc)
        return ""

    # ==================== Verification ====================

    def is_projects_page(self) -> bool:
        """
        Verify we are on the projects page.

        Returns:
            True if on projects page, False otherwise
        """
        return (
            "/projects" in self.get_current_path() or
            self.is_visible(self.page_title)
        )

    def wait_for_projects_page(self) -> None:
        """Wait for projects page to be fully loaded."""
        self.wait_for_load()
        # Wait for loading to complete
        if self.is_visible(self.loading_indicator):
            self.wait_for_element(self.loading_indicator, state="hidden")

    def project_exists(self, name: str) -> bool:
        """Check if a project with given name exists."""
        return self.is_visible(self.get_project_card(name))

    def is_empty(self) -> bool:
        """Check if no projects exist."""
        return self.is_visible(self.empty_state)

    def has_projects(self) -> bool:
        """Check if any projects exist."""
        return self.count(self.project_cards) > 0
