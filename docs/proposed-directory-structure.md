# スウィングトレードシステム 推奨ディレクトリ構造

**作成日**: 2025-12-06
**ステータス**: 提案（未実装）

---

## 1. 設計方針

### 採用アプローチ

```
軽量DDD（境界・値オブジェクト）
  + ヘキサゴナル（ポート&アダプター）
  + パイプラインパターン
```

### 採用理由

| 特性 | 対応 |
|------|------|
| バッチ処理中心（日次） | パイプラインパターン |
| 明確な4層構造（分析→選定→実行→管理） | 境界づけられたコンテキスト |
| 外部依存（Yahoo Finance, PostgreSQL） | ポート&アダプター |
| 設定駆動（戦略パラメータ） | 設定ファイル分離 |
| MVP開発中 | 過度な抽象化を回避 |

### 不採用としたもの

- **フルDDD**: 集約・リポジトリパターンは過剰
- **クリーンアーキテクチャ**: UseCase層は冗長
- **マイクロサービス**: モノリスで十分
- **リアルタイム対応設計**: 現時点で不要
- **マルチアセット対応**: 日本株のみで不要

---

## 2. ディレクトリ構造

```
src/
├── domain/                          # ドメイン層（ビジネスロジックの核心）
│   ├── models/                      # エンティティ・値オブジェクト
│   │   ├── market.py               # MarketRegime, RiskScore
│   │   ├── stock.py                # StockProfile, Ticker
│   │   ├── signal.py               # Signal, SignalType
│   │   ├── trade.py                # Trade, Position
│   │   └── portfolio.py            # Portfolio, PortfolioState
│   │
│   ├── services/                    # ドメインサービス（ステートレスなビジネスロジック）
│   │   ├── analysis/               # 分析層
│   │   │   ├── market_regime.py    # 市場レジーム分析
│   │   │   ├── stock_profile.py    # 銘柄プロファイル
│   │   │   └── event_calendar.py   # イベントカレンダー
│   │   │
│   │   ├── selection/              # 選定層
│   │   │   ├── universe.py         # ユニバース選定
│   │   │   ├── screener.py         # スクリーニング
│   │   │   └── strategy_matcher.py # 戦略マッチング
│   │   │
│   │   ├── execution/              # 実行層
│   │   │   ├── strategies/         # 戦略実装
│   │   │   │   ├── base.py
│   │   │   │   ├── trend_follow.py
│   │   │   │   ├── mean_reversion.py
│   │   │   │   └── breakout.py
│   │   │   ├── position_sizing.py  # ポジションサイジング
│   │   │   ├── risk_manager.py     # リスク管理
│   │   │   └── execution_manager.py # 執行管理
│   │   │
│   │   └── management/             # 管理層
│   │       ├── portfolio_manager.py
│   │       └── performance.py
│   │
│   ├── ports/                       # ポート（インターフェース定義）
│   │   ├── price_repository.py     # 価格データ取得
│   │   ├── trade_repository.py     # トレード履歴
│   │   └── data_source.py          # 外部データソース
│   │
│   └── events/                      # ドメインイベント
│       ├── signal_generated.py
│       ├── trade_executed.py
│       └── position_closed.py
│
├── application/                     # アプリケーション層（ユースケース・オーケストレーション）
│   ├── pipelines/                   # パイプライン（日次処理フロー）
│   │   ├── daily_analysis.py       # 日次分析パイプライン
│   │   ├── entry_screening.py      # エントリー候補選定
│   │   └── exit_evaluation.py      # エグジット評価
│   │
│   ├── backtest/                    # バックテスト
│   │   ├── strategy_backtester.py  # 単一銘柄バックテスト
│   │   ├── portfolio_backtester.py # ポートフォリオバックテスト
│   │   └── batch_backtester.py     # バッチバックテスト
│   │
│   └── commands/                    # コマンドハンドラ（CLI操作の処理）
│       ├── collect_data.py
│       ├── run_backtest.py
│       └── generate_signals.py
│
├── infrastructure/                  # インフラ層（外部依存）
│   ├── persistence/                 # 永続化
│   │   ├── repositories/           # リポジトリ実装
│   │   │   ├── ticker_repository.py
│   │   │   ├── price_repository.py
│   │   │   └── trade_repository.py
│   │   ├── models/                 # SQLAlchemyモデル
│   │   │   └── orm.py
│   │   └── database.py             # DB接続管理
│   │
│   ├── external/                    # 外部API
│   │   ├── yahoo_finance.py        # yfinanceラッパー
│   │   └── broker_api.py           # 証券会社API（将来）
│   │
│   ├── indicators/                  # テクニカル指標計算
│   │   └── calculator.py
│   │
│   └── config/                      # 設定読み込み
│       └── loader.py
│
├── interfaces/                      # インターフェース層（外部とのやり取り）
│   ├── cli/                         # CLIコマンド
│   │   ├── main.py
│   │   ├── data_commands.py
│   │   ├── backtest_commands.py
│   │   └── swing_commands.py
│   │
│   └── api/                         # REST API（将来）
│       └── routes.py
│
└── shared/                          # 共有ユーティリティ
    ├── types.py                    # 型定義
    ├── exceptions.py               # カスタム例外
    ├── logging.py                  # ログ設定
    └── datetime_utils.py           # 日付ユーティリティ

config/                              # 設定ファイル（既存構造維持）
├── market_regime/
├── strategies/
├── universe_selector/
└── ...

tests/                               # テスト
├── unit/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── integration/
└── e2e/
```

---

## 3. 層の責務と依存関係

### 依存関係図

```
interfaces → application → domain ← infrastructure
                              ↑
                         (依存性逆転)
```

### 各層の責務

| 層 | 責務 | 依存先 |
|----|------|--------|
| **domain** | ビジネスロジックの核心、外部依存なし | なし |
| **application** | ユースケース、パイプラインオーケストレーション | domain |
| **infrastructure** | DB、外部API、ファイルI/O | domain（ポート実装） |
| **interfaces** | CLI、API（将来） | application |
| **shared** | 共通ユーティリティ | なし |

### 境界づけられたコンテキスト

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Analysis   │→│  Selection  │→│  Execution  │→│ Management  │
│  (分析)     │  │  (選定)     │  │  (実行)     │  │  (管理)     │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 4. 主要コンポーネントの配置

| 構成要素 | 配置先 |
|---------|--------|
| 市場レジーム分析 | `domain/services/analysis/market_regime.py` |
| 銘柄プロファイル | `domain/services/analysis/stock_profile.py` |
| イベントカレンダー | `domain/services/analysis/event_calendar.py` |
| 銘柄ユニバース | `domain/services/selection/universe.py` |
| 銘柄スクリーニング | `domain/services/selection/screener.py` |
| 戦略セレクター | `domain/services/selection/strategy_matcher.py` |
| 戦略実行 | `domain/services/execution/strategies/` |
| ポジションサイジング | `domain/services/execution/position_sizing.py` |
| リスク管理 | `domain/services/execution/risk_manager.py` |
| 執行管理 | `domain/services/execution/execution_manager.py` |
| ポートフォリオ管理 | `domain/services/management/portfolio_manager.py` |
| パフォーマンス評価 | `domain/services/management/performance.py` |

---

## 5. 値オブジェクト例

```python
# domain/models/market.py
from dataclasses import dataclass
from enum import Enum

class RegimeType(Enum):
    STABLE_UPTREND = "stable_uptrend"
    OVERHEATED_UPTREND = "overheated_uptrend"
    VOLATILE_UPTREND = "volatile_uptrend"
    QUIET_RANGE = "quiet_range"
    VOLATILE_RANGE = "volatile_range"
    CORRECTION = "correction"
    STRONG_DOWNTREND = "strong_downtrend"
    PANIC_SELL = "panic_sell"

@dataclass(frozen=True)
class RiskScore:
    """リスクスコア（0-100）"""
    value: float

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError("RiskScore must be between 0 and 100")

    @property
    def is_high_risk(self) -> bool:
        return self.value >= 70

    @property
    def is_tradeable(self) -> bool:
        return self.value < 80

@dataclass(frozen=True)
class MarketRegime:
    """市場レジーム"""
    regime_type: RegimeType
    risk_score: RiskScore

    @property
    def tradeable(self) -> bool:
        if self.regime_type in [RegimeType.STRONG_DOWNTREND, RegimeType.PANIC_SELL]:
            return False
        return self.risk_score.is_tradeable
```

```python
# domain/models/signal.py
from dataclasses import dataclass
from enum import Enum
from datetime import date
from decimal import Decimal

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass(frozen=True)
class Signal:
    """トレードシグナル"""
    signal_type: SignalType
    symbol: str
    date: date
    strategy_name: str
    confidence: float  # 0.0 - 1.0
    entry_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
```

---

## 6. ポート&アダプター例

```python
# domain/ports/price_repository.py
from typing import Protocol
from datetime import date
import pandas as pd

class PriceRepository(Protocol):
    """価格データリポジトリのインターフェース"""

    def get_daily_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """日足データを取得"""
        ...

    def save_daily_prices(
        self,
        symbol: str,
        data: pd.DataFrame
    ) -> None:
        """日足データを保存"""
        ...
```

```python
# infrastructure/persistence/repositories/price_repository.py
# 注: Protocolは構造的部分型のため継承不要
from infrastructure.persistence.database import get_session

class PostgresPriceRepository:
    """PostgreSQL実装 - PriceRepository Protocolに構造的に適合"""

    def get_daily_prices(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        with get_session() as session:
            # SQL実行
            ...

    def save_daily_prices(self, symbol: str, data: pd.DataFrame) -> None:
        with get_session() as session:
            # SQL実行
            ...
```

---

## 7. 改修耐性

### 強い改修パターン

| 改修内容 | 対応箇所 | 影響範囲 |
|----------|----------|----------|
| 新戦略の追加 | `domain/services/execution/strategies/` | 1ファイル追加 |
| スクリーニング条件変更 | `config/` | コード変更なし |
| 新テクニカル指標 | `infrastructure/indicators/` | 局所的 |
| データソース追加 | `infrastructure/external/` | 局所的 |
| CLIコマンド追加 | `interfaces/cli/` | 局所的 |

### 弱い改修パターン（現時点で対応不要）

| 改修内容 | 理由 |
|----------|------|
| リアルタイム化 | バッチ前提の設計 |
| マルチアセット対応 | 日本株専用設計（予定なし） |
| マイクロサービス分割 | モノリス前提 |

---

## 8. 移行戦略（段階的）

1. **Phase 1**: `domain/models/` に値オブジェクトを抽出
2. **Phase 2**: `domain/services/` に純粋なビジネスロジックを移動
3. **Phase 3**: `domain/ports/` + `infrastructure/` で外部依存を分離
4. **Phase 4**: `application/pipelines/` でオーケストレーション整理

---

## 9. 関連ドキュメント

- [アーキテクチャ・処理フロー](./architecture-flow.md)
- [コンポーネント検証ガイド](./component-validation.md)
- [コンポーネント入出力定義](./component-io-definitions/)

---

**最終更新**: 2025-12-06
