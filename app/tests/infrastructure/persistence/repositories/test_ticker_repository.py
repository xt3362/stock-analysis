"""Tests for PostgresTickerRepository."""

# pyright: reportArgumentType=false
# pyright: reportGeneralTypeIssues=false
# NOTE: Above suppresses SQLAlchemy Column type issues in tests.
# At runtime, Column values are actual Python types, but static analysis
# sees them as Column[T] objects.

from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import Ticker
from src.infrastructure.persistence.repositories import PostgresTickerRepository


class TestPostgresTickerRepository:
    """Test cases for PostgresTickerRepository."""

    def test_save_and_get_by_id(self, session: Session) -> None:
        """Test saving a ticker and retrieving it by ID."""
        repo = PostgresTickerRepository(session)
        ticker = Ticker(symbol="7203.T", name="Toyota Motor Corporation")

        saved = repo.save(ticker)
        session.commit()

        result = repo.get_by_id(saved.ticker_id)

        assert result is not None
        assert result.symbol == "7203.T"
        assert result.name == "Toyota Motor Corporation"

    def test_get_by_id_not_found(self, session: Session) -> None:
        """Test get_by_id returns None for non-existent ID."""
        repo = PostgresTickerRepository(session)

        result = repo.get_by_id(9999)

        assert result is None

    def test_get_by_symbol(self, session: Session) -> None:
        """Test retrieving a ticker by symbol."""
        repo = PostgresTickerRepository(session)
        ticker = Ticker(symbol="9984.T", name="SoftBank Group Corp")
        repo.save(ticker)
        session.commit()

        result = repo.get_by_symbol("9984.T")

        assert result is not None
        assert result.symbol == "9984.T"
        assert result.name == "SoftBank Group Corp"

    def test_get_by_symbol_not_found(self, session: Session) -> None:
        """Test get_by_symbol returns None for non-existent symbol."""
        repo = PostgresTickerRepository(session)

        result = repo.get_by_symbol("NONEXISTENT")

        assert result is None

    def test_get_all(self, session: Session) -> None:
        """Test retrieving all tickers."""
        repo = PostgresTickerRepository(session)
        repo.save(Ticker(symbol="7203.T", name="Toyota"))
        repo.save(Ticker(symbol="9984.T", name="SoftBank"))
        repo.save(Ticker(symbol="6758.T", name="Sony"))
        session.commit()

        result = repo.get_all()

        assert len(result) == 3
        symbols = {t.symbol for t in result}
        assert symbols == {"7203.T", "9984.T", "6758.T"}

    def test_get_all_empty(self, session: Session) -> None:
        """Test get_all returns empty list when no tickers exist."""
        repo = PostgresTickerRepository(session)

        result = repo.get_all()

        assert result == []

    def test_delete(self, session: Session) -> None:
        """Test deleting a ticker."""
        repo = PostgresTickerRepository(session)
        ticker = Ticker(symbol="7203.T", name="Toyota")
        saved = repo.save(ticker)
        session.commit()
        ticker_id = saved.ticker_id

        result = repo.delete(ticker_id)
        session.commit()

        assert result is True
        assert repo.get_by_id(ticker_id) is None

    def test_delete_not_found(self, session: Session) -> None:
        """Test delete returns False for non-existent ID."""
        repo = PostgresTickerRepository(session)

        result = repo.delete(9999)

        assert result is False
