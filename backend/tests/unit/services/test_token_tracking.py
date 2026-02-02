"""Unit tests for token_tracking pure functions."""

import pytest
from decimal import Decimal
from app.services.token_tracking import (
    calculate_cost,
    PRICING,
    DEFAULT_MONTHLY_BUDGET,
)


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_known_model_input_cost(self):
        # Claude Sonnet: $3/1M input tokens
        cost = calculate_cost("claude-sonnet-4-5-20250929", 1_000_000, 0)
        assert cost == Decimal("3.00")

    def test_known_model_output_cost(self):
        # Claude Sonnet: $15/1M output tokens
        cost = calculate_cost("claude-sonnet-4-5-20250929", 0, 1_000_000)
        assert cost == Decimal("15.00")

    def test_known_model_combined_cost(self):
        # 1000 input + 500 output
        # Input: 1000/1M * $3 = $0.003
        # Output: 500/1M * $15 = $0.0075
        cost = calculate_cost("claude-sonnet-4-5-20250929", 1000, 500)
        expected = Decimal("0.003") + Decimal("0.0075")
        assert cost == expected

    def test_unknown_model_uses_default_pricing(self):
        # Unknown model should use default pricing
        cost = calculate_cost("unknown-model-xyz", 1_000_000, 0)
        # Default input price is $3/1M
        assert cost == Decimal("3.00")

    def test_zero_tokens_returns_zero(self):
        cost = calculate_cost("claude-sonnet-4-5-20250929", 0, 0)
        assert cost == Decimal("0")

    def test_decimal_precision_maintained(self):
        # Small token counts should maintain precision
        cost = calculate_cost("claude-sonnet-4-5-20250929", 1, 1)
        # 1/1M * $3 = 0.000003
        # 1/1M * $15 = 0.000015
        # Total = 0.000018
        assert cost > Decimal("0")
        assert cost < Decimal("0.001")

    def test_large_token_count(self):
        # 10M tokens
        cost = calculate_cost("claude-sonnet-4-5-20250929", 10_000_000, 10_000_000)
        # 10 * $3 + 10 * $15 = $30 + $150 = $180
        assert cost == Decimal("180.00")


class TestPricingConfig:
    """Tests for pricing configuration constants."""

    def test_default_pricing_exists(self):
        assert "default" in PRICING
        assert "input" in PRICING["default"]
        assert "output" in PRICING["default"]

    def test_claude_sonnet_pricing_exists(self):
        assert "claude-sonnet-4-5-20250929" in PRICING

    def test_default_monthly_budget_is_reasonable(self):
        # Should be a positive Decimal
        assert DEFAULT_MONTHLY_BUDGET > Decimal("0")
        assert DEFAULT_MONTHLY_BUDGET == Decimal("50.00")
