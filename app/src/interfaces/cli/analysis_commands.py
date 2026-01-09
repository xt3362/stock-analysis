"""CLI commands for market analysis operations."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportArgumentType=false
# pyright: reportUnnecessaryComparison=false
# NOTE: pandas type stubs are incomplete, SQLAlchemy ORM Column typing issues

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated, Any

import typer
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.models.market_regime import (
    EnvironmentCode,
    MarketRegime,
    RiskLevel,
    Sentiment,
    TrendDirection,
    TrendType,
    VolatilityLevel,
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

app = typer.Typer(help="Analysis commands - 市場分析コマンド")

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

TREND_TYPE_NAMES: dict[TrendType, str] = {
    TrendType.TRENDING: "トレンド相場",
    TrendType.RANGING: "レンジ相場",
    TrendType.NEUTRAL: "中立",
}

TREND_DIRECTION_NAMES: dict[TrendDirection, str] = {
    TrendDirection.UPTREND: "上昇",
    TrendDirection.DOWNTREND: "下降",
    TrendDirection.SIDEWAYS: "横ばい",
}

VOLATILITY_NAMES: dict[VolatilityLevel, str] = {
    VolatilityLevel.LOW: "低",
    VolatilityLevel.NORMAL: "通常",
    VolatilityLevel.ELEVATED: "やや高",
    VolatilityLevel.HIGH: "高",
}

SENTIMENT_NAMES: dict[Sentiment, str] = {
    Sentiment.POSITIVE: "強気",
    Sentiment.NEUTRAL: "中立",
    Sentiment.NEGATIVE: "弱気",
}

RISK_LEVEL_NAMES: dict[RiskLevel, str] = {
    RiskLevel.LOW: "低リスク",
    RiskLevel.MEDIUM: "中リスク",
    RiskLevel.HIGH: "高リスク",
    RiskLevel.EXTREME: "極めて高リスク",
}

# 市場指数ETFシンボル
NIKKEI_ETF_SYMBOL = "1321.T"
TOPIX_ETF_SYMBOL = "1306.T"


def _get_database_url() -> str:
    """環境変数からデータベースURLを構築する."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "swing_trading")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def _format_table_output(regime: MarketRegime) -> str:
    """MarketRegimeをテーブル形式で整形する."""
    lines = []
    sep = "=" * 80

    lines.append(sep)
    lines.append("                          市場レジーム分析結果")
    lines.append(sep)
    lines.append(f"分析日: {regime.analysis_date}")
    lines.append("")

    # 環境分類
    env_name = ENVIRONMENT_NAMES.get(regime.environment_code, "不明")
    tradeable = "✓ 可能" if regime.is_tradeable else "✗ 不可"
    lines.append("■ 環境分類")
    lines.append(f"  コード: {regime.environment_code.value}（{env_name}）")
    lines.append(f"  トレード可否: {tradeable}")
    lines.append("")

    # トレンド分析
    trend = regime.trend_analysis
    trend_type_name = TREND_TYPE_NAMES.get(trend.trend_type, "不明")
    trend_dir_name = TREND_DIRECTION_NAMES.get(trend.trend_direction, "不明")
    lines.append("■ トレンド分析")
    lines.append(f"  種別: {trend.trend_type.value}（{trend_type_name}）")
    lines.append(f"  方向: {trend.trend_direction.value}（{trend_dir_name}）")
    lines.append(f"  ADX: {trend.adx_value:.1f} - {trend.adx_interpretation}")
    lines.append("")

    # ボラティリティ分析
    vol = regime.volatility_analysis
    vol_name = VOLATILITY_NAMES.get(vol.volatility_level, "不明")
    consensus = "✓" if vol.volatility_consensus else "✗"
    lines.append("■ ボラティリティ分析")
    lines.append(f"  水準: {vol.volatility_level.value}（{vol_name}）")
    lines.append(f"  ATR%: {vol.atr_percent:.2f}%")
    lines.append(f"  BB幅: {vol.bollinger_band_width:.1f}%")
    lines.append(f"  一致度: {consensus}")
    lines.append("")

    # センチメント分析
    sent = regime.sentiment_analysis
    sent_name = SENTIMENT_NAMES.get(sent.sentiment, "不明")
    nikkei_dir = TREND_DIRECTION_NAMES.get(sent.nikkei_trend, "不明")
    topix_dir = TREND_DIRECTION_NAMES.get(sent.topix_trend, "不明")
    lines.append("■ センチメント分析")
    lines.append(f"  判定: {sent.sentiment.value}（{sent_name}）")
    lines.append(f"  日経225: {sent.nikkei_trend.value}（{nikkei_dir}）")
    lines.append(f"  TOPIX: {sent.topix_trend.value}（{topix_dir}）")
    lines.append("")

    # 騰落レシオ
    breadth = regime.market_breadth
    short_adr = breadth.advancing_declining_ratios.get("short_term", 0.0)
    medium_adr = breadth.advancing_declining_ratios.get("medium_term", 0.0)
    lines.append("■ 騰落レシオ (ADR)")
    lines.append(f"  短期(5日): {short_adr:.1f}")
    lines.append(f"  中期(25日): {medium_adr:.1f}")
    lines.append(f"  乖離: {breadth.adr_divergence.value}")
    lines.append("")

    # リスク評価
    risk = regime.risk_assessment
    risk_name = RISK_LEVEL_NAMES.get(risk.risk_level, "不明")
    lines.append("■ リスク評価")
    lines.append(f"  スコア: {risk.risk_score} / 100")
    lines.append(f"  レベル: {risk.risk_level.value}（{risk_name}）")
    lines.append(sep)

    return "\n".join(lines)


def _format_json_output(regime: MarketRegime) -> str:
    """MarketRegimeをJSON形式で整形する."""
    data: dict[str, Any] = {
        "analysis_date": regime.analysis_date.isoformat(),
        "environment_code": regime.environment_code.value,
        "is_tradeable": regime.is_tradeable,
        "trend_analysis": {
            "trend_type": regime.trend_analysis.trend_type.value,
            "trend_direction": regime.trend_analysis.trend_direction.value,
            "adx_value": regime.trend_analysis.adx_value,
            "adx_interpretation": regime.trend_analysis.adx_interpretation,
        },
        "volatility_analysis": {
            "volatility_level": regime.volatility_analysis.volatility_level.value,
            "atr_percent": regime.volatility_analysis.atr_percent,
            "bollinger_band_width": regime.volatility_analysis.bollinger_band_width,
            "volatility_consensus": regime.volatility_analysis.volatility_consensus,
        },
        "sentiment_analysis": {
            "sentiment": regime.sentiment_analysis.sentiment.value,
            "nikkei_trend": regime.sentiment_analysis.nikkei_trend.value,
            "topix_trend": regime.sentiment_analysis.topix_trend.value,
        },
        "market_breadth": {
            "advancing_declining_ratios": (
                regime.market_breadth.advancing_declining_ratios
            ),
            "adr_divergence": regime.market_breadth.adr_divergence.value,
        },
        "risk_assessment": {
            "risk_level": regime.risk_assessment.risk_level.value,
            "risk_score": regime.risk_assessment.risk_score,
        },
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def _get_index_ohlcv(
    session: Session,
    symbol: str,
    end_date: date,
    days: int = 60,
) -> tuple[bool, Any]:
    """
    市場指数ETFのOHLCVデータを取得する.

    Returns:
        (成功フラグ, DataFrame or エラーメッセージ)
    """
    repo = PostgresDailyPriceRepository(session)

    # Tickerを取得
    ticker = repo.get_or_create_ticker(symbol)
    if ticker is None:
        return (False, f"シンボル {symbol} が見つかりません")

    # 日付範囲を計算（営業日を考慮して余裕を持って取得）
    start_date = end_date - timedelta(days=days * 2)

    # 価格データ取得
    daily_prices = repo.get_by_ticker_and_date_range(
        ticker.ticker_id, start_date, end_date
    )

    if not daily_prices:
        return (False, f"シンボル {symbol} の価格データがありません")

    # DataFrameに変換
    df = repo.daily_prices_to_dataframe(daily_prices)

    if len(df) < 20:
        return (False, f"シンボル {symbol} のデータが不足しています（{len(df)}日分）")

    return (True, df)


@app.command(name="market-regime")
def market_regime(
    universe: Annotated[
        str | None,
        typer.Option(
            "--universe",
            "-u",
            help="使用するユニバース名（指定なしで最新のユニバースを使用）",
        ),
    ] = None,
    analysis_date: Annotated[
        str | None,
        typer.Option(
            "--date",
            "-d",
            help="分析基準日（YYYY-MM-DD形式）",
        ),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="出力形式（table/json）",
        ),
    ] = "table",
) -> None:
    """
    市場レジーム分析を実行し結果を表示する.

    8パターンの市場環境分類とリスクスコアを計算します。

    Examples:

        # 基本実行（最新ユニバース、最新日付）
        stock-cli analysis market-regime

        # ユニバース指定
        stock-cli analysis market-regime -u "test_universe"

        # 日付指定
        stock-cli analysis market-regime -d 2024-01-15

        # JSON出力
        stock-cli analysis market-regime -f json
    """
    # 出力形式の検証
    if output_format not in ("table", "json"):
        typer.echo(
            f"Error: 無効な出力形式です: {output_format}（table/json）", err=True
        )
        raise typer.Exit(code=1)

    # 日付の解析
    parsed_date: date | None = None
    if analysis_date:
        try:
            parsed_date = date.fromisoformat(analysis_date)
        except ValueError:
            typer.echo(
                f"Error: 無効な日付形式です: {analysis_date}（YYYY-MM-DD）", err=True
            )
            raise typer.Exit(code=1) from None

    # DB接続
    try:
        database_url = _get_database_url()
        engine = create_engine(database_url)
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
    except Exception as e:
        typer.echo(f"Error: データベース接続に失敗しました: {e}", err=True)
        raise typer.Exit(code=1) from None

    try:
        universe_repo = PostgresUniverseRepository(session)

        # ユニバース取得
        if universe:
            universe_obj = universe_repo.get_by_name(universe)
            if universe_obj is None:
                typer.echo(f"Error: ユニバース '{universe}' が見つかりません", err=True)
                raise typer.Exit(code=1)
        else:
            universe_obj = universe_repo.get_latest()
            if universe_obj is None:
                typer.echo("Error: ユニバースが存在しません", err=True)
                raise typer.Exit(code=1)

        typer.echo(f"ユニバース: {universe_obj.name}")

        # 分析基準日の決定
        target_date = parsed_date or date.today()
        typer.echo(f"分析基準日: {target_date}")
        typer.echo("")

        # 市場指数ETF価格データ取得
        typer.echo("市場データを取得中...")

        success, nikkei_result = _get_index_ohlcv(
            session, NIKKEI_ETF_SYMBOL, target_date
        )
        if not success:
            typer.echo(
                f"Error: 日経225 ETF ({NIKKEI_ETF_SYMBOL}): {nikkei_result}",
                err=True,
            )
            raise typer.Exit(code=1)
        nikkei_df = nikkei_result

        success, topix_result = _get_index_ohlcv(session, TOPIX_ETF_SYMBOL, target_date)
        if not success:
            typer.echo(
                f"Error: TOPIX ETF ({TOPIX_ETF_SYMBOL}): {topix_result}",
                err=True,
            )
            raise typer.Exit(code=1)
        topix_df = topix_result

        typer.echo(f"  日経225 ETF: {len(nikkei_df)}日分")
        typer.echo(f"  TOPIX ETF: {len(topix_df)}日分")

        # ユニバース銘柄価格データ取得（ADR計算用）
        start_for_adr = target_date - timedelta(days=50)
        universe_prices = universe_repo.get_universe_prices(
            universe_obj.universe_id,
            start_for_adr,
            target_date,
        )
        typer.echo(f"  ユニバース銘柄: {len(universe_prices)}銘柄")
        typer.echo("")

        # 分析実行
        typer.echo("分析を実行中...")
        analyzer = MarketRegimeAnalyzer()
        result = analyzer.analyze(
            nikkei_df=nikkei_df,
            topix_df=topix_df,
            universe_prices=universe_prices,
            end_date=target_date,
        )
        typer.echo("")

        # 結果出力
        if output_format == "json":
            typer.echo(_format_json_output(result))
        else:
            typer.echo(_format_table_output(result))

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: 分析に失敗しました: {e}", err=True)
        raise typer.Exit(code=1) from None
    finally:
        session.close()
