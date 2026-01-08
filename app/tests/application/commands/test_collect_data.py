"""Tests for CollectDataHandler."""

# pyright: reportUnusedImport=false

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest  # noqa: F401

from src.application.commands.collect_data import (
    CollectDataHandler,
    FetchStockDataCommand,
)
from src.shared.exceptions import StockDataFetchError


class TestFetchStockDataCommand:
    """Test cases for FetchStockDataCommand."""

    def test_create_with_period(self) -> None:
        """Test creating command with period."""
        command = FetchStockDataCommand(
            symbols=["AAPL", "MSFT"],
            period="1mo",
        )
        assert command.symbols == ["AAPL", "MSFT"]
        assert command.period == "1mo"
        assert command.start_date is None
        assert command.end_date is None

    def test_create_with_dates(self) -> None:
        """Test creating command with date range."""
        command = FetchStockDataCommand(
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert command.symbols == ["AAPL"]
        assert command.start_date == date(2024, 1, 1)
        assert command.end_date == date(2024, 12, 31)
        assert command.period is None


class TestCollectDataHandler:
    """Test cases for CollectDataHandler."""

    def test_handle_single_symbol_success(self) -> None:
        """Test fetching single symbol successfully."""
        # Arrange
        mock_data_source = MagicMock()
        mock_df = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [110.0, 111.0],
                "low": [95.0, 96.0],
                "close": [105.0, 106.0],
                "volume": [1000, 1100],
            },
            index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"]),
        )
        mock_data_source.fetch_multiple_daily_prices.return_value = {"7203.T": mock_df}

        handler = CollectDataHandler(data_source=mock_data_source)
        command = FetchStockDataCommand(
            symbols=["7203.T"],
            period="1mo",
        )

        # Act
        result = handler.handle(command)

        # Assert
        assert result.success_count == 1
        assert result.error_count == 0
        assert "7203.T" in result.data
        assert len(result.data["7203.T"]) == 2

    def test_handle_multiple_symbols_success(self) -> None:
        """Test fetching multiple symbols successfully."""
        # Arrange
        mock_data_source = MagicMock()
        mock_df1 = pd.DataFrame(
            {
                "open": [100.0],
                "close": [105.0],
                "high": [110.0],
                "low": [95.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        mock_df2 = pd.DataFrame(
            {
                "open": [200.0],
                "close": [205.0],
                "high": [210.0],
                "low": [195.0],
                "volume": [2000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        mock_data_source.fetch_multiple_daily_prices.return_value = {
            "AAPL": mock_df1,
            "MSFT": mock_df2,
        }

        handler = CollectDataHandler(data_source=mock_data_source)
        command = FetchStockDataCommand(
            symbols=["AAPL", "MSFT"],
            period="1mo",
        )

        # Act
        result = handler.handle(command)

        # Assert
        assert result.success_count == 2
        assert result.error_count == 0
        assert "AAPL" in result.data
        assert "MSFT" in result.data

    def test_handle_partial_failure(self) -> None:
        """Test handling partial failures in bulk fetch."""
        # Arrange
        mock_data_source = MagicMock()
        mock_df = pd.DataFrame(
            {
                "open": [100.0],
                "close": [105.0],
                "high": [110.0],
                "low": [95.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        # Only return data for AAPL, not INVALID
        mock_data_source.fetch_multiple_daily_prices.return_value = {"AAPL": mock_df}

        handler = CollectDataHandler(data_source=mock_data_source)
        command = FetchStockDataCommand(
            symbols=["AAPL", "INVALID"],
            period="1mo",
        )

        # Act
        result = handler.handle(command)

        # Assert
        assert result.success_count == 1
        assert result.error_count == 1
        assert "AAPL" in result.data
        assert "INVALID" in result.errors

    def test_handle_bulk_fetch_failure_falls_back(self) -> None:
        """Test fallback to individual fetching on bulk failure."""
        # Arrange
        mock_data_source = MagicMock()
        mock_df = pd.DataFrame(
            {
                "open": [100.0],
                "close": [105.0],
                "high": [110.0],
                "low": [95.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        # Bulk fetch fails
        mock_data_source.fetch_multiple_daily_prices.side_effect = StockDataFetchError(
            "Bulk fetch failed"
        )
        # Individual fetch succeeds for AAPL, fails for INVALID
        mock_data_source.fetch_daily_prices.side_effect = [
            mock_df,
            StockDataFetchError("Invalid symbol", symbol="INVALID"),
        ]

        handler = CollectDataHandler(data_source=mock_data_source)
        command = FetchStockDataCommand(
            symbols=["AAPL", "INVALID"],
            period="1mo",
        )

        # Act
        result = handler.handle(command)

        # Assert
        assert result.success_count == 1
        assert result.error_count == 1
        assert "AAPL" in result.data
        assert "INVALID" in result.errors

    def test_handle_with_repository_saves_data(self) -> None:
        """Test that data is saved when repository is provided."""
        # Arrange
        mock_data_source = MagicMock()
        mock_repository = MagicMock()
        mock_ticker = MagicMock()
        mock_ticker.ticker_id = 1

        mock_df = pd.DataFrame(
            {
                "open": [100.0],
                "close": [105.0],
                "high": [110.0],
                "low": [95.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        mock_data_source.fetch_multiple_daily_prices.return_value = {"AAPL": mock_df}
        mock_data_source.fetch_ticker_info.return_value = {
            "name": "Apple Inc.",
            "symbol": "AAPL",
        }
        mock_repository.get_or_create_ticker.return_value = mock_ticker
        mock_repository.bulk_upsert_from_dataframe.return_value = 1

        handler = CollectDataHandler(
            data_source=mock_data_source,
            daily_price_repository=mock_repository,
        )
        command = FetchStockDataCommand(
            symbols=["AAPL"],
            period="1mo",
        )

        # Act
        result = handler.handle(command)

        # Assert
        mock_repository.get_or_create_ticker.assert_called_once_with(
            symbol="AAPL", name="Apple Inc."
        )
        mock_repository.bulk_upsert_from_dataframe.assert_called_once()
        assert result.saved_records["AAPL"] == 1

    def test_handle_ticker_info_failure_continues(self) -> None:
        """Test that ticker info failure doesn't stop the process."""
        # Arrange
        mock_data_source = MagicMock()
        mock_repository = MagicMock()
        mock_ticker = MagicMock()
        mock_ticker.ticker_id = 1

        mock_df = pd.DataFrame(
            {
                "open": [100.0],
                "close": [105.0],
                "high": [110.0],
                "low": [95.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        mock_data_source.fetch_multiple_daily_prices.return_value = {"AAPL": mock_df}
        mock_data_source.fetch_ticker_info.side_effect = StockDataFetchError(
            "Failed to get info"
        )
        mock_repository.get_or_create_ticker.return_value = mock_ticker
        mock_repository.bulk_upsert_from_dataframe.return_value = 1

        handler = CollectDataHandler(
            data_source=mock_data_source,
            daily_price_repository=mock_repository,
        )
        command = FetchStockDataCommand(
            symbols=["AAPL"],
            period="1mo",
        )

        # Act
        result = handler.handle(command)

        # Assert - should still save with None name
        mock_repository.get_or_create_ticker.assert_called_once_with(
            symbol="AAPL", name=None
        )
        assert result.saved_records["AAPL"] == 1


class TestCollectDataHandlerWithHistoricalData:
    """Test cases for CollectDataHandler with historical data integration."""

    def test_uses_historical_data_for_indicator_calculation(self) -> None:
        """Test that historical data is used when calculating indicators."""
        # Arrange
        mock_data_source = MagicMock()
        mock_repository = MagicMock()
        mock_indicator_service = MagicMock()
        mock_ticker = MagicMock()
        mock_ticker.ticker_id = 1

        # New data (small dataset)
        new_df = pd.DataFrame(
            {
                "open": [100.0],
                "high": [110.0],
                "low": [95.0],
                "close": [105.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-10"]),
        )

        # Historical data from DB
        historical_df = pd.DataFrame(
            {
                "open": [90.0 + i for i in range(5)],
                "high": [100.0 + i for i in range(5)],
                "low": [85.0 + i for i in range(5)],
                "close": [95.0 + i for i in range(5)],
                "volume": [900 + i * 10 for i in range(5)],
            },
            index=pd.DatetimeIndex(
                ["2024-01-05", "2024-01-06", "2024-01-07", "2024-01-08", "2024-01-09"]
            ),
        )

        mock_data_source.fetch_multiple_daily_prices.return_value = {"AAPL": new_df}
        mock_data_source.fetch_ticker_info.return_value = {"name": "Apple"}
        mock_repository.get_or_create_ticker.return_value = mock_ticker
        mock_repository.get_historical_for_indicator_calculation.return_value = []
        mock_repository.daily_prices_to_dataframe.return_value = historical_df
        mock_repository.bulk_upsert_from_dataframe.return_value = 1
        mock_indicator_service.get_required_lookback.return_value = 75

        # Mock calculate_all to return a result with all data
        mock_calc_result = MagicMock()
        mock_calc_result.data = pd.concat([historical_df, new_df]).sort_index()
        mock_indicator_service.calculate_all.return_value = mock_calc_result

        handler = CollectDataHandler(
            data_source=mock_data_source,
            daily_price_repository=mock_repository,
            indicator_service=mock_indicator_service,
        )
        command = FetchStockDataCommand(symbols=["AAPL"], period="1d")

        # Act
        result = handler.handle(command)

        # Assert
        mock_repository.get_historical_for_indicator_calculation.assert_called_once()
        mock_repository.daily_prices_to_dataframe.assert_called_once()
        mock_indicator_service.calculate_all.assert_called_once()
        assert result.success_count == 1

    def test_handles_no_historical_data_gracefully(self) -> None:
        """Test that missing historical data doesn't cause errors."""
        # Arrange
        mock_data_source = MagicMock()
        mock_repository = MagicMock()
        mock_indicator_service = MagicMock()
        mock_ticker = MagicMock()
        mock_ticker.ticker_id = 1

        new_df = pd.DataFrame(
            {
                "open": [100.0],
                "high": [110.0],
                "low": [95.0],
                "close": [105.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )

        # Empty historical data
        empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        mock_data_source.fetch_multiple_daily_prices.return_value = {"AAPL": new_df}
        mock_data_source.fetch_ticker_info.return_value = {"name": "Apple"}
        mock_repository.get_or_create_ticker.return_value = mock_ticker
        mock_repository.get_historical_for_indicator_calculation.return_value = []
        mock_repository.daily_prices_to_dataframe.return_value = empty_df
        mock_repository.bulk_upsert_from_dataframe.return_value = 1
        mock_indicator_service.get_required_lookback.return_value = 75

        mock_calc_result = MagicMock()
        mock_calc_result.data = new_df.copy()
        mock_indicator_service.calculate_all.return_value = mock_calc_result

        handler = CollectDataHandler(
            data_source=mock_data_source,
            daily_price_repository=mock_repository,
            indicator_service=mock_indicator_service,
        )
        command = FetchStockDataCommand(symbols=["AAPL"], period="1d")

        # Act
        result = handler.handle(command)

        # Assert - should still work without errors
        assert result.success_count == 1
        assert result.error_count == 0

    def test_backward_compatible_without_repository(self) -> None:
        """Test that indicator calculation works without repository."""
        # Arrange
        mock_data_source = MagicMock()
        mock_indicator_service = MagicMock()

        new_df = pd.DataFrame(
            {
                "open": [100.0],
                "high": [110.0],
                "low": [95.0],
                "close": [105.0],
                "volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )

        mock_data_source.fetch_multiple_daily_prices.return_value = {"AAPL": new_df}

        mock_calc_result = MagicMock()
        mock_calc_result.data = new_df.copy()
        mock_calc_result.failed_indicators = {}
        mock_indicator_service.calculate_all.return_value = mock_calc_result

        # No repository provided
        handler = CollectDataHandler(
            data_source=mock_data_source,
            indicator_service=mock_indicator_service,
        )
        command = FetchStockDataCommand(symbols=["AAPL"], period="1d")

        # Act
        result = handler.handle(command)

        # Assert - should work without repository
        assert result.success_count == 1
        mock_indicator_service.calculate_all.assert_called_once()

    def test_only_saves_new_data_portion(self) -> None:
        """Test that only new data is saved to database after calculation."""
        # Arrange
        mock_data_source = MagicMock()
        mock_repository = MagicMock()
        mock_indicator_service = MagicMock()
        mock_ticker = MagicMock()
        mock_ticker.ticker_id = 1

        new_df = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [110.0, 111.0],
                "low": [95.0, 96.0],
                "close": [105.0, 106.0],
                "volume": [1000, 1100],
            },
            index=pd.DatetimeIndex(["2024-01-10", "2024-01-11"]),
        )

        historical_df = pd.DataFrame(
            {
                "open": [90.0],
                "high": [100.0],
                "low": [85.0],
                "close": [95.0],
                "volume": [900],
            },
            index=pd.DatetimeIndex(["2024-01-09"]),
        )

        mock_data_source.fetch_multiple_daily_prices.return_value = {"AAPL": new_df}
        mock_data_source.fetch_ticker_info.return_value = {"name": "Apple"}
        mock_repository.get_or_create_ticker.return_value = mock_ticker
        mock_repository.get_historical_for_indicator_calculation.return_value = []
        mock_repository.daily_prices_to_dataframe.return_value = historical_df
        mock_repository.bulk_upsert_from_dataframe.return_value = 2
        mock_indicator_service.get_required_lookback.return_value = 75

        # Combined data with indicator columns
        combined = pd.concat([historical_df, new_df]).sort_index()
        combined["sma_5"] = 100.0  # Mock indicator

        mock_calc_result = MagicMock()
        mock_calc_result.data = combined
        mock_indicator_service.calculate_all.return_value = mock_calc_result

        handler = CollectDataHandler(
            data_source=mock_data_source,
            daily_price_repository=mock_repository,
            indicator_service=mock_indicator_service,
        )
        command = FetchStockDataCommand(symbols=["AAPL"], period="2d")

        # Act
        result = handler.handle(command)

        # Assert
        # The saved DataFrame should only contain 2 rows (new data)
        call_args = mock_repository.bulk_upsert_from_dataframe.call_args
        saved_df = call_args.kwargs.get("df")
        if saved_df is None and len(call_args.args) > 1:
            saved_df = call_args.args[1]
        assert saved_df is not None
        assert len(saved_df) == 2
        assert result.saved_records["AAPL"] == 2
