"""Pytest fixtures for testing."""

from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.persistence.database import Base


@pytest.fixture
def engine() -> Engine:
    """Create an in-memory SQLite engine for testing."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    """
    Create a test session with auto-rollback.

    This fixture:
    1. Creates all tables in the in-memory database
    2. Provides a session for the test
    3. Closes the session after the test
    """
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    test_session = session_factory()
    yield test_session
    test_session.close()
