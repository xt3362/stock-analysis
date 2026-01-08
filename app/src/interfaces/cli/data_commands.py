"""CLI commands for data operations."""

import os
from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env file from project root
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)

from src.application.commands.collect_data import (  # noqa: E402
    CollectDataHandler,
    FetchStockDataCommand,
)
from src.domain.services.analysis.technical_indicators import (  # noqa: E402
    TechnicalIndicatorService,
)
from src.infrastructure.external.yahoo_finance import YahooFinanceClient  # noqa: E402
from src.infrastructure.persistence.repositories.daily_price_repository import (  # noqa: E402
    PostgresDailyPriceRepository,
)

app = typer.Typer(help="Data fetching and management commands")


def _get_database_url() -> str:
    """環境変数からデータベースURLを構築する."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "swing_trading")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


@app.command()
def fetch(
    symbols: Annotated[
        list[str],
        typer.Option(
            "--symbol",
            "-s",
            help="Stock symbol(s) to fetch (e.g., 7203.T, AAPL). Can specify multiple.",
        ),
    ],
    start_date: Annotated[
        str | None,
        typer.Option(
            "--start-date",
            help="Start date (YYYY-MM-DD)",
        ),
    ] = None,
    end_date: Annotated[
        str | None,
        typer.Option(
            "--end-date",
            help="End date (YYYY-MM-DD)",
        ),
    ] = None,
    period: Annotated[
        str | None,
        typer.Option(
            "--period",
            "-p",
            help="Period (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)",
        ),
    ] = None,
) -> None:
    """
    Fetch stock price data from Yahoo Finance and save to database.

    Examples:

        # Fetch last month of data for Toyota
        uv run python -m src.interfaces.cli.main data fetch -s 7203.T --period 1mo

        # Fetch specific date range
        uv run python -m src.interfaces.cli.main data fetch -s AAPL \
--start-date 2024-01-01 --end-date 2024-12-31

        # Fetch multiple symbols
        uv run python -m src.interfaces.cli.main data fetch -s 7203.T -s 9984.T \
--period 3mo
    """
    # Validate parameters
    if not symbols:
        typer.echo("Error: At least one symbol is required", err=True)
        raise typer.Exit(code=1)

    if period and (start_date or end_date):
        typer.echo(
            "Error: Cannot use --period with --start-date/--end-date",
            err=True,
        )
        raise typer.Exit(code=1)

    if not period and not start_date:
        typer.echo(
            "Error: Must specify --period or --start-date",
            err=True,
        )
        raise typer.Exit(code=1)

    # Parse dates
    parsed_start_date: date | None = None
    parsed_end_date: date | None = None

    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            typer.echo(f"Error: Invalid start date format: {start_date}", err=True)
            raise typer.Exit(code=1) from None

    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            typer.echo(f"Error: Invalid end date format: {end_date}", err=True)
            raise typer.Exit(code=1) from None

    # Create dependencies
    data_source = YahooFinanceClient()

    # Create database session
    try:
        database_url = _get_database_url()
        engine = create_engine(database_url)
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
    except Exception as e:
        typer.echo(f"Error: Failed to connect to database: {e}", err=True)
        raise typer.Exit(code=1) from None

    try:
        daily_price_repository = PostgresDailyPriceRepository(session)
        indicator_service = TechnicalIndicatorService()
        handler = CollectDataHandler(
            data_source=data_source,
            daily_price_repository=daily_price_repository,
            indicator_service=indicator_service,
        )

        # Execute command
        command = FetchStockDataCommand(
            symbols=list(symbols),
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            period=period,
        )

        typer.echo(f"Fetching data for: {', '.join(symbols)}...")

        result = handler.handle(command)

        # Commit transaction
        session.commit()

        # Display results
        if result.errors:
            typer.echo(f"\nWarnings: {len(result.errors)} symbol(s) had errors:")
            for symbol, error in result.errors.items():
                typer.echo(f"  - {symbol}: {error}", err=True)

        if result.success_count > 0:
            typer.echo(f"\nSuccessfully fetched {result.success_count} symbol(s):")
            for symbol, df in result.data.items():
                saved = result.saved_records.get(symbol, 0)
                typer.echo(f"  - {symbol}: {len(df)} rows fetched, {saved} rows saved")
        else:
            typer.echo("No data was fetched.", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        session.rollback()
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from None
    finally:
        session.close()
