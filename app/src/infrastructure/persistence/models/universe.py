"""
Universe ORM model for stock universe management.
"""

# pyright: reportUnnecessaryComparison=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

import enum

from sqlalchemy import Column, Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class UniverseMode(enum.Enum):
    """Universe mode enum."""

    BACKTEST = "backtest"
    PRODUCTION = "production"


class Universe(Base):
    """
    Stock universe for backtesting or production trading.

    Attributes:
        universe_id: Unique universe ID
        name: Universe name
        mode: Universe mode (backtest/production)
        as_of_date: As-of date for universe selection
        config_name: Config file name used
        description: Optional description
        total_symbols: Number of symbols in universe
        created_at: Creation timestamp
    """

    __tablename__ = "universes"

    universe_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    mode = Column(Enum(UniverseMode), nullable=False, default=UniverseMode.BACKTEST)
    as_of_date = Column(Date, nullable=False)
    config_name = Column(String(100), nullable=False)
    description = Column(Text)
    total_symbols = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    symbol_associations = relationship(
        "UniverseSymbol", back_populates="universe", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Universe(name='{self.name}', mode='{self.mode.value}', "
            f"as_of_date='{self.as_of_date}')>"
        )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "universe_id": self.universe_id,
            "name": self.name,
            "mode": self.mode.value,
            "as_of_date": self.as_of_date.isoformat()
            if self.as_of_date is not None
            else None,
            "config_name": self.config_name,
            "description": self.description,
            "total_symbols": self.total_symbols,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
        }
