"""
Authentication helper for E2E tests.
Handles OAuth mocking through token injection and API interception.
"""
from playwright.sync_api import Page, BrowserContext, Route
from config.test_users import TestUser, TestUsers, DEFAULT_TOKEN
from config.settings import settings
import json
from typing import Optional


class AuthHelper:
    """Helper class for authentication mocking in E2E tests."""

    # Flutter web storage keys
    STORAGE_KEY_TOKEN = "flutter.auth_token"
    STORAGE_KEY_USER = "flutter.user_data"
    STORAGE_KEY_REFRESH = "flutter.refresh_token"

    @staticmethod
    def inject_auth_token(page: Page, token: str) -> None:
        """
        Inject JWT token into Flutter's localStorage.

        Flutter web uses localStorage with 'flutter.' prefix for secure storage.
        """
        page.evaluate(f"""
            localStorage.setItem('{AuthHelper.STORAGE_KEY_TOKEN}', '{token}');
        """)

    @staticmethod
    def inject_user_data(page: Page, user: TestUser) -> None:
        """
        Inject user data into localStorage.
        """
        user_json = json.dumps(user.to_dict())
        page.evaluate(f"""
            localStorage.setItem('{AuthHelper.STORAGE_KEY_USER}', '{user_json}');
        """)

    @staticmethod
    def inject_full_auth(
        page: Page,
        user: TestUser = None,
        token: str = None
    ) -> None:
        """
        Inject complete authentication state.

        Args:
            page: Playwright page instance
            user: Test user (defaults to TestUsers.DEFAULT)
            token: JWT token (auto-generated if not provided)
        """
        user = user or TestUsers.DEFAULT
        token = token or TestUsers.generate_token(user)

        AuthHelper.inject_auth_token(page, token)
        AuthHelper.inject_user_data(page, user)

    @staticmethod
    def clear_auth(page: Page) -> None:
        """Clear all authentication data from localStorage."""
        page.evaluate(f"""
            localStorage.removeItem('{AuthHelper.STORAGE_KEY_TOKEN}');
            localStorage.removeItem('{AuthHelper.STORAGE_KEY_USER}');
            localStorage.removeItem('{AuthHelper.STORAGE_KEY_REFRESH}');
        """)

    @staticmethod
    def get_stored_token(page: Page) -> Optional[str]:
        """Get the currently stored auth token."""
        return page.evaluate(f"""
            localStorage.getItem('{AuthHelper.STORAGE_KEY_TOKEN}')
        """)

    @staticmethod
    def is_authenticated(page: Page) -> bool:
        """Check if user appears to be authenticated."""
        token = AuthHelper.get_stored_token(page)
        return token is not None and len(token) > 0

    @staticmethod
    def setup_auth_intercept(
        context: BrowserContext,
        user: TestUser = None
    ) -> None:
        """
        Set up route interception to mock auth API responses.

        This intercepts calls to /auth/me to return mock user data
        without requiring a real OAuth flow.
        """
        user = user or TestUsers.DEFAULT

        def handle_auth_me(route: Route) -> None:
            """Handle /auth/me requests with mock response."""
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "user": user.to_dict(),
                    "authenticated": True
                })
            )

        def handle_auth_logout(route: Route) -> None:
            """Handle /auth/logout requests."""
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True})
            )

        # Intercept auth endpoints
        context.route("**/auth/me", handle_auth_me)
        context.route("**/auth/logout", handle_auth_logout)

    @staticmethod
    def setup_authenticated_context(
        context: BrowserContext,
        user: TestUser = None,
        token: str = None
    ) -> None:
        """
        Set up a fully authenticated browser context.

        This sets up both:
        1. Route interception for API mocking
        2. Storage state will be injected after page load
        """
        user = user or TestUsers.DEFAULT
        AuthHelper.setup_auth_intercept(context, user)

    @staticmethod
    def authenticate_page(
        page: Page,
        user: TestUser = None,
        token: str = None
    ) -> None:
        """
        Authenticate a page by injecting auth state.

        Call this after navigating to the app but before interacting.
        """
        user = user or TestUsers.DEFAULT
        token = token or TestUsers.generate_token(user)

        # Navigate to base URL first to set localStorage on correct origin
        page.goto(settings.FRONTEND_URL)

        # Inject auth data
        AuthHelper.inject_full_auth(page, user, token)

        # Reload to pick up auth state
        page.reload()

    @staticmethod
    def login_as(
        page: Page,
        user: TestUser = None,
        navigate_to: str = None
    ) -> None:
        """
        Convenience method to log in as a test user and navigate.

        Args:
            page: Playwright page
            user: Test user to log in as
            navigate_to: Optional path to navigate to after auth
        """
        user = user or TestUsers.DEFAULT
        AuthHelper.authenticate_page(page, user)

        if navigate_to:
            full_url = settings.get_frontend_url(navigate_to)
            page.goto(full_url)
