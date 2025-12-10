"""
NewsArticle ORM model for stock-related news headlines.

Stores recent news articles with publication metadata.
Maintains windowed retention (50 most recent articles per ticker).
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class NewsArticle(Base):
    """
    Recent news headlines and article metadata.

    Stores news articles with INSERT-only pattern and retention limit.
    Cleanup job maintains 50 most recent articles per ticker.
    """

    __tablename__ = "news_articles"

    # Primary Key
    article_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    ticker_id = Column(
        Integer, ForeignKey("tickers.ticker_id", ondelete="CASCADE"), nullable=False
    )

    # Article Content
    title = Column(Text, nullable=False)  # Article headline
    url = Column(Text, nullable=False)  # Article URL
    publisher = Column(String(100))  # Publisher name (nullable)

    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    ticker = relationship("Ticker", back_populates="news_articles")

    # Indexes
    __table_args__ = (
        # Composite index for efficient time-based queries
        Index(
            "idx_news_ticker_published",
            "ticker_id",
            "published_at",
            postgresql_using="btree",
            postgresql_ops={"published_at": "DESC"},
        ),
        # Unique constraint on ticker + URL to prevent duplicates
        Index("uq_news_ticker_url", "ticker_id", "url", unique=True),
    )

    def __repr__(self):
        return (
            f"<NewsArticle(ticker_id={self.ticker_id}, "
            f"published_at={self.published_at}, title={self.title[:50]})>"
        )
