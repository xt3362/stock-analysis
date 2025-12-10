"""
CollectionJob ORM model for tracking data collection operations.
"""

# pyright: reportUnnecessaryComparison=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class CollectionJob(Base):
    """
    Tracks data collection operations for auditing and debugging.

    Attributes:
        job_id: Unique job ID
        ticker_id: Ticker collected (NULL for batch jobs)
        job_type: "single", "batch", "scheduled"
        start_date: Requested start date
        end_date: Requested end date
        status: "pending", "running", "completed", "failed", "partial"
        started_at: Job start time
        completed_at: Job completion time
        records_fetched: Number of records from yfinance
        records_inserted: Number of new records inserted
        records_updated: Number of existing records updated
        error_message: Error details if failed
        created_at: Record creation timestamp
    """

    __tablename__ = "collection_jobs"

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(
        Integer,
        ForeignKey("tickers.ticker_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_type = Column(
        String(20),
        nullable=False,
        default="single",
    )
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "job_type IN ('single', 'batch', 'scheduled')",
            name="chk_job_type_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'partial')",
            name="chk_status_valid",
        ),
        Index("idx_collection_jobs_started", "started_at"),
    )

    # Relationships
    ticker = relationship("Ticker", back_populates="collection_jobs")

    def __repr__(self):
        return (
            f"<CollectionJob(job_id={self.job_id}, "
            f"type='{self.job_type}', status='{self.status}')>"
        )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "job_id": self.job_id,
            "ticker_id": self.ticker_id,
            "job_type": self.job_type,
            "start_date": self.start_date.isoformat()
            if self.start_date is not None
            else None,
            "end_date": self.end_date.isoformat()
            if self.end_date is not None
            else None,
            "status": self.status,
            "started_at": self.started_at.isoformat()
            if self.started_at is not None
            else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at is not None else None
            ),
            "records_fetched": self.records_fetched,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
        }
