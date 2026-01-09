"""Stock Analysis Dashboard - メインエントリポイント."""

import streamlit as st

st.set_page_config(
    page_title="Stock Analysis",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Stock Analysis Dashboard")

st.markdown(
    """
    ## ようこそ

    左のサイドバーからページを選択してください。

    ### 利用可能なページ

    - **📊 市場レジーム**: 市場環境の分析とリスク評価
    - **📁 ユニバース管理**: 銘柄ユニバースの作成と管理
    """
)
