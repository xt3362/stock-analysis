"""決算・配当スケジュール同期サービス.

YahooFinanceClientから取得したデータをDBに永続化する。
また、DBから永続化データを取得してEventInputを構築する。
"""

from dataclasses import dataclass, field
from datetime import date

from src.domain.models.event_calendar import EventInput
from src.infrastructure.external.yahoo_finance import YahooFinanceClient
from src.infrastructure.persistence.repositories import (
    PostgresDividendScheduleRepository,
    PostgresEarningsScheduleRepository,
)


@dataclass
class SyncResult:
    """同期結果."""

    symbol: str
    earnings_synced: int = 0  # 同期した決算日の数
    dividend_synced: bool = False  # 配当情報を同期したか
    errors: list[str] = field(default_factory=lambda: [])

    @property
    def success(self) -> bool:
        """エラーがなければ成功."""
        return len(self.errors) == 0


def _estimate_fiscal_quarter(earnings_date: date) -> tuple[str, int]:
    """
    決算発表日から四半期と会計年度を推定する.

    日本企業（3月決算）を前提とした推定:
    - 4-5月発表 → Q4（本決算）
    - 7-8月発表 → Q1
    - 10-11月発表 → Q2
    - 1-2月発表 → Q3

    Args:
        earnings_date: 決算発表日

    Returns:
        (fiscal_quarter, fiscal_year) のタプル
        例: ("Q1", 2025)
    """
    month = earnings_date.month
    year = earnings_date.year

    # 発表月から四半期を推定
    if month in (4, 5, 6):
        # Q4（本決算）: 1-3月期の決算を4-5月頃発表
        return "Q4", year
    elif month in (7, 8, 9):
        # Q1: 4-6月期の決算を7-8月頃発表
        return "Q1", year + 1  # 翌年3月期
    elif month in (10, 11, 12):
        # Q2: 7-9月期の決算を10-11月頃発表
        return "Q2", year + 1
    else:  # 1, 2, 3月
        # Q3: 10-12月期の決算を1-2月頃発表
        return "Q3", year


class EventScheduleSyncService:
    """
    決算・配当スケジュール同期サービス.

    YahooFinanceClientから決算日・配当情報を取得し、
    DBに永続化する。
    """

    def __init__(
        self,
        yahoo_client: YahooFinanceClient,
        earnings_repo: PostgresEarningsScheduleRepository,
        dividend_repo: PostgresDividendScheduleRepository,
    ) -> None:
        """
        サービスを初期化する.

        Args:
            yahoo_client: Yahoo Finance APIクライアント
            earnings_repo: 決算スケジュールリポジトリ
            dividend_repo: 配当スケジュールリポジトリ
        """
        self._yahoo_client = yahoo_client
        self._earnings_repo = earnings_repo
        self._dividend_repo = dividend_repo

    def sync_symbol(
        self,
        symbol: str,
        ticker_id: int,
        earnings_limit: int = 4,
    ) -> SyncResult:
        """
        1銘柄の決算・配当スケジュールを同期する.

        Args:
            symbol: ティッカーシンボル（例: "7203.T", "AAPL"）
            ticker_id: DBのticker_id
            earnings_limit: 取得する決算日の数

        Returns:
            SyncResult: 同期結果
        """
        result = SyncResult(symbol=symbol)

        # 決算日の同期
        result = self._sync_earnings(symbol, ticker_id, earnings_limit, result)

        # 配当情報の同期
        result = self._sync_dividend(symbol, ticker_id, result)

        return result

    def _sync_earnings(
        self,
        symbol: str,
        ticker_id: int,
        limit: int,
        result: SyncResult,
    ) -> SyncResult:
        """決算日を同期する."""
        try:
            earnings_dates = self._yahoo_client.fetch_earnings_dates(
                symbol=symbol, limit=limit
            )

            for earnings_date in earnings_dates:
                # 日付から四半期・会計年度を推定
                fiscal_quarter, fiscal_year = _estimate_fiscal_quarter(earnings_date)

                self._earnings_repo.upsert(
                    ticker_id=ticker_id,
                    earnings_date=earnings_date,
                    fiscal_quarter=fiscal_quarter,
                    fiscal_year=fiscal_year,
                )
                result.earnings_synced += 1

        except Exception as e:
            result.errors.append(f"決算日取得エラー: {e}")

        return result

    def _sync_dividend(
        self,
        symbol: str,
        ticker_id: int,
        result: SyncResult,
    ) -> SyncResult:
        """配当情報を同期する."""
        try:
            dividend_info = self._yahoo_client.fetch_dividend_info(symbol=symbol)

            ex_dividend_date: date | None = dividend_info.get("ex_dividend_date")
            if ex_dividend_date is not None:
                self._dividend_repo.upsert(
                    ticker_id=ticker_id,
                    ex_dividend_date=ex_dividend_date,
                    dividend_rate=dividend_info.get("dividend_rate"),
                    dividend_yield=dividend_info.get("dividend_yield"),
                )
                result.dividend_synced = True

        except Exception as e:
            result.errors.append(f"配当情報取得エラー: {e}")

        return result

    def sync_symbols(
        self,
        symbols: list[tuple[str, int]],
        earnings_limit: int = 4,
    ) -> list[SyncResult]:
        """
        複数銘柄の決算・配当スケジュールを同期する.

        Args:
            symbols: (symbol, ticker_id) のタプルリスト
            earnings_limit: 各銘柄で取得する決算日の数

        Returns:
            list[SyncResult]: 各銘柄の同期結果
        """
        results: list[SyncResult] = []

        for symbol, ticker_id in symbols:
            result = self.sync_symbol(
                symbol=symbol,
                ticker_id=ticker_id,
                earnings_limit=earnings_limit,
            )
            results.append(result)

        return results

    def get_upcoming_earnings_date(
        self,
        ticker_id: int,
        from_date: date,
    ) -> date | None:
        """
        DBから次回決算日を取得する.

        Args:
            ticker_id: TickerID
            from_date: 基準日

        Returns:
            次回決算日、なければNone
        """
        schedule = self._earnings_repo.get_upcoming_by_ticker(ticker_id, from_date)
        if schedule is None:
            return None
        # ORMモデルからPython dateを取得（型チェッカー用にキャスト）
        earnings_date: date = schedule.earnings_date  # type: ignore[assignment]
        return earnings_date

    def get_upcoming_ex_dividend_date(
        self,
        ticker_id: int,
        from_date: date,
    ) -> date | None:
        """
        DBから次回配当落ち日を取得する.

        Args:
            ticker_id: TickerID
            from_date: 基準日

        Returns:
            次回配当落ち日、なければNone
        """
        schedule = self._dividend_repo.get_upcoming_by_ticker(ticker_id, from_date)
        if schedule is None:
            return None
        # ORMモデルからPython dateを取得（型チェッカー用にキャスト）
        ex_dividend_date: date = schedule.ex_dividend_date  # type: ignore[assignment]
        return ex_dividend_date

    def build_event_input(
        self,
        symbol: str,
        ticker_id: int,
        check_date: date,
        position_pnl: float | None = None,
    ) -> EventInput:
        """
        DBからスケジュール情報を取得してEventInputを構築する.

        Args:
            symbol: 銘柄コード
            ticker_id: TickerID
            check_date: 判定日
            position_pnl: 含み損益率（%）

        Returns:
            EventCalendarServiceに渡すEventInput
        """
        return EventInput(
            symbol=symbol,
            check_date=check_date,
            earnings_date=self.get_upcoming_earnings_date(ticker_id, check_date),
            ex_dividend_date=self.get_upcoming_ex_dividend_date(ticker_id, check_date),
            position_pnl=position_pnl,
        )
