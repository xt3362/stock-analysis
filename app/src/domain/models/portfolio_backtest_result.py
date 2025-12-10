"""ポートフォリオバックテスト結果のデータモデル"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from .backtest_result import PerformanceMetrics, Trade


@dataclass(frozen=True)
class DailyPortfolioState:
    """日次ポートフォリオ状態"""

    date: date
    total_value: float  # ポートフォリオ総額
    cash: float  # 現金
    positions_count: int  # 保有銘柄数
    active_symbols: List[str]  # 保有銘柄リスト


@dataclass(frozen=True)
class DailyMarketEnvironment:
    """日次市場環境情報"""

    date: date
    environment: str  # 8パターン分類コード
    risk_level: str
    risk_score: int  # 0-100
    trend_direction: str
    volatility_level: str
    adx_value: float
    atr_pct: float


@dataclass(frozen=True)
class PortfolioPerformanceMetrics(PerformanceMetrics):
    """ポートフォリオパフォーマンス指標

    基本的な PerformanceMetrics を継承し、ポートフォリオ固有の指標を追加
    """

    # ポートフォリオ固有のメトリクス
    avg_positions_held: Optional[float] = None  # 平均保有銘柄数
    max_positions_held: Optional[int] = None  # 最大同時保有銘柄数
    position_utilization_rate: Optional[float] = None  # ポジション利用率（%）

    # 銘柄別パフォーマンス
    symbol_performance: Optional[Dict[str, Dict[str, float]]] = None  # 銘柄別統計


@dataclass(frozen=True)
class PortfolioBacktestResult:
    """ポートフォリオバックテスト結果全体"""

    period_start: date
    period_end: date
    trades: List[Trade]
    metrics: PortfolioPerformanceMetrics
    daily_states: List[DailyPortfolioState]  # 日次ポートフォリオ状態の履歴
    initial_capital: float
    final_value: float
    daily_market_environments: List[DailyMarketEnvironment] = field(
        default_factory=lambda: []
    )  # 日次市場環境の履歴
