"""イベント同期ページ.

決算日・配当日をYahoo Financeから取得してDBに同期する。
"""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportUnnecessaryComparison=false, reportAttributeAccessIssue=false
# pyright: reportGeneralTypeIssues=false, reportAssignmentType=false
# NOTE: Streamlit/SQLAlchemy type stubs are incomplete

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.application.services import EventScheduleSyncService
from src.infrastructure.external.yahoo_finance import YahooFinanceClient
from src.infrastructure.persistence.models import Universe
from src.infrastructure.persistence.repositories import (
    PostgresDividendScheduleRepository,
    PostgresEarningsScheduleRepository,
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
    return list(session.query(Universe).order_by(Universe.created_at.desc()).all())


def main() -> None:
    """イベント同期ページ."""
    st.title("🔄 イベント同期")
    st.markdown("Yahoo Financeから決算日・配当日を取得してDBに同期します。")

    # DB接続
    try:
        session = get_db_session()
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        return

    ticker_repo = PostgresTickerRepository(session)
    universe_repo = PostgresUniverseRepository(session)

    # サービス初期化
    yahoo_client = YahooFinanceClient()
    earnings_repo = PostgresEarningsScheduleRepository(session)
    dividend_repo = PostgresDividendScheduleRepository(session)
    sync_service = EventScheduleSyncService(
        yahoo_client=yahoo_client,
        earnings_repo=earnings_repo,
        dividend_repo=dividend_repo,
    )

    # ========== タブ ==========
    tab1, tab2 = st.tabs(["ユニバース同期", "個別銘柄同期"])

    # ---------- タブ1: ユニバース同期 ----------
    with tab1:
        st.subheader("ユニバースから一括同期")

        universes = get_all_universes(session)

        if not universes:
            st.warning("ユニバースが登録されていません")
        else:
            universe_options = {
                f"{u.name} ({u.total_symbols}銘柄)": u.universe_id for u in universes
            }

            selected_universe_label = st.selectbox(
                "ユニバースを選択",
                options=list(universe_options.keys()),
                key="sync_universe_selectbox",
            )

            # 決算日取得数
            earnings_limit = st.number_input(
                "決算日取得数",
                min_value=1,
                max_value=12,
                value=4,
                help="各銘柄で取得する決算日の数",
                key="universe_earnings_limit",
            )

            if selected_universe_label:
                selected_universe_id = universe_options[selected_universe_label]
                symbols = universe_repo.get_symbols(selected_universe_id)
                ticker_ids = universe_repo.get_ticker_ids(selected_universe_id)

                if symbols:
                    st.info(f"対象銘柄: {len(symbols)}件")

                    # 銘柄一覧を表示（展開可能）
                    with st.expander("銘柄一覧を表示"):
                        cols = st.columns(4)
                        for i, symbol in enumerate(symbols):
                            cols[i % 4].write(f"• {symbol}")

                    # 同期実行ボタン
                    if st.button(
                        "🔄 同期実行", type="primary", key="universe_sync_button"
                    ):
                        symbol_pairs = list(zip(symbols, ticker_ids, strict=True))

                        with st.status("同期中...", expanded=True) as status:
                            st.write(f"対象銘柄: {len(symbol_pairs)}件")

                            try:
                                results = sync_service.sync_symbols(
                                    symbols=symbol_pairs,
                                    earnings_limit=int(earnings_limit),
                                )

                                # コミット
                                session.commit()

                                # 結果集計
                                success_count = sum(1 for r in results if r.success)
                                error_count = len(results) - success_count

                                if success_count > 0:
                                    status.update(label="完了", state="complete")
                                    st.success(f"✓ {success_count}銘柄の同期が完了")

                                # 詳細結果
                                st.subheader("同期結果")

                                for result in results:
                                    div = "配当あり" if result.dividend_synced else ""
                                    if result.success:
                                        msg = f"決算{result.earnings_synced}件 {div}"
                                        st.write(f"✓ **{result.symbol}**: {msg}")
                                    else:
                                        err = ", ".join(result.errors)
                                        st.error(f"✗ **{result.symbol}**: {err}")

                                if error_count > 0:
                                    st.warning(f"⚠ {error_count}銘柄でエラーが発生")

                            except Exception as e:
                                session.rollback()
                                status.update(label="エラー", state="error")
                                st.error(f"同期に失敗しました: {e}")

    # ---------- タブ2: 個別銘柄同期 ----------
    with tab2:
        st.subheader("個別銘柄を選択して同期")

        all_tickers = ticker_repo.get_all()

        if not all_tickers:
            st.warning("Tickerテーブルに銘柄が登録されていません")
        else:
            # 検索フィルタ
            search_query = st.text_input(
                "銘柄検索",
                placeholder="シンボルまたは銘柄名で検索...",
                key="sync_ticker_search",
            )

            # フィルタリング
            filtered_tickers = all_tickers
            if search_query:
                query_lower = search_query.lower()
                filtered_tickers = [
                    t
                    for t in all_tickers
                    if query_lower in (t.symbol or "").lower()
                    or query_lower in (t.name or "").lower()
                ]

            st.write(f"表示中: {len(filtered_tickers)}銘柄 / 全{len(all_tickers)}銘柄")

            # マルチセレクト
            ticker_options = {
                f"{t.symbol} - {t.name or ''}": (t.symbol, t.ticker_id)
                for t in filtered_tickers[:200]  # 最大200件
            }

            selected_ticker_labels = st.multiselect(
                "銘柄を選択",
                options=list(ticker_options.keys()),
                key="sync_ticker_multiselect",
            )

            selected_tickers = [
                ticker_options[label] for label in selected_ticker_labels
            ]

            # 決算日取得数
            earnings_limit_individual = st.number_input(
                "決算日取得数",
                min_value=1,
                max_value=12,
                value=4,
                help="各銘柄で取得する決算日の数",
                key="individual_earnings_limit",
            )

            if selected_tickers:
                st.info(f"選択中: {len(selected_tickers)}銘柄")

                # 同期実行ボタン
                if st.button(
                    "🔄 同期実行", type="primary", key="individual_sync_button"
                ):
                    with st.status("同期中...", expanded=True) as status:
                        st.write(f"対象銘柄: {len(selected_tickers)}件")

                        try:
                            results = sync_service.sync_symbols(
                                symbols=selected_tickers,
                                earnings_limit=int(earnings_limit_individual),
                            )

                            # コミット
                            session.commit()

                            # 結果集計
                            success_count = sum(1 for r in results if r.success)
                            error_count = len(results) - success_count

                            if success_count > 0:
                                status.update(label="完了", state="complete")
                                st.success(f"✓ {success_count}銘柄の同期が完了")

                            # 詳細結果
                            st.subheader("同期結果")

                            for result in results:
                                div = "配当あり" if result.dividend_synced else ""
                                if result.success:
                                    msg = f"決算{result.earnings_synced}件 {div}"
                                    st.write(f"✓ **{result.symbol}**: {msg}")
                                else:
                                    err = ", ".join(result.errors)
                                    st.error(f"✗ **{result.symbol}**: {err}")

                            if error_count > 0:
                                st.warning(f"⚠ {error_count}銘柄でエラーが発生")

                        except Exception as e:
                            session.rollback()
                            status.update(label="エラー", state="error")
                            st.error(f"同期に失敗しました: {e}")


# ページ実行
main()
