"""騰落レシオ（ADR）計算サービス

ユニバース全銘柄の終値から騰落レシオを計算する。
"""

# pyright: reportUnknownVariableType=false
# NOTE: dataclass field default_factory type inference issue

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from src.domain.models.market_regime import ADRDivergence


@dataclass
class ADRCalculationResult:
    """ADR計算結果"""

    short_term_adr: float  # 5日ADR
    medium_term_adr: float  # 25日ADR
    divergence: ADRDivergence
    daily_advancing: "List[int]" = field(default_factory=list)  # 日ごとの上昇銘柄数
    daily_declining: "List[int]" = field(default_factory=list)  # 日ごとの下落銘柄数


class AdvancingDecliningRatioService:
    """
    騰落レシオ計算サービス.

    ユニバース全銘柄の終値から、上昇銘柄数と下落銘柄数を集計し、
    騰落レシオを計算する。

    騰落レシオ = (上昇銘柄数合計 / 下落銘柄数合計) × 100
    """

    def calculate(
        self,
        universe_prices: Dict[str, pd.DataFrame],
        short_period: int = 5,
        medium_period: int = 25,
        divergence_threshold: float = 10.0,
    ) -> ADRCalculationResult:
        """
        ユニバース全銘柄の終値から騰落レシオを計算.

        Args:
            universe_prices: 銘柄別の価格DataFrame
                {symbol: DataFrame(index=date, columns=['close'])}
            short_period: 短期ADR期間（デフォルト5日）
            medium_period: 中期ADR期間（デフォルト25日）
            divergence_threshold: ダイバージェンス判定閾値

        Returns:
            ADRCalculationResult: 計算結果
        """
        if not universe_prices:
            return ADRCalculationResult(
                short_term_adr=100.0,
                medium_term_adr=100.0,
                divergence=ADRDivergence.NEUTRAL,
            )

        # 全銘柄の終値を結合
        close_prices = self._merge_close_prices(universe_prices)

        if close_prices.empty:
            return ADRCalculationResult(
                short_term_adr=100.0,
                medium_term_adr=100.0,
                divergence=ADRDivergence.NEUTRAL,
            )

        # 日次変化を計算
        daily_changes = close_prices.pct_change()

        # 日ごとの上昇・下落銘柄数をカウント
        daily_advancing = (daily_changes > 0).sum(axis=1).tolist()
        daily_declining = (daily_changes < 0).sum(axis=1).tolist()

        # 短期ADR（直近N日分）
        short_adv = sum(daily_advancing[-short_period:])
        short_dec = sum(daily_declining[-short_period:])
        short_term_adr = self._calculate_adr(short_adv, short_dec)

        # 中期ADR（直近N日分）
        medium_adv = sum(daily_advancing[-medium_period:])
        medium_dec = sum(daily_declining[-medium_period:])
        medium_term_adr = self._calculate_adr(medium_adv, medium_dec)

        # ダイバージェンス判定
        divergence = self._determine_divergence(
            short_term_adr, medium_term_adr, divergence_threshold
        )

        return ADRCalculationResult(
            short_term_adr=short_term_adr,
            medium_term_adr=medium_term_adr,
            divergence=divergence,
            daily_advancing=daily_advancing,
            daily_declining=daily_declining,
        )

    def _merge_close_prices(
        self, universe_prices: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        全銘柄の終値を1つのDataFrameに結合.

        Args:
            universe_prices: 銘柄別の価格DataFrame

        Returns:
            結合されたDataFrame（columns=symbols, index=date）
        """
        close_series: Dict[str, pd.Series] = {}

        for symbol, df in universe_prices.items():
            if df.empty:
                continue

            if "close" in df.columns:
                close_series[symbol] = df["close"]
            elif "Close" in df.columns:
                close_series[symbol] = df["Close"]

        if not close_series:
            return pd.DataFrame()

        return pd.DataFrame(close_series)

    def _calculate_adr(self, advancing: int, declining: int) -> float:
        """
        騰落レシオを計算.

        Args:
            advancing: 上昇銘柄数合計
            declining: 下落銘柄数合計

        Returns:
            騰落レシオ（%）
        """
        if declining == 0:
            return 200.0 if advancing > 0 else 100.0
        return (advancing / declining) * 100

    def _determine_divergence(
        self,
        short_term: float,
        medium_term: float,
        threshold: float,
    ) -> ADRDivergence:
        """
        ダイバージェンスを判定.

        Args:
            short_term: 短期ADR
            medium_term: 中期ADR
            threshold: 閾値

        Returns:
            ADRDivergence
        """
        diff = short_term - medium_term

        if diff > threshold:
            return ADRDivergence.BULLISH
        elif diff < -threshold:
            return ADRDivergence.BEARISH
        else:
            return ADRDivergence.NEUTRAL
