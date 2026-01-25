"""Pytest configuration and fixtures for backend tests."""

import os
import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from main import app


# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Set up test environment variables
if not os.getenv("FERNET_KEY"):
    # Generate a test key for encryption
    os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-jwt"


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key constraints for SQLite tests
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create FTS5 virtual table for document search
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
                document_id UNINDEXED,
                filename,
                content,
                tokenize = 'porter ascii'
            )
        """))

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session_maker = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """Create test HTTP client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================
# Skill Integration Test Fixtures
# ============================================

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

### Secondary Objectives
Improve customer satisfaction scores from 75% to 90%.

## User Personas

### Persona 1: Account Manager
- **Demographics:** 30-45 years old, 5+ years experience
- **Role and Responsibilities:** Manages customer relationships, handles onboarding
- **Pain Points:** Manual data entry, slow approval process
- **Goals:** Faster customer activation, more time for strategic work
- **Technical Proficiency:** Intermediate

## User Flows and Journeys

### Flow 1: New Customer Onboarding
**User Persona:** Account Manager
**Business Goal:** Complete customer setup in under 2 days
**User Goal:** Activate customer account quickly

**Steps:**
1. Account Manager receives signed contract
2. System auto-populates customer data from contract
3. Account Manager reviews and confirms
4. Customer receives activation email

## Functional Requirements

### Must-Have Requirements (Priority 0)
1. **Automated Data Entry**
   - Description: System extracts customer data from signed contracts
   - Business rationale: Eliminates manual data entry errors and delays
   - User story: As an Account Manager, I need automated data extraction so that I can onboard customers faster
   - Success criteria: 95% of fields auto-populated correctly

## Business Processes

### Process 1: Customer Onboarding
- **Current State:** 14 days, 5 systems, multiple manual handoffs
- **Future State:** 2 days, single system, automated workflows
- **Process Flow:** Contract -> Auto-extract -> Review -> Activate
- **Stakeholders:** Sales, Account Management, Customer Success

## Stakeholder Analysis

| Stakeholder Group | Role | Key Requirements | Success Criteria | Concerns |
|-------------------|------|------------------|------------------|----------|
| Account Managers | Primary users | Fast onboarding | < 2 days | Learning curve |
| Customers | End beneficiaries | Quick activation | < 48 hours | Data security |

## Success Metrics and KPIs

| KPI | Current State | Target State | Measurement Method | Timeline |
|-----|---------------|--------------|-------------------|----------|
| Onboarding time | 14 days | 2 days | Time tracking | 3 months |
| Customer satisfaction | 75% | 90% | NPS survey | 6 months |

## Regulatory and Compliance Requirements
Data must be stored in accordance with GDPR requirements. Customer consent required for data processing.

## Assumptions and Constraints
**Assumptions:**
- Contracts are digitally signed and machine-readable
- Account Managers have stable internet connectivity

**Constraints:**
- Must integrate with existing CRM system
- Must launch before Q4 2026

## Risks and Mitigation Strategies

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|-------------------|
| Integration delays | High | Medium | Early prototyping with CRM team |
| User adoption resistance | Medium | Low | Training program and champions |

## Next Steps
- Technical team review and architecture design
- Proposal development with cost and timeline estimates
- Customer review and sign-off on requirements
"""
