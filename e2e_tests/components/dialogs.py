"""
Dialog Component for handling modal dialogs.
"""
from playwright.sync_api import Page, Locator
from config.settings import settings
from typing import Optional


class DialogComponent:
    """
    Component for handling modal dialogs.

    Provides methods for interacting with create, rename,
    delete, and other modal dialogs.
    """

    def __init__(self, page: Page):
        """
        Initialize dialog component.

        Args:
            page: Playwright Page instance
        """
        self.page = page

    # ==================== Locators ====================

    @property
    def dialog(self) -> Locator:
        """Any visible dialog."""
        return self.page.locator("[role='dialog'], [role='alertdialog']").first

    @property
    def dialog_title(self) -> Locator:
        """Dialog title/header."""
        return self.dialog.locator("[data-testid='dialog-title'], h2, .dialog-title")

    @property
    def dialog_content(self) -> Locator:
        """Dialog content area."""
        return self.dialog.locator("[data-testid='dialog-content'], .dialog-content")

    @property
    def dialog_actions(self) -> Locator:
        """Dialog action buttons area."""
        return self.dialog.locator("[data-testid='dialog-actions'], .dialog-actions")

    @property
    def close_button(self) -> Locator:
        """Close dialog button (X)."""
        return self.dialog.locator("button[aria-label='Close'], button:has-text('×')")

    @property
    def cancel_button(self) -> Locator:
        """Cancel button."""
        return self.dialog.get_by_role("button", name="Cancel")

    @property
    def confirm_button(self) -> Locator:
        """Confirm/OK button."""
        return self.dialog.locator(
            "button:has-text('OK'), "
            "button:has-text('Confirm'), "
            "button:has-text('Yes')"
        ).first

    @property
    def overlay(self) -> Locator:
        """Dialog overlay/backdrop."""
        return self.page.locator("[data-testid='dialog-overlay'], .dialog-overlay, .backdrop")

    # ==================== Actions ====================

    def wait_for_dialog(self, timeout: int = None) -> None:
        """
        Wait for a dialog to appear.

        Args:
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        self.dialog.wait_for(state="visible", timeout=timeout)

    def wait_for_dialog_closed(self, timeout: int = None) -> None:
        """
        Wait for dialog to close.

        Args:
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        self.dialog.wait_for(state="hidden", timeout=timeout)

    def close(self) -> None:
        """Close the dialog using the X button."""
        self.close_button.click()
        self.wait_for_dialog_closed()

    def cancel(self) -> None:
        """Cancel the dialog."""
        self.cancel_button.click()
        self.wait_for_dialog_closed()

    def confirm(self) -> None:
        """Confirm/accept the dialog."""
        self.confirm_button.click()
        self.wait_for_dialog_closed()

    def click_button(self, name: str) -> None:
        """
        Click a button in the dialog by name.

        Args:
            name: Button name/text
        """
        button = self.dialog.get_by_role("button", name=name)
        button.click()

    def click_overlay(self) -> None:
        """Click the overlay to close (if supported)."""
        self.overlay.click()

    # ==================== Form Dialogs ====================

    def fill_input(self, label: str, value: str) -> None:
        """
        Fill an input field in the dialog.

        Args:
            label: Input label
            value: Value to fill
        """
        input_field = self.dialog.get_by_label(label)
        input_field.fill(value)

    def fill_textarea(self, label: str, value: str) -> None:
        """
        Fill a textarea in the dialog.

        Args:
            label: Textarea label
            value: Value to fill
        """
        textarea = self.dialog.get_by_label(label)
        textarea.fill(value)

    def select_option(self, label: str, option: str) -> None:
        """
        Select an option in a dropdown.

        Args:
            label: Dropdown label
            option: Option to select
        """
        dropdown = self.dialog.get_by_label(label)
        dropdown.click()
        option_element = self.page.get_by_role("option", name=option)
        option_element.click()

    def check_checkbox(self, label: str) -> None:
        """
        Check a checkbox.

        Args:
            label: Checkbox label
        """
        checkbox = self.dialog.get_by_label(label)
        checkbox.check()

    def uncheck_checkbox(self, label: str) -> None:
        """
        Uncheck a checkbox.

        Args:
            label: Checkbox label
        """
        checkbox = self.dialog.get_by_label(label)
        checkbox.uncheck()

    # ==================== Queries ====================

    def get_title(self) -> str:
        """Get dialog title text."""
        if self.is_visible():
            return self.dialog_title.text_content() or ""
        return ""

    def get_content_text(self) -> str:
        """Get dialog content text."""
        if self.is_visible():
            return self.dialog_content.text_content() or ""
        return ""

    def get_input_value(self, label: str) -> str:
        """Get value of an input field."""
        input_field = self.dialog.get_by_label(label)
        return input_field.input_value()

    # ==================== Verification ====================

    def is_visible(self) -> bool:
        """Check if any dialog is visible."""
        try:
            return self.dialog.is_visible()
        except Exception:
            return False

    def has_title(self, expected: str) -> bool:
        """Check if dialog has expected title."""
        return expected.lower() in self.get_title().lower()

    def has_button(self, name: str) -> bool:
        """Check if dialog has a button with given name."""
        button = self.dialog.get_by_role("button", name=name)
        return button.is_visible()


class CreateDialogComponent(DialogComponent):
    """Specialized component for create dialogs."""

    @property
    def name_input(self) -> Locator:
        """Name input field."""
        return self.dialog.get_by_label("Name")

    @property
    def title_input(self) -> Locator:
        """Title input field."""
        return self.dialog.get_by_label("Title")

    @property
    def description_input(self) -> Locator:
        """Description input field."""
        return self.dialog.get_by_label("Description")

    @property
    def create_button(self) -> Locator:
        """Create button."""
        return self.dialog.get_by_role("button", name="Create")

    def fill_name(self, name: str) -> None:
        """Fill the name field."""
        self.name_input.fill(name)

    def fill_title(self, title: str) -> None:
        """Fill the title field."""
        self.title_input.fill(title)

    def fill_description(self, description: str) -> None:
        """Fill the description field."""
        self.description_input.fill(description)

    def create(self) -> None:
        """Click create and wait for dialog to close."""
        self.create_button.click()
        self.wait_for_dialog_closed()


class DeleteDialogComponent(DialogComponent):
    """Specialized component for delete confirmation dialogs."""

    @property
    def warning_message(self) -> Locator:
        """Warning message text."""
        return self.dialog.locator(".warning-message, [data-testid='warning']")

    @property
    def delete_button(self) -> Locator:
        """Delete confirmation button."""
        return self.dialog.get_by_role("button", name="Delete")

    def confirm_delete(self) -> None:
        """Confirm deletion and wait for dialog to close."""
        self.delete_button.click()
        self.wait_for_dialog_closed()

    def get_warning_text(self) -> str:
        """Get the warning message text."""
        if self.warning_message.is_visible():
            return self.warning_message.text_content() or ""
        return ""


class RenameDialogComponent(DialogComponent):
    """Specialized component for rename dialogs."""

    @property
    def name_input(self) -> Locator:
        """New name input field."""
        return self.dialog.get_by_label("Name")

    @property
    def save_button(self) -> Locator:
        """Save button."""
        return self.dialog.get_by_role("button", name="Save")

    def fill_new_name(self, name: str) -> None:
        """Fill the new name."""
        self.name_input.clear()
        self.name_input.fill(name)

    def save(self) -> None:
        """Save and wait for dialog to close."""
        self.save_button.click()
        self.wait_for_dialog_closed()
