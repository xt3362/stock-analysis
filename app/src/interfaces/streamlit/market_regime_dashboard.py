"""市場レジーム分析ダッシュボード."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportUnnecessaryComparison=false, reportAttributeAccessIssue=false
# NOTE: Streamlit/pandas/plotly type stubs are incomplete

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.models.market_regime import (
    EnvironmentCode,
    MarketRegime,
    RiskLevel,
)
from src.domain.services.analysis.market_regime_analyzer import MarketRegimeAnalyzer
from src.infrastructure.persistence.repositories.daily_price_repository import (
    PostgresDailyPriceRepository,
)
from src.infrastructure.persistence.repositories.universe_repository import (
    PostgresUniverseRepository,
)

# Load .env file from project root
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)

# 日本語表示名マッピング
ENVIRONMENT_NAMES: dict[EnvironmentCode, str] = {
    EnvironmentCode.STABLE_UPTREND: "健全な上昇",
    EnvironmentCode.OVERHEATED_UPTREND: "過熱上昇",
    EnvironmentCode.VOLATILE_UPTREND: "荒れた上昇",
    EnvironmentCode.QUIET_RANGE: "静かなレンジ",
    EnvironmentCode.VOLATILE_RANGE: "荒れたレンジ",
    EnvironmentCode.CORRECTION: "調整局面",
    EnvironmentCode.STRONG_DOWNTREND: "本格下降",
    EnvironmentCode.PANIC_SELL: "パニック売り",
}

ENVIRONMENT_COLORS: dict[EnvironmentCode, str] = {
    EnvironmentCode.STABLE_UPTREND: "#2ecc71",  # 緑
    EnvironmentCode.OVERHEATED_UPTREND: "#f39c12",  # オレンジ
    EnvironmentCode.VOLATILE_UPTREND: "#e67e22",  # ダークオレンジ
    EnvironmentCode.QUIET_RANGE: "#3498db",  # 青
    EnvironmentCode.VOLATILE_RANGE: "#9b59b6",  # 紫
    EnvironmentCode.CORRECTION: "#e74c3c",  # 赤
    EnvironmentCode.STRONG_DOWNTREND: "#c0392b",  # ダーク赤
    EnvironmentCode.PANIC_SELL: "#8e44ad",  # ダーク紫
}

RISK_LEVEL_NAMES: dict[RiskLevel, str] = {
    RiskLevel.LOW: "低",
    RiskLevel.MEDIUM: "中",
    RiskLevel.HIGH: "高",
    RiskLevel.EXTREME: "極高",
}

# 市場指数ETFシンボル
NIKKEI_ETF_SYMBOL = "1321.T"
TOPIX_ETF_SYMBOL = "1306.T"


def get_database_url() -> str:
    """環境変数からデータベースURLを構築する."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "swing_trading")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


@st.cache_resource
def get_db_session() -> Session:
    """DBセッションを取得（キャッシュ）."""
    database_url = get_database_url()
    engine = create_engine(database_url)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def get_index_prices(
    session: Session,
    symbol: str,
    start_date: date,
    end_date: date,
) -> pd.DataFrame | None:
    """市場指数ETFの価格データを取得."""
    repo = PostgresDailyPriceRepository(session)
    ticker = repo.get_or_create_ticker(symbol)

    # 分析に必要な遡り期間を含めて取得
    extended_start = start_date - timedelta(days=100)
    daily_prices = repo.get_by_ticker_and_date_range(
        ticker.ticker_id, extended_start, end_date
    )

    if not daily_prices:
        return None

    return repo.daily_prices_to_dataframe(daily_prices)


@st.cache_data(ttl=3600)
def analyze_period(
    _session: Session,
    universe_id: int,
    start_date: date,
    end_date: date,
) -> list[MarketRegime]:
    """期間内の各日の市場レジームを分析."""
    # 価格データ取得
    nikkei_df = get_index_prices(_session, NIKKEI_ETF_SYMBOL, start_date, end_date)
    topix_df = get_index_prices(_session, TOPIX_ETF_SYMBOL, start_date, end_date)

    if nikkei_df is None or topix_df is None:
        return []

    # ユニバース価格取得
    universe_repo = PostgresUniverseRepository(_session)
    extended_start = start_date - timedelta(days=50)
    universe_prices = universe_repo.get_universe_prices(
        universe_id, extended_start, end_date
    )

    # 分析実行
    analyzer = MarketRegimeAnalyzer()
    results: list[MarketRegime] = []

    # 分析対象日のリスト
    analysis_dates = pd.date_range(start=start_date, end=end_date, freq="B")

    for target_date in analysis_dates:
        target = target_date.date()

        # 対象日までのデータでフィルタ
        nikkei_subset = nikkei_df[nikkei_df.index <= target_date]
        topix_subset = topix_df[topix_df.index <= target_date]

        if len(nikkei_subset) < 30 or len(topix_subset) < 30:
            continue

        # ユニバース価格もフィルタ
        universe_subset = {}
        for symbol, df in universe_prices.items():
            filtered = df[df.index <= target_date]
            if len(filtered) >= 5:
                universe_subset[symbol] = filtered

        try:
            result = analyzer.analyze(
                nikkei_df=nikkei_subset,
                topix_df=topix_subset,
                universe_prices=universe_subset,
                end_date=target,
            )
            results.append(result)
        except Exception:
            continue

    return results


def create_price_chart(
    nikkei_df: pd.DataFrame,
    regimes: list[MarketRegime],
    start_date: date,
    end_date: date,
) -> go.Figure:
    """日経平均チャートと環境コードを表示."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=("日経225 ETF", "市場環境"),
    )

    # 期間でフィルタ
    mask = (nikkei_df.index >= pd.Timestamp(start_date)) & (
        nikkei_df.index <= pd.Timestamp(end_date)
    )
    filtered_df = nikkei_df[mask]

    # ローソク足チャート
    fig.add_trace(
        go.Candlestick(
            x=filtered_df.index,
            open=filtered_df["open"],
            high=filtered_df["high"],
            low=filtered_df["low"],
            close=filtered_df["close"],
            name="日経225 ETF",
        ),
        row=1,
        col=1,
    )

    # 環境コードのバー表示
    if regimes:
        dates = [r.analysis_date for r in regimes]
        colors = [ENVIRONMENT_COLORS.get(r.environment_code, "#999") for r in regimes]
        env_names = [
            ENVIRONMENT_NAMES.get(r.environment_code, "不明") for r in regimes
        ]

        fig.add_trace(
            go.Bar(
                x=dates,
                y=[1] * len(dates),
                marker_color=colors,
                text=env_names,
                textposition="inside",
                name="環境",
                hovertemplate="%{x}<br>%{text}<extra></extra>",
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        yaxis2=dict(showticklabels=False),
    )

    return fig


def create_risk_chart(regimes: list[MarketRegime]) -> go.Figure:
    """リスクスコアの推移チャート."""
    if not regimes:
        return go.Figure()

    dates = [r.analysis_date for r in regimes]
    scores = [r.risk_assessment.risk_score for r in regimes]

    fig = go.Figure()

    # リスクレベルの背景色
    fig.add_hrect(y0=0, y1=25, fillcolor="green", opacity=0.1, line_width=0)
    fig.add_hrect(y0=25, y1=50, fillcolor="yellow", opacity=0.1, line_width=0)
    fig.add_hrect(y0=50, y1=75, fillcolor="orange", opacity=0.1, line_width=0)
    fig.add_hrect(y0=75, y1=100, fillcolor="red", opacity=0.1, line_width=0)

    # ラインチャート
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode="lines+markers",
            name="リスクスコア",
            line=dict(color="#e74c3c", width=2),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title="リスクスコア推移",
        yaxis=dict(range=[0, 100], title="スコア"),
        height=300,
    )

    return fig


def create_adr_chart(regimes: list[MarketRegime]) -> go.Figure:
    """ADR（騰落レシオ）の推移チャート."""
    if not regimes:
        return go.Figure()

    dates = [r.analysis_date for r in regimes]
    short_adr = [
        r.market_breadth.advancing_declining_ratios.get("short_term", 100)
        for r in regimes
    ]
    medium_adr = [
        r.market_breadth.advancing_declining_ratios.get("medium_term", 100)
        for r in regimes
    ]

    fig = go.Figure()

    # 基準線
    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_hline(
        y=130, line_dash="dot", line_color="red", opacity=0.5, annotation_text="過熱"
    )
    fig.add_hline(
        y=70,
        line_dash="dot",
        line_color="blue",
        opacity=0.5,
        annotation_text="売られ過ぎ",
    )

    # 短期ADR
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=short_adr,
            mode="lines",
            name="短期ADR (5日)",
            line=dict(color="#3498db", width=2),
        )
    )

    # 中期ADR
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=medium_adr,
            mode="lines",
            name="中期ADR (25日)",
            line=dict(color="#2ecc71", width=2),
        )
    )

    fig.update_layout(
        title="騰落レシオ (ADR) 推移",
        yaxis=dict(title="ADR (%)"),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    return fig


def main() -> None:
    """メインアプリケーション."""
    st.set_page_config(
        page_title="市場レジーム分析",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 市場レジーム分析ダッシュボード")

    # サイドバー
    st.sidebar.header("分析設定")

    # DB接続
    try:
        session = get_db_session()
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        return

    # ユニバース選択
    universe_repo = PostgresUniverseRepository(session)
    latest_universe = universe_repo.get_latest()

    if latest_universe is None:
        st.error("ユニバースが登録されていません")
        return

    st.sidebar.info(f"ユニバース: {latest_universe.name}")

    # 期間選択
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "開始日",
            value=date.today() - timedelta(days=30),
            max_value=date.today(),
        )
    with col2:
        end_date = st.date_input(
            "終了日",
            value=date.today(),
            max_value=date.today(),
        )

    if start_date >= end_date:
        st.error("開始日は終了日より前に設定してください")
        return

    # 分析実行
    with st.spinner("分析中..."):
        regimes = analyze_period(
            session,
            latest_universe.universe_id,
            start_date,
            end_date,
        )

    if not regimes:
        st.warning("指定期間のデータが不足しています")
        return

    # 最新の分析結果サマリー
    latest = regimes[-1]
    env_name = ENVIRONMENT_NAMES.get(latest.environment_code, "不明")
    risk_name = RISK_LEVEL_NAMES.get(latest.risk_assessment.risk_level, "不明")

    st.header(f"現在の市場環境: {env_name}")

    # メトリクス
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta = None
        if len(regimes) >= 2:
            prev_score = regimes[-2].risk_assessment.risk_score
            curr_score = regimes[-1].risk_assessment.risk_score
            delta = curr_score - prev_score
        st.metric(
            f"リスクスコア ({risk_name})",
            f"{latest.risk_assessment.risk_score}",
            delta=delta,
            delta_color="inverse",
        )

    with col2:
        short_adr = latest.market_breadth.advancing_declining_ratios.get(
            "short_term", 100
        )
        st.metric("短期ADR", f"{short_adr:.1f}")

    with col3:
        st.metric("ATR%", f"{latest.volatility_analysis.atr_percent:.2f}%")

    with col4:
        tradeable = "✓ 可能" if latest.is_tradeable else "✗ 不可"
        st.metric("トレード可否", tradeable)

    st.divider()

    # チャート
    nikkei_df = get_index_prices(session, NIKKEI_ETF_SYMBOL, start_date, end_date)

    if nikkei_df is not None:
        st.plotly_chart(
            create_price_chart(nikkei_df, regimes, start_date, end_date),
            use_container_width=True,
        )

    # 下段のチャート
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(create_risk_chart(regimes), use_container_width=True)

    with col2:
        st.plotly_chart(create_adr_chart(regimes), use_container_width=True)

    # 環境コードの凡例
    st.sidebar.divider()
    st.sidebar.subheader("環境コード凡例")
    for code, name in ENVIRONMENT_NAMES.items():
        color = ENVIRONMENT_COLORS.get(code, "#999")
        st.sidebar.markdown(
            f'<span style="color:{color}">●</span> {name}',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
