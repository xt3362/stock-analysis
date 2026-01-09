"""Tests for Event Schedule Repositories."""

# pyright: reportUnknownMemberType=false, reportGeneralTypeIssues=false
# pyright: reportArgumentType=false
# NOTE: MagicMock typing issues in tests

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from src.infrastructure.persistence.repositories import (
    PostgresDividendScheduleRepository,
    PostgresEarningsScheduleRepository,
)


class TestPostgresEarningsScheduleRepository:
    """Test cases for PostgresEarningsScheduleRepository."""

    def test_get_by_ticker_returns_list(self) -> None:
        """Test that get_by_ticker returns list of schedules."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)

        mock_results = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_results

        # Act
        result = repo.get_by_ticker(ticker_id=1, limit=10)

        # Assert
        assert len(result) == 2

    def test_get_by_ticker_respects_limit(self) -> None:
        """Test that get_by_ticker respects the limit parameter."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # Act
        repo.get_by_ticker(ticker_id=1, limit=5)

        # Assert
        mock_query.limit.assert_called_once_with(5)

    def test_get_upcoming_by_ticker_returns_first_future(self) -> None:
        """Test that get_upcoming_by_ticker returns the first future schedule."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)

        mock_schedule = MagicMock()
        mock_schedule.earnings_date = date(2024, 5, 15)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_schedule

        # Act
        result = repo.get_upcoming_by_ticker(ticker_id=1, from_date=date(2024, 4, 1))

        # Assert
        assert result is not None
        assert result.earnings_date == date(2024, 5, 15)

    def test_get_upcoming_by_ticker_returns_none_when_no_future(self) -> None:
        """Test that get_upcoming_by_ticker returns None when no future schedules."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = repo.get_upcoming_by_ticker(ticker_id=1, from_date=date(2024, 12, 31))

        # Assert
        assert result is None

    def test_save_adds_to_session(self) -> None:
        """Test that save adds schedule to session."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)
        mock_schedule = MagicMock()

        # Act
        result = repo.save(mock_schedule)

        # Assert
        mock_session.add.assert_called_once_with(mock_schedule)
        mock_session.flush.assert_called_once()
        assert result == mock_schedule

    def test_upsert_creates_new_when_not_exists(self) -> None:
        """Test that upsert creates new schedule when not exists."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = repo.upsert(
            ticker_id=1,
            earnings_date=date(2024, 5, 15),
            fiscal_quarter="Q1",
            fiscal_year=2024,
        )

        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.ticker_id == 1
        assert result.earnings_date == date(2024, 5, 15)

    def test_upsert_updates_existing(self) -> None:
        """Test that upsert updates existing schedule."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)

        mock_existing = MagicMock()
        mock_existing.fiscal_quarter = None
        mock_existing.fiscal_year = None
        mock_existing.is_confirmed = False

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing

        # Act
        result = repo.upsert(
            ticker_id=1,
            earnings_date=date(2024, 5, 15),
            fiscal_quarter="Q1",
            fiscal_year=2024,
            is_confirmed=True,
        )

        # Assert
        assert result == mock_existing
        assert mock_existing.fiscal_quarter == "Q1"
        assert mock_existing.fiscal_year == 2024
        assert mock_existing.is_confirmed is True
        mock_session.flush.assert_called_once()

    def test_delete_by_ticker_returns_count(self) -> None:
        """Test that delete_by_ticker returns deleted count."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresEarningsScheduleRepository(mock_session)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 3

        # Act
        result = repo.delete_by_ticker(ticker_id=1)

        # Assert
        assert result == 3


class TestPostgresDividendScheduleRepository:
    """Test cases for PostgresDividendScheduleRepository."""

    def test_get_by_ticker_returns_list(self) -> None:
        """Test that get_by_ticker returns list of schedules."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDividendScheduleRepository(mock_session)

        mock_results = [MagicMock(), MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_results

        # Act
        result = repo.get_by_ticker(ticker_id=1, limit=10)

        # Assert
        assert len(result) == 3

    def test_get_upcoming_by_ticker_returns_first_future(self) -> None:
        """Test that get_upcoming_by_ticker returns the first future schedule."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDividendScheduleRepository(mock_session)

        mock_schedule = MagicMock()
        mock_schedule.ex_dividend_date = date(2024, 9, 27)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_schedule

        # Act
        result = repo.get_upcoming_by_ticker(ticker_id=1, from_date=date(2024, 4, 1))

        # Assert
        assert result is not None
        assert result.ex_dividend_date == date(2024, 9, 27)

    def test_save_adds_to_session(self) -> None:
        """Test that save adds schedule to session."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDividendScheduleRepository(mock_session)
        mock_schedule = MagicMock()

        # Act
        result = repo.save(mock_schedule)

        # Assert
        mock_session.add.assert_called_once_with(mock_schedule)
        mock_session.flush.assert_called_once()
        assert result == mock_schedule

    def test_upsert_creates_new_when_not_exists(self) -> None:
        """Test that upsert creates new schedule when not exists."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDividendScheduleRepository(mock_session)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = repo.upsert(
            ticker_id=1,
            ex_dividend_date=date(2024, 9, 27),
            dividend_rate=75.0,
            dividend_yield=0.018,
        )

        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.ticker_id == 1
        assert result.ex_dividend_date == date(2024, 9, 27)

    def test_upsert_updates_existing(self) -> None:
        """Test that upsert updates existing schedule."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDividendScheduleRepository(mock_session)

        mock_existing = MagicMock()
        mock_existing.dividend_rate = None
        mock_existing.dividend_yield = None

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing

        # Act
        result = repo.upsert(
            ticker_id=1,
            ex_dividend_date=date(2024, 9, 27),
            dividend_rate=80.0,
            dividend_yield=0.02,
        )

        # Assert
        assert result == mock_existing
        assert mock_existing.dividend_rate == Decimal("80.0")
        assert mock_existing.dividend_yield == Decimal("0.02")
        mock_session.flush.assert_called_once()

    def test_upsert_handles_none_values(self) -> None:
        """Test that upsert handles None values correctly."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDividendScheduleRepository(mock_session)

        mock_existing = MagicMock()
        mock_existing.dividend_rate = Decimal("50.0")
        mock_existing.dividend_yield = Decimal("0.01")

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing

        # Act - upsert with None values should not update
        result = repo.upsert(
            ticker_id=1,
            ex_dividend_date=date(2024, 9, 27),
            dividend_rate=None,
            dividend_yield=None,
        )

        # Assert - existing values should remain unchanged
        assert result == mock_existing
        # Existing values should NOT be updated when None is passed
        assert mock_existing.dividend_rate == Decimal("50.0")
        assert mock_existing.dividend_yield == Decimal("0.01")

    def test_delete_by_ticker_returns_count(self) -> None:
        """Test that delete_by_ticker returns deleted count."""
        # Arrange
        mock_session = MagicMock()
        repo = PostgresDividendScheduleRepository(mock_session)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 5

        # Act
        result = repo.delete_by_ticker(ticker_id=1)

        # Assert
        assert result == 5
