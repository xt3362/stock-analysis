"""ポートフォリオ内のポジションを表すデータモデル"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict


@dataclass
class Position:
    """ポートフォリオ内のポジションを表すデータクラス"""

    symbol: str
    entry_date: date
    entry_price: float
    stop_loss: float
    take_profit: float
    recommendation: str
    strategy: str
    score: int
    shares: float = 0.0  # 保有株数
    position_value: float = 0.0  # 投資金額（エントリー時）
    max_holding_days: int = 15  # 戦略別最大保有日数
    # トレーリングストップ関連
    trailing_stop_enabled: bool = False  # トレーリングストップ有効化
    trailing_stop_pct: float = 0.0  # 高値からの下落率（%）でトレーリング（後方互換用）
    trailing_atr_multiplier: float = 0.0  # ATR × この倍率でトレーリング
    trailing_trigger_pct: float = 0.0  # この%の含み益でトレーリング開始
    # 追加フィールド（trades.csv出力用）
    raw_entry_price: float = 0.0  # スリッページ前エントリー価格
    atr_pct: float = 0.0  # エントリー時ATR%
    rank: str = ""  # スコアランク (S/A/B/C/D)
    strategy_confidence: float = 0.0  # 戦略信頼度
    market_regime_score: float = 0.0  # 市場環境スコア
    indicator_score: float = 0.0  # テクニカル指標スコア
    # market_regimeラベル
    market_environment: str = ""  # 8パターン分類
    market_risk_level: str = ""  # リスクレベル
    market_trend_direction: str = ""  # トレンド方向
    market_volatility_level: str = ""  # ボラティリティレベル
    market_risk_score: int = 0  # リスクスコア
    market_adx_value: float = 0.0  # ADX値
    market_atr_percent: float = 0.0  # 市場全体ATR%

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            Position の辞書表現
        """
        return {
            "symbol": self.symbol,
            "entry_date": self.entry_date,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "recommendation": self.recommendation,
            "strategy": self.strategy,
            "score": self.score,
            "shares": self.shares,
            "position_value": self.position_value,
            "max_holding_days": self.max_holding_days,
            "trailing_stop_enabled": self.trailing_stop_enabled,
            "trailing_stop_pct": self.trailing_stop_pct,
        }
