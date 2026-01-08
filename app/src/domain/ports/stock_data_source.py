"""Stock data source port (interface)."""

from datetime import date
from typing import Any, Protocol

import pandas as pd


class StockDataSource(Protocol):
    """
    株価データソースのインターフェース.

    ポート&アダプターパターンにおけるポート（抽象）として機能する。
    具体的な実装（yfinance, Bloomberg API等）はinfrastructure層で提供される。
    """

    def fetch_daily_prices(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
        period: str | None = None,
    ) -> pd.DataFrame:
        """
        指定銘柄の日足データを取得する.

        Args:
            symbol: ティッカーシンボル (例: "7203.T", "AAPL")
            start_date: 取得開始日 (periodと排他)
            end_date: 取得終了日 (periodと排他)
            period: 取得期間 (例: "1mo", "1y") (start_date/end_dateと排他)

        Returns:
            OHLCV データを含む DataFrame
            columns: ['open', 'high', 'low', 'close', 'adj_close', 'volume']
            index: DatetimeIndex

        Raises:
            StockDataFetchError: データ取得に失敗した場合
        """
        ...

    def fetch_ticker_info(self, symbol: str) -> dict[str, Any]:
        """
        銘柄のメタ情報を取得する.

        Args:
            symbol: ティッカーシンボル

        Returns:
            銘柄情報の辞書 (name, exchange, sector, industry, etc.)

        Raises:
            StockDataFetchError: データ取得に失敗した場合
        """
        ...

    def fetch_multiple_daily_prices(
        self,
        symbols: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
        period: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        複数銘柄の日足データを一括取得する.

        Args:
            symbols: ティッカーシンボルのリスト
            start_date: 取得開始日
            end_date: 取得終了日
            period: 取得期間

        Returns:
            シンボルをキーとしたDataFrameの辞書
        """
        ...
