"""
Project Detail Page Object for individual project view.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from typing import List


class ProjectDetailPage(BasePage):
    """
    Page Object for the Project Detail screen.

    Handles project detail view including threads,
    documents, and project-specific actions.
    """

    # ==================== Locators ====================

    @property
    def project_title(self) -> Locator:
        """Project name/title."""
        return self.page.locator("[data-testid='project-title'], .project-title, h1")

    @property
    def project_description(self) -> Locator:
        """Project description."""
        return self.page.locator("[data-testid='project-description'], .project-description")

    @property
    def back_button(self) -> Locator:
        """Back navigation button."""
        return self.page.get_by_role("button", name="Back")

    @property
    def edit_button(self) -> Locator:
        """Edit project button."""
        return self.page.get_by_role("button", name="Edit")

    @property
    def delete_button(self) -> Locator:
        """Delete project button."""
        return self.page.get_by_role("button", name="Delete")

    @property
    def menu_button(self) -> Locator:
        """Project menu button."""
        return self.page.locator("[data-testid='project-menu'], button[aria-label*='more' i]")

    # ==================== Threads Section ====================

    @property
    def threads_section(self) -> Locator:
        """Threads section container."""
        return self.page.locator("[data-testid='threads-section'], .threads-section")

    @property
    def thread_list(self) -> Locator:
        """Thread list container."""
        return self.page.locator("[data-testid='thread-list'], .thread-list")

    @property
    def thread_items(self) -> Locator:
        """All thread items."""
        return self.page.locator("[data-testid='thread-item'], .thread-item")

    @property
    def new_thread_button(self) -> Locator:
        """New thread button."""
        return self.page.get_by_role("button", name="New Thread")

    @property
    def threads_empty_state(self) -> Locator:
        """Empty state for threads."""
        return self.threads_section.locator("[data-testid='empty-state'], .empty-state")

    # ==================== Documents Section ====================

    @property
    def documents_section(self) -> Locator:
        """Documents section container."""
        return self.page.locator("[data-testid='documents-section'], .documents-section")

    @property
    def document_list(self) -> Locator:
        """Document list container."""
        return self.page.locator("[data-testid='document-list'], .document-list")

    @property
    def document_items(self) -> Locator:
        """All document items."""
        return self.page.locator("[data-testid='document-item'], .document-item")

    @property
    def upload_document_button(self) -> Locator:
        """Upload document button."""
        return self.page.get_by_role("button", name="Upload Document")

    @property
    def documents_empty_state(self) -> Locator:
        """Empty state for documents."""
        return self.documents_section.locator("[data-testid='empty-state'], .empty-state")

    # ==================== Thread Actions ====================

    def get_thread_item(self, title: str) -> Locator:
        """Get a specific thread item by title."""
        return self.thread_items.filter(has_text=title).first

    def create_thread(self, title: str) -> None:
        """
        Create a new thread in this project.

        Args:
            title: Thread title
        """
        self.click(self.new_thread_button)

        # Wait for dialog
        dialog = self.page.locator("[role='dialog']")
        self.wait_for_element(dialog)

        # Fill thread title
        title_input = dialog.get_by_label("Title")
        self.fill(title_input, title)

        # Confirm creation
        create_button = dialog.get_by_role("button", name="Create")
        self.click(create_button)

        # Wait for dialog to close
        self.wait_for_element(dialog, state="hidden")

    def open_thread(self, title: str) -> None:
        """
        Open a specific thread.

        Args:
            title: Thread title to open
        """
        thread = self.get_thread_item(title)
        self.click(thread)

    def delete_thread(self, title: str) -> None:
        """
        Delete a thread.

        Args:
            title: Thread title to delete
        """
        thread = self.get_thread_item(title)
        menu = thread.locator("[data-testid='thread-menu'], button[aria-label*='menu' i]")
        self.click(menu)

        delete_option = self.page.get_by_role("menuitem", name="Delete")
        self.click(delete_option)

        # Confirm deletion
        dialog = self.page.locator("[role='dialog'], [role='alertdialog']")
        confirm = dialog.get_by_role("button", name="Delete")
        self.click(confirm)

    # ==================== Document Actions ====================

    def get_document_item(self, name: str) -> Locator:
        """Get a specific document item by name."""
        return self.document_items.filter(has_text=name).first

    def click_upload_document(self) -> None:
        """Click the upload document button."""
        self.click(self.upload_document_button)

    def open_document(self, name: str) -> None:
        """
        Open a specific document.

        Args:
            name: Document name to open
        """
        document = self.get_document_item(name)
        self.click(document)

    def delete_document(self, name: str) -> None:
        """
        Delete a document.

        Args:
            name: Document name to delete
        """
        document = self.get_document_item(name)
        menu = document.locator("[data-testid='document-menu'], button[aria-label*='menu' i]")
        self.click(menu)

        delete_option = self.page.get_by_role("menuitem", name="Delete")
        self.click(delete_option)

        # Confirm deletion
        dialog = self.page.locator("[role='dialog'], [role='alertdialog']")
        confirm = dialog.get_by_role("button", name="Delete")
        self.click(confirm)

    # ==================== Queries ====================

    def get_project_name(self) -> str:
        """Get the project name/title."""
        return self.get_text(self.project_title)

    def get_project_description_text(self) -> str:
        """Get the project description."""
        if self.is_visible(self.project_description):
            return self.get_text(self.project_description)
        return ""

    def get_thread_titles(self) -> List[str]:
        """Get list of all thread titles."""
        return self.get_all_texts(self.thread_items)

    def get_thread_count(self) -> int:
        """Get number of threads."""
        return self.count(self.thread_items)

    def get_document_names(self) -> List[str]:
        """Get list of all document names."""
        return self.get_all_texts(self.document_items)

    def get_document_count(self) -> int:
        """Get number of documents."""
        return self.count(self.document_items)

    # ==================== Navigation ====================

    def go_back(self) -> None:
        """Navigate back to projects list."""
        self.click(self.back_button)

    # ==================== Verification ====================

    def is_project_detail_page(self) -> bool:
        """
        Verify we are on a project detail page.

        Returns:
            True if on project detail page, False otherwise
        """
        path = self.get_current_path()
        return "/projects/" in path and self.is_visible(self.project_title)

    def wait_for_project_detail_page(self) -> None:
        """Wait for project detail page to be fully loaded."""
        self.wait_for_load()
        self.wait_for_element(self.project_title)

    def thread_exists(self, title: str) -> bool:
        """Check if a thread with given title exists."""
        return self.is_visible(self.get_thread_item(title))

    def document_exists(self, name: str) -> bool:
        """Check if a document with given name exists."""
        return self.is_visible(self.get_document_item(name))

    def has_threads(self) -> bool:
        """Check if any threads exist."""
        return self.count(self.thread_items) > 0

    def has_documents(self) -> bool:
        """Check if any documents exist."""
        return self.count(self.document_items) > 0
