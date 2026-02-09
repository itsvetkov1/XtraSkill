"""
Documents Page Object for document upload and management.
"""
from playwright.sync_api import Page, Locator, FileChooser
from pages.base_page import BasePage
from config.settings import settings
from typing import List
import os


class DocumentsPage(BasePage):
    """
    Page Object for the Documents screen.

    Handles document upload, viewing, and management.
    """

    # ==================== Locators ====================

    @property
    def page_title(self) -> Locator:
        """Page title/header."""
        return self.page.get_by_role("heading", name="Documents")

    @property
    def upload_button(self) -> Locator:
        """Upload button."""
        return self.page.get_by_role("button", name="Upload")

    @property
    def upload_dropzone(self) -> Locator:
        """Drag and drop upload zone."""
        return self.page.locator("[data-testid='upload-dropzone'], .dropzone")

    @property
    def file_input(self) -> Locator:
        """Hidden file input element."""
        return self.page.locator("input[type='file']")

    @property
    def document_list(self) -> Locator:
        """Document list container."""
        return self.page.locator("[data-testid='document-list'], .document-list")

    @property
    def document_cards(self) -> Locator:
        """All document cards."""
        return self.page.locator("[data-testid='document-card'], .document-card")

    @property
    def empty_state(self) -> Locator:
        """Empty state when no documents exist."""
        return self.page.locator("[data-testid='empty-state'], .empty-state")

    @property
    def upload_progress(self) -> Locator:
        """Upload progress indicator."""
        return self.page.locator("[data-testid='upload-progress'], .upload-progress")

    @property
    def loading_indicator(self) -> Locator:
        """Loading indicator."""
        return self.page.locator("[role='progressbar'], .loading")

    # ==================== Document Card Locators ====================

    def get_document_card(self, name: str) -> Locator:
        """Get a specific document card by name."""
        return self.document_cards.filter(has_text=name).first

    def get_document_menu_button(self, name: str) -> Locator:
        """Get the menu button for a specific document."""
        card = self.get_document_card(name)
        return card.locator("[data-testid='document-menu'], button[aria-label*='menu' i]")

    def get_document_type_icon(self, name: str) -> Locator:
        """Get the file type icon for a document."""
        card = self.get_document_card(name)
        return card.locator(".document-icon, [data-testid='document-icon']")

    def get_document_size(self, name: str) -> Locator:
        """Get the file size element for a document."""
        card = self.get_document_card(name)
        return card.locator(".document-size, [data-testid='document-size']")

    # ==================== Upload Actions ====================

    def upload_file(self, file_path: str) -> None:
        """
        Upload a file.

        Args:
            file_path: Path to the file to upload
        """
        # Use file chooser
        with self.page.expect_file_chooser() as fc_info:
            self.click(self.upload_button)
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)

        # Wait for upload to complete
        self.wait_for_upload_complete()

    def upload_files(self, file_paths: List[str]) -> None:
        """
        Upload multiple files.

        Args:
            file_paths: List of file paths to upload
        """
        with self.page.expect_file_chooser() as fc_info:
            self.click(self.upload_button)
        file_chooser = fc_info.value
        file_chooser.set_files(file_paths)

        # Wait for all uploads to complete
        self.wait_for_upload_complete()

    def upload_via_dropzone(self, file_path: str) -> None:
        """
        Upload a file by setting it on the hidden input.

        This simulates drag-and-drop without actual mouse events.

        Args:
            file_path: Path to the file to upload
        """
        self.file_input.set_input_files(file_path)
        self.wait_for_upload_complete()

    def wait_for_upload_complete(self, timeout: int = None) -> None:
        """Wait for upload progress to complete."""
        timeout = timeout or settings.TIMEOUT_LONG

        # Wait for progress indicator to appear and disappear
        if self.is_visible(self.upload_progress):
            self.wait_for_element(self.upload_progress, state="hidden", timeout=timeout)

        # Additional wait for document to appear in list
        self.page.wait_for_timeout(500)

    # ==================== Document Actions ====================

    def open_document(self, name: str) -> None:
        """
        Open/view a document.

        Args:
            name: Document name to open
        """
        card = self.get_document_card(name)
        self.click(card)

    def delete_document(self, name: str) -> None:
        """
        Delete a document.

        Args:
            name: Document name to delete
        """
        # Open context menu
        menu_button = self.get_document_menu_button(name)
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

    def download_document(self, name: str) -> str:
        """
        Download a document.

        Args:
            name: Document name to download

        Returns:
            Path to downloaded file
        """
        menu_button = self.get_document_menu_button(name)
        self.click(menu_button)

        # Click download option and wait for download
        with self.page.expect_download() as download_info:
            download_option = self.page.get_by_role("menuitem", name="Download")
            self.click(download_option)

        download = download_info.value
        return download.path()

    def rename_document(self, old_name: str, new_name: str) -> None:
        """
        Rename a document.

        Args:
            old_name: Current document name
            new_name: New document name
        """
        menu_button = self.get_document_menu_button(old_name)
        self.click(menu_button)

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

    # ==================== Queries ====================

    def get_document_names(self) -> List[str]:
        """Get list of all document names."""
        return self.get_all_texts(self.document_cards)

    def get_document_count(self) -> int:
        """Get number of documents displayed."""
        return self.count(self.document_cards)

    def get_document_size_text(self, name: str) -> str:
        """Get the file size of a document."""
        size = self.get_document_size(name)
        if self.is_visible(size):
            return self.get_text(size)
        return ""

    # ==================== Verification ====================

    def is_documents_page(self) -> bool:
        """
        Verify we are on the documents page.

        Returns:
            True if on documents page, False otherwise
        """
        return (
            "/documents" in self.get_current_path() or
            self.is_visible(self.page_title)
        )

    def wait_for_documents_page(self) -> None:
        """Wait for documents page to be fully loaded."""
        self.wait_for_load()
        # Wait for loading to complete
        if self.is_visible(self.loading_indicator):
            self.wait_for_element(self.loading_indicator, state="hidden")

    def document_exists(self, name: str) -> bool:
        """Check if a document with given name exists."""
        return self.is_visible(self.get_document_card(name))

    def is_empty(self) -> bool:
        """Check if no documents exist."""
        return self.is_visible(self.empty_state)

    def has_documents(self) -> bool:
        """Check if any documents exist."""
        return self.count(self.document_cards) > 0

    def is_uploading(self) -> bool:
        """Check if upload is in progress."""
        return self.is_visible(self.upload_progress)
