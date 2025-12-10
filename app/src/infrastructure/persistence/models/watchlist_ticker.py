"""
WatchlistTicker ORM model for many-to-many association between watchlists and tickers.
"""

# pyright: reportUnnecessaryComparison=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    func,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class WatchlistTicker(Base):
    """
    Association between watchlists and tickers (many-to-many relationship).

    Attributes:
        watchlist_id: Watchlist reference
        ticker_id: Ticker reference
        added_at: When ticker was added to watchlist
    """

    __tablename__ = "watchlist_tickers"

    watchlist_id = Column(
        Integer,
        ForeignKey("watchlists.watchlist_id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker_id = Column(
        Integer,
        ForeignKey("tickers.ticker_id", ondelete="CASCADE"),
        nullable=False,
    )
    added_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Composite Primary Key
    __table_args__ = (
        PrimaryKeyConstraint("watchlist_id", "ticker_id"),
        Index("idx_watchlist_tickers_ticker", "ticker_id"),
    )

    # Relationships
    watchlist = relationship("Watchlist", back_populates="ticker_associations")
    ticker = relationship("Ticker", back_populates="watchlist_associations")

    def __repr__(self):
        return (
            f"<WatchlistTicker(watchlist_id={self.watchlist_id}, "
            f"ticker_id={self.ticker_id})>"
        )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "watchlist_id": self.watchlist_id,
            "ticker_id": self.ticker_id,
            "added_at": self.added_at.isoformat()
            if self.added_at is not None
            else None,
        }
