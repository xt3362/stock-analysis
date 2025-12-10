"""バックテスト結果のデータモデル"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass(frozen=True)
class Trade:
    """個別取引の記録"""

    symbol: str
    entry_date: date
    entry_price: float
    stop_loss: float
    take_profit: float
    exit_date: date
    exit_price: float
    exit_reason: str  # "stop_loss", "take_profit", "timeout"
    pnl_pct: float  # 損益率（%）
    holding_days: int
    recommendation: str  # "強い買い", "買い"
    strategy: str  # "A: トレンドフォロー", etc.
    score: int  # 総合スコア

    # 追加フィールド（資金・損益関連）
    shares: Optional[int] = None  # 取引株数
    position_value: Optional[float] = None  # 投資額（円）
    pnl_amount: Optional[float] = None  # 損益額（円）
    exit_value: Optional[float] = None  # 受取額（円）

    # 追加フィールド（リスク・価格関連）
    risk_reward_ratio: Optional[float] = None  # 実現R:R比
    atr_pct: Optional[float] = None  # エントリー時ATR%
    raw_entry_price: Optional[float] = None  # スリッページ前エントリー価格
    raw_exit_price: Optional[float] = None  # スリッページ前エグジット価格

    # 追加フィールド（スコア・戦略関連）
    rank: Optional[str] = None  # スコアランク (S/A/B/C/D)
    strategy_confidence: Optional[float] = None  # 戦略信頼度
    market_regime_score: Optional[float] = None  # 市場環境スコア
    indicator_score: Optional[float] = None  # テクニカル指標スコア

    # 追加フィールド（エントリー時market_regimeラベル）
    entry_market_environment: Optional[str] = None  # 8パターン分類
    entry_market_risk_level: Optional[str] = None  # リスクレベル
    entry_market_trend_direction: Optional[str] = None  # トレンド方向
    entry_market_volatility_level: Optional[str] = None  # ボラティリティレベル
    entry_market_risk_score: Optional[int] = None  # リスクスコア
    entry_market_adx_value: Optional[float] = None  # ADX値
    entry_market_atr_percent: Optional[float] = None  # 市場全体ATR%

    # 追加フィールド（イグジット時market_regimeラベル）
    exit_market_environment: Optional[str] = None  # 8パターン分類
    exit_market_risk_level: Optional[str] = None  # リスクレベル
    exit_market_trend_direction: Optional[str] = None  # トレンド方向
    exit_market_volatility_level: Optional[str] = None  # ボラティリティレベル
    exit_market_risk_score: Optional[int] = None  # リスクスコア
    exit_market_adx_value: Optional[float] = None  # ADX値
    exit_market_atr_percent: Optional[float] = None  # 市場全体ATR%


@dataclass(frozen=True)
class PerformanceMetrics:
    """パフォーマンス指標"""

    # 基本メトリクス
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # 勝率（0.0-1.0）
    avg_return: float  # 平均リターン（%）
    total_return: float  # 累積リターン（%）
    avg_holding_days: float  # 平均保有期間（日）

    # 高度なメトリクス
    max_drawdown_pct: Optional[float] = None  # 最大ドローダウン（%）
    max_drawdown_duration_days: Optional[int] = None  # 最大ドローダウン継続期間（日）
    recovery_time_days: Optional[int] = None  # 回復期間（日）
    current_drawdown_pct: Optional[float] = None  # 現在のドローダウン（%）

    sharpe_ratio: Optional[float] = None  # シャープレシオ
    sortino_ratio: Optional[float] = None  # ソルティノレシオ
    profit_factor: Optional[float] = None  # プロフィットファクター（総利益/総損失）
    expectancy: Optional[float] = None  # 期待値（%）


@dataclass(frozen=True)
class BacktestResult:
    """バックテスト結果全体"""

    symbol: str
    period_start: date
    period_end: date
    trades: List[Trade]
    metrics: PerformanceMetrics
