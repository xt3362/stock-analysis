"""
DailyPrice ORM model for OHLCV data with technical indicators.
"""

# pyright: reportArgumentType=false, reportUnnecessaryComparison=false
# NOTE: Above suppresses false positives for SQLAlchemy Column types in to_dict()

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class DailyPrice(Base):
    """
    Daily price data with pre-calculated technical indicators.

    Stores OHLCV (Open, High, Low, Close, Volume) data and technical indicators
    for performance optimization.
    """

    __tablename__ = "daily_prices"

    # Primary Key
    price_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign Keys
    ticker_id = Column(
        Integer, ForeignKey("tickers.ticker_id", ondelete="CASCADE"), nullable=False
    )
    date = Column(Date, nullable=False)

    # OHLCV Data
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    adj_close = Column(Numeric(12, 4))
    volume = Column(BigInteger)

    # Moving Averages
    sma_5 = Column(Numeric(12, 4))
    sma_25 = Column(Numeric(12, 4))
    sma_75 = Column(Numeric(12, 4))
    ema_12 = Column(Numeric(12, 4))
    ema_26 = Column(Numeric(12, 4))

    # Momentum Indicators
    rsi_14 = Column(Numeric(6, 2))
    stoch_k = Column(Numeric(6, 2))
    stoch_d = Column(Numeric(6, 2))

    # MACD
    macd = Column(Numeric(12, 4))
    macd_signal = Column(Numeric(12, 4))
    macd_histogram = Column(Numeric(12, 4))

    # Bollinger Bands
    bb_upper = Column(Numeric(12, 4))
    bb_middle = Column(Numeric(12, 4))
    bb_lower = Column(Numeric(12, 4))
    bb_width = Column(Numeric(12, 4))

    # Volatility
    atr_14 = Column(Numeric(12, 4))
    realized_volatility = Column(Numeric(8, 4))

    # Trend
    adx_14 = Column(Numeric(6, 2))
    sar = Column(Numeric(12, 4))

    # Volume Indicators
    obv = Column(BigInteger)
    volume_ma_20 = Column(BigInteger)
    volume_ratio = Column(Numeric(8, 4))

    # Metadata
    data_quality_score = Column(Numeric(3, 2), default=1.0)
    is_repaired = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("ticker_id", "date", name="uq_ticker_date"),
        CheckConstraint(
            "open > 0 AND high >= low AND high >= open "
            "AND high >= close AND low <= open AND low <= close",
            name="chk_ohlc_valid",
        ),
        Index(
            "idx_daily_prices_ticker_date",
            "ticker_id",
            "date",
            postgresql_using="btree",
        ),
        Index("idx_daily_prices_date", "date"),
    )

    # Relationships
    ticker = relationship("Ticker", back_populates="daily_prices")

    def __repr__(self):
        return (
            f"<DailyPrice(ticker_id={self.ticker_id}, "
            f"date={self.date}, close={self.close})>"
        )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "price_id": self.price_id,
            "ticker_id": self.ticker_id,
            "date": self.date.isoformat() if self.date is not None else None,
            "open": float(self.open) if self.open is not None else None,
            "high": float(self.high) if self.high is not None else None,
            "low": float(self.low) if self.low is not None else None,
            "close": float(self.close) if self.close is not None else None,
            "adj_close": float(self.adj_close) if self.adj_close is not None else None,
            "volume": self.volume,
            "sma_5": float(self.sma_5) if self.sma_5 is not None else None,
            "sma_25": float(self.sma_25) if self.sma_25 is not None else None,
            "sma_75": float(self.sma_75) if self.sma_75 is not None else None,
            "ema_12": float(self.ema_12) if self.ema_12 is not None else None,
            "ema_26": float(self.ema_26) if self.ema_26 is not None else None,
            "rsi_14": float(self.rsi_14) if self.rsi_14 is not None else None,
            "stoch_k": float(self.stoch_k) if self.stoch_k is not None else None,
            "stoch_d": float(self.stoch_d) if self.stoch_d is not None else None,
            "macd": float(self.macd) if self.macd is not None else None,
            "macd_signal": float(self.macd_signal)
            if self.macd_signal is not None
            else None,
            "macd_histogram": (
                float(self.macd_histogram) if self.macd_histogram is not None else None
            ),
            "bb_upper": float(self.bb_upper) if self.bb_upper is not None else None,
            "bb_middle": float(self.bb_middle) if self.bb_middle is not None else None,
            "bb_lower": float(self.bb_lower) if self.bb_lower is not None else None,
            "bb_width": float(self.bb_width) if self.bb_width is not None else None,
            "atr_14": float(self.atr_14) if self.atr_14 is not None else None,
            "realized_volatility": (
                float(self.realized_volatility)
                if self.realized_volatility is not None
                else None
            ),
            "adx_14": float(self.adx_14) if self.adx_14 is not None else None,
            "sar": float(self.sar) if self.sar is not None else None,
            "obv": self.obv,
            "volume_ma_20": self.volume_ma_20,
            "volume_ratio": float(self.volume_ratio)
            if self.volume_ratio is not None
            else None,
            "data_quality_score": (
                float(self.data_quality_score)
                if self.data_quality_score is not None
                else None
            ),
            "is_repaired": self.is_repaired,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
        }
