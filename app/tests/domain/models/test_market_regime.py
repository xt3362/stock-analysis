"""Tests for MarketRegime domain models."""

from datetime import date

import pytest

from src.domain.models.market_regime import (
    ADRDivergence,
    EnvironmentCode,
    MarketBreadth,
    MarketRegime,
    MarketRegimeConfig,
    RiskAssessment,
    RiskLevel,
    Sentiment,
    SentimentAnalysis,
    TrendAnalysis,
    TrendDirection,
    TrendType,
    VolatilityAnalysis,
    VolatilityLevel,
)


class TestRiskAssessment:
    """Tests for RiskAssessment."""

    def test_from_score_low(self) -> None:
        """Test LOW risk level for scores 0-25."""
        for score in [0, 10, 20, 25]:
            result = RiskAssessment.from_score(score)
            assert result.risk_level == RiskLevel.LOW
            assert result.risk_score == score

    def test_from_score_medium(self) -> None:
        """Test MEDIUM risk level for scores 26-50."""
        for score in [26, 35, 45, 50]:
            result = RiskAssessment.from_score(score)
            assert result.risk_level == RiskLevel.MEDIUM
            assert result.risk_score == score

    def test_from_score_high(self) -> None:
        """Test HIGH risk level for scores 51-75."""
        for score in [51, 60, 70, 75]:
            result = RiskAssessment.from_score(score)
            assert result.risk_level == RiskLevel.HIGH
            assert result.risk_score == score

    def test_from_score_extreme(self) -> None:
        """Test EXTREME risk level for scores 76-100."""
        for score in [76, 85, 95, 100]:
            result = RiskAssessment.from_score(score)
            assert result.risk_level == RiskLevel.EXTREME
            assert result.risk_score == score

    def test_from_score_clamps_negative(self) -> None:
        """Test that negative scores are clamped to 0."""
        result = RiskAssessment.from_score(-10)
        assert result.risk_score == 0
        assert result.risk_level == RiskLevel.LOW

    def test_from_score_clamps_over_100(self) -> None:
        """Test that scores over 100 are clamped to 100."""
        result = RiskAssessment.from_score(150)
        assert result.risk_score == 100
        assert result.risk_level == RiskLevel.EXTREME


class TestMarketRegime:
    """Tests for MarketRegime."""

    @pytest.fixture
    def stable_uptrend_regime(self) -> MarketRegime:
        """Create a stable uptrend market regime."""
        return MarketRegime(
            analysis_date=date(2024, 1, 15),
            trend_analysis=TrendAnalysis(
                trend_type=TrendType.TRENDING,
                trend_direction=TrendDirection.UPTREND,
                adx_value=30.0,
                adx_interpretation="Strong Trend",
            ),
            volatility_analysis=VolatilityAnalysis(
                volatility_level=VolatilityLevel.NORMAL,
                atr_percent=1.5,
                bollinger_band_width=8.0,
                volatility_consensus=True,
            ),
            sentiment_analysis=SentimentAnalysis(
                sentiment=Sentiment.POSITIVE,
                nikkei_trend=TrendDirection.UPTREND,
                topix_trend=TrendDirection.UPTREND,
            ),
            environment_code=EnvironmentCode.STABLE_UPTREND,
            risk_assessment=RiskAssessment.from_score(10),
            market_breadth=MarketBreadth(
                advancing_declining_ratios={"short_term": 120.0, "medium_term": 110.0},
                adr_divergence=ADRDivergence.BULLISH,
            ),
        )

    @pytest.fixture
    def panic_sell_regime(self) -> MarketRegime:
        """Create a panic sell market regime."""
        return MarketRegime(
            analysis_date=date(2024, 1, 15),
            trend_analysis=TrendAnalysis(
                trend_type=TrendType.TRENDING,
                trend_direction=TrendDirection.DOWNTREND,
                adx_value=45.0,
                adx_interpretation="Strong Trend",
            ),
            volatility_analysis=VolatilityAnalysis(
                volatility_level=VolatilityLevel.HIGH,
                atr_percent=4.5,
                bollinger_band_width=15.0,
                volatility_consensus=True,
            ),
            sentiment_analysis=SentimentAnalysis(
                sentiment=Sentiment.NEGATIVE,
                nikkei_trend=TrendDirection.DOWNTREND,
                topix_trend=TrendDirection.DOWNTREND,
            ),
            environment_code=EnvironmentCode.PANIC_SELL,
            risk_assessment=RiskAssessment.from_score(95),
            market_breadth=MarketBreadth(
                advancing_declining_ratios={"short_term": 50.0, "medium_term": 70.0},
                adr_divergence=ADRDivergence.BEARISH,
            ),
        )

    def test_is_tradeable_stable_uptrend(
        self, stable_uptrend_regime: MarketRegime
    ) -> None:
        """Test that stable uptrend is tradeable."""
        assert stable_uptrend_regime.is_tradeable is True

    def test_is_tradeable_panic_sell(self, panic_sell_regime: MarketRegime) -> None:
        """Test that panic sell is not tradeable."""
        assert panic_sell_regime.is_tradeable is False

    def test_is_tradeable_strong_downtrend(self) -> None:
        """Test that strong downtrend is not tradeable."""
        regime = MarketRegime(
            analysis_date=date(2024, 1, 15),
            trend_analysis=TrendAnalysis(
                trend_type=TrendType.TRENDING,
                trend_direction=TrendDirection.DOWNTREND,
                adx_value=35.0,
                adx_interpretation="Strong Trend",
            ),
            volatility_analysis=VolatilityAnalysis(
                volatility_level=VolatilityLevel.NORMAL,
                atr_percent=1.8,
                bollinger_band_width=9.0,
                volatility_consensus=True,
            ),
            sentiment_analysis=SentimentAnalysis(
                sentiment=Sentiment.NEGATIVE,
                nikkei_trend=TrendDirection.DOWNTREND,
                topix_trend=TrendDirection.DOWNTREND,
            ),
            environment_code=EnvironmentCode.STRONG_DOWNTREND,
            risk_assessment=RiskAssessment.from_score(70),
            market_breadth=MarketBreadth(
                advancing_declining_ratios={"short_term": 80.0, "medium_term": 90.0},
                adr_divergence=ADRDivergence.BEARISH,
            ),
        )
        assert regime.is_tradeable is False

    def test_is_tradeable_extreme_risk(self) -> None:
        """Test that extreme risk (even in uptrend) is not tradeable."""
        regime = MarketRegime(
            analysis_date=date(2024, 1, 15),
            trend_analysis=TrendAnalysis(
                trend_type=TrendType.TRENDING,
                trend_direction=TrendDirection.UPTREND,
                adx_value=30.0,
                adx_interpretation="Strong Trend",
            ),
            volatility_analysis=VolatilityAnalysis(
                volatility_level=VolatilityLevel.HIGH,
                atr_percent=4.0,
                bollinger_band_width=14.0,
                volatility_consensus=True,
            ),
            sentiment_analysis=SentimentAnalysis(
                sentiment=Sentiment.NEUTRAL,
                nikkei_trend=TrendDirection.UPTREND,
                topix_trend=TrendDirection.SIDEWAYS,
            ),
            environment_code=EnvironmentCode.VOLATILE_UPTREND,
            risk_assessment=RiskAssessment.from_score(80),  # EXTREME
            market_breadth=MarketBreadth(
                advancing_declining_ratios={"short_term": 110.0, "medium_term": 100.0},
                adr_divergence=ADRDivergence.NEUTRAL,
            ),
        )
        assert regime.is_tradeable is False


class TestMarketRegimeConfig:
    """Tests for MarketRegimeConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = MarketRegimeConfig()

        # Trend defaults
        assert config.adx_trending_threshold == 25.0
        assert config.adx_ranging_threshold == 20.0
        assert config.sma_period == 25
        assert config.sma_slope_uptrend == 0.06
        assert config.sma_slope_downtrend == -0.06

        # Volatility defaults
        assert config.atr_period == 14
        assert config.atr_low_threshold == 0.8
        assert config.atr_normal_threshold == 2.0
        assert config.atr_elevated_threshold == 3.0

        # ADR defaults
        assert config.adr_short_period == 5
        assert config.adr_medium_period == 25
        assert config.adr_short_panic == 60.0
        assert config.adr_overbought == 130.0

        # Risk score defaults
        assert config.risk_trend_weight == 40
        assert config.risk_volatility_weight == 30
        assert config.risk_adr_weight == 30
        assert config.risk_divergence_adjustment == 5

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = MarketRegimeConfig(
            adx_trending_threshold=30.0,
            atr_low_threshold=1.0,
        )

        assert config.adx_trending_threshold == 30.0
        assert config.atr_low_threshold == 1.0
        # Other values should still be defaults
        assert config.adx_ranging_threshold == 20.0


class TestEnums:
    """Tests for enum values."""

    def test_trend_type_values(self) -> None:
        """Test TrendType enum values."""
        assert TrendType.TRENDING.value == "trending"
        assert TrendType.RANGING.value == "ranging"
        assert TrendType.NEUTRAL.value == "neutral"

    def test_trend_direction_values(self) -> None:
        """Test TrendDirection enum values."""
        assert TrendDirection.UPTREND.value == "uptrend"
        assert TrendDirection.DOWNTREND.value == "downtrend"
        assert TrendDirection.SIDEWAYS.value == "sideways"

    def test_volatility_level_values(self) -> None:
        """Test VolatilityLevel enum values."""
        assert VolatilityLevel.LOW.value == "low"
        assert VolatilityLevel.NORMAL.value == "normal"
        assert VolatilityLevel.ELEVATED.value == "elevated"
        assert VolatilityLevel.HIGH.value == "high"

    def test_environment_code_values(self) -> None:
        """Test EnvironmentCode enum values (8 patterns)."""
        assert len(EnvironmentCode) == 8
        assert EnvironmentCode.STABLE_UPTREND.value == "stable_uptrend"
        assert EnvironmentCode.OVERHEATED_UPTREND.value == "overheated_uptrend"
        assert EnvironmentCode.VOLATILE_UPTREND.value == "volatile_uptrend"
        assert EnvironmentCode.QUIET_RANGE.value == "quiet_range"
        assert EnvironmentCode.VOLATILE_RANGE.value == "volatile_range"
        assert EnvironmentCode.CORRECTION.value == "correction"
        assert EnvironmentCode.STRONG_DOWNTREND.value == "strong_downtrend"
        assert EnvironmentCode.PANIC_SELL.value == "panic_sell"
