"""
UniverseSymbol ORM model for universe-ticker relationships.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class UniverseSymbol(Base):
    """
    Association table for Universe and Ticker many-to-many relationship.

    Attributes:
        universe_id: Foreign key to Universe
        ticker_id: Foreign key to Ticker
        added_at: Timestamp when ticker was added to universe
    """

    __tablename__ = "universe_symbols"

    universe_id = Column(
        Integer,
        ForeignKey("universes.universe_id", ondelete="CASCADE"),
        primary_key=True,
    )
    ticker_id = Column(
        Integer, ForeignKey("tickers.ticker_id", ondelete="CASCADE"), primary_key=True
    )
    added_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    universe = relationship("Universe", back_populates="symbol_associations")
    ticker = relationship("Ticker")

    def __repr__(self):
        return (
            f"<UniverseSymbol(universe_id={self.universe_id}, "
            f"ticker_id={self.ticker_id})>"
        )
