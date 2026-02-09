"""
Home Page Object for the main dashboard screen.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from typing import List


class HomePage(BasePage):
    """
    Page Object for the Home screen.

    Handles home screen interactions including recent projects,
    quick actions, and welcome messages.
    """

    # ==================== Locators ====================

    @property
    def welcome_message(self) -> Locator:
        """Welcome message/greeting."""
        return self.page.locator("[data-testid='welcome-message'], .welcome-message")

    @property
    def user_greeting(self) -> Locator:
        """User-specific greeting (e.g., "Hello, John")."""
        return self.page.get_by_text("Hello,").first

    @property
    def recent_projects_section(self) -> Locator:
        """Recent projects section container."""
        return self.page.locator("[data-testid='recent-projects'], .recent-projects")

    @property
    def project_cards(self) -> Locator:
        """All project cards on home screen."""
        return self.page.locator("[data-testid='project-card'], .project-card")

    @property
    def quick_actions_section(self) -> Locator:
        """Quick actions section container."""
        return self.page.locator("[data-testid='quick-actions'], .quick-actions")

    @property
    def new_project_button(self) -> Locator:
        """New project quick action button."""
        return self.page.get_by_role("button", name="New Project")

    @property
    def new_chat_button(self) -> Locator:
        """New chat quick action button."""
        return self.page.get_by_role("button", name="New Chat")

    @property
    def recent_chats_section(self) -> Locator:
        """Recent chats section."""
        return self.page.locator("[data-testid='recent-chats'], .recent-chats")

    @property
    def chat_cards(self) -> Locator:
        """All chat cards on home screen."""
        return self.page.locator("[data-testid='chat-card'], .chat-card")

    @property
    def empty_state(self) -> Locator:
        """Empty state when no projects/chats exist."""
        return self.page.locator("[data-testid='empty-state'], .empty-state")

    # ==================== Actions ====================

    def click_new_project(self) -> None:
        """Click the new project button."""
        self.click(self.new_project_button)

    def click_new_chat(self) -> None:
        """Click the new chat button."""
        self.click(self.new_chat_button)

    def click_project(self, name: str) -> None:
        """
        Click on a specific project card.

        Args:
            name: Project name to click
        """
        project = self.project_cards.filter(has_text=name).first
        self.click(project)

    def click_chat(self, title: str) -> None:
        """
        Click on a specific chat card.

        Args:
            title: Chat title to click
        """
        chat = self.chat_cards.filter(has_text=title).first
        self.click(chat)

    # ==================== Queries ====================

    def get_welcome_text(self) -> str:
        """Get the welcome message text."""
        return self.get_text(self.welcome_message)

    def get_recent_project_names(self) -> List[str]:
        """Get list of recent project names."""
        return self.get_all_texts(self.project_cards)

    def get_recent_chat_titles(self) -> List[str]:
        """Get list of recent chat titles."""
        return self.get_all_texts(self.chat_cards)

    def get_project_count(self) -> int:
        """Get number of project cards displayed."""
        return self.count(self.project_cards)

    def get_chat_count(self) -> int:
        """Get number of chat cards displayed."""
        return self.count(self.chat_cards)

    # ==================== Verification ====================

    def is_home_page(self) -> bool:
        """
        Verify we are on the home page.

        Returns:
            True if on home page, False otherwise
        """
        # Check for home-specific elements
        return (
            self.is_visible(self.welcome_message) or
            self.is_visible(self.quick_actions_section) or
            "/home" in self.get_current_path() or
            self.get_current_path() == "/"
        )

    def wait_for_home_page(self) -> None:
        """Wait for home page to be fully loaded."""
        self.wait_for_load()
        # Wait for content to appear
        try:
            self.wait_for_element(self.welcome_message, timeout=5000)
        except Exception:
            # Fallback: just wait for page to settle
            self.page.wait_for_timeout(1000)

    def has_recent_projects(self) -> bool:
        """Check if there are any recent projects displayed."""
        return self.count(self.project_cards) > 0

    def has_recent_chats(self) -> bool:
        """Check if there are any recent chats displayed."""
        return self.count(self.chat_cards) > 0

    def is_empty_state(self) -> bool:
        """Check if empty state is displayed."""
        return self.is_visible(self.empty_state)

    def project_exists(self, name: str) -> bool:
        """Check if a project with given name is displayed."""
        return self.is_visible(self.project_cards.filter(has_text=name).first)

    def chat_exists(self, title: str) -> bool:
        """Check if a chat with given title is displayed."""
        return self.is_visible(self.chat_cards.filter(has_text=title).first)
