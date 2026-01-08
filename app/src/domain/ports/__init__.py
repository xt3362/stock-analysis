"""Domain ports (interfaces) for dependency inversion."""

from src.domain.ports.stock_data_source import StockDataSource
from src.domain.ports.ticker_repository import TickerRepository

__all__ = ["StockDataSource", "TickerRepository"]
