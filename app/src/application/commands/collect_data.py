"""Command handler for data collection."""

# pyright: reportUnknownVariableType=false
# NOTE: dataclass field default_factory typing issue

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, cast

import pandas as pd

from src.shared.exceptions import StockDataFetchError

if TYPE_CHECKING:
    from src.domain.ports.stock_data_source import StockDataSource
    from src.domain.services.analysis.technical_indicators import (
        TechnicalIndicatorService,
    )
    from src.infrastructure.persistence.repositories.daily_price_repository import (
        PostgresDailyPriceRepository,
    )


@dataclass
class FetchStockDataCommand:
    """株価データ取得コマンド."""

    symbols: list[str]
    start_date: date | None = None
    end_date: date | None = None
    period: str | None = None


@dataclass
class FetchStockDataResult:
    """株価データ取得結果."""

    data: dict[str, pd.DataFrame] = field(default_factory=dict)
    success_count: int = 0
    error_count: int = 0
    errors: dict[str, str] = field(default_factory=dict)
    saved_records: dict[str, int] = field(default_factory=dict)


class CollectDataHandler:
    """
    データ収集のコマンドハンドラ.

    株価データの取得、テクニカル指標計算、データベース保存をオーケストレーションする。
    """

    def __init__(
        self,
        data_source: "StockDataSource",
        daily_price_repository: "PostgresDailyPriceRepository | None" = None,
        indicator_service: "TechnicalIndicatorService | None" = None,
    ) -> None:
        """
        ハンドラを初期化する.

        Args:
            data_source: 株価データソース
            daily_price_repository: DailyPriceリポジトリ（保存時に使用）
            indicator_service: テクニカル指標計算サービス（指標計算時に使用）
        """
        self._data_source = data_source
        self._daily_price_repository = daily_price_repository
        self._indicator_service = indicator_service

    def handle(self, command: FetchStockDataCommand) -> FetchStockDataResult:
        """
        コマンドを実行する.

        Args:
            command: 株価データ取得コマンド

        Returns:
            取得結果
        """
        result = FetchStockDataResult()

        # Try bulk fetch first
        try:
            fetched_data = self._data_source.fetch_multiple_daily_prices(
                symbols=command.symbols,
                start_date=command.start_date,
                end_date=command.end_date,
                period=command.period,
            )
            result.data = fetched_data
            result.success_count = len(fetched_data)

            # Check for symbols that weren't fetched
            for symbol in command.symbols:
                if symbol not in fetched_data:
                    result.errors[symbol] = "No data returned"
                    result.error_count += 1

        except StockDataFetchError:
            # Fall back to individual fetching on bulk failure
            for symbol in command.symbols:
                try:
                    df = self._data_source.fetch_daily_prices(
                        symbol=symbol,
                        start_date=command.start_date,
                        end_date=command.end_date,
                        period=command.period,
                    )
                    result.data[symbol] = df
                    result.success_count += 1
                except StockDataFetchError as e:
                    result.errors[symbol] = str(e)
                    result.error_count += 1

        # Prepare ticker cache for indicator calculation and saving
        ticker_cache: dict[str, int] = {}
        if self._daily_price_repository and result.data:
            ticker_cache = self._prepare_tickers(result)

        # Calculate technical indicators if service is available
        if self._indicator_service and result.data:
            self._calculate_indicators(result, ticker_cache)

        # Save to database if repository is available
        if self._daily_price_repository and result.data:
            self._save_to_database(result, ticker_cache)

        return result

    def _prepare_tickers(self, result: FetchStockDataResult) -> dict[str, int]:
        """シンボルに対応するTickerを事前取得してキャッシュを作成する."""
        ticker_cache: dict[str, int] = {}
        if self._daily_price_repository is None:
            return ticker_cache

        for symbol in result.data:
            try:
                ticker_info = self._get_ticker_info_safe(symbol)
                name: str | None = None
                if ticker_info:
                    name_value = ticker_info.get("name")
                    if isinstance(name_value, str):
                        name = name_value

                ticker = self._daily_price_repository.get_or_create_ticker(
                    symbol=symbol,
                    name=name,
                )
                ticker_cache[symbol] = cast("int", ticker.ticker_id)
            except Exception:
                # Skip this symbol if ticker creation fails
                pass

        return ticker_cache

    def _calculate_indicators(
        self,
        result: FetchStockDataResult,
        ticker_cache: dict[str, int] | None = None,
    ) -> None:
        """全シンボルに対してテクニカル指標を計算する."""
        if self._indicator_service is None:
            return

        if ticker_cache is None:
            ticker_cache = {}

        for symbol, df in result.data.items():
            try:
                # Use historical data if ticker_id is available
                ticker_id = ticker_cache.get(symbol)
                if ticker_id is not None and self._daily_price_repository is not None:
                    result.data[symbol] = self._calculate_indicators_with_historical(
                        new_data=df,
                        ticker_id=ticker_id,
                    )
                else:
                    # Fallback: calculate without historical data
                    calc_result = self._indicator_service.calculate_all(df)
                    result.data[symbol] = calc_result.data

            except Exception as e:
                # Log warning but continue with other symbols
                if symbol not in result.errors:
                    result.errors[symbol] = f"Indicator calculation warning: {e}"

    def _calculate_indicators_with_historical(
        self,
        new_data: pd.DataFrame,
        ticker_id: int,
    ) -> pd.DataFrame:
        """
        既存データと結合してテクニカル指標を計算する.

        Args:
            new_data: 新規取得データ
            ticker_id: TickerID

        Returns:
            指標計算済みDataFrame（新規データ部分のみ）
        """
        if self._daily_price_repository is None or self._indicator_service is None:
            return new_data

        # 1. Get required lookback period
        lookback_days = self._indicator_service.get_required_lookback()

        # 2. Determine start date of new data
        new_data_start = new_data.index.min()
        if hasattr(new_data_start, "date"):
            new_data_start_date = new_data_start.date()
        else:
            new_data_start_date = new_data_start

        # 3. Fetch historical data from DB
        historical_prices = (
            self._daily_price_repository.get_historical_for_indicator_calculation(
                ticker_id=ticker_id,
                new_data_start_date=new_data_start_date,
                lookback_days=lookback_days,
            )
        )

        # 4. Convert historical data to DataFrame
        historical_df = self._daily_price_repository.daily_prices_to_dataframe(
            historical_prices
        )

        # 5. Combine historical and new data
        if len(historical_df) > 0:
            combined_df = pd.concat([historical_df, new_data]).sort_index()
            # Remove duplicates, keeping the latest data
            combined_df = combined_df[~combined_df.index.duplicated(keep="last")]
        else:
            combined_df = new_data

        # 6. Calculate indicators on combined data
        calc_result = self._indicator_service.calculate_all(combined_df)

        # 7. Extract only the new data portion
        return calc_result.data.loc[new_data.index]

    def _save_to_database(
        self,
        result: FetchStockDataResult,
        ticker_cache: dict[str, int] | None = None,
    ) -> None:
        """データベースに保存する."""
        if self._daily_price_repository is None:
            return

        if ticker_cache is None:
            ticker_cache = {}

        for symbol, df in result.data.items():
            try:
                # Use cached ticker_id if available
                ticker_id = ticker_cache.get(symbol)
                if ticker_id is None:
                    # Fallback: get or create ticker
                    ticker_info = self._get_ticker_info_safe(symbol)
                    name: str | None = None
                    if ticker_info:
                        name_value = ticker_info.get("name")
                        if isinstance(name_value, str):
                            name = name_value
                    ticker = self._daily_price_repository.get_or_create_ticker(
                        symbol=symbol,
                        name=name,
                    )
                    ticker_id = cast("int", ticker.ticker_id)

                # Bulk upsert daily prices
                saved_count = self._daily_price_repository.bulk_upsert_from_dataframe(
                    ticker_id=ticker_id,
                    df=df,
                )
                result.saved_records[symbol] = saved_count

            except Exception as e:
                # Log error but don't fail the entire operation
                if symbol not in result.errors:
                    result.errors[symbol] = f"Failed to save: {e}"

    def _get_ticker_info_safe(self, symbol: str) -> dict[str, object] | None:
        """銘柄情報を安全に取得する（失敗してもNoneを返す）."""
        try:
            return self._data_source.fetch_ticker_info(symbol)
        except StockDataFetchError:
            return None
