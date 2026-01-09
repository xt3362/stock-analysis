"""Tests for Event Schedule ORM models."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportGeneralTypeIssues=false
# NOTE: SQLAlchemy ORM typing issues in tests

from datetime import date, datetime, timezone
from decimal import Decimal

from src.infrastructure.persistence.models import DividendSchedule, EarningsSchedule


class TestEarningsScheduleModel:
    """Test cases for EarningsSchedule ORM model."""

    def test_repr(self) -> None:
        """Test __repr__ method."""
        schedule = EarningsSchedule(
            ticker_id=1,
            earnings_date=date(2024, 5, 15),
            fiscal_quarter="Q1",
            fiscal_year=2024,
            is_confirmed=False,
            retrieved_at=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        repr_str = repr(schedule)

        assert "EarningsSchedule" in repr_str
        assert "ticker_id=1" in repr_str
        assert "2024-05-15" in repr_str
        assert "Q1" in repr_str

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        retrieved_at = datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        schedule = EarningsSchedule(
            schedule_id=1,
            ticker_id=1,
            earnings_date=date(2024, 5, 15),
            fiscal_quarter="Q1",
            fiscal_year=2024,
            is_confirmed=True,
            retrieved_at=retrieved_at,
        )

        result = schedule.to_dict()

        assert result["schedule_id"] == 1
        assert result["ticker_id"] == 1
        assert result["earnings_date"] == "2024-05-15"
        assert result["fiscal_quarter"] == "Q1"
        assert result["fiscal_year"] == 2024
        assert result["is_confirmed"] is True
        assert "2024-04-01" in result["retrieved_at"]

    def test_to_dict_with_none_values(self) -> None:
        """Test to_dict method with None values."""
        schedule = EarningsSchedule(
            ticker_id=1,
            earnings_date=date(2024, 5, 15),
            fiscal_quarter=None,
            fiscal_year=None,
            is_confirmed=False,
            retrieved_at=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = schedule.to_dict()

        assert result["fiscal_quarter"] is None
        assert result["fiscal_year"] is None

    def test_instantiation(self) -> None:
        """Test that EarningsSchedule can be instantiated."""
        schedule = EarningsSchedule(
            ticker_id=1,
            earnings_date=date(2024, 5, 15),
            retrieved_at=datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Verify basic attributes are set
        assert schedule.ticker_id == 1
        assert schedule.earnings_date == date(2024, 5, 15)


class TestDividendScheduleModel:
    """Test cases for DividendSchedule ORM model."""

    def test_repr(self) -> None:
        """Test __repr__ method."""
        schedule = DividendSchedule(
            ticker_id=1,
            ex_dividend_date=date(2024, 9, 27),
            dividend_rate=Decimal("75.0000"),
            dividend_yield=Decimal("0.0180"),
            retrieved_at=datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        repr_str = repr(schedule)

        assert "DividendSchedule" in repr_str
        assert "ticker_id=1" in repr_str
        assert "2024-09-27" in repr_str
        assert "75" in repr_str

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        retrieved_at = datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        schedule = DividendSchedule(
            schedule_id=1,
            ticker_id=1,
            ex_dividend_date=date(2024, 9, 27),
            dividend_rate=Decimal("75.0000"),
            dividend_yield=Decimal("0.0180"),
            retrieved_at=retrieved_at,
        )

        result = schedule.to_dict()

        assert result["schedule_id"] == 1
        assert result["ticker_id"] == 1
        assert result["ex_dividend_date"] == "2024-09-27"
        assert result["dividend_rate"] == 75.0
        assert result["dividend_yield"] == 0.018
        assert "2024-09-01" in result["retrieved_at"]

    def test_to_dict_with_none_values(self) -> None:
        """Test to_dict method with None values."""
        schedule = DividendSchedule(
            ticker_id=1,
            ex_dividend_date=date(2024, 9, 27),
            dividend_rate=None,
            dividend_yield=None,
            retrieved_at=datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = schedule.to_dict()

        assert result["dividend_rate"] is None
        assert result["dividend_yield"] is None

    def test_decimal_precision(self) -> None:
        """Test that Decimal values maintain precision."""
        schedule = DividendSchedule(
            ticker_id=1,
            ex_dividend_date=date(2024, 9, 27),
            dividend_rate=Decimal("75.1234"),
            dividend_yield=Decimal("0.0189"),
            retrieved_at=datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = schedule.to_dict()

        # Float conversion may lose some precision
        assert abs(result["dividend_rate"] - 75.1234) < 0.0001
        assert abs(result["dividend_yield"] - 0.0189) < 0.00001
