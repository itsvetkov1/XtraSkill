"""
Token usage tracking service for AI cost monitoring.

Tracks token usage per request, calculates costs, and enforces
monthly budgets to prevent cost explosion.
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import TokenUsage

# Claude pricing (Claude 4.5 Sonnet)
# $3/1M input, $15/1M output
PRICING = {
    "claude-sonnet-4-5-20250929": {
        "input": Decimal("3.00"),   # $3 per 1M input tokens
        "output": Decimal("15.00"),  # $15 per 1M output tokens
    },
    # Fallback pricing
    "default": {
        "input": Decimal("3.00"),
        "output": Decimal("15.00"),
    }
}

# Default monthly budget per user
DEFAULT_MONTHLY_BUDGET = Decimal("50.00")  # $50/month


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> Decimal:
    """
    Calculate cost for token usage.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in USD
    """
    pricing = PRICING.get(model, PRICING["default"])

    input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * pricing["input"]
    output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * pricing["output"]

    return input_cost + output_cost


async def track_token_usage(
    db: AsyncSession,
    user_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    endpoint: str
) -> TokenUsage:
    """
    Record token usage for a request.

    Args:
        db: Database session
        user_id: User ID
        model: Model name used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        endpoint: API endpoint that used tokens

    Returns:
        Created TokenUsage record
    """
    total_cost = calculate_cost(model, input_tokens, output_tokens)

    usage = TokenUsage(
        user_id=user_id,
        request_tokens=input_tokens,
        response_tokens=output_tokens,
        total_cost=total_cost,
        endpoint=endpoint,
        model=model
    )

    db.add(usage)
    await db.commit()
    await db.refresh(usage)

    return usage


async def get_monthly_usage(
    db: AsyncSession,
    user_id: str
) -> dict:
    """
    Get token usage statistics for current month.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dict with total_cost, total_requests, total_input_tokens, total_output_tokens
    """
    month_start = datetime.utcnow().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    result = await db.execute(
        select(
            func.sum(TokenUsage.total_cost).label("total_cost"),
            func.count(TokenUsage.id).label("total_requests"),
            func.sum(TokenUsage.request_tokens).label("total_input_tokens"),
            func.sum(TokenUsage.response_tokens).label("total_output_tokens")
        ).where(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= month_start
        )
    )
    row = result.first()

    return {
        "total_cost": row.total_cost or Decimal("0"),
        "total_requests": row.total_requests or 0,
        "total_input_tokens": row.total_input_tokens or 0,
        "total_output_tokens": row.total_output_tokens or 0,
        "month_start": month_start.isoformat(),
        "budget": DEFAULT_MONTHLY_BUDGET
    }


async def check_user_budget(
    db: AsyncSession,
    user_id: str,
    monthly_limit: Optional[Decimal] = None
) -> bool:
    """
    Check if user is within monthly budget.

    Args:
        db: Database session
        user_id: User ID
        monthly_limit: Optional custom limit (defaults to DEFAULT_MONTHLY_BUDGET)

    Returns:
        True if user can make requests, False if budget exceeded
    """
    limit = monthly_limit or DEFAULT_MONTHLY_BUDGET
    usage = await get_monthly_usage(db, user_id)

    return usage["total_cost"] < limit
