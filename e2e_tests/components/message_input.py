"""
Message Input Component for chat message composition.
"""
from playwright.sync_api import Page, Locator
from config.settings import settings
from typing import Optional


class MessageInputComponent:
    """
    Component for the message input area in conversations.

    Handles text input, sending, and attachments.
    """

    def __init__(self, page: Page):
        """
        Initialize message input component.

        Args:
            page: Playwright Page instance
        """
        self.page = page

    # ==================== Locators ====================

    @property
    def input_container(self) -> Locator:
        """Message input container."""
        return self.page.locator(
            "[data-testid='message-input-container'], "
            ".message-input-container, "
            ".chat-input"
        )

    @property
    def text_input(self) -> Locator:
        """Text input field."""
        return self.page.locator(
            "[data-testid='message-input'], "
            "textarea[placeholder*='message' i], "
            "input[placeholder*='message' i]"
        )

    @property
    def send_button(self) -> Locator:
        """Send message button."""
        return self.page.locator(
            "[data-testid='send-button'], "
            "button[aria-label*='send' i], "
            "button:has-text('Send')"
        ).first

    @property
    def attach_button(self) -> Locator:
        """Attach file button."""
        return self.page.locator(
            "[data-testid='attach-button'], "
            "button[aria-label*='attach' i], "
            "button:has-text('Attach')"
        ).first

    @property
    def file_input(self) -> Locator:
        """Hidden file input for attachments."""
        return self.input_container.locator("input[type='file']")

    @property
    def character_count(self) -> Locator:
        """Character count display."""
        return self.input_container.locator(
            "[data-testid='char-count'], "
            ".character-count"
        )

    @property
    def emoji_button(self) -> Locator:
        """Emoji picker button."""
        return self.input_container.locator(
            "[data-testid='emoji-button'], "
            "button[aria-label*='emoji' i]"
        )

    @property
    def formatting_toolbar(self) -> Locator:
        """Text formatting toolbar."""
        return self.input_container.locator(
            "[data-testid='formatting-toolbar'], "
            ".formatting-toolbar"
        )

    # ==================== Input Actions ====================

    def type_message(self, text: str) -> None:
        """
        Type text into the message input.

        Args:
            text: Message text
        """
        self.text_input.fill(text)

    def type_slowly(self, text: str, delay: int = 50) -> None:
        """
        Type text character by character.

        Args:
            text: Message text
            delay: Delay between characters in ms
        """
        self.text_input.type(text, delay=delay)

    def clear(self) -> None:
        """Clear the message input."""
        self.text_input.fill("")

    def append_text(self, text: str) -> None:
        """
        Append text to existing input.

        Args:
            text: Text to append
        """
        current = self.get_value()
        self.text_input.fill(current + text)

    def get_value(self) -> str:
        """Get current input value."""
        return self.text_input.input_value()

    # ==================== Send Actions ====================

    def send(self) -> None:
        """Send the message using send button."""
        self.send_button.click()

    def send_via_enter(self) -> None:
        """Send the message by pressing Enter."""
        self.text_input.press("Enter")

    def send_via_ctrl_enter(self) -> None:
        """Send the message by pressing Ctrl+Enter."""
        self.text_input.press("Control+Enter")

    def send_message(self, text: str, via_enter: bool = False) -> None:
        """
        Type and send a message.

        Args:
            text: Message text
            via_enter: Use Enter key instead of button
        """
        self.type_message(text)
        if via_enter:
            self.send_via_enter()
        else:
            self.send()

    # ==================== Attachment Actions ====================

    def attach_file(self, file_path: str) -> None:
        """
        Attach a file to the message.

        Args:
            file_path: Path to file
        """
        with self.page.expect_file_chooser() as fc_info:
            self.attach_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)

    def attach_files(self, file_paths: list) -> None:
        """
        Attach multiple files.

        Args:
            file_paths: List of file paths
        """
        with self.page.expect_file_chooser() as fc_info:
            self.attach_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(file_paths)

    # ==================== Keyboard Actions ====================

    def press_key(self, key: str) -> None:
        """
        Press a key in the input.

        Args:
            key: Key name (Enter, Escape, etc.)
        """
        self.text_input.press(key)

    def insert_newline(self) -> None:
        """Insert a newline (Shift+Enter)."""
        self.text_input.press("Shift+Enter")

    def undo(self) -> None:
        """Undo last action (Ctrl+Z)."""
        self.text_input.press("Control+z")

    def redo(self) -> None:
        """Redo last action (Ctrl+Y)."""
        self.text_input.press("Control+y")

    def select_all(self) -> None:
        """Select all text (Ctrl+A)."""
        self.text_input.press("Control+a")

    # ==================== Queries ====================

    def get_character_count(self) -> int:
        """
        Get current character count.

        Returns:
            Number of characters
        """
        if self.character_count.is_visible():
            text = self.character_count.text_content() or ""
            # Extract number from text like "123/1000"
            import re
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        return len(self.get_value())

    def get_max_characters(self) -> Optional[int]:
        """
        Get maximum character limit if displayed.

        Returns:
            Max character limit or None
        """
        if self.character_count.is_visible():
            text = self.character_count.text_content() or ""
            import re
            match = re.search(r'/(\d+)', text)
            if match:
                return int(match.group(1))
        return None

    # ==================== Verification ====================

    def is_visible(self) -> bool:
        """Check if message input is visible."""
        return self.text_input.is_visible()

    def is_enabled(self) -> bool:
        """Check if message input is enabled."""
        return self.text_input.is_enabled()

    def is_empty(self) -> bool:
        """Check if input is empty."""
        return len(self.get_value().strip()) == 0

    def can_send(self) -> bool:
        """Check if send button is enabled."""
        return self.send_button.is_enabled()

    def has_text(self, expected: str) -> bool:
        """
        Check if input contains expected text.

        Args:
            expected: Text to find

        Returns:
            True if found
        """
        return expected in self.get_value()

    def has_attachment_support(self) -> bool:
        """Check if attachment button is available."""
        return self.attach_button.is_visible()

    def is_at_character_limit(self) -> bool:
        """Check if at character limit."""
        max_chars = self.get_max_characters()
        if max_chars:
            return self.get_character_count() >= max_chars
        return False
