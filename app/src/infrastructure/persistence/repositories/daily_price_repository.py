"""PostgreSQL implementation of DailyPriceRepository."""

# pyright: reportAttributeAccessIssue=false, reportUnknownVariableType=false
# NOTE: SQLAlchemy ORM Column assignment and pandas iterrows() typing issues

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import DailyPrice, Ticker

# Indicator columns that can be saved from DataFrame
INDICATOR_COLUMNS: list[str] = [
    "sma_5",
    "sma_25",
    "sma_75",
    "ema_12",
    "ema_26",
    "rsi_14",
    "stoch_k",
    "stoch_d",
    "macd",
    "macd_signal",
    "macd_histogram",
    "bb_upper",
    "bb_middle",
    "bb_lower",
    "bb_width",
    "atr_14",
    "realized_volatility",
    "adx_14",
    "sar",
    "obv",
    "volume_ma_20",
    "volume_ratio",
]

# Columns that should be stored as integers
INTEGER_COLUMNS: set[str] = {"obv", "volume_ma_20"}


class PostgresDailyPriceRepository:
    """
    PostgreSQL実装 - DailyPriceの永続化を行う.

    SQLAlchemyセッションを使用してDailyPriceエンティティの永続化を行う。
    """

    def __init__(self, session: Session) -> None:
        """
        リポジトリを初期化する.

        Args:
            session: SQLAlchemyセッション
        """
        self._session = session

    def get_by_ticker_and_date(
        self, ticker_id: int, target_date: date
    ) -> DailyPrice | None:
        """TickerIDと日付でDailyPriceを取得する."""
        return (
            self._session.query(DailyPrice)
            .filter(DailyPrice.ticker_id == ticker_id, DailyPrice.date == target_date)
            .first()
        )

    def get_by_ticker_and_date_range(
        self,
        ticker_id: int,
        start_date: date,
        end_date: date,
    ) -> list[DailyPrice]:
        """TickerIDと日付範囲でDailyPriceを取得する."""
        return list(
            self._session.query(DailyPrice)
            .filter(
                DailyPrice.ticker_id == ticker_id,
                DailyPrice.date >= start_date,
                DailyPrice.date <= end_date,
            )
            .order_by(DailyPrice.date)
            .all()
        )

    def save(self, daily_price: DailyPrice) -> DailyPrice:
        """
        DailyPriceを保存する.

        Args:
            daily_price: 保存するDailyPriceエンティティ

        Returns:
            保存されたDailyPriceエンティティ
        """
        self._session.add(daily_price)
        self._session.flush()
        return daily_price

    def bulk_upsert_from_dataframe(
        self,
        ticker_id: int,
        df: pd.DataFrame,
    ) -> int:
        """
        DataFrameからDailyPriceを一括保存（upsert）する.

        Args:
            ticker_id: TickerID
            df: 価格データを含むDataFrame
                必須カラム: open, high, low, close, volume
                オプションカラム: adj_close, 各種テクニカル指標
                index: DatetimeIndex

        Returns:
            保存されたレコード数
        """
        count = 0

        for idx, row in df.iterrows():
            # idx is DatetimeIndex, extract date
            price_date: date = (
                idx.date() if hasattr(idx, "date") else idx  # type: ignore[union-attr,assignment]
            )

            # Check if record already exists
            existing = self.get_by_ticker_and_date(ticker_id, price_date)

            if existing:
                # Update existing record - OHLCV
                existing.open = Decimal(str(row["open"]))
                existing.high = Decimal(str(row["high"]))
                existing.low = Decimal(str(row["low"]))
                existing.close = Decimal(str(row["close"]))
                existing.volume = int(row["volume"])
                if "adj_close" in row:
                    existing.adj_close = Decimal(str(row["adj_close"]))

                # Update indicator columns
                for col in INDICATOR_COLUMNS:
                    if col in row and pd.notna(row[col]):
                        setattr(existing, col, self._convert_value(col, row[col]))
            else:
                # Create new record - prepare indicator data
                indicator_data: dict[str, Any] = {}
                for col in INDICATOR_COLUMNS:
                    if col in row and pd.notna(row[col]):
                        indicator_data[col] = self._convert_value(col, row[col])

                daily_price = DailyPrice(
                    ticker_id=ticker_id,
                    date=price_date,
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=int(row["volume"]),
                    adj_close=(
                        Decimal(str(row["adj_close"])) if "adj_close" in row else None
                    ),
                    **indicator_data,
                )
                self._session.add(daily_price)

            count += 1

        self._session.flush()
        return count

    def _convert_value(self, column: str, value: float) -> Decimal | int:
        """
        カラムに応じた適切な型に値を変換する.

        Args:
            column: カラム名
            value: 変換する値

        Returns:
            変換された値（Decimalまたはint）
        """
        if column in INTEGER_COLUMNS:
            return int(value)
        return Decimal(str(value))

    def delete_by_ticker(self, ticker_id: int) -> int:
        """
        TickerIDに紐づく全てのDailyPriceを削除する.

        Args:
            ticker_id: 削除対象のTickerID

        Returns:
            削除されたレコード数
        """
        result = (
            self._session.query(DailyPrice)
            .filter(DailyPrice.ticker_id == ticker_id)
            .delete()
        )
        return result

    def get_or_create_ticker(self, symbol: str, name: str | None = None) -> Ticker:
        """
        シンボルでTickerを取得、存在しなければ作成する.

        Args:
            symbol: ティッカーシンボル
            name: 銘柄名（新規作成時に使用）

        Returns:
            Tickerエンティティ
        """
        ticker = self._session.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker is None:
            ticker = Ticker(symbol=symbol, name=name)
            self._session.add(ticker)
            self._session.flush()
        return ticker
