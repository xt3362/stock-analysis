"""イベントカレンダーサービス.

決算・配当・SQ日等のイベントを判定し、エントリー/エグジット判断を支援する。
"""

from calendar import monthcalendar
from datetime import date
from typing import Final

from src.domain.models.event_calendar import (
    EventCalendarConfig,
    EventCalendarResult,
    EventInput,
    EventRiskLevel,
    EventType,
    NearestEvent,
)


class EventCalendarService:
    """
    イベントカレンダーサービス.

    入力:
    - EventInput（銘柄コード、判定日、決算日、配当日、含み損益率）

    出力:
    - EventCalendarResult（エントリー可否、決済要否、リスクレベル、最近イベント、理由）
    """

    # SQ日は毎月第2金曜日
    _FRIDAY: Final[int] = 4  # weekday() で金曜日は4

    def __init__(
        self,
        config: EventCalendarConfig | None = None,
    ) -> None:
        """
        コンストラクタ.

        Args:
            config: 設定（Noneでデフォルト）
        """
        self._config = config or EventCalendarConfig()

    def evaluate(self, event_input: EventInput) -> EventCalendarResult:
        """
        イベントリスクを評価する.

        Args:
            event_input: イベント判定入力

        Returns:
            EventCalendarResult: 判定結果
        """
        check_date = event_input.check_date
        events: list[tuple[EventType, date, int]] = []

        # 決算イベントの評価
        earnings_result = self._evaluate_earnings(
            check_date=check_date,
            earnings_date=event_input.earnings_date,
            position_pnl=event_input.position_pnl,
        )
        if event_input.earnings_date:
            days_until = (event_input.earnings_date - check_date).days
            events.append((EventType.EARNINGS, event_input.earnings_date, days_until))

        # 配当イベントの評価
        dividend_result = self._evaluate_dividend(
            check_date=check_date,
            ex_dividend_date=event_input.ex_dividend_date,
        )
        if event_input.ex_dividend_date:
            days_until = (event_input.ex_dividend_date - check_date).days
            events.append(
                (EventType.DIVIDEND, event_input.ex_dividend_date, days_until)
            )

        # SQ日の評価
        sq_date = self.get_next_sq_date(check_date)
        sq_result = self._evaluate_sq(check_date=check_date, sq_date=sq_date)
        days_until = (sq_date - check_date).days
        events.append((EventType.SQ, sq_date, days_until))

        # 結果を統合
        return self._combine_results(
            earnings_result=earnings_result,
            dividend_result=dividend_result,
            sq_result=sq_result,
            events=events,
        )

    def _evaluate_earnings(
        self,
        check_date: date,
        earnings_date: date | None,
        position_pnl: float | None,
    ) -> tuple[bool, bool, EventRiskLevel, str]:
        """
        決算イベントを評価.

        Returns:
            (entry_allowed, exit_required, risk_level, reason)
        """
        if earnings_date is None:
            return True, False, EventRiskLevel.NONE, ""

        days_until = (earnings_date - check_date).days
        exclude_before = self._config.earnings_exclude_before
        exclude_after = self._config.earnings_exclude_after

        # 決算除外期間（発表日-2日〜+1日）
        if -exclude_after <= days_until <= exclude_before:
            # 除外期間内
            if position_pnl is not None and days_until > 0:
                # ポジション保有中で決算前
                if position_pnl >= self._config.earnings_cross_threshold:
                    # 含み益が閾値以上なら跨ぎ許容
                    return (
                        False,  # entry_allowed
                        False,  # exit_required
                        EventRiskLevel.CRITICAL,
                        f"決算発表まで{days_until}日、含み益{position_pnl:.1f}%で跨ぎ許容",
                    )
                else:
                    # 含み益不足で前日決済推奨
                    return (
                        False,
                        True,
                        EventRiskLevel.CRITICAL,
                        f"決算発表まで{days_until}日、含み益{position_pnl:.1f}%"
                        f"（<{self._config.earnings_cross_threshold}%）で決済推奨",
                    )
            # 新規エントリー禁止
            elif days_until >= 0:
                return (
                    False,
                    False,
                    EventRiskLevel.CRITICAL,
                    f"決算発表まで{days_until}日、除外期間中",
                )
            else:
                return (
                    False,
                    False,
                    EventRiskLevel.CRITICAL,
                    f"決算発表後{-days_until}日、除外期間中",
                )

        # 除外期間外だが近接（5日以内）
        if 0 < days_until <= 5:
            return (
                True,
                False,
                EventRiskLevel.HIGH,
                f"決算発表まで{days_until}日、注意",
            )

        return True, False, EventRiskLevel.NONE, ""

    def _evaluate_dividend(
        self,
        check_date: date,
        ex_dividend_date: date | None,
    ) -> tuple[bool, bool, EventRiskLevel, str]:
        """
        配当イベントを評価.

        Returns:
            (entry_allowed, exit_required, risk_level, reason)
        """
        if ex_dividend_date is None:
            return True, False, EventRiskLevel.NONE, ""

        days_until = (ex_dividend_date - check_date).days

        # 権利付最終日（配当落ち前日）のみ除外
        if days_until == self._config.dividend_exclude_days:
            return (
                False,
                False,
                EventRiskLevel.MEDIUM,
                f"配当権利確定日まで{days_until}日、権利付最終日",
            )

        return True, False, EventRiskLevel.NONE, ""

    def _evaluate_sq(
        self,
        check_date: date,
        sq_date: date,
    ) -> tuple[bool, bool, EventRiskLevel, str]:
        """
        SQ日を評価.

        Returns:
            (entry_allowed, exit_required, risk_level, reason)
        """
        days_until = (sq_date - check_date).days

        if days_until == 0:
            return (
                True,  # エントリーは可能だが注意
                False,
                EventRiskLevel.LOW,
                "SQ日当日、寄付き注意",
            )

        return True, False, EventRiskLevel.NONE, ""

    def _get_sq_date(self, year: int, month: int) -> date:
        """
        指定年月のSQ日（第2金曜日）を計算.

        Args:
            year: 年
            month: 月

        Returns:
            SQ日
        """
        cal = monthcalendar(year, month)

        # 第2金曜日を探す
        friday_count = 0
        for week in cal:
            if week[self._FRIDAY] != 0:
                friday_count += 1
                if friday_count == 2:
                    return date(year, month, week[self._FRIDAY])

        # フォールバック（理論上到達しない）
        return date(year, month, 14)

    def get_next_sq_date(self, from_date: date) -> date:
        """
        指定日以降の最も近いSQ日を取得.

        Args:
            from_date: 基準日

        Returns:
            次のSQ日
        """
        sq_date = self._get_sq_date(from_date.year, from_date.month)

        if sq_date >= from_date:
            return sq_date

        # 翌月のSQ日
        if from_date.month == 12:
            return self._get_sq_date(from_date.year + 1, 1)
        else:
            return self._get_sq_date(from_date.year, from_date.month + 1)

    def _combine_results(
        self,
        earnings_result: tuple[bool, bool, EventRiskLevel, str],
        dividend_result: tuple[bool, bool, EventRiskLevel, str],
        sq_result: tuple[bool, bool, EventRiskLevel, str],
        events: list[tuple[EventType, date, int]],
    ) -> EventCalendarResult:
        """複数イベントの結果を統合."""
        # リスクレベルの優先順位
        risk_priority = {
            EventRiskLevel.CRITICAL: 5,
            EventRiskLevel.HIGH: 4,
            EventRiskLevel.MEDIUM: 3,
            EventRiskLevel.LOW: 2,
            EventRiskLevel.NONE: 1,
        }

        results = [earnings_result, dividend_result, sq_result]

        # entry_allowed: すべてTrueの場合のみTrue
        entry_allowed = all(r[0] for r in results)

        # exit_required: いずれかTrueならTrue
        exit_required = any(r[1] for r in results)

        # risk_level: 最も高いものを採用
        max_risk = max(results, key=lambda r: risk_priority[r[2]])
        risk_level = max_risk[2]

        # reason: 最も高いリスクの理由を採用
        reason = max_risk[3] or "イベントなし"

        # nearest_event: 最も近いイベント（days_until >= 0のみ）
        future_events = [e for e in events if e[2] >= 0]
        nearest_event = None
        if future_events:
            nearest = min(future_events, key=lambda e: e[2])
            nearest_event = NearestEvent(
                event_type=nearest[0],
                event_date=nearest[1],
                days_until=nearest[2],
            )

        return EventCalendarResult(
            entry_allowed=entry_allowed,
            exit_required=exit_required,
            risk_level=risk_level,
            nearest_event=nearest_event,
            reason=reason,
        )
