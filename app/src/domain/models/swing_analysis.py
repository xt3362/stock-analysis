"""スイングトレード分析のデータモデル"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TrendScore:
    """トレンド評価スコア"""

    score: int  # 0-4点
    max_score: int
    signals: list[str]  # ["強いトレンド", "上昇トレンド（SMA5>25）"]
    adx: float
    sma5: float
    sma25: float


@dataclass(frozen=True)
class MomentumScore:
    """モメンタム評価スコア"""

    score: int  # 0-5点
    max_score: int
    signals: list[str]
    rsi: float
    macd_hist: float


@dataclass(frozen=True)
class VolumeScore:
    """出来高評価スコア"""

    score: int  # 0-3点
    max_score: int
    signals: list[str]
    ratio: float


@dataclass(frozen=True)
class ValueScore:
    """バリュエーション評価スコア"""

    score: int  # 0-6点
    max_score: int
    signals: list[str]
    pe: Optional[float]
    peg: Optional[float]
    growth: Optional[float]


@dataclass(frozen=True)
class EarningsScore:
    """決算評価スコア"""

    score: int  # 0-4点
    max_score: int
    signals: list[str]
    latest_beat: Optional[bool]  # True: Beat, False: Miss, None: データなし


@dataclass
class EntryPlan:
    """エントリープラン（価格ベース + 金額ベース）"""

    # 価格ベース情報（必須）
    entry_price: float  # エントリー価格
    stop_loss: float  # ストップロス価格
    target: Optional[float] = None  # 利確目標価格（後方互換性のためOptional）
    take_profit: Optional[float] = (
        None  # 利確目標価格（targetのエイリアス、後方互換性のため）
    )
    risk_pct: Optional[float] = None  # リスク率（%）
    reward_pct: Optional[float] = None  # リワード率（%）
    risk_reward_ratio: Optional[float] = None  # リスクリワード比

    # 戦略クラス用の追加フィールド
    position_size_suggestion: Optional[int] = None  # ポジションサイズ提案（株数）
    max_loss_per_share: Optional[float] = None  # 1株あたり最大損失
    expected_gain_per_share: Optional[float] = None  # 1株あたり期待利益
    entry_timing: Optional[str] = None  # エントリータイミング
    notes: Optional[str] = None  # 備考

    # 金額ベース情報（オプショナル）
    portfolio_size: Optional[float] = None  # 投資金額
    risk_tolerance: Optional[float] = None  # リスク許容度（%）
    position_size: Optional[int] = None  # ポジションサイズ（株数）
    max_loss_amount: Optional[float] = None  # 最大損失金額
    target_profit_amount: Optional[float] = None  # 目標利益金額
    required_capital: Optional[float] = None  # 必要資金

    # バリデーション結果（オプショナル）
    warnings: Optional[list[str]] = None  # 警告メッセージ

    def __post_init__(self):
        """targetとtake_profitの整合性を保つ"""
        # take_profitが指定されていてtargetがNoneの場合、targetに設定
        if self.take_profit is not None and self.target is None:
            self.target = self.take_profit
        # targetが指定されていてtake_profitがNoneの場合、take_profitに設定
        elif self.target is not None and self.take_profit is None:
            self.take_profit = self.target


@dataclass(frozen=True)
class ScoresSummary:
    """スコアサマリー"""

    trend: TrendScore
    momentum: MomentumScore
    volume: VolumeScore
    value: ValueScore
    earnings: EarningsScore


@dataclass(frozen=True)
class AnalysisResult:
    """分析結果"""

    symbol: str
    recommendation: str  # "強い買い ✅✅" / "買い ✅" / "様子見 ⏸️" / "見送り ❌"
    strategy: Optional[str]  # "A: トレンドフォロー" など
    scores: ScoresSummary
    risks: list[str]  # ["決算発表直前（3日後）", ...]
    entry_plan: EntryPlan
    current_price: float
    holding_period: str = "3-10日"
    strategy_score: Optional[int] = None  # 戦略スコア（100点満点）


@dataclass(frozen=True)
class AdvancedIndicatorsScore:
    """高度なテクニカル指標評価スコア"""

    score: int  # 0-10点
    max_score: int
    signals: List[str]

    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_bandwidth: Optional[float] = None
    bb_percent_b: Optional[float] = None
    bb_is_squeeze: Optional[bool] = None

    # Ichimoku
    ichimoku_tenkan: Optional[float] = None
    ichimoku_kijun: Optional[float] = None
    ichimoku_cloud_top: Optional[float] = None
    ichimoku_cloud_bottom: Optional[float] = None
    ichimoku_price_vs_cloud: Optional[str] = None  # "above", "in", "below"

    # Fibonacci
    fib_nearest_level: Optional[str] = None
    fib_distance: Optional[float] = None

    # VWAP
    vwap: Optional[float] = None
    vwap_position: Optional[str] = None  # "above" or "below"

    # OBV
    obv_trend: Optional[str] = None  # "rising", "falling", "neutral"
    obv_divergence: Optional[str] = None  # "bullish", "bearish", None


@dataclass(frozen=True)
class DetailedScoresSummary:
    """詳細分析のスコアサマリー（基本 + 高度な指標 + 複数時間軸）"""

    # 基本スコア（既存）
    trend: TrendScore
    momentum: MomentumScore
    volume: VolumeScore
    value: ValueScore
    earnings: EarningsScore

    # 高度な指標スコア
    advanced: Optional[AdvancedIndicatorsScore] = None

    # 複数時間軸スコア（alignment_scoreを追加）
    multi_timeframe_score: Optional[int] = None  # -3 to 3
    multi_timeframe_alignment: Optional[str] = None  # "strong_bullish", etc.


@dataclass(frozen=True)
class DetailedAnalysisResult:
    """詳細分析結果（swing analyzeコマンド用）"""

    # 基本情報（quickと同じ）
    symbol: str
    recommendation: str
    strategy: Optional[str]
    scores: DetailedScoresSummary  # 拡張されたスコアサマリー
    risks: List[str]
    entry_plan: EntryPlan
    current_price: float
    holding_period: str = "3-10日"

    # 詳細分析情報
    multi_timeframe_signals: Optional[List[str]] = None
    support_resistance_levels: Optional[List[Tuple[float, str]]] = None
    fibonacci_levels: Optional[Dict[str, float]] = None


@dataclass(frozen=True)
class SignalIndicator:
    """個別シグナル指標"""

    indicator: str  # 指標名（例: "BB_Lower_Touch", "Volume_Surge"）
    value: float  # 指標値
    signal: str  # シグナル内容（例: "BB下限タッチ"）


@dataclass(frozen=True)
class StrategyScore:
    """戦略スコア"""

    total_score: int  # 合計スコア
    confidence: float  # 信頼度 (0.0-1.0)
    details: Dict[str, int]  # 詳細スコア（例: {"bb_signal": 40, "volume_surge": 30}）


@dataclass
class StrategyAnalysisResult:
    """戦略分析結果（新アーキテクチャ用）"""

    symbol: str
    strategy_name: str  # 戦略名（例: "ボリンジャーバンド＋出来高戦略"）
    # "BUY" / "HOLD" / "SELL" または "強い買い" / "買い" / "様子見" / "見送り"
    recommendation: str
    score: StrategyScore  # スコアリング結果
    signals: List[SignalIndicator]  # 検出されたシグナルのリスト
    entry_plan: Optional[EntryPlan] = None  # エントリープラン（HOLDの場合はNone）
    current_price: Optional[float] = None  # 現在価格
    analysis_date: Optional[str] = None  # 分析日時（文字列形式）
    timestamp: Optional[object] = None  # 分析日時（datetime形式、後方互換性のため）
    reason: Optional[str] = None  # 推奨理由
    holding_period: str = "3-10日"
    risks: Optional[List[str]] = None  # リスク要因

    def __post_init__(self):
        """timestampとanalysis_dateの整合性を保つ"""
        # timestampが指定されていてanalysis_dateがNoneの場合
        if self.timestamp is not None and self.analysis_date is None:
            if isinstance(self.timestamp, datetime):
                self.analysis_date = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                self.analysis_date = str(self.timestamp)

        # analysis_dateが指定されていてtimestampがNoneの場合は何もしない
        # (analysis_dateは文字列なので、datetimeへの変換は行わない)
