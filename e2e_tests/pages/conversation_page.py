"""
Conversation Page Object for chat/thread conversation view.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from config.settings import settings
from typing import List, Optional


class ConversationPage(BasePage):
    """
    Page Object for the Conversation/Chat screen.

    Handles message sending, receiving, and interaction
    within a chat thread.
    """

    # ==================== Locators ====================

    @property
    def conversation_title(self) -> Locator:
        """Conversation/thread title."""
        return self.page.locator("[data-testid='conversation-title'], .conversation-title, h1")

    @property
    def back_button(self) -> Locator:
        """Back navigation button."""
        return self.page.get_by_role("button", name="Back")

    @property
    def menu_button(self) -> Locator:
        """Conversation menu button."""
        return self.page.locator("[data-testid='conversation-menu'], button[aria-label*='more' i]")

    # ==================== Message List ====================

    @property
    def message_list(self) -> Locator:
        """Message list container."""
        return self.page.locator("[data-testid='message-list'], .message-list")

    @property
    def messages(self) -> Locator:
        """All message bubbles."""
        return self.page.locator("[data-testid='message'], .message")

    @property
    def user_messages(self) -> Locator:
        """User (sent) messages."""
        return self.page.locator("[data-testid='user-message'], .user-message")

    @property
    def ai_messages(self) -> Locator:
        """AI (received) messages."""
        return self.page.locator("[data-testid='ai-message'], .ai-message, .assistant-message")

    @property
    def loading_indicator(self) -> Locator:
        """AI response loading indicator."""
        return self.page.locator("[data-testid='loading'], .loading, .typing-indicator")

    @property
    def empty_state(self) -> Locator:
        """Empty conversation state."""
        return self.page.locator("[data-testid='empty-state'], .empty-conversation")

    # ==================== Message Input ====================

    @property
    def message_input(self) -> Locator:
        """Message text input."""
        return self.page.locator(
            "[data-testid='message-input'], "
            "textarea[placeholder*='message' i], "
            "input[placeholder*='message' i]"
        )

    @property
    def send_button(self) -> Locator:
        """Send message button."""
        return self.page.get_by_role("button", name="Send")

    @property
    def attach_button(self) -> Locator:
        """Attach file button."""
        return self.page.get_by_role("button", name="Attach")

    # ==================== Message Actions ====================

    def get_message(self, index: int) -> Locator:
        """
        Get a message by index.

        Args:
            index: 0-based message index

        Returns:
            Message locator
        """
        return self.messages.nth(index)

    def get_last_message(self) -> Locator:
        """Get the last message in the conversation."""
        return self.messages.last

    def get_last_user_message(self) -> Locator:
        """Get the last user message."""
        return self.user_messages.last

    def get_last_ai_message(self) -> Locator:
        """Get the last AI response."""
        return self.ai_messages.last

    def get_message_copy_button(self, message: Locator) -> Locator:
        """Get copy button for a message."""
        return message.locator("[data-testid='copy-button'], button[aria-label*='copy' i]")

    def get_message_retry_button(self, message: Locator) -> Locator:
        """Get retry button for a message."""
        return message.locator("[data-testid='retry-button'], button[aria-label*='retry' i]")

    # ==================== Sending Messages ====================

    def send_message(self, text: str) -> None:
        """
        Send a chat message.

        Args:
            text: Message text to send
        """
        self.fill(self.message_input, text)
        self.click(self.send_button)

    def type_message(self, text: str) -> None:
        """
        Type a message without sending.

        Args:
            text: Message text to type
        """
        self.fill(self.message_input, text)

    def send_via_enter(self, text: str) -> None:
        """
        Send a message by pressing Enter.

        Args:
            text: Message text to send
        """
        self.fill(self.message_input, text)
        self.press_enter()

    def clear_input(self) -> None:
        """Clear the message input."""
        self.fill(self.message_input, "")

    def get_input_value(self) -> str:
        """Get current text in input."""
        return self.message_input.input_value()

    # ==================== Waiting for Responses ====================

    def wait_for_response(self, timeout: int = None) -> None:
        """
        Wait for AI response to complete.

        Args:
            timeout: Timeout in ms (uses long timeout by default)
        """
        timeout = timeout or settings.TIMEOUT_LONG

        # Wait for loading indicator to appear
        try:
            self.wait_for_element(self.loading_indicator, timeout=3000)
        except Exception:
            # Loading may have already completed
            pass

        # Wait for loading indicator to disappear
        self.wait_for_element(self.loading_indicator, state="hidden", timeout=timeout)

        # Additional settle time
        self.page.wait_for_timeout(500)

    def wait_for_message_count(self, count: int, timeout: int = None) -> None:
        """
        Wait for specific number of messages.

        Args:
            count: Expected message count
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        self.messages.nth(count - 1).wait_for(timeout=timeout)

    # ==================== Message Interactions ====================

    def copy_message(self, index: int) -> None:
        """
        Copy a message to clipboard.

        Args:
            index: Message index to copy
        """
        message = self.get_message(index)
        # Hover to show action buttons
        self.hover(message)
        copy_button = self.get_message_copy_button(message)
        self.click(copy_button)

    def copy_last_response(self) -> None:
        """Copy the last AI response."""
        message = self.get_last_ai_message()
        self.hover(message)
        copy_button = self.get_message_copy_button(message)
        self.click(copy_button)

    def retry_last_message(self) -> None:
        """Retry the last message to regenerate response."""
        message = self.get_last_user_message()
        self.hover(message)
        retry_button = self.get_message_retry_button(message)
        self.click(retry_button)

    # ==================== Queries ====================

    def get_message_count(self) -> int:
        """Get total number of messages."""
        return self.count(self.messages)

    def get_user_message_count(self) -> int:
        """Get number of user messages."""
        return self.count(self.user_messages)

    def get_ai_message_count(self) -> int:
        """Get number of AI messages."""
        return self.count(self.ai_messages)

    def get_all_message_texts(self) -> List[str]:
        """Get text content of all messages."""
        return self.get_all_texts(self.messages)

    def get_message_text(self, index: int) -> str:
        """Get text content of a specific message."""
        return self.get_text(self.get_message(index))

    def get_last_message_text(self) -> str:
        """Get text of the last message."""
        return self.get_text(self.get_last_message())

    def get_last_response_text(self) -> str:
        """Get text of the last AI response."""
        return self.get_text(self.get_last_ai_message())

    def get_conversation_title_text(self) -> str:
        """Get the conversation title."""
        return self.get_text(self.conversation_title)

    # ==================== Navigation ====================

    def go_back(self) -> None:
        """Navigate back to previous screen."""
        self.click(self.back_button)

    # ==================== Verification ====================

    def is_conversation_page(self) -> bool:
        """
        Verify we are on a conversation page.

        Returns:
            True if on conversation page, False otherwise
        """
        return (
            self.is_visible(self.message_input) and
            self.is_visible(self.send_button)
        )

    def wait_for_conversation_page(self) -> None:
        """Wait for conversation page to be fully loaded."""
        self.wait_for_load()
        self.wait_for_element(self.message_input)

    def has_messages(self) -> bool:
        """Check if any messages exist."""
        return self.count(self.messages) > 0

    def is_empty(self) -> bool:
        """Check if conversation is empty."""
        return self.is_visible(self.empty_state) or self.count(self.messages) == 0

    def is_loading(self) -> bool:
        """Check if waiting for AI response."""
        return self.is_visible(self.loading_indicator)

    def can_send(self) -> bool:
        """Check if send button is enabled."""
        return self.is_enabled(self.send_button)
