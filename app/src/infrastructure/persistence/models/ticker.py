"""
Ticker ORM model representing publicly traded securities.
"""

# pyright: reportUnnecessaryComparison=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class Ticker(Base):
    """
    Represents a publicly traded security with unique symbol identifier.

    Attributes:
        ticker_id: Auto-increment unique ID
        symbol: Ticker symbol (e.g., "AAPL", "7203.T")
        name: Company name (e.g., "Apple Inc.")
        exchange: Exchange code (e.g., "NASDAQ", "TSE")
        currency: Trading currency (e.g., "USD", "JPY")
        sector: Business sector
        industry: Industry classification
        is_active: Whether ticker is actively tracked
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "tickers"

    ticker_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    exchange = Column(String(50))
    currency = Column(String(10))
    sector = Column(String(100), index=True)
    industry = Column(String(100), index=True)
    beta = Column(Numeric(6, 3))  # Market beta (volatility indicator)
    fifty_two_week_high = Column(Numeric(10, 2))  # 52-week high price
    fifty_two_week_low = Column(Numeric(10, 2))  # 52-week low price
    is_active = Column(Boolean, default=True, nullable=False)
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
    daily_prices = relationship(
        "DailyPrice", back_populates="ticker", cascade="all, delete-orphan"
    )
    collection_jobs = relationship(
        "CollectionJob", back_populates="ticker", cascade="all, delete-orphan"
    )
    watchlist_associations = relationship(
        "WatchlistTicker", back_populates="ticker", cascade="all, delete-orphan"
    )
    fundamental_data = relationship(
        "FundamentalData", back_populates="ticker", cascade="all, delete-orphan"
    )
    earnings_data = relationship(
        "EarningsData", back_populates="ticker", cascade="all, delete-orphan"
    )
    financial_statements = relationship(
        "FinancialStatement", back_populates="ticker", cascade="all, delete-orphan"
    )
    analyst_ratings = relationship(
        "AnalystRating", back_populates="ticker", cascade="all, delete-orphan"
    )
    news_articles = relationship(
        "NewsArticle", back_populates="ticker", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Ticker(symbol='{self.symbol}', name='{self.name}')>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "ticker_id": self.ticker_id,
            "symbol": self.symbol,
            "name": self.name,
            "exchange": self.exchange,
            "currency": self.currency,
            "sector": self.sector,
            "industry": self.industry,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at is not None
            else None,
        }
