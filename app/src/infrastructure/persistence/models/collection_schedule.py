"""
CollectionSchedule ORM model for scheduled automatic data collection.
"""

# pyright: reportUnnecessaryComparison=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class CollectionSchedule(Base):
    """
    Configuration for scheduled automatic data collection (P3).

    Attributes:
        schedule_id: Unique schedule ID
        watchlist_id: Watchlist to update
        frequency: "daily", "weekly"
        execution_time: Time to run (e.g., "21:00")
        is_enabled: Whether schedule is active
        data_types: JSON list of data types to collect
        last_run_at: Last successful execution
        next_run_at: Next scheduled execution
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "collection_schedules"

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(
        Integer,
        ForeignKey("watchlists.watchlist_id", ondelete="CASCADE"),
        nullable=False,
    )
    frequency = Column(String(20), nullable=False)
    execution_time = Column(Time, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    data_types = Column(JSON, nullable=False, server_default='["price"]')
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "frequency IN ('daily', 'weekly')",
            name="chk_frequency_valid",
        ),
        Index(
            "idx_collection_schedules_next_run",
            "next_run_at",
            postgresql_where=is_enabled,
        ),
    )

    # Relationships
    watchlist = relationship("Watchlist", back_populates="collection_schedules")

    def __repr__(self):
        return (
            f"<CollectionSchedule(id={self.schedule_id}, "
            f"frequency='{self.frequency}', enabled={self.is_enabled})>"
        )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "schedule_id": self.schedule_id,
            "watchlist_id": self.watchlist_id,
            "frequency": self.frequency,
            "execution_time": (
                self.execution_time.isoformat()
                if self.execution_time is not None
                else None
            ),
            "is_enabled": self.is_enabled,
            "data_types": self.data_types if self.data_types is not None else ["price"],
            "last_run_at": self.last_run_at.isoformat()
            if self.last_run_at is not None
            else None,
            "next_run_at": self.next_run_at.isoformat()
            if self.next_run_at is not None
            else None,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at is not None
            else None,
        }
