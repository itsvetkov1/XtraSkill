# Page Objects module for E2E tests
from .base_page import BasePage
from .login_page import LoginPage
from .home_page import HomePage
from .chats_page import ChatsPage
from .projects_page import ProjectsPage
from .project_detail_page import ProjectDetailPage
from .documents_page import DocumentsPage
from .conversation_page import ConversationPage
from .settings_page import SettingsPage

__all__ = [
    "BasePage",
    "LoginPage",
    "HomePage",
    "ChatsPage",
    "ProjectsPage",
    "ProjectDetailPage",
    "DocumentsPage",
    "ConversationPage",
    "SettingsPage",
]
