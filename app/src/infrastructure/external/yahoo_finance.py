"""Yahoo Finance data source adapter using yfinance."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false
# pyright: reportArgumentType=false, reportUnknownArgumentType=false
# NOTE: yfinance has incomplete type stubs, suppressing related errors

from datetime import date
from typing import Any

import pandas as pd
import yfinance as yf

from src.shared.exceptions import StockDataFetchError


class YahooFinanceClient:
    """
    yfinanceを使用した株価データ取得アダプター.

    StockDataSource Protocolに構造的に適合する。
    """

    def __init__(
        self,
        request_timeout: int = 30,
        retry_count: int = 3,
    ) -> None:
        """
        クライアントを初期化する.

        Args:
            request_timeout: リクエストタイムアウト（秒）
            retry_count: リトライ回数
        """
        self._timeout = request_timeout
        self._retry_count = retry_count

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

        Raises:
            StockDataFetchError: データ取得に失敗した場合
        """
        self._validate_date_params(start_date, end_date, period)

        try:
            ticker = yf.Ticker(symbol)

            if period:
                df = ticker.history(period=period)
            else:
                df = ticker.history(
                    start=start_date.isoformat() if start_date else None,
                    end=end_date.isoformat() if end_date else None,
                )

            if df.empty:
                raise StockDataFetchError(
                    f"No data returned for symbol: {symbol}", symbol=symbol
                )

            return self._normalize_dataframe(df)

        except StockDataFetchError:
            raise
        except Exception as e:
            raise StockDataFetchError(
                f"Failed to fetch data for {symbol}: {e}", symbol=symbol
            ) from e

    def fetch_ticker_info(self, symbol: str) -> dict[str, Any]:
        """
        銘柄のメタ情報を取得する.

        Args:
            symbol: ティッカーシンボル

        Returns:
            銘柄情報の辞書

        Raises:
            StockDataFetchError: データ取得に失敗した場合
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName"),
                "exchange": info.get("exchange"),
                "currency": info.get("currency"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            }
        except Exception as e:
            raise StockDataFetchError(
                f"Failed to fetch info for {symbol}: {e}", symbol=symbol
            ) from e

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

        Raises:
            StockDataFetchError: データ取得に失敗した場合
        """
        self._validate_date_params(start_date, end_date, period)

        results: dict[str, pd.DataFrame] = {}

        try:
            if period:
                data = yf.download(
                    symbols, period=period, group_by="ticker", progress=False
                )
            else:
                data = yf.download(
                    symbols,
                    start=start_date.isoformat() if start_date else None,
                    end=end_date.isoformat() if end_date else None,
                    group_by="ticker",
                    progress=False,
                )

            # Handle single vs multiple symbols
            # yf.download with group_by="ticker" returns MultiIndex columns
            if len(symbols) == 1:
                if not data.empty:
                    symbol = symbols[0]
                    # Extract single symbol data from MultiIndex if present
                    if isinstance(data.columns, pd.MultiIndex):
                        df = data[symbol].dropna(how="all")
                    else:
                        df = data
                    if not df.empty:
                        results[symbol] = self._normalize_dataframe(df)
            else:
                for symbol in symbols:
                    if symbol in data.columns.get_level_values(0):
                        df = data[symbol].dropna(how="all")
                        if not df.empty:
                            results[symbol] = self._normalize_dataframe(df)

        except Exception as e:
            raise StockDataFetchError(f"Failed to fetch data for symbols: {e}") from e

        return results

    def _validate_date_params(
        self,
        start_date: date | None,
        end_date: date | None,
        period: str | None,
    ) -> None:
        """日付パラメータのバリデーション."""
        if period and (start_date or end_date):
            raise ValueError("Cannot specify both 'period' and 'start_date/end_date'")
        if not period and not start_date and not end_date:
            raise ValueError("Must specify either 'period' or 'start_date/end_date'")

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrameのカラム名を正規化."""
        # yfinance returns columns with various casing
        df.columns = [str(col).lower().replace(" ", "_") for col in df.columns]
        return df
