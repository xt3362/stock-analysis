"""
Domain models for swing trading system.

This module exports:
- Data Classes (domain layer): Position, Trade, BacktestResult, etc.
- ORM Models (backward compatibility): Ticker, DailyPrice, etc.
  NOTE: ORM models are now located in src.infrastructure.persistence.models
"""

# Data Classes (domain layer)
from src.domain.models.backtest_result import BacktestResult, PerformanceMetrics, Trade
from src.domain.models.market_regime import (
    ADRDivergence,
    AdvancingDecliningRatio,
    EnvironmentCode,
    MarketBreadth,
    MarketRegime,
    MarketRegimeConfig,
    RiskAssessment,
    RiskLevel,
    Sentiment,
    SentimentAnalysis,
    TrendAnalysis,
    TrendDirection,
    TrendType,
    VolatilityAnalysis,
    VolatilityLevel,
)
from src.domain.models.portfolio_backtest_result import (
    DailyMarketEnvironment,
    DailyPortfolioState,
    PortfolioBacktestResult,
    PortfolioPerformanceMetrics,
)
from src.domain.models.position import Position
from src.domain.models.strategy_backtest_result import StrategyBacktestResult
from src.domain.models.strategy_statistics import (
    MarketEnvironmentBreakdown,
    StrategyStatistics,
)
from src.domain.models.swing_analysis import (
    AdvancedIndicatorsScore,
    AnalysisResult,
    DetailedAnalysisResult,
    DetailedScoresSummary,
    EarningsScore,
    EntryPlan,
    MomentumScore,
    ScoresSummary,
    SignalIndicator,
    StrategyAnalysisResult,
    StrategyScore,
    TrendScore,
    ValueScore,
    VolumeScore,
)

# ORM Models (backward compatibility - prefer src.infrastructure.persistence.models)
from src.infrastructure.persistence.models import (
    AnalystRating,
    CollectionJob,
    CollectionSchedule,
    DailyPrice,
    EarningsData,
    FinancialStatement,
    FundamentalData,
    NewsArticle,
    Rating,
    RatingAction,
    StatementType,
    Ticker,
    Universe,
    UniverseMode,
    UniverseSymbol,
    Watchlist,
    WatchlistTicker,
)

__all__ = [
    "ADRDivergence",
    "AdvancedIndicatorsScore",
    "AdvancingDecliningRatio",
    "AnalysisResult",
    "AnalystRating",
    "BacktestResult",
    "CollectionJob",
    "CollectionSchedule",
    "DailyMarketEnvironment",
    "DailyPortfolioState",
    "DailyPrice",
    "DetailedAnalysisResult",
    "DetailedScoresSummary",
    "EarningsData",
    "EarningsScore",
    "EntryPlan",
    "EnvironmentCode",
    "FinancialStatement",
    "FundamentalData",
    "MarketBreadth",
    "MarketEnvironmentBreakdown",
    "MarketRegime",
    "MarketRegimeConfig",
    "MomentumScore",
    "NewsArticle",
    "PerformanceMetrics",
    "PortfolioBacktestResult",
    "PortfolioPerformanceMetrics",
    "Position",
    "Rating",
    "RatingAction",
    "RiskAssessment",
    "RiskLevel",
    "ScoresSummary",
    "Sentiment",
    "SentimentAnalysis",
    "SignalIndicator",
    "StatementType",
    "StrategyAnalysisResult",
    "StrategyBacktestResult",
    "StrategyScore",
    "StrategyStatistics",
    "Ticker",
    "Trade",
    "TrendAnalysis",
    "TrendDirection",
    "TrendScore",
    "TrendType",
    "Universe",
    "UniverseMode",
    "UniverseSymbol",
    "ValueScore",
    "VolatilityAnalysis",
    "VolatilityLevel",
    "VolumeScore",
    "Watchlist",
    "WatchlistTicker",
]
