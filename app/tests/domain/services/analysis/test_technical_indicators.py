"""Tests for TechnicalIndicatorService."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportGeneralTypeIssues=false
# NOTE: pandas type stubs are incomplete, suppressing related errors

import numpy as np
import pandas as pd
import pytest

from src.domain.services.analysis.technical_indicators import (
    IndicatorCalculationResult,
    TechnicalIndicatorService,
)


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Create sample OHLCV data for testing (100 days)."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    # Generate realistic price data with trend
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, 100)
    close_prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
            "high": close_prices * (1 + np.random.uniform(0, 0.02, 100)),
            "low": close_prices * (1 - np.random.uniform(0, 0.02, 100)),
            "close": close_prices,
            "volume": np.random.randint(1000000, 5000000, 100),
        },
        index=dates,
    )


@pytest.fixture
def small_ohlcv_df() -> pd.DataFrame:
    """Create small OHLCV data for testing (10 days)."""
    dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0 + i for i in range(10)],
            "high": [105.0 + i for i in range(10)],
            "low": [95.0 + i for i in range(10)],
            "close": [102.0 + i for i in range(10)],
            "volume": [1000000 + i * 10000 for i in range(10)],
        },
        index=dates,
    )


class TestTechnicalIndicatorService:
    """Tests for TechnicalIndicatorService."""

    def test_calculate_all_returns_result_object(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Test that calculate_all returns IndicatorCalculationResult."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(sample_ohlcv_df)

        assert isinstance(result, IndicatorCalculationResult)
        assert isinstance(result.data, pd.DataFrame)
        assert isinstance(result.calculated_indicators, list)
        assert isinstance(result.failed_indicators, dict)

    def test_calculate_all_adds_indicator_columns(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Test that calculate_all adds expected indicator columns."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(sample_ohlcv_df)

        expected_indicators = [
            "sma_5",
            "sma_25",
            "sma_75",
            "ema_12",
            "ema_26",
            "rsi_14",
            "stoch_k",
            "stoch_d",
            "macd",
            "macd_signal",
            "macd_histogram",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "bb_width",
            "atr_14",
            "realized_volatility",
            "adx_14",
            "sar",
            "obv",
            "volume_ma_20",
            "volume_ratio",
        ]

        for indicator in expected_indicators:
            assert indicator in result.data.columns, f"Missing indicator: {indicator}"

    def test_calculate_all_preserves_original_columns(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Test that calculate_all preserves original OHLCV columns."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(sample_ohlcv_df)

        for col in ["open", "high", "low", "close", "volume"]:
            assert col in result.data.columns
            pd.testing.assert_series_equal(
                result.data[col], sample_ohlcv_df[col], check_names=False
            )

    def test_sma_calculation_correct(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Test SMA calculation is mathematically correct."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(sample_ohlcv_df)

        # Manually calculate SMA5 for verification
        expected_sma5 = sample_ohlcv_df["close"].rolling(5).mean()
        pd.testing.assert_series_equal(
            result.data["sma_5"], expected_sma5, check_names=False
        )

    def test_insufficient_data_returns_nan(self, small_ohlcv_df: pd.DataFrame) -> None:
        """Test that insufficient data produces NaN values."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(small_ohlcv_df)

        # SMA75 should be all NaN with only 10 days of data
        assert result.data["sma_75"].isna().all()

        # SMA5 should have NaN for first 4 rows
        assert result.data["sma_5"].isna().sum() == 4
        assert result.data["sma_5"].notna().sum() == 6

    def test_get_required_lookback_all(self) -> None:
        """Test get_required_lookback returns max for all indicators."""
        service = TechnicalIndicatorService()
        lookback = service.get_required_lookback()

        # SMA75 requires the most days
        assert lookback == 75

    def test_get_required_lookback_subset(self) -> None:
        """Test get_required_lookback for specific indicators."""
        service = TechnicalIndicatorService()

        lookback = service.get_required_lookback(["sma_5", "rsi_14"])
        assert lookback == 15  # RSI needs 15

        lookback = service.get_required_lookback(["sma_5"])
        assert lookback == 5

    def test_volume_indicators_calculated(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Test volume indicators are calculated."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(sample_ohlcv_df)

        # OBV should be calculated
        assert "obv" in result.data.columns
        assert result.data["obv"].notna().any()

        # Volume MA should be calculated
        assert "volume_ma_20" in result.data.columns

        # Volume ratio should be calculated
        assert "volume_ratio" in result.data.columns

    def test_bollinger_bands_calculated(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Test Bollinger Bands are calculated correctly."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(sample_ohlcv_df)

        # Check all BB columns exist
        assert "bb_upper" in result.data.columns
        assert "bb_middle" in result.data.columns
        assert "bb_lower" in result.data.columns
        assert "bb_width" in result.data.columns

        # Upper should be > middle > lower
        valid_idx = result.data["bb_middle"].notna()
        assert (
            result.data.loc[valid_idx, "bb_upper"]
            >= result.data.loc[valid_idx, "bb_middle"]
        ).all()
        assert (
            result.data.loc[valid_idx, "bb_middle"]
            >= result.data.loc[valid_idx, "bb_lower"]
        ).all()

    def test_empty_dataframe_handled(self) -> None:
        """Test that empty DataFrame is handled gracefully."""
        service = TechnicalIndicatorService()
        empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        result = service.calculate_all(empty_df)

        # Should return result without crashing
        assert isinstance(result, IndicatorCalculationResult)
        assert len(result.data) == 0

    def test_calculated_indicators_list_populated(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Test that calculated_indicators list is populated."""
        service = TechnicalIndicatorService()
        result = service.calculate_all(sample_ohlcv_df)

        assert len(result.calculated_indicators) > 0
        assert "sma_5" in result.calculated_indicators
        assert "rsi_14" in result.calculated_indicators
