"""Unit tests for token_tracking database functions."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.services.token_tracking import (
    track_token_usage,
    get_monthly_usage,
    check_user_budget,
    DEFAULT_MONTHLY_BUDGET,
)
from app.models import TokenUsage


class TestTrackTokenUsage:
    """Tests for track_token_usage function."""

    @pytest.mark.asyncio
    async def test_creates_usage_record(self, db_session, user):
        """Creates TokenUsage record with correct attributes."""
        db_session.add(user)
        await db_session.commit()

        usage = await track_token_usage(
            db_session,
            user.id,
            "claude-sonnet-4-5-20250929",
            100,
            50,
            "/api/chat"
        )

        assert usage.user_id == user.id
        assert usage.request_tokens == 100
        assert usage.response_tokens == 50
        assert usage.endpoint == "/api/chat"
        assert usage.model == "claude-sonnet-4-5-20250929"

    @pytest.mark.asyncio
    async def test_calculates_cost_correctly(self, db_session, user):
        """Cost is calculated based on model pricing."""
        db_session.add(user)
        await db_session.commit()

        usage = await track_token_usage(
            db_session,
            user.id,
            "claude-sonnet-4-5-20250929",
            1_000_000,  # $3
            1_000_000,  # $15
            "/api/chat"
        )

        assert usage.total_cost == Decimal("18.00")

    @pytest.mark.asyncio
    async def test_persists_to_database(self, db_session, user):
        """Usage record is persisted and can be queried."""
        db_session.add(user)
        await db_session.commit()

        usage = await track_token_usage(
            db_session,
            user.id,
            "claude-sonnet",
            100,
            50,
            "/api/chat"
        )

        # Query back from DB
        from sqlalchemy import select
        result = await db_session.execute(
            select(TokenUsage).where(TokenUsage.id == usage.id)
        )
        persisted = result.scalar_one()

        assert persisted.request_tokens == 100


class TestGetMonthlyUsage:
    """Tests for get_monthly_usage function."""

    @pytest.mark.asyncio
    async def test_returns_zero_for_new_user(self, db_session, user):
        """New user with no usage returns zeros."""
        db_session.add(user)
        await db_session.commit()

        usage = await get_monthly_usage(db_session, user.id)

        assert usage["total_cost"] == Decimal("0")
        assert usage["total_requests"] == 0
        assert usage["total_input_tokens"] == 0
        assert usage["total_output_tokens"] == 0

    @pytest.mark.asyncio
    async def test_aggregates_multiple_requests(self, db_session, user):
        """Aggregates usage across multiple requests."""
        db_session.add(user)
        await db_session.commit()

        await track_token_usage(db_session, user.id, "claude", 100, 50, "/chat")
        await track_token_usage(db_session, user.id, "claude", 200, 100, "/chat")
        await track_token_usage(db_session, user.id, "claude", 300, 150, "/chat")

        usage = await get_monthly_usage(db_session, user.id)

        assert usage["total_requests"] == 3
        assert usage["total_input_tokens"] == 600
        assert usage["total_output_tokens"] == 300

    @pytest.mark.asyncio
    async def test_includes_budget_info(self, db_session, user):
        """Response includes budget and month_start."""
        db_session.add(user)
        await db_session.commit()

        usage = await get_monthly_usage(db_session, user.id)

        assert "budget" in usage
        assert usage["budget"] == DEFAULT_MONTHLY_BUDGET
        assert "month_start" in usage

    @pytest.mark.asyncio
    async def test_only_includes_current_month(self, db_session, user):
        """Only includes usage from current month."""
        db_session.add(user)
        await db_session.commit()

        # Create usage record for current month
        await track_token_usage(db_session, user.id, "claude", 100, 50, "/chat")

        # Manually create old usage record (last month)
        old_usage = TokenUsage(
            user_id=user.id,
            request_tokens=999,
            response_tokens=999,
            total_cost=Decimal("10.00"),
            endpoint="/old",
            model="claude",
            created_at=datetime.now(timezone.utc) - timedelta(days=35)
        )
        db_session.add(old_usage)
        await db_session.commit()

        usage = await get_monthly_usage(db_session, user.id)

        # Should only count current month's 100 tokens
        assert usage["total_input_tokens"] == 100
        assert usage["total_requests"] == 1


class TestCheckUserBudget:
    """Tests for check_user_budget function."""

    @pytest.mark.asyncio
    async def test_returns_true_for_new_user(self, db_session, user):
        """New user is under budget."""
        db_session.add(user)
        await db_session.commit()

        result = await check_user_budget(db_session, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_over_budget(self, db_session, user):
        """Returns False when user exceeds monthly budget."""
        db_session.add(user)
        await db_session.commit()

        # Create large usage that exceeds $50 budget
        # $51 worth of tokens
        usage = TokenUsage(
            user_id=user.id,
            request_tokens=17_000_000,  # ~$51 at $3/1M
            response_tokens=0,
            total_cost=Decimal("51.00"),
            endpoint="/chat",
            model="claude"
        )
        db_session.add(usage)
        await db_session.commit()

        result = await check_user_budget(db_session, user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_custom_budget_limit(self, db_session, user):
        """Respects custom monthly limit."""
        db_session.add(user)
        await db_session.commit()

        # Add $5 worth of usage
        usage = TokenUsage(
            user_id=user.id,
            request_tokens=1_000_000,
            response_tokens=0,
            total_cost=Decimal("5.00"),
            endpoint="/chat",
            model="claude"
        )
        db_session.add(usage)
        await db_session.commit()

        # With $10 limit, should be under
        assert await check_user_budget(db_session, user.id, Decimal("10.00")) is True

        # With $3 limit, should be over
        assert await check_user_budget(db_session, user.id, Decimal("3.00")) is False
