# yfinance

## 概要

yfinanceは、Yahoo! FinanceのAPIを利用してマーケットデータをダウンロードするためのオープンソースのPythonパッケージです。

### 重要な法的免責事項

- Yahoo!、Y!Finance、Yahoo! financeは、Yahoo, Inc.の登録商標です
- yfinanceは、Yahoo, Inc.と提携、承認、または検証されていません
- Yahoo!の公開APIを使用する研究および教育目的のオープンソースツールです
- Yahoo!の利用規約を参照し、ダウンロードしたデータの使用権について確認してください
- Yahoo! Finance APIは個人使用のみを目的としています

## インストール

```bash
pip install yfinance
```

## 主な機能

### 単一ティッカーシンボルの取得

```python
import yfinance as yf

dat = yf.Ticker("MSFT")

# 様々なデータにアクセス可能
dat.info                        # 基本情報
dat.calendar                    # カレンダー情報
dat.analyst_price_targets       # アナリストの目標株価
dat.quarterly_income_stmt       # 四半期損益計算書
dat.history(period='1mo')       # 過去1ヶ月の株価履歴
dat.option_chain(dat.options[0]).calls  # オプション情報
```

### 複数ティッカーシンボルの取得

```python
# 複数銘柄の情報を一度に取得
tickers = yf.Tickers('MSFT AAPL GOOG')
tickers.tickers['MSFT'].info

# 複数銘柄のダウンロード
yf.download(['MSFT', 'AAPL', 'GOOG'], period='1mo')
```

### ファンド情報の取得

```python
spy = yf.Ticker('SPY').funds_data
spy.description    # ファンドの説明
spy.top_holdings   # 主要保有銘柄
```

## ドキュメント

- [API Reference](https://ranaroussi.github.io/yfinance/reference/index.html) - 完全なAPIリファレンス
- [Advanced](https://ranaroussi.github.io/yfinance/advanced/index.html) - 高度な使用方法
- [Development](https://ranaroussi.github.io/yfinance/development/index.html) - 開発者向け情報

## 参考リンク

- 公式ドキュメント: https://ranaroussi.github.io/yfinance/
- GitHub: https://github.com/ranaroussi/yfinance

---

*© Copyright 2017-2025 Ran Aroussi*
