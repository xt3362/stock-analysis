"""Tests for MarketRegimeAnalyzer."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# NOTE: pandas type stubs are incomplete

from typing import Dict

import numpy as np
import pandas as pd
import pytest

from src.domain.models.market_regime import (
    EnvironmentCode,
    MarketRegime,
    MarketRegimeConfig,
    Sentiment,
    TrendDirection,
    VolatilityLevel,
)
from src.domain.services.analysis.market_regime_analyzer import MarketRegimeAnalyzer


@pytest.fixture
def analyzer() -> MarketRegimeAnalyzer:
    """Create MarketRegimeAnalyzer instance."""
    return MarketRegimeAnalyzer()


@pytest.fixture
def uptrend_ohlcv() -> pd.DataFrame:
    """Create OHLCV data for uptrend scenario."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    # Strong uptrend
    base_price = 100.0
    returns = np.random.normal(0.003, 0.015, 100)  # Positive bias, low volatility
    close_prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.uniform(-0.005, 0.005, 100)),
            "high": close_prices * (1 + np.random.uniform(0, 0.01, 100)),
            "low": close_prices * (1 - np.random.uniform(0, 0.01, 100)),
            "close": close_prices,
            "volume": np.random.randint(1000000, 5000000, 100),
        },
        index=dates,
    )


@pytest.fixture
def downtrend_ohlcv() -> pd.DataFrame:
    """Create OHLCV data for downtrend scenario."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    # Strong downtrend
    base_price = 100.0
    returns = np.random.normal(-0.003, 0.015, 100)  # Negative bias
    close_prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.uniform(-0.005, 0.005, 100)),
            "high": close_prices * (1 + np.random.uniform(0, 0.01, 100)),
            "low": close_prices * (1 - np.random.uniform(0, 0.01, 100)),
            "close": close_prices,
            "volume": np.random.randint(1000000, 5000000, 100),
        },
        index=dates,
    )


@pytest.fixture
def sideways_ohlcv() -> pd.DataFrame:
    """Create OHLCV data for sideways/range-bound scenario."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

    # Sideways movement - flat prices with tiny noise
    base_price = 100.0
    # Almost flat prices - vary only by +/- 0.01%
    close_prices = np.array([base_price + 0.001 * (i % 5 - 2) for i in range(100)])

    return pd.DataFrame(
        {
            "open": close_prices * 0.999,
            "high": close_prices * 1.002,
            "low": close_prices * 0.998,
            "close": close_prices,
            "volume": [2000000] * 100,
        },
        index=dates,
    )


@pytest.fixture
def high_volatility_ohlcv() -> pd.DataFrame:
    """Create OHLCV data with high volatility."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    # High volatility
    base_price = 100.0
    returns = np.random.normal(0.0, 0.04, 100)  # High std dev
    close_prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.uniform(-0.02, 0.02, 100)),
            "high": close_prices * (1 + np.random.uniform(0, 0.04, 100)),
            "low": close_prices * (1 - np.random.uniform(0, 0.04, 100)),
            "close": close_prices,
            "volume": np.random.randint(1000000, 5000000, 100),
        },
        index=dates,
    )


@pytest.fixture
def sample_universe_prices() -> Dict[str, pd.DataFrame]:
    """Create sample universe prices for ADR calculation."""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    np.random.seed(42)

    prices = {}
    # 6 advancing stocks
    for i in range(6):
        symbol = f"ADV{i}"
        close = [100.0 + j * 0.5 for j in range(30)]
        prices[symbol] = pd.DataFrame({"close": close}, index=dates)

    # 4 declining stocks
    for i in range(4):
        symbol = f"DEC{i}"
        close = [100.0 - j * 0.3 for j in range(30)]
        prices[symbol] = pd.DataFrame({"close": close}, index=dates)

    return prices


class TestMarketRegimeAnalyzer:
    """Tests for MarketRegimeAnalyzer."""

    def test_analyze_returns_market_regime(
        self,
        analyzer: MarketRegimeAnalyzer,
        uptrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that analyze returns MarketRegime object."""
        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert isinstance(result, MarketRegime)
        assert result.analysis_date is not None
        assert result.trend_analysis is not None
        assert result.volatility_analysis is not None
        assert result.sentiment_analysis is not None
        assert result.environment_code is not None
        assert result.risk_assessment is not None
        assert result.market_breadth is not None

    def test_uptrend_detection(
        self,
        analyzer: MarketRegimeAnalyzer,
        uptrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that uptrend is correctly detected."""
        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert result.trend_analysis.trend_direction == TrendDirection.UPTREND

    def test_downtrend_detection(
        self,
        analyzer: MarketRegimeAnalyzer,
        downtrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that downtrend is correctly detected."""
        result = analyzer.analyze(
            nikkei_df=downtrend_ohlcv,
            topix_df=downtrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert result.trend_analysis.trend_direction == TrendDirection.DOWNTREND

    def test_sideways_detection(
        self,
        analyzer: MarketRegimeAnalyzer,
        sideways_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that sideways market is correctly detected."""
        result = analyzer.analyze(
            nikkei_df=sideways_ohlcv,
            topix_df=sideways_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert result.trend_analysis.trend_direction == TrendDirection.SIDEWAYS

    def test_risk_score_uptrend_low(
        self,
        analyzer: MarketRegimeAnalyzer,
        uptrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that uptrend with normal volatility has low risk score."""
        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        # Uptrend should have lower risk score
        assert result.risk_assessment.risk_score <= 50

    def test_risk_score_downtrend_higher(
        self,
        analyzer: MarketRegimeAnalyzer,
        downtrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that downtrend has higher risk score."""
        result = analyzer.analyze(
            nikkei_df=downtrend_ohlcv,
            topix_df=downtrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        # Downtrend adds 40 points to risk score
        assert result.risk_assessment.risk_score >= 40

    def test_volatility_analysis(
        self,
        analyzer: MarketRegimeAnalyzer,
        high_volatility_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test volatility analysis."""
        result = analyzer.analyze(
            nikkei_df=high_volatility_ohlcv,
            topix_df=high_volatility_ohlcv,
            universe_prices=sample_universe_prices,
        )

        # High volatility OHLCV should result in elevated/high volatility
        assert result.volatility_analysis.volatility_level in [
            VolatilityLevel.ELEVATED,
            VolatilityLevel.HIGH,
        ]

    def test_environment_classification_stable_uptrend(
        self,
        analyzer: MarketRegimeAnalyzer,
        uptrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test environment classification for stable uptrend."""
        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        # Should be some form of uptrend environment
        assert result.environment_code in [
            EnvironmentCode.STABLE_UPTREND,
            EnvironmentCode.VOLATILE_UPTREND,
            EnvironmentCode.OVERHEATED_UPTREND,
        ]

    def test_sentiment_positive_when_both_uptrend(
        self,
        analyzer: MarketRegimeAnalyzer,
        uptrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test sentiment is positive when both indices are in uptrend."""
        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert result.sentiment_analysis.sentiment == Sentiment.POSITIVE

    def test_sentiment_negative_when_both_downtrend(
        self,
        analyzer: MarketRegimeAnalyzer,
        downtrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test sentiment is negative when both indices are in downtrend."""
        result = analyzer.analyze(
            nikkei_df=downtrend_ohlcv,
            topix_df=downtrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert result.sentiment_analysis.sentiment == Sentiment.NEGATIVE

    def test_market_breadth_populated(
        self,
        analyzer: MarketRegimeAnalyzer,
        uptrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test that market breadth is correctly populated."""
        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert "short_term" in result.market_breadth.advancing_declining_ratios
        assert "medium_term" in result.market_breadth.advancing_declining_ratios
        assert result.market_breadth.advancing_declining_ratios["short_term"] > 0
        assert result.market_breadth.advancing_declining_ratios["medium_term"] > 0

    def test_empty_universe_prices_handled(
        self,
        analyzer: MarketRegimeAnalyzer,
        uptrend_ohlcv: pd.DataFrame,
    ) -> None:
        """Test that empty universe prices are handled gracefully."""
        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices={},
        )

        assert isinstance(result, MarketRegime)
        # ADR should default to 100 (neutral)
        assert result.market_breadth.advancing_declining_ratios["short_term"] == 100.0

    def test_custom_config(
        self,
        uptrend_ohlcv: pd.DataFrame,
        sample_universe_prices: Dict[str, pd.DataFrame],
    ) -> None:
        """Test analyzer with custom configuration."""
        config = MarketRegimeConfig(
            adx_trending_threshold=30.0,
            atr_low_threshold=1.0,
        )
        analyzer = MarketRegimeAnalyzer(config=config)

        result = analyzer.analyze(
            nikkei_df=uptrend_ohlcv,
            topix_df=uptrend_ohlcv,
            universe_prices=sample_universe_prices,
        )

        assert isinstance(result, MarketRegime)


class TestRiskScoreCalculation:
    """Tests for risk score calculation logic."""

    def test_risk_score_components(self) -> None:
        """Test that risk score correctly combines components."""
        analyzer = MarketRegimeAnalyzer()

        # Create specific scenario for predictable risk score
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

        # Downtrend with high volatility
        base_price = 100.0
        returns = [-0.005] * 100  # Consistent decline
        close_prices = [base_price]
        for r in returns[:-1]:
            close_prices.append(close_prices[-1] * (1 + r))
        close_prices = np.array(close_prices)

        # Add high volatility
        high_prices = close_prices * 1.05
        low_prices = close_prices * 0.95

        ohlcv = pd.DataFrame(
            {
                "open": close_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": [1000000] * 100,
            },
            index=dates,
        )

        # Low ADR (panic-like)
        universe_prices = {}
        for i in range(10):
            symbol = f"STOCK{i}"
            # All declining
            close = [100.0 - j * 0.5 for j in range(30)]
            prices_dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
            universe_prices[symbol] = pd.DataFrame({"close": close}, index=prices_dates)

        result = analyzer.analyze(
            nikkei_df=ohlcv,
            topix_df=ohlcv,
            universe_prices=universe_prices,
        )

        # Should have high risk score
        # DOWNTREND: +40, some volatility: +10-30, low ADR: +15-30
        assert result.risk_assessment.risk_score >= 50
