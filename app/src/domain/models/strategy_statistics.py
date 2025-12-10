"""戦略別統計のデータモデル"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StrategyStatistics:
    """戦略別統計データクラス"""

    strategy_name: str

    # 基本指標
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # 勝率（0.0-1.0）
    avg_pnl_pct: float  # 平均PnL%
    avg_holding_days: float  # 平均保有日数

    # リスク指標
    sharpe_ratio: Optional[float]  # シャープレシオ
    sortino_ratio: Optional[float]  # ソルティノレシオ
    max_drawdown_pct: Optional[float]  # 最大ドローダウン%
    pnl_std_dev: float  # PnL%の標準偏差

    # 収益性指標
    total_pnl_amount: float  # 総損益額（円）
    gross_profit: float  # 総利益（円）
    gross_loss: float  # 総損失（円）
    profit_factor: Optional[float]  # プロフィットファクター
    avg_win_amount: float  # 平均勝ち額（円）
    avg_loss_amount: float  # 平均負け額（円）


@dataclass(frozen=True)
class MarketEnvironmentBreakdown:
    """市場環境別統計データクラス"""

    strategy_name: str
    market_environment: str  # 8パターン分類

    # 統計情報
    total_trades: int
    winning_trades: int
    win_rate: float  # 勝率（0.0-1.0）
    avg_pnl_pct: float  # 平均PnL%
    total_pnl_amount: float  # 総損益額（円）
    avg_holding_days: float  # 平均保有日数
