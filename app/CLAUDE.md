# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 本システムの目的

日本株式データの取得・分析を通じて株式投資の最適化を目的としたシステム。
スウィングトレードによる年利40~60%の稼ぎを目標としている。

## 技術スタック

- Python 3.12
- PostgreSQL（データ永続化）
- Yahoo Finance（yfinance - データソース）

## 開発コマンド

```bash
# 仮想環境のアクティベート
source .venv/bin/activate

# スクリプト実行
uv run script_path

# 型チェック
make typecheck

# リント
make lint

# フォーマット
make format

# テスト実行
make test
```

## コア開発

以下のルールを順守すること
@../CoreDevelopmentRules.md

## アーキテクチャ概要

### 4層構造

1. **分析層 (Analysis)**: 市場レジーム分析、銘柄プロファイル、イベントカレンダー
2. **選定層 (Selection)**: 銘柄ユニバース、スクリーニング、戦略セレクター
3. **実行層 (Execution)**: 戦略実行、ポジションサイジング、リスク管理、執行管理
4. **管理層 (Management)**: ポートフォリオ管理、パフォーマンス評価

### 推奨ディレクトリ構造（計画中）

```
src/
├── domain/           # ドメイン層（ビジネスロジック）
│   ├── models/       # エンティティ・値オブジェクト
│   ├── services/     # ドメインサービス
│   │   ├── analysis/     # 分析層
│   │   ├── selection/    # 選定層
│   │   ├── execution/    # 実行層（戦略含む）
│   │   └── management/   # 管理層
│   ├── ports/        # インターフェース定義
│   └── events/       # ドメインイベント
├── application/      # パイプライン、バックテスト
├── infrastructure/   # DB、外部API
├── interfaces/       # CLI
└── shared/           # 共通ユーティリティ
```

### 設定ファイル

設定は`config/`配下でYAML管理。`latest.yml`シンボリックリンクで最新版を参照。

## コード規約

- 型チェック: pyright strict モード
- リント: ruff (E, W, F, I, B, SIM, RUF, TCH, PTH, PL)
- 日本語コメント可

## ドキュメント

詳細設計は `/home/xt3362/development/stock-analysis/docs/` を参照:
- `architecture-flow.md`: 処理フロー詳細
- `component-validation.md`: 検証方法
- `proposed-directory-structure.md`: 推奨構造
