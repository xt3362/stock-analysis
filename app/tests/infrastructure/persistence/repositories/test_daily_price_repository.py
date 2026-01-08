"""Tests for PostgresDailyPriceRepository."""

# pyright: reportUnknownMemberType=false, reportGeneralTypeIssues=false
# pyright: reportArgumentType=false
# NOTE: MagicMock typing issues in tests

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd

from src.infrastructure.persistence.repositories import PostgresDailyPriceRepository


class TestGetHistoricalForIndicatorCalculation:
    """Test cases for get_historical_for_indicator_calculation."""

    def test_returns_lookback_days_before_start_date(self) -> None:
        """Test that it returns the specified number of days before start date."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDailyPriceRepository(mock_session)

        # Create mock results (5 days before Jan 8)
        mock_results = []
        for i in range(5):
            mock_dp = MagicMock()
            mock_dp.date = date(2024, 1, 7 - i)  # 7, 6, 5, 4, 3 (desc order)
            mock_results.append(mock_dp)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_results

        # Act
        result = repo.get_historical_for_indicator_calculation(
            ticker_id=1,
            new_data_start_date=date(2024, 1, 8),
            lookback_days=5,
        )

        # Assert
        assert len(result) == 5
        # Should be reversed to ascending order: 3, 4, 5, 6, 7
        assert result[0].date == date(2024, 1, 3)
        assert result[-1].date == date(2024, 1, 7)

    def test_returns_empty_when_no_historical_data(self) -> None:
        """Test that it returns empty list when no data exists before start date."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDailyPriceRepository(mock_session)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # Act
        result = repo.get_historical_for_indicator_calculation(
            ticker_id=1,
            new_data_start_date=date(2024, 1, 5),
            lookback_days=10,
        )

        # Assert
        assert len(result) == 0

    def test_returns_less_than_lookback_when_insufficient_data(self) -> None:
        """Test that it returns available data when less than lookback days exist."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDailyPriceRepository(mock_session)

        # Only 3 days available
        mock_results = []
        for i in range(3):
            mock_dp = MagicMock()
            mock_dp.date = date(2024, 1, 3 - i)
            mock_results.append(mock_dp)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_results

        # Act
        result = repo.get_historical_for_indicator_calculation(
            ticker_id=1,
            new_data_start_date=date(2024, 1, 10),
            lookback_days=10,
        )

        # Assert
        assert len(result) == 3

    def test_orders_by_date_ascending(self) -> None:
        """Test that results are ordered by date ascending."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDailyPriceRepository(mock_session)

        # Mock returns data in desc order (as DB would)
        mock_results = []
        for day in [8, 5, 4, 2, 1]:  # desc order
            mock_dp = MagicMock()
            mock_dp.date = date(2024, 1, day)
            mock_results.append(mock_dp)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_results

        # Act
        result = repo.get_historical_for_indicator_calculation(
            ticker_id=1,
            new_data_start_date=date(2024, 1, 10),
            lookback_days=10,
        )

        # Assert - should be ascending order after reversal
        dates = [dp.date for dp in result]
        assert dates == sorted(dates)


class TestDailyPricesToDataframe:
    """Test cases for daily_prices_to_dataframe."""

    def test_converts_to_correct_format(self) -> None:
        """Test that DailyPrice list is converted to correct DataFrame format."""
        mock_session = MagicMock()
        repo = PostgresDailyPriceRepository(mock_session)

        # Create mock daily prices
        dp1 = MagicMock()
        dp1.date = date(2024, 1, 1)
        dp1.open = Decimal("100.50")
        dp1.high = Decimal("110.25")
        dp1.low = Decimal("95.75")
        dp1.close = Decimal("105.00")
        dp1.volume = 1000
        dp1.adj_close = Decimal("104.50")

        dp2 = MagicMock()
        dp2.date = date(2024, 1, 2)
        dp2.open = Decimal("105.00")
        dp2.high = Decimal("115.00")
        dp2.low = Decimal("100.00")
        dp2.close = Decimal("110.00")
        dp2.volume = 1500
        dp2.adj_close = Decimal("109.50")

        daily_prices = [dp1, dp2]

        # Act
        df = repo.daily_prices_to_dataframe(daily_prices)

        # Assert columns
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns
        assert "adj_close" in df.columns

        # Check values
        assert len(df) == 2
        assert df["open"].iloc[0] == 100.50
        assert df["close"].iloc[1] == 110.00
        assert df["volume"].iloc[0] == 1000

        # Check index
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_handles_empty_list(self) -> None:
        """Test that empty list returns empty DataFrame."""
        mock_session = MagicMock()
        repo = PostgresDailyPriceRepository(mock_session)

        # Act
        df = repo.daily_prices_to_dataframe([])

        # Assert
        assert len(df) == 0
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_handles_missing_adj_close(self) -> None:
        """Test that missing adj_close is handled correctly."""
        mock_session = MagicMock()
        repo = PostgresDailyPriceRepository(mock_session)

        dp = MagicMock()
        dp.date = date(2024, 1, 1)
        dp.open = Decimal("100.00")
        dp.high = Decimal("110.00")
        dp.low = Decimal("95.00")
        dp.close = Decimal("105.00")
        dp.volume = 1000
        dp.adj_close = None

        # Act
        df = repo.daily_prices_to_dataframe([dp])

        # Assert
        assert "adj_close" not in df.columns
        assert len(df) == 1
