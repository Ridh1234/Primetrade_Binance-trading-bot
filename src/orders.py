"""
Order placement logic for market and limit orders.

This module contains the core order placement functionality,
handling both market and limit orders with proper error handling
and validation.
"""

import logging
import os
import sys
from typing import Dict, Any

# Handle imports for both direct execution and module usage
try:
    # Try relative imports first (when used as module)
    from .binance_client import BinanceClient
    from .exceptions import OrderPlacementException, APIConnectionException
    from .utils import retry_api_call, format_order_response
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add src directory to path if needed
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from binance_client import BinanceClient
    from exceptions import OrderPlacementException, APIConnectionException
    from utils import retry_api_call, format_order_response


class OrderManager:
    """
    Manages order placement and execution for the trading bot.
    
    This class provides high-level methods for placing market and limit orders
    with proper error handling, validation, and logging.
    """
    
    def __init__(self):
        """Initialize the order manager with a Binance client."""
        self.logger = logging.getLogger("binance_trading_bot")
        self.client = None
        
    def _get_client(self) -> BinanceClient:
        """
        Get or create Binance client instance.
        
        Returns:
            BinanceClient instance
            
        Raises:
            OrderPlacementException: If client initialization fails
        """
        if not self.client:
            try:
                self.client = BinanceClient()
                self.logger.info("Binance client initialized successfully")
            except Exception as e:
                error_msg = f"Failed to initialize Binance client: {str(e)}"
                self.logger.error(error_msg)
                raise OrderPlacementException(error_msg)
        
        return self.client
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market order with retry logic and error handling.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            
        Returns:
            Order response dictionary with execution details
            
        Raises:
            OrderPlacementException: If order placement fails
        """
        self.logger.info(f"Initiating market {side} order for {symbol}")
        self.logger.info(f"Order parameters - Symbol: {symbol}, Side: {side}, Quantity: {quantity}")
        
        try:
            client = self._get_client()
            
            # Verify symbol exists on exchange
            symbol_info = client.get_symbol_info(symbol)
            if not symbol_info:
                raise OrderPlacementException(f"Symbol {symbol} not found on exchange")
            
            if symbol_info.get('status') != 'TRADING':
                raise OrderPlacementException(f"Symbol {symbol} is not currently trading")
            
            # Get current price for logging
            try:
                current_price = client.get_ticker_price(symbol)
                self.logger.info(f"Current market price for {symbol}: {current_price}")
            except Exception as e:
                self.logger.warning(f"Could not retrieve current price: {str(e)}")
            
            # Place the market order with retry logic
            def place_order():
                return client.place_market_order(symbol, side, quantity)
            
            order_response = retry_api_call(place_order, max_retries=3)
            
            # Log successful order placement
            self.logger.info(f"Market order placed successfully!")
            self.logger.info(format_order_response(order_response))
            
            return order_response
            
        except (APIConnectionException, OrderPlacementException):
            raise
        except Exception as e:
            error_msg = f"Unexpected error placing market order: {str(e)}"
            self.logger.error(error_msg)
            raise OrderPlacementException(error_msg)
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order with retry logic and error handling.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            quantity: Order quantity
            price: Limit price
            
        Returns:
            Order response dictionary with execution details
            
        Raises:
            OrderPlacementException: If order placement fails
        """
        self.logger.info(f"Initiating limit {side} order for {symbol}")
        self.logger.info(f"Order parameters - Symbol: {symbol}, Side: {side}, Quantity: {quantity}, Price: {price}")
        
        try:
            client = self._get_client()
            
            # Verify symbol exists on exchange
            symbol_info = client.get_symbol_info(symbol)
            if not symbol_info:
                raise OrderPlacementException(f"Symbol {symbol} not found on exchange")
            
            if symbol_info.get('status') != 'TRADING':
                raise OrderPlacementException(f"Symbol {symbol} is not currently trading")
            
            # Get current price and compare with limit price
            try:
                current_price = client.get_ticker_price(symbol)
                self.logger.info(f"Current market price for {symbol}: {current_price}")
                
                # Log price comparison
                if side.upper() == 'BUY':
                    if price >= current_price:
                        self.logger.warning(f"BUY limit price ({price}) is at or above market price ({current_price}). Order may execute immediately.")
                    else:
                        self.logger.info(f"BUY limit price ({price}) is below market price ({current_price}). Order will wait for price to drop.")
                else:  # SELL
                    if price <= current_price:
                        self.logger.warning(f"SELL limit price ({price}) is at or below market price ({current_price}). Order may execute immediately.")
                    else:
                        self.logger.info(f"SELL limit price ({price}) is above market price ({current_price}). Order will wait for price to rise.")
                        
            except Exception as e:
                self.logger.warning(f"Could not retrieve current price for comparison: {str(e)}")
            
            # Place the limit order with retry logic
            def place_order():
                return client.place_limit_order(symbol, side, quantity, price)
            
            order_response = retry_api_call(place_order, max_retries=3)
            
            # Log successful order placement
            self.logger.info(f"Limit order placed successfully!")
            self.logger.info(format_order_response(order_response))
            
            return order_response
            
        except (APIConnectionException, OrderPlacementException):
            raise
        except Exception as e:
            error_msg = f"Unexpected error placing limit order: {str(e)}"
            self.logger.error(error_msg)
            raise OrderPlacementException(error_msg)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Get the status of a specific order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to check
            
        Returns:
            Order status dictionary
            
        Raises:
            OrderPlacementException: If status retrieval fails
        """
        try:
            client = self._get_client()
            
            def get_status():
                return client.get_order_status(symbol, order_id)
            
            order_status = retry_api_call(get_status, max_retries=2)
            
            self.logger.info(f"Order status retrieved for Order ID {order_id}")
            self.logger.info(format_order_response(order_status))
            
            return order_status
            
        except (APIConnectionException, OrderPlacementException):
            raise
        except Exception as e:
            error_msg = f"Failed to get order status: {str(e)}"
            self.logger.error(error_msg)
            raise OrderPlacementException(error_msg)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel a specific order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            
        Returns:
            Cancellation response dictionary
            
        Raises:
            OrderPlacementException: If cancellation fails
        """
        try:
            client = self._get_client()
            
            def cancel():
                return client.cancel_order(symbol, order_id)
            
            cancel_response = retry_api_call(cancel, max_retries=2)
            
            self.logger.info(f"Order {order_id} cancelled successfully")
            
            return cancel_response
            
        except (APIConnectionException, OrderPlacementException):
            raise
        except Exception as e:
            error_msg = f"Failed to cancel order: {str(e)}"
            self.logger.error(error_msg)
            raise OrderPlacementException(error_msg)
    
    def get_open_orders(self, symbol: str = None) -> list:
        """
        Get all open orders or open orders for a specific symbol.
        
        Args:
            symbol: Optional symbol to filter orders
            
        Returns:
            List of open orders
            
        Raises:
            OrderPlacementException: If retrieval fails
        """
        try:
            client = self._get_client()
            
            def get_orders():
                return client.get_open_orders(symbol)
            
            open_orders = retry_api_call(get_orders, max_retries=2)
            
            if symbol:
                self.logger.info(f"Retrieved {len(open_orders)} open orders for {symbol}")
            else:
                self.logger.info(f"Retrieved {len(open_orders)} total open orders")
            
            return open_orders
            
        except (APIConnectionException, OrderPlacementException):
            raise
        except Exception as e:
            error_msg = f"Failed to get open orders: {str(e)}"
            self.logger.error(error_msg)
            raise OrderPlacementException(error_msg)


# Standalone functions for simple usage
def place_market_order(symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    """
    Standalone function to place a market order.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        side: Order side (BUY or SELL)
        quantity: Order quantity
        
    Returns:
        Order response dictionary
        
    Raises:
        OrderPlacementException: If order placement fails
    """
    order_manager = OrderManager()
    return order_manager.place_market_order(symbol, side, quantity)


def place_limit_order(symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
    """
    Standalone function to place a limit order.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
        side: Order side (BUY or SELL)
        quantity: Order quantity
        price: Limit price
        
    Returns:
        Order response dictionary
        
    Raises:
        OrderPlacementException: If order placement fails
    """
    order_manager = OrderManager()
    return order_manager.place_limit_order(symbol, side, quantity, price)
