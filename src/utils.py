"""
Utility functions for the Binance trading bot.

This module provides helper functions for validation, logging configuration,
error handling, and other reusable utilities.
"""

import logging
import os
import sys
import re
from decimal import Decimal, InvalidOperation
from logging.handlers import RotatingFileHandler
from typing import Optional

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .exceptions import ValidationException
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add src directory to path if needed
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from exceptions import ValidationException


def setup_logging(log_file: str = "bot.log", max_bytes: int = 10485760, backup_count: int = 5) -> logging.Logger:
    """
    Set up logging configuration with both file and console handlers.
    
    Args:
        log_file: Name of the log file
        max_bytes: Maximum file size before rotation (default 10MB)
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("binance_trading_bot")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes, 
        backupCount=backup_count
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        
    Returns:
        Validated symbol in uppercase
        
    Raises:
        ValidationException: If symbol format is invalid
    """
    if not symbol:
        raise ValidationException("Symbol cannot be empty")
    
    symbol = symbol.upper().strip()
    
    # Basic validation for crypto pairs (must contain letters and end with USDT)
    if not re.match(r'^[A-Z]+USDT$', symbol):
        raise ValidationException(f"Invalid symbol format: {symbol}. Must be a valid USDT pair (e.g., BTCUSDT)")
    
    if len(symbol) < 6 or len(symbol) > 12:
        raise ValidationException(f"Invalid symbol length: {symbol}")
    
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.
    
    Args:
        side: Order side (BUY or SELL)
        
    Returns:
        Validated side in uppercase
        
    Raises:
        ValidationException: If side is invalid
    """
    if not side:
        raise ValidationException("Side cannot be empty")
    
    side = side.upper().strip()
    
    if side not in ['BUY', 'SELL']:
        raise ValidationException(f"Invalid side: {side}. Must be BUY or SELL")
    
    return side


def validate_quantity(quantity: str) -> float:
    """
    Validate order quantity.
    
    Args:
        quantity: Order quantity as string
        
    Returns:
        Validated quantity as float
        
    Raises:
        ValidationException: If quantity is invalid
    """
    if not quantity:
        raise ValidationException("Quantity cannot be empty")
    
    try:
        qty = float(quantity)
    except ValueError:
        raise ValidationException(f"Invalid quantity format: {quantity}. Must be a valid number")
    
    if qty <= 0:
        raise ValidationException(f"Quantity must be positive: {qty}")
    
    if qty > 1000:  # Reasonable upper limit for testnet
        raise ValidationException(f"Quantity too large: {qty}. Maximum allowed is 1000")
    
    # Check for reasonable precision (max 8 decimal places)
    try:
        decimal_qty = Decimal(str(qty))
        if decimal_qty.as_tuple().exponent < -8:
            raise ValidationException(f"Quantity precision too high: {qty}. Maximum 8 decimal places")
    except InvalidOperation:
        raise ValidationException(f"Invalid quantity precision: {qty}")
    
    return qty


def validate_price(price: str) -> float:
    """
    Validate order price.
    
    Args:
        price: Order price as string
        
    Returns:
        Validated price as float
        
    Raises:
        ValidationException: If price is invalid
    """
    if not price:
        raise ValidationException("Price cannot be empty")
    
    try:
        price_val = float(price)
    except ValueError:
        raise ValidationException(f"Invalid price format: {price}. Must be a valid number")
    
    if price_val <= 0:
        raise ValidationException(f"Price must be positive: {price_val}")
    
    if price_val > 1000000:  # Reasonable upper limit
        raise ValidationException(f"Price too high: {price_val}")
    
    # Check for reasonable precision (max 8 decimal places)
    try:
        decimal_price = Decimal(str(price_val))
        if decimal_price.as_tuple().exponent < -8:
            raise ValidationException(f"Price precision too high: {price_val}. Maximum 8 decimal places")
    except InvalidOperation:
        raise ValidationException(f"Invalid price precision: {price_val}")
    
    return price_val


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.
    
    Args:
        order_type: Order type (market or limit)
        
    Returns:
        Validated order type in lowercase
        
    Raises:
        ValidationException: If order type is invalid
    """
    if not order_type:
        raise ValidationException("Order type cannot be empty")
    
    order_type = order_type.lower().strip()
    
    if order_type not in ['market', 'limit']:
        raise ValidationException(f"Invalid order type: {order_type}. Must be 'market' or 'limit'")
    
    return order_type


def validate_env_variables() -> tuple[str, str]:
    """
    Validate that required environment variables are set.
    
    Returns:
        Tuple of (api_key, api_secret)
        
    Raises:
        ValidationException: If required environment variables are missing
    """
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key:
        raise ValidationException("BINANCE_API_KEY environment variable is required")
    
    if not api_secret:
        raise ValidationException("BINANCE_API_SECRET environment variable is required")
    
    if len(api_key.strip()) < 10:
        raise ValidationException("BINANCE_API_KEY appears to be invalid (too short)")
    
    if len(api_secret.strip()) < 10:
        raise ValidationException("BINANCE_API_SECRET appears to be invalid (too short)")
    
    return api_key.strip(), api_secret.strip()


def format_order_response(response: dict) -> str:
    """
    Format order response for display.
    
    Args:
        response: Order response from Binance API
        
    Returns:
        Formatted string representation of the order
    """
    if not response:
        return "No order data available"
    
    order_id = response.get('orderId', 'N/A')
    symbol = response.get('symbol', 'N/A')
    side = response.get('side', 'N/A')
    order_type = response.get('type', 'N/A')
    quantity = response.get('origQty', response.get('executedQty', 'N/A'))
    price = response.get('price', response.get('avgPrice', 'Market Price'))
    status = response.get('status', 'N/A')
    
    return (f"Order Details:\n"
           f"  Order ID: {order_id}\n"
           f"  Symbol: {symbol}\n"
           f"  Side: {side}\n"
           f"  Type: {order_type}\n"
           f"  Quantity: {quantity}\n"
           f"  Price: {price}\n"
           f"  Status: {status}")


def retry_api_call(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Retry decorator for API calls with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        
    Returns:
        Function result or raises the last exception
    """
    import time
    from binance.exceptions import BinanceAPIException, BinanceOrderException
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except (BinanceAPIException, BinanceOrderException, ConnectionError) as e:
            last_exception = e
            if attempt == max_retries:
                break
            
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            logger = logging.getLogger("binance_trading_bot")
            logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying in {delay}s...")
            time.sleep(delay)
    
    raise last_exception
