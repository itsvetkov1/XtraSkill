"""
Pytest configuration for service unit tests.

This file can contain service-specific fixtures for unit tests.
Shared fixtures (db, auth, llm, factories) come from tests/fixtures/
via pytest_plugins in the root conftest.py.

Note: Unit tests in this directory should test pure functions without
database or external dependencies. For integration tests that require
the database, use tests/integration/ directory.
"""

import pytest


# Service-specific fixtures can be added here as needed.
# For example:
#
# @pytest.fixture
# def sample_message_data():
#     """Sample message data for testing."""
#     return {
#         "role": "user",
#         "content": "Hello, how can you help me?"
#     }
