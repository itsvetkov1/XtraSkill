"""Pytest configuration and fixtures for backend tests."""

# Import all fixtures from the fixtures module
# This enables pytest to discover fixtures via pytest_plugins
pytest_plugins = [
    "tests.fixtures.db_fixtures",
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.llm_fixtures",
    "tests.fixtures.factories",
]

# Keep skill integration fixtures in conftest for backward compatibility
# These are specific to skill tests and used infrequently

import pytest


@pytest.fixture
def skill_prompt():
    """Load the business-analyst skill prompt for testing."""
    from app.services.skill_loader import load_skill_prompt
    return load_skill_prompt()


@pytest.fixture
def mock_agent_response():
    """Factory for creating mock agent responses."""
    def _create_response(text: str, tool_calls: list = None):
        return {
            "text": text,
            "tool_calls": tool_calls or [],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }
    return _create_response


@pytest.fixture
def sample_discovery_context():
    """Sample context from a discovery conversation."""
    return {
        "business_objective": "Reduce customer onboarding time from 14 days to 2 days",
        "personas": [
            {
                "name": "Account Manager",
                "role": "Manages customer relationships",
                "pain_points": ["Manual data entry", "Slow approval process"],
                "goals": ["Faster customer activation", "More time for strategic work"]
            }
        ],
        "user_flows": [
            "Customer signs contract -> Account Manager creates account -> Customer activates"
        ],
        "success_metrics": [
            "Onboarding time < 2 days",
            "Customer satisfaction > 90%"
        ]
    }


@pytest.fixture
def sample_brd_content():
    """Sample valid BRD content for testing."""
    return """# Business Requirements Document: Customer Onboarding Portal

## Executive Summary
The Customer Onboarding Portal aims to reduce customer onboarding time from 14 days to 2 days.

## Business Context
Current manual process requires 5 different systems and multiple handoffs.

## Business Objectives

### Primary Objective
Reduce onboarding time from 14 days to 2 days by automating data entry and approvals.
"""
