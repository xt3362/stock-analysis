"""
FundamentalData ORM model for fundamental financial metrics.

Stores daily snapshots of fundamental data including EPS, P/E ratios,
market cap, dividend yield, and other key financial metrics.
"""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class FundamentalData(Base):
    """
    Daily snapshots of fundamental financial metrics.

    Stores key financial metrics retrieved from yfinance ticker.info.
    Supports historical tracking via append-only pattern with daily UPSERT.
    """

    __tablename__ = "fundamental_data"

    # Primary Key
    fundamental_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    ticker_id = Column(
        Integer, ForeignKey("tickers.ticker_id", ondelete="CASCADE"), nullable=False
    )

    # Timestamp
    retrieved_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Earnings Per Share
    eps_trailing = Column(Numeric(20, 4))  # Trailing 12-month EPS (can be negative)
    eps_forward = Column(Numeric(20, 4))  # Forward EPS estimate

    # Price-to-Earnings Ratios
    per_trailing = Column(Numeric(10, 2))  # Trailing P/E ratio
    per_forward = Column(Numeric(10, 2))  # Forward P/E ratio

    # Other Valuation Metrics
    peg_ratio = Column(Numeric(10, 2))  # Price/Earnings-to-Growth ratio
    market_cap = Column(BigInteger)  # Market capitalization

    # Income and Growth Metrics
    dividend_yield = Column(
        Numeric(5, 4)
    )  # Dividend yield as decimal (e.g., 0.0215 for 2.15%)
    profit_margin = Column(Numeric(5, 4))  # Profit margin as decimal
    earnings_growth = Column(Numeric(6, 4))  # YoY earnings growth as decimal

    # Relationship
    ticker = relationship("Ticker", back_populates="fundamental_data")

    # Indexes
    __table_args__ = (
        # Composite index for efficient time-series queries
        Index(
            "idx_fundamental_ticker_date",
            "ticker_id",
            "retrieved_at",
            postgresql_using="btree",
            postgresql_ops={"retrieved_at": "DESC"},
        ),
        # Unique constraint to prevent duplicate snapshots
        Index("uq_fundamental_ticker_date", "ticker_id", "retrieved_at", unique=True),
    )

    def __repr__(self):
        return (
            f"<FundamentalData(ticker_id={self.ticker_id}, "
            f"retrieved_at={self.retrieved_at}, "
            f"eps_trailing={self.eps_trailing}, per_trailing={self.per_trailing})>"
        )
