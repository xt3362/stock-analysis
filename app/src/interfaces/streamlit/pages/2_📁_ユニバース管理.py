"""ユニバース管理ページ."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportUnnecessaryComparison=false, reportAttributeAccessIssue=false
# pyright: reportGeneralTypeIssues=false
# NOTE: Streamlit/SQLAlchemy type stubs are incomplete

import os
from datetime import date
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.persistence.models import Universe, UniverseMode
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


def delete_universe(session: Session, universe_id: int) -> bool:
    """ユニバースを削除."""
    universe = (
        session.query(Universe).filter(Universe.universe_id == universe_id).first()
    )
    if universe:
        session.delete(universe)
        session.commit()
        return True
    return False


def main() -> None:
    """ユニバース管理ページ."""
    st.title("📁 ユニバース管理")

    # DB接続
    try:
        session = get_db_session()
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        return

    ticker_repo = PostgresTickerRepository(session)
    universe_repo = PostgresUniverseRepository(session)

    # タブ
    tab1, tab2 = st.tabs(["新規作成", "既存を表示"])

    # ========== 新規作成タブ ==========
    with tab1:
        st.subheader("新規ユニバース作成")

        # 入力フォーム
        col1, col2 = st.columns(2)
        with col1:
            universe_name = st.text_input("ユニバース名", placeholder="my_universe")
        with col2:
            universe_desc = st.text_input("説明（任意）", placeholder="説明を入力")

        # 銘柄一覧取得
        all_tickers = ticker_repo.get_all()

        if not all_tickers:
            st.warning("Tickerテーブルに銘柄が登録されていません")
            return

        # 検索フィルタ
        search_query = st.text_input(
            "銘柄検索",
            placeholder="シンボルまたは銘柄名で検索...",
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

        # セッションステートで選択を管理
        if "selected_ticker_ids" not in st.session_state:
            st.session_state.selected_ticker_ids = set()

        # 銘柄選択UI
        st.write(f"表示中: {len(filtered_tickers)}銘柄 / 全{len(all_tickers)}銘柄")

        # データフレーム形式で表示
        ticker_data = []
        for t in filtered_tickers[:100]:  # 最大100件表示
            ticker_data.append(
                {
                    "ticker_id": t.ticker_id,
                    "symbol": t.symbol,
                    "name": t.name or "",
                    "sector": t.sector or "",
                }
            )

        if ticker_data:
            # マルチセレクト
            options = {
                f"{t['symbol']} - {t['name']}": t["ticker_id"] for t in ticker_data
            }

            selected_labels = st.multiselect(
                "銘柄を選択",
                options=list(options.keys()),
                default=[
                    label
                    for label, tid in options.items()
                    if tid in st.session_state.selected_ticker_ids
                ],
            )

            # 選択状態を更新
            st.session_state.selected_ticker_ids = {
                options[label] for label in selected_labels
            }

        st.info(f"選択中: {len(st.session_state.selected_ticker_ids)}銘柄")

        # 作成ボタン
        if st.button("ユニバースを作成", type="primary"):
            if not universe_name:
                st.error("ユニバース名を入力してください")
            elif not st.session_state.selected_ticker_ids:
                st.error("銘柄を1つ以上選択してください")
            else:
                try:
                    # ユニバース作成
                    new_universe = Universe(
                        name=universe_name,
                        mode=UniverseMode.PRODUCTION,
                        as_of_date=date.today(),
                        config_name="streamlit_ui",
                        description=universe_desc or None,
                        total_symbols=len(st.session_state.selected_ticker_ids),
                    )
                    universe_repo.save(new_universe)

                    # シンボル追加
                    for ticker_id in st.session_state.selected_ticker_ids:
                        universe_repo.add_symbol(
                            new_universe.universe_id,
                            ticker_id,
                        )

                    session.commit()

                    st.success(
                        f"ユニバース '{universe_name}' を作成しました "
                        f"({len(st.session_state.selected_ticker_ids)}銘柄)"
                    )

                    # 選択をクリア
                    st.session_state.selected_ticker_ids = set()
                    st.rerun()

                except Exception as e:
                    session.rollback()
                    st.error(f"作成に失敗しました: {e}")

    # ========== 既存を表示タブ ==========
    with tab2:
        st.subheader("既存ユニバース一覧")

        universes = get_all_universes(session)

        if not universes:
            st.info("ユニバースがまだ作成されていません")
            return

        # ユニバース選択
        universe_options = {
            f"{u.name} ({u.total_symbols}銘柄) - {u.as_of_date}": u.universe_id
            for u in universes
        }

        selected_universe_label = st.selectbox(
            "ユニバースを選択",
            options=list(universe_options.keys()),
        )

        if selected_universe_label:
            selected_universe_id = universe_options[selected_universe_label]
            selected_universe = universe_repo.get_by_id(selected_universe_id)

            if selected_universe:
                st.divider()

                # 詳細表示
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("銘柄数", selected_universe.total_symbols)
                with col2:
                    st.metric("作成日", str(selected_universe.as_of_date))
                with col3:
                    st.metric("モード", selected_universe.mode.value)

                if selected_universe.description:
                    st.write(f"**説明:** {selected_universe.description}")

                # 銘柄リスト
                st.subheader("含まれる銘柄")
                symbols = universe_repo.get_symbols(selected_universe_id)

                if symbols:
                    # 3列で表示
                    cols = st.columns(3)
                    for i, symbol in enumerate(symbols):
                        cols[i % 3].write(f"• {symbol}")
                else:
                    st.write("銘柄がありません")

                # 削除ボタン
                st.divider()
                if st.button("このユニバースを削除", type="secondary"):
                    if delete_universe(session, selected_universe_id):
                        name = selected_universe.name
                        st.success(f"ユニバース '{name}' を削除しました")
                        st.rerun()
                    else:
                        st.error("削除に失敗しました")


# ページ実行
main()
