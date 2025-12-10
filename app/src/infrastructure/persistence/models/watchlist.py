"""
Watchlist ORM model for user-defined ticker collections.
"""

# pyright: reportUnnecessaryComparison=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class Watchlist(Base):
    """
    User-defined collections of tickers for batch operations and monitoring.

    Attributes:
        watchlist_id: Unique watchlist ID
        name: Watchlist name (e.g., "Tech Stocks")
        description: Optional description
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "watchlists"

    watchlist_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    ticker_associations = relationship(
        "WatchlistTicker", back_populates="watchlist", cascade="all, delete-orphan"
    )
    collection_schedules = relationship(
        "CollectionSchedule", back_populates="watchlist", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Watchlist(name='{self.name}')>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "watchlist_id": self.watchlist_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at is not None
            else None,
        }
