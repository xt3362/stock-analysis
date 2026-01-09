"""PostgreSQL implementation of Event Schedule Repositories."""

# pyright: reportAttributeAccessIssue=false, reportUnknownVariableType=false
# pyright: reportArgumentType=false, reportUnnecessaryComparison=false
# NOTE: SQLAlchemy ORM Column assignment typing issues

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import DividendSchedule, EarningsSchedule


class PostgresEarningsScheduleRepository:
    """
    PostgreSQL実装 - 決算スケジュールの永続化を行う.

    SQLAlchemyセッションを使用してEarningsScheduleエンティティの永続化を行う。
    """

    def __init__(self, session: Session) -> None:
        """
        リポジトリを初期化する.

        Args:
            session: SQLAlchemyセッション
        """
        self._session = session

    def get_by_ticker(self, ticker_id: int, limit: int = 10) -> list[EarningsSchedule]:
        """
        TickerIDで決算スケジュールを取得する（日付昇順）.

        Args:
            ticker_id: TickerID
            limit: 取得件数上限

        Returns:
            決算スケジュールのリスト
        """
        return list(
            self._session.query(EarningsSchedule)
            .filter(EarningsSchedule.ticker_id == ticker_id)
            .order_by(EarningsSchedule.earnings_date)
            .limit(limit)
            .all()
        )

    def get_upcoming_by_ticker(
        self, ticker_id: int, from_date: date
    ) -> EarningsSchedule | None:
        """
        次回の決算発表日を取得する.

        Args:
            ticker_id: TickerID
            from_date: 基準日

        Returns:
            次回の決算スケジュール、なければNone
        """
        return (
            self._session.query(EarningsSchedule)
            .filter(
                EarningsSchedule.ticker_id == ticker_id,
                EarningsSchedule.earnings_date >= from_date,
            )
            .order_by(EarningsSchedule.earnings_date)
            .first()
        )

    def save(self, schedule: EarningsSchedule) -> EarningsSchedule:
        """
        決算スケジュールを保存する.

        Args:
            schedule: 保存するスケジュール

        Returns:
            保存されたスケジュール
        """
        self._session.add(schedule)
        self._session.flush()
        return schedule

    def upsert(
        self,
        ticker_id: int,
        earnings_date: date,
        fiscal_quarter: str | None = None,
        fiscal_year: int | None = None,
        is_confirmed: bool = False,
    ) -> EarningsSchedule:
        """
        決算スケジュールをupsertする.

        Args:
            ticker_id: TickerID
            earnings_date: 決算発表日
            fiscal_quarter: 決算期（"Q1", "Q2", "Q3", "Q4"）
            fiscal_year: 決算年度
            is_confirmed: 確定日かどうか

        Returns:
            upsertされたスケジュール
        """
        existing = (
            self._session.query(EarningsSchedule)
            .filter(
                EarningsSchedule.ticker_id == ticker_id,
                EarningsSchedule.earnings_date == earnings_date,
            )
            .first()
        )

        now = datetime.now(tz=timezone.utc)

        if existing:
            # Update existing record
            if fiscal_quarter is not None:
                existing.fiscal_quarter = fiscal_quarter
            if fiscal_year is not None:
                existing.fiscal_year = fiscal_year
            existing.is_confirmed = is_confirmed
            existing.retrieved_at = now
            self._session.flush()
            return existing
        else:
            # Create new record
            schedule = EarningsSchedule(
                ticker_id=ticker_id,
                earnings_date=earnings_date,
                fiscal_quarter=fiscal_quarter,
                fiscal_year=fiscal_year,
                is_confirmed=is_confirmed,
                retrieved_at=now,
            )
            self._session.add(schedule)
            self._session.flush()
            return schedule

    def delete_by_ticker(self, ticker_id: int) -> int:
        """
        Tickerの全決算スケジュールを削除する.

        Args:
            ticker_id: 削除対象のTickerID

        Returns:
            削除されたレコード数
        """
        result = (
            self._session.query(EarningsSchedule)
            .filter(EarningsSchedule.ticker_id == ticker_id)
            .delete()
        )
        return result


class PostgresDividendScheduleRepository:
    """
    PostgreSQL実装 - 配当スケジュールの永続化を行う.

    SQLAlchemyセッションを使用してDividendScheduleエンティティの永続化を行う。
    """

    def __init__(self, session: Session) -> None:
        """
        リポジトリを初期化する.

        Args:
            session: SQLAlchemyセッション
        """
        self._session = session

    def get_by_ticker(self, ticker_id: int, limit: int = 10) -> list[DividendSchedule]:
        """
        TickerIDで配当スケジュールを取得する（日付昇順）.

        Args:
            ticker_id: TickerID
            limit: 取得件数上限

        Returns:
            配当スケジュールのリスト
        """
        return list(
            self._session.query(DividendSchedule)
            .filter(DividendSchedule.ticker_id == ticker_id)
            .order_by(DividendSchedule.ex_dividend_date)
            .limit(limit)
            .all()
        )

    def get_upcoming_by_ticker(
        self, ticker_id: int, from_date: date
    ) -> DividendSchedule | None:
        """
        次回の配当権利確定日を取得する.

        Args:
            ticker_id: TickerID
            from_date: 基準日

        Returns:
            次回の配当スケジュール、なければNone
        """
        return (
            self._session.query(DividendSchedule)
            .filter(
                DividendSchedule.ticker_id == ticker_id,
                DividendSchedule.ex_dividend_date >= from_date,
            )
            .order_by(DividendSchedule.ex_dividend_date)
            .first()
        )

    def save(self, schedule: DividendSchedule) -> DividendSchedule:
        """
        配当スケジュールを保存する.

        Args:
            schedule: 保存するスケジュール

        Returns:
            保存されたスケジュール
        """
        self._session.add(schedule)
        self._session.flush()
        return schedule

    def upsert(
        self,
        ticker_id: int,
        ex_dividend_date: date,
        dividend_rate: float | None = None,
        dividend_yield: float | None = None,
    ) -> DividendSchedule:
        """
        配当スケジュールをupsertする.

        Args:
            ticker_id: TickerID
            ex_dividend_date: 配当落ち日
            dividend_rate: 1株あたり配当額
            dividend_yield: 配当利回り（小数）

        Returns:
            upsertされたスケジュール
        """
        existing = (
            self._session.query(DividendSchedule)
            .filter(
                DividendSchedule.ticker_id == ticker_id,
                DividendSchedule.ex_dividend_date == ex_dividend_date,
            )
            .first()
        )

        now = datetime.now(tz=timezone.utc)

        if existing:
            # Update existing record
            if dividend_rate is not None:
                existing.dividend_rate = Decimal(str(dividend_rate))
            if dividend_yield is not None:
                existing.dividend_yield = Decimal(str(dividend_yield))
            existing.retrieved_at = now
            self._session.flush()
            return existing
        else:
            # Create new record
            schedule = DividendSchedule(
                ticker_id=ticker_id,
                ex_dividend_date=ex_dividend_date,
                dividend_rate=Decimal(str(dividend_rate))
                if dividend_rate is not None
                else None,
                dividend_yield=Decimal(str(dividend_yield))
                if dividend_yield is not None
                else None,
                retrieved_at=now,
            )
            self._session.add(schedule)
            self._session.flush()
            return schedule

    def delete_by_ticker(self, ticker_id: int) -> int:
        """
        Tickerの全配当スケジュールを削除する.

        Args:
            ticker_id: 削除対象のTickerID

        Returns:
            削除されたレコード数
        """
        result = (
            self._session.query(DividendSchedule)
            .filter(DividendSchedule.ticker_id == ticker_id)
            .delete()
        )
        return result
