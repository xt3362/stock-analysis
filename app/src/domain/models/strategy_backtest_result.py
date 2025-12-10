"""戦略バックテスト結果のデータモデル"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, cast

import pandas as pd

from .backtest_result import PerformanceMetrics, Trade


@dataclass
class StrategyBacktestResult:
    """単一戦略のバックテスト結果"""

    strategy_name: str
    symbol: str
    period_start: date
    period_end: date
    trades: List[Trade]
    metrics: PerformanceMetrics
    signals_df: Optional[pd.DataFrame] = None  # 生成されたシグナル（分析用）

    @property
    def total_signals(self) -> int:
        """BUYシグナル総数"""
        if self.signals_df is None or len(self.signals_df) == 0:
            return 0
        buy_signals = cast(
            "pd.DataFrame", self.signals_df[self.signals_df["signal"] == "BUY"]
        )
        return len(buy_signals)

    @property
    def signal_to_trade_ratio(self) -> float:
        """シグナル→トレード変換率"""
        if self.total_signals == 0:
            return 0.0
        return len(self.trades) / self.total_signals
