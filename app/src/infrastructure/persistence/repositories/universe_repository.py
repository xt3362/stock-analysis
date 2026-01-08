"""PostgreSQL implementation of UniverseRepository."""

# pyright: reportAttributeAccessIssue=false, reportUnknownVariableType=false
# pyright: reportArgumentType=false
# NOTE: SQLAlchemy ORM typing issues

from datetime import date
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import (
    DailyPrice,
    Ticker,
    Universe,
    UniverseSymbol,
)


class PostgresUniverseRepository:
    """
    PostgreSQL実装 - Universeの永続化を行う.

    SQLAlchemyセッションを使用してUniverseエンティティの永続化と
    関連するシンボル・価格データの取得を行う。
    """

    def __init__(self, session: Session) -> None:
        """
        リポジトリを初期化する.

        Args:
            session: SQLAlchemyセッション
        """
        self._session = session

    def get_by_id(self, universe_id: int) -> Universe | None:
        """IDでUniverseを取得する."""
        return (
            self._session.query(Universe)
            .filter(Universe.universe_id == universe_id)
            .first()
        )

    def get_by_name(self, name: str) -> Universe | None:
        """名前でUniverseを取得する."""
        return self._session.query(Universe).filter(Universe.name == name).first()

    def get_latest(self) -> Universe | None:
        """最新のUniverseを取得する（作成日時が最も新しいもの）."""
        return (
            self._session.query(Universe).order_by(Universe.created_at.desc()).first()
        )

    def get_symbols(self, universe_id: int) -> List[str]:
        """
        Universe内の全シンボルを取得する.

        Args:
            universe_id: UniverseのID

        Returns:
            シンボルのリスト
        """
        results = (
            self._session.query(Ticker.symbol)
            .join(UniverseSymbol, Ticker.ticker_id == UniverseSymbol.ticker_id)
            .filter(UniverseSymbol.universe_id == universe_id)
            .all()
        )
        return [row[0] for row in results]

    def get_ticker_ids(self, universe_id: int) -> List[int]:
        """
        Universe内の全TickerIDを取得する.

        Args:
            universe_id: UniverseのID

        Returns:
            TickerIDのリスト
        """
        results = (
            self._session.query(UniverseSymbol.ticker_id)
            .filter(UniverseSymbol.universe_id == universe_id)
            .all()
        )
        return [row[0] for row in results]

    def get_universe_prices(
        self,
        universe_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.DataFrame]:
        """
        Universe内の全銘柄の価格データを取得する.

        Args:
            universe_id: UniverseのID
            start_date: 取得開始日
            end_date: 取得終了日

        Returns:
            銘柄別の価格DataFrame {symbol: DataFrame(columns=['close'])}
        """
        # ユニバース内の全銘柄の価格データを一括取得
        results = (
            self._session.query(
                Ticker.symbol,
                DailyPrice.date,
                DailyPrice.close,
            )
            .join(UniverseSymbol, Ticker.ticker_id == UniverseSymbol.ticker_id)
            .join(DailyPrice, Ticker.ticker_id == DailyPrice.ticker_id)
            .filter(
                UniverseSymbol.universe_id == universe_id,
                DailyPrice.date >= start_date,
                DailyPrice.date <= end_date,
            )
            .order_by(Ticker.symbol, DailyPrice.date)
            .all()
        )

        # シンボルごとにグループ化
        symbol_data: Dict[str, List[Dict[str, Any]]] = {}
        for symbol, price_date, close in results:
            if symbol not in symbol_data:
                symbol_data[symbol] = []
            symbol_data[symbol].append(
                {
                    "date": price_date,
                    "close": float(close),
                }
            )

        # DataFrameに変換
        universe_prices: Dict[str, pd.DataFrame] = {}
        for symbol, data in symbol_data.items():
            df = pd.DataFrame(data)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
                universe_prices[symbol] = df

        return universe_prices

    def save(self, universe: Universe) -> Universe:
        """
        Universeを保存する.

        Args:
            universe: 保存するUniverseエンティティ

        Returns:
            保存されたUniverseエンティティ
        """
        self._session.add(universe)
        self._session.flush()
        return universe

    def add_symbol(self, universe_id: int, ticker_id: int) -> UniverseSymbol:
        """
        UniverseにシンボルをTickerを追加する.

        Args:
            universe_id: UniverseのID
            ticker_id: 追加するTickerのID

        Returns:
            作成されたUniverseSymbolエンティティ
        """
        universe_symbol = UniverseSymbol(
            universe_id=universe_id,
            ticker_id=ticker_id,
        )
        self._session.add(universe_symbol)
        self._session.flush()
        return universe_symbol

    def remove_symbol(self, universe_id: int, ticker_id: int) -> bool:
        """
        UniverseからシンボルをTickerを削除する.

        Args:
            universe_id: UniverseのID
            ticker_id: 削除するTickerのID

        Returns:
            削除成功時はTrue
        """
        result = (
            self._session.query(UniverseSymbol)
            .filter(
                UniverseSymbol.universe_id == universe_id,
                UniverseSymbol.ticker_id == ticker_id,
            )
            .delete()
        )
        return result > 0
