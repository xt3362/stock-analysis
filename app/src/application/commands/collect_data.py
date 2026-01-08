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

        # Calculate technical indicators if service is available
        if self._indicator_service and result.data:
            self._calculate_indicators(result)

        # Save to database if repository is available
        if self._daily_price_repository and result.data:
            self._save_to_database(result)

        return result

    def _calculate_indicators(self, result: FetchStockDataResult) -> None:
        """全シンボルに対してテクニカル指標を計算する."""
        if self._indicator_service is None:
            return

        for symbol, df in result.data.items():
            try:
                calc_result = self._indicator_service.calculate_all(df)
                result.data[symbol] = calc_result.data

                # Log any failed indicator groups (but don't treat as errors)
                if calc_result.failed_indicators:
                    # Optionally track partial failures
                    pass

            except Exception as e:
                # Log warning but continue with other symbols
                if symbol not in result.errors:
                    result.errors[symbol] = f"Indicator calculation warning: {e}"

    def _save_to_database(self, result: FetchStockDataResult) -> None:
        """データベースに保存する."""
        if self._daily_price_repository is None:
            return

        for symbol, df in result.data.items():
            try:
                # Get or create ticker
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

                # Bulk upsert daily prices
                saved_count = self._daily_price_repository.bulk_upsert_from_dataframe(
                    ticker_id=cast("int", ticker.ticker_id),
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
