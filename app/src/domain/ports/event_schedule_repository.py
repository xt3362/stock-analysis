"""Event schedule repository ports (interfaces)."""

from datetime import date
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.infrastructure.persistence.models import DividendSchedule, EarningsSchedule


class EarningsScheduleRepository(Protocol):
    """
    決算スケジュールリポジトリのインターフェース.

    ポート&アダプターパターンにおけるポート（抽象）として機能する。
    具体的な実装はinfrastructure層で提供される。
    """

    def get_by_ticker(
        self, ticker_id: int, limit: int = 10
    ) -> list["EarningsSchedule"]:
        """
        TickerIDで決算スケジュールを取得する（日付昇順）.

        Args:
            ticker_id: TickerID
            limit: 取得件数上限

        Returns:
            決算スケジュールのリスト
        """
        ...

    def get_upcoming_by_ticker(
        self, ticker_id: int, from_date: date
    ) -> "EarningsSchedule | None":
        """
        次回の決算発表日を取得する.

        Args:
            ticker_id: TickerID
            from_date: 基準日

        Returns:
            次回の決算スケジュール、なければNone
        """
        ...

    def save(self, schedule: "EarningsSchedule") -> "EarningsSchedule":
        """
        決算スケジュールを保存する.

        Args:
            schedule: 保存するスケジュール

        Returns:
            保存されたスケジュール
        """
        ...

    def upsert(
        self,
        ticker_id: int,
        earnings_date: date,
        **kwargs: Any,
    ) -> "EarningsSchedule":
        """
        決算スケジュールをupsertする.

        Args:
            ticker_id: TickerID
            earnings_date: 決算発表日
            **kwargs: 追加フィールド（fiscal_quarter, fiscal_year, is_confirmed等）

        Returns:
            upsertされたスケジュール
        """
        ...

    def delete_by_ticker(self, ticker_id: int) -> int:
        """
        Tickerの全決算スケジュールを削除する.

        Args:
            ticker_id: 削除対象のTickerID

        Returns:
            削除されたレコード数
        """
        ...


class DividendScheduleRepository(Protocol):
    """
    配当スケジュールリポジトリのインターフェース.

    ポート&アダプターパターンにおけるポート（抽象）として機能する。
    具体的な実装はinfrastructure層で提供される。
    """

    def get_by_ticker(
        self, ticker_id: int, limit: int = 10
    ) -> list["DividendSchedule"]:
        """
        TickerIDで配当スケジュールを取得する（日付昇順）.

        Args:
            ticker_id: TickerID
            limit: 取得件数上限

        Returns:
            配当スケジュールのリスト
        """
        ...

    def get_upcoming_by_ticker(
        self, ticker_id: int, from_date: date
    ) -> "DividendSchedule | None":
        """
        次回の配当権利確定日を取得する.

        Args:
            ticker_id: TickerID
            from_date: 基準日

        Returns:
            次回の配当スケジュール、なければNone
        """
        ...

    def save(self, schedule: "DividendSchedule") -> "DividendSchedule":
        """
        配当スケジュールを保存する.

        Args:
            schedule: 保存するスケジュール

        Returns:
            保存されたスケジュール
        """
        ...

    def upsert(
        self,
        ticker_id: int,
        ex_dividend_date: date,
        **kwargs: Any,
    ) -> "DividendSchedule":
        """
        配当スケジュールをupsertする.

        Args:
            ticker_id: TickerID
            ex_dividend_date: 配当落ち日
            **kwargs: 追加フィールド（dividend_rate, dividend_yield等）

        Returns:
            upsertされたスケジュール
        """
        ...

    def delete_by_ticker(self, ticker_id: int) -> int:
        """
        Tickerの全配当スケジュールを削除する.

        Args:
            ticker_id: 削除対象のTickerID

        Returns:
            削除されたレコード数
        """
        ...
