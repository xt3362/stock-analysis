"""
AnalystRating ORM model for analyst recommendations and price targets.

Stores historical analyst ratings, rating changes, and price targets
from various analyst firms.
"""

import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class Rating(enum.Enum):
    """Analyst rating categories."""

    strong_buy = "strong_buy"
    buy = "buy"
    hold = "hold"
    sell = "sell"
    strong_sell = "strong_sell"


class RatingAction(enum.Enum):
    """Rating action types."""

    upgrade = "upgrade"
    downgrade = "downgrade"
    maintain = "maintain"
    initiate = "initiate"


class AnalystRating(Base):
    """
    Analyst recommendation history and rating changes.

    Stores historical analyst ratings as immutable events.
    INSERT-only pattern (no updates or deletes).
    """

    __tablename__ = "analyst_ratings"

    # Primary Key
    rating_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    ticker_id = Column(
        Integer, ForeignKey("tickers.ticker_id", ondelete="CASCADE"), nullable=False
    )

    # Rating Information
    rating_date = Column(Date, nullable=False, index=True)
    rating = Column(
        Enum(Rating, name="rating_enum", create_type=True),
        nullable=False,
    )
    firm = Column(String(100))  # Analyst firm name (nullable - not always provided)
    action = Column(
        Enum(RatingAction, name="rating_action_enum", create_type=True)
    )  # Rating action (nullable)
    target_price = Column(Numeric(10, 2))  # Price target

    # Metadata
    retrieved_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    ticker = relationship("Ticker", back_populates="analyst_ratings")

    # Indexes
    __table_args__ = (
        # Composite index for efficient time-based queries
        Index(
            "idx_rating_ticker_date",
            "ticker_id",
            "rating_date",
            postgresql_using="btree",
            postgresql_ops={"rating_date": "DESC"},
        ),
        # Unique constraint on ticker + date + firm (if firm provided)
        # Note: This allows multiple ratings on same date if firm is null
        Index(
            "uq_rating_ticker_date_firm",
            "ticker_id",
            "rating_date",
            "firm",
            unique=True,
            postgresql_where="firm IS NOT NULL",
        ),
    )

    def __repr__(self):
        return (
            f"<AnalystRating(ticker_id={self.ticker_id}, "
            f"rating_date={self.rating_date}, rating={self.rating.value}, "
            f"firm={self.firm})>"
        )
