"""
Custom exception classes for Binance trading bot.

This module defines custom exceptions for better error handling
and cleaner error reporting throughout the trading bot.
"""


class TradingBotException(Exception):
    """Base exception class for all trading bot related errors."""
    pass


class InvalidInputException(TradingBotException):
    """Raised when invalid input parameters are provided."""
    pass


class APIConnectionException(TradingBotException):
    """Raised when API connection fails."""
    pass


class OrderPlacementException(TradingBotException):
    """Raised when order placement fails."""
    pass


class ConfigurationException(TradingBotException):
    """Raised when configuration is missing or invalid."""
    pass


class ValidationException(TradingBotException):
    """Raised when input validation fails."""
    pass


class StopLimitOrderException(TradingBotException):
    """Raised when stop-limit order operations fail."""
    pass


class OCOOrderException(TradingBotException):
    """Raised when OCO order operations fail."""
    pass


class TWAPOrderException(TradingBotException):
    """Raised when TWAP order operations fail."""
    pass


class GridOrderException(TradingBotException):
    """Raised when grid order operations fail."""
    pass


class OrderCancellationException(TradingBotException):
    """Raised when order cancellation fails."""
    pass


class InsufficientBalanceException(TradingBotException):
    """Raised when account has insufficient balance."""
    pass
