"""add_event_schedule_tables

Revision ID: a8c3d2e1f4b5
Revises: 7237d5cf30fe
Create Date: 2025-01-09 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8c3d2e1f4b5"
down_revision: Union[str, None] = "7237d5cf30fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create earnings_schedule table
    op.create_table(
        "earnings_schedule",
        sa.Column("schedule_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("earnings_date", sa.Date(), nullable=False),
        sa.Column("fiscal_quarter", sa.String(length=10), nullable=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ticker_id"], ["tickers.ticker_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("schedule_id"),
    )

    # Create indexes for earnings_schedule
    op.create_index(
        "idx_earnings_schedule_ticker_date",
        "earnings_schedule",
        ["ticker_id", "earnings_date"],
        unique=False,
    )
    op.create_index(
        "uq_earnings_schedule",
        "earnings_schedule",
        ["ticker_id", "earnings_date"],
        unique=True,
    )

    # Create dividend_schedule table
    op.create_table(
        "dividend_schedule",
        sa.Column("schedule_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("ex_dividend_date", sa.Date(), nullable=False),
        sa.Column("dividend_rate", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("dividend_yield", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ticker_id"], ["tickers.ticker_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("schedule_id"),
    )

    # Create indexes for dividend_schedule
    op.create_index(
        "idx_dividend_schedule_ticker_date",
        "dividend_schedule",
        ["ticker_id", "ex_dividend_date"],
        unique=False,
    )
    op.create_index(
        "uq_dividend_schedule",
        "dividend_schedule",
        ["ticker_id", "ex_dividend_date"],
        unique=True,
    )


def downgrade() -> None:
    # Drop indexes for dividend_schedule
    op.drop_index("uq_dividend_schedule", table_name="dividend_schedule")
    op.drop_index("idx_dividend_schedule_ticker_date", table_name="dividend_schedule")

    # Drop dividend_schedule table
    op.drop_table("dividend_schedule")

    # Drop indexes for earnings_schedule
    op.drop_index("uq_earnings_schedule", table_name="earnings_schedule")
    op.drop_index("idx_earnings_schedule_ticker_date", table_name="earnings_schedule")

    # Drop earnings_schedule table
    op.drop_table("earnings_schedule")
