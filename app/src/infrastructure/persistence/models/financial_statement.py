"""
FinancialStatement ORM model for quarterly financial statement line items.

Stores income statement, balance sheet, and cash flow statement data
in a normalized line-item format.
"""

import enum

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class StatementType(enum.Enum):
    """Financial statement types."""

    income_statement = "income_statement"
    balance_sheet = "balance_sheet"
    cash_flow = "cash_flow"


class FinancialStatement(Base):
    """
    Quarterly financial statement line items.

    Stores individual line items from financial statements in a normalized format.
    Supports windowed retention (most recent 8 quarters per ticker/statement type).
    """

    __tablename__ = "financial_statements"

    # Primary Key
    statement_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    ticker_id = Column(
        Integer, ForeignKey("tickers.ticker_id", ondelete="CASCADE"), nullable=False
    )

    # Statement Classification
    statement_type = Column(
        Enum(StatementType, name="statement_type_enum", create_type=True),
        nullable=False,
    )

    # Fiscal Period Identification
    fiscal_quarter = Column(String(10), nullable=False)  # Format: "Q1 2024"
    fiscal_year = Column(Integer, nullable=False)  # Fiscal year

    # Line Item Data
    line_item = Column(
        String(100), nullable=False
    )  # Normalized item name (lowercase with underscores)
    value = Column(BigInteger)  # Line item value
    currency = Column(String(10), nullable=False)  # Currency code (e.g., "USD", "JPY")

    # Metadata
    retrieved_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    ticker = relationship("Ticker", back_populates="financial_statements")

    # Indexes
    __table_args__ = (
        # Composite index for efficient statement queries
        Index(
            "idx_statement_ticker_type_quarter",
            "ticker_id",
            "statement_type",
            "fiscal_year",
            "fiscal_quarter",
            postgresql_using="btree",
            postgresql_ops={"fiscal_year": "DESC"},
        ),
        # Unique constraint on ticker + statement type + period + line item
        Index(
            "uq_statement_ticker_line_item",
            "ticker_id",
            "statement_type",
            "fiscal_quarter",
            "fiscal_year",
            "line_item",
            unique=True,
        ),
        # Index on line_item for cross-stock queries
        Index("idx_statement_line_item", "line_item"),
    )

    def __repr__(self):
        return (
            f"<FinancialStatement(ticker_id={self.ticker_id}, "
            f"statement_type={self.statement_type.value}, "
            f"fiscal_quarter={self.fiscal_quarter}, line_item={self.line_item})>"
        )
