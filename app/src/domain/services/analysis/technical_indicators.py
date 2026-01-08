"""Technical indicator calculation service using pandas-ta."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportUnnecessaryComparison=false
# NOTE: pandas-ta has incomplete type stubs, suppressing related errors

from dataclasses import dataclass, field

import pandas as pd
import pandas_ta as ta


@dataclass
class IndicatorCalculationResult:
    """テクニカル指標計算結果."""

    data: pd.DataFrame
    calculated_indicators: list[str] = field(default_factory=list)
    failed_indicators: dict[str, str] = field(default_factory=dict)


class TechnicalIndicatorService:
    """
    テクニカル指標計算サービス.

    pandas-taを使用してOHLCVデータからテクニカル指標を計算する。
    ステートレスなドメインサービスとして実装。
    """

    # Required lookback periods for each indicator
    LOOKBACK_PERIODS: dict[str, int] = {
        "sma_5": 5,
        "sma_25": 25,
        "sma_75": 75,
        "ema_12": 12,
        "ema_26": 26,
        "rsi_14": 15,  # RSI needs length + 1
        "stoch_k": 14,
        "stoch_d": 17,  # 14 + 3 for smoothing
        "macd": 35,  # 26 + 9 for signal
        "macd_signal": 35,
        "macd_histogram": 35,
        "bb_upper": 20,
        "bb_middle": 20,
        "bb_lower": 20,
        "bb_width": 20,
        "atr_14": 15,
        "realized_volatility": 20,
        "adx_14": 28,  # ADX typically needs 2x period
        "sar": 5,  # SAR needs minimal data
        "obv": 1,  # OBV is cumulative
        "volume_ma_20": 20,
        "volume_ratio": 20,
    }

    def calculate_all(
        self,
        df: pd.DataFrame,
        indicators: list[str] | None = None,
    ) -> IndicatorCalculationResult:
        """
        全てのテクニカル指標を計算する.

        Args:
            df: OHLCVデータを含むDataFrame
                必須カラム: open, high, low, close, volume
            indicators: 計算する指標リスト（Noneで全指標）

        Returns:
            計算結果
        """
        result_df = df.copy()
        calculated: list[str] = []
        failed: dict[str, str] = {}

        # Calculate each indicator group
        calculators: list[tuple[str, object]] = [
            ("moving_averages", self._calculate_moving_averages),
            ("momentum", self._calculate_momentum),
            ("macd", self._calculate_macd),
            ("bollinger", self._calculate_bollinger_bands),
            ("volatility", self._calculate_volatility),
            ("trend", self._calculate_trend),
            ("volume", self._calculate_volume_indicators),
        ]

        for group_name, calculator in calculators:
            try:
                indicator_df = calculator(result_df)  # type: ignore[operator]
                for col in indicator_df.columns:
                    if col not in result_df.columns:
                        result_df[col] = indicator_df[col]
                        calculated.append(col)
            except Exception as e:
                failed[group_name] = str(e)

        return IndicatorCalculationResult(
            data=result_df,
            calculated_indicators=calculated,
            failed_indicators=failed,
        )

    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """SMA/EMAを計算."""
        result = pd.DataFrame(index=df.index)

        result["sma_5"] = ta.sma(df["close"], length=5)
        result["sma_25"] = ta.sma(df["close"], length=25)
        result["sma_75"] = ta.sma(df["close"], length=75)
        result["ema_12"] = ta.ema(df["close"], length=12)
        result["ema_26"] = ta.ema(df["close"], length=26)

        return result

    def _calculate_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI, Stochasticsを計算."""
        result = pd.DataFrame(index=df.index)

        result["rsi_14"] = ta.rsi(df["close"], length=14)

        stoch = ta.stoch(df["high"], df["low"], df["close"], k=14, d=3)
        if stoch is not None and not stoch.empty:
            result["stoch_k"] = stoch.iloc[:, 0]  # STOCHk_14_3_3
            result["stoch_d"] = stoch.iloc[:, 1]  # STOCHd_14_3_3

        return result

    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """MACD関連指標を計算."""
        result = pd.DataFrame(index=df.index)

        macd_result = ta.macd(df["close"], fast=12, slow=26, signal=9)
        if macd_result is not None and not macd_result.empty:
            result["macd"] = macd_result.iloc[:, 0]  # MACD_12_26_9
            result["macd_histogram"] = macd_result.iloc[:, 1]  # MACDh_12_26_9
            result["macd_signal"] = macd_result.iloc[:, 2]  # MACDs_12_26_9

        return result

    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """ボリンジャーバンドを計算."""
        result = pd.DataFrame(index=df.index)

        bbands = ta.bbands(df["close"], length=20, std=2)
        if bbands is not None and not bbands.empty:
            result["bb_lower"] = bbands.iloc[:, 0]  # BBL_20_2.0
            result["bb_middle"] = bbands.iloc[:, 1]  # BBM_20_2.0
            result["bb_upper"] = bbands.iloc[:, 2]  # BBU_20_2.0
            # Calculate width as percentage of middle
            result["bb_width"] = (bbands.iloc[:, 2] - bbands.iloc[:, 0]) / bbands.iloc[
                :, 1
            ]

        return result

    def _calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """ATR, Realized Volatilityを計算."""
        result = pd.DataFrame(index=df.index)

        result["atr_14"] = ta.atr(df["high"], df["low"], df["close"], length=14)

        # Realized volatility: 20-day rolling std of percentage returns, annualized
        pct_returns = df["close"].pct_change()
        result["realized_volatility"] = pct_returns.rolling(window=20).std() * (
            252**0.5
        )

        return result

    def _calculate_trend(self, df: pd.DataFrame) -> pd.DataFrame:
        """ADX, Parabolic SARを計算."""
        result = pd.DataFrame(index=df.index)

        adx_result = ta.adx(df["high"], df["low"], df["close"], length=14)
        if adx_result is not None and not adx_result.empty:
            result["adx_14"] = adx_result.iloc[:, 0]  # ADX_14

        psar = ta.psar(df["high"], df["low"], df["close"])
        if psar is not None and not psar.empty:
            # PSAR returns PSARl (long) and PSARs (short) columns, combine them
            psar_long = psar.iloc[:, 0]
            psar_short = psar.iloc[:, 1]
            result["sar"] = psar_long.combine_first(psar_short)

        return result

    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """OBV, Volume MA, Volume Ratioを計算."""
        result = pd.DataFrame(index=df.index)

        result["obv"] = ta.obv(df["close"], df["volume"])
        result["volume_ma_20"] = ta.sma(df["volume"], length=20)

        # Volume ratio: current volume / 20-day average
        if result["volume_ma_20"] is not None:
            result["volume_ratio"] = df["volume"] / result["volume_ma_20"]

        return result

    def get_required_lookback(self, indicators: list[str] | None = None) -> int:
        """
        指定指標に必要な最小データ点数を返す.

        Args:
            indicators: 指標リスト（Noneで全指標）

        Returns:
            必要な最小データ点数
        """
        if indicators is None:
            return max(self.LOOKBACK_PERIODS.values())

        return max(self.LOOKBACK_PERIODS.get(ind, 0) for ind in indicators)
