"""
Custom wait conditions and helpers for E2E tests.
"""
from playwright.sync_api import Page, Locator, expect
from config.settings import settings
from typing import Callable, Optional
import time


class WaitHelpers:
    """Custom wait conditions for Flutter web app testing."""

    @staticmethod
    def wait_for_flutter_ready(page: Page, timeout: int = None) -> None:
        """
        Wait for Flutter web app to be fully loaded and ready.

        Flutter web apps have a loading indicator that disappears when ready.
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT

        # Wait for Flutter's loading indicator to disappear
        # Flutter web shows a loading spinner during initialization
        page.wait_for_function(
            """
            () => {
                // Check if Flutter loading indicator is gone
                const loading = document.querySelector('flt-glass-pane');
                if (!loading) return false;

                // Check if the app has rendered content
                const hasContent = document.body.textContent.length > 100;
                return hasContent;
            }
            """,
            timeout=timeout
        )

        # Additional wait for any animations to settle
        page.wait_for_timeout(500)

    @staticmethod
    def wait_for_navigation_complete(page: Page, timeout: int = None) -> None:
        """Wait for navigation to complete (URL change + content load)."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        page.wait_for_load_state("networkidle", timeout=timeout)

    @staticmethod
    def wait_for_element_text(
        locator: Locator,
        expected_text: str,
        timeout: int = None
    ) -> None:
        """Wait for an element to contain specific text."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_contain_text(expected_text, timeout=timeout)

    @staticmethod
    def wait_for_element_visible(
        locator: Locator,
        timeout: int = None
    ) -> None:
        """Wait for an element to become visible."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_be_visible(timeout=timeout)

    @staticmethod
    def wait_for_element_hidden(
        locator: Locator,
        timeout: int = None
    ) -> None:
        """Wait for an element to become hidden."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_be_hidden(timeout=timeout)

    @staticmethod
    def wait_for_element_enabled(
        locator: Locator,
        timeout: int = None
    ) -> None:
        """Wait for an element to become enabled."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_be_enabled(timeout=timeout)

    @staticmethod
    def wait_for_url_contains(
        page: Page,
        url_part: str,
        timeout: int = None
    ) -> None:
        """Wait for URL to contain a specific string."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        page.wait_for_url(f"**{url_part}**", timeout=timeout)

    @staticmethod
    def wait_for_api_response(
        page: Page,
        url_pattern: str,
        timeout: int = None
    ) -> None:
        """
        Wait for a specific API call to complete.

        Args:
            page: Playwright page
            url_pattern: Pattern to match (e.g., "**/api/projects*")
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        with page.expect_response(url_pattern, timeout=timeout):
            pass

    @staticmethod
    def wait_for_toast_message(
        page: Page,
        message: str = None,
        timeout: int = None
    ) -> None:
        """
        Wait for a toast/snackbar message to appear.

        Args:
            page: Playwright page
            message: Optional message text to wait for
            timeout: Timeout in ms
        """
        timeout = timeout or settings.TIMEOUT_SHORT

        # Look for common snackbar/toast patterns
        snackbar = page.locator("[role='alert'], .snackbar, .toast")

        if message:
            expect(snackbar).to_contain_text(message, timeout=timeout)
        else:
            expect(snackbar).to_be_visible(timeout=timeout)

    @staticmethod
    def wait_for_dialog(
        page: Page,
        timeout: int = None
    ) -> Locator:
        """Wait for a dialog to appear and return its locator."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        dialog = page.locator("[role='dialog'], [role='alertdialog']")
        expect(dialog).to_be_visible(timeout=timeout)
        return dialog

    @staticmethod
    def wait_for_dialog_closed(
        page: Page,
        timeout: int = None
    ) -> None:
        """Wait for all dialogs to close."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        dialog = page.locator("[role='dialog'], [role='alertdialog']")
        expect(dialog).to_be_hidden(timeout=timeout)

    @staticmethod
    def wait_for_loading_complete(
        page: Page,
        timeout: int = None
    ) -> None:
        """Wait for loading indicators to disappear."""
        timeout = timeout or settings.TIMEOUT_DEFAULT

        # Common loading indicator patterns
        loading_selectors = [
            "[role='progressbar']",
            ".loading",
            ".spinner",
            "[aria-busy='true']"
        ]

        for selector in loading_selectors:
            loading = page.locator(selector)
            if loading.count() > 0:
                expect(loading.first).to_be_hidden(timeout=timeout)

    @staticmethod
    def wait_for_list_items(
        locator: Locator,
        min_count: int = 1,
        timeout: int = None
    ) -> None:
        """Wait for a list to have at least min_count items."""
        timeout = timeout or settings.TIMEOUT_DEFAULT
        expect(locator).to_have_count(min_count, timeout=timeout)

    @staticmethod
    def retry_until(
        condition: Callable[[], bool],
        timeout: int = None,
        interval: int = 500
    ) -> bool:
        """
        Retry a condition until it returns True or timeout.

        Args:
            condition: Callable that returns True when condition is met
            timeout: Timeout in ms
            interval: Check interval in ms

        Returns:
            True if condition was met, False if timed out
        """
        timeout = timeout or settings.TIMEOUT_DEFAULT
        start_time = time.time()
        timeout_seconds = timeout / 1000

        while time.time() - start_time < timeout_seconds:
            try:
                if condition():
                    return True
            except Exception:
                pass
            time.sleep(interval / 1000)

        return False

    @staticmethod
    def wait_for_stable_dom(page: Page, stability_time: int = 500) -> None:
        """
        Wait for DOM to be stable (no changes for stability_time ms).

        Useful after animations or dynamic content loading.
        """
        page.wait_for_function(
            f"""
            async () => {{
                return new Promise(resolve => {{
                    let lastHtml = document.body.innerHTML;
                    let stableTime = 0;
                    const interval = 100;

                    const check = () => {{
                        const currentHtml = document.body.innerHTML;
                        if (currentHtml === lastHtml) {{
                            stableTime += interval;
                            if (stableTime >= {stability_time}) {{
                                resolve(true);
                                return;
                            }}
                        }} else {{
                            stableTime = 0;
                            lastHtml = currentHtml;
                        }}
                        setTimeout(check, interval);
                    }};

                    check();
                }});
            }}
            """,
            timeout=settings.TIMEOUT_DEFAULT
        )
