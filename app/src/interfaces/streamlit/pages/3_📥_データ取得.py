"""データ取得ページ."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportUnnecessaryComparison=false, reportAttributeAccessIssue=false
# pyright: reportGeneralTypeIssues=false, reportAssignmentType=false
# NOTE: Streamlit/SQLAlchemy type stubs are incomplete

import os
import re
from datetime import date, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.application.commands.collect_data import (
    CollectDataHandler,
    FetchStockDataCommand,
    FetchStockDataResult,
)
from src.domain.services.analysis.technical_indicators import (
    TechnicalIndicatorService,
)
from src.infrastructure.external.yahoo_finance import YahooFinanceClient
from src.infrastructure.persistence.models import Universe
from src.infrastructure.persistence.repositories.daily_price_repository import (
    PostgresDailyPriceRepository,
)
from src.infrastructure.persistence.repositories.ticker_repository import (
    PostgresTickerRepository,
)
from src.infrastructure.persistence.repositories.universe_repository import (
    PostgresUniverseRepository,
)

# Load .env file from project root
_env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(_env_path)

# 期間プリセット
PERIOD_OPTIONS = {
    "1日": "1d",
    "5日": "5d",
    "1ヶ月": "1mo",
    "3ヶ月": "3mo",
    "6ヶ月": "6mo",
    "1年": "1y",
    "2年": "2y",
    "5年": "5y",
    "10年": "10y",
    "年初来": "ytd",
    "全期間": "max",
}


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


def get_all_universes(session: Session) -> list[Universe]:
    """全ユニバースを取得."""
    return list(
        session.query(Universe).order_by(Universe.created_at.desc()).all()
    )


def parse_symbols(input_text: str) -> list[str]:
    """
    入力テキストからシンボルリストをパースする.

    カンマ、改行、スペースで分割し、空白をトリム。
    .Tサフィックスがない場合は自動付与（数字のみの場合）。
    """
    if not input_text.strip():
        return []

    # カンマ、改行、スペースで分割
    symbols = re.split(r"[,\s\n]+", input_text.strip())

    # 空白トリムとフィルタ
    symbols = [s.strip().upper() for s in symbols if s.strip()]

    # 数字のみの場合は.Tを付与
    processed = []
    for s in symbols:
        if s.isdigit():
            processed.append(f"{s}.T")
        else:
            processed.append(s)

    return processed


def execute_data_fetch(
    symbols: list[str],
    start_date: date | None,
    end_date: date | None,
    period: str | None,
    session: Session,
) -> FetchStockDataResult:
    """データ取得を実行する."""
    data_source = YahooFinanceClient()
    daily_price_repository = PostgresDailyPriceRepository(session)
    indicator_service = TechnicalIndicatorService()

    handler = CollectDataHandler(
        data_source=data_source,
        daily_price_repository=daily_price_repository,
        indicator_service=indicator_service,
    )

    command = FetchStockDataCommand(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )

    return handler.handle(command)


def main() -> None:
    """データ取得ページ."""
    st.title("📥 データ取得")
    st.markdown("Yahoo Financeから株価データを取得してDBに保存します。")

    # DB接続
    try:
        session = get_db_session()
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        return

    ticker_repo = PostgresTickerRepository(session)
    universe_repo = PostgresUniverseRepository(session)

    # セッションステートで選択銘柄を管理
    if "data_fetch_symbols" not in st.session_state:
        st.session_state.data_fetch_symbols = []
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0

    # ========== 銘柄選択（3タブ）==========
    tab1, tab2, tab3 = st.tabs(["Ticker一覧", "ユニバース", "新規シンボル"])

    symbols_from_ticker: list[str] = []
    symbols_from_universe: list[str] = []
    symbols_from_input: list[str] = []

    # ---------- タブ1: Ticker一覧から選択 ----------
    with tab1:
        st.subheader("登録済みTickerから選択")

        all_tickers = ticker_repo.get_all()

        if not all_tickers:
            st.warning("Tickerテーブルに銘柄が登録されていません")
        else:
            # 検索フィルタ
            search_query = st.text_input(
                "銘柄検索",
                placeholder="シンボルまたは銘柄名で検索...",
                key="ticker_search",
            )

            # フィルタリング
            filtered_tickers = all_tickers
            if search_query:
                query_lower = search_query.lower()
                filtered_tickers = [
                    t for t in all_tickers
                    if query_lower in (t.symbol or "").lower()
                    or query_lower in (t.name or "").lower()
                ]

            st.write(f"表示中: {len(filtered_tickers)}銘柄 / 全{len(all_tickers)}銘柄")

            # マルチセレクト
            ticker_options = {
                f"{t.symbol} - {t.name or ''}": t.symbol
                for t in filtered_tickers[:200]  # 最大200件
            }

            selected_ticker_labels = st.multiselect(
                "銘柄を選択",
                options=list(ticker_options.keys()),
                key="ticker_multiselect",
            )

            symbols_from_ticker = [
                ticker_options[label] for label in selected_ticker_labels
            ]

            if symbols_from_ticker:
                st.info(f"選択中: {len(symbols_from_ticker)}銘柄")

    # ---------- タブ2: ユニバースから選択 ----------
    with tab2:
        st.subheader("ユニバースから選択")

        universes = get_all_universes(session)

        if not universes:
            st.warning("ユニバースが登録されていません")
        else:
            universe_options = {
                f"{u.name} ({u.total_symbols}銘柄)": u.universe_id
                for u in universes
            }

            selected_universe_label = st.selectbox(
                "ユニバースを選択",
                options=list(universe_options.keys()),
                key="universe_selectbox",
            )

            if selected_universe_label:
                selected_universe_id = universe_options[selected_universe_label]
                symbols_from_universe = universe_repo.get_symbols(selected_universe_id)

                if symbols_from_universe:
                    st.info(f"含まれる銘柄: {len(symbols_from_universe)}件")

                    # 銘柄一覧を表示（展開可能）
                    with st.expander("銘柄一覧を表示"):
                        cols = st.columns(4)
                        for i, symbol in enumerate(symbols_from_universe):
                            cols[i % 4].write(f"• {symbol}")

    # ---------- タブ3: 新規シンボル入力 ----------
    with tab3:
        st.subheader("新規シンボル入力")

        st.markdown("""
        - カンマ、改行、スペースで区切って複数入力可能
        - 数字のみの場合は自動で`.T`を付与（例: `7203` → `7203.T`）
        - 取得成功時にtickersテーブルへ自動登録
        """)

        symbol_input = st.text_area(
            "銘柄コード",
            placeholder="7203, 9984\n6758",
            height=100,
            key="symbol_input",
        )

        symbols_from_input = parse_symbols(symbol_input)

        if symbols_from_input:
            st.info(f"入力された銘柄: {', '.join(symbols_from_input)}")

    st.divider()

    # ========== 期間選択 ==========
    st.subheader("期間設定")

    period_mode = st.radio(
        "期間指定方法",
        options=["プリセット期間", "日付範囲指定"],
        horizontal=True,
        key="period_mode",
    )

    selected_period: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    if period_mode == "プリセット期間":
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_period_label = st.selectbox(
                "期間",
                options=list(PERIOD_OPTIONS.keys()),
                index=3,  # デフォルト: 3ヶ月
                key="period_select",
            )
            selected_period = PERIOD_OPTIONS[selected_period_label]
    else:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "開始日",
                value=date.today() - timedelta(days=90),
                key="start_date",
            )
        with col2:
            end_date = st.date_input(
                "終了日",
                value=date.today(),
                key="end_date",
            )

        # バリデーション
        if start_date and end_date and start_date >= end_date:
            st.error("開始日は終了日より前に設定してください")

    st.divider()

    # ========== 取得対象の確定 ==========
    # 各タブで選択された銘柄を統合
    all_selected_symbols: list[str] = []
    source_description = ""

    if symbols_from_ticker:
        all_selected_symbols = symbols_from_ticker
        source_description = "Ticker一覧"
    elif symbols_from_universe:
        all_selected_symbols = symbols_from_universe
        source_description = "ユニバース"
    elif symbols_from_input:
        all_selected_symbols = symbols_from_input
        source_description = "新規シンボル"

    # 取得対象の表示
    if all_selected_symbols:
        count = len(all_selected_symbols)
        st.markdown(f"**取得対象**: {count}銘柄 ({source_description})")
    else:
        st.warning("銘柄を選択または入力してください")

    # ========== 実行ボタン ==========
    disabled = not all_selected_symbols
    if st.button("🚀 データ取得を実行", type="primary", disabled=disabled):
        # バリデーション
        if not selected_period and not start_date:
            st.error("期間を指定してください")
        elif (
            period_mode == "日付範囲指定"
            and start_date
            and end_date
            and start_date >= end_date
        ):
            st.error("開始日は終了日より前に設定してください")
        else:
            # 実行
            with st.status("データ取得中...", expanded=True) as status:
                st.write(f"対象銘柄: {len(all_selected_symbols)}件")
                st.write(f"取得元: {source_description}")

                try:
                    result = execute_data_fetch(
                        symbols=all_selected_symbols,
                        start_date=start_date,
                        end_date=end_date,
                        period=selected_period,
                        session=session,
                    )

                    # コミット
                    session.commit()

                    # 結果表示
                    if result.success_count > 0:
                        status.update(label="完了", state="complete")
                        st.success(
                            f"✓ {result.success_count}銘柄のデータを取得しました"
                        )

                        # 詳細結果
                        st.subheader("取得結果")
                        for symbol, df in result.data.items():
                            saved = result.saved_records.get(symbol, 0)
                            st.write(f"• **{symbol}**: {len(df)}行取得, {saved}行保存")
                    else:
                        status.update(label="データなし", state="error")
                        st.warning("データを取得できませんでした")

                    # エラー表示
                    if result.errors:
                        st.subheader("エラー")
                        for symbol, error in result.errors.items():
                            st.error(f"• {symbol}: {error}")

                except Exception as e:
                    session.rollback()
                    status.update(label="エラー", state="error")
                    st.error(f"データ取得に失敗しました: {e}")


# ページ実行
main()
