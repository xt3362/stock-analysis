"""Tests for EventScheduleSyncService."""

from datetime import date
from unittest.mock import MagicMock

from src.application.services import EventScheduleSyncService, SyncResult
from src.domain.models.event_calendar import EventInput
from src.shared.exceptions import StockDataFetchError


class TestSyncResult:
    """Test cases for SyncResult."""

    def test_success_when_no_errors(self) -> None:
        """Test that success is True when no errors."""
        result = SyncResult(symbol="AAPL", earnings_synced=2, dividend_synced=True)
        assert result.success is True

    def test_not_success_when_errors(self) -> None:
        """Test that success is False when errors exist."""
        result = SyncResult(
            symbol="AAPL",
            earnings_synced=0,
            dividend_synced=False,
            errors=["Error occurred"],
        )
        assert result.success is False

    def test_default_values(self) -> None:
        """Test default values."""
        result = SyncResult(symbol="AAPL")
        assert result.earnings_synced == 0
        assert result.dividend_synced is False
        assert result.errors == []


class TestEventScheduleSyncService:
    """Test cases for EventScheduleSyncService."""

    def test_sync_symbol_success(self) -> None:
        """Test successful sync of a single symbol."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_yahoo.fetch_earnings_dates.return_value = [
            date(2024, 5, 15),
            date(2024, 8, 15),
        ]
        mock_yahoo.fetch_dividend_info.return_value = {
            "ex_dividend_date": date(2024, 9, 27),
            "dividend_rate": 0.96,
            "dividend_yield": 0.0048,
        }

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.sync_symbol(symbol="AAPL", ticker_id=1)

        # Assert
        assert result.symbol == "AAPL"
        assert result.earnings_synced == 2
        assert result.dividend_synced is True
        assert result.success is True

        # Verify repository calls
        assert mock_earnings_repo.upsert.call_count == 2
        mock_dividend_repo.upsert.assert_called_once()

    def test_sync_symbol_no_dividend(self) -> None:
        """Test sync when no dividend info available."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_yahoo.fetch_earnings_dates.return_value = [date(2024, 5, 15)]
        mock_yahoo.fetch_dividend_info.return_value = {
            "ex_dividend_date": None,
            "dividend_rate": None,
            "dividend_yield": None,
        }

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.sync_symbol(symbol="TSLA", ticker_id=2)

        # Assert
        assert result.earnings_synced == 1
        assert result.dividend_synced is False
        mock_dividend_repo.upsert.assert_not_called()

    def test_sync_symbol_earnings_error(self) -> None:
        """Test sync when earnings fetch fails."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_yahoo.fetch_earnings_dates.side_effect = StockDataFetchError(
            "API error", symbol="AAPL"
        )
        mock_yahoo.fetch_dividend_info.return_value = {
            "ex_dividend_date": date(2024, 9, 27),
            "dividend_rate": 0.96,
            "dividend_yield": 0.0048,
        }

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.sync_symbol(symbol="AAPL", ticker_id=1)

        # Assert
        assert result.earnings_synced == 0
        assert result.dividend_synced is True  # Dividend still synced
        assert result.success is False
        assert len(result.errors) == 1
        assert "決算日取得エラー" in result.errors[0]

    def test_sync_symbol_dividend_error(self) -> None:
        """Test sync when dividend fetch fails."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_yahoo.fetch_earnings_dates.return_value = [date(2024, 5, 15)]
        mock_yahoo.fetch_dividend_info.side_effect = StockDataFetchError(
            "API error", symbol="AAPL"
        )

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.sync_symbol(symbol="AAPL", ticker_id=1)

        # Assert
        assert result.earnings_synced == 1  # Earnings still synced
        assert result.dividend_synced is False
        assert result.success is False
        assert len(result.errors) == 1
        assert "配当情報取得エラー" in result.errors[0]

    def test_sync_symbol_both_errors(self) -> None:
        """Test sync when both fetches fail."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_yahoo.fetch_earnings_dates.side_effect = Exception("Earnings error")
        mock_yahoo.fetch_dividend_info.side_effect = Exception("Dividend error")

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.sync_symbol(symbol="INVALID", ticker_id=999)

        # Assert
        assert result.earnings_synced == 0
        assert result.dividend_synced is False
        assert result.success is False
        assert len(result.errors) == 2

    def test_sync_symbol_with_earnings_limit(self) -> None:
        """Test that earnings_limit is passed to fetch."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_yahoo.fetch_earnings_dates.return_value = []
        mock_yahoo.fetch_dividend_info.return_value = {"ex_dividend_date": None}

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        service.sync_symbol(symbol="AAPL", ticker_id=1, earnings_limit=8)

        # Assert
        mock_yahoo.fetch_earnings_dates.assert_called_once_with(symbol="AAPL", limit=8)

    def test_sync_symbols_multiple(self) -> None:
        """Test sync of multiple symbols."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_yahoo.fetch_earnings_dates.return_value = [date(2024, 5, 15)]
        mock_yahoo.fetch_dividend_info.return_value = {
            "ex_dividend_date": date(2024, 9, 27),
            "dividend_rate": 0.96,
            "dividend_yield": 0.0048,
        }

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        symbols = [("AAPL", 1), ("MSFT", 2), ("GOOGL", 3)]

        # Act
        results = service.sync_symbols(symbols)

        # Assert
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].symbol == "AAPL"
        assert results[1].symbol == "MSFT"
        assert results[2].symbol == "GOOGL"

    def test_sync_symbols_empty_list(self) -> None:
        """Test sync with empty symbol list."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        results = service.sync_symbols([])

        # Assert
        assert results == []
        mock_yahoo.fetch_earnings_dates.assert_not_called()


class TestEventScheduleSyncServiceDataRetrieval:
    """Test cases for data retrieval methods."""

    def test_get_upcoming_earnings_date_found(self) -> None:
        """Test get_upcoming_earnings_date when schedule exists."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_schedule = MagicMock()
        mock_schedule.earnings_date = date(2024, 5, 15)
        mock_earnings_repo.get_upcoming_by_ticker.return_value = mock_schedule

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.get_upcoming_earnings_date(
            ticker_id=1, from_date=date(2024, 5, 1)
        )

        # Assert
        assert result == date(2024, 5, 15)
        mock_earnings_repo.get_upcoming_by_ticker.assert_called_once_with(
            1, date(2024, 5, 1)
        )

    def test_get_upcoming_earnings_date_not_found(self) -> None:
        """Test get_upcoming_earnings_date when no schedule exists."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_earnings_repo.get_upcoming_by_ticker.return_value = None

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.get_upcoming_earnings_date(
            ticker_id=1, from_date=date(2024, 5, 1)
        )

        # Assert
        assert result is None

    def test_get_upcoming_ex_dividend_date_found(self) -> None:
        """Test get_upcoming_ex_dividend_date when schedule exists."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_schedule = MagicMock()
        mock_schedule.ex_dividend_date = date(2024, 9, 27)
        mock_dividend_repo.get_upcoming_by_ticker.return_value = mock_schedule

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.get_upcoming_ex_dividend_date(
            ticker_id=1, from_date=date(2024, 9, 1)
        )

        # Assert
        assert result == date(2024, 9, 27)
        mock_dividend_repo.get_upcoming_by_ticker.assert_called_once_with(
            1, date(2024, 9, 1)
        )

    def test_get_upcoming_ex_dividend_date_not_found(self) -> None:
        """Test get_upcoming_ex_dividend_date when no schedule exists."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_dividend_repo.get_upcoming_by_ticker.return_value = None

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.get_upcoming_ex_dividend_date(
            ticker_id=1, from_date=date(2024, 9, 1)
        )

        # Assert
        assert result is None

    def test_build_event_input_with_schedules(self) -> None:
        """Test build_event_input when both schedules exist."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_earnings = MagicMock()
        mock_earnings.earnings_date = date(2024, 5, 15)
        mock_earnings_repo.get_upcoming_by_ticker.return_value = mock_earnings

        mock_dividend = MagicMock()
        mock_dividend.ex_dividend_date = date(2024, 9, 27)
        mock_dividend_repo.get_upcoming_by_ticker.return_value = mock_dividend

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.build_event_input(
            symbol="AAPL",
            ticker_id=1,
            check_date=date(2024, 5, 1),
            position_pnl=5.0,
        )

        # Assert
        assert isinstance(result, EventInput)
        assert result.symbol == "AAPL"
        assert result.check_date == date(2024, 5, 1)
        assert result.earnings_date == date(2024, 5, 15)
        assert result.ex_dividend_date == date(2024, 9, 27)
        assert result.position_pnl == 5.0

    def test_build_event_input_without_schedules(self) -> None:
        """Test build_event_input when no schedules exist."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_earnings_repo.get_upcoming_by_ticker.return_value = None
        mock_dividend_repo.get_upcoming_by_ticker.return_value = None

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.build_event_input(
            symbol="TSLA",
            ticker_id=2,
            check_date=date(2024, 5, 1),
        )

        # Assert
        assert isinstance(result, EventInput)
        assert result.symbol == "TSLA"
        assert result.check_date == date(2024, 5, 1)
        assert result.earnings_date is None
        assert result.ex_dividend_date is None
        assert result.position_pnl is None

    def test_build_event_input_only_earnings(self) -> None:
        """Test build_event_input when only earnings schedule exists."""
        # Arrange
        mock_yahoo = MagicMock()
        mock_earnings_repo = MagicMock()
        mock_dividend_repo = MagicMock()

        mock_earnings = MagicMock()
        mock_earnings.earnings_date = date(2024, 5, 15)
        mock_earnings_repo.get_upcoming_by_ticker.return_value = mock_earnings
        mock_dividend_repo.get_upcoming_by_ticker.return_value = None

        service = EventScheduleSyncService(
            yahoo_client=mock_yahoo,
            earnings_repo=mock_earnings_repo,
            dividend_repo=mock_dividend_repo,
        )

        # Act
        result = service.build_event_input(
            symbol="GOOGL",
            ticker_id=3,
            check_date=date(2024, 5, 1),
        )

        # Assert
        assert result.earnings_date == date(2024, 5, 15)
        assert result.ex_dividend_date is None
