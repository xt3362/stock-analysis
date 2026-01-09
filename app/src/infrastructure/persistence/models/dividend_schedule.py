"""
DividendSchedule ORM model for dividend ex-dates.

Stores dividend ex-dividend dates for event calendar evaluation.
"""

# pyright: reportUnnecessaryComparison=false, reportGeneralTypeIssues=false
# pyright: reportArgumentType=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from typing import Any

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class DividendSchedule(Base):
    """
    配当権利確定日スケジュール.

    EventCalendarServiceで使用する配当落ち日を保存する。
    """

    __tablename__ = "dividend_schedule"

    # Primary Key
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    ticker_id = Column(
        Integer,
        ForeignKey("tickers.ticker_id", ondelete="CASCADE"),
        nullable=False,
    )

    # 配当情報
    ex_dividend_date = Column(Date, nullable=False)  # 配当落ち日

    # 追加情報
    dividend_rate = Column(Numeric(10, 4))  # 1株あたり配当額
    dividend_yield = Column(Numeric(6, 4))  # 配当利回り（小数）

    # メタデータ
    retrieved_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    ticker = relationship("Ticker", back_populates="dividend_schedule")

    # Indexes
    __table_args__ = (
        # Composite index for efficient date-based queries
        Index(
            "idx_dividend_schedule_ticker_date",
            "ticker_id",
            "ex_dividend_date",
            postgresql_using="btree",
        ),
        # Unique constraint on ticker + ex_dividend_date
        Index(
            "uq_dividend_schedule",
            "ticker_id",
            "ex_dividend_date",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DividendSchedule(ticker_id={self.ticker_id}, "
            f"ex_dividend_date={self.ex_dividend_date}, "
            f"dividend_rate={self.dividend_rate})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "schedule_id": self.schedule_id,
            "ticker_id": self.ticker_id,
            "ex_dividend_date": self.ex_dividend_date.isoformat()
            if self.ex_dividend_date
            else None,
            "dividend_rate": float(self.dividend_rate)
            if self.dividend_rate is not None
            else None,
            "dividend_yield": float(self.dividend_yield)
            if self.dividend_yield is not None
            else None,
            "retrieved_at": self.retrieved_at.isoformat()
            if self.retrieved_at
            else None,
        }
