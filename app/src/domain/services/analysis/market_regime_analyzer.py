"""市場レジーム分析サービス

市場環境を分析し、8パターンに分類してリスク評価を行う。
"""

from datetime import date
from typing import Dict, Optional

import pandas as pd

from src.domain.models.market_regime import (
    ADRDivergence,
    AdvancingDecliningRatio,
    EnvironmentCode,
    MarketBreadth,
    MarketRegime,
    MarketRegimeConfig,
    RiskAssessment,
    Sentiment,
    SentimentAnalysis,
    TrendAnalysis,
    TrendDirection,
    TrendType,
    VolatilityAnalysis,
    VolatilityLevel,
)
from src.domain.services.analysis.advancing_declining_ratio import (
    AdvancingDecliningRatioService,
)
from src.domain.services.analysis.technical_indicators import TechnicalIndicatorService


class MarketRegimeAnalyzer:
    """
    市場レジーム分析サービス.

    入力:
    - 市場指数価格（日経225 ETF, TOPIX ETF）60日分
    - ユニバース銘柄価格（ADR計算用）25日分

    出力:
    - MarketRegime値オブジェクト（8パターン分類 + リスクスコア）
    """

    def __init__(
        self,
        technical_indicator_service: Optional[TechnicalIndicatorService] = None,
        adr_service: Optional[AdvancingDecliningRatioService] = None,
        config: Optional[MarketRegimeConfig] = None,
    ) -> None:
        """
        コンストラクタ.

        Args:
            technical_indicator_service: テクニカル指標計算サービス
            adr_service: 騰落レシオ計算サービス
            config: 分析設定（Noneでデフォルト）
        """
        self._technical_service = (
            technical_indicator_service or TechnicalIndicatorService()
        )
        self._adr_service = adr_service or AdvancingDecliningRatioService()
        self._config = config or MarketRegimeConfig()

    def analyze(
        self,
        nikkei_df: pd.DataFrame,
        topix_df: pd.DataFrame,
        universe_prices: Dict[str, pd.DataFrame],
        end_date: Optional[date] = None,
    ) -> MarketRegime:
        """
        市場レジームを分析する.

        Args:
            nikkei_df: 日経225 ETF (1321.T) OHLCV データ
            topix_df: TOPIX ETF (1306.T) OHLCV データ
            universe_prices: ユニバース全銘柄の価格データ（ADR計算用）
            end_date: 分析基準日（Noneで最新日付）

        Returns:
            MarketRegime: 分析結果
        """
        # 基準日の決定
        analysis_date = end_date or self._get_latest_date(nikkei_df)

        # テクニカル指標計算（日経225をメイン分析対象とする）
        nikkei_indicators = self._technical_service.calculate_all(nikkei_df)
        topix_indicators = self._technical_service.calculate_all(topix_df)

        # トレンド分析
        nikkei_trend = self._analyze_trend(nikkei_indicators.data)
        topix_trend_direction = self._get_trend_direction(topix_indicators.data)

        # ボラティリティ分析
        volatility = self._analyze_volatility(nikkei_indicators.data)

        # センチメント分析
        sentiment = self._analyze_sentiment(
            nikkei_trend.trend_direction, topix_trend_direction
        )

        # ADR計算
        adr_result = self._adr_service.calculate(
            universe_prices,
            short_period=self._config.adr_short_period,
            medium_period=self._config.adr_medium_period,
            divergence_threshold=self._config.adr_divergence_threshold,
        )

        adr = AdvancingDecliningRatio(
            short_term=adr_result.short_term_adr,
            medium_term=adr_result.medium_term_adr,
            divergence=adr_result.divergence,
        )

        # 環境分類
        environment = self._classify_environment(nikkei_trend, volatility, adr)

        # リスクスコア計算
        risk_score = self._calculate_risk_score(nikkei_trend, volatility, adr)
        risk_assessment = RiskAssessment.from_score(risk_score)

        # 市場ブレッドス
        market_breadth = MarketBreadth(
            advancing_declining_ratios={
                "short_term": adr.short_term,
                "medium_term": adr.medium_term,
            },
            adr_divergence=adr.divergence,
        )

        return MarketRegime(
            analysis_date=analysis_date,
            trend_analysis=nikkei_trend,
            volatility_analysis=volatility,
            sentiment_analysis=sentiment,
            environment_code=environment,
            risk_assessment=risk_assessment,
            market_breadth=market_breadth,
        )

    def _get_latest_date(self, df: pd.DataFrame) -> date:
        """DataFrameの最新日付を取得."""
        if df.index.name == "date" or isinstance(df.index, pd.DatetimeIndex):
            last_idx = df.index[-1]
            return last_idx.date() if hasattr(last_idx, "date") else last_idx
        return date.today()

    def _analyze_trend(self, df: pd.DataFrame) -> TrendAnalysis:
        """
        トレンド分析.

        ADX値とSMA傾きからトレンド種別・方向を判定する。
        """
        # ADX値の取得
        adx_value = self._get_latest_value(df, "adx_14", 20.0)

        # トレンド種別の判定
        if adx_value >= self._config.adx_trending_threshold:
            trend_type = TrendType.TRENDING
            adx_interpretation = "Strong Trend"
        elif adx_value >= self._config.adx_ranging_threshold:
            trend_type = TrendType.NEUTRAL
            adx_interpretation = "Weak Trend"
        else:
            trend_type = TrendType.RANGING
            adx_interpretation = "No Trend"

        # トレンド方向の判定（SMA傾き）
        trend_direction = self._get_trend_direction(df)

        return TrendAnalysis(
            trend_type=trend_type,
            trend_direction=trend_direction,
            adx_value=adx_value,
            adx_interpretation=adx_interpretation,
        )

    def _get_trend_direction(self, df: pd.DataFrame) -> TrendDirection:
        """SMA傾きからトレンド方向を判定."""
        sma_col = f"sma_{self._config.sma_period}"

        if sma_col not in df.columns:
            # SMAがない場合は終値の変化で判定
            if "close" in df.columns and len(df) >= 5:
                recent_close = df["close"].iloc[-5:]
                change = recent_close.iloc[-1] - recent_close.iloc[0]
                slope = change / recent_close.iloc[0] * 100 / 5
            else:
                return TrendDirection.SIDEWAYS
        else:
            # SMA傾きを計算（直近5日間の変化率/日）
            sma = df[sma_col].dropna()
            if len(sma) < 5:
                return TrendDirection.SIDEWAYS
            slope = (sma.iloc[-1] - sma.iloc[-5]) / sma.iloc[-5] * 100 / 5

        if slope > self._config.sma_slope_uptrend:
            return TrendDirection.UPTREND
        elif slope < self._config.sma_slope_downtrend:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS

    def _analyze_volatility(self, df: pd.DataFrame) -> VolatilityAnalysis:
        """
        ボラティリティ分析.

        ATR%とボリンジャーバンド幅から判定する。
        """
        # ATR%の計算
        atr = self._get_latest_value(df, "atr_14", 0.0)
        close = self._get_latest_value(df, "close", 1.0)
        atr_percent = (atr / close) * 100 if close > 0 else 0.0

        # ボリンジャーバンド幅
        bb_width = self._get_latest_value(df, "bb_width", 0.0) * 100  # %に変換

        # ボラティリティレベル判定
        if atr_percent < self._config.atr_low_threshold:
            vol_level = VolatilityLevel.LOW
        elif atr_percent < self._config.atr_normal_threshold:
            vol_level = VolatilityLevel.NORMAL
        elif atr_percent < self._config.atr_elevated_threshold:
            vol_level = VolatilityLevel.ELEVATED
        else:
            vol_level = VolatilityLevel.HIGH

        # ATRとBB幅の一致判定
        # 両方が同じ傾向を示しているかチェック
        bb_is_high = bb_width > 10.0  # BB幅10%以上は高い
        atr_is_high = atr_percent >= self._config.atr_elevated_threshold
        volatility_consensus = bb_is_high == atr_is_high

        return VolatilityAnalysis(
            volatility_level=vol_level,
            atr_percent=atr_percent,
            bollinger_band_width=bb_width,
            volatility_consensus=volatility_consensus,
        )

    def _analyze_sentiment(
        self,
        nikkei_trend: TrendDirection,
        topix_trend: TrendDirection,
    ) -> SentimentAnalysis:
        """
        センチメント分析.

        日経225とTOPIXのトレンド方向から市場センチメントを判定する。
        """
        # 両方上昇ならPOSITIVE、両方下落ならNEGATIVE、それ以外はNEUTRAL
        both_up = (
            nikkei_trend == TrendDirection.UPTREND
            and topix_trend == TrendDirection.UPTREND
        )
        both_down = (
            nikkei_trend == TrendDirection.DOWNTREND
            and topix_trend == TrendDirection.DOWNTREND
        )

        if both_up:
            sentiment = Sentiment.POSITIVE
        elif both_down:
            sentiment = Sentiment.NEGATIVE
        else:
            sentiment = Sentiment.NEUTRAL

        return SentimentAnalysis(
            sentiment=sentiment,
            nikkei_trend=nikkei_trend,
            topix_trend=topix_trend,
        )

    def _classify_environment(
        self,
        trend: TrendAnalysis,
        volatility: VolatilityAnalysis,
        adr: AdvancingDecliningRatio,
    ) -> EnvironmentCode:
        """
        市場環境を8パターンに分類.

        | コード | 条件 |
        |--------|------|
        | STABLE_UPTREND | 上昇 + 低〜通常Vol + 正常ADR |
        | OVERHEATED_UPTREND | 上昇 + ADR買われ過ぎ(>130) |
        | VOLATILE_UPTREND | 上昇 + 高Vol |
        | QUIET_RANGE | 横ばい + 低Vol |
        | VOLATILE_RANGE | 横ばい + 高Vol |
        | CORRECTION | 下落 + 通常Vol |
        | STRONG_DOWNTREND | 強い下落（ADX高い + 下落） |
        | PANIC_SELL | 急落 + 高Vol + パニックADR(<60) |
        """
        is_uptrend = trend.trend_direction == TrendDirection.UPTREND
        is_downtrend = trend.trend_direction == TrendDirection.DOWNTREND
        is_sideways = trend.trend_direction == TrendDirection.SIDEWAYS

        high_vol_levels = [VolatilityLevel.HIGH, VolatilityLevel.ELEVATED]
        is_high_vol = volatility.volatility_level in high_vol_levels
        is_low_vol = volatility.volatility_level == VolatilityLevel.LOW

        is_overbought = adr.short_term > self._config.adr_overbought
        is_panic = adr.short_term < self._config.adr_short_panic

        is_strong_trend = trend.trend_type == TrendType.TRENDING

        # パニック売り（最優先判定）
        if is_downtrend and is_high_vol and is_panic:
            return EnvironmentCode.PANIC_SELL

        # 本格下降（強いトレンド + 下落）
        if is_strong_trend and is_downtrend:
            return EnvironmentCode.STRONG_DOWNTREND

        # 上昇系
        if is_uptrend:
            if is_overbought:
                return EnvironmentCode.OVERHEATED_UPTREND
            if is_high_vol:
                return EnvironmentCode.VOLATILE_UPTREND
            return EnvironmentCode.STABLE_UPTREND

        # レンジ系
        if is_sideways or trend.trend_type == TrendType.RANGING:
            if is_low_vol:
                return EnvironmentCode.QUIET_RANGE
            if is_high_vol:
                return EnvironmentCode.VOLATILE_RANGE
            return EnvironmentCode.QUIET_RANGE

        # 下落系（調整局面）
        if is_downtrend:
            return EnvironmentCode.CORRECTION

        # デフォルト
        return EnvironmentCode.QUIET_RANGE

    def _calculate_risk_score(
        self,
        trend: TrendAnalysis,
        volatility: VolatilityAnalysis,
        adr: AdvancingDecliningRatio,
    ) -> int:
        """
        リスクスコアを計算 (0-100).

        計算式:
        - トレンド(40点): DOWNTREND +40, SIDEWAYS +20, UPTREND +0
        - ボラティリティ(30点): HIGH +30, ELEVATED +20, NORMAL +10, LOW +0
        - ADR(30点): パニック水準 +30, 売られ過ぎ +15, 正常範囲 +0
        - ダイバージェンス調整: Bullish -5, Bearish +5
        """
        score = 0

        # トレンド方向 (40点)
        if trend.trend_direction == TrendDirection.DOWNTREND:
            score += self._config.risk_trend_weight  # 40
        elif trend.trend_direction == TrendDirection.SIDEWAYS:
            score += self._config.risk_trend_weight // 2  # 20

        # ボラティリティ (30点)
        vol_weight = self._config.risk_volatility_weight
        vol_scores = {
            VolatilityLevel.HIGH: vol_weight,  # 30
            VolatilityLevel.ELEVATED: vol_weight * 2 // 3,  # 20
            VolatilityLevel.NORMAL: vol_weight // 3,  # 10
            VolatilityLevel.LOW: 0,
        }
        score += vol_scores.get(volatility.volatility_level, 0)

        # ADR (30点)
        if adr.short_term < self._config.adr_short_panic:
            score += self._config.risk_adr_weight  # 30
        elif adr.short_term < self._config.adr_oversold:
            score += self._config.risk_adr_weight // 2  # 15

        # ダイバージェンス調整 (±5点)
        if adr.divergence == ADRDivergence.BULLISH:
            score -= self._config.risk_divergence_adjustment  # -5
        elif adr.divergence == ADRDivergence.BEARISH:
            score += self._config.risk_divergence_adjustment  # +5

        return max(0, min(100, score))

    def _get_latest_value(
        self,
        df: pd.DataFrame,
        column: str,
        default: float,
    ) -> float:
        """DataFrameから最新値を取得."""
        if column not in df.columns:
            return default

        series = df[column].dropna()
        if series.empty:
            return default

        return float(series.iloc[-1])
