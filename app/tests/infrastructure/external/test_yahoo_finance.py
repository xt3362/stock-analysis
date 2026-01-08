"""Tests for YahooFinanceClient."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.infrastructure.external.yahoo_finance import YahooFinanceClient
from src.shared.exceptions import StockDataFetchError


class TestYahooFinanceClient:
    """Test cases for YahooFinanceClient."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        client = YahooFinanceClient()
        assert client._timeout == 30
        assert client._retry_count == 3

    def test_init_custom_values(self) -> None:
        """Test initialization with custom values."""
        client = YahooFinanceClient(request_timeout=60, retry_count=5)
        assert client._timeout == 60
        assert client._retry_count == 5

    def test_validate_date_params_period_only(self) -> None:
        """Test validation passes with period only."""
        client = YahooFinanceClient()
        # Should not raise
        client._validate_date_params(None, None, "1mo")

    def test_validate_date_params_dates_only(self) -> None:
        """Test validation passes with dates only."""
        client = YahooFinanceClient()
        # Should not raise
        client._validate_date_params(date(2024, 1, 1), date(2024, 12, 31), None)

    def test_validate_date_params_both_raises(self) -> None:
        """Test validation raises when both period and dates specified."""
        client = YahooFinanceClient()
        with pytest.raises(ValueError, match="Cannot specify both"):
            client._validate_date_params(date(2024, 1, 1), None, "1mo")

    def test_validate_date_params_none_raises(self) -> None:
        """Test validation raises when neither specified."""
        client = YahooFinanceClient()
        with pytest.raises(ValueError, match="Must specify either"):
            client._validate_date_params(None, None, None)

    def test_normalize_dataframe(self) -> None:
        """Test DataFrame column normalization."""
        client = YahooFinanceClient()
        df = pd.DataFrame(
            {
                "Open": [100],
                "High": [110],
                "Low": [95],
                "Close": [105],
                "Volume": [1000],
            }
        )
        normalized = client._normalize_dataframe(df)
        assert list(normalized.columns) == ["open", "high", "low", "close", "volume"]

    def test_normalize_dataframe_with_adj_close(self) -> None:
        """Test DataFrame normalization with Adj Close column."""
        client = YahooFinanceClient()
        df = pd.DataFrame(
            {
                "Open": [100],
                "High": [110],
                "Low": [95],
                "Close": [105],
                "Adj Close": [104],
                "Volume": [1000],
            }
        )
        normalized = client._normalize_dataframe(df)
        assert "adj_close" in normalized.columns

    @patch("src.infrastructure.external.yahoo_finance.yf.Ticker")
    def test_fetch_daily_prices_with_period(self, mock_ticker_class: MagicMock) -> None:
        """Test fetching daily prices with period parameter."""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_df = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [110.0, 111.0],
                "Low": [95.0, 96.0],
                "Close": [105.0, 106.0],
                "Volume": [1000, 1100],
            },
            index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"]),
        )
        mock_ticker.history.return_value = mock_df

        # Execute
        client = YahooFinanceClient()
        result = client.fetch_daily_prices(symbol="AAPL", period="1mo")

        # Verify
        mock_ticker_class.assert_called_once_with("AAPL")
        mock_ticker.history.assert_called_once_with(period="1mo")
        assert len(result) == 2
        assert "open" in result.columns

    @patch("src.infrastructure.external.yahoo_finance.yf.Ticker")
    def test_fetch_daily_prices_with_dates(self, mock_ticker_class: MagicMock) -> None:
        """Test fetching daily prices with date range."""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [110.0],
                "Low": [95.0],
                "Close": [105.0],
                "Volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        mock_ticker.history.return_value = mock_df

        # Execute
        client = YahooFinanceClient()
        result = client.fetch_daily_prices(
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        # Verify
        mock_ticker.history.assert_called_once_with(
            start="2024-01-01", end="2024-12-31"
        )
        assert len(result) == 1

    @patch("src.infrastructure.external.yahoo_finance.yf.Ticker")
    def test_fetch_daily_prices_empty_raises(
        self, mock_ticker_class: MagicMock
    ) -> None:
        """Test that empty result raises StockDataFetchError."""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame()

        # Execute & Verify
        client = YahooFinanceClient()
        with pytest.raises(StockDataFetchError, match="No data returned"):
            client.fetch_daily_prices(symbol="INVALID", period="1mo")

    @patch("src.infrastructure.external.yahoo_finance.yf.Ticker")
    def test_fetch_ticker_info(self, mock_ticker_class: MagicMock) -> None:
        """Test fetching ticker info."""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {
            "longName": "Apple Inc.",
            "exchange": "NMS",
            "currency": "USD",
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }

        # Execute
        client = YahooFinanceClient()
        result = client.fetch_ticker_info("AAPL")

        # Verify
        assert result["symbol"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["exchange"] == "NMS"
        assert result["currency"] == "USD"
        assert result["sector"] == "Technology"

    @patch("src.infrastructure.external.yahoo_finance.yf.download")
    def test_fetch_multiple_daily_prices_single_symbol(
        self, mock_download: MagicMock
    ) -> None:
        """Test fetching multiple symbols with single symbol."""
        # Setup mock
        mock_df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [110.0],
                "Low": [95.0],
                "Close": [105.0],
                "Volume": [1000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        mock_download.return_value = mock_df

        # Execute
        client = YahooFinanceClient()
        result = client.fetch_multiple_daily_prices(symbols=["AAPL"], period="1mo")

        # Verify
        mock_download.assert_called_once_with(
            ["AAPL"], period="1mo", group_by="ticker", progress=False
        )
        assert "AAPL" in result
        assert len(result["AAPL"]) == 1

    @patch("src.infrastructure.external.yahoo_finance.yf.download")
    def test_fetch_multiple_daily_prices_multiple_symbols(
        self, mock_download: MagicMock
    ) -> None:
        """Test fetching multiple symbols."""
        # Setup mock - yf.download returns MultiIndex columns for multiple symbols
        mock_df = pd.DataFrame(
            {
                ("AAPL", "Open"): [100.0],
                ("AAPL", "High"): [110.0],
                ("AAPL", "Low"): [95.0],
                ("AAPL", "Close"): [105.0],
                ("AAPL", "Volume"): [1000],
                ("MSFT", "Open"): [200.0],
                ("MSFT", "High"): [210.0],
                ("MSFT", "Low"): [195.0],
                ("MSFT", "Close"): [205.0],
                ("MSFT", "Volume"): [2000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )
        mock_df.columns = pd.MultiIndex.from_tuples(
            list(mock_df.columns)  # type: ignore[arg-type]
        )
        mock_download.return_value = mock_df

        # Execute
        client = YahooFinanceClient()
        result = client.fetch_multiple_daily_prices(
            symbols=["AAPL", "MSFT"], period="1mo"
        )

        # Verify
        assert "AAPL" in result
        assert "MSFT" in result
