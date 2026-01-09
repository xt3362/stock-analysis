"""Tests for EventCalendar domain models."""

from datetime import date

import pytest

from src.domain.models.event_calendar import (
    EventCalendarConfig,
    EventCalendarResult,
    EventInput,
    EventRiskLevel,
    EventType,
    NearestEvent,
)


class TestEventRiskLevel:
    """EventRiskLevel enum のテスト."""

    def test_enum_values(self) -> None:
        """Enum値の確認."""
        assert EventRiskLevel.NONE.value == "none"
        assert EventRiskLevel.LOW.value == "low"
        assert EventRiskLevel.MEDIUM.value == "medium"
        assert EventRiskLevel.HIGH.value == "high"
        assert EventRiskLevel.CRITICAL.value == "critical"

    def test_enum_count(self) -> None:
        """5つのレベルが存在."""
        assert len(EventRiskLevel) == 5


class TestEventType:
    """EventType enum のテスト."""

    def test_enum_values(self) -> None:
        """Enum値の確認."""
        assert EventType.EARNINGS.value == "earnings"
        assert EventType.DIVIDEND.value == "dividend"
        assert EventType.SQ.value == "sq"

    def test_enum_count(self) -> None:
        """3つのイベント種別が存在."""
        assert len(EventType) == 3


class TestNearestEvent:
    """NearestEvent dataclass のテスト."""

    def test_creation(self) -> None:
        """正常に作成できることを確認."""
        event = NearestEvent(
            event_type=EventType.EARNINGS,
            event_date=date(2024, 1, 15),
            days_until=5,
        )
        assert event.event_type == EventType.EARNINGS
        assert event.event_date == date(2024, 1, 15)
        assert event.days_until == 5

    def test_frozen(self) -> None:
        """イミュータブルであることを確認."""
        event = NearestEvent(
            event_type=EventType.EARNINGS,
            event_date=date(2024, 1, 15),
            days_until=5,
        )
        with pytest.raises(AttributeError):
            event.days_until = 10  # type: ignore[misc]


class TestEventCalendarResult:
    """EventCalendarResult dataclass のテスト."""

    def test_creation(self) -> None:
        """正常に作成できることを確認."""
        result = EventCalendarResult(
            entry_allowed=False,
            exit_required=True,
            risk_level=EventRiskLevel.CRITICAL,
            nearest_event=NearestEvent(
                event_type=EventType.EARNINGS,
                event_date=date(2024, 1, 15),
                days_until=2,
            ),
            reason="決算発表まで2日",
        )

        assert result.entry_allowed is False
        assert result.exit_required is True
        assert result.risk_level == EventRiskLevel.CRITICAL
        assert result.nearest_event is not None
        assert result.nearest_event.event_type == EventType.EARNINGS

    def test_nearest_event_none(self) -> None:
        """nearest_eventがNoneでも作成可能."""
        result = EventCalendarResult(
            entry_allowed=True,
            exit_required=False,
            risk_level=EventRiskLevel.NONE,
            nearest_event=None,
            reason="イベントなし",
        )

        assert result.nearest_event is None

    def test_frozen(self) -> None:
        """イミュータブルであることを確認."""
        result = EventCalendarResult(
            entry_allowed=True,
            exit_required=False,
            risk_level=EventRiskLevel.NONE,
            nearest_event=None,
            reason="イベントなし",
        )
        with pytest.raises(AttributeError):
            result.entry_allowed = False  # type: ignore[misc]


class TestEventCalendarConfig:
    """EventCalendarConfig dataclass のテスト."""

    def test_default_values(self) -> None:
        """デフォルト値の確認."""
        config = EventCalendarConfig()

        assert config.earnings_exclude_before == 2
        assert config.earnings_exclude_after == 1
        assert config.earnings_cross_threshold == 8.0
        assert config.dividend_exclude_days == 1

    def test_custom_values(self) -> None:
        """カスタム値の設定."""
        config = EventCalendarConfig(
            earnings_exclude_before=3,
            earnings_exclude_after=2,
            earnings_cross_threshold=10.0,
            dividend_exclude_days=2,
        )

        assert config.earnings_exclude_before == 3
        assert config.earnings_exclude_after == 2
        assert config.earnings_cross_threshold == 10.0
        assert config.dividend_exclude_days == 2

    def test_frozen(self) -> None:
        """イミュータブルであることを確認."""
        config = EventCalendarConfig()
        with pytest.raises(AttributeError):
            config.earnings_exclude_before = 5  # type: ignore[misc]


class TestEventInput:
    """EventInput dataclass のテスト."""

    def test_minimal_input(self) -> None:
        """最小限の入力で作成可能."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),
        )

        assert event_input.symbol == "7203.T"
        assert event_input.check_date == date(2024, 1, 15)
        assert event_input.earnings_date is None
        assert event_input.ex_dividend_date is None
        assert event_input.position_pnl is None

    def test_full_input(self) -> None:
        """すべてのフィールドを指定."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),
            earnings_date=date(2024, 1, 20),
            ex_dividend_date=date(2024, 3, 28),
            position_pnl=5.5,
        )

        assert event_input.earnings_date == date(2024, 1, 20)
        assert event_input.ex_dividend_date == date(2024, 3, 28)
        assert event_input.position_pnl == 5.5

    def test_frozen(self) -> None:
        """イミュータブルであることを確認."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),
        )
        with pytest.raises(AttributeError):
            event_input.symbol = "9984.T"  # type: ignore[misc]
