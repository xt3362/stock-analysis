# スウィングトレードシステム アーキテクチャ・処理フロー

**最終更新**: 2025-12-02

---

## 1. システム構成要素

スウィングトレードシステムは以下の12要素で構成される。

```mermaid
graph TB
    subgraph Analysis["分析層 (Analysis)"]
        A1[1. 市場レジーム分析<br/>MarketRegime]
        A2[2. 銘柄プロファイル<br/>StockProfile]
        A3[3. イベントカレンダー<br/>EventCalendar]
    end

    subgraph Selection["選定層 (Selection)"]
        S1[4. 銘柄ユニバース<br/>Universe]
        S2[5. 銘柄スクリーニング<br/>Screening]
        S3[6. 戦略セレクター<br/>StrategyMatcher]
    end

    subgraph Execution["実行層 (Execution)"]
        E1[7. 戦略実行<br/>StrategyExecution]
        E2[8. ポジションサイジング<br/>PositionSizing]
        E3[9. リスク管理<br/>RiskManagement]
        E4[10. 執行管理<br/>ExecutionManager]
    end

    subgraph Management["管理層 (Management)"]
        M1[11. ポートフォリオ管理<br/>PortfolioManagement]
        M2[12. パフォーマンス評価<br/>Performance]
    end

    Analysis --> Selection
    Selection --> Execution
    Execution --> Management
```

### 各要素の責務

| # | 要素 | 責務 | 入力 | 出力 |
|---|------|------|------|------|
| 1 | 市場レジーム分析 | 市場全体の状態判定 | 市場指数の日足データ | 環境コード、リスクスコア |
| 2 | 銘柄プロファイル | 銘柄の長期特性分析 | 過去500日の日足データ | プロファイルタイプ、推奨戦略 |
| 3 | イベントカレンダー | 決算・SQ等のイベント管理 | 決算日、配当日、SQ日 | イベントリスクフラグ、除外期間 |
| 4 | 銘柄ユニバース | 取引対象の母集合定義 | 全銘柄の流動性データ | フィルタ済み銘柄リスト |
| 5 | 銘柄スクリーニング | テクニカル条件でのフィルタ | ユニバース銘柄、日足データ | テクニカル指標、スクリーニング結果 |
| 6 | 戦略セレクター | 銘柄×環境に適した戦略選択 | 市場環境、銘柄プロファイル、テクニカル指標 | マッチした戦略、信頼度 |
| 7 | 戦略実行 | エントリー/エグジットシグナル生成 | 日足データ、選択された戦略 | BUY/SELL/HOLDシグナル、SL/TP価格 |
| 8 | ポジションサイジング | 資金配分・株数決定 | 資金、リスク許容度、期待値 | 投入資金比率、株数 |
| 9 | リスク管理 | SL/TP設定、トレーリング | シグナル、ATR、ポジションサイズ | 調整済みSL/TP価格、トレーリング条件 |
| 10 | 執行管理 | 注文執行・スリッページ管理 | 注文情報、板情報 | 約定結果、執行コスト |
| 11 | ポートフォリオ管理 | 複数ポジションの統合管理 | ポジション群、現金残高 | ポートフォリオ状態 |
| 12 | パフォーマンス評価 | 収益率、リスク指標の計算 | トレード履歴、日次ポートフォリオ価値 | 勝率、シャープレシオ等 |

---

## 2. 実運用フロー

実運用（ライブトレード）における日次の処理フロー。

### 2.1 日次処理フロー図

```mermaid
flowchart TD
    Start([毎日の処理<br/>市場終了後]) --> Step1

    subgraph Step1[STEP 1: データ更新]
        D1[価格データ取得 OHLCV]
        D2[テクニカル指標計算]
        D3[市場指数データ取得<br/>日経225, TOPIX ETF]
        D1 --> D2 --> D3
    end

    Step1 --> Step2

    subgraph Step2[STEP 2: 市場環境分析]
        M1[市場レジーム判定<br/>8パターン]
        M2[リスクスコア算出<br/>0-100]
        M3{トレード可否判定}
        M1 --> M2 --> M3
    end

    M3 -->|高リスク環境<br/>PANIC_SELL等| Stop[新規エントリー停止]
    M3 -->|通常環境| Step3

    subgraph Step3[STEP 3: 保有ポジション評価]
        P1{ストップロス到達?}
        P2{テイクプロフィット到達?}
        P3{最大保有日数超過?}
        P4[トレーリングストップ更新]
        P5{市場環境悪化?}
        P1 -->|Yes| Exit1[翌日寄付で決済]
        P1 -->|No| P2
        P2 -->|Yes| Exit2[翌日寄付で決済]
        P2 -->|No| P3
        P3 -->|Yes| Exit3[翌日寄付で決済]
        P3 -->|No| P4 --> P5
        P5 -->|Yes| Exit4[早期撤退検討]
        P5 -->|No| Continue[保有継続]
    end

    Step3 --> Step4

    subgraph Step4[STEP 4: 新規エントリー候補選定]
        C1[4.1 ユニバースから候補抽出<br/>流動性/価格/データ品質]
        C2[4.2 スクリーニング<br/>ADX, RSI, ATR%, 出来高比率]
        C3[4.3 銘柄プロファイル照合<br/>推奨戦略確認]
        C4[4.4 戦略マッチング<br/>市場環境×銘柄特性→戦略選択]
        C1 --> C2 --> C3 --> C4
    end

    Step4 --> Step5

    subgraph Step5[STEP 5: エントリー判定]
        E1[5.1 シグナル生成<br/>generate_signals実行]
        E2[5.2 リスク管理チェック<br/>ポジションサイズ/SL/TP]
        E3[5.3 ポートフォリオ制約<br/>セクター集中度/相関リスク]
        E1 --> E2 --> E3
    end

    Step5 --> Step6

    subgraph Step6[STEP 6: 注文実行]
        O1[決済注文: 寄付成行]
        O2[新規注文: 寄付成行 or 指値]
        O3[ポートフォリオ状態更新]
        O1 --> O2 --> O3
    end

    Step6 --> Step7

    subgraph Step7[STEP 7: 記録・レポート]
        R1[トレード履歴保存]
        R2[日次パフォーマンス計算]
        R3[ポートフォリオ価値記録]
        R1 --> R2 --> R3
    end

    Step7 --> End([処理完了])
    Stop --> Step3
```

### 2.2 市場レジーム判定フロー

```mermaid
flowchart TD
    Start[市場データ取得] --> Trend[トレンド分析<br/>ADX + SMA傾き]
    Start --> Vol[ボラティリティ分析<br/>ATR% + BB幅]
    Start --> Sent[センチメント分析<br/>騰落レシオ]

    Trend --> Combine[統合判定]
    Vol --> Combine
    Sent --> Combine

    Combine --> Judge{判定}

    Judge -->|ADX高+上昇| Bull1[STABLE_UPTREND]
    Judge -->|ADX高+上昇+過熱| Bull2[OVERHEATED_UPTREND]
    Judge -->|ADX高+上昇+高Vol| Bull3[VOLATILE_UPTREND]
    Judge -->|ADX低+横ばい+低Vol| Range1[QUIET_RANGE]
    Judge -->|ADX低+横ばい+高Vol| Range2[VOLATILE_RANGE]
    Judge -->|下落+調整| Bear1[CORRECTION]
    Judge -->|強い下落| Bear2[STRONG_DOWNTREND]
    Judge -->|急落+パニック| Bear3[PANIC_SELL]

    Bull1 --> Risk[リスクスコア計算<br/>0-100]
    Bull2 --> Risk
    Bull3 --> Risk
    Range1 --> Risk
    Range2 --> Risk
    Bear1 --> Risk
    Bear2 --> Risk
    Bear3 --> Risk
```

### 2.3 実運用の判断基準

#### 市場レジーム別のアクション

| 市場環境 | 新規エントリー | 保有継続 | 推奨戦略 |
|---------|--------------|---------|---------|
| STABLE_UPTREND | ○ 積極的 | ○ | trend_follow, breakout |
| OVERHEATED_UPTREND | △ 慎重 | ○ トレーリング推奨 | defensive_long |
| VOLATILE_UPTREND | △ 慎重 | ○ SL拡大 | trend_follow |
| QUIET_RANGE | ○ | ○ | mean_reversion |
| VOLATILE_RANGE | △ 慎重 | △ | mean_reversion |
| CORRECTION | △ 底打ち確認後 | △ SL縮小 | bottom_fishing |
| STRONG_DOWNTREND | × 停止 | △ 早期撤退検討 | - |
| PANIC_SELL | × 停止 | × 即撤退 | - |

---

## 3. バックテストフロー

過去データを使った戦略検証のフロー。

### 3.1 バックテストフロー図

```mermaid
flowchart TD
    Start([バックテスト開始]) --> Input

    subgraph Input[入力パラメータ]
        I1[対象銘柄 or ユニバース]
        I2[期間: start_date, end_date]
        I3[初期資金]
        I4[戦略: 指定 or 自動選択]
    end

    Input --> Step1

    subgraph Step1[STEP 1: データ準備]
        D1[1.1 価格データ取得<br/>ウォームアップ期間含む 60日前〜]
        D2[1.2 ユニバース準備<br/>月次/四半期更新]
        D3[1.3 銘柄プロファイル準備<br/>月末日ベース]
        D1 --> D2 --> D3
    end

    Step1 --> Loop

    subgraph Loop[STEP 2: 日次シミュレーションループ]
        L0[for each trading_day]
        L1[2.1 市場レジーム判定<br/>先読みバイアス回避]
        L2[2.2 エグジット判定<br/>SL/TP/タイムアウト]
        L3[2.3 新規エントリー判定<br/>スクリーニング→マッチング→シグナル]
        L4[2.4 トレード実行シミュレーション<br/>スリッページ適用]
        L5[2.5 日次記録<br/>ポートフォリオ価値/ポジション]
        L0 --> L1 --> L2 --> L3 --> L4 --> L5
        L5 -->|次の営業日| L0
    end

    Loop --> Step3

    subgraph Step3[STEP 3: パフォーマンス計算]
        P1[3.1 基本指標<br/>総トレード数/勝率/平均リターン]
        P2[3.2 リスク指標<br/>最大DD/シャープ/ソルティノ]
        P3[3.3 期間別分析<br/>月次リターン/市場環境別]
        P4[3.4 戦略別分析<br/>戦略別勝率/期待値]
        P1 --> P2 --> P3 --> P4
    end

    Step3 --> Step4

    subgraph Step4[STEP 4: 結果出力]
        O1[サマリーレポート]
        O2[トレード履歴 CSV]
        O3[日次ポートフォリオ推移 CSV]
        O4[エクイティカーブ]
    end

    Step4 --> End([バックテスト完了])
```

### 3.2 日次シミュレーション詳細

```mermaid
flowchart TD
    Day[営業日 t] --> Regime[市場レジーム判定<br/>t-1以前のデータのみ使用]

    Regime --> ExitCheck{保有ポジションあり?}

    ExitCheck -->|Yes| SLCheck{安値 <= SL価格?}
    ExitCheck -->|No| EntryCheck

    SLCheck -->|Yes| SLExit[SL決済<br/>約定価格=SL価格]
    SLCheck -->|No| TPCheck{高値 >= TP価格?}

    TPCheck -->|Yes| TPExit[TP決済<br/>約定価格=TP価格]
    TPCheck -->|No| TimeCheck{保有日数 > max?}

    TimeCheck -->|Yes| TimeExit[タイムアウト決済<br/>約定価格=終値-スリッページ]
    TimeCheck -->|No| TrailingUpdate[トレーリングストップ更新]

    SLExit --> EntryCheck
    TPExit --> EntryCheck
    TimeExit --> EntryCheck
    TrailingUpdate --> EntryCheck

    EntryCheck{新規エントリー可能?<br/>ポジション枠/現金} -->|Yes| Screen[スクリーニング]
    EntryCheck -->|No| Record

    Screen --> Match[戦略マッチング]
    Match --> Signal{BUYシグナル?}

    Signal -->|Yes| Entry[エントリー<br/>約定価格=翌日始値+スリッページ]
    Signal -->|No| Record

    Entry --> Record[日次記録]
    Record --> Next[次の営業日へ]
```

### 3.3 バックテストの種類

| 種類 | 対象 | 用途 | ファイル |
|------|------|------|---------|
| 単一銘柄バックテスト | 1銘柄 | 戦略のシグナル検証 | `strategy_backtester.py` |
| スコアベースバックテスト | 1銘柄 | スコアリングモデル検証 | `backtester.py` |
| ポートフォリオバックテスト | 複数銘柄 | 実運用シミュレーション | `portfolio_backtester.py` |
| バッチバックテスト | 複数銘柄×複数期間 | 大規模検証 | `batch_backtester.py` |

### 3.4 先読みバイアス回避

```mermaid
flowchart LR
    subgraph NG[NG: 先読みバイアス]
        N1[判定日tで<br/>t以降のデータ使用]
        N2[将来の終値で<br/>エントリー判定]
        N3[上場廃止銘柄を<br/>除外]
    end

    subgraph OK[OK: 正しい実装]
        O1[判定日tで<br/>t-1以前のデータのみ]
        O2[翌日始値+スリッページで<br/>約定]
        O3[当時のユニバースを<br/>再現]
    end

    NG -.->|修正| OK
```

**先読みバイアス回避ルール:**

1. **データ使用制限**: 判定日(t)の分析には、t-1以前のデータのみ使用
2. **テクニカル指標**: 各日付時点で計算（将来データを含まない）
3. **銘柄プロファイル**: バックテスト用プロファイル（月末日ベース）を使用
4. **ユニバース**: 過去のユニバース構成を再現（サバイバーシップバイアス考慮）
5. **約定価格**: エントリーは翌日始値+スリッページ、エグジットは当日終値 or SL/TP価格

---

## 4. データ取得・管理フロー

### 4.1 データ取得フロー図

```mermaid
flowchart TD
    subgraph Source[データソース]
        YF[Yahoo Finance<br/>yfinance]
    end

    YF --> Collector

    subgraph Collector[STEP 1: データ取得]
        C1[DataCollector]
        C2[レート制限対策<br/>1.5秒間隔]
        C3[リトライ機能<br/>最大3回]
        C4[エラーハンドリング<br/>部分的成功許容]
        C1 --> C2 --> C3 --> C4
    end

    Collector --> Indicator

    subgraph Indicator[STEP 2: テクニカル指標計算]
        I1[IndicatorCalculator]
        I2[基本指標<br/>SMA/EMA/RSI/MACD/BB/ADX/ATR]
        I3[出来高指標<br/>Volume MA/Ratio/OBV]
        I1 --> I2 --> I3
    end

    Indicator --> Storage

    subgraph Storage[STEP 3: データ保存]
        DB[(PostgreSQL)]
        T1[tickers<br/>銘柄マスタ]
        T2[daily_prices<br/>価格+指標]
        T3[fundamental_data<br/>ファンダ]
        T4[earnings_data<br/>決算]
        T5[universes<br/>ユニバース]
        T6[universe_symbols<br/>構成銘柄]
        DB --- T1
        DB --- T2
        DB --- T3
        DB --- T4
        DB --- T5
        DB --- T6
    end
```

### 4.2 データフロー全体像

```mermaid
flowchart LR
    subgraph External[外部データ]
        YF[Yahoo Finance]
    end

    subgraph Collection[データ収集]
        DC[DataCollector]
    end

    subgraph Storage[永続化]
        DB[(PostgreSQL)]
    end

    subgraph Processing[処理]
        IC[IndicatorCalculator]
        MR[MarketRegimeAnalyzer]
        PG[ProfileGenerator]
        US[UniverseSelector]
    end

    subgraph Analysis[分析]
        SS[StockScreener]
        SM[StrategyMatcher]
        SE[StrategyExecution]
    end

    subgraph Execution[実行]
        PS[PositionSizer]
        RM[RiskManager]
        PM[PortfolioManager]
    end

    YF --> DC --> DB
    DB --> IC --> DB
    DB --> MR
    DB --> PG
    DB --> US
    MR --> SM
    PG --> SM
    US --> SS --> SM
    SM --> SE --> PS --> RM --> PM
```

### 4.3 データ管理の仕組み

#### データ更新スケジュール

| データ種別 | 更新頻度 | タイミング | 保存期間 |
|-----------|---------|-----------|---------|
| 価格データ (OHLCV) | 日次 | 市場終了後 | 無期限 |
| テクニカル指標 | 日次 | 価格更新時 | 無期限 |
| ファンダメンタル | 週次/四半期 | 決算発表後 | 無期限 |
| ユニバース | 月次/四半期 | 月末 | 履歴保持 |
| 銘柄プロファイル | 月次 | 月末 | 履歴保持 |
| 市場レジーム | 日次 | 市場終了後 | キャッシュ |

#### データ品質チェック

```mermaid
flowchart TD
    Data[データ] --> Check1{欠損チェック<br/>欠損率 <= 30%<br/>連続欠損 <= 60日}
    Check1 -->|Pass| Check2{異常値チェック<br/>価格: ±30%以内<br/>出来高: ±1000%以内}
    Check1 -->|Fail| Reject1[除外]

    Check2 -->|Pass| Check3{整合性チェック<br/>High >= Low<br/>Open/Closeが範囲内}
    Check2 -->|Fail| Reject2[除外]

    Check3 -->|Pass| Check4{最新性チェック<br/>最終更新 >= 前営業日}
    Check3 -->|Fail| Reject3[除外]

    Check4 -->|Pass| Accept[採用]
    Check4 -->|Fail| Reject4[除外]
```

### 4.4 設定ファイル管理

```mermaid
graph TD
    subgraph Config[config/]
        MR[market_regime/]
        PR[profiles/]
        SM[strategy_matcher/]
        US[universe_selector/]
        PB[portfolio_backtester/]
        ST[strategies/]
    end

    MR --> MR1[01_init.yml]
    MR --> MR2[02_enhanced.yml]
    MR --> MR3[03_multi_period_adr.yml]
    MR --> MRL[latest.yml → 03_multi_period_adr.yml]

    PR --> PRL[live/latest.yml]
    PR --> PRB[backtest/{symbol}/{date}.yml]

    SM --> SM1[01_init.yml]
    SM --> SM2[02_phase1_relaxed.yml]
    SM --> SML[latest.yml]

    US --> US1[01_init.yml]
    US --> USL[latest.yml]

    ST --> STN[{strategy_name}/latest.yml]
```

---

## 5. 要素間の依存関係

### 5.1 依存関係図

```mermaid
flowchart TD
    subgraph Data[データ管理]
        DM[価格・指標データ]
    end

    subgraph Analysis[分析層]
        A1[1. 市場レジーム分析]
        A2[2. 銘柄プロファイル]
        A3[3. イベントカレンダー]
    end

    subgraph Selection[選定層]
        S1[4. 銘柄ユニバース]
        S2[5. 銘柄スクリーニング]
        S3[6. 戦略セレクター]
    end

    subgraph Execution[実行層]
        E1[7. 戦略実行]
        E2[8. ポジションサイジング]
        E3[9. リスク管理]
        E4[10. 執行管理]
    end

    subgraph Management[管理層]
        M1[11. ポートフォリオ管理]
        M2[12. パフォーマンス評価]
    end

    DM --> A1
    DM --> A2
    DM --> A3
    DM --> S1
    DM --> S2

    A1 --> S3
    A2 --> S3
    A3 --> S2
    S1 --> S2
    S2 --> S3

    S3 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> M1
    M1 --> M2
```

### 5.2 情報の流れ

```mermaid
flowchart LR
    subgraph Input[入力]
        I1[市場指数データ]
        I2[過去500日価格]
        I3[決算日/配当日]
        I4[全銘柄]
        I5[価格/指標]
        I6[板情報]
    end

    subgraph Process[処理]
        P1[市場レジーム分析]
        P2[銘柄プロファイル]
        P3[イベントカレンダー]
        P4[銘柄ユニバース]
        P5[スクリーニング]
        P6[戦略セレクター]
        P7[戦略実行]
        P8[ポジションサイジング]
        P9[リスク管理]
        P10[執行管理]
        P11[ポートフォリオ管理]
        P12[パフォーマンス評価]
    end

    subgraph Output[出力]
        O1[環境コード/リスクスコア]
        O2[プロファイルタイプ/推奨戦略]
        O3[イベントリスク/除外期間]
        O4[フィルタ済み銘柄]
        O5[スクリーニング結果]
        O6[マッチ戦略/信頼度]
        O7[BUY/SELL/HOLDシグナル]
        O8[投入資金比率/株数]
        O9[調整済みSL/TP価格]
        O10[約定結果/執行コスト]
        O11[ポートフォリオ状態]
        O12[勝率/シャープレシオ等]
    end

    I1 --> P1 --> O1
    I2 --> P2 --> O2
    I3 --> P3 --> O3
    I4 --> P4 --> O4
    I5 --> P5 --> O5

    O1 --> P6
    O2 --> P6
    O3 --> P5
    O4 --> P5
    O5 --> P6
    P6 --> O6

    O6 --> P7 --> O7
    O7 --> P8 --> O8
    O8 --> P9 --> O9
    I6 --> P10
    O9 --> P10 --> O10
    O10 --> P11 --> O11
    O11 --> P12 --> O12
```

### 5.3 情報フロー表

| From | To | 情報 |
|------|-----|------|
| データ管理 | 市場レジーム分析 | 市場指数の日足データ |
| データ管理 | 銘柄プロファイル | 過去500日の日足データ |
| データ管理 | イベントカレンダー | 決算日、配当日、SQ日 |
| データ管理 | 銘柄ユニバース | 全銘柄の流動性データ |
| データ管理 | 銘柄スクリーニング | 日足データ（価格、出来高） |
| 市場レジーム分析 | 戦略セレクター | 環境コード、リスクスコア |
| 銘柄プロファイル | 戦略セレクター | プロファイルタイプ、推奨戦略 |
| イベントカレンダー | 銘柄スクリーニング | イベントリスクフラグ、除外期間 |
| 銘柄ユニバース | 銘柄スクリーニング | 対象銘柄リスト |
| 銘柄スクリーニング | 戦略セレクター | テクニカル指標（ADX, RSI, ATR%等） |
| 戦略セレクター | 戦略実行 | 選択された戦略、信頼度 |
| データ管理 | 戦略実行 | 日足データ（シグナル生成用） |
| 戦略実行 | ポジションサイジング | BUYシグナル、SL/TP価格、期待値 |
| ポジションサイジング | リスク管理 | 投入資金比率、株数 |
| リスク管理 | 執行管理 | 調整済みSL/TP価格、トレーリング条件 |
| データ管理 | 執行管理 | 板情報、流動性データ |
| 執行管理 | ポートフォリオ管理 | 約定結果、執行コスト |
| ポートフォリオ管理 | パフォーマンス評価 | トレード履歴、日次ポートフォリオ価値 |

---

## 6. 補足: 主要クラス対応表

| 構成要素 | 主要クラス | ファイルパス | 実装状況 |
|---------|-----------|-------------|----------|
| 市場レジーム分析 | `MarketRegimeAnalyzer` | `src/services/market_regime/market_regime_analyzer.py` | 実装済み |
| 銘柄プロファイル | `ProfileMatcher`, `ProfileGenerator` | `src/services/profile/` | 実装済み |
| イベントカレンダー | `EventCalendar` | 未実装 | **未実装** |
| 銘柄ユニバース | `UniverseSelector` | `src/services/universe_selector/universe_selector.py` | 実装済み |
| 銘柄スクリーニング | `StockScreener`, `MarketAwareScreener` | `src/services/stock_screener/`, `src/services/market_aware_screening/` | 実装済み |
| 戦略セレクター | `StrategyMatcher` | `src/services/strategy_matcher/strategy_matcher.py` | 実装済み |
| 戦略実行 | `BaseSwingStrategy`, 各戦略クラス | `src/services/strategies/` | 実装済み |
| ポジションサイジング | `PositionSizer` | `src/services/trading/position_sizer.py` | 実装済み（Kelly基準未対応） |
| リスク管理 | `RiskManager`, `ExitManager` | `src/services/trading/` | 実装済み |
| 執行管理 | `ExecutionManager` | 未実装 | **未実装** |
| ポートフォリオ管理 | `PortfolioManager` | `src/services/trading/portfolio_manager.py` | 実装済み |
| パフォーマンス評価 | `PortfolioMetricsCalculator` | `src/services/portfolio_backtester.py` | 実装済み |

---

## 7. 関連ドキュメント

- [コンポーネント検証ガイド](./component-validation.md) - 各要素の検証方法とパラメータ最適化手順
- [コンポーネント入出力定義](./component-io-definitions/) - 各要素の入出力データ仕様
  - [市場レジーム分析](./component-io-definitions/01-market-regime.md)

---

**最終更新**: 2025-12-02
