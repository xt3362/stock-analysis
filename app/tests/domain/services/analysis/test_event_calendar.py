"""Tests for EventCalendarService."""

from datetime import date

import pytest

from src.domain.models.event_calendar import (
    EventCalendarConfig,
    EventInput,
    EventRiskLevel,
    EventType,
)
from src.domain.services.analysis.event_calendar import EventCalendarService


@pytest.fixture
def service() -> EventCalendarService:
    """Create EventCalendarService instance with default config."""
    return EventCalendarService()


@pytest.fixture
def custom_config_service() -> EventCalendarService:
    """Create EventCalendarService with custom config."""
    config = EventCalendarConfig(
        earnings_exclude_before=3,
        earnings_exclude_after=2,
        earnings_cross_threshold=10.0,
    )
    return EventCalendarService(config=config)


class TestEarningsEvaluation:
    """決算イベント評価のテスト."""

    def test_no_earnings_date_returns_allowed(
        self, service: EventCalendarService
    ) -> None:
        """決算日なしの場合はエントリー許可."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),
            earnings_date=None,
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is True
        assert result.exit_required is False

    def test_earnings_exclude_period_blocks_entry(
        self, service: EventCalendarService
    ) -> None:
        """決算除外期間（-2日〜+1日）はエントリー禁止."""
        # 決算2日前
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 13),
            earnings_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is False
        assert result.risk_level == EventRiskLevel.CRITICAL
        assert "除外期間" in result.reason

    def test_earnings_1_day_before_blocks_entry(
        self, service: EventCalendarService
    ) -> None:
        """決算1日前はエントリー禁止."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 14),
            earnings_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is False
        assert result.risk_level == EventRiskLevel.CRITICAL

    def test_earnings_day_blocks_entry(self, service: EventCalendarService) -> None:
        """決算当日はエントリー禁止."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),
            earnings_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is False
        assert result.risk_level == EventRiskLevel.CRITICAL

    def test_earnings_after_exclude_blocks_entry(
        self, service: EventCalendarService
    ) -> None:
        """決算翌日（+1日）はエントリー禁止."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 16),
            earnings_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is False
        assert result.risk_level == EventRiskLevel.CRITICAL

    def test_earnings_2_days_after_allowed(self, service: EventCalendarService) -> None:
        """決算2日後はエントリー許可."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 17),
            earnings_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        # 決算2日後は除外期間外
        assert result.risk_level != EventRiskLevel.CRITICAL

    def test_earnings_cross_with_high_pnl_allowed(
        self, service: EventCalendarService
    ) -> None:
        """+8%以上の含み益なら決算跨ぎ許容."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 14),  # 決算1日前
            earnings_date=date(2024, 1, 15),
            position_pnl=10.0,  # 10%の含み益
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is False  # 新規エントリーは不可
        assert result.exit_required is False  # 決済は不要
        assert "跨ぎ許容" in result.reason

    def test_earnings_cross_with_low_pnl_exit_required(
        self, service: EventCalendarService
    ) -> None:
        """+8%未満の含み益なら決算前決済推奨."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 14),
            earnings_date=date(2024, 1, 15),
            position_pnl=5.0,  # 5%の含み益
        )
        result = service.evaluate(event_input)

        assert result.exit_required is True
        assert "決済推奨" in result.reason

    def test_earnings_cross_with_exactly_threshold(
        self, service: EventCalendarService
    ) -> None:
        """ちょうど8%の含み益なら決算跨ぎ許容."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 14),
            earnings_date=date(2024, 1, 15),
            position_pnl=8.0,  # ちょうど8%
        )
        result = service.evaluate(event_input)

        assert result.exit_required is False
        assert "跨ぎ許容" in result.reason

    def test_earnings_5_days_before_high_risk(
        self, service: EventCalendarService
    ) -> None:
        """決算5日前は HIGH リスクだがエントリー可能."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 10),
            earnings_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is True
        assert result.risk_level == EventRiskLevel.HIGH

    def test_earnings_3_days_before_high_risk(
        self, service: EventCalendarService
    ) -> None:
        """決算3日前は HIGH リスク（除外期間外）でエントリー可能."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 12),
            earnings_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is True
        assert result.risk_level == EventRiskLevel.HIGH


class TestDividendEvaluation:
    """配当イベント評価のテスト."""

    def test_no_dividend_date_returns_allowed(
        self, service: EventCalendarService
    ) -> None:
        """配当日なしの場合はエントリー許可."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),
            ex_dividend_date=None,
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is True

    def test_ex_dividend_day_minus_1_blocks_entry(
        self, service: EventCalendarService
    ) -> None:
        """権利付最終日（配当落ち前日）はエントリー禁止."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 3, 27),  # 権利確定日の1日前
            ex_dividend_date=date(2024, 3, 28),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is False
        assert result.risk_level == EventRiskLevel.MEDIUM

    def test_ex_dividend_day_allows_entry(self, service: EventCalendarService) -> None:
        """配当権利確定日当日はエントリー許可."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 3, 28),
            ex_dividend_date=date(2024, 3, 28),
        )
        result = service.evaluate(event_input)

        # 当日は除外対象外
        is_medium_risk = result.risk_level == EventRiskLevel.MEDIUM
        assert not is_medium_risk or result.entry_allowed is True


class TestSQEvaluation:
    """SQ日評価のテスト."""

    def test_sq_day_low_risk(self, service: EventCalendarService) -> None:
        """SQ日当日は LOW リスク."""
        # 2024年1月のSQ日は12日（第2金曜）
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 12),
        )
        result = service.evaluate(event_input)

        # SQ日当日
        assert result.risk_level == EventRiskLevel.LOW
        assert result.entry_allowed is True  # エントリーは可能
        assert "SQ日" in result.reason

    def test_non_sq_day_no_risk(self, service: EventCalendarService) -> None:
        """SQ日以外はリスクなし."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),  # SQ日ではない
        )
        result = service.evaluate(event_input)

        # SQに関するリスクなし（他にイベントがなければNONE）
        assert result.risk_level == EventRiskLevel.NONE


class TestSQDateCalculation:
    """SQ日計算のテスト."""

    def test_sq_date_january_2024(self, service: EventCalendarService) -> None:
        """2024年1月のSQ日は12日."""
        sq_date = service._get_sq_date(2024, 1)
        assert sq_date == date(2024, 1, 12)

    def test_sq_date_february_2024(self, service: EventCalendarService) -> None:
        """2024年2月のSQ日は9日."""
        sq_date = service._get_sq_date(2024, 2)
        assert sq_date == date(2024, 2, 9)

    def test_sq_date_march_2024(self, service: EventCalendarService) -> None:
        """2024年3月のSQ日（メジャーSQ）は8日."""
        sq_date = service._get_sq_date(2024, 3)
        assert sq_date == date(2024, 3, 8)

    def test_sq_date_december_2024(self, service: EventCalendarService) -> None:
        """2024年12月のSQ日は13日."""
        sq_date = service._get_sq_date(2024, 12)
        assert sq_date == date(2024, 12, 13)

    def test_get_next_sq_date_before_sq(self, service: EventCalendarService) -> None:
        """SQ日前なら当月のSQ日を返す."""
        next_sq = service.get_next_sq_date(date(2024, 1, 5))
        assert next_sq == date(2024, 1, 12)

    def test_get_next_sq_date_on_sq(self, service: EventCalendarService) -> None:
        """SQ日当日はその日を返す."""
        next_sq = service.get_next_sq_date(date(2024, 1, 12))
        assert next_sq == date(2024, 1, 12)

    def test_get_next_sq_date_after_sq(self, service: EventCalendarService) -> None:
        """SQ日後なら翌月のSQ日を返す."""
        next_sq = service.get_next_sq_date(date(2024, 1, 15))
        assert next_sq == date(2024, 2, 9)

    def test_get_next_sq_date_december(self, service: EventCalendarService) -> None:
        """12月のSQ日後は翌年1月のSQ日を返す."""
        next_sq = service.get_next_sq_date(date(2024, 12, 20))
        assert next_sq == date(2025, 1, 10)


class TestCombinedEvaluation:
    """複合イベント評価のテスト."""

    def test_multiple_events_highest_risk_wins(
        self, service: EventCalendarService
    ) -> None:
        """複数イベントがある場合、最も高いリスクを採用."""
        # 決算直前 + SQ日
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 12),  # SQ日
            earnings_date=date(2024, 1, 14),  # 決算2日前
        )
        result = service.evaluate(event_input)

        assert result.risk_level == EventRiskLevel.CRITICAL
        assert result.entry_allowed is False

    def test_nearest_event_is_correct(self, service: EventCalendarService) -> None:
        """最も近いイベントが正しく返される."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 10),
            earnings_date=date(2024, 1, 20),
            ex_dividend_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.nearest_event is not None
        # SQ日(1/12)が最も近い
        assert result.nearest_event.event_type == EventType.SQ
        assert result.nearest_event.days_until == 2

    def test_all_events_entry_allowed_when_no_exclusion(
        self, service: EventCalendarService
    ) -> None:
        """すべてのイベントが除外期間外ならエントリー許可."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 5),
            earnings_date=date(2024, 1, 20),  # 15日後
            ex_dividend_date=date(2024, 1, 25),  # 20日後
        )
        result = service.evaluate(event_input)

        # 除外期間外なのでエントリー可
        assert result.entry_allowed is True


class TestCustomConfig:
    """カスタム設定のテスト."""

    def test_custom_earnings_exclude_before(
        self, custom_config_service: EventCalendarService
    ) -> None:
        """カスタム設定で決算前除外日数が変更される."""
        # 3日前（カスタム設定では除外期間）
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 12),
            earnings_date=date(2024, 1, 15),
        )
        result = custom_config_service.evaluate(event_input)

        assert result.entry_allowed is False
        assert result.risk_level == EventRiskLevel.CRITICAL

    def test_custom_cross_threshold(
        self, custom_config_service: EventCalendarService
    ) -> None:
        """カスタム設定で跨ぎ閾値が変更される."""
        # 8%では不足（閾値10%）
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 14),
            earnings_date=date(2024, 1, 15),
            position_pnl=8.0,
        )
        result = custom_config_service.evaluate(event_input)

        assert result.exit_required is True


class TestEdgeCases:
    """エッジケースのテスト."""

    def test_all_none_inputs(self, service: EventCalendarService) -> None:
        """すべてのイベント日がNoneの場合."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 15),
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is True
        assert result.exit_required is False
        # SQ日(1/12)は過ぎているので次は2月のSQ日
        assert result.risk_level == EventRiskLevel.NONE

    def test_negative_pnl_exit_required(self, service: EventCalendarService) -> None:
        """含み損の場合も決済推奨."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 14),
            earnings_date=date(2024, 1, 15),
            position_pnl=-5.0,  # マイナス
        )
        result = service.evaluate(event_input)

        assert result.exit_required is True

    def test_past_earnings_date_within_exclude(
        self, service: EventCalendarService
    ) -> None:
        """過去の決算日が除外期間内（+1日）の場合."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 16),
            earnings_date=date(2024, 1, 15),  # 昨日
        )
        result = service.evaluate(event_input)

        assert result.entry_allowed is False
        assert result.risk_level == EventRiskLevel.CRITICAL

    def test_past_earnings_date_outside_exclude(
        self, service: EventCalendarService
    ) -> None:
        """過去の決算日が除外期間外（+2日以降）の場合."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 20),
            earnings_date=date(2024, 1, 15),  # 5日前
        )
        result = service.evaluate(event_input)

        # 除外期間外なので CRITICAL ではない
        assert result.risk_level != EventRiskLevel.CRITICAL

    def test_nearest_event_with_only_sq(self, service: EventCalendarService) -> None:
        """決算・配当がない場合、SQ日が最近イベントになる."""
        event_input = EventInput(
            symbol="7203.T",
            check_date=date(2024, 1, 5),
        )
        result = service.evaluate(event_input)

        assert result.nearest_event is not None
        assert result.nearest_event.event_type == EventType.SQ
        assert result.nearest_event.event_date == date(2024, 1, 12)
