"""市場レジーム分析のデータモデル

市場環境を8パターンに分類し、リスク評価を行うためのモデル定義。
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Dict


class TrendType(str, Enum):
    """トレンド種別"""

    TRENDING = "trending"  # トレンド相場
    RANGING = "ranging"  # レンジ相場
    NEUTRAL = "neutral"  # 中立


class TrendDirection(str, Enum):
    """トレンド方向"""

    UPTREND = "uptrend"  # 上昇トレンド
    DOWNTREND = "downtrend"  # 下降トレンド
    SIDEWAYS = "sideways"  # 横ばい


class VolatilityLevel(str, Enum):
    """ボラティリティ水準"""

    LOW = "low"  # 低
    NORMAL = "normal"  # 通常
    ELEVATED = "elevated"  # やや高
    HIGH = "high"  # 高


class RiskLevel(str, Enum):
    """リスク水準"""

    LOW = "low"  # 低 (0-25)
    MEDIUM = "medium"  # 中 (26-50)
    HIGH = "high"  # 高 (51-75)
    EXTREME = "extreme"  # 極端 (76-100)


class EnvironmentCode(str, Enum):
    """市場環境コード（8パターン）"""

    STABLE_UPTREND = "stable_uptrend"  # 健全な上昇
    OVERHEATED_UPTREND = "overheated_uptrend"  # 過熱上昇
    VOLATILE_UPTREND = "volatile_uptrend"  # 荒れた上昇
    QUIET_RANGE = "quiet_range"  # 静かなレンジ
    VOLATILE_RANGE = "volatile_range"  # 荒れたレンジ
    CORRECTION = "correction"  # 調整局面
    STRONG_DOWNTREND = "strong_downtrend"  # 本格下降
    PANIC_SELL = "panic_sell"  # パニック売り


class Sentiment(str, Enum):
    """市場センチメント"""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class ADRDivergence(str, Enum):
    """ADRダイバージェンス"""

    BULLISH = "bullish"  # 強気（短期ADR > 中期ADR）
    BEARISH = "bearish"  # 弱気（短期ADR < 中期ADR）
    NEUTRAL = "neutral"  # 中立


@dataclass(frozen=True)
class TrendAnalysis:
    """トレンド分析結果"""

    trend_type: TrendType
    trend_direction: TrendDirection
    adx_value: float
    adx_interpretation: str  # "Strong Trend", "Weak Trend", "No Trend"


@dataclass(frozen=True)
class VolatilityAnalysis:
    """ボラティリティ分析結果"""

    volatility_level: VolatilityLevel
    atr_percent: float
    bollinger_band_width: float
    volatility_consensus: bool  # ATRとBB幅の一致


@dataclass(frozen=True)
class SentimentAnalysis:
    """センチメント分析結果"""

    sentiment: Sentiment
    nikkei_trend: TrendDirection
    topix_trend: TrendDirection


@dataclass(frozen=True)
class AdvancingDecliningRatio:
    """騰落レシオ"""

    short_term: float  # 5日ADR
    medium_term: float  # 25日ADR
    divergence: ADRDivergence


@dataclass(frozen=True)
class RiskAssessment:
    """リスク評価"""

    risk_level: RiskLevel
    risk_score: int  # 0-100

    @staticmethod
    def from_score(score: int) -> "RiskAssessment":
        """スコアからRiskAssessmentを生成"""
        clamped_score = max(0, min(100, score))
        if clamped_score <= 25:
            level = RiskLevel.LOW
        elif clamped_score <= 50:
            level = RiskLevel.MEDIUM
        elif clamped_score <= 75:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.EXTREME
        return RiskAssessment(risk_level=level, risk_score=clamped_score)


@dataclass(frozen=True)
class MarketBreadth:
    """市場ブレッドス"""

    # {"short_term": 120.5, "medium_term": 95.2}
    advancing_declining_ratios: Dict[str, float]
    adr_divergence: ADRDivergence


@dataclass(frozen=True)
class MarketRegime:
    """市場レジーム（完全な出力）"""

    analysis_date: date
    trend_analysis: TrendAnalysis
    volatility_analysis: VolatilityAnalysis
    sentiment_analysis: SentimentAnalysis
    environment_code: EnvironmentCode
    risk_assessment: RiskAssessment
    market_breadth: MarketBreadth

    @property
    def is_tradeable(self) -> bool:
        """トレード可否判定"""
        if self.environment_code in [
            EnvironmentCode.STRONG_DOWNTREND,
            EnvironmentCode.PANIC_SELL,
        ]:
            return False
        return self.risk_assessment.risk_level != RiskLevel.EXTREME


@dataclass(frozen=True)
class MarketRegimeConfig:
    """市場レジーム分析設定"""

    # トレンド設定
    adx_trending_threshold: float = 25.0
    adx_ranging_threshold: float = 20.0
    sma_period: int = 25
    sma_slope_uptrend: float = 0.06  # %/日
    sma_slope_downtrend: float = -0.06

    # ボラティリティ設定
    atr_period: int = 14
    atr_low_threshold: float = 0.8
    atr_normal_threshold: float = 2.0
    atr_elevated_threshold: float = 3.0
    bb_period: int = 20
    bb_std: float = 2.0

    # ADR設定
    adr_short_period: int = 5
    adr_medium_period: int = 25
    adr_short_panic: float = 60.0
    adr_medium_panic: float = 50.0
    adr_overbought: float = 130.0
    adr_oversold: float = 70.0
    adr_divergence_threshold: float = 10.0

    # リスクスコア配点
    risk_trend_weight: int = 40
    risk_volatility_weight: int = 30
    risk_adr_weight: int = 30
    risk_divergence_adjustment: int = 5
