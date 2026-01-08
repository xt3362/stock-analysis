"""Custom exceptions for the stock analysis application."""


class StockAnalysisError(Exception):
    """Base exception for stock analysis application."""

    pass


class StockDataFetchError(StockAnalysisError):
    """
    Exception raised when stock data fetching fails.

    Attributes:
        symbol: The ticker symbol that failed to fetch (optional).
    """

    def __init__(self, message: str, symbol: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message describing the failure.
            symbol: The ticker symbol that failed to fetch.
        """
        self.symbol = symbol
        super().__init__(message)


class ValidationError(StockAnalysisError):
    """Exception raised for validation errors."""

    pass


class DatabaseError(StockAnalysisError):
    """Exception raised for database operation errors."""

    pass


class IndicatorCalculationError(StockAnalysisError):
    """
    Exception raised when indicator calculation fails.

    Attributes:
        indicator: The indicator name that failed to calculate (optional).
        symbol: The ticker symbol that failed (optional).
    """

    def __init__(
        self,
        message: str,
        indicator: str | None = None,
        symbol: str | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message describing the failure.
            indicator: The indicator name that failed.
            symbol: The ticker symbol that failed.
        """
        self.indicator = indicator
        self.symbol = symbol
        super().__init__(message)


class MarketRegimeAnalysisError(StockAnalysisError):
    """
    Exception raised when market regime analysis fails.

    Attributes:
        reason: The reason for the analysis failure (optional).
    """

    def __init__(
        self,
        message: str,
        reason: str | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message describing the failure.
            reason: The reason for the analysis failure.
        """
        self.reason = reason
        super().__init__(message)
