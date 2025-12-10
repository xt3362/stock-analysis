"""
EarningsData ORM model for quarterly earnings results.

Stores quarterly earnings data including reported EPS, estimates,
surprises, and revenue information.
"""

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class EarningsData(Base):
    """
    Quarterly earnings results and calendar data.

    Stores both historical earnings results and upcoming earnings dates.
    Supports UPSERT pattern for updating estimates to actuals.
    """

    __tablename__ = "earnings_data"

    # Primary Key
    earnings_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    ticker_id = Column(
        Integer, ForeignKey("tickers.ticker_id", ondelete="CASCADE"), nullable=False
    )

    # Fiscal Period Identification
    fiscal_quarter = Column(String(10), nullable=False)  # Format: "Q1 2024"
    fiscal_year = Column(Integer, nullable=False)  # Fiscal year

    # Earnings Data
    earnings_date = Column(Date)  # Actual or estimated earnings date
    reported_eps = Column(Numeric(20, 4))  # Reported EPS (actual)
    estimated_eps = Column(Numeric(20, 4))  # Analyst estimate
    surprise_pct = Column(Numeric(6, 2))  # Surprise percentage
    revenue = Column(BigInteger)  # Quarterly revenue

    # Metadata
    retrieved_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    ticker = relationship("Ticker", back_populates="earnings_data")

    # Indexes
    __table_args__ = (
        # Composite index for efficient quarter-based queries
        Index(
            "idx_earnings_ticker_quarter",
            "ticker_id",
            "fiscal_year",
            "fiscal_quarter",
            postgresql_using="btree",
            postgresql_ops={"fiscal_year": "DESC"},
        ),
        # Unique constraint on ticker + fiscal period
        Index(
            "uq_earnings_ticker_period",
            "ticker_id",
            "fiscal_quarter",
            "fiscal_year",
            unique=True,
        ),
    )

    def __repr__(self):
        return (
            f"<EarningsData(ticker_id={self.ticker_id}, "
            f"fiscal_quarter={self.fiscal_quarter}, fiscal_year={self.fiscal_year}, "
            f"reported_eps={self.reported_eps})>"
        )
