"""
Chats Page Object for global chat/thread management.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from typing import List, Optional


class ChatsPage(BasePage):
    """
    Page Object for the Chats screen.

    Handles global chat thread management including creation,
    listing, renaming, and deletion.
    """

    # ==================== Locators ====================

    @property
    def page_title(self) -> Locator:
        """Page title/header."""
        return self.page.get_by_role("heading", name="Chats")

    @property
    def new_chat_button(self) -> Locator:
        """New chat button."""
        return self.page.get_by_role("button", name="New Chat")

    @property
    def chat_list(self) -> Locator:
        """Chat list container."""
        return self.page.locator("[data-testid='chat-list'], .chat-list")

    @property
    def chat_items(self) -> Locator:
        """All chat list items."""
        return self.page.locator("[data-testid='chat-item'], .chat-item, [role='listitem']")

    @property
    def empty_state(self) -> Locator:
        """Empty state when no chats exist."""
        return self.page.locator("[data-testid='empty-state'], .empty-state")

    @property
    def search_input(self) -> Locator:
        """Search/filter input for chats."""
        return self.page.get_by_placeholder("Search chats")

    @property
    def loading_indicator(self) -> Locator:
        """Loading indicator."""
        return self.page.locator("[role='progressbar'], .loading")

    # ==================== Chat Item Locators ====================

    def get_chat_item(self, title: str) -> Locator:
        """Get a specific chat item by title."""
        return self.chat_items.filter(has_text=title).first

    def get_chat_menu_button(self, title: str) -> Locator:
        """Get the menu button for a specific chat."""
        chat = self.get_chat_item(title)
        return chat.locator("[data-testid='chat-menu'], button[aria-label*='menu' i]")

    def get_chat_title_element(self, title: str) -> Locator:
        """Get the title element of a chat."""
        chat = self.get_chat_item(title)
        return chat.locator(".chat-title, [data-testid='chat-title']")

    # ==================== Actions ====================

    def create_new_chat(self, title: str = None) -> None:
        """
        Create a new chat.

        Args:
            title: Optional chat title (uses default if not provided)
        """
        self.click(self.new_chat_button)

        if title:
            # Wait for dialog and enter title
            dialog = self.page.locator("[role='dialog']")
            self.wait_for_element(dialog)
            title_input = dialog.get_by_label("Title")
            self.fill(title_input, title)
            confirm_button = dialog.get_by_role("button", name="Create")
            self.click(confirm_button)

    def open_chat(self, title: str) -> None:
        """
        Open a specific chat.

        Args:
            title: Chat title to open
        """
        chat = self.get_chat_item(title)
        self.click(chat)

    def delete_chat(self, title: str) -> None:
        """
        Delete a chat.

        Args:
            title: Chat title to delete
        """
        # Open context menu
        menu_button = self.get_chat_menu_button(title)
        self.click(menu_button)

        # Click delete option
        delete_option = self.page.get_by_role("menuitem", name="Delete")
        self.click(delete_option)

        # Confirm deletion
        confirm_button = self.page.get_by_role("button", name="Delete")
        self.click(confirm_button)

    def rename_chat(self, old_title: str, new_title: str) -> None:
        """
        Rename a chat.

        Args:
            old_title: Current chat title
            new_title: New chat title
        """
        # Open context menu
        menu_button = self.get_chat_menu_button(old_title)
        self.click(menu_button)

        # Click rename option
        rename_option = self.page.get_by_role("menuitem", name="Rename")
        self.click(rename_option)

        # Enter new title
        dialog = self.page.locator("[role='dialog']")
        self.wait_for_element(dialog)
        title_input = dialog.get_by_label("Title")
        self.clear_and_fill(title_input, new_title)

        # Confirm
        save_button = dialog.get_by_role("button", name="Save")
        self.click(save_button)

    def search_chats(self, query: str) -> None:
        """
        Search/filter chats.

        Args:
            query: Search query
        """
        self.fill(self.search_input, query)

    def clear_search(self) -> None:
        """Clear the search filter."""
        self.fill(self.search_input, "")

    # ==================== Queries ====================

    def get_chat_titles(self) -> List[str]:
        """Get list of all chat titles."""
        return self.get_all_texts(self.chat_items)

    def get_chat_count(self) -> int:
        """Get number of chats displayed."""
        return self.count(self.chat_items)

    # ==================== Verification ====================

    def is_chats_page(self) -> bool:
        """
        Verify we are on the chats page.

        Returns:
            True if on chats page, False otherwise
        """
        return (
            "/chats" in self.get_current_path() or
            self.is_visible(self.page_title)
        )

    def wait_for_chats_page(self) -> None:
        """Wait for chats page to be fully loaded."""
        self.wait_for_load()
        # Wait for loading to complete
        if self.is_visible(self.loading_indicator):
            self.wait_for_element(self.loading_indicator, state="hidden")

    def chat_exists(self, title: str) -> bool:
        """Check if a chat with given title exists."""
        return self.is_visible(self.get_chat_item(title))

    def is_empty(self) -> bool:
        """Check if no chats exist."""
        return self.is_visible(self.empty_state)

    def has_chats(self) -> bool:
        """Check if any chats exist."""
        return self.count(self.chat_items) > 0
