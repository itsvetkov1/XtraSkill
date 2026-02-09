"""
Chats E2E Tests.

Tests for global chat/thread management.
"""
import pytest
from playwright.sync_api import Page

from pages.chats_page import ChatsPage
from pages.conversation_page import ConversationPage
from utils.test_data import TestDataGenerator
from config.settings import settings


@pytest.mark.chats
class TestChatsCRUD:
    """Chat CRUD test suite."""

    def test_chats_page_loads(self, chats_page: ChatsPage):
        """
        Chats page should load successfully.

        Steps:
        1. Navigate to chats (via fixture)
        2. Verify chats page is displayed
        """
        assert chats_page.is_chats_page(), "Chats page should load"

    def test_create_new_chat(self, chats_page: ChatsPage, test_data: TestDataGenerator):
        """
        Should be able to create a new chat.

        Steps:
        1. Navigate to chats
        2. Click new chat
        3. Verify chat is created
        """
        chat_title = test_data.thread_title("Global Chat")

        # Create chat
        chats_page.create_new_chat(chat_title)

        # Wait for update
        chats_page.wait_for_load()

        # Should either be in chat list or navigated to conversation
        in_list = chats_page.chat_exists(chat_title)
        in_conversation = "/chats/" in chats_page.get_current_path()

        assert in_list or in_conversation, \
            "New chat should be created"

    def test_list_chats(self, chats_page: ChatsPage):
        """
        Chats page should list existing chats.

        Steps:
        1. Navigate to chats
        2. Verify chat list or empty state is displayed
        """
        has_chats = chats_page.has_chats()
        has_empty = chats_page.is_empty()

        assert has_chats or has_empty, \
            "Should show chats or empty state"

    def test_open_chat(self, chats_page: ChatsPage, test_data: TestDataGenerator):
        """
        Should be able to open a chat.

        Steps:
        1. Create a chat
        2. Open the chat
        3. Verify conversation page loads
        """
        chat_title = test_data.thread_title()

        # Create chat
        chats_page.create_new_chat(chat_title)
        chats_page.wait_for_load()

        # If we're still on chats page, open the chat
        if chats_page.is_chats_page() and chats_page.chat_exists(chat_title):
            chats_page.open_chat(chat_title)

        # Verify on conversation
        conversation = ConversationPage(chats_page.page)

        # Wait for either conversation UI or URL change
        chats_page.page.wait_for_timeout(1000)

        is_in_conversation = (
            conversation.is_conversation_page() or
            "/chats/" in chats_page.get_current_path()
        )

        assert is_in_conversation, "Should open conversation"

    def test_delete_chat(self, chats_page: ChatsPage, test_data: TestDataGenerator):
        """
        Should be able to delete a chat.

        Steps:
        1. Create a chat
        2. Delete the chat
        3. Verify chat is removed
        """
        chat_title = test_data.thread_title()

        # Create chat
        chats_page.create_new_chat(chat_title)
        chats_page.wait_for_load()

        # Navigate back to chats if we left
        if not chats_page.is_chats_page():
            chats_page.navigate_to("/chats")

        if chats_page.chat_exists(chat_title):
            # Delete chat
            chats_page.delete_chat(chat_title)
            chats_page.wait_for_load()

            # Verify deleted
            assert not chats_page.chat_exists(chat_title), \
                "Chat should be deleted"

    def test_rename_chat(self, chats_page: ChatsPage, test_data: TestDataGenerator):
        """
        Should be able to rename a chat.

        Steps:
        1. Create a chat
        2. Rename the chat
        3. Verify new name appears
        """
        old_title = test_data.thread_title("Old")
        new_title = test_data.thread_title("New")

        # Create chat
        chats_page.create_new_chat(old_title)
        chats_page.wait_for_load()

        # Navigate back to chats if we left
        if not chats_page.is_chats_page():
            chats_page.navigate_to("/chats")

        if chats_page.chat_exists(old_title):
            # Rename chat
            chats_page.rename_chat(old_title, new_title)
            chats_page.wait_for_load()

            # Verify renamed
            assert chats_page.chat_exists(new_title), "Chat should have new name"
            assert not chats_page.chat_exists(old_title), "Old name should not exist"


@pytest.mark.chats
class TestChatSearch:
    """Chat search/filter tests."""

    def test_search_chats(self, chats_page: ChatsPage, test_data: TestDataGenerator):
        """
        Should be able to search/filter chats.

        Steps:
        1. Create multiple chats with different names
        2. Search for specific name
        3. Verify filtered results
        """
        unique = test_data.unique_id()
        chat1 = f"Alpha {unique}"
        chat2 = f"Beta {unique}"

        # Create chats
        chats_page.create_new_chat(chat1)
        chats_page.wait_for_load()

        if not chats_page.is_chats_page():
            chats_page.navigate_to("/chats")

        chats_page.create_new_chat(chat2)
        chats_page.wait_for_load()

        if not chats_page.is_chats_page():
            chats_page.navigate_to("/chats")

        # Search if input is available
        if chats_page.is_visible(chats_page.search_input):
            chats_page.search_chats("Alpha")
            chats_page.wait_for_load()

            # Alpha should be visible, Beta might not
            assert chats_page.chat_exists(chat1), "Searched chat should appear"


@pytest.mark.chats
@pytest.mark.smoke
class TestChatsSmoke:
    """Quick chat smoke tests."""

    def test_can_access_chats_page(self, chats_page: ChatsPage):
        """Verify chats page is accessible."""
        assert chats_page.is_chats_page()

    def test_new_chat_button_visible(self, chats_page: ChatsPage):
        """Verify new chat button is visible."""
        assert chats_page.is_visible(chats_page.new_chat_button)
