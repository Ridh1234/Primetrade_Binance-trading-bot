"""
Binance Futures Testnet Trading Bot

A complete trading bot for Binance Futures Testnet with CLI interface,
comprehensive logging, and modular architecture.
"""

__version__ = "1.0.0"
__author__ = "GitHub Copilot"

from .binance_client import BinanceClient
from .orders import OrderManager, place_market_order, place_limit_order
from .exceptions import (
    TradingBotException,
    InvalidInputException,
    APIConnectionException,
    OrderPlacementException,
    ConfigurationException,
    ValidationException
)

__all__ = [
    'BinanceClient',
    'OrderManager',
    'place_market_order',
    'place_limit_order',
    'TradingBotException',
    'InvalidInputException',
    'APIConnectionException',
    'OrderPlacementException',
    'ConfigurationException',
    'ValidationException'
]
