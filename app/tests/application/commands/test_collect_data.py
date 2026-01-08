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
