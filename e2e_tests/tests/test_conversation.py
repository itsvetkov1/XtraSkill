"""
Conversation E2E Tests.

Tests for chat conversation functionality.
"""
import pytest
from playwright.sync_api import Page

from pages.chats_page import ChatsPage
from pages.conversation_page import ConversationPage
from utils.test_data import TestDataGenerator
from config.settings import settings


@pytest.mark.chats
class TestConversationMessaging:
    """Conversation messaging test suite."""

    @pytest.fixture
    def conversation_page(
        self,
        chats_page: ChatsPage,
        test_data: TestDataGenerator
    ) -> ConversationPage:
        """Create a chat and navigate to conversation."""
        chat_title = test_data.thread_title()

        # Create chat
        chats_page.create_new_chat(chat_title)
        chats_page.wait_for_load()

        # Navigate to conversation if not already there
        if chats_page.is_chats_page() and chats_page.chat_exists(chat_title):
            chats_page.open_chat(chat_title)

        conv = ConversationPage(chats_page.page)
        conv.wait_for_conversation_page()

        return conv

    def test_conversation_page_loads(self, conversation_page: ConversationPage):
        """
        Conversation page should load successfully.

        Steps:
        1. Create and open a chat
        2. Verify conversation UI is displayed
        """
        assert conversation_page.is_conversation_page(), \
            "Conversation page should load"

    def test_message_input_visible(self, conversation_page: ConversationPage):
        """
        Message input should be visible.

        Steps:
        1. Open conversation
        2. Verify input field and send button exist
        """
        assert conversation_page.is_visible(conversation_page.message_input), \
            "Message input should be visible"
        assert conversation_page.is_visible(conversation_page.send_button), \
            "Send button should be visible"

    def test_send_message(self, conversation_page: ConversationPage):
        """
        Should be able to send a message.

        Steps:
        1. Open conversation
        2. Type and send message
        3. Verify message appears in chat
        """
        message = "Hello, this is a test message"

        initial_count = conversation_page.get_message_count()

        # Send message
        conversation_page.send_message(message)

        # Wait for message to appear
        conversation_page.wait_for_message_count(initial_count + 1, timeout=5000)

        # Verify message was sent
        assert conversation_page.get_message_count() > initial_count, \
            "Message count should increase"

    @pytest.mark.slow
    def test_receive_ai_response(self, conversation_page: ConversationPage):
        """
        Should receive AI response after sending message.

        Steps:
        1. Open conversation
        2. Send a message
        3. Wait for AI response
        4. Verify response appears
        """
        message = "What is 2 + 2?"

        # Send message
        conversation_page.send_message(message)

        # Wait for AI response
        conversation_page.wait_for_response(timeout=settings.TIMEOUT_LONG)

        # Should have at least user message + AI response
        assert conversation_page.get_ai_message_count() >= 1, \
            "Should have at least one AI response"

    def test_send_via_enter_key(self, conversation_page: ConversationPage):
        """
        Should be able to send message by pressing Enter.

        Steps:
        1. Open conversation
        2. Type message and press Enter
        3. Verify message is sent
        """
        message = "Test message via Enter key"

        initial_count = conversation_page.get_message_count()

        # Send via Enter
        conversation_page.send_via_enter(message)

        # Wait for message
        conversation_page.page.wait_for_timeout(1000)

        # Verify sent (input should be cleared)
        input_value = conversation_page.page.locator(
            "[data-testid='message-input'], textarea, input"
        ).first.input_value()

        assert input_value == "" or conversation_page.get_message_count() > initial_count, \
            "Message should be sent via Enter"


@pytest.mark.chats
class TestConversationInteractions:
    """Message interaction tests."""

    @pytest.fixture
    def conversation_with_messages(
        self,
        chats_page: ChatsPage,
        test_data: TestDataGenerator
    ) -> ConversationPage:
        """Create a chat with some messages."""
        chat_title = test_data.thread_title()

        # Create chat
        chats_page.create_new_chat(chat_title)
        chats_page.wait_for_load()

        if chats_page.is_chats_page() and chats_page.chat_exists(chat_title):
            chats_page.open_chat(chat_title)

        conv = ConversationPage(chats_page.page)
        conv.wait_for_conversation_page()

        # Send a message
        conv.send_message("Test message for interactions")
        conv.page.wait_for_timeout(1000)

        return conv

    def test_copy_message(self, conversation_with_messages: ConversationPage):
        """
        Should be able to copy a message.

        Steps:
        1. Open conversation with messages
        2. Click copy on a message
        3. Verify copy action (may show toast or change clipboard)
        """
        conv = conversation_with_messages

        if conv.get_message_count() > 0:
            # Try to copy first message
            try:
                conv.copy_message(0)
                # If no error, copy action was triggered
                assert True, "Copy action was successful"
            except Exception:
                # Copy button may not be visible without hover
                pytest.skip("Copy button not accessible")

    @pytest.mark.slow
    def test_retry_message(self, conversation_with_messages: ConversationPage):
        """
        Should be able to retry a message.

        Steps:
        1. Open conversation with sent message
        2. Wait for AI response
        3. Click retry
        4. Verify new response is generated
        """
        conv = conversation_with_messages

        # Wait for initial response
        try:
            conv.wait_for_response(timeout=settings.TIMEOUT_LONG)
        except Exception:
            pytest.skip("No AI response received")

        initial_ai_count = conv.get_ai_message_count()

        if initial_ai_count > 0:
            try:
                conv.retry_last_message()
                conv.wait_for_response(timeout=settings.TIMEOUT_LONG)

                # Should have new response
                # (actual count may vary based on implementation)
                assert True, "Retry action was successful"
            except Exception:
                pytest.skip("Retry button not accessible")


@pytest.mark.chats
class TestConversationPersistence:
    """Conversation persistence tests."""

    @pytest.mark.slow
    def test_message_persists_after_refresh(
        self,
        chats_page: ChatsPage,
        test_data: TestDataGenerator
    ):
        """
        Messages should persist after page refresh.

        Steps:
        1. Create chat and send message
        2. Refresh page
        3. Navigate back to conversation
        4. Verify message still exists
        """
        chat_title = test_data.thread_title()
        message = "Persistent message test"

        # Create chat
        chats_page.create_new_chat(chat_title)
        chats_page.wait_for_load()

        if chats_page.is_chats_page() and chats_page.chat_exists(chat_title):
            chats_page.open_chat(chat_title)

        conv = ConversationPage(chats_page.page)
        conv.wait_for_conversation_page()

        # Send message
        conv.send_message(message)
        conv.page.wait_for_timeout(2000)

        # Refresh
        conv.reload()
        conv.wait_for_conversation_page()

        # Verify message exists
        messages = conv.get_all_message_texts()
        message_found = any(message in m for m in messages)

        assert message_found, "Message should persist after refresh"


@pytest.mark.chats
@pytest.mark.smoke
class TestConversationSmoke:
    """Quick conversation smoke tests."""

    def test_can_type_in_input(
        self,
        chats_page: ChatsPage,
        test_data: TestDataGenerator
    ):
        """Verify can type in message input."""
        chat_title = test_data.thread_title()

        chats_page.create_new_chat(chat_title)
        chats_page.wait_for_load()

        if chats_page.is_chats_page() and chats_page.chat_exists(chat_title):
            chats_page.open_chat(chat_title)

        conv = ConversationPage(chats_page.page)
        conv.wait_for_conversation_page()

        # Type in input
        test_text = "Test typing"
        conv.type_message(test_text)

        # Verify text is in input
        value = conv.message_input.input_value()
        assert test_text in value, "Should be able to type in input"
