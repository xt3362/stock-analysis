"""Tests for AdvancingDecliningRatioService."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# NOTE: pandas type stubs are incomplete

from typing import Dict

import pandas as pd
import pytest

from src.domain.models.market_regime import ADRDivergence
from src.domain.services.analysis.advancing_declining_ratio import (
    ADRCalculationResult,
    AdvancingDecliningRatioService,
)


@pytest.fixture
def adr_service() -> AdvancingDecliningRatioService:
    """Create ADR service instance."""
    return AdvancingDecliningRatioService()


@pytest.fixture
def all_advancing_prices() -> Dict[str, pd.DataFrame]:
    """Create universe prices where all stocks are advancing."""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

    prices = {}
    for i in range(10):
        symbol = f"STOCK{i}"
        # All stocks trending up
        close = [100.0 + j * 0.5 for j in range(30)]
        prices[symbol] = pd.DataFrame({"close": close}, index=dates)

    return prices


@pytest.fixture
def all_declining_prices() -> Dict[str, pd.DataFrame]:
    """Create universe prices where all stocks are declining."""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

    prices = {}
    for i in range(10):
        symbol = f"STOCK{i}"
        # All stocks trending down
        close = [100.0 - j * 0.5 for j in range(30)]
        prices[symbol] = pd.DataFrame({"close": close}, index=dates)

    return prices


@pytest.fixture
def mixed_prices() -> Dict[str, pd.DataFrame]:
    """Create universe prices with mixed advancing/declining stocks."""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

    prices = {}
    # 6 advancing stocks
    for i in range(6):
        symbol = f"ADV{i}"
        close = [100.0 + j * 0.5 for j in range(30)]
        prices[symbol] = pd.DataFrame({"close": close}, index=dates)

    # 4 declining stocks
    for i in range(4):
        symbol = f"DEC{i}"
        close = [100.0 - j * 0.5 for j in range(30)]
        prices[symbol] = pd.DataFrame({"close": close}, index=dates)

    return prices


class TestAdvancingDecliningRatioService:
    """Tests for AdvancingDecliningRatioService."""

    def test_calculate_returns_result_object(
        self,
        adr_service: AdvancingDecliningRatioService,
        mixed_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that calculate returns ADRCalculationResult."""
        result = adr_service.calculate(mixed_prices)

        assert isinstance(result, ADRCalculationResult)
        assert isinstance(result.short_term_adr, float)
        assert isinstance(result.medium_term_adr, float)
        assert isinstance(result.divergence, ADRDivergence)

    def test_all_advancing_adr_above_100(
        self,
        adr_service: AdvancingDecliningRatioService,
        all_advancing_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that all advancing stocks produces ADR > 100."""
        result = adr_service.calculate(all_advancing_prices)

        # When all stocks advance, ADR should be very high (200 cap)
        assert result.short_term_adr >= 100.0
        assert result.medium_term_adr >= 100.0

    def test_all_declining_adr_below_100(
        self,
        adr_service: AdvancingDecliningRatioService,
        all_declining_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that all declining stocks produces ADR < 100."""
        result = adr_service.calculate(all_declining_prices)

        # When all stocks decline, ADR should be very low
        assert result.short_term_adr < 100.0
        assert result.medium_term_adr < 100.0

    def test_mixed_adr_around_150(
        self,
        adr_service: AdvancingDecliningRatioService,
        mixed_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test ADR with 6 advancing, 4 declining stocks."""
        result = adr_service.calculate(mixed_prices)

        # 6 advancing / 4 declining = 1.5 * 100 = 150
        assert 140.0 <= result.short_term_adr <= 160.0
        assert 140.0 <= result.medium_term_adr <= 160.0

    def test_empty_prices_returns_neutral(
        self,
        adr_service: AdvancingDecliningRatioService,
    ) -> None:
        """Test that empty prices returns neutral ADR."""
        result = adr_service.calculate({})

        assert result.short_term_adr == 100.0
        assert result.medium_term_adr == 100.0
        assert result.divergence == ADRDivergence.NEUTRAL

    def test_divergence_bullish(
        self,
        adr_service: AdvancingDecliningRatioService,
    ) -> None:
        """Test bullish divergence when short-term > medium-term + threshold."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

        prices = {}
        for i in range(10):
            symbol = f"STOCK{i}"
            # First 20 days declining, last 10 days advancing strongly
            close = [100.0 - j * 0.3 for j in range(20)]
            close.extend([close[-1] + j * 1.0 for j in range(10)])
            prices[symbol] = pd.DataFrame({"close": close}, index=dates)

        result = adr_service.calculate(prices, divergence_threshold=10.0)

        # Short-term should be higher (recent advance)
        assert result.short_term_adr > result.medium_term_adr
        assert result.divergence == ADRDivergence.BULLISH

    def test_divergence_bearish(
        self,
        adr_service: AdvancingDecliningRatioService,
    ) -> None:
        """Test bearish divergence when short-term < medium-term - threshold."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

        prices = {}
        for i in range(10):
            symbol = f"STOCK{i}"
            # First 20 days advancing, last 10 days declining strongly
            close = [100.0 + j * 0.3 for j in range(20)]
            close.extend([close[-1] - j * 1.0 for j in range(10)])
            prices[symbol] = pd.DataFrame({"close": close}, index=dates)

        result = adr_service.calculate(prices, divergence_threshold=10.0)

        # Short-term should be lower (recent decline)
        assert result.short_term_adr < result.medium_term_adr
        assert result.divergence == ADRDivergence.BEARISH

    def test_custom_periods(
        self,
        adr_service: AdvancingDecliningRatioService,
        mixed_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test custom short and medium periods."""
        result = adr_service.calculate(
            mixed_prices,
            short_period=3,
            medium_period=10,
        )

        assert isinstance(result, ADRCalculationResult)
        # ADR should still be calculated correctly
        assert result.short_term_adr > 0
        assert result.medium_term_adr > 0

    def test_daily_counts_populated(
        self,
        adr_service: AdvancingDecliningRatioService,
        mixed_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that daily advancing/declining counts are populated."""
        result = adr_service.calculate(mixed_prices)

        assert len(result.daily_advancing) > 0
        assert len(result.daily_declining) > 0
        assert len(result.daily_advancing) == len(result.daily_declining)

    def test_handles_close_column_case_insensitive(
        self,
        adr_service: AdvancingDecliningRatioService,
    ) -> None:
        """Test that both 'close' and 'Close' column names work."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

        # Use 'Close' (capitalized) column name
        prices = {
            "STOCK1": pd.DataFrame(
                {"Close": [100.0 + j * 0.5 for j in range(30)]}, index=dates
            ),
            "STOCK2": pd.DataFrame(
                {"Close": [100.0 - j * 0.5 for j in range(30)]}, index=dates
            ),
        }

        result = adr_service.calculate(prices)

        # Should calculate without error
        assert result.short_term_adr > 0
        assert result.medium_term_adr > 0

    def test_adr_no_declining_returns_200(
        self,
        adr_service: AdvancingDecliningRatioService,
    ) -> None:
        """Test that 0 declining stocks returns ADR of 200."""
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")

        # All stocks advancing
        prices = {
            "STOCK1": pd.DataFrame(
                {"close": [100.0 + j for j in range(10)]}, index=dates
            ),
        }

        result = adr_service.calculate(prices, short_period=5, medium_period=9)

        # With no declining, ADR should be capped at 200
        assert result.short_term_adr == 200.0
