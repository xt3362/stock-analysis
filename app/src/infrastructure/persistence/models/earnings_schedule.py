"""
EarningsSchedule ORM model for earnings announcement dates.

Stores earnings announcement dates for event calendar evaluation.
Separate from EarningsData which stores quarterly results (EPS, revenue, etc.).
"""

# pyright: reportUnnecessaryComparison=false, reportGeneralTypeIssues=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class EarningsSchedule(Base):
    """
    決算発表日スケジュール.

    EventCalendarServiceで使用する決算発表日を保存する。
    EarningsData（四半期決算結果）とは別のテーブル。
    """

    __tablename__ = "earnings_schedule"

    # Primary Key
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    ticker_id = Column(
        Integer,
        ForeignKey("tickers.ticker_id", ondelete="CASCADE"),
        nullable=False,
    )

    # 決算発表日
    earnings_date = Column(Date, nullable=False)

    # 財務期間（オプション）
    fiscal_quarter = Column(String(10))  # "Q1", "Q2", "Q3", "Q4"
    fiscal_year = Column(Integer)  # 決算年度

    # メタデータ
    is_confirmed = Column(Boolean, default=False, nullable=False)  # 確定日かどうか
    retrieved_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    ticker = relationship("Ticker", back_populates="earnings_schedule")

    # Indexes
    __table_args__ = (
        # Composite index for efficient date-based queries
        Index(
            "idx_earnings_schedule_ticker_date",
            "ticker_id",
            "earnings_date",
            postgresql_using="btree",
        ),
        # Unique constraint on ticker + earnings_date
        Index(
            "uq_earnings_schedule",
            "ticker_id",
            "earnings_date",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EarningsSchedule(ticker_id={self.ticker_id}, "
            f"earnings_date={self.earnings_date}, "
            f"fiscal_quarter={self.fiscal_quarter})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "schedule_id": self.schedule_id,
            "ticker_id": self.ticker_id,
            "earnings_date": self.earnings_date.isoformat()
            if self.earnings_date
            else None,
            "fiscal_quarter": self.fiscal_quarter,
            "fiscal_year": self.fiscal_year,
            "is_confirmed": self.is_confirmed,
            "retrieved_at": self.retrieved_at.isoformat()
            if self.retrieved_at
            else None,
        }
