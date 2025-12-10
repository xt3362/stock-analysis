"""Repository implementations for database persistence."""

from src.infrastructure.persistence.repositories.ticker_repository import (
    PostgresTickerRepository,
)

__all__ = ["PostgresTickerRepository"]
