"""Main CLI entry point."""

import typer

from src.interfaces.cli.data_commands import app as data_app

app = typer.Typer(
    name="stock-cli",
    help="Stock analysis CLI tool - yfinanceを使用した株価データ取得ツール",
    add_completion=False,
)

app.add_typer(data_app, name="data")


@app.callback()
def main() -> None:
    """Stock Analysis CLI."""
    pass


if __name__ == "__main__":
    app()
