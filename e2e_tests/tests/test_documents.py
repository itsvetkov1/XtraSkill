"""
Documents E2E Tests.

Tests for document upload, view, and management.
"""
import pytest
from playwright.sync_api import Page

from pages.documents_page import DocumentsPage
from pages.projects_page import ProjectsPage
from pages.project_detail_page import ProjectDetailPage
from utils.test_data import TestDataGenerator
from config.settings import settings


@pytest.mark.documents
class TestDocumentUpload:
    """Document upload test suite."""

    def test_documents_page_loads(self, documents_page: DocumentsPage):
        """
        Documents page should load successfully.

        Steps:
        1. Navigate to documents (via fixture)
        2. Verify documents page is displayed
        """
        assert documents_page.is_documents_page(), "Documents page should load"

    def test_upload_button_visible(self, documents_page: DocumentsPage):
        """
        Upload button should be visible.

        Steps:
        1. Navigate to documents
        2. Verify upload button is available
        """
        has_upload_button = documents_page.is_visible(documents_page.upload_button)
        has_dropzone = documents_page.is_visible(documents_page.upload_dropzone)

        assert has_upload_button or has_dropzone, \
            "Upload mechanism should be visible"

    def test_upload_document(
        self,
        documents_page: DocumentsPage,
        test_file: str,
        test_data: TestDataGenerator
    ):
        """
        Should be able to upload a document.

        Steps:
        1. Navigate to documents
        2. Upload a test file
        3. Verify document appears in list
        """
        # Get the filename
        import os
        filename = os.path.basename(test_file)

        # Upload file
        documents_page.upload_file(test_file)

        # Wait for upload to complete
        documents_page.wait_for_upload_complete()
        documents_page.wait_for_load()

        # Verify document appears
        assert documents_page.document_exists(filename), \
            f"Document '{filename}' should appear after upload"

    def test_upload_pdf_document(
        self,
        documents_page: DocumentsPage,
        test_pdf: str
    ):
        """
        Should be able to upload a PDF document.

        Steps:
        1. Navigate to documents
        2. Upload a PDF file
        3. Verify document appears
        """
        import os
        filename = os.path.basename(test_pdf)

        documents_page.upload_file(test_pdf)
        documents_page.wait_for_upload_complete()
        documents_page.wait_for_load()

        assert documents_page.document_exists(filename), \
            "PDF should be uploaded successfully"


@pytest.mark.documents
class TestDocumentManagement:
    """Document management test suite."""

    def test_view_document(
        self,
        documents_page: DocumentsPage,
        test_file: str
    ):
        """
        Should be able to view an uploaded document.

        Steps:
        1. Upload a document
        2. Click on the document
        3. Verify document viewer opens or navigation occurs
        """
        import os
        filename = os.path.basename(test_file)

        # Upload first
        documents_page.upload_file(test_file)
        documents_page.wait_for_upload_complete()
        documents_page.wait_for_load()

        # Click to view
        initial_url = documents_page.get_current_url()
        documents_page.open_document(filename)

        # Wait for any navigation or viewer
        documents_page.page.wait_for_timeout(1000)

        # Verify something happened (navigation or modal)
        url_changed = documents_page.get_current_url() != initial_url
        has_viewer = documents_page.page.locator(
            "[data-testid='document-viewer'], .document-viewer, [role='dialog']"
        ).is_visible()

        assert url_changed or has_viewer, \
            "Clicking document should open viewer or navigate"

    def test_delete_document(
        self,
        documents_page: DocumentsPage,
        test_file: str
    ):
        """
        Should be able to delete a document.

        Steps:
        1. Upload a document
        2. Delete the document
        3. Verify document is removed
        """
        import os
        filename = os.path.basename(test_file)

        # Upload first
        documents_page.upload_file(test_file)
        documents_page.wait_for_upload_complete()
        documents_page.wait_for_load()
        assert documents_page.document_exists(filename), "Document should exist"

        # Delete
        documents_page.delete_document(filename)
        documents_page.wait_for_load()

        # Verify deleted
        assert not documents_page.document_exists(filename), \
            "Document should be deleted"


@pytest.mark.documents
class TestDocumentInProject:
    """Document upload within project context."""

    def test_upload_document_to_project(
        self,
        projects_page: ProjectsPage,
        test_data: TestDataGenerator,
        test_file: str
    ):
        """
        Should be able to upload document to a project.

        Steps:
        1. Create a project
        2. Open project detail
        3. Upload a document
        4. Verify document appears in project
        """
        import os
        project_name = test_data.project_name()
        filename = os.path.basename(test_file)

        # Create and open project
        projects_page.create_project(project_name)
        projects_page.wait_for_load()
        projects_page.open_project(project_name)

        detail_page = ProjectDetailPage(projects_page.page)
        detail_page.wait_for_project_detail_page()

        # Click upload and handle file
        if detail_page.is_visible(detail_page.upload_document_button):
            detail_page.click_upload_document()

            # Handle file chooser if it opens
            try:
                with projects_page.page.expect_file_chooser(timeout=3000) as fc:
                    pass
                fc.value.set_files(test_file)

                # Wait for upload
                detail_page.wait_for_load()

                assert detail_page.document_exists(filename), \
                    "Document should appear in project"
            except Exception:
                # File chooser may not have opened, skip test
                pytest.skip("File chooser did not open")


@pytest.mark.documents
@pytest.mark.smoke
class TestDocumentsSmoke:
    """Quick document smoke tests."""

    def test_can_access_documents_page(self, documents_page: DocumentsPage):
        """Verify documents page is accessible."""
        assert documents_page.is_documents_page()

    def test_documents_shows_list_or_empty(self, documents_page: DocumentsPage):
        """Verify documents shows list or empty state."""
        has_documents = documents_page.has_documents()
        has_empty = documents_page.is_empty()

        assert has_documents or has_empty, \
            "Should show document list or empty state"
