"""イベントカレンダーのデータモデル.

決算・配当・SQ日等のイベントを管理し、リスク評価を行うためのモデル定義。
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class EventType(str, Enum):
    """イベント種別."""

    EARNINGS = "earnings"  # 決算発表
    DIVIDEND = "dividend"  # 配当権利確定
    SQ = "sq"  # SQ日（先物・オプション決済日）


class EventRiskLevel(str, Enum):
    """イベントリスクレベル.

    各イベントに対するリスクの度合いを示す。
    市場レジームの RiskLevel とは異なるセマンティクス。
    """

    NONE = "none"  # イベントなし
    LOW = "low"  # SQ日当日
    MEDIUM = "medium"  # 配当権利確定日
    HIGH = "high"  # 決算近接（除外期間外）
    CRITICAL = "critical"  # 決算除外期間（発表日-2日〜+1日）


@dataclass(frozen=True)
class NearestEvent:
    """最も近いイベント情報."""

    event_type: EventType
    event_date: date
    days_until: int


@dataclass(frozen=True)
class EventCalendarResult:
    """イベントカレンダー判定結果.

    Attributes:
        entry_allowed: 新規エントリー可否
        exit_required: 強制決済要否
        risk_level: イベントリスクレベル
        nearest_event: 最も近いイベント情報（None可）
        reason: 判定理由
    """

    entry_allowed: bool
    exit_required: bool
    risk_level: EventRiskLevel
    nearest_event: NearestEvent | None
    reason: str


@dataclass(frozen=True)
class EventCalendarConfig:
    """イベントカレンダー設定.

    Attributes:
        earnings_exclude_before: 決算前除外日数
        earnings_exclude_after: 決算後除外日数
        earnings_cross_threshold: 決算跨ぎ許容の含み益閾値（%）
        dividend_exclude_days: 配当権利確定日の除外日数
    """

    earnings_exclude_before: int = 2
    earnings_exclude_after: int = 1
    earnings_cross_threshold: float = 8.0
    dividend_exclude_days: int = 1


@dataclass(frozen=True)
class EventInput:
    """イベント判定の入力データ.

    サービスの入力を明示的に定義。

    Attributes:
        symbol: 銘柄コード
        check_date: 判定日
        earnings_date: 決算発表日（任意）
        ex_dividend_date: 配当権利確定日（任意）
        position_pnl: 含み損益率（%、保有時のみ）
    """

    symbol: str
    check_date: date
    earnings_date: date | None = None
    ex_dividend_date: date | None = None
    position_pnl: float | None = None
